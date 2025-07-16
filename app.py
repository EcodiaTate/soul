import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv

# Load .env config
load_dotenv()

# Pre-validate critical secrets (fail fast if missing)
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY")
assert FLASK_SECRET_KEY, "FLASK_SECRET_KEY is required"

JWT_SECRET = os.getenv("JWT_SECRET")
assert JWT_SECRET, "JWT_SECRET is required"

SOCKETIO_ASYNC_MODE = os.getenv("SOCKETIO_ASYNC_MODE", "eventlet")  # Default to eventlet
socketio = SocketIO(cors_allowed_origins="*", async_mode=SOCKETIO_ASYNC_MODE)

def create_app():
    app = Flask(__name__)

    # Load config
    app.config['SECRET_KEY'] = FLASK_SECRET_KEY
    app.config['JWT_SECRET_KEY'] = JWT_SECRET

    # CORS: Only allow your frontend in prod
    allowed_origins = [
        os.getenv("FRONTEND_URL", "http://localhost:5173"),
        "http://localhost:5173"
    ]
    CORS(app, supports_credentials=True, origins=allowed_origins)

    # Register blueprints
    from routes.events import events_bp
    from routes.chat import chat_bp
    from routes.timeline import timeline_bp
    from routes.dreams import dreams_bp

    app.register_blueprint(events_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(timeline_bp)
    app.register_blueprint(dreams_bp)

    # JWT setup
    jwt = JWTManager(app)

    # Health check endpoint
    @app.route("/api/ping")
    def ping():
        return jsonify({"status": "ok"})

    # Clean Neo4j connection
    from core.graph_io import getdriver

    @app.teardown_appcontext
    def closedriver(exception=None):
        driver = getdriver()
        driver.close()
        print("[app] Closed Neo4j driver connection.")

    # Attach SocketIO
    socketio.init_app(app)

    return app

# Local development server (Flask + SocketIO)
if __name__ == "__main__":
    app = create_app()
    port = int(os.getenv("PORT", 5000))
    print(f"[socketio] Using async mode: {socketio.async_mode}")
    socketio.run(app, host="0.0.0.0", port=port)
