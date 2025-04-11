#!/usr/bin/env python3
import os
import sys
import pickle
import requests
import json
from PIL import Image, ImageFilter, ImageEnhance
from datetime import datetime

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# OAuth scope and paths.
SCOPES = ["https://www.googleapis.com/auth/photoslibrary.readonly"]
CREDENTIALS_PATH = "/home/jack/PYSIDE_RASPI_FRONTEND/google_credentials.json"
TOKEN_PICKLE = "token.pickle"
ALBUM_NAME = "test"  # Change this to your desired album title.
DOWNLOAD_DIR = "/home/jack/PYSIDE_RASPI_FRONTEND/frontend/downloaded_media"
METADATA_FILE = os.path.join(DOWNLOAD_DIR, "photo_metadata.json")


def authenticate_google_photos():
    """Authenticate with Google Photos using OAuth2."""
    creds = None
    if os.path.exists(TOKEN_PICKLE):
        with open(TOKEN_PICKLE, "rb") as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PICKLE, "wb") as token:
            pickle.dump(creds, token)
    return creds


def get_google_photos_service(creds):
    """Build the Google Photos service client."""
    return build("photoslibrary", "v1", credentials=creds, static_discovery=False)


def find_album_by_title(service, album_title):
    """Search for an album by title."""
    next_page_token = None
    while True:
        response = (
            service.albums().list(pageSize=50, pageToken=next_page_token).execute()
        )
        albums = response.get("albums", [])
        for album in albums:
            if album.get("title") == album_title:
                return album
        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break
    return None


def fetch_all_media_items(service, album_id):
    """Fetch all media items in the given album."""
    all_items = []
    next_page_token = None
    while True:
        body = {"albumId": album_id, "pageSize": 100}
        if next_page_token:
            body["pageToken"] = next_page_token
        response = service.mediaItems().search(body=body).execute()
        all_items.extend(response.get("mediaItems", []))
        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break
    return all_items


def create_blurred_background(image_path):
    """
    Create a blurred background version of the image

    Args:
        image_path: Path to the original image

    Returns:
        Path to the blurred image
    """
    try:
        # Skip if not an image
        if not image_path.lower().endswith((".jpg", ".jpeg", ".png")):
            print(f"Skipping non-image file for blur: {image_path}")
            return None

        # Create output path for the blurred image
        filename = os.path.basename(image_path)
        name, ext = os.path.splitext(filename)
        # Always use JPG for blurred backgrounds (no need for transparency)
        blurred_filename = f"{name}_blurred.jpg"
        blurred_path = os.path.join(os.path.dirname(image_path), blurred_filename)

        # Check if blurred version already exists
        if os.path.exists(blurred_path):
            print(f"Blurred background already exists: {blurred_path}")
            return blurred_path

        # Open the image
        print(f"Creating blurred background for: {image_path}")
        img = Image.open(image_path)

        # Convert to RGB mode if needed
        if img.mode != "RGB":
            img = img.convert("RGB")

        # Create a low-resolution version first (for faster processing)
        small_size = (20, 20)
        small = img.resize(small_size, Image.LANCZOS)

        # Scale back up to create pixelation effect
        blurred = small.resize(img.size, Image.LANCZOS)

        # Apply additional Gaussian blur
        blurred = blurred.filter(ImageFilter.GaussianBlur(radius=5))

        # Darken the image for better contrast with foreground content
        enhancer = ImageEnhance.Brightness(blurred)
        blurred = enhancer.enhance(0.7)  # 70% brightness

        # Save the blurred image
        blurred.save(blurred_path, quality=90)
        print(f"Saved blurred background to: {blurred_path}")

        return blurred_path

    except Exception as e:
        print(f"Error creating blurred background for {image_path}: {e}")
        return None


def format_creation_date(creation_time):
    """Format creation date to a user-friendly string."""
    if not creation_time:
        return ""

    try:
        # Parse the ISO date string from Google Photos
        dt = datetime.fromisoformat(creation_time.replace("Z", "+00:00"))
        # Format as "Thursday, April 3, 2025"
        return dt.strftime("%A, %B %-d, %Y")
    except Exception as e:
        print(f"Error formatting date {creation_time}: {e}")
        return ""


def save_metadata(metadata_dict):
    """Save metadata to a JSON file."""
    try:
        with open(METADATA_FILE, "w") as f:
            json.dump(metadata_dict, f, indent=2)
        print(f"Saved metadata to {METADATA_FILE}")
    except Exception as e:
        print(f"Error saving metadata: {e}")


def load_metadata():
    """Load metadata from the JSON file if it exists."""
    if os.path.exists(METADATA_FILE):
        try:
            with open(METADATA_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading metadata: {e}")
    return {}


def download_media_item(media, download_dir, metadata_dict):
    """
    Download a media item (image or video) to the specified folder.
    For images, saves as JPEG; for videos, saves as MP4.
    """
    mime = media.get("mimeType", "")
    if mime.startswith("image/"):
        ext = ".jpg"
        url = media.get("baseUrl") + "=w1280-h720"
    elif mime.startswith("video/"):
        ext = ".mp4"
        url = media.get("baseUrl") + "=dv"
    else:
        print("Unsupported media type:", mime)
        return None

    filename = media.get("id") + ext
    file_path = os.path.join(download_dir, filename)

    # Extract and format the creation date/time
    creation_time = media.get("mediaMetadata", {}).get("creationTime", "")
    formatted_date = format_creation_date(creation_time)

    # Store the metadata
    metadata_dict[filename] = {
        "date": formatted_date,
        "title": media.get("filename", ""),
        "description": media.get("description", ""),
        "creation_time": creation_time,
    }

    if os.path.exists(file_path):
        print("File exists:", file_path)
        # For images, create blurred background if it doesn't exist yet
        if mime.startswith("image/"):
            create_blurred_background(file_path)
        return file_path
    try:
        print("Downloading media from:", url)
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            print("Downloaded", file_path)

            # For images, create a blurred background version
            if mime.startswith("image/"):
                create_blurred_background(file_path)

            return file_path
        else:
            print("Failed to download", url, "Status code:", response.status_code)
            return None
    except Exception as e:
        print("Error downloading", url, e)
        return None


def download_all_media_items(service, album, download_dir):
    """Download all images and videos from the specified album into download_dir."""
    album_id = album.get("id")
    media_items = fetch_all_media_items(service, album_id)
    print("Found", len(media_items), "media items in album", album.get("title"))

    if not os.path.exists(download_dir):
        os.makedirs(download_dir)

    # Load existing metadata
    metadata_dict = load_metadata()

    for media in media_items:
        if media.get("mimeType", "").startswith("image/") or media.get(
            "mimeType", ""
        ).startswith("video/"):
            download_media_item(media, download_dir, metadata_dict)

    # Save updated metadata
    save_metadata(metadata_dict)


def main():
    creds = authenticate_google_photos()
    service = get_google_photos_service(creds)
    album = find_album_by_title(service, ALBUM_NAME)
    if not album:
        print(f"Album '{ALBUM_NAME}' not found.")
        sys.exit(1)
    download_all_media_items(service, album, DOWNLOAD_DIR)


if __name__ == "__main__":
    main()
