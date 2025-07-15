import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv

# Load .env config
load_dotenv()

SOCKETIO_ASYNC_MODE = os.environ.get("SOCKETIO_ASYNC_MODE", "threading")  # or "eventlet"

# Create SocketIO singleton (NO app attached yet)
socketio = SocketIO(cors_allowed_origins="*", async_mode=SOCKETIO_ASYNC_MODE)

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

    # Attach SocketIO to app
    socketio.init_app(app)

    return app

# Run only for local/dev (not in Gunicorn/wsgi)
if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port)
