import os.path
import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/calendar.readonly'
]

def authenticate_google():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    token_path = os.path.join(os.getcwd(), 'token.json')
    creds_path = os.path.join(os.getcwd(), 'credentials.json')
    
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                pass
        else:
            if not os.path.exists(creds_path):
                print("credentials.json not found. Please download it from Google Cloud Console.")
                return None
            
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            # Run local server for auth (requires browser on the Pi or port forwarding)
            creds = flow.run_local_server(port=0)
            
        # Save the credentials for the next run
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
            
    return creds

def google_action(service_name, action, params=None):
    """
    Interacts with Google APIs (Gmail, Calendar).
    """
    creds = authenticate_google()
    if not creds:
        return "Authentication with Google failed. Please ensure credentials.json is present."
        
    try:
        if service_name == "gmail":
            service = build('gmail', 'v1', credentials=creds)
            if action == "read_recent":
                # Call the Gmail API to fetch INBOX
                results = service.users().messages().list(userId='me', labelIds=['INBOX'], maxResults=5).execute()
                messages = results.get('messages', [])

                if not messages:
                    return 'No new messages found.'
                
                output = "Recent emails:\n"
                for msg in messages:
                    msg_data = service.users().messages().get(userId='me', id=msg['id'], format='metadata', metadataHeaders=['Subject', 'From']).execute()
                    headers = msg_data['payload']['headers']
                    subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                    sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
                    output += f"- From: {sender} | Subject: {subject}\n"
                return output
                
        elif service_name == "calendar":
            service = build('calendar', 'v3', credentials=creds)
            if action == "get_events":
                # Call the Calendar API
                now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
                events_result = service.events().list(calendarId='primary', timeMin=now,
                                                      maxResults=5, singleEvents=True,
                                                      orderBy='startTime').execute()
                events = events_result.get('items', [])

                if not events:
                    return 'No upcoming events found.'
                
                output = "Upcoming events:\n"
                for event in events:
                    start = event['start'].get('dateTime', event['start'].get('date'))
                    output += f"- {start}: {event['summary']}\n"
                return output
                
        return f"Unknown service '{service_name}' or action '{action}'."

    except HttpError as error:
        return f"An error occurred with Google APIs: {error}"


google_tool_schema = {
    "type": "function",
    "function": {
        "name": "google_action",
        "description": "Call this tool to interact with the user's Google Account (Gmail, Calendar).",
        "parameters": {
            "type": "object",
            "properties": {
                "service_name": {
                    "type": "string",
                    "enum": ["gmail", "calendar"],
                    "description": "The Google service to use."
                },
                "action": {
                    "type": "string",
                    "enum": ["read_recent", "get_events"],
                    "description": "The action to perform on the service."
                }
            },
            "required": ["service_name", "action"]
        }
    }
}
