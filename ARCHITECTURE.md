# Smart Screen Application Architecture

This is a PySide6-based smart screen interface for desktop and Raspberry Pi with screens for weather, chat, calendar, clock, alarms, timer, and photos. It features a conversational interface, real-time weather data, and smooth transitions between views.

## Core Architecture

- [Overview and Structure](docs/architecture/1-overview.md)  
  *PySide6-based application with modular frontend/backend separation. Uses StackView for navigation between screens, with consistent control patterns across screens.*

- [Key Components](docs/architecture/2-key-components.md)  
  *Main screens include Chat, Weather, Calendar, Clock, Alarm, Timer, Photos, and Settings. Core services provide theming, settings management, audio playback, and error handling. Supports modern visual effects like blur and gradient overlays.*

## Screen Implementations

- [Weather Screen](docs/architecture/screens/weather.md)  
  *Shows weather using Lottie animations and PNG icons. Features 72-hour view, hourly graph (with temperature/precipitation), and 7-day forecast. Data from NWS and OpenWeatherMap APIs with background timer improvements.*

- [Photo Screen](docs/architecture/screens/photo.md)  
  *Slideshow with crossfade transitions and blurred backgrounds. Supports both images and videos using a dual-image architecture for smooth transitions. Special handling ensures videos play to completion.*

- [Calendar Screen](docs/architecture/screens/calendar.md)  
  *Provides month, week, and day views with seamless transitions. Current implementation needs refactoring for better vertical expansion and scrolling of day cells with many events.*

- [Clock and Alarm Screen](docs/architecture/screens/clock-alarm.md)  
  *Digital clock with date display and integrated alarm management system. Supports one-time and recurring alarms with configurable notification sounds. Recent UI improvements for better alarm creation.*

- [Timer Screen](docs/architecture/screens/timer.md)  
  *Countdown timer with tumbler interface for time selection. Features preset buttons, pause/resume controls, and customizable sound notifications. Integrates with chat for natural language timer creation.*

## Development Guidelines

- [Code Maintenance](docs/architecture/development/code-maintenance.md)  
  *Guidelines for keeping code clean and organized. Removes unused files, maintains Python package structure, and enforces 200-300 line limit for files. Uses modular tool functions system for easy extension.*

- [UI Updates](docs/architecture/development/ui-updates.md)  
  *Recent UI improvements including alarm screen enhancements, calendar controls additions, and navigation icon reordering. Follows QML design principles focusing on simplicity and minimal properties.*

- [Known Issues](docs/architecture/development/known-issues.md)  
  *Documented runtime issues including audio configuration problems on Raspberry Pi, shutdown errors with PhotoController, and fixes for time parsing in the alarm system.*

## Utilities and Services

- [Navigation System](docs/architecture/services/navigation.md)  
  *Natural language navigation via chat commands. Supports conversational commands like "show weather" and navigation to sub-screens. Uses multi-tiered matching for precise command recognition.*

- [Time Context Management](docs/architecture/services/time-context.md)  
  *Provides accurate time awareness for LLM interactions. Updates time information based on location coordinates and configurable intervals. Returns comprehensive time info including date, day of week, and time of day.*

- [Natural Language Commands](docs/architecture/services/natural-language.md)  
  *Command processors for timer and alarm functionality that intercept chat input. Uses regex patterns to match commands and extract parameters. Recent improvements for AM/PM time handling. Now preserves LLM responses when executing commands rather than replacing them with generic responses.*

- [Tool Orchestration](docs/architecture/services/tool-orchestration.md)  
  *Manages parallel and sequential execution of tools based on dependencies. Automatically runs navigation tools in parallel with other operations. Handles tool dependencies by creating execution batches and passing outputs between tools. Uses asyncio.gather() for parallel execution of independent tools. As of May 2025, synchronous tool functions are executed using asyncio.to_thread() to avoid blocking the event loop, improving performance and responsiveness when running sync and async tools together.*

- [Connection-Aware Tools](docs/architecture/services/connection-tools.md)  
  *Tools that maintain awareness of which WebSocket connection initiated a request. Provides connection context throughout the tool execution pipeline. Ensures responses and navigation actions are directed to the originating client. Enhances multi-user support by preventing broadcasts to all connections.*

