from PySide6.QtCore import QObject, Slot, Signal, Property, QTimer, QUrl
from PySide6.QtGui import QPixmap
import os
import logging

logger = logging.getLogger("frontend.photo_controller")

class PhotoController(QObject):
    """Controller for the photo screen that manages photo and video slideshow"""
    
    # Signal when current media changes (path, isVideo)
    currentMediaChanged = Signal(str, bool)
    
    # Signal when slideshow state changes
    slideshowRunningChanged = Signal(bool)
    
    def __init__(self):
        super().__init__()
        self.media_folder = '/home/human/AAREPOS/PYSIDE_RASPI_FRONTEND/frontend/downloaded_media'
        self.media_files = []
        self.current_index = 0
        self._is_running = False
        
        # Timer for auto-advancing images
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.show_next_media)
        self.timer.setInterval(5000)  # 5 seconds for images
        
        # Load media files
        self.load_media_files()
        logger.info("PhotoController initialized")
    
    def load_media_files(self):
        """Load all media files from the specified folder"""
        try:
            if os.path.exists(self.media_folder):
                self.media_files = []
                for filename in os.listdir(self.media_folder):
                    file_path = os.path.join(self.media_folder, filename)
                    if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.mp4', '.mov', '.webm')):
                        is_video = filename.lower().endswith(('.mp4', '.mov', '.webm'))
                        self.media_files.append((file_path, is_video))
                
                # Sort files by name
                self.media_files.sort(key=lambda x: x[0])
                
                logger.info(f"Loaded {len(self.media_files)} media files from {self.media_folder}")
                
                # Emit the first media item
                if self.media_files:
                    self.currentMediaChanged.emit(self.media_files[0][0], self.media_files[0][1])
            else:
                logger.error(f"Media folder does not exist: {self.media_folder}")
        except Exception as e:
            logger.error(f"Error loading media files: {e}")
    
    @Slot()
    def start_slideshow(self):
        """Start the slideshow timer"""
        if self.media_files:
            self.timer.start()
            self._is_running = True
            self.slideshowRunningChanged.emit(True)
            logger.info("Slideshow started")
    
    @Slot()
    def stop_slideshow(self):
        """Stop the slideshow timer"""
        self.timer.stop()
        self._is_running = False
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
    
    @Slot()
    def advance_to_next(self):
        """Manually advance to the next media item"""
        if not self.media_files:
            return
        
        self.current_index = (self.current_index + 1) % len(self.media_files)
        current_path, is_video = self.media_files[self.current_index]
        
        # Emit the new media item
        self.currentMediaChanged.emit(current_path, is_video)
        logger.debug(f"Showing media {self.current_index + 1}/{len(self.media_files)}: {current_path}")
    
    @Slot()
    def go_to_previous(self):
        """Go to the previous media item"""
        if not self.media_files:
            return
        
        self.current_index = (self.current_index - 1) % len(self.media_files)
        current_path, is_video = self.media_files[self.current_index]
        
        # Emit the new media item
        self.currentMediaChanged.emit(current_path, is_video)
        logger.debug(f"Showing media {self.current_index + 1}/{len(self.media_files)}: {current_path}")
    
    @Slot()
    def video_finished(self):
        """Called when a video finishes playing"""
        logger.info("Video finished playing")
        self.advance_to_next()
    
    @Property(bool, notify=slideshowRunningChanged)
    def is_running(self):
        """Return whether the slideshow is currently running"""
        return self._is_running 