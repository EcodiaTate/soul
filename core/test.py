# test.py
import requests
import time

BASE = "https://ecodia.au"

def post_event(text):
    res = requests.post(f"{BASE}/api/event", json={"text": text})
    print("POST /api/event:", res.status_code, res.json())
    return res.json()

def get_timeline():
    res = requests.get(f"{BASE}/api/timeline")
    print("GET /api/timeline:", res.status_code)
    data = res.json()
    print(f"Timeline entries: {len(data)}")
    for entry in data[:3]:  # print latest 3
        print(f"- {entry['timestamp']} | {entry['summary']}")
    return data

if __name__ == "__main__":
    print("Testing POST /api/event...")
    post_event("Memory test: This should show up on the timeline!")
    time.sleep(2)  # give backend a sec to process

    print("\nTesting GET /api/timeline...")
    get_timeline()
