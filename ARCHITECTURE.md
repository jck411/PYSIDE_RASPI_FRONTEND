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
- **config_manager.py**: Advanced configuration management (handles loading/saving)
- **settings_service.py**: Unified service for accessing/modifying settings (wraps ConfigManager)
- **theme_manager.py**: Manages application theming (dark/light mode)

#### Logic Components

- **logic/resource_manager.py**: Unified manager for asynchronous tasks and service operations
- **logic/audio_manager.py**: Handles audio playback
- **logic/speech_manager.py**: Manages speech recognition
- **logic/websocket_client.py**: Handles WebSocket communication
- **logic/chat_controller.py**: Main controller for chat functionality that handles all chat-related operations
- **logic/message_handler.py**: Processes chat messages

## Configuration System

The application uses a multi-layered configuration system managed primarily by the `ConfigManager`:

1.  **Default Config**: Default configurations potentially defined in Python modules (e.g., `frontend.config` or feature-specific config modules).
2.  **User Config**: User-specific overrides stored in `~/.smartscreen_config.json`.

### ConfigManager

The `ConfigManager` class handles the low-level loading of configurations from modules and the user JSON file, as well as saving user overrides. It is primarily used internally by the `SettingsService`.

### SettingsService

The `SettingsService` class provides a simplified, unified, and singleton interface for the rest of the application (both Python and QML) to interact with settings. It wraps the `ConfigManager`.

**Accessing Settings (Python):**

```python
from frontend.settings_service import SettingsService

settings_service = SettingsService() # Get singleton instance

# Get a setting value
value = settings_service.getSetting("stt.STT_CONFIG.enabled", default=False)

# Set a setting value
success = settings_service.setSetting("stt.STT_CONFIG.enabled", True)

# Observe changes (connect to the signal)
def handle_change(path, new_value):
    print(f"Setting {path} changed to {new_value}")

settings_service.settingChanged.connect(handle_change)
```

**Accessing Settings (QML):**

The `SettingsService` is registered as a QML singleton `SettingsService` under the URI `MyServices`. Import it and use its methods:

```qml
import QtQuick 2.15
import MyServices 1.0

Item {
    property bool someSettingValue: false

    Component.onCompleted: {
        // Get initial value
        someSettingValue = SettingsService.getSetting("some.config.path", false)
    }

    Switch {
        checked: someSettingValue
        onToggled: {
            var success = SettingsService.setSetting("some.config.path", checked)
            if (success) {
                someSettingValue = checked
            } else {
                // Revert UI if setting failed
                checked = Qt.binding(function() { return someSettingValue; })
            }
        }
    }
}
```

Configuration paths follow the format `source.variable.key`:

-   `stt.STT_CONFIG.enabled` refers to the `enabled` key within the `STT_CONFIG` dictionary, loaded under the `stt` source key.
-   `server.SERVER_HOST` refers to the `SERVER_HOST` variable, loaded under the `server` source key.
-   `user.theme.is_dark_mode` refers to the `is_dark_mode` key within the `theme` dictionary in the user config file.

### Speech-to-Text Configuration

The Speech-to-Text system configuration can be accessed via `SettingsService` using paths starting with `stt.`: 

-   `stt.STT_CONFIG.enabled`: Global switch to enable/disable STT
-   `stt.STT_CONFIG.auto_start`: Whether to start STT automatically on initialization
-   `stt.STT_CONFIG.use_keepalive`: Whether to use KeepAlive for pausing/resuming during TTS
-   `stt.STT_CONFIG.auto_submit_utterances`: When enabled, complete utterances are automatically submitted to the chat instead of being placed in the input field (displayed as "Auto Send" in UI)

### STT Inactivity Timeout

To prevent STT from staying active indefinitely when no speech is detected, an inactivity timeout mechanism is implemented:

