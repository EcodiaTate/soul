# routes/test.py
import os
import openai
from flask import Blueprint, jsonify

bp = Blueprint("test", __name__)

@bp.route("/api/test-openai", methods=["GET"])
def test_openai():
    try:
        openai.api_key = os.environ["OPENAI_API_KEY"]
        response = openai.Model.list()
        return jsonify({"status": "ok", "models": [m.id for m in response.data]})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
