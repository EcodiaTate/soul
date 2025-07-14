import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv

# Load .env
load_dotenv()

# Flask setup
def create_app():
    app = Flask(__name__)
    CORS(app, supports_credentials=True, origins=[
        os.environ.get("FRONTEND_URL", "http://localhost:5173"),
        "http://localhost:5173"
    ])
    # Set Flask/JWT config
    app.config['SECRET_KEY'] = os.environ.get("FLASK_SECRET_KEY", "supersecret")
    app.config['JWT_SECRET_KEY'] = os.environ.get("JWT_SECRET", "jwtsecret")

    # Register Blueprints
    from routes.events import events_bp
    from routes.chat import chat_bp
    from routes.timeline import timeline_bp
    # Add others as you expand (e.g. agents_bp, dreams_bp, auth_bp)
    import routes.test  # If you have a 'test' blueprint

    app.register_blueprint(events_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(timeline_bp)
    app.register_blueprint(routes.test.bp)

    # JWT
    jwt = JWTManager(app)

    # Health check
    @app.route("/api/ping")
    def ping():
        return jsonify({"status": "ok"})

    return app

# SocketIO setup (must be global for import in core/socket_handlers.py)
socketio = SocketIO(cors_allowed_origins="*")  # Allow all for dev; restrict in prod

app = create_app()
socketio.init_app(app, async_mode="eventlet")

# Optionally: Start background jobs here
# from core.memory_engine import run_decay_cycle
# socketio.start_background_task(run_decay_cycle)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port)
