# PySide Raspberry Pi Frontend Architecture

This document provides an overview of the architecture and design principles of the PySide Raspberry Pi Frontend application. It serves as a guide for understanding the codebase and for future development.

## Project Overview

The PySide Raspberry Pi Frontend is a Qt/QML-based application designed to run on Raspberry Pi devices. It provides a modern, touch-friendly interface with multiple screens including:

- Chat interface with speech-to-text and text-to-speech capabilities
- Weather display
- Calendar view
- Clock/time display
- Photo viewer
- Settings management

The application is built using Python with PySide6 (Qt for Python) for the backend and QML for the frontend UI.

## Core Components

### UI Layer (QML)

The UI is built with QML and organized into screen components:

- **MainWindow.qml**: The main application window that contains the navigation and screen management
- **BaseScreen.qml**: Base component that all screens inherit from, providing common structure and properties
- **BaseControls.qml**: Base component that all control bars inherit from, providing common layout and behavior
- **BaseControlButton.qml**: Reusable button component for consistent UI controls
- **[Screen]Screen.qml**: Individual screen implementations (ChatScreen.qml, WeatherScreen.qml, etc.) that inherit from BaseScreen
- **[Screen]Controls.qml**: Control components for each screen that appear in the top bar and inherit from BaseControls

### Backend (Python)

The Python backend is organized into several key components:

- **main.py**: Application entry point and initialization
- **config.py**: Basic configuration and logging setup
- **config_manager.py**: Advanced configuration management
- **theme_manager.py**: Manages application theming (dark/light mode)
- **settings_model.py**: QML-compatible model for settings management

#### Logic Components

- **logic/resource_manager.py**: Unified manager for asynchronous tasks and service operations
- **logic/audio_manager.py**: Handles audio playback
- **logic/speech_manager.py**: Manages speech recognition
- **logic/websocket_client.py**: Handles WebSocket communication
- **logic/chat_controller.py**: Main controller for chat functionality that handles all chat-related operations
- **logic/message_handler.py**: Processes chat messages

## Configuration System

The application uses a multi-layered configuration system:

1. **Centralized Config**: Default configurations defined in `frontend/config.py`
2. **User Configs**: User-specific overrides stored in `~/.smartscreen_config.json`

### ConfigManager

The `ConfigManager` class provides a unified interface for accessing configuration values from different sources:

```python
# Get a configuration value
config_manager = ConfigManager()
value = config_manager.get_config("stt.STT_CONFIG.enabled")

# Set a configuration value
config_manager.set_config("stt.STT_CONFIG.enabled", True)
```

Configuration paths follow the format `source.variable.key`:
- `stt.STT_CONFIG.enabled` refers to the `enabled` key in the `STT_CONFIG` variable in the config module
- `server.SERVER_HOST` refers to the `SERVER_HOST` variable in the config module
- `user.theme.is_dark_mode` refers to the `is_dark_mode` key in the `theme` section of the user config

### Speech-to-Text Configuration

The Speech-to-Text system is highly configurable through the `STT_CONFIG` dictionary:

- `enabled`: Global switch to enable/disable STT
- `auto_start`: Whether to start STT automatically on initialization
- `use_keepalive`: Whether to use KeepAlive for pausing/resuming during TTS
- `auto_submit_utterances`: When enabled, complete utterances are automatically submitted to the chat instead of being placed in the input field (displayed as "Auto Send" in UI)

### Settings Model

The settings system uses a model-view architecture to expose configuration values to the QML UI:

- **SettingsModel**: Main model containing all settings categories
- **SettingsCategory**: Groups related settings (e.g., "Speech-to-Text", "Audio")
- **SettingItem**: Individual setting with properties like name, type, and value

The model is registered with QML in `main.py`:

```python
settings_model = SettingsModel()
engine.rootContext().setContextProperty("settingsModel", settings_model)
```

#### Settings UI Implementation

The settings UI uses a direct hardcoded approach rather than a fully dynamic one. This approach was chosen for reliability and simplicity:

1. Each settings category is explicitly defined in the SettingsScreen.qml file
2. Settings within each category are explicitly coded with their labels and controls
3. Settings values are accessed directly using model indices

Example setting implementation:

