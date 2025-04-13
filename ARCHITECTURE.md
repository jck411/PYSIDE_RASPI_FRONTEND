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
- **PhotoScreen**: Displays photos and videos in a slideshow
- **SettingsScreen**: Application settings

### Services
Services provide functionality to QML components:

- **ThemeManager**: Manages light/dark theme switching
  - Supports manual light/dark mode toggling
  - Supports automatic day/night theme switching based on sunrise/sunset times
  - Obtains sunrise/sunset data from weather API
  - Persists theme preferences, including auto theme mode
  - Automatically checks day/night status periodically when auto mode is enabled
- **SettingsService**: Manages application settings
- **ErrorHandler**: Centralized error handling
- **ChatService**: Handles chat interactions
- **PhotoController**: Manages photo and video slideshow functionality

## Photo Screen Implementation
The PhotoScreen provides a slideshow of images and videos directly within the interface:

- **PhotoController**: Python class that manages the slideshow logic
  - Loads media files (both images and videos) from a specified directory
  - Handles automatic advancement for images using a QTimer
  - Provides signals for media changes and slideshow state
  - Includes methods for manual navigation (next/previous)
  - Special handling for videos to ensure they play to completion before advancing
  - Creates blurred background versions of images for an aesthetic display
  - Emits signals when blurred backgrounds are ready for the UI to display

- **PhotoProcessor**: Python class for advanced image processing
  - Applies effects to images such as shadows and frames
  - Creates blurred background images using PIL/Pillow
  - Implements a multi-step blur process:
    1. Downsampling the image to a small size (20x20 pixels)
    2. Rescaling back up to create a pixelation effect
    3. Applying Gaussian blur for smoothing
    4. Darkening the result for better contrast with foreground content
  - Caches processed images to improve performance
  - Uses tempfile directory for storing cached images

- **PhotoScreen.qml**: QML component that displays both images and videos
  - Uses dual Image components for displaying photos with smooth crossfade transitions:
    - Maintains two overlapping image elements with controlled opacity animations
    - New images load in the inactive element while keeping the current image visible
    - Only transitions after the new image is fully loaded to prevent blank screens
    - Uses a 1-second fade duration with InOutQuad easing for a professional look
    - Implements status change handlers to trigger transitions only when images are ready
    - Ensures the background is never visible during transitions for a seamless experience
  - Uses QtMultimedia 6.0 for video playback with MediaPlayer and VideoOutput components
  - Displays an initial photo immediately upon loading the screen
  - Features a Python-generated blurred background for photos:
    - Uses the current image, blurred and darkened for an aesthetic background
    - Falls back to a theme-adaptive gradient background when no image is available
    - Handles transitions between images with synchronized background changes
  - Automatically advances slideshows for images
  - Includes touch/click functionality for manual navigation (for images)
  - Shows overlay information about the current media item
  - Gracefully handles component cleanup during application shutdown

- **PhotoControls.qml**: Provides navigation controls
  - Uses TouchFriendlyButton components for consistent styling with other controls
  - Includes SVG icons with tooltips for better usability
  - Play/Pause button to control automatic advancement (with icon that changes based on state)
  - Next/Previous buttons for manual navigation
  - Back button to return to the previous screen

The implementation follows a clean separation of concerns:
- Python handles the media file management, image processing, and slideshow logic
- QML handles the display of media and user interaction
- The controller coordinates the interaction between the UI and the media files

## Advanced PhotoScreen Features

### Crossfade Transitions
The PhotoScreen implements a seamless crossfade system for transitioning between images:

1. **Dual Image Architecture**
   - Uses two Image components (photoImage1 and photoImage2) that occupy the same space
   - Only one image is visible at full opacity at any time (controlled by isImage1Active property)
   - New images are loaded into the inactive image element while the active one remains visible

2. **Smooth Animation System**
   - Implements Behavior on opacity with NumberAnimation for smooth transitions
   - Uses a 1-second duration with InOutQuad easing for professional fade effects
   - Transitions are triggered only when the new image is fully loaded
   - Background image transitions are synchronized with foreground crossfades

3. **Smart Image Loading**
   - Image.onStatusChanged handlers monitor loading progress
   - Transitions are only triggered when Image.Ready status is achieved
   - Prevents showing blank/empty images during loading
   - Provides debug logging of image loading states

