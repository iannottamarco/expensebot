from .models import UserGoogleSheetsCredentials
from .db_utils import Session, add_to_session_and_close
from .flask_app import REDIRECT_URI
import logging
logging.basicConfig(filename='./logs/mylogs.log',
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
CREDENTIALS_FILE = './client_secret_413293732491-pdfv31n1tct9o1kdeace1qv1v03r7rt9.apps.googleusercontent.com.json'


# Add user info
def add_basicinfo(user_id, spreadsheet_id, sheet_name):
    session = Session()
    try:
        spreadsheet = UserGoogleSheetsCredentials(user_id=user_id,spreadsheet_id=spreadsheet_id,sheet_name=sheet_name)
        add_to_session_and_close(session,spreadsheet)
        logging.info(f'Spreadsheet info added by user:{user_id} : {spreadsheet_id}')
        return spreadsheet
    except Exception as e:
        session.rollback()
        logging.error(f'Error adding spreadsheet of user:{user_id}: {e}')
        return None
    finally:
        session.close()

# Extract Spreadsheet id from link
def extract_spreadsheet_id(input_string):
    if "docs.google.com/spreadsheets" in input_string:
        parts = input_string.split('/')
        return max(parts, key=len, default=None)
    else:
        try:
            len(input_string) > 20
            return input_string
        except:
            return None

def get_google_auth_url():
    flow = InstalledAppFlow.from_client_secrets_file(
        CREDENTIALS_FILE, 
        SCOPES,
        redirect_uri=REDIRECT_URI
    )
    auth_url, _ = flow.authorization_url(
        access_type='offline', 
        include_granted_scopes='true'
    )
    return auth_url

print(get_google_auth_url())