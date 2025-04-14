#!/usr/bin/env python3
from PySide6.QtCore import QObject, Signal, Property, Slot, QTimer
from PySide6.QtGui import QColor
from frontend.style import DARK_COLORS, LIGHT_COLORS
from frontend.config import logger
import json
import os
from datetime import datetime, timezone


class ThemeManager(QObject):
    themeChanged = Signal()
    autoThemeModeChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_dark_mode = True
        self._auto_theme_mode = False  # Auto theme mode disabled by default
        self._colors = DARK_COLORS.copy()
        self._sunrise_time = None
        self._sunset_time = None
        self._load_theme_preferences()

        # QML color properties
        self._background_color = QColor(self._colors["background"])
        self._background_secondary_color = QColor(self._colors["background_secondary"])
        self._background_input_color = QColor(self._colors["background_input"])
        self._user_bubble_color = QColor(self._colors["user_bubble"])
        self._assistant_bubble_color = QColor(self._colors["assistant_bubble"])
        self._text_primary_color = QColor(self._colors["text_primary"])
        self._text_secondary_color = QColor(self._colors["text_secondary"])
        self._button_primary_color = QColor(self._colors["button_primary"])
        self._button_hover_color = QColor(self._colors["button_hover"])
        self._button_pressed_color = QColor(self._colors["button_pressed"])
        self._input_background_color = QColor(self._colors["input_background"])
        self._input_border_color = QColor(self._colors["input_border"])
        self._card_color = QColor(self._colors["card_color"])
        self._card_alternate_color = QColor(self._colors["card_alternate_color"])
        self._accent_color = QColor(self._colors["accent_color"])
        self._accent_text_color = QColor(self._colors["accent_text_color"])
        self._border_color = QColor(self._colors["border_color"])
        self._danger_color = QColor(self._colors["danger_color"])
        self._dialog_background_color = QColor(self._colors["dialog_background_color"])
        self._dialog_header_color = QColor(self._colors["dialog_header_color"])
        
        # Create timer for day/night checks
        self._auto_theme_timer = QTimer(self)
        self._auto_theme_timer.timeout.connect(self._check_day_night_status)
        
        # Only start the timer if auto mode is enabled
        if self._auto_theme_mode:
            self._auto_theme_timer.start(60000)  # Check every minute

    def _load_theme_preferences(self):
        """Load theme preferences from file if it exists"""
        try:
            config_path = os.path.expanduser("~/.smartscreen_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    config = json.load(f)
                    if "is_dark_mode" in config:
                        self._is_dark_mode = config["is_dark_mode"]
                        self._colors = (
                            DARK_COLORS if self._is_dark_mode else LIGHT_COLORS
                        )
                        logger.info(
                            f"Loaded theme preference: {'dark' if self._is_dark_mode else 'light'} mode"
                        )
                    # Load auto theme mode setting
                    if "auto_theme_mode" in config:
                        self._auto_theme_mode = config["auto_theme_mode"]
                        logger.info(f"Loaded auto theme mode: {self._auto_theme_mode}")
        except Exception as e:
            logger.error(f"Error loading theme preferences: {e}")

    def _save_theme_preferences(self):
        """Save theme preferences to file"""
        try:
            config_path = os.path.expanduser("~/.smartscreen_config.json")
            config = {}
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    config = json.load(f)

            config["is_dark_mode"] = self._is_dark_mode
            config["auto_theme_mode"] = self._auto_theme_mode

            with open(config_path, "w") as f:
                json.dump(config, f)

            logger.info(
                f"Saved theme preferences: {'dark' if self._is_dark_mode else 'light'} mode, auto mode: {self._auto_theme_mode}"
            )
        except Exception as e:
            logger.error(f"Error saving theme preferences: {e}")

    def _get_is_dark_mode(self):
        return self._is_dark_mode

    def _set_is_dark_mode(self, value):
        if self._is_dark_mode != value:
            self._is_dark_mode = value
            self._colors = DARK_COLORS if value else LIGHT_COLORS
            self._save_theme_preferences()

            # Update all QML colors
            self._background_color = QColor(self._colors["background"])
            self._background_secondary_color = QColor(self._colors["background_secondary"])
            self._background_input_color = QColor(self._colors["background_input"])
            self._user_bubble_color = QColor(self._colors["user_bubble"])
            self._assistant_bubble_color = QColor(self._colors["assistant_bubble"])
            self._text_primary_color = QColor(self._colors["text_primary"])
            self._text_secondary_color = QColor(self._colors["text_secondary"])
            self._button_primary_color = QColor(self._colors["button_primary"])
            self._button_hover_color = QColor(self._colors["button_hover"])
            self._button_pressed_color = QColor(self._colors["button_pressed"])
            self._input_background_color = QColor(self._colors["input_background"])
            self._input_border_color = QColor(self._colors["input_border"])
            self._card_color = QColor(self._colors["card_color"])
            self._card_alternate_color = QColor(self._colors["card_alternate_color"])
            self._accent_color = QColor(self._colors["accent_color"])
            self._accent_text_color = QColor(self._colors["accent_text_color"])
            self._border_color = QColor(self._colors["border_color"])
            self._danger_color = QColor(self._colors["danger_color"])
            self._dialog_background_color = QColor(self._colors["dialog_background_color"])
            self._dialog_header_color = QColor(self._colors["dialog_header_color"])

            self.themeChanged.emit()
            logger.info(f"Theme changed to {'dark' if value else 'light'} mode")
            
    def _get_auto_theme_mode(self):
        return self._auto_theme_mode
        
    def update_sun_times(self, sunrise=None, sunset=None):
        """Update the sunrise and sunset times used for auto theming"""
        times_changed = False
        
        if sunrise and sunrise != self._sunrise_time:
            self._sunrise_time = sunrise
            times_changed = True
            logger.info(f"Updated sunrise time: {sunrise}")
            
        if sunset and sunset != self._sunset_time:
            self._sunset_time = sunset
            times_changed = True
            logger.info(f"Updated sunset time: {sunset}")
            
        if times_changed and self._auto_theme_mode:
            # Immediately check if theme should change
            self._check_day_night_status()
    
    def _check_day_night_status(self):
        """Check if it's day or night and update theme accordingly"""
        if not self._auto_theme_mode or not self._sunrise_time or not self._sunset_time:
            return
            
        try:
            # Get current time in UTC
            now = datetime.now(timezone.utc)
            
            # Parse sunrise and sunset times
            # Assuming format like "2025-04-12T10:43:12+00:00"
            sunrise = datetime.fromisoformat(self._sunrise_time)
            sunset = datetime.fromisoformat(self._sunset_time)
            
            # Determine if it's night or day
            is_night = now < sunrise or now > sunset
            
            # Only change theme if needed
            if is_night != self._is_dark_mode:
                logger.info(f"Auto switching to {'dark' if is_night else 'light'} theme")
                self.is_dark_mode = is_night  # This will trigger _save_theme_preferences
        except Exception as e:
            logger.error(f"Error checking day/night status: {e}")

    @Slot()
    def toggle_theme(self):
        # Only manually toggle if not in auto mode
        if not self._auto_theme_mode:
            self.is_dark_mode = not self._is_dark_mode
            
    @Slot(result=bool)
    def toggle_auto_theme_mode(self):
        """Toggle automatic theme switching based on day/night"""
        self._auto_theme_mode = not self._auto_theme_mode
        
        if self._auto_theme_mode:
            # Start the timer when enabling auto mode
            self._auto_theme_timer.start(60000)  # Check every minute
            # Immediately check status
            self._check_day_night_status()
        else:
            # Stop timer when disabling auto mode
            self._auto_theme_timer.stop()
            
        self._save_theme_preferences()
        self.autoThemeModeChanged.emit()
        return self._auto_theme_mode

    # Define the properties
    is_dark_mode = Property(
        bool, _get_is_dark_mode, _set_is_dark_mode, notify=themeChanged
    )
    
    auto_theme_mode = Property(
        bool, _get_auto_theme_mode, notify=autoThemeModeChanged
    )

    # Define properties for direct QML use
    def _get_background_color(self):
        return self._background_color

    def _get_user_bubble_color(self):
        return self._user_bubble_color

    def _get_assistant_bubble_color(self):
        return self._assistant_bubble_color

    def _get_text_primary_color(self):
        return self._text_primary_color

    def _get_text_secondary_color(self):
        return self._text_secondary_color

    def _get_button_primary_color(self):
        return self._button_primary_color

    def _get_button_hover_color(self):
        return self._button_hover_color

    def _get_button_pressed_color(self):
        return self._button_pressed_color

    def _get_input_background_color(self):
        return self._input_background_color

    def _get_input_border_color(self):
        return self._input_border_color

    def _get_card_color(self):
        return self._card_color

    def _get_card_alternate_color(self):
        return self._card_alternate_color
        
    def _get_background_secondary_color(self):
        return self._background_secondary_color
        
    def _get_background_input_color(self):
        return self._background_input_color
        
    def _get_accent_color(self):
        return self._accent_color
        
    def _get_accent_text_color(self):
        return self._accent_text_color
        
    def _get_border_color(self):
        return self._border_color
        
    def _get_danger_color(self):
        return self._danger_color
        
    def _get_dialog_background_color(self):
        return self._dialog_background_color
        
    def _get_dialog_header_color(self):
        return self._dialog_header_color

    # QML color properties
    background_color = Property(QColor, _get_background_color, notify=themeChanged)
    background_secondary_color = Property(QColor, _get_background_secondary_color, notify=themeChanged)
    background_input_color = Property(QColor, _get_background_input_color, notify=themeChanged)
    user_bubble_color = Property(QColor, _get_user_bubble_color, notify=themeChanged)
    assistant_bubble_color = Property(
        QColor, _get_assistant_bubble_color, notify=themeChanged
    )
    text_primary_color = Property(QColor, _get_text_primary_color, notify=themeChanged)
    text_secondary_color = Property(
        QColor, _get_text_secondary_color, notify=themeChanged
    )
    button_primary_color = Property(
        QColor, _get_button_primary_color, notify=themeChanged
    )
    button_hover_color = Property(QColor, _get_button_hover_color, notify=themeChanged)
    button_pressed_color = Property(
        QColor, _get_button_pressed_color, notify=themeChanged
    )
    input_background_color = Property(
        QColor, _get_input_background_color, notify=themeChanged
    )
    input_border_color = Property(QColor, _get_input_border_color, notify=themeChanged)
    card_color = Property(QColor, _get_card_color, notify=themeChanged)
    card_alternate_color = Property(QColor, _get_card_alternate_color, notify=themeChanged)
    accent_color = Property(QColor, _get_accent_color, notify=themeChanged)
    accent_text_color = Property(QColor, _get_accent_text_color, notify=themeChanged)
    border_color = Property(QColor, _get_border_color, notify=themeChanged)
    danger_color = Property(QColor, _get_danger_color, notify=themeChanged)
    dialog_background_color = Property(QColor, _get_dialog_background_color, notify=themeChanged)
    dialog_header_color = Property(QColor, _get_dialog_header_color, notify=themeChanged)
