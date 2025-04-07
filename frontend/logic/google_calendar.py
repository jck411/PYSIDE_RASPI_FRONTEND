import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import pickle
from pathlib import Path

class GoogleCalendarClient:
    """Handles Google Calendar API authentication and operations."""
    
    # If modifying these scopes, delete the file token.pickle.
    SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
    
    # Blocklist for calendars we want to exclude
    BLOCKED_CALENDAR_NAMES = [
        "Holidays in Australia",
        "weather for Orlando",
        "Weather in Orlando",  # Adding alternate name variation
        "Weather for Orlando"  # Adding capitalized variation
    ]
    
    # Display name mapping for calendars
    DISPLAY_NAME_MAPPING = {
        "jck411@gmail.com": "Dad",
        "Mom Work Schedule": "Mom Work",
        "Dad Work Schedule": "Dad Work"
    }
    
    def __init__(self):
        self.credentials = None
        self.service = None
        self.token_path = Path.home() / '.config' / 'pyside_raspi' / 'token.pickle'
        # Use the existing credentials file
        self.credentials_path = Path("/home/human/AAREPOS/PYSIDE_RASPI_FRONTEND/google_photos_credentials.json")
        
        # Ensure config directory exists
        self.token_path.parent.mkdir(parents=True, exist_ok=True)
        
    def authenticate(self):
        """Authenticate with Google Calendar API."""
        if os.path.exists(self.token_path):
            with open(self.token_path, 'rb') as token:
                self.credentials = pickle.load(token)
        
        # If credentials are invalid or don't exist, let the user log in
        if not self.credentials or not self.credentials.valid:
            if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                self.credentials.refresh(Request())
            else:
                if not os.path.exists(self.credentials_path):
                    raise FileNotFoundError(
                        f"Credentials file not found at {self.credentials_path}. "
                        "Please ensure the google_photos_credentials.json file exists."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, self.SCOPES)
                self.credentials = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open(self.token_path, 'wb') as token:
                pickle.dump(self.credentials, token)
        
        self.service = build('calendar', 'v3', credentials=self.credentials)
        return True
    
    def get_calendars(self):
        """Get list of user's calendars."""
        if not self.service:
            self.authenticate()
        
        calendars = []
        page_token = None
        while True:
            calendar_list = self.service.calendarList().list(
                pageToken=page_token,
                fields='items(id,summary,backgroundColor)'
            ).execute()
            
            for calendar in calendar_list.get('items', []):
                # Skip calendars in the blocklist
                if calendar['summary'] in self.BLOCKED_CALENDAR_NAMES:
                    print(f"Skipping blocked calendar: {calendar['summary']}")
                    continue
                
                # Use display name mapping if available
                original_name = calendar['summary']
                display_name = self.DISPLAY_NAME_MAPPING.get(original_name, original_name)
                
                calendars.append({
                    'id': calendar['id'],
                    'name': display_name,  # Use the mapped display name
                    'original_name': original_name,  # Keep the original name for reference
                    'color': calendar.get('backgroundColor', '#1a73e8')  # Default Google blue
                })
            
            page_token = calendar_list.get('nextPageToken')
            if not page_token:
                break
        
        return calendars
    
    def get_events(self, calendar_id, time_min, time_max):
        """Get events for a specific calendar within a time range."""
        if not self.service:
            self.authenticate()
        
        events = []
        page_token = None
        while True:
            events_result = self.service.events().list(
                calendarId=calendar_id,
                timeMin=time_min.isoformat() + 'Z',
                timeMax=time_max.isoformat() + 'Z',
                singleEvents=True,
                orderBy='startTime',
                pageToken=page_token,
                fields='items(id,summary,start,end,colorId)'
            ).execute()
            
            for event in events_result.get('items', []):
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                
                events.append({
                    'id': event['id'],
                    'calendar_id': calendar_id,
                    'title': event['summary'],
                    'start_time': start,
                    'end_time': end,
                    'all_day': 'date' in event['start'],
                    'color': event.get('colorId', None)  # Will be mapped to actual color in controller
                })
            
            page_token = events_result.get('nextPageToken')
            if not page_token:
                break
        
        return events 