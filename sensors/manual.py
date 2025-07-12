import csv
import os
from core.db import save_event
from datetime import datetime

CSV_FILE = os.getenv("MANUAL_CSV_PATH", "manual_events.csv")  # Set this path in .env if needed

def get_events(max_results=None):
    events = []
    with open(CSV_FILE, newline='', encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for i, row in enumerate(reader):
            # Get and parse labels from CSV, always include "unprocessed"
            csv_labels = row.get("labels", "")
            label_list = [lbl.strip() for lbl in csv_labels.split(",") if lbl.strip()] if csv_labels else []
            if "unprocessed" not in label_list:
                label_list.append("unprocessed")

            event = {
                "raw_text": row.get("raw_text") or row.get("summary") or row.get("Summary", ""),
                "timestamp": row.get("timestamp") or datetime.utcnow().isoformat(),
                "source": row.get("source") or "manual",
                "_labels": label_list,
                "meta": {k: v for k, v in row.items() if k not in ["raw_text", "summary", "Summary", "timestamp", "source", "labels"]}
            }
            save_event(event)
            events.append(event)
            if max_results and len(events) >= max_results:
                break
    return events

# Example usage/test
if __name__ == "__main__":
    events = get_events()
    print(f"Ingested {len(events)} manual events.")
