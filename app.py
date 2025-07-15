# app.py (PRODUCTION)

import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv

load_dotenv()

SOCKETIO_ASYNC_MODE = os.environ.get("SOCKETIO_ASYNC_MODE", "threading")  # or "eventlet"

socketio = SocketIO(cors_allowed_origins="*", async_mode=SOCKETIO_ASYNC_MODE)  # <-- NO app argument here!

def create_app():
    app = Flask(__name__)
    allowed_origins = [
        os.environ.get("FRONTEND_URL", "http://localhost:5173"),
        "http://localhost:5173"
    ]
    CORS(app, supports_credentials=True, origins=allowed_origins)
    app.config['SECRET_KEY'] = os.environ.get("FLASK_SECRET_KEY", "supersecret")
    app.config['JWT_SECRET_KEY'] = os.environ.get("JWT_SECRET", "jwtsecret")

    from routes.events import events_bp
    from routes.chat import chat_bp
    from routes.timeline import timeline_bp
    from routes.dreams import dreams_bp

    app.register_blueprint(events_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(timeline_bp)
    app.register_blueprint(dreams_bp)

    jwt = JWTManager(app)

    @app.route("/api/ping")
    def ping():
        return jsonify({"status": "ok"})

    # --- IMPORTANT: Initialize socketio with the created app! ---
    socketio.init_app(app)

    return app

# Only for running with "python app.py" (dev/local)
if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port)
