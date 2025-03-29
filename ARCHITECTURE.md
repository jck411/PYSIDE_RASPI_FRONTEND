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

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        QML UI Layer                          │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────────────┐  │
│  │ Chat     │  │ Weather │  │ Calendar│  │ Settings        │  │
│  │ Screen   │  │ Screen  │  │ Screen  │  │ Screen          │  │
│  └─────────┘  └─────────┘  └─────────┘  └─────────────────┘  │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                      Python Backend                          │
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │ Theme Manager   │  │ Settings Model  │  │ Config       │ │
│  └─────────────────┘  └─────────────────┘  │ Manager      │ │
│                                            └──────────────┘ │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │ Chat Logic      │  │ Audio Manager   │  │ Task Manager │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │ WebSocket       │  │ Speech Manager  │  │ Service      │ │
│  │ Client          │  │                 │  │ Manager      │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### UI Layer (QML)

The UI is built with QML and organized into screen components:

- **MainWindow.qml**: The main application window that contains the navigation and screen management
- **[Screen]Screen.qml**: Individual screen implementations (ChatScreen.qml, WeatherScreen.qml, etc.)
- **[Screen]Controls.qml**: Control components for each screen that appear in the top bar

### Backend (Python)

The Python backend is organized into several key components:

- **main.py**: Application entry point and initialization
- **config.py**: Basic configuration and logging setup
- **config_manager.py**: Advanced configuration management
- **theme_manager.py**: Manages application theming (dark/light mode)
- **settings_model.py**: QML-compatible model for settings management

#### Logic Components

- **logic/task_manager.py**: Manages asynchronous tasks
- **logic/audio_manager.py**: Handles audio playback
- **logic/speech_manager.py**: Manages speech recognition
- **logic/service_manager.py**: Manages external services
- **logic/websocket_client.py**: Handles WebSocket communication
- **logic/chat/**: Chat-related components
  - **core/chat_controller.py**: Main controller for chat functionality
  - **core/chatlogic.py**: Adapter for backward compatibility
  - **handlers/message_handler.py**: Processes chat messages

## Configuration System

The application uses a multi-layered configuration system:

1. **Module Configs**: Default configurations defined in Python modules (e.g., `frontend/stt/config.py`)
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
- `stt.STT_CONFIG.enabled` refers to the `enabled` key in the `STT_CONFIG` variable from the STT module
- `user.theme.is_dark_mode` refers to the `is_dark_mode` key in the `theme` section of the user config

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

And used in QML:

```qml
Repeater {
    model: settingsModel
    delegate: // ... render each category
}
```

## Signal Flow

The application uses Qt's signal/slot mechanism for communication between components:

1. **Python to Python**: Components emit signals that other Python components can connect to
2. **Python to QML**: Python signals are exposed to QML through properties and can trigger UI updates
3. **QML to Python**: QML calls Python methods through exposed slots and properties

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

## Best Practices

1. **Separation of Concerns**: Keep UI logic in QML and business logic in Python
2. **Asynchronous Operations**: Use `TaskManager` for async operations to avoid blocking the UI
3. **Configuration**: Store configuration in the appropriate place based on its nature
4. **Error Handling**: Use proper error handling and logging throughout the application
5. **Documentation**: Keep this document updated as the application evolves
