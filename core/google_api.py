# core/google_api.py — Google Integration Layer
from google.oauth2 import service_account
from googleapiclient.discovery import build
import requests
import os
from datetime import datetime
from core.logging_engine import log_action

# --- Config ---
GOOGLE_CREDS_PATH = "secrets/google_creds.json"
GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/maps-platform"
]

calendar_defaults = {
    "calendarId": "primary",
    "timeZone": "Australia/Brisbane"
}

# --- Auth Service Generator ---
def _get_google_service(service_name: str, version: str):
    creds = service_account.Credentials.from_service_account_file(
        GOOGLE_CREDS_PATH,
        scopes=GOOGLE_SCOPES
    )
    return build(service_name, version, credentials=creds)

# --- Calendar API ---
def add_calendar_event(title: str, start_time: str, end_time: str, description: str = "") -> bool:
    """Create a Google Calendar event tied to a system milestone or simulation."""
    try:
        service = _get_google_service("calendar", "v3")
        event = {
            "summary": title,
            "description": description,
            "start": {"dateTime": start_time, "timeZone": calendar_defaults["timeZone"]},
            "end": {"dateTime": end_time, "timeZone": calendar_defaults["timeZone"]}
        }
        service.events().insert(calendarId=calendar_defaults["calendarId"], body=event).execute()
        log_action("google_api", "calendar_event", f"Created event: {title}")
        return True
    except Exception as e:
        log_action("google_api", "calendar_error", str(e))
        return False

# --- Sheets API ---
def fetch_sheet_data(sheet_id: str, range_: str) -> list[list[str]]:
    """Read structured data from a given sheet range."""
    try:
        service = _get_google_service("sheets", "v4")
        result = service.spreadsheets().values().get(spreadsheetId=sheet_id, range=range_).execute()
        data = result.get("values", [])
        log_action("google_api", "sheet_read", f"Read {len(data)} rows from {sheet_id}")
        return data
    except Exception as e:
        log_action("google_api", "sheet_error", str(e))
        return []

# --- Maps API ---
def get_geocode(address: str) -> dict:
    """Resolve a human-readable address into lat/lng via Google Maps API."""
    try:
        api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={api_key}"
        response = requests.get(url)
        data = response.json()
        if data["status"] == "OK":
            result = data["results"][0]["geometry"]["location"]
            log_action("google_api", "geocode", f"{address} → {result}")
            return result
        else:
            raise Exception(data["status"])
    except Exception as e:
        log_action("google_api", "geocode_error", f"{address}: {e}")
        return {}

def get_place_context(lat: float, lng: float) -> dict:
    """Fetch place name, type, and context from lat/lng coordinates."""
    try:
        api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lng}&key={api_key}"
        response = requests.get(url)
        data = response.json()
        if data["status"] == "OK":
            result = data["results"][0]
            log_action("google_api", "reverse_geocode", f"{lat},{lng} → {result['formatted_address']}")
            return {
                "address": result["formatted_address"],
                "place_type": result["types"]
            }
        else:
            raise Exception(data["status"])
    except Exception as e:
        log_action("google_api", "place_context_error", f"{lat},{lng}: {e}")
        return {}