- [Utility Services](docs/architecture/services/utilities.md)  
  *Common utilities including MarkdownUtils for text formatting, AudioManager for sound playback, PathProvider for consistent resource paths, ThemeManager for light/dark theme switching, and SettingsService for application preferences.*

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
- **ClockScreen**: Displays time and date with a digital clock
- **AlarmScreen**: Dedicated screen for managing alarms
- **TimerScreen**: Countdown timer functionality
- **PhotoScreen**: Displays photos and videos in a slideshow
- **SettingsScreen**: Application settings

### Screen Navigation
Screens can be navigated in two ways:
- Via the top navigation bar buttons in MainWindow.qml
- Via screen-specific control buttons (e.g., ClockScreen's "Show Alarms" button navigates to AlarmScreen, and AlarmScreen's "Show Clock" button navigates back to ClockScreen)
- Via natural language commands processed by `NavigationController` or backend `navigate_to_screen` tool.
- **NEW**: Via wakeword "hey computer", which automatically navigates to `ChatScreen.qml` if the user is on a different screen before activating voice interaction.

The navigation is handled using the StackView component, with each screen having access to the MainWindow's stackView for navigation between screens.

`NavigationController` (`frontend/logic/navigation_controller.py`) now includes:
- A `currentScreenName` Q_PROPERTY (type `str`) that stores the QML filename of the currently displayed screen (e.g., "ChatScreen.qml").
- A slot `setCurrentScreenName(screen_name: str)` called by `MainWindow.qml`.
- `MainWindow.qml`, in its `StackView.onCurrentItemChanged` handler, determines the QML filename of the new `currentItem` (usually from `currentItem.sourceComponent.url`) and calls `NavigationController.setCurrentScreenName()` to keep it updated.

The "hey computer" wakeword flow is as follows:
1. `WakeWordHandler` detects "hey computer".
2. It calls a dedicated method in `ChatController` (e.g., `handle_hey_computer_wakeword`).
3. `ChatController` retrieves the `currentScreenName` from `NavigationController`.
4. **IMPROVED (September 2025)**: Now uses asynchronous parallel processing:
   - Immediately starts preparing voice interaction (wake sound) in the background
   - Simultaneously triggers navigation to ChatScreen if not already there
   - Both operations run concurrently for faster responsiveness
   - Only waits for navigation if needed, while voice preparation continues
   - Finalizes voice activation (enabling STT/TTS) after navigation is complete
5. The parallel approach ensures faster response to wake word detection by eliminating sequential waiting.

Screen controls maintain consistent navigation patterns:
- Each screen has its own controls file (e.g., ClockControls.qml, AlarmControls.qml) that inherits from BaseControls
- Navigation buttons use consistent icons across screens
- Related screens maintain simple, bidirectional navigation:
  - ClockScreen has a "Show Alarms" button that navigates to AlarmScreen
  - AlarmScreen has a "Show Clock" button that navigates back to ClockScreen
- Controls are positioned on the left side of the screen using a simple Row layout
- The MainWindow's screenControlsLoader positions and initializes all controls consistently

### Clock and Alarm Architecture
The application provides both time display and alarm management functionality:

- **ClockScreen**: Focused on displaying the current time and date with a large, easy-to-read digital display
  - Shows hours, minutes, seconds in a large font
  - Displays current date (month, day, year)
  - Shows the day of the week

- **AlarmScreen**: Dedicated screen for managing alarms
  - Displays a list of configured alarms with time, name, and recurrence pattern
  - Provides controls to add, edit, and delete alarms
  - Supports various recurrence patterns (Once, Daily, Weekdays, Weekends, Custom)
  - Includes improved property binding for alarm IDs to ensure reliable alarm deletion
  - Uses multiple fallbacks for property access to handle different controller implementations
  
- **Alarm Notifications**: When an alarm triggers, a notification dialog is shown
  - The notification appears over any screen that's currently active
  - Offers options to dismiss or snooze the alarm
  - Snoozing an alarm creates a new one-time alarm for 5 minutes later