```qml
// Setting: Auto Send
RowLayout {
    Layout.fillWidth: true
    spacing: 16
    
    Text {
        text: "Auto Send:"
        color: ThemeManager.text_primary_color
        Layout.preferredWidth: 150
        elide: Text.ElideRight
        
        ToolTip.visible: autoSendMouseArea.containsMouse
        ToolTip.text: "Automatically submit complete utterances..."
        
        MouseArea {
            id: autoSendMouseArea
            anchors.fill: parent
            hoverEnabled: true
        }
    }
    
    Switch {
        id: autoSendSwitch
        checked: settingsModel.data(settingsModel.index(0, 0), 259)[3].value
        onCheckedChanged: {
            if (checked !== settingsModel.data(settingsModel.index(0, 0), 259)[3].value) {
                settingsModel.data(settingsModel.index(0, 0), 259)[3].value = checked
            }
        }
    }
}
```

#### Direct Method Approach for Settings

For settings that need to persist across screen navigation, we use a direct method approach to avoid QML/Python type conversion issues:

1. **Define getter and setter methods in the Python model** that are exposed as slots:

```python
@Slot(bool, result=bool)
def setAutoSubmitUtterances(self, enabled: bool) -> bool:
    """Directly set the auto_submit_utterances setting value."""
    # Initialize the config manager
    config_manager = ConfigManager()
    
    # Directly set the config value using the config path
    result = config_manager.set_config("stt.STT_CONFIG.auto_submit_utterances", enabled)
    
    if result:
        logger.info(f"Updated auto_submit_utterances to {enabled}")
        # Update UI consistency if needed
    
    return result
    
@Slot(result=bool)
def getAutoSubmitUtterances(self) -> bool:
    """Directly get the auto_submit_utterances setting value."""
    config_manager = ConfigManager()
    return config_manager.get_config("stt.STT_CONFIG.auto_submit_utterances", False)
```

2. **In QML, store the current value in a property** and update it using the direct methods:

```qml
// Property to store current value
property bool autoSendEnabled: false

// Initialize on component load
Component.onCompleted: {
    if (settingsModel) {
        autoSendEnabled = settingsModel.getAutoSubmitUtterances()
    }
}

// Update via direct method call
Switch {
    checked: autoSendEnabled
    onToggled: {
        if (settingsModel) {
            var success = settingsModel.setAutoSubmitUtterances(checked)
            if (success) {
                autoSendEnabled = checked
            }
        }
    }
}
```

3. **Components that use the setting must access it via ConfigManager, not directly**:

```python
# In SpeechManager.py
def handle_frontend_stt_text(self, text):
    """Handle final transcription results"""
    if text.strip():
        # Get the most up-to-date setting value from ConfigManager
        auto_submit = self.config_manager.get_config("stt.STT_CONFIG.auto_submit_utterances", False)
        
        if auto_submit:
            # Auto-submit the utterance to chat
            self.autoSubmitUtterance.emit(text)
        else:
            # Default: populate the input field
            self.sttInputTextReceived.emit(text)
}
```

This approach solves QML/Python type conversion issues by:
- Using explicit methods instead of property bindings
- Only exchanging simple types (boolean, string, numbers) between QML and Python
- Handling all complex logic in Python rather than QML
- Ensuring that components access the latest config values directly via ConfigManager
- Avoiding stale cached values from module imports

#### Adding New Settings

To add a new setting:

1. **Backend**: Add the setting to the appropriate category in `settings_model.py`:

```python
category.add_setting(SettingItem(
    "setting_name", "Display Name", 
    "Description of the setting", 
    "bool", "config.path.to.setting"
))
```

2. **Frontend**: Add a new UI block to the appropriate category in `SettingsScreen.qml`:

```qml
// Setting: New Setting
RowLayout {
    Layout.fillWidth: true
    spacing: 16
    
    Text {
        text: "New Setting:"
        color: ThemeManager.text_primary_color
        Layout.preferredWidth: 150
        elide: Text.ElideRight
        
        ToolTip.visible: newSettingMouseArea.containsMouse
        ToolTip.text: "Description of the new setting"
        
        MouseArea {
            id: newSettingMouseArea
            anchors.fill: parent
            hoverEnabled: true
        }
    }
    
    // For boolean settings
    Switch {
        id: newSettingSwitch
        // categoryIndex, settingIndex - adjust these as needed
        checked: settingsModel.data(settingsModel.index(0, 0), 259)[4].value
        onCheckedChanged: {
            if (checked !== settingsModel.data(settingsModel.index(0, 0), 259)[4].value) {
                settingsModel.data(settingsModel.index(0, 0), 259)[4].value = checked
            }
        }
    }
    
    // For other types, copy appropriate controls from existing examples
}
```

