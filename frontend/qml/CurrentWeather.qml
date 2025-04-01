import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtWebEngine 1.8
import MyTheme 1.0

// Current Weather Component
Item {
    id: currentWeatherComponent
    width: parent.width
    implicitHeight: currentWeatherColumn.implicitHeight
    
    // --- Properties ---
    property var weatherData: null
    property string statusMessage: ""
    property string weatherCode: ""
    property string lottieIconsBase: ""
    property string lottiePlayerPath: ""
    
    // --- Public Functions ---
    // Date Formatting Function - needed by WeatherScreen
    function formatDateToDay(unixTimestamp) {
        var date = new Date(unixTimestamp * 1000);
        var days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
        var dayName = days[date.getDay()];
        var month = ("0" + (date.getMonth() + 1)).slice(-2); 
        var dayNum = ("0" + date.getDate()).slice(-2);
        return dayName + " " + month + "/" + dayNum;
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
    
    // --- Signals ---
    signal weatherIconUpdateRequested()
    
    // --- Functions ---
    // Lottie Icon Mapping Function
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
                return null;
            }
        } catch (e) {
            console.error("Exception loading Lottie file:", e);
            return null;
        }
    }

    // Function to update the Lottie animation
    function updateLottieAnimation() {
        if (weatherCode && lottieIconsBase && lottiePlayerPath && lottieHtmlTemplate) {
            try {
                var lottieJsonPath = getWeatherIconPath(weatherCode);
                var animationJson = loadLottieAnimation(lottieJsonPath);
                if (animationJson) {
                    var htmlContent = lottieHtmlTemplate
                        .replace("%ANIMATION_DATA%", animationJson)
                        .replace("%LOTTIE_PLAYER_PATH%", lottiePlayerPath);
                    weatherWeb.loadHtml(htmlContent, "file:///");
                    console.log("Updated Lottie animation successfully");
                }
            } catch (e) {
                console.error("Error updating animation:", e);
            }
        }
    }
    
    // Trigger update when the code changes
    onWeatherCodeChanged: {
        updateLottieAnimation();
    }
    
    // Handle external update requests
    onWeatherIconUpdateRequested: {
        updateLottieAnimation();
    }
    
    // --- UI Layout ---
    Column {
        id: currentWeatherColumn
        width: parent.width
        spacing: 10
        visible: statusMessage === ""
        
        // Status Text (Displayed when loading or error)
        Text {
            id: statusText
            width: parent.width
            text: statusMessage
            visible: statusMessage !== ""
            color: ThemeManager.text_secondary_color
            font.pixelSize: 16
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
        }

        // Weather Animation Container
        Rectangle {
            id: weatherIconContainer
            width: 150 
            height: 150
            color: "transparent"
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
                    if (loadRequest.status === WebEngineView.LoadFailedStatus) { 
                        console.error("Failed Lottie load:", loadRequest.errorString); 
                    }
                }
                onJavaScriptConsoleMessage: console.log("WebEngine JS:", message);
            }
        }

        // Current Temperature Text
        Text {
            id: currentTempText
            width: parent.width
            text: weatherData ? ("Current: " + Math.round(weatherData.current.temp) + "°F") : "--"
            color: ThemeManager.text_primary_color
            font.pixelSize: 22 
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
        }
        
        // Weather Description
        Text {
            id: weatherDescription
            width: parent.width
            text: weatherData && weatherData.current && weatherData.current.weather && weatherData.current.weather.length > 0 ? 
                  weatherData.current.weather[0].description.charAt(0).toUpperCase() + weatherData.current.weather[0].description.slice(1) : ""
            visible: text !== ""
            color: ThemeManager.text_secondary_color
            font.pixelSize: 16 
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
        }
    }
} 