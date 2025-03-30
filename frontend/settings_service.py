#!/usr/bin/env python3
"""
Settings Service for the PySide Raspberry Pi Frontend

Provides a simplified and unified interface for accessing and modifying 
application settings, abstracting the underlying ConfigManager.
"""

from PySide6.QtCore import QObject, Signal, Slot
from typing import Any, Optional

from frontend.config_manager import ConfigManager
from frontend.config import logger

class SettingsService(QObject):
    """
    A singleton service providing a simplified interface for settings management.

    This service wraps the ConfigManager to offer a stable API for other parts
    of the application. It also provides signals for observing setting changes.
    """
    
    # Signal emitted when a setting's value is successfully changed.
    # Arguments: setting_path (str), new_value (Any)
    settingChanged = Signal(str, object)

    _instance: Optional['SettingsService'] = None
    _initialized: bool = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the SettingsService."""
        if self._initialized:
            return
            
        super().__init__() # Initialize QObject
        self._config_manager = ConfigManager()
        self._initialized = True
        logger.info("SettingsService initialized.")

    @Slot(str, bool, result=bool)
    def getSetting(self, path: str, default: bool = False) -> bool:
        """
        Get a configuration setting value (currently specialized for bool).

        Args:
            path: The configuration path (e.g., 'stt.STT_CONFIG.enabled').
            default: The default value to return if the path is not found.

        Returns:
            The configuration value or the default.
        """
        # Get the value, might be non-bool if stored incorrectly
        value = self._config_manager.get_config(path, default)
        # Ensure we return a boolean as per the slot signature
        return bool(value) if value is not None else default

    @Slot(str, bool, result=bool)
    def setSetting(self, path: str, value: bool) -> bool:
        """
        Set a configuration setting value (currently specialized for bool).

        Emits the `settingChanged` signal if the value is successfully set.

        Args:
            path: The configuration path (e.g., 'stt.STT_CONFIG.enabled').
            value: The new value to set.

        Returns:
            True if the setting was successfully saved, False otherwise.
        """
        logger.debug(f"Attempting to set setting '{path}' to: {value}")
        success = self._config_manager.set_config(path, value)
        if success:
            logger.info(f"Setting '{path}' updated successfully.")
            try:
                # Emit signal after successful change
                self.settingChanged.emit(path, value) 
            except Exception as e:
                 # Log if signal emission fails, but don't block the set operation
                 logger.error(f"Error emitting settingChanged signal for path '{path}': {e}")
        else:
            logger.warning(f"Failed to set setting '{path}'.")
            
        return success

# Optional: Add an observeSetting method if more complex observation logic is needed later.
# For now, components can connect directly to the settingChanged signal.

# --- Example Usage ---
# if __name__ == '__main__':
#     # This is just for demonstration, normally initialized in main.py
#     
#     # Need a Qt Application context for signals
#     from PySide6.QtWidgets import QApplication
#     import sys
#     app = QApplication(sys.argv) 
#
#     settings_service = SettingsService()
#     
#     def on_setting_changed(path, value):
#         print(f"Setting changed via signal! Path: {path}, New Value: {value}")
#
#     # Connect to the signal
#     settings_service.settingChanged.connect(on_setting_changed)
#
#     # Example: Get initial value
#     initial_dark_mode = settings_service.getSetting('user.theme.is_dark_mode', False)
#     print(f"Initial dark mode: {initial_dark_mode}")
#
#     # Example: Set a value (this should trigger the signal)
#     print("Setting dark mode to True...")
#     settings_service.setSetting('user.theme.is_dark_mode', not initial_dark_mode)
#     
#     # Example: Get the new value
#     new_dark_mode = settings_service.getSetting('user.theme.is_dark_mode')
#     print(f"New dark mode: {new_dark_mode}")
#     
#     # Example: Set a module override
#     print("Setting STT auto_start...")
#     settings_service.setSetting('stt.STT_CONFIG.auto_start', True)
#     print(f"STT auto_start: {settings_service.getSetting('stt.STT_CONFIG.auto_start')}")
#
#     # Need to run the Qt event loop briefly for signals to process in this example
#     # In the main app, the event loop runs continuously.
#     app.processEvents() 