4. **Fixed Sequential Navigation**
   - Images are displayed in a fixed order based on filename sorting
   - Navigation buttons move sequentially through this order
   - Previous/Next functionality for intuitive browsing
   - Automatic advancement during slideshow mode
   
This implementation ensures there's always a visible image during transitions and the background is never revealed, creating a polished, professional user experience.

### Video Handling
The application fully supports videos in the slideshow using QtMultimedia 6.0:
- Videos are played directly in the UI using the MediaPlayer and VideoOutput components
- Automatic advancement after the video completes playing
- Fallback mechanism with a timer if video fails to play
- Error handling for problematic video files
- Visual feedback during video playback
- Automatic detection of video formats based on file extension

## Weather Screen Implementation
The WeatherScreen uses:
- Lottie animations for current weather conditions
- PNG icons for forecast displays
- National Weather Service (NWS) API for weather data
- Sunrise-sunset.org API for accurate sunrise and sunset times

The screen is built as a modular component with clear separation of concerns:
- **WeatherScreen.qml**: Main container component that manages data fetching, UI components, and animations
- **ForecastDisplay.qml**: Original component for OpenWeatherMap forecasts (maintained for compatibility)
- **SevenDayForecast.qml**: Component that displays forecasts for the next 12 periods (skipping the first 2 periods shown in the 72-hour view) with static PNG icons in a stacked row layout, showing detailed forecast information in each row
- **HourlyWeatherGraph.qml**: Component that displays a 24-hour temperature and precipitation forecast graph using Canvas for temperature line plotting and bars for precipitation probability
- **WeatherControls.qml**: Provides navigation between Current Weather (72 Hour), Hourly Graph, and 7-Day Forecast views

### Weather UI Interaction
The Weather screen is interactive, allowing users to:
- Click on any weather section in the current weather view to view detailed information
- Toggle between the 72-hour view (with Lottie animations), the hourly graph view (with temperature trends and precipitation), and the 7-day forecast view
- The 7-day forecast displays comprehensive details directly in each row, eliminating the need for additional popups
- Each forecast row includes the date, icon, temperature, and a detailed description
- The dialog for the current weather sections uses blur effects (via QtQuick.Effects) for a modern, frosted-glass appearance

### Hourly Weather Graph
The hourly weather graph provides a visualization of temperature and precipitation forecast for the next 24 hours:
- Temperature is displayed as a connected line graph with data points and labels
- Precipitation probability is shown as vertical bars at the bottom of the graph
- Time labels along the bottom show the time for each hour in the forecast
- The graph automatically scales based on minimum and maximum temperatures in the forecast
- Precipitation probability is extracted from forecast text when explicit values aren't available
- Sunrise and sunset times are indicated with sun icons at the top of the graph
- Sunrise is marked with a full sun icon and golden/orange color
- Sunset is marked with a half-sun icon and salmon/tomato color 
- Current time is indicated by bolding and slightly enlarging the relevant time label on the x-axis
- Time labels update automatically every minute
- The graph is fully responsive and adapts to different screen sizes
- Theme-aware color scheme matches the application's light/dark theme

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

### 7-Day Forecast Layout
The 7-day forecast view uses:
- A structured grid layout with dedicated columns for each data element
- Each row displays:
  - The date in a dedicated column
  - Day/Night indicator as plain text in its own column
  - Weather icon column
  - Temperature column
  - Detailed forecast description with text wrapping
- Alternating background colors for better readability
- Fixed height rows with proper spacing between columns
- Better alignment of elements using GridLayout instead of nested rows

### Weather Icon Implementation
The application supports two types of weather icons:
1. **Lottie Animations**: Used for the current weather view (72-hour forecast) with smooth animations
2. **Static PNG Icons**: Used for the 7-day forecast view

It uses the PathProvider to load resources with dynamic paths that work across different machines:
```qml
property string lottieIconsBase: PathProvider.getAbsolutePath("frontend/icons/weather/lottie/")
property string lottiePlayerPath: PathProvider.getAbsolutePath("frontend/assets/js/lottie.min.js")
property string pngIconsBase: "file://" + PathProvider.getAbsolutePath("frontend/icons/weather/PNG/")
```

#### Icon Mapping
Both icon types use a consistent mapping system to convert NWS (National Weather Service) icon URLs to the appropriate animations or PNG files. The mapping includes day and night variations for:
- Clear skies
- Cloudy conditions
- Rain and precipitation
- Snow and winter weather
- Extreme weather events (hurricanes, tornados)
- Special conditions (fog, haze, wind)

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

