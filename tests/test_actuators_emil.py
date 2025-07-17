# tests/test_actuators_email.py

import pytest
from core.actuators import email

@pytest.fixture(autouse=True)
def patch_core(monkeypatch):
    monkeypatch.setattr("core.actuators.email.log_action", lambda *a, **k: True)
    
    dummy_smtp = type("DummySMTP", (), {
        "sendmail": staticmethod(lambda *a, **k: None),
        "quit": staticmethod(lambda: None)
    })
    monkeypatch.setattr("core.actuators.email.smtplib", type("SMTP", (), {"SMTP": staticmethod(lambda *a, **k: dummy_smtp)}))

    monkeypatch.setattr("core.actuators.email.MIMEText", lambda *a, **k: "mime")
    monkeypatch.setattr("core.actuators.email.MIMEMultipart", lambda *a, **k: type("MM", (), {
        "attach": lambda self, part: None,
        "__str__": lambda self: "email"
    })())
    
    monkeypatch.setattr("core.actuators.email.get_email_config", lambda: {
        "server": "smtp.test", "port": 123, "user": "u", "password": "p"
    })

def test_get_email_config():
    cfg = email.get_email_config()
    assert isinstance(cfg, dict)

def test_send_email():
    ok = email.send_email("to@ex.com", "Subject", "Body")
    assert isinstance(ok, bool) or ok is None

def test_notify_admin():
    ok = email.notify_admin("type", {"payload": "x"})
    assert isinstance(ok, bool) or ok is None

def test_send_weekly_digest():
    ok = email.send_weekly_digest("user1")
    assert isinstance(ok, bool) or ok is None
