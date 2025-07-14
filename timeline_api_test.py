# timeline_api_test.py

import requests
import time

BASE = "https://ecodia.au"  # Change to your deployed API base

def post_event():
    resp = requests.post(f"{BASE}/api/event", json={"text": "Timeline socket test event!"})
    print("POST /api/event:", resp.status_code, resp.json())

def get_timeline():
    resp = requests.get(f"{BASE}/api/timeline")
    print("GET /api/timeline:", resp.status_code)
    data = resp.json()
    for entry in data[:3]:
        print(f"{entry['timestamp']} | {entry['summary']}")

if __name__ == "__main__":
    post_event()
    time.sleep(2)  # Give backend time to process/promote
    get_timeline()
