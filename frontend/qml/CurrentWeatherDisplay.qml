import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtWebEngine 1.8
import MyTheme 1.0

Item {
    id: currentWeatherRoot
    width: parent.width // Take available width
    // REMOVE explicit height: Let parent ColumnLayout manage height

    // --- Properties Passed from Parent (WeatherScreen) ---
    property var currentWeatherData: null
    property string statusMessage: "Loading..."
    property string currentWeatherCode: ""
    property string lottieIconsBase: ""
    property string lottiePlayerPath: ""
    property string lottieHtmlTemplate: ""

    // --- Lottie Icon Mapping Function ---
    function getWeatherIconPath(owmIconCode) {
        // Map OpenWeatherMap icon codes to Basmilius collection Lottie files
        const iconMap = {
            "01d": "clear-day",             // clear sky day
            "01n": "clear-night",           // clear sky night
            "02d": "partly-cloudy-day",     // few clouds day
            "02n": "partly-cloudy-night",   // few clouds night
            "03d": "cloudy",                // scattered clouds day
            "03n": "cloudy",                // scattered clouds night
            "04d": "overcast-day",          // broken clouds day
            "04n": "overcast-night",        // broken clouds night
            "09d": "rain",                  // shower rain day
            "09n": "rain",                  // shower rain night
            "10d": "partly-cloudy-day-rain", // rain day
            "10n": "partly-cloudy-night-rain", // rain night
            "11d": "thunderstorms-day",     // thunderstorm day
            "11n": "thunderstorms-night",   // thunderstorm night
            "13d": "snow",                  // snow day
            "13n": "snow",                  // snow night
            "50d": "mist",                  // mist day
            "50n": "mist"                   // mist night
        };
        
        if (!iconMap[owmIconCode]) {
            console.warn("Unknown weather icon code:", owmIconCode);
            return lottieIconsBase + "thermometer.json"; // Default fallback
        }
        
        return lottieIconsBase + iconMap[owmIconCode] + ".json";
    }

    // Function to load and parse Lottie JSON file
    function loadLottieAnimation(filePath) {
        console.log("Attempting to load Lottie file from:", filePath);
        var xhr = new XMLHttpRequest();
        try {
            var fileUrl = "file://" + filePath;
            console.log("Loading from URL:", fileUrl);
            xhr.open("GET", fileUrl, false); // Synchronous request
            xhr.onerror = function() {
                console.error("Network error occurred when trying to load Lottie file:", filePath);
                return null;
            };
            xhr.send(null);
            if (xhr.status === 200) {
                console.log("Successfully loaded Lottie file:", filePath);
                try {
                    var jsonContent = xhr.responseText;
                    JSON.parse(jsonContent); // Validate JSON
                    return jsonContent;
                } catch (e) {
                    console.error("Error parsing JSON from file:", filePath, e);
                    statusMessage = "Error: Invalid JSON in animation file"; // Update status locally if needed
                    return null;
                }
            } else {
                console.error("Error loading Lottie file:", filePath, "Status:", xhr.status, xhr.statusText);
                statusMessage = "Error: Could not load animation file (Status: " + xhr.status + ")";
                if (xhr.status === 0) {
                    console.error("Access denied or file not found. Make sure QML_XHR_ALLOW_FILE_READ=1 is set.");
                    statusMessage = "Error: Animation file access denied (check permissions)";
                }
                return null;
            }
        } catch (e) {
            console.error("Exception when loading Lottie file:", e);
            statusMessage = "Error: Exception occurred loading animation file";
            return null;
        }
    }

    // Function to update the Lottie animation
    function updateLottieAnimation() {
        if (currentWeatherCode && lottieIconsBase && lottiePlayerPath && lottieHtmlTemplate) {
            try {
                var lottieJsonPath = getWeatherIconPath(currentWeatherCode);
                console.log("Getting Lottie file for weather code:", currentWeatherCode);
                var animationJson = loadLottieAnimation(lottieJsonPath);
                if (animationJson) {
                    var htmlContent = lottieHtmlTemplate
                        .replace("%ANIMATION_DATA%", animationJson)
                        .replace("%LOTTIE_PLAYER_PATH%", lottiePlayerPath);
                    weatherWeb.loadHtml(htmlContent, "file:///");
                    console.log("Updated Lottie animation successfully");
                } else {
                    console.error("Failed to load animation data from:", lottieJsonPath);
                    statusMessage = "Error: Failed to load weather animation";
                }
            } catch (e) {
                console.error("Error updating animation:", e);
                statusMessage = "Error: Exception when updating animation";
            }
        } else {
             console.warn("Cannot update Lottie: Missing required properties (code, paths, template).");
        }
    }

    // Trigger update when the code changes
    onCurrentWeatherCodeChanged: {
        updateLottieAnimation();
    }

    // --- UI Elements ---
    Column {
        // anchors.centerIn: parent // REMOVE: Let parent ColumnLayout handle positioning
        width: parent.width // Use parent's width
        spacing: 10 // Reduced spacing a bit

        // Weather Animation Container
        Rectangle {
            id: weatherIconContainer
            width: 150 // Slightly smaller icon
            height: 150
            color: "transparent"
            visible: statusMessage === ""
            anchors.horizontalCenter: parent.horizontalCenter
            
            WebEngineView {
                id: weatherWeb
                anchors.fill: parent
                backgroundColor: Qt.rgba(0, 0, 0, 0)
                settings.accelerated2dCanvasEnabled: true
                settings.allowRunningInsecureContent: true
                settings.javascriptEnabled: true
                settings.showScrollBars: false
                
                onLoadingChanged: function(loadRequest) {
                    if (loadRequest.status === WebEngineView.LoadSucceededStatus) {
                        console.log("Lottie animation loaded successfully (CurrentWeatherDisplay)");
                    } else if (loadRequest.status === WebEngineView.LoadFailedStatus) {
                        console.error("Failed to load Lottie animation (CurrentWeatherDisplay):", loadRequest.errorString);
                    }
                }
                
                onJavaScriptConsoleMessage: function(level, message, lineNumber, sourceID) {
                    console.log("WebEngine JS (CurrentWeatherDisplay):", message, "at line", lineNumber);
                }
            }
        }

        // Current Temperature Text
        Text {
            id: currentTempText
            width: parent.width
            text: currentWeatherData ? 
                  ("Current: " + Math.round(currentWeatherData.current.temp) + "°F") : "--" // Added "Current:" label
            visible: statusMessage === ""
            color: ThemeManager.text_primary_color
            font.pixelSize: 22 // Slightly smaller font
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
        }
        
        // Weather Description
        Text {
            id: weatherDescription
            width: parent.width
            text: currentWeatherData && currentWeatherData.current && 
                  currentWeatherData.current.weather && 
                  currentWeatherData.current.weather.length > 0 ? 
                  currentWeatherData.current.weather[0].description.charAt(0).toUpperCase() + 
                  currentWeatherData.current.weather[0].description.slice(1) : ""
            visible: statusMessage === "" && text !== ""
            color: ThemeManager.text_secondary_color
            font.pixelSize: 16 // Slightly smaller font
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
        }
    }
}