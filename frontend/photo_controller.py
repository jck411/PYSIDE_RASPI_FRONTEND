from PySide6.QtCore import QObject, Slot, Signal, Property, QTimer
import os
import json
import logging
from .photo_processor import PhotoProcessor

logger = logging.getLogger("frontend.photo_controller")


class PhotoController(QObject):
    """Controller for the photo screen that manages photo and video slideshow"""

    # Signal when current media changes (path, isVideo)
    currentMediaChanged = Signal(str, bool)

    # Signal when slideshow state changes
    slideshowRunningChanged = Signal(bool)

    # Signal when a blurred background image is ready
    blurredBackgroundChanged = Signal(str)

    # Signal when the date metadata changes
    dateTextChanged = Signal(str)

    def __init__(self):
        super().__init__()
        self.media_folder = (
            "/home/jack/PYSIDE_RASPI_FRONTEND/frontend/downloaded_media"
        )
        self.metadata_file = os.path.join(self.media_folder, "photo_metadata.json")
        self.metadata = {}
        self.media_files = []
        self.current_index = 0
        self._is_running = False
        self._current_blurred_bg = ""
        self._current_date_text = ""
        self._user_paused = False # Flag to track user-initiated pause
        
        # Load metadata if it exists
        self.load_metadata()

        # Create the photo processor for adding effects
        self.photo_processor = PhotoProcessor()

        # Timer for auto-advancing images
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.show_next_media)
        self.timer.setInterval(5000)  # 5 seconds for images

        # Load media files
        self.load_media_files()
        logger.info("PhotoController initialized")

    def load_metadata(self):
        """Load metadata from the JSON file if it exists."""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, "r") as f:
                    self.metadata = json.load(f)
                logger.info(f"Loaded metadata for {len(self.metadata)} media items")
            except Exception as e:
                logger.error(f"Error loading metadata: {e}")
                self.metadata = {}
        else:
            logger.warning(f"Metadata file not found: {self.metadata_file}")
            self.metadata = {}

    def load_media_files(self):
        """Load all media files from the specified folder"""
        try:
            if os.path.exists(self.media_folder):
                self.media_files = []
                for filename in os.listdir(self.media_folder):
                    # Skip blurred background images (ending with _blurred.jpg)
                    if filename.endswith("_blurred.jpg"):
                        continue
                    # Skip the metadata file
                    if filename == "photo_metadata.json":
                        continue
                    # Skip Python scripts
                    if filename.endswith(".py"):
                        continue

                    file_path = os.path.join(self.media_folder, filename)
                    if filename.lower().endswith(
                        (".jpg", ".jpeg", ".png", ".mp4", ".mov", ".webm")
                    ):
                        is_video = filename.lower().endswith((".mp4", ".mov", ".webm"))
                        self.media_files.append((file_path, is_video))

                # Sort files by name - this ensures a consistent order
                self.media_files.sort(key=lambda x: x[0])

                logger.info(
                    f"Loaded {len(self.media_files)} media files from {self.media_folder}"
                )

                # Emit the first media item
                if self.media_files:
                    self.currentMediaChanged.emit(
                        self.media_files[0][0], self.media_files[0][1]
                    )
            else:
                logger.error(f"Media folder does not exist: {self.media_folder}")
        except Exception as e:
            logger.error(f"Error loading media files: {e}")

    def get_date_for_file(self, file_path):
        """Get the date from metadata for a file."""
        if not file_path:
            return ""

        filename = os.path.basename(file_path)
        if filename in self.metadata:
            return self.metadata[filename].get("date", "")
        return ""

    @Slot()
    def start_slideshow(self):
        """Start the slideshow timer"""
        if self.media_files:
            # Clear the image cache to ensure fresh processing
            self.photo_processor.clear_cache()

            # Immediately emit the current media item to ensure something is displayed
            current_path, is_video = self.media_files[self.current_index]

            # Process the image before sending to UI
            processed_path = self.process_media_path(current_path, is_video)

            # Update date text
            self.update_date_text(current_path)

            # Create and emit blurred background if this is an image
            if not is_video:
                self.find_blurred_background(current_path)

            # Emit the new media item
            self.currentMediaChanged.emit(processed_path, is_video)

            # Start the timer for automatic advancement
            self.timer.start()
            self._is_running = True
            self._user_paused = False # Reset user pause flag when starting
            self.slideshowRunningChanged.emit(True)
            logger.info("Slideshow started")

    def update_date_text(self, file_path):
        """Update the date text for the current file."""
        date_text = self.get_date_for_file(file_path)
        if date_text != self._current_date_text:
            self._current_date_text = date_text
            self.dateTextChanged.emit(date_text)

    @Slot()
    def stop_slideshow(self):
        """Stop the slideshow timer"""
        self.timer.stop()
        self._is_running = False
        self._user_paused = True # Set user pause flag when stopping via controls/cleanup
        self.slideshowRunningChanged.emit(False)
        logger.info("Slideshow stopped")

    @Slot()
    def show_next_media(self):
        """Show the next media item in the slideshow"""
        if not self.media_files:
            return

        # If current item is a video, don't auto-advance
        current_path, is_video = self.media_files[self.current_index]
        if is_video:
            return

        self.advance_to_next()

    @Slot(bool)
    def set_dark_mode(self, is_dark_mode):
        """Update the processor with current theme info"""
        self.is_dark_mode = is_dark_mode
        logger.info(f"Dark mode set to {is_dark_mode}")

        # If we're currently displaying an image, refresh it
        if self.media_files:
            current_path, is_video = self.media_files[self.current_index]
            if not is_video:
                self.currentMediaChanged.emit(current_path, is_video)

    def process_media_path(self, media_path, is_video):
        """Apply effects to image files before sending to the UI"""
        if is_video:
            # Don't process videos
            return media_path
        else:
            # Apply shadow effect to images
            return self.photo_processor.add_shadow_effect(
                media_path, getattr(self, "is_dark_mode", False)
            )

    def find_blurred_background(self, image_path):
        """Find or create a blurred background version of the current image"""
        if not image_path or not os.path.exists(image_path):
            logger.error(
                f"Cannot find blurred background: Invalid image path {image_path}"
            )
            return

        try:
            # First check if there's already a pre-generated blurred version
            filename = os.path.basename(image_path)
            name, ext = os.path.splitext(filename)
            blurred_filename = f"{name}_blurred.jpg"
            blurred_path = os.path.join(os.path.dirname(image_path), blurred_filename)

            if os.path.exists(blurred_path):
                # Use the pre-generated blurred background
                self._current_blurred_bg = blurred_path
                self.blurredBackgroundChanged.emit(blurred_path)
                logger.info(f"Using pre-generated blurred background: {blurred_path}")
                return

            # If no pre-generated version exists, create one on-the-fly
            blurred_path = self.photo_processor.create_blurred_background(image_path)

            if blurred_path and os.path.exists(blurred_path):
                self._current_blurred_bg = blurred_path
                # Emit signal with the path to the blurred image
                self.blurredBackgroundChanged.emit(blurred_path)
                logger.info(f"Created blurred background: {blurred_path}")
            else:
                logger.error("Failed to create blurred background")
        except Exception as e:
            logger.error(f"Error finding/creating blurred background: {e}")

    @Slot()
    def advance_to_next(self):
        """Manually advance to the next media item"""
        if not self.media_files:
            return

        # Simple index advancement in the fixed order
        self.current_index = (self.current_index + 1) % len(self.media_files)
        current_path, is_video = self.media_files[self.current_index]

        # Process the image before sending to UI
        processed_path = self.process_media_path(current_path, is_video)

        # Update date text
        self.update_date_text(current_path)

        # Create and emit blurred background if this is an image
        if not is_video:
            self.find_blurred_background(current_path)

        # Emit the new media item
        self.currentMediaChanged.emit(processed_path, is_video)
        logger.debug(
            f"Showing media {self.current_index + 1}/{len(self.media_files)}: {processed_path}"
        )

    @Slot()
    def go_to_previous(self):
        """Go to the previous media item"""
        if not self.media_files:
            return

        # Simple previous in the fixed order
        self.current_index = (self.current_index - 1) % len(self.media_files)
        current_path, is_video = self.media_files[self.current_index]

        # Process the image before sending to UI
        processed_path = self.process_media_path(current_path, is_video)

        # Update date text
        self.update_date_text(current_path)

        # Create and emit blurred background if this is an image
        if not is_video:
            self.find_blurred_background(current_path)

        # Emit the new media item
        self.currentMediaChanged.emit(processed_path, is_video)
        logger.debug(
            f"Showing media {self.current_index + 1}/{len(self.media_files)}: {processed_path}"
        )
        
    @Slot(int)
    def go_to_specific_index(self, index):
        """Go to a specific media item by index"""
        if not self.media_files or index < 0 or index >= len(self.media_files):
            logger.error(f"Invalid index {index} for media files of length {len(self.media_files)}")
            return

        # Set current index to the specified index
        self.current_index = index
        current_path, is_video = self.media_files[self.current_index]

        # Process the image before sending to UI
        processed_path = self.process_media_path(current_path, is_video)

        # Update date text
        self.update_date_text(current_path)

        # Create and emit blurred background if this is an image
        if not is_video:
            self.find_blurred_background(current_path)

        # Emit the new media item
        self.currentMediaChanged.emit(processed_path, is_video)
        logger.debug(
            f"Direct jump to media {self.current_index + 1}/{len(self.media_files)}: {processed_path}"
        )

    @Slot()
    def video_finished(self):
        """Called when a video finishes playing"""
        logger.info("Video finished playing")
        self.advance_to_next()

    @Property(bool, notify=slideshowRunningChanged)
    def is_running(self):
        """Return whether the slideshow is currently running"""
        return self._is_running

    @Property(str, notify=blurredBackgroundChanged)
    def current_blurred_background(self):
        """Return the path to the current blurred background image"""
        return self._current_blurred_bg

    @Property(str, notify=dateTextChanged)
    def current_date_text(self):
        """Return the date text for the current media"""
        return self._current_date_text

    @Slot()
    def pause_timer(self):
        """Pause the automatic advancement timer (e.g., when screen is hidden)."""
        if self._is_running:
            self.timer.stop()
            self._is_running = False
            self.slideshowRunningChanged.emit(False)
            logger.info("Slideshow timer paused (e.g., screen hidden).")

    @Slot()
    def resume_timer(self):
        """Resume the automatic advancement timer if not paused by user."""
        # Only resume if not manually paused by user and slideshow isn't already running
        if not self._user_paused and not self._is_running and self.media_files:
            current_path, is_video = self.media_files[self.current_index]
            # Only start timer if the current item is an image
            if not is_video:
                self.timer.start()
                self._is_running = True
                self.slideshowRunningChanged.emit(True)
                logger.info("Slideshow timer resumed (e.g., screen shown).")
            else:
                logger.info("Screen shown, but current item is video. Timer not resumed.")
        elif self._user_paused:
            logger.info("Screen shown, but slideshow was paused by user. Timer not resumed.")
        elif self._is_running:
             logger.info("Screen shown, but timer is already running.")
