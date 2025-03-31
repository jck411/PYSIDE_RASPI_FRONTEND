# PySide Raspberry Pi Frontend Architecture

This document provides a high-level overview of the architecture and design principles for the **frontend** of the PySide Raspberry Pi application, serving as a guide for frontend development.

## Project Overview

A Qt/QML application for Raspberry Pi providing a touch-friendly **frontend** interface with Chat, Weather, Calendar, Clock, Photo Viewer, and Settings screens. Built with Python (PySide6) backend and QML frontend.

## Core Components

### UI Layer (QML)

- **MainWindow.qml**: Main window, navigation, screen management.
- **BaseScreen.qml**: Base for all screens (common structure).
- **BaseControls.qml**: Base for screen-specific control bars.
- **BaseControlButton.qml**: Reusable button component.
- **[Screen]Screen.qml**: Specific screen implementations (e.g., `ChatScreen.qml`).
- **[Screen]Controls.qml**: Screen-specific controls (e.g., `ChatControls.qml`).

### Backend (Python)

- **main.py**: Entry point, initialization.
- **config.py**: Basic configuration, logging.
- **config_manager.py**: Handles loading/saving configuration.
- **settings_service.py**: Singleton interface for settings access (wraps `ConfigManager`).
- **theme_manager.py**: Manages theming.

#### Logic Components

- **logic/resource_manager.py**: Manages async tasks/service ops.
- **logic/audio_manager.py**: Audio playback.
- **logic/speech_manager.py**: Speech recognition.
- **logic/websocket_client.py**: WebSocket communication.
- **logic/chat_controller.py**: Chat functionality controller.
- **logic/message_handler.py**: Processes chat messages.

## Configuration System

Uses a multi-layered system managed by `ConfigManager`:
1.  **Default Config**: Defined in Python modules.
2.  **User Config**: Overrides in `~/.smartscreen_config.json`.

### ConfigManager

Handles low-level loading/saving of configs. Used internally by `SettingsService`.

### SettingsService

Provides a unified singleton interface for Python and QML to interact with settings.

**Accessing Settings (Python):**

```python
# Get singleton instance
settings_service = SettingsService()
# Get/Set a value
value = settings_service.getSetting("source.variable.key", default=None)
success = settings_service.setSetting("source.variable.key", new_value)
# Observe changes
settings_service.settingChanged.connect(handler_func)
```

**Accessing Settings (QML):**

Registered as `SettingsService` singleton (URI `MyServices`).

```qml
import MyServices 1.0

Item {
    property bool setting: SettingsService.getSetting("some.config.path", false)
    // ... Use SettingsService.setSetting(...) in event handlers
}
```

Configuration paths use `source.variable.key` format (e.g., `stt.STT_CONFIG.enabled`, `user.theme.is_dark_mode`).

### Speech-to-Text Configuration (`stt.*`)

Key settings accessed via `SettingsService`:
-   `stt.STT_CONFIG.enabled`: Global STT toggle.
-   `stt.STT_CONFIG.auto_start`: Start STT automatically.
-   `stt.STT_CONFIG.use_keepalive`: Use KeepAlive during TTS pause.
-   `stt.STT_CONFIG.auto_submit_utterances`: Auto-send completed utterances to chat ("Auto Send" UI).
-   `stt.STT_CONFIG.inactivity_timeout_ms`: Timeout (ms) to disable STT if no speech detected (0 = disabled).

### STT Inactivity Timeout

- Managed in `frontend/stt/deepgram_stt.py` using an `asyncio` timer.
- Timer starts on STT enable/resume/final transcript.
- Timer cancels on STT disable/pause/any transcript received.
- If timer completes, STT is disabled.
- State/remaining time queryable via `ChatController` slots for UI feedback.

### STT/TTS Pause Interaction

- `ChatController` pauses STT (`SpeechManager.set_paused(True)`) when TTS starts (cancels inactivity timer).
- `ChatController` resumes STT (`SpeechManager.set_paused(False)`) when TTS ends (restarts inactivity timer).

### Settings UI Implementation (`SettingsScreen.qml`)

- Directly uses `SettingsService.getSetting` and `SettingsService.setSetting`.
- Layout maps UI controls to config paths.
- Contains sections for different setting categories (e.g., STT, UI).

#### Adding New Settings to the UI

1.  Ensure config exists in a Python module (e.g., `frontend/ui/config.py` for UI settings) and is loaded in `main.py` via `config_manager.load_module_config` (using a key like `'ui'`).
2.  Add UI controls to the relevant section in `SettingsScreen.qml`.
3.  Use `SettingsService.getSetting` to initialize UI state (e.g., `'ui.WINDOW_CONFIG.fullscreen'`) and `SettingsService.setSetting` in event handlers.
4.  If the setting affects the main window or other persistent components, ensure they connect to `SettingsService.settingChanged` signal and update accordingly (see `MainWindow.qml` for fullscreen example).

