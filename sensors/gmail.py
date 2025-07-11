import json
from googleapiclient.discovery import build
from api.google_oauth import load_google_creds
from core.db import save_event
from datetime import datetime
import email.utils

def censor_email(addr):
    """Censor email addresses: user@domain.com -> u***@d***.com"""
    if not addr or "@" not in addr: return addr
    user, dom = addr.split("@", 1)
    return f"{user[0]}***@{dom[0]}***.{dom.split('.')[-1]}"

def get_events(max_results=20):
    creds = load_google_creds()
    service = build('gmail', 'v1', credentials=creds)
    results = service.users().messages().list(userId='me', maxResults=max_results, q="in:anywhere").execute()
    messages = results.get('messages', [])
    events = []
    for msg in messages:
        msg_detail = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
        snippet = msg_detail.get('snippet', '')
        headers = {h['name']: h['value'] for h in msg_detail['payload'].get('headers', [])}
        date_header = headers.get('Date')
        try:
            timestamp = email.utils.parsedate_to_datetime(date_header).isoformat() if date_header else datetime.utcnow().isoformat()
        except Exception:
            timestamp = datetime.utcnow().isoformat()
        event = {
            'raw_text': snippet,
            'timestamp': timestamp,
            'source': 'gmail',
            'meta': json.dumps({
                'from': censor_email(headers.get('From')),
                'to': censor_email(headers.get('To')),
                'subject': "[REDACTED]",
                'labels': msg_detail.get('labelIds', [])
            })
        }
        save_event(event)
        events.append(event)
    return events