The weather data is fetched from the National Weather Service API and then formatted to be compatible with the existing frontend UI structure. The backend handles the mapping of NWS weather icons and descriptions to the appropriate visual elements.

### Weather Display Improvements (May 2025)
- **Observation Time Display:** The CurrentWeather component shows "as of" the actual observation time from the National Weather Service, providing users with the exact time of the weather reading.
- **Real-time Data:** The application always displays the most current observation data available from NWS, refreshing automatically every 30 minutes.
- **UI Text Update:** The "As of" text in the current weather section uses the observation timestamp to accurately reflect when the weather reading was taken.
- **Code Cleanup:** Removed unused properties and functions from the CurrentWeather component to maintain code cleanliness.

### Weather Fetching Optimizations (May 2025)
- **Concurrent API Requests:** Modified the weather fetcher to use `asyncio.gather()` for parallel requests, significantly reducing total fetch time.
- **Request Timeouts:** Added explicit timeouts to prevent the application from hanging on slow network connections.
- **Accurate Data Only:** The system strictly displays only real data from the National Weather Service, with clear status messages when data is not yet available.
- **Sunrise/Sunset Integration:** The weather API provides sunrise and sunset data that is used for the automatic day/night theme switching feature.

### OpenWeatherMap Integration (June 2025)
- **OpenWeatherMap API:** Integrated OpenWeatherMap One Call 3.0 API for more accurate current weather data, replacing NWS for current conditions.
- **Two API Calls Design:** Implementation makes two concurrent API calls:
  1. Current weather + minutely rain forecast (1 API call)
  2. Human-readable weather overview (1 API call)
- **Current Weather Card:** The current weather card displays OpenWeatherMap data including:
  - Current temperature
  - "Feels like" temperature
  - Weather description
  - Wind speed and direction
  - Humidity
- **Enhanced Detailed View:** When clicking on the current weather card, users see:
  - Human-readable weather overview
  - Minute-by-minute rain forecast for the next 30 minutes (if available)
- **NWS Data Preserved:** NWS data is still used for hourly and daily forecasts, preserving forecast capabilities.
- **Environment Variables:** API key is stored in the `.env` file as `OPENWEATHER_API_KEY`.
- **Concurrent Fetching:** Both NWS and OpenWeatherMap data are fetched concurrently to minimize loading times.
- **Manual Refresh:** Added a manual refresh button that updates both OpenWeatherMap current data and NWS forecasts:
  - Sends a POST request to a dedicated refresh endpoint
  - Forces immediate fetch of new data from all sources 
  - Provides visual feedback during the refresh process
  - Updates all views after refresh completion

### Sunrise and Sunset Data Enhancement (April 2025)
- **Dedicated API Integration:** Added integration with the sunrise-sunset.org API for accurate sunrise and sunset time data.
- **Improved Reliability:** Implemented a fallback mechanism that uses NWS grid forecast data when the specialized API is unavailable.
- **Error Handling:** Added comprehensive error handling to ensure the application continues to function even when sunrise/sunset data is unavailable.
- **Time Format Compatibility:** Enhanced the time formatting functions to handle various ISO 8601 time formats from different APIs.
- **Visual Display:** Optimized the hourly graph to display sunrise and sunset information in a clean, user-friendly manner with appropriate icons.

## Calendar Screen Implementation

The CalendarScreen provides an intuitive calendar interface with simplified navigation between views:

### Key Features
- **Two Primary View Modes:**
  - **Month View:** Traditional calendar grid displaying the entire month
  - **Week View:** Focused 7-day view showing more event details
- **Day View Navigation:**
  - Tapping/clicking on any day cell in month or week view navigates to that day's detailed view
  - Back button appears in day view to return to the previous view (month or week)
- **Seamless View Transitions:**
  - The system remembers which view (month or week) was active before entering day view
  - When returning from day view, the user is taken back to their previous context
- **Simple Toggle:**
  - A calendar icon with a badge indicating the current view mode (M/W/D) allows quick switching between views

### Current Implementation
The calendar implementation consists of:
- `CalendarScreen.qml`: Main container that switches between view modes
- `UnifiedCalendarView.qml`: Implements the month view with a grid layout 
- `CustomCalendarView.qml`: Implements week/day views with a column layout
- `CalendarController.py`: Backend class that provides data models and navigation logic

### Refactoring Guidelines