3. To find the correct indices for a new setting, use:
   - **categoryIndex**: The index of the category in the `_categories` list (0 for STT, 1 for Audio, etc.)
   - **settingIndex**: The index of the setting within that category (based on order added to category)
   - **Role ID**: Always use 259 for accessing settings (this is the SettingsRole value)

This direct approach means changes to settings require changes to both the model and UI code, but results in a more reliable and straightforward implementation.

## Signal Flow

The application uses Qt's signal/slot mechanism for communication between components:

1. **Python to Python**: Components emit signals that other Python components can connect to
2. **Python to QML**: Python signals are exposed to QML through properties and can trigger UI updates
3. **QML to Python**: QML calls Python methods through exposed slots and properties

### Chat Signal Flow

The ChatController exposes several signals to QML:
- `messageReceived`: Emitted when a new message is received from the backend
- `messageChunkReceived`: Emitted when a streaming message chunk is received 
- `sttTextReceived`: Emitted when speech-to-text transcription arrives
- `sttInputTextReceived`: Emitted when a complete utterance should be set in the input field
- `userMessageAutoSubmitted`: Emitted when an utterance is auto-submitted to chat, ensuring it appears in the chat history
- `connectionStatusChanged`: Emitted when the WebSocket connection status changes
- `ttsStateChanged`: Emitted when the text-to-speech state changes

## Adding New Features

### Adding a New Screen

1. Create a new QML file in `frontend/qml/` (e.g., `NewScreen.qml`)
2. Create a corresponding controls file (e.g., `NewControls.qml`)
3. Add a navigation button in `MainWindow.qml`

### Adding New Settings

1. Identify the appropriate category or create a new one in `settings_model.py`
2. Add the setting to the category in the `_init_model` method:

```python
category.add_setting(SettingItem(
    "setting_name", "Display Name", 
    "Description of the setting", 
    "bool", "config.path.to.setting"
))
```

3. The setting will automatically appear in the Settings screen

### Adding a New Configuration Module

1. Create a new Python module with configuration variables
2. Update `ConfigManager` to load the new module:

```python
if source == 'new_module':
    self.load_module_config('frontend.new_module.config', ['CONFIG_VAR1', 'CONFIG_VAR2'])
```

## Component Inheritance System

The application uses a component inheritance system to promote code reuse and maintain consistency across the UI:

### Base Components

- **BaseScreen**: Provides common structure and properties for all screens
  - Standard background and layout
  - Common properties like `screenControls` and `title`
  - Content area that child screens can override

- **BaseControls**: Provides common layout and behavior for all control bars
  - Standard spacing and alignment
  - Reference to the screen it controls
  - Common utility functions

- **BaseControlButton**: Reusable button component for consistent UI controls
  - Standard size and appearance
  - Properties for customization (icon, tooltip, etc.)
  - Toggle functionality

### Inheritance Pattern

Screen components inherit from BaseScreen:
```qml
BaseScreen {
    id: myScreen
    screenControls: "MyControls.qml"
    title: "My Screen"
    
    // Screen-specific content here
}
```

Control components inherit from BaseControls:
```qml
BaseControls {
    id: myControls
    
    // Control-specific buttons and widgets here
}
```

This inheritance system makes it easier to:
- Add new screens and controls with consistent behavior
- Make global changes to all screens or controls
- Maintain a cleaner, more organized codebase

## Best Practices

1. **Separation of Concerns**: Keep UI logic in QML and business logic in Python
2. **Component Inheritance**: Use the base components for new screens and controls
3. **Asynchronous Operations**: Use `TaskManager` for async operations to avoid blocking the UI
4. **Configuration**: Store configuration in the appropriate place based on its nature
5. **Error Handling**: Use proper error handling and logging throughout the application
6. **Documentation**: Keep this document updated as the application evolves

## Common Issues and Solutions

### Configuration Management

The application's configuration system can be tricky to work with. Here are solutions to common issues:

#### Module Key Naming