- **Timer Functionality**: Manages countdown timers with a flexible interface
  - **TimerScreen**: Dedicated UI for creating and managing timers
    - Shows active timer with hours, minutes, seconds countdown
    - Includes tumbler controls for setting time values
    - Supports timer naming for identification
    - Provides controls for pause, resume, and cancel operations
  - **TimerController**: Core class that manages timer state and operations
    - Handles countdown logic with a QTimer for accurate timing
    - Emits signals for timer completion and state changes
    - Provides methods for starting, pausing, stopping, and extending timers
    - Implements a persistent timer state across application sessions
    - Automatically navigates to the TimerScreen when a timer is started, resumed, paused, stopped, or extended.
    - **Function Call API**: Provides a schema-based API for LLM integration
      - Supports direct timer creation via `create_timer()` method
      - Accepts parameters for name, hours, minutes, seconds, and auto-start option
      - Returns structured response with success status and message
      - Can be called from any part of the application without UI navigation
      - Integrates with chat interface for natural language timer creation
  - **Sound Notifications**: Plays configurable alert sounds when timer completes
    - Uses application's AudioManager for consistent sound handling
    - Supports customizable sound selection via settings
  - **Integration with Chat**: Allows timer creation through natural language
    - Parses timer commands like "set timer for 5 minutes"
    - Processes function call requests with structured timer parameters
    - Voice commands are integrated directly via the TimerCommandProcessor
    - Supports various command formats like "set timer to 15 minutes" or "set timer for 10 minutes"
    - Improved flexibility for cancellation commands (e.g., "cancel" or "cancel timer") in TimerCommandProcessor.
    - Responds to timer commands with natural language responses
    - Prevents navigation-only behavior by processing timer commands before navigation commands

- **AlarmController**: Manages alarm data and functionality
  - Located in `frontend/logic/alarm_controller.py`
  - Provides methods for adding, updating, and deleting alarms
  - Handles alarm persistence via JSON file storage
  - Exposes signals to QML for alarm triggering and list updates
  - Follows camelCase naming conventions for QML-exposed methods
  - Enhanced error handling and validation for alarm management operations
  - Improved debugging for alarm deletion with detailed logging

- **Sound Notification Settings**: Configurable sound notifications for alarms and timers
  - Each feature (alarm/timer) can have its own distinct notification sound
  - Sounds can be selected from available .raw files in the sounds directory
  - Settings are persisted using the SettingsService
  - Includes test functionality to preview sounds before saving
  - Automatically detects available sound files in the sounds directory
  - Settings UI is integrated into the SettingsScreen with other application settings

### Services
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

### Weather Screen Timer Improvements (July 2025)
- **Enhanced Timer Management**: Implemented robust timer handling in WeatherScreen.qml:
  - Added safety checks before starting/stopping timers to prevent duplicate timer instances
  - Implemented explicit cleanup in Component.onDestruction to ensure timers are properly stopped
  - Added detailed logging for timer state changes to aid in debugging and monitoring
  - Enhanced error handling with specific handlers for different error types
  - Added timeout handling to prevent application hangs during network issues
  - Implemented comprehensive retry mechanism for all error conditions
- **Error Handling Improvements**:
  - Added specific error handlers for timeouts, network errors, and request failures
  - Implemented try/catch blocks around network operations to handle exceptions
  - Enhanced status message display with more detailed error information
  - Added validation of received data to prevent processing of invalid or incomplete responses
- **Logging Enhancements**:
  - Added structured logging with context information for easier debugging
  - Reduced verbose output of large response objects to improve log readability
  - Added specific log messages for different timer state transitions
  - Improved error logging with more context about the nature of failures
- **Navigation Parameter Support** (July 2025):
  - Added proper handling of navigation parameters for switching between weather views
  - Fixed missing _navigationParams property in WeatherScreen component
  - Improved WeatherControls to use NavigationController for consistent navigation
  - Enhanced debugging and logging for parameter handling
  - Added fallback to default view when no parameters are provided
  - Implemented mainStackView reference in WeatherControls for direct navigation

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

## Clock Screen Implementation
The ClockScreen provides time/date display plus an integrated alarm management system:

