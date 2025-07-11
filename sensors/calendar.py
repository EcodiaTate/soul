import json
from googleapiclient.discovery import build
from api.google_oauth import load_google_creds
from core.db import save_event
from datetime import datetime

def censor_summary(summary):
    if summary: return "[REDACTED]"
    return summary

def get_events(max_results=20):
    creds = load_google_creds()
    service = build('calendar', 'v3', credentials=creds)
    now = datetime.utcnow().isoformat() + 'Z'
    events_result = service.events().list(calendarId='primary', timeMin=now, maxResults=max_results, singleEvents=True, orderBy='startTime').execute()
    events = []
    for event_data in events_result.get('items', []):
        start = event_data.get('start', {}).get('dateTime', event_data.get('start', {}).get('date'))
        event = {
            'raw_text': event_data.get('description', ''),
            'timestamp': start,
            'source': 'calendar',
            'meta': json.dumps({
                'summary': censor_summary(event_data.get('summary')),
                'location': "[REDACTED]" if event_data.get('location') else None,
                'attendees': "[REDACTED]",
            })
        }
        save_event(event)
        events.append(event)
    return events
