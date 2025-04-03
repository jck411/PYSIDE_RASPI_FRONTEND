#!/usr/bin/env python3
import os
import sys
import pickle
import requests

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# OAuth scope and paths.
SCOPES = ['https://www.googleapis.com/auth/photoslibrary.readonly']
CREDENTIALS_PATH = '/home/human/AAREPOS/PYSIDE_RASPI_FRONTEND/google_photos_credentials.json'
TOKEN_PICKLE = 'token.pickle'
ALBUM_NAME = 'test'  # Change this to your desired album title.
DOWNLOAD_DIR = '/home/human/AAREPOS/PYSIDE_RASPI_FRONTEND/frontend/downloaded_media'

def authenticate_google_photos():
    """Authenticate with Google Photos using OAuth2."""
    creds = None
    if os.path.exists(TOKEN_PICKLE):
        with open(TOKEN_PICKLE, 'rb') as token:
            creds = pickle.load(token)
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
    """Build the Google Photos service client."""
    return build('photoslibrary', 'v1', credentials=creds, static_discovery=False)

def find_album_by_title(service, album_title):
    """Search for an album by title."""
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

def fetch_all_media_items(service, album_id):
    """Fetch all media items in the given album."""
    all_items = []
    next_page_token = None
    while True:
        body = {'albumId': album_id, 'pageSize': 100}
        if next_page_token:
            body['pageToken'] = next_page_token
        response = service.mediaItems().search(body=body).execute()
        all_items.extend(response.get('mediaItems', []))
        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break
    return all_items

def download_media_item(media, download_dir):
    """
    Download a media item (image or video) to the specified folder.
    For images, saves as JPEG; for videos, saves as MP4.
    """
    mime = media.get('mimeType', '')
    if mime.startswith("image/"):
        ext = ".jpg"
        url = media.get('baseUrl') + "=w1280-h720"
    elif mime.startswith("video/"):
        ext = ".mp4"
        url = media.get('baseUrl') + "=dv"
    else:
        print("Unsupported media type:", mime)
        return None
    
    filename = media.get('id') + ext
    file_path = os.path.join(download_dir, filename)
    if os.path.exists(file_path):
        print("File exists:", file_path)
        return file_path
    try:
        print("Downloading media from:", url)
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            print("Downloaded", file_path)
            return file_path
        else:
            print("Failed to download", url, "Status code:", response.status_code)
            return None
    except Exception as e:
        print("Error downloading", url, e)
        return None

def download_all_media_items(service, album, download_dir):
    """Download all images and videos from the specified album into download_dir."""
    album_id = album.get('id')
    media_items = fetch_all_media_items(service, album_id)
    print("Found", len(media_items), "media items in album", album.get('title'))
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)
    for media in media_items:
        if media.get('mimeType', '').startswith("image/") or media.get('mimeType', '').startswith("video/"):
            download_media_item(media, download_dir)

def main():
    creds = authenticate_google_photos()
    service = get_google_photos_service(creds)
    album = find_album_by_title(service, ALBUM_NAME)
    if not album:
        print(f"Album '{ALBUM_NAME}' not found.")
        sys.exit(1)
    download_all_media_items(service, album, DOWNLOAD_DIR)

if __name__ == '__main__':
    main()