- **Dual-View Interface**: The ClockScreen has two main screens, accessed via dedicated navigation buttons:
  - ClockScreen: Large, prominent time/date display
  - AlarmScreen: List of alarms with management controls

- **Navigation Controls**: Both screens have a consistent set of navigation buttons:
  - Clock button: Navigates to the ClockScreen
  - Alarm button: Navigates to the AlarmScreen
  - Both controls appear in the same position across both screens for consistent navigation

- **Alarm Management**: Users can create, edit, disable, and delete alarms
  - One-time alarms for specific times
  - Recurring alarms with various patterns:
    - Daily alarms
    - Weekday alarms (Mon-Fri)
    - Weekend alarms (Sat-Sun)
    - Custom day selection for any combination of days

- **AlarmController**: Backend class that manages the alarm system
  - Event-based triggering using Qt's timer and signal/slot system
  - Persistent storage of alarm configurations in JSON format
  - Smart scheduling that minimizes resource usage by calculating the exact time until the next alarm
  - Automatic handling of recurrence patterns

- **UI Components**:
  - Alarm list with visual indicators for recurrence patterns
  - Time selection interface using tumbler controls for intuitive time picking
  - Alarm setup dialog with various recurrence options
  - Notification dialog with snooze functionality
  - Dedicated navigation buttons for moving between clock and alarm screens
  - Floating action button for adding new alarms, positioned in the bottom-right of the alarm list
  - Modern UI with theme-aware styling

### Alarm Edit Screen Layout Update (May 2025)
- **Improved Layout**: The alarm edit screen layout was restructured to use a more intuitive arrangement
  - The screen title and name field are positioned side by side at the top of the form
  - Save and Cancel buttons are now positioned at the bottom right of the screen
  - The main content area is organized into three distinct columns:
    - Left column: Time selection with hour/minute tumblers
    - Middle column: Repeat options (Once, Daily, Weekdays, etc.)
    - Right column: Custom day selection (only visible when "Custom" is selected)
  - Column headings are precisely aligned at the same height for visual consistency
  - Content in each column starts at the same vertical position with consistent spacing
- **Enhanced Usability**: The new layout is more consistent with standard form design patterns
  - Improved visual hierarchy with the heading and name field at the top
  - Action buttons (Save/Cancel) are consistently positioned at the bottom right
  - Content organized into logical columns that flow left-to-right
  - Custom days appear as an extension of the repeat options when needed
  - Better use of screen space for a cleaner, more organized interface
  - Consistent spacing and alignment across all form sections

## Timer Screen Implementation
The TimerScreen provides a countdown timer with intuitive controls:

- **Time Selection Interface**: Uses tumblers to select hours, minutes, and seconds
  - Hour tumbler with values from 0-23
  - Minute tumbler with values from 0-59
  - Second tumbler with values from 0-59
  - Tumblers follow the same styling as the alarm edit interface

- **Quick Preset Buttons**: Preset time durations for common use cases
  - 1 minute preset
  - 5 minute preset
  - 10 minute preset
  - 30 minute preset
  - Clicking a preset immediately sets the tumblers to the corresponding time

- **Timer Controls**:
  - Start button to begin the countdown
  - Pause button to temporarily halt the countdown
  - Resume button to continue after pausing
  - Reset button to stop and reset the timer
  - Buttons dynamically show/hide based on the timer's current state

- **Timer Display**: Shows the remaining time in large, easy-to-read format
  - Display format automatically switches between MM:SS and HH:MM:SS as needed
  - Updates every second while the timer is running

- **Timer Notification**: When the timer completes, a notification dialog appears
  - Plays an alarm sound using the same AudioManager as the alarm feature
  - Notification includes a dismiss button to close the dialog and stop the sound

- **Navigation**: The screen includes the same navigation structure as Clock and Alarm screens
  - Clock button to navigate to the ClockScreen
  - Alarm button to navigate to the AlarmScreen
  - Timer button for the current screen

The timer implementation is purely client-side within QML, using the built-in Timer component for the countdown functionality. This provides a responsive user experience without requiring backend processing.

