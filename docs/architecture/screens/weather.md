# Weather Screen Implementation

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

## Weather Screen Timer Improvements (July 2025)
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

## Weather UI Interaction
The Weather screen is interactive, allowing users to:
- Click on any weather section in the current weather view to view detailed information
- Toggle between the 72-hour view (with Lottie animations), the hourly graph view (with temperature trends and precipitation), and the 7-day forecast view
- The 7-day forecast displays comprehensive details directly in each row, eliminating the need for additional popups
- Each forecast row includes the date, icon, temperature, and a detailed description
- The dialog for the current weather sections uses blur effects (via QtQuick.Effects) for a modern, frosted-glass appearance

## Hourly Weather Graph
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

## Weather UI Layout
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

## 7-Day Forecast Layout
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

## Weather Icon Implementation
The application supports two types of weather icons:
1. **Lottie Animations**: Used for the current weather view (72-hour forecast) with smooth animations
2. **Static PNG Icons**: Used for the 7-day forecast view

It uses the PathProvider to load resources with dynamic paths that work across different machines:
```qml
property string lottieIconsBase: PathProvider.getAbsolutePath("frontend/icons/weather/lottie/")
property string lottiePlayerPath: PathProvider.getAbsolutePath("frontend/assets/js/lottie.min.js")
property string pngIconsBase: "file://" + PathProvider.getAbsolutePath("frontend/icons/weather/PNG/")
```

### Icon Mapping
Both icon types use a consistent mapping system to convert NWS (National Weather Service) icon URLs to the appropriate animations or PNG files. The mapping includes day and night variations for:
- Clear skies
- Cloudy conditions
- Rain and precipitation
- Snow and winter weather
- Extreme weather events (hurricanes, tornados)
- Special conditions (fog, haze, wind)

## Weather Display Improvements (May 2025)
- **Observation Time Display:** The CurrentWeather component shows "as of" the actual observation time from the National Weather Service, providing users with the exact time of the weather reading.
- **Real-time Data:** The application always displays the most current observation data available from NWS, refreshing automatically every 30 minutes.
- **UI Text Update:** The "As of" text in the current weather section uses the observation timestamp to accurately reflect when the weather reading was taken.
- **Code Cleanup:** Removed unused properties and functions from the CurrentWeather component to maintain code cleanliness.

## Weather Fetching Optimizations (May 2025)
- **Concurrent API Requests:** Modified the weather fetcher to use `asyncio.gather()` for parallel requests, significantly reducing total fetch time.
- **Request Timeouts:** Added explicit timeouts to prevent the application from hanging on slow network connections.
- **Accurate Data Only:** The system strictly displays only real data from the National Weather Service, with clear status messages when data is not yet available.
- **Sunrise/Sunset Integration:** The weather API provides sunrise and sunset data that is used for the automatic day/night theme switching feature.

## OpenWeatherMap Integration (June 2025)
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

## Sunrise and Sunset Data Enhancement (April 2025)
- **Dedicated API Integration:** Added integration with the sunrise-sunset.org API for accurate sunrise and sunset time data.
- **Improved Reliability:** Implemented a fallback mechanism that uses NWS grid forecast data when the specialized API is unavailable.
- **Error Handling:** Added comprehensive error handling to ensure the application continues to function even when sunrise/sunset data is unavailable.
- **Time Format Compatibility:** Enhanced the time formatting functions to handle various ISO 8601 time formats from different APIs.
- **Visual Display:** Optimized the hourly graph to display sunrise and sunset information in a clean, user-friendly manner with appropriate icons. 