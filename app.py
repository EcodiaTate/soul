import os
from flask import Flask, jsonify
from routes.events import events_bp  # ✅ Import the events blueprint

def create_app():
    app = Flask(__name__)

    # ✅ Register API routes
    app.register_blueprint(events_bp)

    @app.route("/api/ping")
    def ping():
        return jsonify({"status": "ok"})

    return app

if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