The UI follows the same design principles as the Clock and Alarm screens, maintaining visual consistency through the use of:
- Consistent color scheme from ThemeManager
- Matching font styles and sizes
- Similar layout structure and component spacing
- Consistent button styling with accent colors for primary actions
- Uniform dialog design for notifications

## UI Updates (May 2025)

This section documents recent UI changes:

### Alarm Screen UI Enhancement (May 2025)
- **In-List Add Button**: Replaced the floating action button with an integrated "Add new alarm" button within the alarm list
- **Consistent Visual Design**: The add button uses the same styling as alarm list items for visual consistency
- **SVG Icon Integration**: Incorporated the `alarm_add.svg` icon for better visual recognition
- **Improved Usability**: The add button now appears at the bottom of the alarm list, making it easy to find and use
- **Alternating Colors**: The add button respects the same alternating color scheme as the alarm items
- **Simplified Interaction**: Clean implementation that retains theme-consistent styling
- **Implementation Details**: The add button is implemented as a footer component in the ListView with:
  - Matching height and visual style to alarm list items for consistency
  - Proper color alternation based on the number of items in the list
  - Clear visual indication of its purpose with icon and text
  - Same interaction pattern as alarm items (tap/click to activate)
  - Responsive layout that adapts to different screen sizes

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

### Async Operations Optimization
The application implements several optimizations for asynchronous operations:

- **Shared HTTP Client**: Uses a singleton SharedHTTPClient for all network requests
  - Implements connection pooling and session reuse to reduce connection overhead
  - Properly closes connections during application shutdown using registered cleanup tasks
  - Centralizes timeout handling for all HTTP operations
  - Eliminates the overhead of creating new sessions for each API request
  - Significantly improves TTS and navigation responsiveness by reusing established connections

- **Screen Name Detection Optimization**: Improved screen name determination in MainWindow.qml
  - Simplified complex URL parsing logic with a clearer, prioritized approach
  - Uses direct property access when available for better performance
  - Improved readability and maintainability with helper functions
  - Reduces error potential by prioritizing more reliable property access methods
  - Falls back to URL parsing only as a last resort

- **Robust Error Handling**: Improved resilience with comprehensive error handling
  - Each async operation has appropriate try/except blocks with specific error types
  - Returns partial data when possible instead of failing completely
  - Includes detailed error logging with traceback information for easier debugging
  - Uses asyncio.TimeoutError handling to prevent hanging operations

- **Timeout Management**: Multiple layers of timeout protection
  - Per-request timeouts for individual HTTP requests
  - Operation-level timeouts using asyncio.wait_for
  - Global timeouts for concurrent operations with asyncio.gather
  - Function-specific timeouts based on operation type (e.g., longer for weather API calls)

- **Concurrent Operations**: Efficiently executes parallel tasks
  - Uses asyncio.gather for concurrent API requests
  - Properly handles exceptions in concurrent tasks without failing the entire operation
  - Balances parallelism with proper resource management
  - Implements proper task cancellation during shutdown

- **Graceful Shutdown**: Ensures all resources are properly released
  - Registers cleanup tasks at application startup
  - Uses an extensible cleanup system in backend.utils.shutdown
  - Properly closes HTTP client connections during application shutdown
  - Cancels and awaits running background tasks during shutdown

This approach ensures the application remains responsive during network operations while efficiently managing system resources.

### Tool Functions Architecture
The application uses a modular tool functions system that allows for easy extension with new capabilities:

- **Tool Registry**: Central management of all available tool functions
  - Auto-discovers tool functions in the `backend/tools` directory
  - Dynamically generates function schemas for API documentation
  - Enforces consistent error handling and parameter validation
  - Provides a unified interface for both synchronous and asynchronous tools

- **One Tool Per Module Pattern**: Each module in the tools directory exposes one primary tool function
  - `backend/tools/sunrise_sunset.py`: `get_sunrise_sunset` - Gets precise sunrise and sunset times for any location
  - `backend/tools/weather_current.py`: `get_weather_current` - Gets current weather conditions (temperature, description, etc.)
  - `backend/tools/weather_forecast.py`: `get_weather_forecast` - Retrieves detailed weather forecasts for upcoming days
  - `backend/tools/time.py`: `get_time` - Retrieves the current time for a specific location based on coordinates
  - Each module has a `get_schema()` function that defines its OpenAI function calling schema
  - Consistent naming pattern (module name directly reflects its functionality) makes it easier for LLMs to understand and use tools