The calendar implementation should be refactored to address several issues:

1. **Vertical Cell Expansion:**
   - Currently, day cells have fixed heights which truncate event display
   - Cells should expand vertically when events can't fit in the fixed space
   - Implement with ScrollView or proper height calculations based on event count

2. **Scrolling for Expanded Content:** 
   - When expanded cells exceed available screen space, the view should be scrollable
   - This requires proper configuration of ScrollView containers with correct policies

3. **Component Architecture:**
   - Extract reusable components:
     - `BaseCalendarView.qml`: Shared base functionality
     - `DayCell.qml`: Reusable day cell component
     - `CalendarEvent.qml`: Single-day event component
     - `MultiDayEvent.qml`: Multi-day event component
     - `WeekdayHeader.qml`: Weekday header component

4. **Implementation Challenges:**
   - ListView vs. ScrollView for events: Use ScrollView with Column for better scrolling
   - Dynamic height calculation: Account for multi-day events at the top of cells
   - Nested ScrollViews: Can cause input handling issues with event propagation
   - Segmentation faults: Be careful when modifying existing code, test incrementally

5. **Data Model Structure:**
   - Day objects include:
     - `date`: ISO date string
     - `day`: Day number as string
     - `isCurrentMonth`: Whether this day is in the current month
     - `isToday`: Whether this day is today
     - `events`: Array of event objects
     - `multiDayEvents`: Special handling for events spanning multiple days

### Future Implementation Approach

When implementing the refactoring:

1. Start by defining shared utility functions in a JavaScript file
2. Implement improvements to the existing views first before extracting components
3. Extract components one at a time, testing thoroughly after each extraction
4. Implement vertical scrolling at the appropriate level (calendar view vs. day cell)
5. Test thoroughly with many events in a single day

## Development Notes & Known Issues

This section captures insights gained during recent debugging and cleanup efforts (April 2025).

### PhotoScreen Optimization (April 2025)
- **Crossfade Implementation:** The PhotoScreen was enhanced with a dual-image crossfade system that ensures seamless transitions between images. This prevents any "blank screen" moments during image loading and creates a more polished user experience.
- **Navigation Simplification:** The navigation system was simplified to use a fixed, sequential order based on filename sorting, making navigation more predictable and intuitive for users.
- **Image Loading Logic:** Image loading was improved to prevent QML errors during rapid navigation and ensure transitions only happen when images are fully loaded.
- **Debug Logs:** Additional logging was added to track image loading states and transition events, aiding future debugging efforts.

### Dependency Management
- The project's dependencies are managed via `requirements.txt`.
- Initial analysis revealed the file was incomplete (missing `requests`, `fastapi`, `openai`, `Pillow`, etc.) and contained an unused package (`numpy`).
- The `requirements.txt` file has been updated (April 2025) to accurately reflect runtime dependencies identified through code analysis for both frontend and backend. `pydub` was excluded as it appeared only necessary for a utility script (`frontend/wakeword/convert_format.py`).
- **Recommendation:** Regularly verify `requirements.txt` against actual imports using tools like `pipreqs` or manual analysis, especially after adding/removing features.

### Code Style & Quality
- Static analysis using `flake8` identified numerous unused imports, a redefined function (`setup_chat_client` in `backend/config/config.py`), and an unused local variable (`msg_type` in `frontend/logic/message_handler.py`). These were removed.
- `flake8` also identified many stylistic issues (line length, whitespace, indentation).
- Automatic formatting using `black` has been applied to resolve most stylistic issues and enforce consistency. Most remaining `flake8` warnings are related to line length (E501), which `black` sometimes preserves for readability.
- **Recommendation:** Consider integrating `flake8` and `black` into the development workflow (e.g., pre-commit hooks) to maintain code quality.

### Runtime Issues & Fixes (Observed April 2025)
- **Chat History Path (Fixed):** An error preventing chat history saving was identified due to a hardcoded user path (`/home/jack/...`) in `frontend/logic/chat_controller.py` (`_save_history_to_file` function). This caused a permission error for the actual user (`human`). The path was corrected to use a relative path (`./chat_history`) within the project directory. Ensure this directory exists or can be created by the application.
- **Audio Configuration (Known Issue):** Logs showed numerous ALSA/JACK errors (e.g., `unable to open slave`, `Unknown PCM cards`, `Cannot open device /dev/dsp`). This indicates potential audio system misconfiguration on the target Linux environment (Raspberry Pi) that could cause instability and requires platform-specific investigation.
- **Shutdown Error (Known Issue):** A QML TypeError (`PhotoController.stop_slideshow not available during cleanup`) occurs during application shutdown, originating from `PhotoScreen.qml`. This suggests an object lifetime or shutdown sequence issue between QML and the Python `PhotoController` that needs further debugging.
- **Deepgram Connection (Observation):** Deepgram connection closure warnings and task cancellation errors were observed, potentially linked to shutdown or inactivity.

