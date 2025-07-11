import json
from googleapiclient.discovery import build
from api.google_oauth import load_google_creds
from core.db import save_event
from datetime import datetime

def censor_filename(name):
    return "[REDACTED]"

def get_events(max_results=20):
    creds = load_google_creds()
    service = build('drive', 'v3', credentials=creds)
    results = service.files().list(pageSize=max_results, fields="files(id, name, mimeType, createdTime, modifiedTime)").execute()
    files = results.get('files', [])
    events = []
    for file in files:
        event = {
            'raw_text': f"Drive file created/modified: {file.get('mimeType', '')}",
            'timestamp': file.get('modifiedTime', file.get('createdTime', datetime.utcnow().isoformat())),
            'source': 'drive',
            'meta': json.dumps({
                'filename': censor_filename(file.get('name')),
                'file_id': "[REDACTED]",
                'mimeType': file.get('mimeType')
            })
        }
        save_event(event)
        events.append(event)
    return events