**Problem**: Configuration modules are loaded with inconsistent keys, causing "Unknown config source" errors when accessing values.

**Solution**: Always ensure module keys match the expected source names:

```python
# In ConfigManager.load_module_config():
# Use 'stt' for STT_CONFIG, 'server' for SERVER_HOST, etc.
if 'STT_CONFIG' in config_vars:
    module_key = 'stt'
elif 'SERVER_HOST' in config_vars:
    module_key = 'server'
else:
    module_key = module_path.split('.')[-1]
```

#### UI Settings Updates

**Problem**: Settings toggled in the UI aren't persisting due to QML/Python type conversion issues.

**Solution**: Use direct method calls (slots) instead of property bindings for settings:

1. Define dedicated get/set methods in your model:

```python
@Slot(bool, result=bool)
def setAutoSubmitUtterances(self, enabled: bool) -> bool:
    config_manager = ConfigManager()
    return config_manager.set_config("stt.STT_CONFIG.auto_submit_utterances", enabled)
    
@Slot(result=bool)
def getAutoSubmitUtterances(self) -> bool:
    config_manager = ConfigManager()
    return config_manager.get_config("stt.STT_CONFIG.auto_submit_utterances", False)
```

2. In QML, use a property and update it via the direct methods:

```qml
// Property to store current value
property bool autoSendEnabled: false

// Initialize in Component.onCompleted
Component.onCompleted: {
    if (settingsModel) {
        autoSendEnabled = settingsModel.getAutoSubmitUtterances()
    }
}

// Update via direct method call
Switch {
    checked: autoSendEnabled
    onToggled: {
        if (settingsModel) {
            var success = settingsModel.setAutoSubmitUtterances(checked)
            if (success) {
                autoSendEnabled = checked
            } else {
                // Revert without triggering events if update failed
                checked = Qt.binding(function() { return autoSendEnabled; })
            }
        }
    }
}
```

3. Never try to assign values directly to PyObject properties in QML:

```qml
// AVOID this pattern - leads to "Cannot assign bool to PySide::PyObjectWrapper" errors
Switch {
    checked: settingsModel.data(settingsModel.index(0, 0), 259)[3].value
    onCheckedChanged: {
        // This will fail!
        settingsModel.data(settingsModel.index(0, 0), 259)[3].value = checked
    }
}
```

#### Testing Configuration Changes

Before assuming configuration changes work, always test them thoroughly:

1. Verify changes persist after navigating between screens
2. Check the logs for errors (especially "Unknown config source" errors)
3. Verify the actual behavior matches the expected setting (e.g., auto-submit actually working)
4. Consider adding debug logging in components that use the configuration

#### Configuration File Integrity

If settings seem to reset themselves, check the user configuration file integrity:

```bash
cat ~/.smartscreen_config.json
```

Ensure it's valid JSON format and contains the expected structure:

```json
{
  "module_overrides": {
    "stt": {
      "STT_CONFIG": {
        "auto_submit_utterances": true
      }
    }
  },
  "theme": {
    "is_dark_mode": true
  }
}
```

### QML UI Issues

#### QML/Python Type Conversion

**Problem**: QML cannot directly modify Python object properties, leading to errors like `Cannot assign bool to PySide::PyObjectWrapper`.

**Solution**: 
1. Use simple types (bool, string, int) for data exchange between QML and Python
2. Provide explicit getters and setters as Python slots for complex operations
3. Store current values in QML properties rather than trying to bind directly to Python objects

#### UI Updates After Configuration Changes

If UI components don't reflect configuration changes:

1. Emit appropriate signals after settings are changed
2. Add a binding function to reset the property if needed:

```qml
// Reset binding if update fails
someProperty = Qt.binding(function() { return originalValue; })
```

3. Consider using the `notify` property in Python `Property` definitions to signal changes:

```python
value = Property(bool, _get_value, _set_value, notify=valueChanged)
```

### Debugging and Testing

1. **Always log configuration changes**: Add debug logs before and after configuration updates
2. **Test navigation**: Ensure settings persist when navigating between screens
3. **Check console output**: Many issues appear as QML errors in the console
4. **Verify configuration file**: Check that changes are actually saved to the user configuration file
5. **Test component by component**: Isolate which component is not behaving as expected

By following these guidelines, you can avoid many common issues with the configuration system and ensure settings work consistently across the application.
