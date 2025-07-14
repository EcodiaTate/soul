# routes/test.py
import os
import openai
from flask import Blueprint, jsonify

bp = Blueprint("test", __name__)

@bp.route("/api/test-openai", methods=["GET"])
def test_openai():
    try:
        # New client interface (>=1.0.0)
        client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        models = client.models.list()

        return jsonify({
            "status": "ok",
            "models": [m.id for m in models.data]
        })
    except Exception as e:
        print("🔥 OpenAI test failed:", repr(e))
        return jsonify({"status": "error", "message": str(e)}), 500
