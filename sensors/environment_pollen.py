import json
import requests
import os
from dotenv import load_dotenv
from core.db import save_event
from datetime import datetime

load_dotenv()
GOOGLE_API_KEY = os.getenv("NEO_GOOGLE_KEY")

def get_events(max_results=1):
    url = f"https://pollen.googleapis.com/v1/pollenCounts:lookup?key={GOOGLE_API_KEY}"
    params = {
        "location": {"latitude": -26.65, "longitude": 153.09}
    }
    resp = requests.post(url, json=params)
    if not resp.ok:
        print("Pollen API error:", resp.text)
        return []
    data = resp.json().get("pollenCounts", {})
    now = datetime.utcnow().isoformat()
    event = {
        'raw_text': f"Pollen Count: Tree {data.get('treeIndex', 'NA')}, Grass {data.get('grassIndex', 'NA')}, Weed {data.get('weedIndex', 'NA')}",
        'timestamp': now,
        'source': 'pollen',
        'meta': json.dumps({
            "location": {"lat": -26.65, "lng": 153.09},   # Redact only if very sensitive
            "tree_pollen": data.get("treeIndex"),
            "grass_pollen": data.get("grassIndex"),
            "weed_pollen": data.get("weedIndex")
        })
    }
    save_event(event)
    return [event]
