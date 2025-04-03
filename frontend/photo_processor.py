from PIL import Image, ImageFilter, ImageEnhance
import os
import logging
import tempfile
from PySide6.QtCore import QObject

logger = logging.getLogger("frontend.photo_processor")


class PhotoProcessor(QObject):
    """Utility class to process photos with borders and effects"""

    def __init__(self):
        super().__init__()
        self.cache_dir = os.path.join(tempfile.gettempdir(), "photo_processor_cache")
        # Create cache directory if it doesn't exist
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
        logger.info(f"PhotoProcessor initialized with cache at {self.cache_dir}")

    def add_shadow_effect(self, image_path, is_dark_mode=False):
        """
        Add a shadow effect to the image and return the path to the processed image

        Args:
            image_path: Path to the original image
            is_dark_mode: Whether the UI is in dark mode

        Returns:
            Path to the processed image
        """
        try:
            # Log the image processing attempt
            logger.info(f"Processing image: {image_path}, dark mode: {is_dark_mode}")

            # Skip if not an image
            if not image_path.lower().endswith((".jpg", ".jpeg", ".png")):
                logger.info(f"Skipping non-image file: {image_path}")
                return image_path

            # Check if we already have a cached version - fix the cache key naming
            filename = os.path.basename(image_path)
            name, ext = os.path.splitext(filename)
            # Always use PNG for output since we ensure RGBA
            cache_key = f"{name}.png"  # Simplified cache key, shadow removed
            cached_path = os.path.join(self.cache_dir, cache_key)

            # Return cached version if it exists
            if os.path.exists(cached_path):
                logger.info(f"Using cached version: {cached_path}")
                return cached_path

            # Open the image
            logger.info(f"Opening image: {image_path}")
            img = Image.open(image_path)

            # Convert to RGBA if not already
            if img.mode != "RGBA":
                logger.info(f"Converting image from {img.mode} to RGBA")
                img = img.convert("RGBA")

            # Shadow creation steps removed. We just use the 'img' (converted to RGBA).
            processed_image = img

            # Save the processed image to cache
            logger.info(f"Saving processed image to: {cached_path}")
            processed_image.save(cached_path)

            logger.info(f"Saved processed (no shadow) image to {cached_path}")
            return cached_path

        except Exception as e:
            logger.error(
                f"Error adding shadow effect to image {image_path}: {str(e)}",
                exc_info=True,
            )
            return image_path  # Return original path on error

    def create_blurred_background(self, image_path):
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
                logger.info(f"Skipping non-image file for blur: {image_path}")
                return None

            # Create cache key for the blurred image
            filename = os.path.basename(image_path)
            name, ext = os.path.splitext(filename)
            # Always use JPG for blurred backgrounds (no need for transparency)
            cache_key = f"{name}_blurred.jpg"
            cached_path = os.path.join(self.cache_dir, cache_key)

            # Return cached version if it exists
            if os.path.exists(cached_path):
                logger.info(f"Using cached blurred background: {cached_path}")
                return cached_path

            # Open the image
            logger.info(f"Creating blurred background for: {image_path}")
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

            # Save to cache
            blurred.save(cached_path, quality=90)
            logger.info(f"Saved blurred background to: {cached_path}")

            return cached_path

        except Exception as e:
            logger.error(f"Error creating blurred background for {image_path}: {e}")
            return None

    def clear_cache(self):
        """Clear all cached images"""
        try:
            # Delete all files in cache directory
            if os.path.exists(self.cache_dir):
                for filename in os.listdir(self.cache_dir):
                    file_path = os.path.join(self.cache_dir, filename)
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                logger.info("Cleared image processing cache")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
