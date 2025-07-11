import json
import requests
import os
from dotenv import load_dotenv
from core.db import save_event
from datetime import datetime

load_dotenv()
GOOGLE_API_KEY = os.getenv("NEO_GOOGLE_KEY")

def get_events(max_results=1):
    url = f"https://solar.googleapis.com/v1/solarPotential:findClosest?key={GOOGLE_API_KEY}"
    params = {
        "location": {"latitude": -26.65, "longitude": 153.09}
    }
    resp = requests.post(url, json=params)
    if not resp.ok:
        print("Solar API error:", resp.text)
        return []
    data = resp.json().get("solarPotential", {})
    now = datetime.utcnow().isoformat()
    event = {
        'raw_text': f"Solar Potential: {data.get('maxSunshineHoursPerYear', 'No data')} hrs/year",
        'timestamp': now,
        'source': 'solar',
        'meta': json.dumps({
            "location": {"lat": -26.65, "lng": 153.09},  # Redact only if necessary
            "max_sunshine_hrs": data.get("maxSunshineHoursPerYear"),
            "panel_count": data.get("maxArrayPanelsCount"),
            "panel_kw": data.get("maxArrayPanelKw")
        })
    }
    save_event(event)
    return [event]
