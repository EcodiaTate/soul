# core/actuators/email.py — System Email Notifier
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from core.logging_engine import log_action

# --- Lazy Config Loader ---
def get_email_config():
    """
    Load SMTP and email credentials at send time.
    Returns a dict with all config values, raising if missing.
    """
    config = {
        "EMAIL_SENDER": os.getenv("EMAIL_SENDER"),
        "SMTP_SERVER": os.getenv("SMTP_SERVER"),
        "SMTP_PORT": int(os.getenv("SMTP_PORT", 587)),
        "SMTP_USER": os.getenv("SMTP_USER"),
        "SMTP_PASS": os.getenv("SMTP_PASS"),
    }
    for k, v in config.items():
        if v in [None, ""]:
            raise RuntimeError(f"Missing email config: {k}")
    return config

# --- Core Functions ---
def send_email(to_address: str, subject: str, body: str) -> bool:
    """Send a plaintext or HTML email to a recipient. Loads SMTP config at call."""
    try:
        cfg = get_email_config()
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = cfg["EMAIL_SENDER"]
        msg["To"] = to_address

        part = MIMEText(body, "html" if "<" in body else "plain")
        msg.attach(part)

        with smtplib.SMTP(cfg["SMTP_SERVER"], cfg["SMTP_PORT"]) as server:
            server.starttls()
            server.login(cfg["SMTP_USER"], cfg["SMTP_PASS"])
            server.sendmail(cfg["EMAIL_SENDER"], to_address, msg.as_string())

        log_action("email", "send", f"Email sent to {to_address}: {subject}")
        return True
    except Exception as e:
        log_action("email", "error", f"Failed to send to {to_address}: {e}")
        return False

def notify_admin(event_type: str, payload: dict) -> bool:
    """Email alert to admins about high-impact events (e.g., contradiction detected)."""
    subject = f"[SoulOS Alert] {event_type.upper()}"
    body = f"<h3>{event_type}</h3><pre>{payload}</pre>"
    admin_email = os.getenv("ADMIN_EMAIL")
    if not admin_email:
        log_action("email", "error", "ADMIN_EMAIL not set in environment")
        return False
    return send_email(admin_email, subject, body)

def send_weekly_digest(user_id: str) -> bool:
    """Compile and send a user-specific digest of recent soul activity (timeline, dreams, shifts)."""
    from core.timeline_engine import get_timeline_entries
    entries = get_timeline_entries(limit=5)

    timeline_html = "".join(
        f"<p><strong>{e['t']['timestamp']}</strong>: {e['t']['summary']}</p>"
        for e in entries
    )
    body = f"<h2>SoulOS Weekly Digest</h2>{timeline_html}"
    return send_email(user_id, "Your Weekly SoulOS Digest", body)