#### Settings Interaction Logic (Auto Send / Show Input Box)

- "Show Input Box" (`chat.CHAT_CONFIG.show_input_box`) UI is hidden if "Auto Send" (`stt.STT_CONFIG.auto_submit_utterances`) is OFF.
- Disabling "Auto Send" forces "Show Input Box" ON via `SettingsService.setSetting`.

### Adding a New Configuration Module

1. Create a Python config file (e.g., `frontend/new_feature/config.py` or `frontend/ui/config.py`).
2. Define configuration dictionaries (e.g., `WINDOW_CONFIG`).
3. Load it in `main.py` using `config_manager.load_module_config(module_path='...', module_key='new_feature', config_vars=[...])`.
4. Access settings via `SettingsService` using `'module_key.VARIABLE.key'` (e.g., `'ui.WINDOW_CONFIG.fullscreen'`).

## Signal Flow

Uses Qt's signal/slot mechanism:
1.  **Python <-> Python**: Standard Qt signals/slots.
2.  **Python -> QML**: Signals exposed via registered objects (e.g., `SettingsService`, Controllers).
3.  **QML -> Python**: Calling Python methods exposed as slots on registered objects.

### Chat Signal Flow

`ChatController` emits signals (relayed from underlying services) to QML for:
- New messages/chunks (`messageReceived`, `messageChunkReceived`)
- STT updates (`sttTextReceived`, `sttInputTextReceived`, `userMessageAutoSubmitted`)
- Connection status (`connectionStatusChanged`)
- TTS state (`ttsStateChanged`)
- STT inactivity timer status (`inactivityTimerStarted`, `inactivityTimerStopped`)

## Adding New Features

### Adding a New Screen

1. Create `NewScreen.qml` inheriting from `BaseScreen.qml`.
2. Create `NewControls.qml` inheriting from `BaseControls.qml`.
3. Add navigation in `MainWindow.qml`.

## Component Inheritance System

Promotes UI consistency and code reuse.

### Base Components

- **BaseScreen**: Common screen structure, properties (`screenControls`, `title`), content area.
- **BaseControls**: Common control bar layout, screen reference (`parentScreen`).
- **BaseControlButton**: Reusable button with standard look/feel.

### Inheritance Pattern

Screens inherit `BaseScreen`, Controls inherit `BaseControls`.

```qml
// MyScreen.qml
import "../BaseComponents"
BaseScreen { screenControls: "MyControls.qml"; title: "My Screen"; /* ...content... */ }

// MyControls.qml
import "../BaseComponents"
BaseControls { /* ...buttons using BaseControlButton... */ }
```

## Best Practices

1.  **Separation of Concerns**: QML for UI, Python for logic/state.
2.  **Component Inheritance**: Use base components.
3.  **Asynchronous Operations**: Use `asyncio`/threads for non-blocking tasks.
4.  **Settings Management**: Use `SettingsService` exclusively.
5.  **Error Handling**: Implement robust error handling (`frontend/error_handler.py`).
6.  **Singleton Pattern for Shared State**: Use singletons (e.g., `ChatController` registered as `ChatService`) for state persisting across screens. Access via registered name (e.g., `ChatService.method()`).
7.  **Documentation**: Keep this document updated.

## Weather Screen Implementation

The Weather Screen uses Lottie animations for displaying weather conditions. These animations are implemented as follows:

### Lottie Animation Integration

- **Animation Files**: Stored in `frontend/icons/weather/lottie/` as JSON files.
- **Lottie Player**: A local copy of the Lottie player (`lottie.min.js`) is stored in `frontend/assets/js/` for offline operation.
- **Display Method**: Using WebEngineView to render HTML content with the local Lottie player.
- **Loading Process**: 
  - JSON animation files are loaded via XMLHttpRequest
  - The local Lottie player script is referenced using the file:// protocol
  - Both are combined into HTML content rendered by WebEngineView

### Required Environment Configuration

- The `QML_XHR_ALLOW_FILE_READ=1` environment variable must be set in `main.py` to enable loading local JSON files and JavaScript through XMLHttpRequest.
- This configuration is essential for the Weather screen's Lottie animations to work properly.

### Icon Mapping

- Weather condition codes from OpenWeatherMap API are mapped to corresponding Lottie animation files in the `getWeatherIconPath` function.
- The mapping follows this pattern:
  ```
  "01d": "clear-day"             // clear sky day
  "01n": "clear-night"           // clear sky night
  // etc.
  ```