- **Code Reuse Pattern**: The tool functions follow a consistent pattern to promote code reuse:
  - Tool functions import and call existing specialized fetcher functions
  - Tool functions focus on formatting and filtering data for LLM consumption
  - API interaction logic is centralized in dedicated fetcher modules
  - This pattern ensures:
    - Consistent error handling
    - No duplication of API fetch logic
    - Separation of concerns between data fetching and LLM formatting
    - Easier maintenance when APIs change

- **Future Tools**: The architecture is designed for easy extension with new tools
  - Create new Python modules in `backend/tools` with standardized schema definitions
  - Follow consistent naming pattern (module name should directly reflect its functionality)
  - Follow consistent error handling patterns
  - Support both synchronous and asynchronous operations
  - Reuse existing fetcher functions when possible
  - Each new module should expose one primary tool function

This modular approach makes it easy to add new capabilities without modifying the core application architecture.

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

### Bug Fixes (May 2025)
- **Navigation and QML Component Simplification:** Fixed "Property has already been assigned a value" errors by:
  1. Eliminating complex code that was causing property conflicts
  2. Drastically simplifying the AlarmScreen.qml to remove unnecessary properties and functions
  3. Using direct StackView.replace() with string paths for navigation
  4. Removing excessive error handling and utility files that were adding complexity
  
  This approach aligns with best practices: minimizing the codebase and eliminating complexity rather than adding layers to work around issues.

- **AlarmNotificationDialog Creation (Fixed):** Fixed through simplification - by removing the complex dialog creation code that was no longer needed in our minimal implementation.

### QML Design Philosophy (May 2025)

The application follows these guidelines for component design and navigation:

1. **Simplicity First**
   - Keep components as simple as possible with minimal properties
   - Avoid complex property bindings that can lead to conflicts
   - Use direct string paths for navigation (e.g., `stackView.replace("ScreenName.qml")`)

2. **Minimize Property Usage**
   - Define only essential properties in components
   - Avoid redefining properties that exist in parent components
   - Be cautious with property initialization, especially for complex types

3. **Direct Navigation**
   - Navigate between screens using simple StackView operations
   - Keep navigation logic straightforward without excessive error handling
   - Avoid creating intermediate components dynamically when possible

4. **Modular Components**
   - Break large components into smaller, focused ones
   - Keep files under 200-300 lines for maintainability
   - Separate visual elements from business logic

These principles help avoid common QML issues like property binding conflicts and component creation errors.

## Time Context Management

The application provides time awareness for LLM interactions, ensuring that the AI assistant has access to accurate current time information without explicitly asking:

### TimeContextManager
A backend component in `backend/tools/time.py` that manages time context updates:
- Regularly updates current time information based on location coordinates
- Uses an event-driven architecture with callbacks for time updates
- Automatically refreshes time information at configurable intervals (default: every 60 seconds)
- Provides timezone-aware time based on geolocation coordinates
- Implemented as an asyncio-based service that runs in the background

### Comprehensive Time Tool
Instead of injecting time context into messages, the system uses a tool-based approach:
- The `get_time()` function provides comprehensive time information for any query
- Returns detailed information including current time, date, day of week, month, year
- Provides calendar-related calculations like days until end of month/year
- Determines time of day (morning, afternoon, evening, night)
- Includes information about yesterday, today, and tomorrow
- Formats nicely summarized time information for easy reference

### System Prompt Time Instructions
The system uses explicit instructions in the system prompt:
- Instructs the LLM to always check the current time for any time-related queries
- Lists specific scenarios when the time function should be used
- Prevents the LLM from guessing or assuming time information without checking
- Makes time awareness automatic for the AI assistant

This implementation ensures the AI assistant always provides accurate time information for any time-related query (not just predefined questions). The approach is robust to format constraints and allows the LLM to access time information on demand while following the expected messaging format.

