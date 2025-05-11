# Overview and Structure

## Application Overview
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

## Path Management
The application uses relative paths for resource files to ensure compatibility across different machines:

- **PathProvider**: A singleton service that provides the application's base path to QML components.
  - `basePath`: Property containing the application's base directory
  - `getAbsolutePath(relativePath)`: Method to convert relative paths to absolute paths

## Screen Navigation
Screens can be navigated in two ways:
- Via the top navigation bar buttons in MainWindow.qml
- Via screen-specific control buttons (e.g., ClockScreen's "Show Alarms" button navigates to AlarmScreen, and AlarmScreen's "Show Clock" button navigates back to ClockScreen)

The navigation is handled using the StackView component, with each screen having access to the MainWindow's stackView for navigation between screens.

Screen controls maintain consistent navigation patterns:
- Each screen has its own controls file (e.g., ClockControls.qml, AlarmControls.qml) that inherits from BaseControls
- Navigation buttons use consistent icons across screens
- Related screens maintain simple, bidirectional navigation
- Controls are positioned on the left side of the screen using a simple Row layout
- The MainWindow's screenControlsLoader positions and initializes all controls consistently 