### Error Handling

- Robust error handling includes checks for:
  - File access permissions
  - JSON parsing errors
  - Network/loading errors
  - Fallback to default animations when specific ones aren't available

### Forecast Implementation (Added March 31, 2025)

The Weather Screen was enhanced to display a 5-day forecast below the current weather conditions.

- **Data Source**: The forecast data is retrieved from the `daily` array within the JSON response provided by the backend's `/api/weather` endpoint. This endpoint caches data fetched by `backend/weather/fetcher.py` from the OpenWeatherMap One Call API.
- **Displayed Information**: For each of the 5 forecast days (excluding the current day), the following is displayed:
    - Day and Date (e.g., "Mon 03/31") using the `formatDateToDay` helper function.
    - Weather condition icon (using static SVGs from `frontend/icons/weather/` via `getWeatherSvgIconPath` helper function for performance).
    - High and Low temperatures (e.g., "75° / 55°").
    - Percentage Chance of Precipitation (PoP) (e.g., "30% rain").
- **Layout**:
    - The forecast items are arranged horizontally using a `RowLayout`.
    - Both the current weather and the forecast sections are placed within a `ColumnLayout`.
    - The entire content area (`ColumnLayout`) is wrapped in a `Flickable` to allow vertical scrolling if the content exceeds the screen height.
- **Development Notes & Troubleshooting**:
    - An initial attempt was made to refactor the screen into `CurrentWeatherDisplay.qml` and `ForecastDisplay.qml` components. However, persistent layout issues (overlapping, incorrect positioning) arose, likely due to complexities in nested layouts, height calculations, and interactions with `Flickable`.
    - To resolve these issues and simplify the structure, the UI elements and logic were merged back into a single `WeatherScreen.qml` file.
    - Layout adjustments included removing explicit heights on child components, removing conflicting anchors within the `Flickable`'s content, adjusting spacing and margins, and ensuring the `RowLayout` fills available width.
    - Date formatting initially used `toLocaleDateString`, but was changed to manual formatting using `getDay()` and an array lookup for better reliability in the QML environment.
    - The `SettingsService` was updated to expose the `httpBaseUrl` as a QML property to fix an issue where the weather API URL was not being constructed correctly.

## Implementation Plan (Current Focus: Chat Enhancements)

**Phase A: Chat Screen UI/UX Enhancements**
*   A.1: Implement STT Visual Indicator: **NOT STARTED**
*   A.2: Implement Option to Hide Chat Input Box: **DONE** (Implemented via Settings)

**Phase B: STT Logic Enhancements**
*   B.1: Implement STT Inactivity Timeout: **DONE**

**Phase C: Chat History Persistence**
*   C.1: Ensure Short-Term Persistence (Screen Switching): **DONE** (`ChatService` singleton)
*   C.2: Implement Long-Term Conversation Storage: **PARTIALLY DONE**
*   C.3: Implement Loading Last Conversation on Startup: **NOT STARTED**
*   C.4: Implement UI for Viewing Past Conversations (Deferred): **NOT STARTED**

**Phase D: UI Enhancements** (Renamed from "Other Screens")
*   D.1: Add Fullscreen Toggle Setting: **DONE**
*   D.2: Weather Screen: **DONE** (Implemented with Lottie animations)
*   D.3: Calendar Screen: **NOT STARTED**
*   D.4: Photo Screen: **NOT STARTED**

## Previous Implementation Plan Status (Archived)

**Phase 1: Configuration System Overhaul**
*   1.1 Standardize Config Module Key Handling: **DONE**
*   1.2 Create SettingsService: **DONE**
*   5.2 Optimize Startup: **NOT STARTED**.

## Common Issues and Solutions

### Configuration Management

-   **Incorrect Path**: Double-check `source.variable.key` format for `SettingsService` calls.
-   **Module Not Loaded**: Ensure `config_manager.load_module_config` is called in `main.py`.
-   **QML UI Not Updating**: Ensure QML updates local state after `setSetting`, and connect Python components to `settingChanged` signal if needed.

### State Persistence Across Screens

-   **Problem**: State lost on navigation (esp. `StackView.replace`).
-   **Solution**: Use Python singleton pattern. Register controller instance via `qmlRegisterSingletonInstance` in `main.py`. Access directly in QML using registered name (e.g., `ChatService`).

### QML UI Issues

-   **Type Conversion Errors**: Explicitly cast types between Python/QML (`Boolean(val)`, `Number(val)`, etc.). Use primitive types for `@Slot` arguments/returns.
-   **Binding Errors**: Use checks (`component ? component.prop : fallback`) for bindings that might reference null/undefined components during init/destruction.
