# core/actuators/wordpress.py — Public Web Publishing Interface
import requests
import os
import base64

from core.timeline_engine import get_timeline_entries
from core.logging_engine import log_action

# --- Config ---
WORDPRESS_API = os.getenv("WORDPRESS_API_URL")  # e.g., https://site.com/wp-json/wp/v2
WP_USER = os.getenv("WORDPRESS_USERNAME")
WP_PASS = os.getenv("WORDPRESS_PASSWORD")

auth_headers = {
    "Authorization": "Basic " + base64.b64encode(f"{WP_USER}:{WP_PASS}".encode()).decode(),
    "Content-Type": "application/json"
}

# --- Core Functions ---
def publish_post(title: str, content: str, tags: list[str] = None) -> dict:
    """Create and publish a new WordPress post via REST API."""
    try:
        data = {
            "title": title,
            "content": content,
            "status": "publish",
            "tags": tags or []
        }
        response = requests.post(
            f"{WORDPRESS_API}/posts",
            headers=auth_headers,
            json=data
        )
        result = response.json()
        log_action("wordpress", "publish", f"Posted: {title}")
        return result
    except Exception as e:
        log_action("wordpress", "error", f"Failed to post: {e}")
        return {"error": str(e)}

def update_post(post_id: int, content: str) -> bool:
    """Edit an existing post (for corrections or timeline additions)."""
    try:
        data = {"content": content}
        response = requests.post(
            f"{WORDPRESS_API}/posts/{post_id}",
            headers=auth_headers,
            json=data
        )
        log_action("wordpress", "update", f"Updated post {post_id}")
        return response.status_code == 200
    except Exception as e:
        log_action("wordpress", "error", f"Failed to update: {e}")
        return False

def sync_timeline_to_wordpress(limit: int = 3) -> bool:
    """Push recent timeline events as blog entries automatically."""
    entries = get_timeline_entries(limit=limit)
    for entry in entries:
        data = entry["t"]
        title = f"Timeline: {data.get('timestamp', '')}"
        content = f"<p>{data.get('summary', '')}</p><p><em>{data.get('rationale', '')}</em></p>"
        publish_post(title, content)
    return True
