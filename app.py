# app.py (PRODUCTION)

import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv

# Load .env config
load_dotenv()

# ------------------------
# Flask app factory
# ------------------------
def create_app():
    app = Flask(__name__)

    # CORS: Only allow your frontend in prod
    allowed_origins = [
        os.environ.get("FRONTEND_URL", "http://localhost:5173"),
        "http://localhost:5173"
    ]
    CORS(app, supports_credentials=True, origins=allowed_origins)

    # Security settings
    app.config['SECRET_KEY'] = os.environ.get("FLASK_SECRET_KEY", "supersecret")
    app.config['JWT_SECRET_KEY'] = os.environ.get("JWT_SECRET", "jwtsecret")

    # Register all blueprints
    from routes.events import events_bp
    from routes.chat import chat_bp
    from routes.timeline import timeline_bp
    from routes.dreams import dreams_bp
    # Uncomment/add more as you expand (e.g. agents_bp, auth_bp)
    # from routes.agents import agents_bp
    # from routes.auth import auth_bp

    app.register_blueprint(events_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(timeline_bp)
    app.register_blueprint(dreams_bp)

    # JWT for admin routes
    jwt = JWTManager(app)

    # Health check endpoint
    @app.route("/api/ping")
    def ping():
        return jsonify({"status": "ok"})

    return app

# ------------------------
# Global SocketIO instance
# ------------------------
# For Neo4j compatibility in production, use "threading" or "eventlet" as needed:
# If deploying with Gunicorn + Eventlet: use "eventlet"
# If you use Gunicorn + threading: use "threading"
SOCKETIO_ASYNC_MODE = os.environ.get("SOCKETIO_ASYNC_MODE", "threading")  # or "eventlet"

app = create_app()
socketio = SocketIO(app, cors_allowed_origins="*", async_mode=SOCKETIO_ASYNC_MODE)

# Optionally: import and start background tasks here if needed in prod
# from core.memory_engine import run_decay_cycle
# socketio.start_background_task(run_decay_cycle)

# ------------------------
# Gunicorn/Production entrypoint
# ------------------------
# To run in production: gunicorn -w 1 -k eventlet -b 0.0.0.0:5000 app:app
# OR (for threading):   gunicorn -w 1 -k gthread   -b 0.0.0.0:5000 app:app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port)
