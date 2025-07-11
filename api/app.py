import os
import logging
import json

from datetime import datetime, timedelta
from flask import Flask, jsonify, request, abort
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token, get_jwt_identity
)
from flask_socketio import SocketIO, emit, join_room, leave_room
from core.db import get_session
from core.vectors import rescore_node_with_llm, update_node_vector, search_vectors
from core.utils import get_embedding
from uuid import uuid4

# ===== CONFIG & INIT =====
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("API_SECRET", "change_this_123")
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET", "super-secret")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=2)

CORS(app, supports_credentials=True)
jwt = JWTManager(app)
socketio = SocketIO(app, cors_allowed_origins="*")

logging.basicConfig(level=logging.INFO, filename="logs/api.log")

# === ADMIN/GODMODE ===
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "changeme")
GOD_SESSIONS = set()  # session_id of admin sessions
GM_SECRET_PHRASE = os.environ.get("GM_SECRET_PHRASE", "unlock the garden of eden").strip().lower()
GM_PASSWORD = os.environ.get("GM_PASSWORD", "changeme").strip()

# ==== AUTH ====

@app.route("/api/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    if username == "admin" and password == ADMIN_PASSWORD:
        token = create_access_token(identity="admin")
        return jsonify(access_token=token)
    abort(401, description="Invalid credentials.")

@app.route("/api/godmode", methods=["POST"])
@jwt_required()
def godmode():
    data = request.json
    pw = data.get("password")
    sid = get_jwt_identity()
    if pw == ADMIN_PASSWORD:
        GOD_SESSIONS.add(sid)
        return jsonify({"status": "godmode enabled"})
    return jsonify({"status": "forbidden"}), 403

def is_god():
    try:
        return get_jwt_identity() == "admin"
    except Exception:
        return False

# ==== GOD MODE CHAT SESSION CHECKER ====

def is_god_session(sid):
    with get_session() as session:
        result = session.run(
            "MATCH (c:ChatSession {session_id: $sid}) RETURN c.god_mode as gm", sid=sid
        )
        gm = (result.single() or {}).get("gm", False)
    return bool(gm)

# ==== EVENT INGESTION ====

def normalize_event(data):
    raw_text = data.get("raw_text") or data.get("Summary") or data.get("summary")
    if not raw_text:
        raise ValueError("Missing raw_text")
    node_type = data.get("node_type", "Event")
    timestamp = data.get("timestamp") or datetime.utcnow().isoformat()
    source = data.get("source") or "api"
    meta = data.get("meta", {})
    return {
        "raw_text": raw_text,
        "node_type": node_type,
        "timestamp": timestamp,
        "source": source,
        "meta": meta
    }

@app.route("/api/event", methods=["POST"])
def add_event():
    data = request.json
    try:
        event = normalize_event(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    embedding = get_embedding(event["raw_text"])
    with get_session() as session:
        result = session.run("""
            MATCH (e:Event) WHERE e.raw_text = $raw_text AND e.timestamp = $timestamp
            RETURN id(e) as eid
        """, raw_text=event["raw_text"], timestamp=event["timestamp"])
        existing = result.single()
        if existing:
            return jsonify({"event_id": existing["eid"], "status": "duplicate"}), 200
        query = f"""
            CREATE (e:{event['node_type']} {{
                raw_text: $raw_text,
                embedding: $embedding,
                timestamp: $timestamp,
                source: $source,
                meta: $meta,
                status: 'unprocessed',
                created: timestamp()
            }}) RETURN id(e) as event_id
        """
        result = session.run(query, raw_text=event["raw_text"], embedding=json.dumps(embedding),
                             timestamp=event["timestamp"], source=event["source"], meta=json.dumps(event["meta"]))
        event_id = result.single()["event_id"]
    node = {"nid": event_id, "labels": [event["node_type"]], "raw_text": event["raw_text"]}
    res = rescore_node_with_llm(node)
    update_node_vector(
        event_id,
        res.get('impact_vector'),
        res.get('justifications', []),
        agent=res.get('agent', 'api'),
        model=res.get('model', 'api'),
        prompt=res.get('prompt', 'api-import')
    )
    socketio.emit("event:new", {"event_id": event_id, "summary": event["raw_text"]}, broadcast=True)
    return jsonify({"event_id": event_id, "status": "saved"})

# ==== TIMELINE FETCH ====

@app.route("/api/timeline", methods=["GET"])
def timeline():
    args = request.args
    source = args.get("source")
    node_type = args.get("type", "Event")
    limit = int(args.get("limit", 100))
    with get_session() as session:
        q = f"MATCH (e:{node_type}) "
        if source:
            q += "WHERE e.source = $source "
        q += "RETURN id(e) as eid, e.raw_text as raw_text, e.timestamp as timestamp, e.source as source, e.meta as meta, e.status as status, e.embedding as embedding ORDER BY e.timestamp DESC LIMIT $limit"
        params = {"source": source, "limit": limit}
        result = session.run(q, **params)
        events = [dict(r) for r in result]
    return jsonify(events)

# ==== VECTOR SEARCH ====

@app.route("/api/vector_search", methods=["POST"])
def vector_search():
    data = request.json
    embedding = data.get("embedding")
    if not embedding:
        text = data.get("text")
        if not text:
            return jsonify({"error": "No embedding or text"}), 400
        embedding = get_embedding(text)
    matches = search_vectors(embedding, top_k=data.get("top_k", 8))
    return jsonify(matches)

# ==== CHAT SESSION MEMORY WITH GOD MODE TRIGGER ====

@app.route("/api/chat_session", methods=["POST"])
def new_chat_session():
    session_id = str(uuid4())
    with get_session() as session:
        session.run("""
            CREATE (c:ChatSession {session_id: $sid, started: timestamp(), god_mode: false, awaiting_gm_pw: false})
        """, sid=session_id)
    return jsonify({"session_id": session_id})

@app.route("/api/chat_session/<sid>/message", methods=["POST"])
def add_message(sid):
    data = request.json
    msg = data.get("text", "")
    sender = data.get("sender", "user")
    msg_lc = msg.strip().lower()
    embedding = get_embedding(msg)

    with get_session() as session:
        # Fetch current god mode state
        result = session.run(
            "MATCH (c:ChatSession {session_id: $sid}) RETURN c.god_mode as gm, c.awaiting_gm_pw as awaiting",
            sid=sid
        )
        state = result.single() or {}
        gm = state.get("gm", False)
        awaiting_gm_pw = state.get("awaiting", False)

        # Step 1: Listen for secret phrase
        if not gm and not awaiting_gm_pw and msg_lc == GM_SECRET_PHRASE:
            session.run("MATCH (c:ChatSession {session_id: $sid}) SET c.awaiting_gm_pw = true", sid=sid)
            return jsonify({"status": "awaiting_godmode_pw", "message": "🌟 God mode phrase detected. Please enter the god mode password."})

        # Step 2: If awaiting password, check it
        if not gm and awaiting_gm_pw:
            if msg.strip() == GM_PASSWORD:
                session.run("MATCH (c:ChatSession {session_id: $sid}) SET c.god_mode = true, c.awaiting_gm_pw = false", sid=sid)
                session.run("""
                    MATCH (c:ChatSession {session_id: $sid})
                    CREATE (m:Message {text: '[GOD MODE ACTIVATED]', sender: 'system', timestamp: timestamp()})
                    CREATE (c)-[:HAS_MESSAGE]->(m)
                """, sid=sid)
                return jsonify({"status": "godmode_activated", "message": "🌟 GOD MODE ACTIVATED. You now have full access."})
            else:
                session.run("MATCH (c:ChatSession {session_id: $sid}) SET c.awaiting_gm_pw = false", sid=sid)
                return jsonify({"status": "gm_pw_incorrect", "message": "❌ Incorrect god mode password."})

        # Step 3: Normal message save
        session.run("""
            MATCH (c:ChatSession {session_id: $sid})
            CREATE (m:Message {text: $msg, sender: $sender, embedding: $embedding, timestamp: timestamp()})
            CREATE (c)-[:HAS_MESSAGE]->(m)
        """, sid=sid, msg=msg, sender=sender, embedding=json.dumps(embedding))
         
         # Store as a timeline event for cognition/timeline
        from core.db import save_event
        event = {
            "raw_text": msg,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "user_chat",
            "meta": {"sid": sid, "sender": sender}
        }
        save_event(event)

    return jsonify({"status": "saved"})

@app.route("/api/chat_session/<sid>/history", methods=["GET"])
def chat_history(sid):
    with get_session() as session:
        result = session.run("""
            MATCH (c:ChatSession {session_id: $sid})-[:HAS_MESSAGE]->(m)
            RETURN m.text as text, m.sender as sender, m.timestamp as ts
            ORDER BY m.timestamp ASC
        """, sid=sid)
        msgs = [dict(r) for r in result]
    return jsonify(msgs)

# ==== GOD MODE: SECURED ADMIN ACTIONS ====

@app.route("/api/god/<action>", methods=["POST"])
@jwt_required()
def god_action(action):
    if not is_god():
        return jsonify({"error": "not admin"}), 403
    if action == "delete_event":
        eid = request.json.get("event_id")
        with get_session() as session:
            session.run("MATCH (e) WHERE id(e) = $eid DETACH DELETE e", eid=eid)
        return jsonify({"status": "deleted"})
    return jsonify({"error": "unknown action"}), 400

# ==== ERROR HANDLING ====

@app.errorhandler(400)
@app.errorhandler(401)
@app.errorhandler(404)
@app.errorhandler(500)
def error_handler(e):
    return jsonify({"error": str(e)}), getattr(e, 'code', 500)

from api.google_oauth import bp as google_auth_bp
app.register_blueprint(google_auth_bp)

if __name__ == "__main__":
    print("API started on http://localhost:5001")
    socketio.run(app, host="0.0.0.0", port=5001, debug=True)
