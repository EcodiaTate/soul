# sensors/all_inputs.py

import logging
from importlib import import_module

logging.basicConfig(level=logging.INFO, filename="logs/all_inputs.log")

# List the modules for all your inputs — just add more as you expand
DATA_SOURCES = [
    "sensors.gmail",
    "sensors.calendar",
    "sensors.drive",
    "sensors.sheets",
    "sensors.environment_weather",
    "sensors.environment_airquality",
    "sensors.environment_solar",
    "sensors.environment_pollen",
    "sensors.places",
    # Optional/future:
    # "sensors.news",
    # "sensors.wordpress",
    # "sensors.user_chat",
    "sensors.manual",
    "sensors.wordpress_db",
    # "sensors.other_thirdparty",
]

def get_all_live_events():
    """Aggregate all events from all registered data sources."""
    events = []
    for src_mod in DATA_SOURCES:
        try:
            mod = import_module(src_mod)
            if hasattr(mod, "get_events"):
                src_events = mod.get_events()
                events.extend(src_events)
                logging.info(f"Loaded {len(src_events)} events from {src_mod}")
            else:
                logging.warning(f"Module {src_mod} has no get_events()")
        except Exception as e:
            logging.error(f"Error in {src_mod}: {e}")
    return events

# === Example: For standalone test ===
if __name__ == "__main__":
    events = get_all_live_events()
    print(f"Total aggregated events: {len(events)}")
    if events: print(events[0])
