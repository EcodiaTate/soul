# tests/test_auth.py

import pytest
import datetime
from core import auth
from flask import Flask, request

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    yield app

def make_token(username="admin", role="admin", exp=None):
    if exp is None:
        exp = datetime.datetime.utcnow() + datetime.timedelta(seconds=auth.JWT_EXPIRY)
    payload = {"username": username, "role": role, "exp": exp}
    return auth.jwt.encode(payload, auth.JWT_SECRET, algorithm="HS256")

def test_authenticate_user_valid(monkeypatch):
    monkeypatch.setitem(auth.USER_DB["admin"], "password_hash", auth.USER_DB["admin"]["password_hash"])
    # Assuming correct password hash is already set in env
    token = auth.authenticate_user("admin", "<correct_password>")
    # This depends on your hashing, you may need to patch check_password_hash to return True
    # Example:
    # monkeypatch.setattr(auth, "check_password_hash", lambda ph, pw: True)
    assert token is not None

def test_authenticate_user_invalid(monkeypatch):
    monkeypatch.setattr(auth, "check_password_hash", lambda ph, pw: False)
    token = auth.authenticate_user("admin", "wrongpassword")
    assert token is None

def test_verify_token_valid():
    token = make_token()
    decoded = auth.verify_token(token)
    assert decoded["username"] == "admin"
    assert decoded["role"] == "admin"

def test_verify_token_expired():
    exp = datetime.datetime.utcnow() - datetime.timedelta(seconds=10)
    token = make_token(exp=exp)
    decoded = auth.verify_token(token)
    assert "error" in decoded and "expired" in decoded["error"].lower()

def test_verify_token_invalid():
    decoded = auth.verify_token("not_a_real_token")
    assert "error" in decoded

def test_is_admin_true():
    assert auth.is_admin({"role": "admin"}) is True

def test_is_admin_false():
    assert auth.is_admin({"role": "user"}) is False

def test_get_current_user_valid(app, monkeypatch):
    token = make_token()
    with app.test_request_context(headers={"Authorization": f"Bearer {token}"}):
        user = auth.get_current_user()
        assert user["username"] == "admin"

def test_get_current_user_missing_token(app):
    with app.test_request_context(headers={}):
        user = auth.get_current_user()
        # Should return error or None if token missing/invalid
        assert user is None or "error" in user
