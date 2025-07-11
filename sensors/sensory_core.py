# sensors/sensory_core.py

import uuid
from datetime import datetime
from core.db import save_event
from core.utils import get_embedding

class BaseSensor:
    """
    Every sensor inherits from this. Override fetch_events().
    Each event returned must be a dict matching the universal schema.
    """
    source_name = "base"

    def fetch_events(self):
        """
        Returns a list of normalized event dicts.
        """
        return []

    def normalize_event(self, raw_text, timestamp=None, meta=None):
        return {
            "event_id": str(uuid.uuid4()),
            "source": self.source_name,
            "raw_text": raw_text,
            "timestamp": timestamp or datetime.utcnow().isoformat(),
            "meta": meta or {},
        }


def run_all_sensors(sensor_classes):
    """
    Pass a list of sensor classes. Instantiates, fetches events, vectorizes, and stores each.
    """
    total = 0
    for SensorClass in sensor_classes:
        sensor = SensorClass()
        print(f"[SENSOR] Running {sensor.source_name}...")
        try:
            events = sensor.fetch_events()
            for event in events:
                # Deduplication: skip if already in Neo4j (by event_id or hash)
                if not save_event(event, dedupe=True):
                    continue
                total += 1
        except Exception as e:
            print(f"Error in {sensor.source_name}: {e}")
    print(f"[SENSOR] All sensors complete. {total} events ingested.")
