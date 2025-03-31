import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtWebEngine 1.8
import MyTheme 1.0
import MyServices 1.0 

BaseScreen {
    id: weatherScreen
    
    screenControls: "WeatherControls.qml"
    title: "Weather"
    
    property var currentWeatherData: null
    property string statusMessage: "Loading weather..."
    property string currentWeatherCode: ""
    
    // Define the absolute path to your Lottie files
    property string lottieIconsBase: "/home/jack/PYSIDE_RASPI_FRONTEND/frontend/icons/weather/lottie/"

    // HTML template for displaying Lottie animations - using local lottie player
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
      <script>
        // Embedded Lottie player library to avoid network dependencies
        %LOTTIE_PLAYER%
      </script>
    </head>
    <body>
      <div id="lottie"></div>
      <script>
        // We use a direct animation object instead of loading from URL
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

    // Load the Lottie player code to embed in our HTML
    property string lottiePlayerCode: '!function(t,e){"object"==typeof exports&&"undefined"!=typeof module?e(exports):"function"==typeof define&&define.amd?define(["exports"],e):e((t="undefined"!=typeof globalThis?globalThis:t||self).lottie={})}(this,(function(t){"use strict";var e="5.9.6";function r(t){return(r="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t})(t)}function i(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}function s(t,e){for(var r=0;r<e.length;r++){var i=e[r];i.enumerable=i.enumerable||!1,i.configurable=!0,"value"in i&&(i.writable=!0),Object.defineProperty(t,i.key,i)}}function a(t,e,r){return e&&s(t.prototype,e),r&&s(t,r),t}function n(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),e&&o(t,e)}function o(t,e){return(o=Object.setPrototypeOf||function(t,e){return t.__proto__=e,t})(t,e)}function h(t){var e=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}());return function(){var r,i=u(t);if(e){var s=u(this).constructor;r=Reflect.construct(i,arguments,s)}else r=i.apply(this,arguments);return l(this,r)}}function l(t,e){return!e||"object"!=typeof e&&"function"!=typeof e?function(t){if(void 0===t)throw new ReferenceError("this hasn\'t been initialised - super() hasn\'t been called");return t}(t):e}function p(t){return(p=Object.setPrototypeOf?Object.getPrototypeOf:function(t){return t.__proto__||Object.getPrototypeOf(t)})(t)}'

    // --- Icon Mapping Function ---
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
        // Try to directly load the file without XMLHttpRequest
        var xhr = new XMLHttpRequest();
        xhr.open("GET", "file://" + filePath, false); // Synchronous request
        xhr.send(null);
        
        if (xhr.status === 200) {
            console.log("Successfully loaded Lottie file:", filePath);
            try {
                return xhr.responseText;
            } catch (e) {
                console.error("Error parsing JSON:", e);
                return null;
            }
        } else {
            console.error("Error loading Lottie file:", filePath, "Status:", xhr.status);
            return null;
        }
    }

    // Function to update the Lottie animation
    function updateLottieAnimation() {
        if (currentWeatherCode) {
            try {
                var lottieJsonPath = getWeatherIconPath(currentWeatherCode);
                console.log("Loading Lottie file from:", lottieJsonPath);
                
                // Use direct file paths with the file:// protocol
                var htmlContent = lottieHtmlTemplate
                    .replace("%LOTTIE_PLAYER%", lottiePlayerCode)
                    .replace("%ANIMATION_DATA%", loadLottieAnimation(lottieJsonPath));
                
                weatherWeb.loadHtml(htmlContent, "file:///");
                console.log("Updated Lottie animation with path:", lottieJsonPath);
            } catch (e) {
                console.error("Error loading animation:", e);
                statusMessage = "Error loading animation.";
            }
        }
    }

    // Function to fetch weather data
    function fetchWeather() {
        console.log("Attempting to fetch weather data...")
        var xhr = new XMLHttpRequest();
        xhr.onreadystatechange = function() {
            if (xhr.readyState === XMLHttpRequest.DONE) {
                if (xhr.status === 200) {
                    try {
                        var response = JSON.parse(xhr.responseText);
                        currentWeatherData = response;
                        statusMessage = ""; 
                        console.log("Weather data fetched successfully.")
                        
                        // Update the weather icon code based on fetched data
                        if (currentWeatherData && currentWeatherData.current && 
                            currentWeatherData.current.weather && 
                            currentWeatherData.current.weather.length > 0) {
                            currentWeatherCode = currentWeatherData.current.weather[0].icon;
                            console.log("Setting weather code to:", currentWeatherCode);
                            updateLottieAnimation();
                        } else {
                            console.warn("Could not find weather icon code in response.");
                            currentWeatherCode = "01d"; // Default to clear day if no code available
                            updateLottieAnimation();
                        }
                    } catch (e) {
                        console.error("Error parsing weather data:", e);
                        statusMessage = "Error parsing weather data.";
                    }
                } else {
                    console.error("Error fetching weather data. Status:", xhr.status, xhr.statusText);
                    statusMessage = "Error fetching weather data. Status: " + xhr.status;
                    if (xhr.status === 503) {
                         statusMessage = "Weather data not yet available from backend.";
                    }
                }
            }
        }
        xhr.open("GET", "http://localhost:8000/api/weather");
        xhr.send();
    }

    // Fetch data when the component is ready
    Component.onCompleted: {
        fetchWeather();
        // Set up a timer to refresh the data every 30 minutes
        weatherTimer.start();
    }

    // Timer to refresh weather data periodically
    Timer {
        id: weatherTimer
        interval: 1800000 // 30 minutes
        repeat: true
        running: false 
        onTriggered: {
            fetchWeather();
        }
    }

    // Content Area
    Rectangle {
        id: weatherContent
        anchors.fill: parent
        color: "transparent"
        
        Column {
            anchors.centerIn: parent
            spacing: 20
            width: parent.width * 0.9

            // Status Text
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
                width: 200
                height: 200
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
                            console.log("Lottie animation loaded successfully");
                        } else if (loadRequest.status === WebEngineView.LoadFailedStatus) {
                            console.error("Failed to load Lottie animation:", loadRequest.errorString);
                        }
                    }
                    
                    onJavaScriptConsoleMessage: function(level, message, lineNumber, sourceID) {
                        console.log("WebEngine JS:", message, "at line", lineNumber);
                    }
                }
            }

            // Current Temperature Text
            Text {
                id: currentTempText
                width: parent.width
                text: currentWeatherData ? 
                      ("Current Temperature: " + Math.round(currentWeatherData.current.temp) + "°F") : "--"
                visible: statusMessage === ""
                color: ThemeManager.text_primary_color
                font.pixelSize: 24
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
                font.pixelSize: 18
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
            }
        }
    }
}