-   **Configuration**: The timeout duration is set via `stt.STT_CONFIG.inactivity_timeout_ms` in `frontend/config.py` (value in milliseconds, 0 disables the feature).
-   **Logic**: Primarily managed within `frontend/stt/deepgram_stt.py`.
    -   An internal `asyncio.Task` (`_inactivity_timer_task`) runs the timeout handler (`_inactivity_timeout_handler`) in a dedicated event loop (`dg_loop`).
    -   The start time (`_timer_start_time`) is recorded when the timer task begins.
    -   The timer task **starts** (via `_start_inactivity_timer`):
        -   When STT is initially enabled (`_async_start`).
        -   When STT resumes from pause (`set_paused(False)`).
        -   After receiving a **final** transcript segment (`result.is_final` is true in `on_transcript`).
    -   The timer task **cancels** (via `_cancel_inactivity_timer`):
        -   When STT is explicitly disabled (`set_enabled(False)`).
        -   When STT is paused (`set_paused(True)`).
        -   When *any* transcript text (interim or final) is received (`transcript.strip()` is true in `on_transcript`).
        -   On connection close/error (`_handle_close`, `_handle_error`).
    -   If the timer completes without being cancelled, the `_inactivity_timeout_handler` calls `self.set_enabled(False)` to turn off STT.
-   **State Querying**: `DeepgramSTT` provides `is_timer_running()` and `get_timer_remaining_ms()` methods. `SpeechManager` delegates calls to these methods. `ChatController` exposes QML-callable slots (`isSttEnabled`, `isSttInactivityTimerRunning`, `getSttInactivityTimeRemaining`) that use the `SpeechManager` methods.
-   **UI Feedback**: 
    - A visual countdown timer is displayed in `ChatControls.qml`, driven by the `remainingMs` property.
    - The `inactivityTimerStarted(int durationMs)` and `inactivityTimerStopped()` signals (relayed from `DeepgramSTT` -> `SpeechManager` -> `ChatController`) notify the UI about timer state changes.
    - On load/reload (`Component.onCompleted`), `ChatControls.qml` calls the state query methods on `ChatService` (`isSttEnabled`, `isSttInactivityTimerRunning`, etc.) to initialize the button and timer display correctly.

### STT/TTS Pause Interaction

- **Pausing STT during TTS**: When TTS audio starts playing, `ChatController._handle_audio_data` detects this and calls `SpeechManager.set_paused(True)`. This pauses the underlying STT engine (`DeepgramSTT`), which involves stopping the microphone (or activating KeepAlive) and cancelling the inactivity timer.
- **Resuming STT after TTS**: When TTS audio finishes, `ChatController._handle_audio_data` calls `SpeechManager.set_paused(False)`. This resumes the STT engine, ensuring the microphone is restarted and explicitly calls `_start_inactivity_timer()` to begin a fresh inactivity countdown.

### Settings UI Implementation

The settings UI (`SettingsScreen.qml`) directly interacts with the `SettingsService` to get and set configuration values. It uses a hardcoded layout for reliability and simplicity, mapping UI controls directly to specific configuration paths via `SettingsService.getSetting` and `SettingsService.setSetting`.

#### Adding New Settings to the UI

1.  **Ensure Config Exists**: Make sure the configuration variable and its default value exist in the appropriate Python config module and are loaded by `ConfigManager` (via `load_module_config` in `main.py`).
2.  **Frontend**: Add a new UI block (e.g., `RowLayout` with `Text` and a `Switch` or `TextField`) to the appropriate section in `SettingsScreen.qml`.
3.  **Connect UI**: 
    *   In `Component.onCompleted`, use `SettingsService.getSetting("your.config.path", default_value)` to initialize the UI control's state (e.g., a `property bool` backing a `Switch`).
    *   In the control's `onToggled`, `onAccepted`, or similar signal handler, call `SettingsService.setSetting("your.config.path", new_value)`.
    *   Update the local QML property based on the success of `setSetting`.
    *   Use the `Qt.binding` trick shown above to revert the UI control if `setSetting` fails.

