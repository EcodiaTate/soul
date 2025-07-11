import json
import requests
import os
from dotenv import load_dotenv
from core.db import save_event
from datetime import datetime

load_dotenv()
GOOGLE_API_KEY = os.getenv("NEO_GOOGLE_KEY")

def get_events(max_results=1):
    url = f"https://airquality.googleapis.com/v1/currentConditions:lookup?key={GOOGLE_API_KEY}"
    params = {
        "location": {"latitude": -26.65, "longitude": 153.09}
    }
    resp = requests.post(url, json=params)
    if not resp.ok:
        print("Air Quality API error:", resp.text)
        return []
    data = resp.json().get("currentConditions", {})
    now = datetime.utcnow().isoformat()
    idx = data.get("indexes", [{}])[0]
    event = {
        'raw_text': f"Air Quality: {idx.get('aqiDisplay', 'No AQI')}",
        'timestamp': now,
        'source': 'air_quality',
        'meta': json.dumps({
            "location": {"lat": -26.65, "lng": 153.09},  # Only redact if this reveals a user's home
            "aqi": idx.get("aqi"),
            "category": idx.get("category"),
            "dominantPollutant": idx.get("dominantPollutant")
        })
    }
    save_event(event)
    return [event]
