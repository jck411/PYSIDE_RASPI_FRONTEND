#!/usr/bin/env python3
"""
Settings Model for the PySide Raspberry Pi Frontend

This module provides QML-compatible models for representing and managing
application settings. It works with the ConfigManager to provide a unified
interface for accessing and modifying settings from various sources.
"""

from PySide6.QtCore import QObject, Signal, Property, Slot, QAbstractListModel, QModelIndex, Qt
from typing import Dict, Any, List, Optional

from frontend.config import logger
from frontend.config_manager import ConfigManager

class SettingItem(QObject):
    """
    Represents a single setting item that can be bound to QML controls.
    
    This class provides properties and signals for QML binding, and handles
    the interaction with the ConfigManager to get and set values.
    """
    
    valueChanged = Signal()
    
    def __init__(self, name: str, display_name: str, description: str, 
                 value_type: str, config_path: str, parent: Optional[QObject] = None):
        """
        Initialize a setting item.
        
        Args:
            name: Internal name of the setting
            display_name: User-friendly name for display
            description: Detailed description of the setting
            value_type: Type of the setting value ("bool", "int", "string", "float", etc.)
            config_path: Path to the configuration value (e.g., "stt.STT_CONFIG.enabled")
            parent: Parent QObject
        """
        super().__init__(parent)
        self._name = name
        self._display_name = display_name
        self._description = description
        self._value_type = value_type
        self._config_path = config_path
        self._config_manager = ConfigManager()
    
    def _get_name(self) -> str:
        """Get the internal name of the setting."""
        return self._name
    
    def _get_display_name(self) -> str:
        """Get the user-friendly name of the setting."""
        return self._display_name
    
    def _get_description(self) -> str:
        """Get the detailed description of the setting."""
        return self._description
    
    def _get_value_type(self) -> str:
        """Get the type of the setting value."""
        return self._value_type
    
    def _get_value(self) -> Any:
        """Get the current value of the setting."""
        value = self._config_manager.get_config(self._config_path)
        
        # Convert to appropriate type if needed
        if self._value_type == "bool" and not isinstance(value, bool):
            return bool(value)
        elif self._value_type == "int" and not isinstance(value, int):
            try:
                return int(value)
            except (TypeError, ValueError):
                return 0
        elif self._value_type == "float" and not isinstance(value, float):
            try:
                return float(value)
            except (TypeError, ValueError):
                return 0.0
        
        return value
    
    def _set_value(self, value: Any) -> None:
        """Set the value of the setting."""
        # Convert to appropriate type if needed
        if self._value_type == "bool":
            value = bool(value)
        elif self._value_type == "int":
            try:
                value = int(value)
            except (TypeError, ValueError):
                logger.error(f"Invalid integer value for {self._name}: {value}")
                return
        elif self._value_type == "float":
            try:
                value = float(value)
            except (TypeError, ValueError):
                logger.error(f"Invalid float value for {self._name}: {value}")
                return
        
        # Update the config
        if self._config_manager.set_config(self._config_path, value):
            logger.info(f"Updated setting {self._name} to {value}")
            self.valueChanged.emit()
        else:
            logger.error(f"Failed to update setting {self._name} to {value}")
    
    # Define properties for QML binding
    name = Property(str, _get_name, constant=True)
    displayName = Property(str, _get_display_name, constant=True)
    description = Property(str, _get_description, constant=True)
    valueType = Property(str, _get_value_type, constant=True)
    value = Property(object, _get_value, _set_value, notify=valueChanged)


class SettingsCategory(QObject):
    """
    Represents a category of settings (e.g., STT, Audio, etc.).
    
    This class groups related settings together and provides properties
    for QML binding.
    """
    
    def __init__(self, name: str, display_name: str, parent: Optional[QObject] = None):
        """
        Initialize a settings category.
        
        Args:
            name: Internal name of the category
            display_name: User-friendly name for display
            parent: Parent QObject
        """
        super().__init__(parent)
        self._name = name
        self._display_name = display_name
        self._settings = []
    
    def add_setting(self, setting_item: SettingItem) -> None:
        """Add a setting item to this category."""
        self._settings.append(setting_item)
    
    def _get_name(self) -> str:
        """Get the internal name of the category."""
        return self._name
    
    def _get_display_name(self) -> str:
        """Get the user-friendly name of the category."""
        return self._display_name
    
    def _get_settings(self) -> List[SettingItem]:
        """Get the list of setting items in this category."""
        return self._settings
    
    # Define properties for QML binding
    name = Property(str, _get_name, constant=True)
    displayName = Property(str, _get_display_name, constant=True)
    settings = Property(list, _get_settings, constant=True)


