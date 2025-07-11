import json
import requests
import os
from dotenv import load_dotenv
from core.db import save_event
from datetime import datetime

load_dotenv()
GOOGLE_API_KEY = os.getenv("NEO_GOOGLE_KEY")

def get_events(max_results=1):
    url = f"https://weather.googleapis.com/v1/weather:lookup?key={GOOGLE_API_KEY}"
    params = {
        "location": {"latitude": -26.65, "longitude": 153.09},  # Replace as needed
        "fields": "currentWeather"
    }
    resp = requests.post(url, json=params)
    if not resp.ok:
        print("Weather API error:", resp.text)
        return []
    data = resp.json().get("currentWeather", {})
    now = datetime.utcnow().isoformat()
    event = {
        'raw_text': f"Weather: {data.get('summary', 'No data')}, {data.get('temperature', 'No data')}°C",
        'timestamp': now,
        'source': 'weather',
        'meta': json.dumps({
            "location": {"lat": -26.65, "lng": 153.09},   # Only redact if user-specific/home
            "temp_c": data.get("temperature"),
            "humidity": data.get("humidity"),
            "condition": data.get("summary")
        })
    }
    save_event(event)
    return [event]
