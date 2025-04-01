import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtWebEngine 1.8 // Required by QtWebEngine
import MyTheme 1.0
import MyServices 1.0 

BaseScreen {
    id: weatherScreen
    
    screenControls: "WeatherControls.qml"
    title: "Weather"
    
    // --- State Properties ---
    property var currentWeatherData: null
    property var forecastPeriods: null
    property string statusMessage: "Loading weather..."
    
    // Start the animation timer when status message changes
    onStatusMessageChanged: {
        if (statusMessage === "") {
            console.log("Status message cleared, starting animation timer");
            animationTimer.start();
        }
    }
    
    // --- Configuration Properties ---
    property string lottieIconsBase: PathProvider.getAbsolutePath("frontend/icons/weather/lottie") + "/"
    property string lottiePlayerPath: PathProvider.getAbsolutePath("frontend/assets/js/lottie.min.js")
    property string pngIconsBase: "file://" + PathProvider.getAbsolutePath("frontend/icons/weather/PNG") + "/"
    
    // --- Icon Mapping Logic ---
    function mapWeatherIcon(iconUrl) {
        // Day Icons Mapping
        const dayIconMap = {
            "https://api.weather.gov/icons/land/day/skc": "clear-day.json",
            "https://api.weather.gov/icons/land/day/few": "partly-cloudy-day.json",
            "https://api.weather.gov/icons/land/day/sct": "partly-cloudy-day.json",
            "https://api.weather.gov/icons/land/day/bkn": "cloudy.json",
            "https://api.weather.gov/icons/land/day/ovc": "overcast-day.json",
            "https://api.weather.gov/icons/land/day/wind_skc": "clear-day.json",
            "https://api.weather.gov/icons/land/day/wind_few": "partly-cloudy-day.json",
            "https://api.weather.gov/icons/land/day/wind_sct": "partly-cloudy-day.json",
            "https://api.weather.gov/icons/land/day/wind_bkn": "cloudy.json",
            "https://api.weather.gov/icons/land/day/wind_ovc": "overcast-day.json",
            "https://api.weather.gov/icons/land/day/snow": "snow.json",
            "https://api.weather.gov/icons/land/day/rain_snow": "sleet.json",
            "https://api.weather.gov/icons/land/day/rain_sleet": "sleet.json",
            "https://api.weather.gov/icons/land/day/snow_sleet": "sleet.json",
            "https://api.weather.gov/icons/land/day/fzra": "rain.json",
            "https://api.weather.gov/icons/land/day/rain_fzra": "rain.json",
            "https://api.weather.gov/icons/land/day/snow_fzra": "rain.json",
            "https://api.weather.gov/icons/land/day/sleet": "sleet.json",
            "https://api.weather.gov/icons/land/day/rain": "rain.json",
            "https://api.weather.gov/icons/land/day/rain_showers": "rain.json",
            "https://api.weather.gov/icons/land/day/rain_showers_hi": "extreme-day-rain.json",
            "https://api.weather.gov/icons/land/day/tsra": "thunderstorms-day.json",
            "https://api.weather.gov/icons/land/day/tsra_sct": "thunderstorms-day-overcast.json",
            "https://api.weather.gov/icons/land/day/tsra_hi": "thunderstorms-day-extreme.json",
            "https://api.weather.gov/icons/land/day/tornado": "tornado.json",
            "https://api.weather.gov/icons/land/day/hurricane": "hurricane.json",
            "https://api.weather.gov/icons/land/day/tropical_storm": "hurricane.json",
            "https://api.weather.gov/icons/land/day/dust": "dust-day.json",
            "https://api.weather.gov/icons/land/day/smoke": "smoke.json",
            "https://api.weather.gov/icons/land/day/haze": "haze-day.json",
            "https://api.weather.gov/icons/land/day/hot": "sun-hot.json",
            "https://api.weather.gov/icons/land/day/cold": "thermometer-mercury-cold.json",
            "https://api.weather.gov/icons/land/day/blizzard": "extreme-day-snow.json",
            "https://api.weather.gov/icons/land/day/fog": "fog-day.json"
        };
        
        // Night Icons Mapping
        const nightIconMap = {
            "https://api.weather.gov/icons/land/night/skc": "clear-night.json",
            "https://api.weather.gov/icons/land/night/few": "partly-cloudy-night.json",
            "https://api.weather.gov/icons/land/night/sct": "partly-cloudy-night.json",
            "https://api.weather.gov/icons/land/night/bkn": "cloudy.json",
            "https://api.weather.gov/icons/land/night/ovc": "overcast-night.json",
            "https://api.weather.gov/icons/land/night/wind_skc": "clear-night.json",
            "https://api.weather.gov/icons/land/night/wind_few": "partly-cloudy-night.json",
            "https://api.weather.gov/icons/land/night/wind_sct": "partly-cloudy-night.json",
            "https://api.weather.gov/icons/land/night/wind_bkn": "cloudy.json",
            "https://api.weather.gov/icons/land/night/wind_ovc": "overcast-night.json",
            "https://api.weather.gov/icons/land/night/snow": "snow.json",
            "https://api.weather.gov/icons/land/night/rain_snow": "sleet.json",
            "https://api.weather.gov/icons/land/night/rain_sleet": "sleet.json",
            "https://api.weather.gov/icons/land/night/snow_sleet": "sleet.json",
            "https://api.weather.gov/icons/land/night/fzra": "rain.json",
            "https://api.weather.gov/icons/land/night/rain_fzra": "rain.json",
            "https://api.weather.gov/icons/land/night/snow_fzra": "rain.json",
            "https://api.weather.gov/icons/land/night/sleet": "sleet.json",
            "https://api.weather.gov/icons/land/night/rain": "rain.json",
            "https://api.weather.gov/icons/land/night/rain_showers": "overcast-night-rain.json",
            "https://api.weather.gov/icons/land/night/rain_showers_hi": "extreme-night-rain.json",
            "https://api.weather.gov/icons/land/night/tsra": "thunderstorms-night.json",
            "https://api.weather.gov/icons/land/night/tsra_sct": "thunderstorms-night-overcast.json",
            "https://api.weather.gov/icons/land/night/tsra_hi": "thunderstorms-night-extreme.json",
            "https://api.weather.gov/icons/land/night/tornado": "tornado.json",
            "https://api.weather.gov/icons/land/night/hurricane": "hurricane.json",
            "https://api.weather.gov/icons/land/night/tropical_storm": "hurricane.json",
            "https://api.weather.gov/icons/land/night/dust": "dust-night.json",
            "https://api.weather.gov/icons/land/night/smoke": "smoke.json",
            "https://api.weather.gov/icons/land/night/haze": "haze-night.json",
            "https://api.weather.gov/icons/land/night/hot": "thermometer-warmer.json",
            "https://api.weather.gov/icons/land/night/cold": "thermometer-mercury-cold.json",
            "https://api.weather.gov/icons/land/night/blizzard": "extreme-night-snow.json",
            "https://api.weather.gov/icons/land/night/fog": "fog-night.json"
        };
        
        // Remove size parameter if present
        let baseUrl = iconUrl;
        if (baseUrl.includes("?size=")) {
            baseUrl = baseUrl.split("?size=")[0];
        }
        
        // Check for additional parameters like probability
        if (baseUrl.includes(",")) {
            baseUrl = baseUrl.split(",")[0];
        }
        
        // Try to find a match in the appropriate map
        if (baseUrl.includes("/day/")) {
            for (const key in dayIconMap) {
                if (baseUrl.startsWith(key)) {
                    return dayIconMap[key];
                }
            }
        } else if (baseUrl.includes("/night/")) {
            for (const key in nightIconMap) {
                if (baseUrl.startsWith(key)) {
                    return nightIconMap[key];
                }
            }
        }
        
        // Default fallback
        console.warn("No icon mapping found for:", iconUrl);
        return "thermometer.json";
    }

    // --- Data Fetching Logic ---
    function fetchWeather() {
        console.log("Attempting to fetch weather data (WeatherScreen)...")
        var xhr = new XMLHttpRequest();
        xhr.onreadystatechange = function() {
            if (xhr.readyState === XMLHttpRequest.DONE) {
                if (xhr.status === 200) {
                    try {
                        var response = JSON.parse(xhr.responseText);
                        console.log("FULL WEATHER RESPONSE:", JSON.stringify(response));
                        
                        // Process the forecast periods
                        if (response && response.forecast && response.forecast.properties && response.forecast.properties.periods) {
                            forecastPeriods = response.forecast.properties.periods;
                            console.log("Forecast periods loaded:", forecastPeriods.length);
                        }
                        
                        currentWeatherData = response; 
                        statusMessage = ""; 
                        console.log("Weather data fetched successfully (WeatherScreen).");
                        
                    } catch (e) {
                        console.error("Error parsing weather data (WeatherScreen):", e);
                        statusMessage = "Error parsing weather data.";
                        currentWeatherData = null;
                        forecastPeriods = null;
                    }
                } else {
                    console.error("Error fetching weather data (WeatherScreen). Status:", xhr.status);
                    statusMessage = "Error fetching weather data. Status: " + xhr.status;
                    if (xhr.status === 503) { 
                        statusMessage = "Weather data not yet available."; 
                    }
                    currentWeatherData = null;
                    forecastPeriods = null;
                }
            }
        }
        xhr.open("GET", SettingsService.httpBaseUrl + "/api/weather"); 
        xhr.send();
    }

    // --- Helper Functions ---
    function formatTime(timeString) {
        var date = new Date(timeString);
        return date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    }
    
    function formatDate(timeString) {
        var date = new Date(timeString);
        return date.toLocaleDateString([], {weekday: 'short', month: 'short', day: 'numeric'});
    }
    
    // Fetch data when the component is ready
    Component.onCompleted: {
        console.log("WeatherScreen: Component.onCompleted running...") 
        console.log("Weather screen paths:");
        console.log("- Lottie icons base:", lottieIconsBase);
        console.log("- Lottie player path:", lottiePlayerPath);
        console.log("- PNG icons base:", pngIconsBase);
        
        fetchWeather();
        weatherTimer.start();
    }

    // Timer to refresh weather data periodically
    Timer {
        id: weatherTimer
        interval: 1800000 // 30 minutes
        repeat: true
        running: false 
        onTriggered: { fetchWeather(); }
    }

    // --- Content Area ---
    Flickable { 
        id: weatherFlickable
        anchors.fill: parent
        contentHeight: parent.height
        clip: true 
        flickableDirection: Flickable.VerticalFlick 

        ColumnLayout { 
            id: weatherColumn 
            width: parent.width * 0.95
            height: parent.height
            spacing: 15
            anchors.horizontalCenter: parent.horizontalCenter 

            // Status Text (visible only when loading or error)
            Text {
                id: statusText
                Layout.fillWidth: true
                text: statusMessage
                visible: statusMessage !== ""
                color: ThemeManager.text_secondary_color
                font.pixelSize: 16
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
            }

            // Weather Sections Container
            RowLayout {
                id: weatherSectionsContainer
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.preferredHeight: parent.height * 0.85
                Layout.maximumHeight: parent.height
                Layout.bottomMargin: 40  // Add padding equal to icon height
                Layout.topMargin: 15
                spacing: 10
                visible: statusMessage === ""
                
                // Section 1: Current Weather
                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.minimumHeight: 300
                    Layout.maximumHeight: parent.height
                    color: Qt.rgba(0, 0, 0, 0.1)
                    radius: 10
                    
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 5
                        
                        // Heading - fixed height
                        Item {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 20
                            
                            Text {
                                anchors.fill: parent
                                text: "Current"
                                font.pixelSize: 16
                                font.bold: true
                                color: ThemeManager.text_primary_color
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                        }
                        
                        // Time - fixed height
                        Item {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 16
                            
                            Text {
                                anchors.fill: parent
                                text: currentWeatherData && currentWeatherData.properties ? 
                                      "As of " + formatTime(currentWeatherData.properties.timestamp) : "N/A"
                                font.pixelSize: 12
                                color: ThemeManager.text_secondary_color
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                        }
                        
                        // Weather Icon - fixed height
                        Item {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 90
                            
                            Rectangle {
                                width: 80
                                height: 80
                                color: "transparent"
                                anchors.horizontalCenter: parent.horizontalCenter
                                
                                WebEngineView {
                                    id: currentWeatherIcon
                                    anchors.fill: parent
                                    backgroundColor: Qt.rgba(0, 0, 0, 0)
                                    settings.accelerated2dCanvasEnabled: true
                                    settings.allowRunningInsecureContent: true
                                    settings.javascriptEnabled: true
                                    settings.showScrollBars: false
                                }
                            }
                        }
                        
                        // Temperature - fixed height
                        Item {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 25
                            
                            Text {
                                anchors.fill: parent
                                text: currentWeatherData && currentWeatherData.properties ? 
                                      (currentWeatherData.properties.temperature ? 
                                       currentWeatherData.properties.temperature.value.toFixed(1) + " °F" : "N/A") : "N/A"
                                font.pixelSize: 20
                                font.bold: true
                                color: ThemeManager.text_primary_color
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                        }
                        
                        // Description - flexible height
                        Text {
                            Layout.alignment: Qt.AlignHCenter
                            Layout.fillWidth: true
                            Layout.maximumWidth: parent.width
                            text: currentWeatherData && currentWeatherData.properties ? 
                                  currentWeatherData.properties.textDescription || "N/A" : "N/A"
                            font.pixelSize: 14
                            color: ThemeManager.text_secondary_color
                            horizontalAlignment: Text.AlignHCenter
                            wrapMode: Text.WordWrap
                            elide: Text.ElideRight
                        }
                        
                        // Humidity - fixed height
                        Text {
                            Layout.alignment: Qt.AlignHCenter
                            Layout.fillWidth: true
                            Layout.maximumWidth: parent.width
                            text: currentWeatherData && currentWeatherData.properties ? 
                                  "Humidity: " + (currentWeatherData.properties.relativeHumidity ? 
                                   currentWeatherData.properties.relativeHumidity.value.toFixed(0) + "%" : "N/A") : "N/A"
                            font.pixelSize: 14
                            color: ThemeManager.text_secondary_color
                            horizontalAlignment: Text.AlignHCenter
                        }
                        
                        // Spacer to push content up
                        Item {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                        }
                    }
                }
                
                // Section 2: Current Period
                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.minimumHeight: 300
                    Layout.maximumHeight: parent.height
                    color: Qt.rgba(0, 0, 0, 0.1)
                    radius: 10
                    
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 5
                        
                        // Heading - fixed height
                        Item {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 20
                            
                            Text {
                                anchors.fill: parent
                                text: forecastPeriods && forecastPeriods.length > 0 ? 
                                      forecastPeriods[0].name : "Current Period"
                                font.pixelSize: 16
                                font.bold: true
                                color: ThemeManager.text_primary_color
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                        }
                        
                        // Time - fixed height
                        Item {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 16
                            
                            Text {
                                anchors.fill: parent
                                text: forecastPeriods && forecastPeriods.length > 0 ? 
                                      formatTime(forecastPeriods[0].startTime) + " - " + 
                                      formatTime(forecastPeriods[0].endTime) : "N/A"
                                font.pixelSize: 12
                                color: ThemeManager.text_secondary_color
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                        }
                        
                        // Weather Icon - fixed height
                        Item {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 90
                            
                            Rectangle {
                                width: 80
                                height: 80
                                color: "transparent"
                                anchors.horizontalCenter: parent.horizontalCenter
                                
                                WebEngineView {
                                    id: currentPeriodIcon
                                    anchors.fill: parent
                                    backgroundColor: Qt.rgba(0, 0, 0, 0)
                                    settings.accelerated2dCanvasEnabled: true
                                    settings.allowRunningInsecureContent: true
                                    settings.javascriptEnabled: true
                                    settings.showScrollBars: false
                                }
                            }
                        }
                        
                        // Temperature - fixed height
                        Item {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 25
                            
                            Text {
                                anchors.fill: parent
                                text: forecastPeriods && forecastPeriods.length > 0 ? 
                                      forecastPeriods[0].temperature + " " + forecastPeriods[0].temperatureUnit : "N/A"
                                font.pixelSize: 20
                                font.bold: true
                                color: ThemeManager.text_primary_color
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                        }
                        
                        // Description - flexible height
                        Text {
                            Layout.alignment: Qt.AlignHCenter
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            Layout.maximumWidth: parent.width
                            text: forecastPeriods && forecastPeriods.length > 0 ? 
                                  forecastPeriods[0].shortForecast : "N/A"
                            font.pixelSize: 14
                            color: ThemeManager.text_secondary_color
                            horizontalAlignment: Text.AlignHCenter
                            wrapMode: Text.WordWrap
                            elide: Text.ElideRight
                        }
                    }
                }
                
                // Section 3: Next 12 Hours
                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.minimumHeight: 300
                    Layout.maximumHeight: parent.height
                    color: Qt.rgba(0, 0, 0, 0.1)
                    radius: 10
                    
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 5
                        
                        // Heading - fixed height
                        Item {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 20
                            
                            Text {
                                anchors.fill: parent
                                text: forecastPeriods && forecastPeriods.length > 1 ? 
                                      forecastPeriods[1].name : "Next 12 Hours"
                                font.pixelSize: 16
                                font.bold: true
                                color: ThemeManager.text_primary_color
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                        }
                        
                        // Time - fixed height
                        Item {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 16
                            
                            Text {
                                anchors.fill: parent
                                text: forecastPeriods && forecastPeriods.length > 1 ? 
                                      formatTime(forecastPeriods[1].startTime) + " - " + 
                                      formatTime(forecastPeriods[1].endTime) : "N/A"
                                font.pixelSize: 12
                                color: ThemeManager.text_secondary_color
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                        }
                        
                        // Weather Icon - fixed height
                        Item {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 90
                            
                            Rectangle {
                                width: 80
                                height: 80
                                color: "transparent"
                                anchors.horizontalCenter: parent.horizontalCenter
                                
                                WebEngineView {
                                    id: next12HoursIcon
                                    anchors.fill: parent
                                    backgroundColor: Qt.rgba(0, 0, 0, 0)
                                    settings.accelerated2dCanvasEnabled: true
                                    settings.allowRunningInsecureContent: true
                                    settings.javascriptEnabled: true
                                    settings.showScrollBars: false
                                }
                            }
                        }
                        
                        // Temperature - fixed height
                        Item {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 25
                            
                            Text {
                                anchors.fill: parent
                                text: forecastPeriods && forecastPeriods.length > 1 ? 
                                      forecastPeriods[1].temperature + " " + forecastPeriods[1].temperatureUnit : "N/A"
                                font.pixelSize: 20
                                font.bold: true
                                color: ThemeManager.text_primary_color
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                        }
                        
                        // Description - flexible height
                        Text {
                            Layout.alignment: Qt.AlignHCenter
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            Layout.maximumWidth: parent.width
                            text: forecastPeriods && forecastPeriods.length > 1 ? 
                                  forecastPeriods[1].shortForecast : "N/A"
                            font.pixelSize: 14
                            color: ThemeManager.text_secondary_color
                            horizontalAlignment: Text.AlignHCenter
                            wrapMode: Text.WordWrap
                            elide: Text.ElideRight
                        }
                    }
                }
                
                // Section 4: 12 Hours After That
                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.minimumHeight: 300
                    Layout.maximumHeight: parent.height
                    color: Qt.rgba(0, 0, 0, 0.1)
                    radius: 10
                    
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 5
                        
                        // Heading - fixed height
                        Item {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 20
                            
                            Text {
                                anchors.fill: parent
                                text: forecastPeriods && forecastPeriods.length > 2 ? 
                                      forecastPeriods[2].name : "Next Day"
                                font.pixelSize: 16
                                font.bold: true
                                color: ThemeManager.text_primary_color
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                        }
                        
                        // Time - fixed height
                        Item {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 16
                            
                            Text {
                                anchors.fill: parent
                                text: forecastPeriods && forecastPeriods.length > 2 ? 
                                      formatTime(forecastPeriods[2].startTime) + " - " + 
                                      formatTime(forecastPeriods[2].endTime) : "N/A"
                                font.pixelSize: 12
                                color: ThemeManager.text_secondary_color
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                        }
                        
                        // Weather Icon - fixed height
                        Item {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 90
                            
                            Rectangle {
                                width: 80
                                height: 80
                                color: "transparent"
                                anchors.horizontalCenter: parent.horizontalCenter
                                
                                WebEngineView {
                                    id: nextDayIcon
                                    anchors.fill: parent
                                    backgroundColor: Qt.rgba(0, 0, 0, 0)
                                    settings.accelerated2dCanvasEnabled: true
                                    settings.allowRunningInsecureContent: true
                                    settings.javascriptEnabled: true
                                    settings.showScrollBars: false
                                }
                            }
                        }
                        
                        // Temperature - fixed height
                        Item {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 25
                            
                            Text {
                                anchors.fill: parent
                                text: forecastPeriods && forecastPeriods.length > 2 ? 
                                      forecastPeriods[2].temperature + " " + forecastPeriods[2].temperatureUnit : "N/A"
                                font.pixelSize: 20
                                font.bold: true
                                color: ThemeManager.text_primary_color
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                        }
                        
                        // Description - flexible height
                        Text {
                            Layout.alignment: Qt.AlignHCenter
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            Layout.maximumWidth: parent.width
                            text: forecastPeriods && forecastPeriods.length > 2 ? 
                                  forecastPeriods[2].shortForecast : "N/A"
                            font.pixelSize: 14
                            color: ThemeManager.text_secondary_color
                            horizontalAlignment: Text.AlignHCenter
                            wrapMode: Text.WordWrap
                            elide: Text.ElideRight
                        }
                    }
                }
            }
            
            // Load Lottie animations when data is available
            Timer {
                id: animationTimer
                interval: 500
                repeat: true
                running: false
                onTriggered: {
                    console.log("Animation timer triggered, checking for forecast data...");
                    if (currentWeatherData && currentWeatherData.forecast && 
                        currentWeatherData.forecast.properties && 
                        currentWeatherData.forecast.properties.periods && 
                        currentWeatherData.forecast.properties.periods.length > 0) {
                        
                        console.log("Forecast data available, loading animations...");
                        var periods = currentWeatherData.forecast.properties.periods;
                        
                        // Load animations for each section
                        loadLottieAnimation(currentWeatherIcon, 
                            currentWeatherData.properties && currentWeatherData.properties.icon ? 
                            mapWeatherIcon(currentWeatherData.properties.icon) : "thermometer.json");
                        console.log("Current weather icon:", currentWeatherData.properties.icon);
                            
                        loadLottieAnimation(currentPeriodIcon, 
                            periods[0].icon ? 
                            mapWeatherIcon(periods[0].icon) : "thermometer.json");
                        console.log("Current period icon:", periods[0].icon);
                            
                        if (periods.length > 1) {
                            loadLottieAnimation(next12HoursIcon, 
                                periods[1].icon ? 
                                mapWeatherIcon(periods[1].icon) : "thermometer.json");
                            console.log("Next 12 hours icon:", periods[1].icon);
                        }
                        
                        if (periods.length > 2) {
                            loadLottieAnimation(nextDayIcon, 
                                periods[2].icon ? 
                                mapWeatherIcon(periods[2].icon) : "thermometer.json");
                            console.log("Next day icon:", periods[2].icon);
                        }
                        
                        // Stop the timer once animations are loaded
                        animationTimer.stop();
                        console.log("Animations loaded, timer stopped");
                    } else {
                        console.log("Waiting for forecast data...");
                    }
                }
            }
            
            // No onStatusMessageChanged handler here
        }
    }
    
    // HTML template for Lottie animations
    property string lottieHtmlTemplate: '
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <style>
        body { margin: 0; padding: 0; overflow: hidden; background-color: transparent; }
        #lottie { width: 100%; height: 100%; background-color: transparent; }
      </style>
      <script src="file://%LOTTIE_PLAYER_PATH%"></script>
    </head>
    <body>
      <div id="lottie"></div>
      <script>
        var animationData = %ANIMATION_DATA%;
        var animation = lottie.loadAnimation({
          container: document.getElementById("lottie"),
          renderer: "svg",
          loop: true,
          autoplay: true,
          animationData: animationData
        });
      </script>
    </body>
    </html>
    '
    
    // Function to load and parse Lottie JSON file
    function loadLottieAnimation(webView, iconName) {
        console.log("Attempting to load Lottie file:", iconName);
        var filePath = lottieIconsBase + iconName;
        var xhr = new XMLHttpRequest();
        try {
            var fileUrl = "file://" + filePath;
            xhr.open("GET", fileUrl, false); 
            xhr.onerror = function() { 
                console.error("Network error loading Lottie:", filePath); 
                return; 
            };
            xhr.send(null);
            if (xhr.status === 200) {
                var jsonContent = xhr.responseText;
                try {
                    JSON.parse(jsonContent); // Validate
                    var htmlContent = lottieHtmlTemplate
                        .replace("%ANIMATION_DATA%", jsonContent)
                        .replace("%LOTTIE_PLAYER_PATH%", lottiePlayerPath);
                    webView.loadHtml(htmlContent, "file:///");
                    console.log("Updated Lottie animation successfully for", iconName);
                } catch (e) {
                    console.error("Error parsing Lottie JSON:", e);
                }
            } else {
                console.error("Error loading Lottie file:", filePath, "Status:", xhr.status);
            }
        } catch (e) {
            console.error("Exception loading Lottie file:", e);
        }
    }
}
