import os
from flask import Flask, jsonify
from dotenv import load_dotenv
load_dotenv()

from routes.events import events_bp
from routes import test
from routes.chat import chat_bp
def create_app():
    app = Flask(__name__)

    # ✅ Register blueprints inside the app context
    app.register_blueprint(events_bp)
    app.register_blueprint(test.bp)
    app.register_blueprint(chat_bp)
    
    @app.route("/api/ping")
    def ping():
        return jsonify({"status": "ok"})

    return app

if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
