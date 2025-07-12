import os
import json
from flask import Blueprint, redirect, url_for, session, request, jsonify
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials

TOKEN_FILE = os.path.join(os.path.dirname(__file__), 'google_tokens.json')

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
    # Add more as needed
]

bp = Blueprint('google_auth', __name__, url_prefix='/api/auth/google')

def load_google_credentials_dict():
    creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    if not creds_json:
        raise Exception("GOOGLE_CREDENTIALS_JSON env var not set")
    return json.loads(creds_json)

@bp.route('/login')
def login():
    client_config = load_google_credentials_dict()
    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=url_for('google_auth.callback', _external=True),
    )
    auth_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    session['oauth_state'] = state
    return redirect(auth_url)

@bp.route('/callback')
def callback():
    client_config = load_google_credentials_dict()
    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=url_for('google_auth.callback', _external=True),
        state=session['oauth_state']
    )
    flow.fetch_token(authorization_response=request.url)
    creds = flow.credentials
    # Save credentials to file for background use!
    with open(TOKEN_FILE, "w") as f:
        json.dump({
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": creds.scopes
        }, f)
    return jsonify({"status": "success", "detail": "Tokens saved. Ready for Gmail/Calendar API use."})

def load_google_creds():
    with open(TOKEN_FILE, "r") as f:
        data = json.load(f)
    return Credentials(**data)
