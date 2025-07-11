import json
import requests
import os
from dotenv import load_dotenv
from core.db import save_event
from datetime import datetime

load_dotenv()
GOOGLE_API_KEY = os.getenv("NEO_GOOGLE_KEY")

def get_events(max_results=3):
    url = f"https://places.googleapis.com/v1/places:searchText?key={GOOGLE_API_KEY}"
    queries = ["Sunshine Coast", "Brisbane", "Sydney"]  # Example queries
    events = []
    for q in queries[:max_results]:
        data = {"textQuery": q}
        resp = requests.post(url, json=data)
        if not resp.ok:
            print("Places API error:", resp.text)
            continue
        res = resp.json()
        now = datetime.utcnow().isoformat()
        for place in res.get("places", []):
            event = {
                "raw_text": f"Place found: {place.get('displayName', {}).get('text', 'Unknown')}",
                "timestamp": now,
                "source": "places",
                "meta": json.dumps({
                    "place_id": place.get("id"),
                    "display_name": place.get("displayName", {}).get("text"),
                    "address": place.get("formattedAddress"),
                    "location": place.get("location"),
                })
            }
            save_event(event)
            events.append(event)
    return events
