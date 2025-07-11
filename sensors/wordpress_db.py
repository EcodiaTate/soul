import mysql.connector
import os
import json
from core.db import save_event
from datetime import datetime

# === DB CONFIG ===
db_config = {
    'host': os.getenv('WP_DB_HOST', 'srv1864.hstgr.io'),
    'user': os.getenv('WP_DB_USER', 'u648780255_btWuC'),
    'password': os.getenv('WP_DB_PASSWORD', '7nSZNzMmPhNRVVna'),
    'database': os.getenv('WP_DB_NAME', 'u648780255_f9Trf'),
    'port': int(os.getenv('WP_DB_PORT', 3306))
}

# === REDACT SENSITIVE ===
def redact(value, field_name=""):
    if not value:
        return value
    if isinstance(value, str) and ("@" in value or "gmail" in value or "email" in field_name or "phone" in field_name):
        return "[REDACTED]"
    if field_name in {"content", "message", "chat", "notes", "comments"}:
        return "[REDACTED]"
    return value

# === PULL POSTS ===
def get_wp_posts(cursor, max_results=50):
    query = """
        SELECT ID, post_title, post_content, post_date_gmt, post_type, post_status
        FROM wp_posts
        WHERE post_status='publish'
        ORDER BY post_date_gmt DESC
        LIMIT %s
    """
    cursor.execute(query, (max_results,))
    rows = cursor.fetchall()
    events = []
    for post_id, title, content, post_date, post_type, post_status in rows:
        meta = {
            "post_id": post_id,
            "post_type": post_type,
            "post_status": post_status,
            "content": redact(content, "content")
        }
        event = {
            "raw_text": title or "Untitled Post",
            "timestamp": post_date.isoformat() if post_date else datetime.utcnow().isoformat(),
            "source": "wordpress_post",
            "meta": meta
        }
        save_event(event)
        events.append(event)
    return events

# === PULL WPForms ENTRIES ===
def get_wpforms_entries(cursor, form_id, field_ids=None, max_results=50):
    query = """
        SELECT entry_id, fields, date FROM wp_wpforms_entries
        WHERE form_id = %s
        ORDER BY date DESC
        LIMIT %s
    """
    cursor.execute(query, (form_id, max_results))
    rows = cursor.fetchall()
    events = []
    for entry_id, fields_json, date in rows:
        try:
            fields = json.loads(fields_json)
        except Exception:
            fields = {}
        meta = {"entry_id": entry_id}
        for fid, val in fields.items():
            field_val = val.get("value", "")
            meta[f"field_{fid}"] = redact(field_val, f"field_{fid}")
        event = {
            "raw_text": f"WPForm Entry {entry_id}",
            "timestamp": date.isoformat() if date else datetime.utcnow().isoformat(),
            "source": "wordpress_form",
            "meta": meta
        }
        save_event(event)
        events.append(event)
    return events

# === PULL SIDEQUEST SUBMISSIONS ===
def get_sidequest_entries(cursor, max_results=50):
    query = """
        SELECT id, quest_id, instagram_url, submission_date, points_awarded, latitude, longitude
        FROM wp_ecodia_quest_submissions
        ORDER BY submission_date DESC
        LIMIT %s
    """
    cursor.execute(query, (max_results,))
    rows = cursor.fetchall()
    events = []
    for row in rows:
        meta = {
            "quest_id": row[1],
            "instagram_url": redact(row[2], "instagram_url"),
            "points_awarded": row[4],
            "latitude": row[5],
            "longitude": row[6]
        }
        event = {
            "raw_text": f"Sidequest Submission {row[0]}",
            "timestamp": row[3].isoformat() if row[3] else datetime.utcnow().isoformat(),
            "source": "sidequest_submission",
            "meta": meta
        }
        save_event(event)
        events.append(event)
    return events

# === ADD MORE FOR OTHER TABLES ===
# Add new get_..._entries() as needed for other custom tables.

# === MAIN RUNNER ===
def run_all(max_results=50):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    all_events = []

    # Posts
    all_events.extend(get_wp_posts(cursor, max_results=max_results))

    # WPForms (example forms, add more as needed)
    # (Form IDs: 85 = EYBA TXN, 406 = Ecotype, 4341 = Signup, 3538 = Contact)
    all_events.extend(get_wpforms_entries(cursor, form_id=85, max_results=max_results))     # EYBA TXN
    all_events.extend(get_wpforms_entries(cursor, form_id=406, max_results=max_results))    # Ecotype Quiz
    all_events.extend(get_wpforms_entries(cursor, form_id=4341, max_results=max_results))   # Signup
    all_events.extend(get_wpforms_entries(cursor, form_id=3538, max_results=max_results))   # Contact

    # Sidequest Submissions
    all_events.extend(get_sidequest_entries(cursor, max_results=max_results))

    cursor.close()
    conn.close()
    return all_events

if __name__ == "__main__":
    events = run_all(50)
    print(f"Ingested {len(events)} WordPress DB events.")
