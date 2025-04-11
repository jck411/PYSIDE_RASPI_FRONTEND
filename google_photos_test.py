#!/usr/bin/env python3
import sys
import os
import pickle
import requests
import random
from datetime import datetime

from PySide6 import QtWidgets, QtGui, QtCore
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# OAuth scope and credentials file.
SCOPES = ["https://www.googleapis.com/auth/photoslibrary.readonly"]
CREDENTIALS_PATH = "/home/jack/PYSIDE_RASPI_FRONTEND/google_credentials.json"
TOKEN_PICKLE = "token.pickle"


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


def download_media_item(media, download_folder):
    """
    Download a media item (photo or video) to the specified folder.
    Determines the URL and file extension based on the mime type.
    Returns the local file path if successful.
    """
    mime = media.get("mimeType", "")
    if mime.startswith("image/"):
        ext = ".jpg"
        url = media.get("baseUrl") + "=w1280-h720"
    elif mime.startswith("video/"):
        ext = ".mp4"
        url = media.get("baseUrl") + "=dv"
    else:
        return None

    local_filename = os.path.join(download_folder, media.get("id") + ext)
    if os.path.exists(local_filename):
        print(f"File exists: {local_filename}")
        return local_filename

    try:
        print("Downloading media from:", url)
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(local_filename, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            print(f"Downloaded {local_filename}")
            return local_filename
        else:
            print("Failed to download media:", url, response.status_code)
            return None
    except Exception as e:
        print("Error downloading media:", e)
        return None


def download_all_media_items(media_items, download_folder):
    """Download all media items into the specified folder."""
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)
    for media in media_items:
        local_path = download_media_item(media, download_folder)
        if local_path:
            media["local_path"] = local_path


class PhotoWidget(QtWidgets.QWidget):
    """
    A widget that displays a photo with a blurred background and an overlay
    showing the full date in the bottom left.
    """

    def __init__(self, photo, parent=None):
        super().__init__(parent)
        self.photo = photo
        self.overlay_text = self.compute_overlay_text()
        # Load the pixmap from the local file.
        if "local_path" in photo:
            self.pixmap = QtGui.QPixmap(photo["local_path"])
        else:
            self.pixmap = None
        self.setMinimumSize(100, 100)

    def compute_overlay_text(self):
        metadata = self.photo.get("mediaMetadata", {})
        creation_time = metadata.get("creationTime", "")
        if creation_time:
            try:
                dt = datetime.fromisoformat(creation_time.replace("Z", "+00:00"))
                return dt.strftime("%A, %B %-d, %Y")
            except Exception as e:
                print("Error parsing creation time:", e)
        return ""

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)
        if self.pixmap:
            # Create a blurred background.
            small = self.pixmap.scaled(
                20, 20, QtCore.Qt.IgnoreAspectRatio, QtCore.Qt.SmoothTransformation
            )
            blurred = small.scaled(
                self.size(), QtCore.Qt.IgnoreAspectRatio, QtCore.Qt.SmoothTransformation
            )
            painter.drawPixmap(0, 0, blurred)
            # Draw the centered sharp image.
            scaled_pixmap = self.pixmap.scaled(
                self.size(), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation
            )
            x = (self.width() - scaled_pixmap.width()) // 2
            y = (self.height() - scaled_pixmap.height()) // 2
            painter.drawPixmap(x, y, scaled_pixmap)
        # Draw the overlay text.
        if self.overlay_text:
            margin = 10
            font = QtGui.QFont("Arial", 16)
            painter.setFont(font)
            metrics = QtGui.QFontMetrics(font)
            text_height = metrics.height()
            x_text = margin
            y_text = self.height() - margin
            shadow_offset = 2
            painter.setPen(QtGui.QColor(0, 0, 0, 160))
            painter.drawText(
                x_text + shadow_offset,
                y_text + shadow_offset - text_height // 4,
                self.overlay_text,
            )
            painter.setPen(QtGui.QColor(255, 255, 255))
            painter.drawText(x_text, y_text - text_height // 4, self.overlay_text)
        painter.end()


class VideoWidget(QtWidgets.QWidget):
    """
    A widget that plays a video from a local file using QMediaPlayer and QVideoWidget.
    Emits a 'finished' signal when the video finishes.
    """

    finished = QtCore.Signal()

    def __init__(self, media, parent=None):
        super().__init__(parent)
        self.media = media
        self.setMinimumSize(100, 100)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.video_widget = QVideoWidget(self)
        layout.addWidget(self.video_widget)
        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)
        self.player.setVideoOutput(self.video_widget)
        local_path = media.get("local_path")
        if local_path:
            self.player.setSource(QtCore.QUrl.fromLocalFile(local_path))
            self.player.play()
        else:
            print("Local video file not found.")
        self.player.mediaStatusChanged.connect(self.on_media_status_changed)

    def on_media_status_changed(self, status):
        if status == QMediaPlayer.EndOfMedia:
            self.finished.emit()

    def stop(self):
        self.player.stop()


def create_media_widget(media):
    """Return a PhotoWidget if media is a photo, or a VideoWidget if it's a video."""
    mime = media.get("mimeType", "")
    if mime.startswith("video/"):
        return VideoWidget(media)
    else:
        return PhotoWidget(media)