## Natural Language Navigation

The application includes a natural language navigation system that allows users to navigate between screens using conversational commands.

### Natural Language Navigation Features

- **Conversational Navigation Commands**: Users can navigate the application with natural language commands:
  - "Show me the weather"
  - "Go to calendar"
  - "Open photos" 
  - "I want to see the clock"
  - "Show alarm screen"
  - "Show timer"
  - "Display settings"

- **Sub-Screen Navigation**: The system supports navigation to specific sub-screens:
  - "Show hourly weather" - navigates to the hourly weather graph
  - "Show 7 day forecast" - navigates to the 7-day forecast view
  - "Show current weather" - navigates to the main weather view
  - Additional sub-screens for other components can be easily added

- **Dual Navigation Mechanisms**:
  1. **Direct UI Command Processing**: Commands entered in the chat input are intercepted and processed before being sent to the LLM
  2. **LLM Tool Calling**: The LLM can call navigation functions directly using the function calling API

- **Precise Command Matching**:
  - Multi-tiered matching algorithm to prevent navigation to incorrect screens
  - Pattern-based extraction of screen names from natural language
  - Whole-word and exact keyword matching to minimize false positives
  - Prefix matching for partial commands (e.g., "alarm" matches "alarms")
  - Detailed logging for troubleshooting navigation issues

- **Consistent Navigation Patterns**:
  - All screens use the same navigation system
  - Natural language commands are processed consistently
  - The system handles variations in phrasing and wording
  - Commands work regardless of capitalization or precise wording

### Navigation Architecture

- **NavigationController**: Core controller that manages natural language navigation
  - Maps keywords to screen names
  - Processes natural language commands using regex patterns
  - Uses multiple matching algorithms for precision and flexibility
  - Special handling for sub-screen navigation with parameters
  - Emits signals to trigger screen navigation
  - Handles backend navigation requests with parameters

- **Integration with Chat Interface**:
  - ChatController intercepts navigation commands before sending to LLM
  - Provides immediate response to navigation requests
  - Prevents unnecessary LLM API calls for basic navigation

- **LLM Function Calling**:
  - Backend defines a `navigate_to_screen` function
  - LLM can call this function to trigger navigation
  - Function accepts screen name and optional parameters
  - Multi-tiered matching to handle various screen name formats
  - Parameters can be passed to control screen behavior (e.g., viewType for weather screens)

- **MainWindow Integration**:
  - Listens for navigation signals
  - Updates the StackView to show requested screens
  - Handles navigation with parameters for advanced use cases
  - Passes parameters to screens as component properties

- **Screen Parameter Handling**:
  - Screens check for _navigationParams during Component.onCompleted
  - Parameters control initial view state, like which sub-view to show
  - Common pattern enables consistent handling across all screens

## Natural Language Command Processors

### TimerCommandProcessor

The `TimerCommandProcessor` class handles natural language commands for the timer functionality. It uses regular expressions to match user input patterns like "set timer for 5 minutes" or "how much time is left on the timer". When a command is recognized, it calls the appropriate methods on the `TimerController` to perform the requested action, and then emits a signal with a response message that gets added to the chat history.

### AlarmCommandProcessor

The `AlarmCommandProcessor` class provides natural language processing for alarm functionality. Similar to the `TimerCommandProcessor`, it uses regex patterns to match user input like "set alarm for 7am" or "list all alarms". When a command is recognized, it calls the appropriate methods on the `AlarmController` to perform the requested action, and emits a signal with a response message that gets added to the chat history.

Key features of the `AlarmCommandProcessor`:
- Setting alarms with specific times (12-hour or 24-hour format)
- Setting recurring alarms (daily, weekdays, weekends, or specific days)
- Naming alarms
- Listing all alarms
- Enabling/disabling alarms
- Deleting alarms

