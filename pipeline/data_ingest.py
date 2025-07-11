import requests
import csv
import os
import logging
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, filename="logs/data_ingest.log")
load_dotenv()

API_URL = os.environ.get("ECODIA_API_URL", "http://localhost:5001/api/event")

def ingest_csv(filename):
    if not os.path.exists(filename):
        logging.error(f"CSV file not found: {filename}")
        return

    with open(filename, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for idx, row in enumerate(reader):
            event_id = row.get("id") or f"row_{idx}"
            raw_text = row.get("summary") or row.get("description") or ""
            if not raw_text:
                logging.warning(f"Row {idx} has no summary/description, skipping.")
                continue
            event = {
                "id": event_id,
                "timestamp": row.get("timestamp"),
                "raw_text": raw_text,
                "status": "unprocessed",
                "_labels": ["Event", "Raw", "Imported"]
            }
            try:
                resp = requests.post(API_URL, json=event, timeout=10)
                if resp.status_code == 200:
                    logging.info(f"Event {event['id']} imported.")
                else:
                    logging.error(f"Event {event['id']} import failed: {resp.status_code} {resp.text}")
            except Exception as e:
                logging.error(f"Event {event['id']} import failed: {e}")

if __name__ == "__main__":
    filename = "path_to_your_data.csv"
    ingest_csv(filename)
