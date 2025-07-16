# core/auth.py — JWT Auth & Access Control
import jwt
import datetime
from werkzeug.security import check_password_hash
import os
from flask import request

# --- Config ---
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_EXPIRY = 3600  # seconds

# --- Mock User DB (replace with DB lookup or delegated auth in future) ---
USER_DB = {
    "admin": {
        "password_hash": os.getenv("ADMIN_HASH"),
        "role": "admin"
    },
    "demo": {
        "password_hash": os.getenv("DEMO_HASH"),
        "role": "user"
    }
}

# --- Core Auth Functions ---
def authenticate_user(username: str, password: str) -> str:
    """Validate credentials and return a JWT token if valid."""
    user = USER_DB.get(username)
    if not user or not check_password_hash(user["password_hash"], password):
        return None

    payload = {
        "username": username,
        "role": user["role"],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(seconds=JWT_EXPIRY)
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return token

def verify_token(token: str) -> dict:
    """Decode and validate a JWT token, returning user claims."""
    try:
        decoded = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return decoded
    except jwt.ExpiredSignatureError:
        return {"error": "Token expired"}
    except jwt.InvalidTokenError:
        return {"error": "Invalid token"}

def is_admin(token_data: dict) -> bool:
    """Check whether a given token belongs to an admin role."""
    return token_data.get("role") == "admin"

def get_current_user(token: str = None) -> dict:
    """Extract user identity from token (for audit or UI personalization)."""
    token = token or request.headers.get("Authorization", "").replace("Bearer ", "")
    return verify_token(token)