class SlideshowViewer(QtWidgets.QWidget):
    """
    A widget that displays a slideshow from the album.
    Photos transition automatically every 15 seconds with fade or slide effects,
    while videos play until finished. Clicking the widget advances immediately.
    """

    def __init__(self, media_items, service, album_id):
        super().__init__()
        self.media_items = media_items
        self.service = service
        self.album_id = album_id

        self.setWindowTitle("Test Album Slideshow")
        self.resize(1280, 800)
        self.container = QtWidgets.QStackedWidget(self)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.container)

        self.current_index = random.randint(0, len(self.media_items) - 1)
        self.current_widget = create_media_widget(self.media_items[self.current_index])
        self.container.addWidget(self.current_widget)
        self.container.setCurrentWidget(self.current_widget)
        self.connect_finished_signal(self.current_widget)

        self.transition_timer = QtCore.QTimer(self)
        self.transition_timer.timeout.connect(self.transition_media)
        if not isinstance(self.current_widget, VideoWidget):
            self.transition_timer.start(15000)

        self.update_timer = QtCore.QTimer(self)
        self.update_timer.timeout.connect(self.update_media_items)
        self.update_timer.start(300000)  # Update every 5 minutes

    def connect_finished_signal(self, widget):
        if isinstance(widget, VideoWidget):
            widget.finished.connect(self.transition_media)

    def mousePressEvent(self, event):
        self.transition_media()

    def update_media_items(self):
        print("Rescanning album for new media...")
        new_items = fetch_all_media_items(self.service, self.album_id)
        if new_items:
            self.media_items = new_items
            print(f"Album updated: {len(self.media_items)} items found.")

    def transition_media(self):
        if isinstance(self.current_widget, VideoWidget):
            if self.current_widget.player.mediaStatus() != QMediaPlayer.EndOfMedia:
                return
        if not self.media_items:
            return
        next_index = self.current_index
        if len(self.media_items) > 1:
            while next_index == self.current_index:
                next_index = random.randint(0, len(self.media_items) - 1)
        self.current_index = next_index
        next_media = self.media_items[self.current_index]
        self.next_widget = create_media_widget(next_media)
        self.container.addWidget(self.next_widget)
        self.connect_finished_signal(self.next_widget)
        if isinstance(self.next_widget, VideoWidget):
            self.transition_timer.stop()
        else:
            if not self.transition_timer.isActive():
                self.transition_timer.start(15000)
        effect = random.choice(["fade", "slide"])
        if effect == "fade":
            self.fade_transition()
        else:
            self.slide_transition()

    def fade_transition(self):
        effect_current = QtWidgets.QGraphicsOpacityEffect(self.current_widget)
        self.current_widget.setGraphicsEffect(effect_current)
        effect_next = QtWidgets.QGraphicsOpacityEffect(self.next_widget)
        self.next_widget.setGraphicsEffect(effect_next)
        anim_current = QtCore.QPropertyAnimation(effect_current, b"opacity")
        anim_current.setDuration(1000)
        anim_current.setStartValue(1.0)
        anim_current.setEndValue(0.0)
        anim_next = QtCore.QPropertyAnimation(effect_next, b"opacity")
        anim_next.setDuration(1000)
        anim_next.setStartValue(0.0)
        anim_next.setEndValue(1.0)
        self.anim_group = QtCore.QParallelAnimationGroup()
        self.anim_group.addAnimation(anim_current)
        self.anim_group.addAnimation(anim_next)
        self.anim_group.finished.connect(self.on_fade_finished)
        self.anim_group.start()

    def on_fade_finished(self):
        self.container.removeWidget(self.current_widget)
        self.current_widget.deleteLater()
        self.current_widget = self.next_widget
        self.next_widget = None
        self.container.setCurrentWidget(self.current_widget)

    def slide_transition(self):
        container_rect = self.container.geometry()
        width = container_rect.width()
        height = container_rect.height()
        current_geo = self.current_widget.geometry()
        direction = random.choice(["left", "right"])
        if direction == "left":
            start_geo_next = QtCore.QRect(width, 0, width, height)
            end_geo_current = QtCore.QRect(-width, 0, width, height)
        else:
            start_geo_next = QtCore.QRect(-width, 0, width, height)
            end_geo_current = QtCore.QRect(width, 0, width, height)
        self.next_widget.setGeometry(start_geo_next)
        self.container.setCurrentWidget(self.next_widget)
        anim_next = QtCore.QPropertyAnimation(self.next_widget, b"geometry")
        anim_next.setDuration(1000)
        anim_next.setStartValue(start_geo_next)
        anim_next.setEndValue(current_geo)
        anim_current = QtCore.QPropertyAnimation(self.current_widget, b"geometry")
        anim_current.setDuration(1000)
        anim_current.setStartValue(current_geo)
        anim_current.setEndValue(end_geo_current)
        self.anim_group = QtCore.QParallelAnimationGroup()
        self.anim_group.addAnimation(anim_next)
        self.anim_group.addAnimation(anim_current)
        self.anim_group.finished.connect(self.on_slide_finished)
        self.anim_group.start()

    def on_slide_finished(self):
        self.container.removeWidget(self.current_widget)
        self.current_widget.deleteLater()
        self.current_widget = self.next_widget
        self.next_widget = None
        self.current_widget.setGeometry(self.container.rect())
        self.container.setCurrentWidget(self.current_widget)


def main():
    creds = authenticate_google_photos()
    service = get_google_photos_service(creds)
    album = find_album_by_title(service, "test")
    if not album:
        print("Album 'test' not found.")
        sys.exit(1)
    media_items = fetch_all_media_items(service, album["id"])
    if not media_items:
        print("No media items found in album.")
        sys.exit(1)

    # Download all media items into a local folder.
    download_folder = os.path.join(os.path.dirname(__file__), "downloaded_media")
    print("Downloading all media items to:", download_folder)
    download_all_media_items(media_items, download_folder)

    app = QtWidgets.QApplication(sys.argv)
    viewer = SlideshowViewer(media_items, service, album["id"])
    viewer.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
