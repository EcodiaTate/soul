# core/actuators/gsheet.py — Google Sheets Integration
from google.oauth2 import service_account
from googleapiclient.discovery import build
from core.logging_engine import log_action
from datetime import datetime
import os

# --- Config ---
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
GOOGLE_CREDENTIALS_FILE = "secrets/gsheet_creds.json"

sheet_fields = ["timestamp", "type", "summary", "significance", "linked_nodes"]

# --- Service Auth ---
def _get_service():
    creds = service_account.Credentials.from_service_account_file(
        GOOGLE_CREDENTIALS_FILE, scopes=SCOPES
    )
    return build('sheets', 'v4', credentials=creds)

# --- Core Functions ---
def append_to_sheet(sheet_id: str, range_: str, values: list[list[str]]) -> bool:
    """Add a row of values to a specified Google Sheet range."""
    try:
        service = _get_service()
        body = {"values": values}
        service.spreadsheets().values().append(
            spreadsheetId=sheet_id,
            range=range_,
            valueInputOption="RAW",
            body=body
        ).execute()

        log_action("gsheet", "append", f"{len(values)} row(s) → {sheet_id}")
        return True
    except Exception as e:
        log_action("gsheet", "error", f"Failed to append: {e}")
        return False

def sync_timeline_to_sheet(sheet_id: str) -> bool:
    """Export recent timeline events to a readable sheet format."""
    from core.timeline_engine import get_timeline_entries
    entries = get_timeline_entries(limit=10)

    rows = []
    for e in entries:
        t = e["t"]
        row = [
            t.get("timestamp", ""),
            "timeline",
            t.get("summary", "")[:200],
            str(t.get("significance", "")),
            ", ".join(t.get("linked_events", []))
        ]
        rows.append(row)

    return append_to_sheet(sheet_id, "Sheet1!A1", rows)

def log_value_shift_to_sheet(sheet_id: str, value_data: dict) -> bool:
    """Push value realignments to a human-readable sheet for tracking."""
    row = [
        datetime.utcnow().isoformat(),
        "value_shift",
        value_data.get("description", ""),
        str(value_data.get("risk_score", "")),
        ", ".join(value_data.get("source_nodes", []))
    ]
    return append_to_sheet(sheet_id, "Sheet1!A1", [row])