This direct approach ensures type safety by exchanging only primitive types via the `SettingsService` and keeps the QML relatively simple.

#### Settings Interaction Logic

Note that within `SettingsScreen.qml`, there is specific interaction logic implemented between the "Auto Send" (`stt.STT_CONFIG.auto_submit_utterances`) and "Show Input Box" (`chat.CHAT_CONFIG.show_input_box`) settings:

*   **"Show Input Box" Visibility:** The UI row containing the toggle switch for "Show Input Box" is only visible when the "Auto Send" setting is enabled (checked).
*   **Disabling "Auto Send" forces "Show Input Box" ON:** If the user turns off the "Auto Send" switch, the code automatically forces the `chat.CHAT_CONFIG.show_input_box` setting to `true` via `SettingsService.setSetting`. The UI toggle for "Show Input Box" also becomes hidden.
*   **User Choice when Auto Send is ON:** When "Auto Send" is enabled, the user can freely toggle the "Show Input Box" setting using its dedicated switch.

This ensures that the input box is always available when STT results are not being automatically sent, while still providing the option to hide it when Auto Send is active.

## Signal Flow

The application uses Qt's signal/slot mechanism for communication between components:

1.  **Python to Python**: Components emit signals that other Python components can connect to (e.g., `SettingsService.settingChanged`).
2.  **Python to QML**: Python signals are exposed to QML through registered objects (like `SettingsService` or controllers registered via `qmlRegisterType`) and can trigger UI updates or actions.
3.  **QML to Python**: QML calls Python methods exposed as slots or methods on registered objects (e.g., `SettingsService.setSetting`, `ChatController.sendMessage`).

### Chat Signal Flow

The ChatController exposes several signals to QML:
- `messageReceived`: Emitted when a new message is received from the backend
- `messageChunkReceived`: Emitted when a streaming message chunk is received 
- `sttTextReceived`: Emitted when speech-to-text transcription arrives
- `sttInputTextReceived`: Emitted when a complete utterance should be set in the input field
- `userMessageAutoSubmitted`: Emitted when an utterance is auto-submitted to chat, ensuring it appears in the chat history
- `connectionStatusChanged`: Emitted when the WebSocket connection status changes
- `ttsStateChanged`: Emitted when the text-to-speech state changes
- `inactivityTimerStarted(int durationMs)`: Emitted when the STT inactivity timer starts, providing the total duration.
- `inactivityTimerStopped()`: Emitted when the STT inactivity timer stops (cancelled or completed).

These signals are relayed from `DeepgramSTT` -> `SpeechManager` -> `ChatController`.

## Adding New Features

### Adding a New Screen

1. Create a new QML file in `frontend/qml/` (e.g., `NewScreen.qml`) inheriting from `BaseScreen.qml`.
2. Create a corresponding controls file (e.g., `NewControls.qml`) inheriting from `BaseControls.qml`.
3. Add a navigation button in `MainWindow.qml` that loads the new screen.

### Adding a New Configuration Module

1. Create a new Python module (e.g., `frontend/new_feature/config.py`) containing configuration variables (dictionaries, strings, bools, etc.).
2. In `frontend/main.py`, add a call to `config_manager.load_module_config` to load variables from your new module under a unique `module_key`:

   ```python
   config_manager.load_module_config(
       module_path='frontend.new_feature.config', 
       module_key='new_feature', # Unique key for this config source
       config_vars=['FEATURE_SETTINGS', 'ANOTHER_VAR']
   )
   ```
3. Access these settings via `SettingsService` using paths like `'new_feature.FEATURE_SETTINGS.some_key'`.

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
// In MyScreen.qml
import "../BaseComponents"

BaseScreen {
    id: myScreen
    screenControls: "MyControls.qml" // Reference to its controls
    title: "My Screen"
    
    // Screen-specific content here
}
```

Control components inherit from BaseControls:
```qml
// In MyControls.qml
import "../BaseComponents"

