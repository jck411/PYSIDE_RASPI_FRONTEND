# Key Components

## Main Application (frontend/main.py)
The main entry point that initializes the QML engine, sets up services, and starts the event loop.

## Screens
The application includes multiple screens that can be navigated via the tab bar:

- **ChatScreen**: Conversational interface
- **WeatherScreen**: Displays weather information with animated Lottie icons
- **CalendarScreen**: Shows calendar events
- **ClockScreen**: Displays time and date with a digital clock
- **AlarmScreen**: Dedicated screen for managing alarms
- **TimerScreen**: Countdown timer functionality
- **PhotoScreen**: Displays photos and videos in a slideshow
- **SettingsScreen**: Application settings

## Services
Services provide functionality to QML components:

- **ThemeManager**: Manages light/dark theme switching
  - Supports manual light/dark mode toggling
  - Supports automatic day/night theme switching based on sunrise/sunset times
  - Obtains sunrise/sunset data from weather API
  - Persists theme preferences, including auto theme mode
  - Automatically checks day/night status periodically when auto mode is enabled
- **SettingsService**: Manages application settings
  - Provides a unified interface for accessing and modifying application settings
  - Supports both boolean and string setting types
  - Emits signals when settings are changed for reactive UI updates
  - Used for alarm and timer sound settings, UI preferences, and STT configuration
- **AudioManager**: Handles audio playback and processing
  - Supports configurable notification sounds for different features
  - Can play different sounds for alarms and timers based on user settings
  - Dynamically discovers available sound files in the sounds directory
  - Provides methods for testing sound selections in the UI
  - Handles sound file loading, validation, and fallback to defaults when needed
- **ErrorHandler**: Centralized error handling
- **ChatService**: Handles chat interactions
- **PhotoController**: Manages photo and video slideshow functionality

## Visual Effects
The application uses modern visual effects for a polished user experience:

- **Blur Effects**: The application uses QtQuick.Effects (available in PySide6 6.5+) to implement blur effects for modal dialogs and popovers
  - For optimal blur performance, the implementation uses ShaderEffectSource to capture the entire screen content
  - MultiEffect is configured with appropriate blur parameters for the best balance of visual quality and performance
  - Dialog backgrounds have semi-transparent color overlays to ensure content readability
  - The detailed weather forecast popup uses a consistent visual style matching the active navigation buttons, with a solid primary button color and matching border
- **Gradient Overlays**: Semi-transparent gradients are used to create visual depth
- **Adaptive Theming**: All UI components respect the application's current theme settings
  - Automatic day/night theme switching based on sunrise/sunset times
  - Theme transitions are smooth and consistent across the UI
  - Theme preferences (including auto mode) are persisted between sessions
  - Settings screen allows users to toggle automatic theme mode

To enable these visual effects, the application requires PySide6 6.5 or later. A script is provided to upgrade to the latest version:
```bash
./update_pyside6.sh
``` 