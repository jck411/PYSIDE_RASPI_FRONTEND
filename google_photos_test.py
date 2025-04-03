#!/usr/bin/env python3
import os
import sys
import random

from PySide6 import QtWidgets, QtGui, QtCore

DOWNLOAD_DIR = '/home/human/AAREPOS/PYSIDE_RASPI_FRONTEND/frontend/downloaded_media'

class Slideshow(QtWidgets.QWidget):
    def __init__(self, image_folder):
        super().__init__()
        self.image_folder = image_folder
        # Filter for image files (jpg, jpeg, png).
        self.image_files = [os.path.join(image_folder, f) for f in os.listdir(image_folder)
                            if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        self.image_files.sort()  # Optional: sort files alphabetically.
        self.label = QtWidgets.QLabel(self)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.label)
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.show_next_image)
        self.timer.start(5000)  # Change image every 5 seconds.
        self.current_index = 0
        if self.image_files:
            self.show_image(self.image_files[self.current_index])
    
    def show_image(self, file_path):
        pixmap = QtGui.QPixmap(file_path)
        # Scale the pixmap to fit the widget while preserving aspect ratio.
        self.label.setPixmap(pixmap.scaled(self.label.size(), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))
    
    def show_next_image(self):
        if not self.image_files:
            return
        self.current_index = (self.current_index + 1) % len(self.image_files)
        self.show_image(self.image_files[self.current_index])
    
    def resizeEvent(self, event):
        if self.image_files:
            self.show_image(self.image_files[self.current_index])
        super().resizeEvent(event)

def main():
    app = QtWidgets.QApplication(sys.argv)
    window = Slideshow(DOWNLOAD_DIR)
    window.resize(800, 600)
    window.setWindowTitle("Slideshow Viewer")
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