## Recent UI Updates (April 2025)

This section documents specific UI changes implemented recently:

### Weather Controls (`frontend/qml/WeatherControls.qml`)
- **Button Text:** The "7 Day Forecast" navigation button text was shortened to "7 Day".
- **Selected Style:** The visual style for the selected navigation button ("72 Hour" or "7 Day") was updated. The semi-transparent background was removed, and a solid border with the color `#565f89` is now used to indicate selection.
- **Button Width:** Both the "72 Hour" and "7 Day" buttons were set to a fixed `implicitWidth` of 90 pixels for visual consistency.

### Calendar Controls (`frontend/qml/CalendarControls.qml`)
- **Refresh Button:** A new refresh button was added using the `../icons/refresh.svg` icon (consistent with the Weather screen).
- **Functionality:** This button is intended to trigger a data refresh/sync for calendar events and is currently configured to call `CalendarController.refreshEvents()`.

### Main Navigation (`frontend/qml/MainWindow.qml`)
- **Icon Reordering:** The Photos and Clock icons in the main navigation bar were swapped to improve workflow. The order is now: Chat, Weather, Calendar, Photos, Clock, Theme Toggle, Settings.
- **Alignment:** This change provides a more logical grouping by placing the visual content screens (Photos) closer to the Calendar and Weather, with utility screens (Clock, Settings) grouped together.

## Future Development Tips

Based on recent work, consider the following for future development:

- **Implement `CalendarController.refreshEvents()`:** Ensure the Python method `CalendarController.refreshEvents()`

## Code Maintenance

### Empty Files and Clean Code
This codebase maintains a policy of avoiding empty or unused files. Empty files like `backend/weather/current.py` that are not referenced anywhere have been cleaned up to maintain code cleanliness. Empty `__init__.py` files are kept as they are necessary for Python package structure.

Several minimal files exist in the codebase that serve important purposes:
- `backend/weather/state.py`: Contains a global variable to store the latest weather data
- `backend/endpoints/state.py`: Contains event flags used for controlling async operations

Regular code maintenance tasks include:
- Removing unused files and code
- Ensuring proper Python package structure 
- Maintaining clean imports and dependencies
- Refactoring files that grow beyond 200-300 lines
- Periodically checking for dead code or unused modules

### Code Organization
The codebase follows these organizational principles:
- Clear separation between backend and frontend components
- Module-specific subdirectories for related functionality (e.g., weather, tts)
- State management via lightweight state modules with clear interfaces
- Event-driven mechanisms for async operations
- Clean import structure to avoid circular dependencies

### Tool Functions Architecture
The application uses a modular tool functions system that allows for easy extension with new capabilities:

- **Individual Tool Modules**: Each tool function is in its own file (e.g., `weather.py`, `time.py`)
  - Each module exposes one primary function (e.g., `fetch_weather`, `get_time`)
  - Each module provides a `get_schema()` function that defines its OpenAI function calling schema
  - Functions can be synchronous or asynchronous (using `async/await`)

- **API Integration**:
  - `weather.py`: Uses OpenWeatherMap API for current weather and National Weather Service API for forecasts
  - `time.py`: Uses TimezoneFinder and pytz for accurate local time

- **Tool Registry** (`registry.py`): Central management of all available tools
  - Automatically discovers and registers tool modules (both sync and async functions)
  - Provides `get_tools()` to retrieve all schema definitions
  - Provides `get_available_functions()` to map function names to implementations

- **Tool Helpers** (`helpers.py`): Utilities for tool execution
  - Validates function arguments
  - Maps OpenAI function call requests to actual Python implementations
  - Handles execution of both synchronous and asynchronous functions

This architecture allows for easy extension by simply adding new Python files to the tools directory, following the pattern of existing tools. The registry will automatically discover and register new tools without requiring changes to other parts of the codebase.

### Utility Services
The application includes several utility services to provide common functionality:

#### MarkdownUtils
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