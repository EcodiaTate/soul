# core/actuators/device.py — Environmental Actuation System
import requests
import json
from datetime import datetime
from core.logging_engine import log_action

# --- Known Devices ---
REGISTERED_DEVICES = {
    "eco_lamp": {
        "type": "light",
        "protocol": "MQTT",
        "address": "192.168.1.20"
    },
    "climate_modulator": {
        "type": "env",
        "protocol": "HTTP",
        "endpoint": "http://localhost:8000/trigger/state"
    }
}

SIGNAL_TYPES = ["pulse", "state_change", "broadcast"]
ENV_PRESETS = ["focus", "alert", "reflect", "offgrid"]

# --- Core Functions ---
def send_signal(device_id: str, signal_type: str, payload: dict) -> bool:
    """Send a structured signal to a known IoT or software-integrated device."""
    device = REGISTERED_DEVICES.get(device_id)
    if not device:
        log_action("device", "error", f"Unknown device: {device_id}")
        return False

    try:
        if device["protocol"] == "HTTP":
            response = requests.post(device["endpoint"], json={
                "type": signal_type,
                "payload": payload,
                "timestamp": datetime.utcnow().isoformat()
            })
            success = response.status_code in [200, 202]
        else:
            # Future: MQTT, WebSocket, etc.
            success = False

        log_action("device", "signal", f"Sent {signal_type} to {device_id}: {payload}")
        return success
    except Exception as e:
        log_action("device", "error", f"Signal to {device_id} failed: {e}")
        return False

def trigger_environmental_state_change(state_id: str) -> bool:
    """Activate a specific environmental preset (e.g., ‘focus mode’)."""
    if state_id not in ENV_PRESETS:
        log_action("device", "invalid_state", f"Tried to trigger unknown state: {state_id}")
        return False

    for dev_id in REGISTERED_DEVICES:
        if REGISTERED_DEVICES[dev_id]["type"] == "env":
            send_signal(dev_id, "state_change", {"state": state_id})
    
    log_action("device", "trigger_env", f"Set environment to: {state_id}")
    return True

def sync_with_sensor_feed(sensor_type: str, source_url: str) -> dict:
    """Retrieve external sensory data and attach to internal context."""
    try:
        response = requests.get(source_url)
        data = response.json()
        log_action("device", "sensor_sync", f"{sensor_type} data received: {data}")
        return data
    except Exception as e:
        log_action("device", "sensor_error", f"Failed to fetch sensor ({sensor_type}): {e}")
        return {"error": str(e)}