BaseControls {
    id: myControls
    
    // Control-specific buttons and widgets here, e.g.:
    BaseControlButton {
        text: "Action"
        onClicked: {
            // Access parent screen via myControls.parentScreen
            console.log("Action clicked on", myControls.parentScreen.title)
        }
    }
}
```

This inheritance system makes it easier to:
- Add new screens and controls with consistent behavior
- Make global changes to all screens or controls
- Maintain a cleaner, more organized codebase

## Best Practices

1.  **Separation of Concerns**: Keep UI layout/presentation in QML and business logic/state management in Python.
2.  **Component Inheritance**: Use the base components for new screens and controls.
3.  **Asynchronous Operations**: Use appropriate async patterns (like `asyncio` integrated with the Qt event loop) or dedicated threads for long-running tasks to avoid blocking the UI.
4.  **Settings Management**: Use the `SettingsService` for all setting access and modification in both Python and QML.
5.  **Error Handling**: Implement robust error handling (see `frontend/error_handler.py`) and provide user feedback where appropriate (logging isn't always sufficient).
6.  **Singleton Pattern for Shared State**: For state that needs to persist across screen navigations (like chat history), use a singleton pattern. Register a single Python instance (e.g., `ChatController` as `ChatService`) using `qmlRegisterSingletonInstance` and access it directly from QML (`ChatService.method()`). Avoid creating stateful logic components directly within QML screens that are dynamically loaded/replaced.
7.  **Documentation**: Keep this document updated as the application evolves.

## Implementation Plan (Current Focus: Chat Enhancements)

This plan outlines the current development focus on improving the chat functionality and adding history persistence.

**Phase A: Chat Screen UI/UX Enhancements**
*   A.1: Implement STT Visual Indicator: **NOT STARTED**
*   A.2: Implement Option to Hide Chat Input Box: **DONE** (Implemented via Settings)

**Phase B: STT Logic Enhancements**
*   B.1: Implement STT Inactivity Timeout: **DONE**

**Phase C: Chat History Persistence**
*   C.1: Ensure Short-Term Persistence (Screen Switching): **DONE** (Achieved via `ChatService` singleton)
*   C.2: Implement Long-Term Conversation Storage: **PARTIALLY DONE**
    *   Current conversations are saved to timestamped JSON files in `chat_history/` upon clearing the chat or closing the application.
    *   Saving logic is handled by `ChatController._save_history_to_file`.
*   C.3: Implement Loading Last Conversation on Startup: **NOT STARTED**
*   C.4: Implement UI for Viewing Past Conversations (Deferred): **NOT STARTED**

**Phase D: Other Screens** (Deferred until Chat Enhancements are complete)
*   D.1: Implement Weather Screen Functionality: **NOT STARTED**
*   D.2: Implement Calendar Screen Functionality: **NOT STARTED**
*   D.3: Implement Photo Screen Enhancements: **NOT STARTED**

## Previous Implementation Plan Status (Archived)

This section tracks the progress of *previously completed* major refactoring and improvement efforts.

**Phase 1: Configuration System Overhaul**
*   1.1 Standardize Configuration Module Key Handling: **DONE**
*   1.2 Create a SettingsService Abstraction Layer: **DONE**
*   5.2 Optimize Startup Sequence: **NOT STARTED**.

## Common Issues and Solutions

### Configuration Management

Problems with settings not saving or loading correctly often stem from issues in the configuration layer.

#### Incorrect Configuration Path

**Problem**: `SettingsService.getSetting` returns the default value, or `setSetting` fails.
**Solution**: Double-check the configuration path string. It must match the `source.variable.key` structure precisely, where `source` is the `module_key` used in `load_module_config` (or `'user'` for user-specific settings), `variable` is the name of the dictionary or variable loaded from the module, and `key` is the nested key within that variable (if applicable).

#### Module Not Loaded

**Problem**: Settings from a specific module cannot be accessed.
**Solution**: Ensure the module's configuration is explicitly loaded using `config_manager.load_module_config` in `main.py` with the correct `module_path`, `module_key`, and `config_vars` list.

#### QML UI Not Updating

**Problem**: Changing a setting via `SettingsService.setSetting` doesn't update the bound QML UI control.
**Solution**: Ensure the QML code correctly updates its local state property after a successful `setSetting` call. If the Python component responsible for the underlying behavior needs to react to the change, connect it to the `SettingsService.settingChanged` signal.

#### Testing Configuration Changes

Before assuming configuration changes work, always test them thoroughly:

1.  Verify changes persist after restarting the application.
2.  Check the application logs (`~/.smartscreen.log`) for errors related to configuration loading or saving.
3.  Verify the actual behavior matches the expected setting (e.g., STT enabling/disabling).
4.  Inspect the user configuration file (`~/.smartscreen_config.json`) to see if overrides are being saved correctly.

### State Persistence Across Screens

**Problem**: State managed within a QML screen component (like chat history in `ChatScreen.qml`'s local `ListModel` or a locally instantiated controller) is lost when navigating away, especially when using `StackView.replace()` which destroys the old component instance.
**Solution**: Implement a singleton pattern for the stateful controller in Python.
1.  **Python**: Create a single instance of the controller (e.g., `chat_controller_instance = ChatController()`) in `main.py`.
2.  **Python**: Register this *instance* as a QML singleton using `qmlRegisterSingletonInstance(ControllerClass, "URI", 1, 0, "SingletonName", instance)` (e.g., `qmlRegisterSingletonInstance(ChatController, "MyServices", 1, 0, "ChatService", chat_controller_instance)`).
3.  **QML**: Remove any local instantiation of the controller within the screen QML (e.g., remove `ChatLogic { id: chatLogic }`).
4.  **QML**: Import the singleton's URI (e.g., `import MyServices 1.0`).
5.  **QML**: Access the singleton instance directly using its registered name (e.g., `ChatService.getHistory()`, `Connections { target: ChatService }`).
This ensures all QML components interact with the *same* persistent Python object, preserving state across navigations.

### QML UI Issues

#### QML/Python Type Conversion Errors

**Problem**: Errors like `Cannot assign QVariant to PySide::PyObjectWrapper` or `Cannot assign <PythonType> to <QMLType>` when receiving signals or calling methods between Python and QML.
**Solution**: 
1.  **Python to QML Signals**: When assigning the received signal value (`value`) to a QML property, explicitly cast it to the expected QML type: `qmlProperty = Boolean(value)`, `qmlProperty = Number(value)`, `qmlProperty = String(value)`. 
2.  **QML to Python Calls**: Ensure methods exposed from Python to QML (`@Slot`s) only accept and return primitive types (bool, int, float, string, list/dict of primitives) whenever possible. Avoid passing complex Python objects directly.

#### QML Binding Errors During Initialization/Destruction

**Problem**: Errors like `TypeError: Cannot read property '<property>' of null` or `TypeError: Cannot read property '<property>' of undefined` when binding a property in one component to a property in another component (e.g., `someProperty: otherComponent.someOtherProperty`). This often occurs during component loading or destruction when `otherComponent` might not be fully ready or is being torn down.
**Solution**: Make the binding more robust by adding checks or using fallback values:
*   Check for existence: `someProperty: otherComponent ? otherComponent.someOtherProperty : fallbackValue`
*   Check for property existence: `someProperty: otherComponent.someOtherProperty !== undefined ? otherComponent.someOtherProperty : fallbackValue`
*   Use a standard value (e.g., from `ThemeManager`) instead of relying on another component's state if possible.

By following these guidelines and using the `SettingsService` consistently, you can maintain a robust and understandable settings system.
