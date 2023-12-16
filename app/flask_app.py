from flask import Flask, request, redirect
from google_auth_oauthlib.flow import Flow
import json
import os

app = Flask(__name__)

with open('./client_secret_413293732491-pdfv31n1tct9o1kdeace1qv1v03r7rt9.apps.googleusercontent.com.json','r') as json_file:
    client_config = json.load(json_file)

SCOPES = 'https://www.googleapis.com/auth/spreadsheets'
REDIRECT_URI = 'http://localhost:5000/oauth2callback'

# Route for initiating OAuth
@app.route('/authorize')
def authorize():
    # Create a flow instance to manage the OAuth 2.0 Authorization Grant Flow steps
    flow = Flow.from_client_config(
        client_config={
            "web": {
                "client_id": client_config['installed']['client_id'],
                "client_secret": client_config['installed']['client_secret'],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": REDIRECT_URI,
            }
        },
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )

    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )

    # You might want to store the state in a secure, user-specific way
    os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
    os.environ['OAUTH_STATE_KEY'] = state

    return redirect(authorization_url)

# OAuth2 callback route
@app.route('/oauth2callback')
def oauth2callback():
    state = os.environ.get('OAUTH_STATE_KEY', '')
    flow = Flow.from_client_config(
        client_config={
            "web": {
                "client_id": client_config['installed']['client_id'],
                "client_secret": client_config['installed']['client_secret'],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": REDIRECT_URI,
            }
        },
        scopes=SCOPES,
        state=state,
        redirect_uri=REDIRECT_URI
    )

    flow.fetch_token(authorization_response=request.url)

    credentials = flow.credentials

    # Here, you should securely store the credentials
    # And possibly associate them with a user

    return 'Authentication successful. You can close this tab.'
