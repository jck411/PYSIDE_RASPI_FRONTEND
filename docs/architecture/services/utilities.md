# Utility Services

The application includes several utility services to provide common functionality:

## MarkdownUtils
A service that provides conversion of markdown formatting to HTML for rich text display in QML:

- **markdownToHtml(text)**: Converts markdown syntax to HTML for use in QML Text elements with textFormat: Text.RichText
- Supports common markdown syntax:
  - **bold text** for bold formatting
  - *italic text* for italic formatting
  - `code` for inline code
  - [link text](url) for hyperlinks
  - Line breaks converted to HTML <br> tags

The utility is registered as a QML singleton and can be used in any QML file:
```qml
import MyUtils 1.0  // Import the utility module

Text {
    text: MarkdownUtils.markdownToHtml("**Bold** and *italic* text")
    textFormat: Text.RichText  // Required for HTML formatting
    onLinkActivated: Qt.openUrlExternally(link)  // Handle any links
}
```

The implementation provides a clean separation between the text formatting logic (Python) and the UI display (QML), ensuring consistent text formatting across the application.

## AudioManager
Handles audio playback and processing:

- Supports configurable notification sounds for different features
- Can play different sounds for alarms and timers based on user settings
- Dynamically discovers available sound files in the sounds directory
- Provides methods for testing sound selections in the UI
- Handles sound file loading, validation, and fallback to defaults when needed

## PathProvider
A singleton service that provides the application's base path to QML components:

- `basePath`: Property containing the application's base directory
- `getAbsolutePath(relativePath)`: Method to convert relative paths to absolute paths

The PathProvider is used throughout the application to ensure consistent path handling:

```qml
property string lottieIconsBase: PathProvider.getAbsolutePath("frontend/icons/weather/lottie/")
property string lottiePlayerPath: PathProvider.getAbsolutePath("frontend/assets/js/lottie.min.js")
property string pngIconsBase: "file://" + PathProvider.getAbsolutePath("frontend/icons/weather/PNG/")
```

This approach ensures that resources are correctly loaded regardless of the current working directory.

## ThemeManager
Manages application theming with light/dark mode support:

- Supports manual light/dark mode toggling
- Supports automatic day/night theme switching based on sunrise/sunset times
- Obtains sunrise/sunset data from weather API
- Persists theme preferences, including auto theme mode
- Automatically checks day/night status periodically when auto mode is enabled

## SettingsService
Provides a unified interface for accessing and modifying application settings:

- Supports both boolean and string setting types
- Emits signals when settings are changed for reactive UI updates
- Used for alarm and timer sound settings, UI preferences, and STT configuration
- Provides methods for retrieving, setting, and testing settings
- Handles persistence of settings across application sessions 