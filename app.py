import os
from flask import Flask, jsonify

def create_app():
    app = Flask(__name__)

    @app.route("/api/ping")
    def ping():
        return jsonify({"status": "ok"})

    return app

if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", 5000))  # Default to 5000 for local, but use Render's PORT in prod
    app.run(host="0.0.0.0", port=port)
