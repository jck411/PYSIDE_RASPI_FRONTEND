# Smart Screen Application Architecture

## Overview
This application is a PySide6-based smart screen interface designed to run on desktop computers and Raspberry Pi devices. It provides various screens including weather, chat, calendar, and more.

## Directory Structure
```
PYSIDE_RASPI_FRONTEND/
├── backend/             # Backend Python code
├── frontend/            # Frontend code (Python + QML)
│   ├── assets/          # JS, CSS, and other assets
│   ├── icons/           # Application icons and images
│   ├── qml/             # QML UI components and screens
│   └── main.py          # Application entry point
├── update_pyside6.sh    # Script to update PySide6 to the latest version
```

## Key Components

### Main Application (frontend/main.py)
The main entry point that initializes the QML engine, sets up services, and starts the event loop.

### Path Management
The application uses relative paths for resource files to ensure compatibility across different machines:

- **PathProvider**: A singleton service that provides the application's base path to QML components.
  - `basePath`: Property containing the application's base directory
  - `getAbsolutePath(relativePath)`: Method to convert relative paths to absolute paths

### Screens
The application includes multiple screens that can be navigated via the tab bar:

- **ChatScreen**: Conversational interface
- **WeatherScreen**: Displays weather information with animated Lottie icons
- **CalendarScreen**: Shows calendar events
- **ClockScreen**: Displays time and date
- **PhotoScreen**: Displays photos
- **SettingsScreen**: Application settings

### Services
Services provide functionality to QML components:

- **ThemeManager**: Manages light/dark theme switching
- **SettingsService**: Manages application settings
- **ErrorHandler**: Centralized error handling
- **ChatService**: Handles chat interactions

## Weather Screen Implementation
The WeatherScreen uses:
- Lottie animations for weather conditions
- PNG fallback icons
- National Weather Service (NWS) API for data (previously used OpenWeatherMap)

The screen is built as a modular component with clear separation of concerns:
- **WeatherScreen.qml**: Main container component that manages data fetching, UI components, and animations
- **ForecastDisplay.qml**: Shows multiple day forecast with PNG icons
- **WeatherControls.qml**: Provides navigation between Current Weather and Forecast views

### Weather UI Interaction
The Weather screen is interactive, allowing users to:
- Click on any weather section (current or forecast periods) to view detailed information
- See extended forecast details in a modal dialog with comprehensive weather data
- The dialog uses blur effects (via QtQuick.Effects) for a modern, frosted-glass appearance
- The dialog displays the relevant forecast period's detailed information in a readable format

### Weather UI Layout
The Weather screen layout uses a responsive design approach with:
- Text elements that have proper width constraints and text wrapping
- Layout.fillWidth and Layout.maximumWidth properties to prevent text overflow
- Text.elide and Text.WordWrap properties for proper text truncation and wrapping
- Horizontally centered content for a clean, aligned appearance
- Screen height-aware sizing with Layout.fillHeight and Layout.minimumHeight
- Weather sections that dynamically adjust to fill available screen space
- Responsive layout that works on different screen sizes and orientations
- Proper height constraints with Layout.maximumHeight to ensure sections stretch appropriately
- Flickable content area that fills the entire screen height

It uses the PathProvider to load resources with dynamic paths that work across different machines:
```qml
property string lottieIconsBase: PathProvider.getAbsolutePath("frontend/icons/weather/lottie/")
property string lottiePlayerPath: PathProvider.getAbsolutePath("frontend/assets/js/lottie.min.js")
property string pngIconsBase: "file://" + PathProvider.getAbsolutePath("frontend/icons/weather/PNG/")
```

## Visual Effects
The application uses modern visual effects for a polished user experience:

- **Blur Effects**: The application uses QtQuick.Effects (available in PySide6 6.5+) to implement blur effects for modal dialogs and popovers
  - For optimal blur performance, the implementation uses ShaderEffectSource to capture the entire screen content
  - MultiEffect is configured with appropriate blur parameters for the best balance of visual quality and performance
  - Dialog backgrounds have semi-transparent color overlays to ensure content readability
  - The detailed weather forecast popup uses a consistent visual style matching the active navigation buttons, with a solid primary button color and matching border
- **Gradient Overlays**: Semi-transparent gradients are used to create visual depth
- **Adaptive Theming**: All UI components respect the application's current theme settings

To enable these visual effects, the application requires PySide6 6.5 or later. A script is provided to upgrade to the latest version:
```bash
./update_pyside6.sh
```

The weather data is fetched from the National Weather Service API and then formatted to be compatible with the existing frontend UI structure. The backend handles the mapping of NWS weather icons and descriptions to the appropriate visual elements.