class SettingsModel(QAbstractListModel):
    """
    Model containing all settings categories.
    
    This class provides a QML-compatible model for displaying and managing
    settings categories and their contained settings.
    """
    
    # Define roles for QML
    NameRole = Qt.UserRole + 1
    DisplayNameRole = Qt.UserRole + 2
    SettingsRole = Qt.UserRole + 3
    
    def __init__(self, parent: Optional[QObject] = None):
        """
        Initialize the settings model.
        
        Args:
            parent: Parent QObject
        """
        super().__init__(parent)
        self._categories = []
        self._init_model()
    
    def _init_model(self) -> None:
        """Initialize the model with predefined settings categories."""
        # STT Category
        stt_category = SettingsCategory("stt", "Speech-to-Text")
        stt_category.add_setting(SettingItem(
            "enabled", "Enable STT", 
            "Turn speech recognition on/off", 
            "bool", "stt.STT_CONFIG.enabled"
        ))
        stt_category.add_setting(SettingItem(
            "auto_start", "Auto-start STT", 
            "Automatically start speech recognition on startup", 
            "bool", "stt.STT_CONFIG.auto_start"
        ))
        stt_category.add_setting(SettingItem(
            "use_keepalive", "Use KeepAlive", 
            "Use KeepAlive for pausing/resuming during TTS", 
            "bool", "stt.STT_CONFIG.use_keepalive"
        ))
        self._categories.append(stt_category)
        
        # Audio Category
        audio_category = SettingsCategory("audio", "Audio Settings")
        audio_category.add_setting(SettingItem(
            "channels", "Audio Channels", 
            "Number of audio channels for recording", 
            "int", "stt.AUDIO_CONFIG.channels"
        ))
        audio_category.add_setting(SettingItem(
            "sample_rate", "Sample Rate", 
            "Audio sample rate in Hz", 
            "int", "stt.AUDIO_CONFIG.sample_rate"
        ))
        audio_category.add_setting(SettingItem(
            "block_size", "Block Size", 
            "Audio block size for processing", 
            "int", "stt.AUDIO_CONFIG.block_size"
        ))
        self._categories.append(audio_category)
        
        # Deepgram Category
        deepgram_category = SettingsCategory("deepgram", "Deepgram STT")
        deepgram_category.add_setting(SettingItem(
            "language", "Language", 
            "Language code for speech recognition", 
            "string", "stt.DEEPGRAM_CONFIG.language"
        ))
        deepgram_category.add_setting(SettingItem(
            "model", "Model", 
            "Deepgram model to use", 
            "string", "stt.DEEPGRAM_CONFIG.model"
        ))
        deepgram_category.add_setting(SettingItem(
            "smart_format", "Smart Format", 
            "Enable smart formatting of transcriptions", 
            "bool", "stt.DEEPGRAM_CONFIG.smart_format"
        ))
        deepgram_category.add_setting(SettingItem(
            "interim_results", "Interim Results", 
            "Enable interim results during transcription", 
            "bool", "stt.DEEPGRAM_CONFIG.interim_results"
        ))
        deepgram_category.add_setting(SettingItem(
            "endpointing", "Endpointing", 
            "Milliseconds of silence to consider end of speech", 
            "int", "stt.DEEPGRAM_CONFIG.endpointing"
        ))
        self._categories.append(deepgram_category)
        
        # Theme Category
        theme_category = SettingsCategory("theme", "Theme Settings")
        theme_category.add_setting(SettingItem(
            "is_dark_mode", "Dark Mode", 
            "Enable dark mode for the interface", 
            "bool", "user.theme.is_dark_mode"
        ))
        self._categories.append(theme_category)
        
        logger.info(f"Initialized settings model with {len(self._categories)} categories")
    
    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """
        Get the number of rows in the model.
        
        Args:
            parent: Parent model index
            
        Returns:
            Number of categories
        """
        return len(self._categories)
    
    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        """
        Get data for the specified index and role.
        
        Args:
            index: Model index
            role: Data role
            
        Returns:
            Data for the specified role
        """
        if not index.isValid() or index.row() >= len(self._categories):
            return None
        
        category = self._categories[index.row()]
        
        if role == self.NameRole:
            return category.name
        elif role == self.DisplayNameRole:
            return category.displayName
        elif role == self.SettingsRole:
            return category.settings
        
        return None
    
    def roleNames(self) -> Dict[int, bytes]:
        """
        Get the role names for QML binding.
        
        Returns:
            Dictionary mapping role IDs to role names
        """
        return {
            self.NameRole: b"name",
            self.DisplayNameRole: b"displayName",
            self.SettingsRole: b"settings"
        }
    
    @Slot(str, str, str, str, str, result=bool)
    def addSetting(self, category_name: str, name: str, display_name: str, 
                  description: str, value_type: str, config_path: str) -> bool:
        """
        Add a new setting to an existing category.
        
        Args:
            category_name: Name of the category to add the setting to
            name: Internal name of the setting
            display_name: User-friendly name for display
            description: Detailed description of the setting
            value_type: Type of the setting value
            config_path: Path to the configuration value
            
        Returns:
            True if the setting was added successfully, False otherwise
        """
        # Find the category
        for category in self._categories:
            if category.name == category_name:
                # Create and add the setting
                setting = SettingItem(name, display_name, description, value_type, config_path)
                category.add_setting(setting)
                
                # Notify the model that data has changed
                self.dataChanged.emit(
                    self.index(self._categories.index(category), 0),
                    self.index(self._categories.index(category), 0),
                    [self.SettingsRole]
                )
                
                logger.info(f"Added setting {name} to category {category_name}")
                return True
        
        logger.error(f"Category {category_name} not found")
        return False
    
    @Slot(str, str, result=bool)
    def addCategory(self, name: str, display_name: str) -> bool:
        """
        Add a new category to the model.
        
        Args:
            name: Internal name of the category
            display_name: User-friendly name for display
            
        Returns:
            True if the category was added successfully, False otherwise
        """
        # Check if the category already exists
        for category in self._categories:
            if category.name == name:
                logger.error(f"Category {name} already exists")
                return False
        
        # Create and add the category
        category = SettingsCategory(name, display_name)
        
        # Insert at the beginning of the model
        self.beginInsertRows(QModelIndex(), 0, 0)
        self._categories.insert(0, category)
        self.endInsertRows()
        
        logger.info(f"Added category {name}")
        return True
