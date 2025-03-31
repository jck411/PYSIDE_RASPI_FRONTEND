import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtWebEngine 1.8 // Needed again for WebEngineView
import MyTheme 1.0
import MyServices 1.0 

BaseScreen {
    id: weatherScreen
    
    screenControls: "WeatherControls.qml"
    title: "Weather"
    
    // --- State Properties ---
    property var currentWeatherData: null
    property string statusMessage: "Loading weather..."
    property string currentWeatherCode: "" 
    
    // --- Configuration Properties ---
    property string lottieIconsBase: "/home/human/AAREPOS/PYSIDE_RASPI_FRONTEND/frontend/icons/weather/lottie/"
    property string lottiePlayerPath: "/home/human/AAREPOS/PYSIDE_RASPI_FRONTEND/frontend/assets/js/lottie.min.js"
    property string pngIconsBase: "file:///home/human/AAREPOS/PYSIDE_RASPI_FRONTEND/frontend/icons/weather/PNG/"

    // HTML template for Lottie 
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

    // --- Helper Functions ---

    // --- Lottie Icon Mapping Function ---
    function getWeatherIconPath(owmIconCode) {
        const iconMap = {
            "01d": "clear-day", "01n": "clear-night", "02d": "partly-cloudy-day", "02n": "partly-cloudy-night",
            "03d": "cloudy", "03n": "cloudy", "04d": "overcast-day", "04n": "overcast-night",
            "09d": "rain", "09n": "rain", "10d": "partly-cloudy-day-rain", "10n": "partly-cloudy-night-rain",
            "11d": "thunderstorms-day", "11n": "thunderstorms-night", "13d": "snow", "13n": "snow",
            "50d": "mist", "50n": "mist"
        };
        if (!iconMap[owmIconCode]) {
            console.warn("Unknown weather icon code:", owmIconCode);
            return lottieIconsBase + "thermometer.json"; 
        }
        return lottieIconsBase + iconMap[owmIconCode] + ".json";
    }

    // --- PNG Icon Mapping Function (for Forecast) ---
    function getWeatherPngIconPath(owmIconCode) {
        // Simple direct mapping to the PNG files
        const iconMap = {
            // Clear sky
            "01d": "clear-day.png",
            "01n": "clear-night.png",
            
            // Few clouds
            "02d": "partly-cloudy-day.png",
            "02n": "partly-cloudy-night.png",
            
            // Scattered clouds
            "03d": "cloudy.png",
            "03n": "cloudy.png",
            
            // Broken clouds
            "04d": "overcast-day.png",
            "04n": "overcast-night.png",
            
            // Shower rain
            "09d": "drizzle.png",
            "09n": "drizzle.png",
            
            // Rain
            "10d": "partly-cloudy-day-rain.png",
            "10n": "partly-cloudy-night-rain.png",
            
            // Thunderstorm
            "11d": "thunderstorms-day.png",
            "11n": "thunderstorms-night.png",
            
            // Snow
            "13d": "snow.png",
            "13n": "snow.png",
            
            // Mist
            "50d": "mist.png",
            "50n": "mist.png"
        };
        
        if (!iconMap[owmIconCode]) {
            console.warn("Unknown weather icon code:", owmIconCode);
            return pngIconsBase + "not-available.png";
        }
        
        return pngIconsBase + iconMap[owmIconCode];
    }

    // --- Date Formatting Function ---
    function formatDateToDay(unixTimestamp) {
        var date = new Date(unixTimestamp * 1000);
        var days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
        var dayName = days[date.getDay()];
        var month = ("0" + (date.getMonth() + 1)).slice(-2); 
        var dayNum = ("0" + date.getDate()).slice(-2);
        return dayName + " " + month + "/" + dayNum;
    }

    // Function to load and parse Lottie JSON file
    function loadLottieAnimation(filePath) {
        console.log("Attempting to load Lottie file from:", filePath);
        var xhr = new XMLHttpRequest();
        try {
            var fileUrl = "file://" + filePath;
            xhr.open("GET", fileUrl, false); 
            xhr.onerror = function() { console.error("Network error loading Lottie:", filePath); return null; };
            xhr.send(null);
            if (xhr.status === 200) {
                var jsonContent = xhr.responseText;
                JSON.parse(jsonContent); // Validate
                return jsonContent;
            } else {
                console.error("Error loading Lottie file:", filePath, "Status:", xhr.status);
                statusMessage = "Error: Could not load animation file (Status: " + xhr.status + ")";
                return null;
            }
        } catch (e) {
            console.error("Exception loading Lottie file:", e);
            statusMessage = "Error: Exception loading animation file";
            return null;
        }
    }

    // Function to update the Lottie animation
    function updateLottieAnimation() {
        if (currentWeatherCode && lottieIconsBase && lottiePlayerPath && lottieHtmlTemplate) {
            try {
                var lottieJsonPath = getWeatherIconPath(currentWeatherCode);
                var animationJson = loadLottieAnimation(lottieJsonPath);
                if (animationJson) {
                    var htmlContent = lottieHtmlTemplate
                        .replace("%ANIMATION_DATA%", animationJson)
                        .replace("%LOTTIE_PLAYER_PATH%", lottiePlayerPath);
                    weatherWeb.loadHtml(htmlContent, "file:///");
                    console.log("Updated Lottie animation successfully");
                } else {
                    statusMessage = "Error: Failed to load weather animation";
                }
            } catch (e) {
                console.error("Error updating animation:", e);
                statusMessage = "Error: Exception when updating animation";
            }
        }
    }
    
    // Trigger update when the code changes
    onCurrentWeatherCodeChanged: {
        updateLottieAnimation();
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
                        currentWeatherData = response; 
                        statusMessage = ""; 
                        console.log("Weather data fetched successfully (WeatherScreen).")
                        if (currentWeatherData && currentWeatherData.current && currentWeatherData.current.weather && currentWeatherData.current.weather.length > 0) {
                            currentWeatherCode = currentWeatherData.current.weather[0].icon;
                        } else {
                            currentWeatherCode = "01d"; // Default
                        }
                    } catch (e) {
                        console.error("Error parsing weather data (WeatherScreen):", e);
                        statusMessage = "Error parsing weather data.";
                        currentWeatherData = null; currentWeatherCode = "";
                    }
                } else {
                    console.error("Error fetching weather data (WeatherScreen). Status:", xhr.status);
                    statusMessage = "Error fetching weather data. Status: " + xhr.status;
                    if (xhr.status === 503) { statusMessage = "Weather data not yet available."; }
                    currentWeatherData = null; currentWeatherCode = "";
                }
            }
        }
        xhr.open("GET", SettingsService.httpBaseUrl + "/api/weather"); 
        xhr.send();
    }

    // Fetch data when the component is ready
    Component.onCompleted: {
        console.log("WeatherScreen: Component.onCompleted running...") 
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
        id: flickableArea
        anchors.fill: parent
        contentHeight: contentColumn.implicitHeight 
        clip: true 
        flickableDirection: Flickable.VerticalFlick 

        ColumnLayout { 
            id: contentColumn 
            width: parent.width * 0.95 
            spacing: 15 // Consistent spacing
            // Center the whole column horizontally within the Flickable
            anchors.horizontalCenter: parent.horizontalCenter 

            // Status Text (Displayed at the top when loading or error)
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

            // --- Current Weather Display Elements ---
            Column {
                id: currentWeatherColumn // Give it an ID
                Layout.fillWidth: true // Take available width in ColumnLayout
                Layout.alignment: Qt.AlignHCenter // Center content horizontally
                spacing: 10 
                visible: statusMessage === "" // Hide when loading/error

                // Weather Animation Container
                Rectangle {
                    id: weatherIconContainer
                    width: 150 
                    height: 150
                    color: "transparent"
                    anchors.horizontalCenter: parent.horizontalCenter // Center within this Column
                    
                    WebEngineView {
                        id: weatherWeb
                        anchors.fill: parent
                        backgroundColor: Qt.rgba(0, 0, 0, 0)
                        settings.accelerated2dCanvasEnabled: true
                        settings.allowRunningInsecureContent: true
                        settings.javascriptEnabled: true
                        settings.showScrollBars: false
                        onLoadingChanged: if (loadRequest.status === WebEngineView.LoadFailedStatus) { console.error("Failed Lottie load:", loadRequest.errorString); }
                        onJavaScriptConsoleMessage: console.log("WebEngine JS:", message);
                    }
                }

                // Current Temperature Text
                Text {
                    id: currentTempText
                    width: parent.width // Fill width of currentWeatherColumn
                    text: currentWeatherData ? ("Current: " + Math.round(currentWeatherData.current.temp) + "°F") : "--"
                    color: ThemeManager.text_primary_color
                    font.pixelSize: 22 
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.WordWrap
                }
                
                // Weather Description
                Text {
                    id: weatherDescription
                    width: parent.width // Fill width of currentWeatherColumn
                    text: currentWeatherData && currentWeatherData.current && currentWeatherData.current.weather && currentWeatherData.current.weather.length > 0 ? 
                          currentWeatherData.current.weather[0].description.charAt(0).toUpperCase() + currentWeatherData.current.weather[0].description.slice(1) : ""
                    visible: text !== ""
                    color: ThemeManager.text_secondary_color
                    font.pixelSize: 16 
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.WordWrap
                }
            } // End Current Weather Column

            // --- Forecast Display Elements ---
            RowLayout {
                id: forecastRowLayout
                Layout.topMargin: 40 // Increased top margin slightly more
                Layout.fillWidth: true // Make the RowLayout use the full width provided by parent ColumnLayout
                spacing: 15 // Spacing between forecast days
                visible: statusMessage === "" && currentWeatherData && currentWeatherData.daily && currentWeatherData.daily.length > 0

                Repeater {
                    model: currentWeatherData ? (currentWeatherData.daily ? currentWeatherData.daily.slice(1, 6) : []) : [] 

                    delegate: Column {
                        Layout.fillWidth: true // Distribute width evenly
                        Layout.alignment: Qt.AlignTop 
                        spacing: 5

                        // Day and Date
                        Text {
                            text: formatDateToDay(modelData.dt)
                            color: ThemeManager.text_primary_color
                            font.pixelSize: 14 
                            horizontalAlignment: Text.AlignHCenter
                            anchors.horizontalCenter: parent.horizontalCenter
                        }

                        // Weather Icon (SVG)
                        Image {
                            id: forecastIcon
                            width: 50; height: 50
                            source: getWeatherPngIconPath(modelData.weather[0].icon)
                            anchors.horizontalCenter: parent.horizontalCenter
                            fillMode: Image.PreserveAspectFit
                            sourceSize.width: 50; sourceSize.height: 50
                        }

                        // High / Low Temperature
                        Text {
                            text: Math.round(modelData.temp.max) + "° / " + Math.round(modelData.temp.min) + "°"
                            color: ThemeManager.text_secondary_color
                            font.pixelSize: 14
                            horizontalAlignment: Text.AlignHCenter
                            anchors.horizontalCenter: parent.horizontalCenter
                        }

                        // Chance of Rain (PoP)
                        Text {
                            text: modelData.pop !== undefined ? (Math.round(modelData.pop * 100) + "% rain") : "" 
                            color: ThemeManager.text_secondary_color
                            font.pixelSize: 12 
                            horizontalAlignment: Text.AlignHCenter
                            anchors.horizontalCenter: parent.horizontalCenter
                            visible: modelData.pop !== undefined 
                        }
                    } 
                } // End Repeater
            } // End RowLayout (Forecast)

        } // End contentColumn (ColumnLayout)
    } // End Flickable
} // End BaseScreen