#### Time Parsing Improvements (May 2025)
- **PM Time Conversion Fix**: Fixed issues with PM time conversion in AlarmCommandProcessor:
  - Enhanced PM indicator detection to handle various formats (PM, pm, p.m., p.m)
  - Improved time parsing logic to correctly convert times with separators (e.g., "11:30 p.m.")
  - Added special case handling for edge cases like "11:30 p.m." to ensure proper conversion to 24-hour format
  - Implemented better parsing of the full command string to detect PM indicators
  - Added extensive debugging logs for time parsing to assist future troubleshooting
  - Fixed issue where "8 PM" was incorrectly interpreted as 0800 (8:00 AM) instead of 2000 (8:00 PM)
  - Ensured consistent handling of times with and without separators (e.g., "8 PM" vs "11:30 p.m.")

#### Time Parsing Improvements (August 2025)
- **Improved AM/PM Handling**: Enhanced the time parsing logic to ensure proper handling of PM times.
  - Modified time parsing to first identify AM/PM indicators before extracting time components
  - Implemented a more robust approach by removing AM/PM indicators before regex matching
  - Separated time component extraction from AM/PM conversion for better maintainability
  - Consolidated the conversion logic to apply after successful parsing
  - Added more explicit logging for each step of the time parsing process
  - Fixed issues where "6 PM" was incorrectly interpreted as 0600 (6:00 AM) instead of 1800 (6:00 PM)
  - **Fixed PM Time Handling in Recurrence Patterns**: Resolved issues where "8 PM daily" was setting the alarm to 8 AM
    - Added PM detection on the full command string before extracting recurrence patterns
    - Preserved PM indicators across all command parsing methods
    - Made PM detection consistent across all alarm command types (one-time, day-specific, and recurring alarms)
    - Added thorough logging to track PM detection and conversions for easier debugging

#### Alarm Command Processor Improvements (August 2025)
- **Enhanced Alarm Creation and Navigation**: Fixed issues where setting alarms only navigated to the alarm screen without creating the alarm.
  - Added comprehensive debug logging throughout the alarm creation process
  - Improved error handling in the alarm command processor and alarm manager
  - Enhanced navigation controller to provide better feedback on navigation requests
  - Ensured proper sequence of operations: first create the alarm, then navigate to the screen
  - Added safeguards for error conditions during alarm creation and navigation
  - Implemented better console logging configuration for troubleshooting
  - Improved coordination between navigation controller and alarm command processor

The `AlarmCommandProcessor` requires an instance of `AlarmController` to be passed to its constructor, as it delegates all alarm operations to this controller. The main application creates and connects these components in `main.py`:

```python
# Create the AlarmCommandProcessor and connect it to the AlarmController
alarm_command_processor_instance = AlarmCommandProcessor(alarm_controller_instance)

# Connect AlarmCommandProcessor to ChatController for processing alarm commands
chat_controller_instance.alarm_command_processor = alarm_command_processor_instance
```

This architecture allows the command processor to focus on language parsing while delegating actual alarm management to the controller.

### Chat and Tool Integration
The application features a robust chat interface that integrates with various system tools:

- **ChatController**: Manages all chat-related functionality
  - Coordinates interaction between Speech-to-Text, Text-to-Speech, WebSocket, and UI
  - Processes incoming messages and dispatches outgoing messages
  - Handles chat history management and persistence
  - **Enhanced Tool Integration**: Preserves natural LLM responses when executing tool functions
    - Previously would replace LLM responses with generic messages like "Navigating to requested screen"
    - Now maintains the original LLM response while still executing the corresponding action
    - Supports parallel processing for navigation, timer, and alarm commands
    - Adds contextual metadata to requests to inform the backend about command types
    - **Prevents Duplicate Responses**: Includes message deduplication through unique message IDs
    - Uses hashed content and action types to identify and prevent duplicate message processing
    - Handles tool-specific responses with consistent message formats
    - Ensures even complex interactions with multiple tools yield clean chat history

- **Navigation Integration**:
  - Detects navigation commands without interrupting the natural conversation flow
  - Performs navigation actions while still displaying the LLM's natural language response
  - Uses a context-aware system to handle both actions simultaneously

- **Timer and Alarm Integration**:
  - Processes timer and alarm commands via dedicated command processors
  - Executes the corresponding commands while preserving the LLM's original response
  - Maintains a natural conversational feel rather than presenting system messages
