import sys
import os
import pickle
import requests

from PySide6 import QtWidgets, QtGui

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Define the scope required to read your Google Photos.
SCOPES = ['https://www.googleapis.com/auth/photoslibrary.readonly']

# Update the path to your credentials file
CREDENTIALS_PATH = '/home/jack/PYSIDE_RASPI_FRONTEND/google_photos_credentials.json'
TOKEN_PICKLE = 'token.pickle'

def authenticate_google_photos():
    """
    Authenticate with Google Photos using OAuth2.
    Uses credentials file at CREDENTIALS_PATH and saves token as TOKEN_PICKLE.
    """
    creds = None
    if os.path.exists(TOKEN_PICKLE):
        with open(TOKEN_PICKLE, 'rb') as token:
            creds = pickle.load(token)
    # If there are no valid credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PICKLE, 'wb') as token:
            pickle.dump(creds, token)
    return creds

def get_google_photos_service(creds):
    """
    Build the Google Photos service client.
    """
    service = build('photoslibrary', 'v1', credentials=creds, static_discovery=False)
    return service

def find_album_by_title(service, album_title):
    """
    Searches for an album with the specified title.
    Returns the album object if found, otherwise None.
    """
    next_page_token = None
    while True:
        response = service.albums().list(pageSize=50, pageToken=next_page_token).execute()
        albums = response.get('albums', [])
        for album in albums:
            if album.get('title') == album_title:
                return album
        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break
    return None

def fetch_media_items_from_album(service, album_id, page_size=20):
    """
    Fetches media items from a specific album using its album_id.
    """
    response = service.mediaItems().search(body={
        'albumId': album_id,
        'pageSize': page_size
    }).execute()
    return response.get('mediaItems', [])

class PhotoViewer(QtWidgets.QWidget):
    """
    A simple PySide6 widget to display photos in a scrollable layout.
    """
    def __init__(self, photos):
        super().__init__()
        self.setWindowTitle("Album: Zoe")
        self.layout = QtWidgets.QVBoxLayout(self)
        
        scroll_area = QtWidgets.QScrollArea()
        scroll_widget = QtWidgets.QWidget()
        scroll_layout = QtWidgets.QVBoxLayout(scroll_widget)
        
        for photo in photos:
            url = photo.get('baseUrl')
            if url:
                # Optionally, add parameters to resize (e.g., '=w800-h600')
                image_data = self.get_image_from_url(url + "=w800-h600")
                if image_data:
                    pixmap = QtGui.QPixmap()
                    pixmap.loadFromData(image_data)
                    label = QtWidgets.QLabel()
                    label.setPixmap(pixmap)
                    label.setScaledContents(True)
                    # Optionally, set a maximum height for each image
                    label.setMaximumHeight(600)
                    scroll_layout.addWidget(label)
        
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        self.layout.addWidget(scroll_area)
        self.resize(800, 600)
    
    def get_image_from_url(self, url):
        """
        Downloads image data from the given URL.
        """
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.content
        except Exception as e:
            print("Error fetching image:", e)
        return None

def main():
    # Authenticate and build the service
    creds = authenticate_google_photos()
    service = get_google_photos_service(creds)
    
    # Search for the "Zoe" album
    album_title = "Zoe"
    album = find_album_by_title(service, album_title)
    
    if not album:
        print(f"Album '{album_title}' not found.")
        sys.exit(1)
    
    album_id = album.get('id')
    print(f"Found album '{album_title}' with id: {album_id}")
    
    # Fetch media items from the album
    photos = fetch_media_items_from_album(service, album_id, page_size=50)
    if not photos:
        print("No photos found in the album.")
        sys.exit(1)
    
    # Start the PySide6 application and display the photos
    app = QtWidgets.QApplication(sys.argv)
    viewer = PhotoViewer(photos)
    viewer.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
