import json
from googleapiclient.discovery import build
from api.google_oauth import load_google_creds
from core.db import save_event
from datetime import datetime

def get_events(max_results=20):
    creds = load_google_creds()
    service = build('sheets', 'v4', credentials=creds)
    results = service.spreadsheets().get(spreadsheetId='your_spreadsheet_id').execute()  # Replace with actual ID(s) or iterate if needed
    event = {
        'raw_text': "Sheet metadata event.",
        'timestamp': datetime.utcnow().isoformat(),
        'source': 'sheets',
        'meta': json.dumps({
            'sheet_id': "[REDACTED]",
            'title': "[REDACTED]",
            'sheets': "[REDACTED]"
        })
    }
    save_event(event)
    return [event]
