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
    property string statusMessage: "Loading weather..."
    
    // --- Configuration Properties ---
    property string lottieIconsBase: PathProvider.getAbsolutePath("frontend/icons/weather/lottie") + "/"
    property string lottiePlayerPath: PathProvider.getAbsolutePath("frontend/assets/js/lottie.min.js")
    property string pngIconsBase: "file://" + PathProvider.getAbsolutePath("frontend/icons/weather/PNG") + "/"
    
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
                        
                        // Debug daily data for forecast
                        if (response && response.daily && response.daily.length > 0) {
                            console.log("Daily data before transformation:");
                            for (var i = 0; i < response.daily.length; i++) {
                                console.log("Day " + i + 
                                          " - Date: " + currentWeather.formatDateToDay(response.daily[i].dt) + 
                                          ", PoP: " + response.daily[i].pop + 
                                          ", Weather: " + response.daily[i].weather[0].description +
                                          ", Icon: " + response.daily[i].weather[0].icon);
                            }
                        }
                        
                        currentWeatherData = response; 
                        statusMessage = ""; 
                        console.log("Weather data fetched successfully (WeatherScreen).");
                        
                        // Update weather code for the current weather component 
                        if (currentWeatherData && currentWeatherData.current && 
                            currentWeatherData.current.weather && currentWeatherData.current.weather.length > 0) {
                            currentWeather.weatherCode = currentWeatherData.current.weather[0].icon;
                            console.log("Current weather code:", currentWeather.weatherCode, 
                                       "Description:", currentWeatherData.current.weather[0].description);
                        }
                    } catch (e) {
                        console.error("Error parsing weather data (WeatherScreen):", e);
                        statusMessage = "Error parsing weather data.";
                        currentWeatherData = null;
                    }
                } else {
                    console.error("Error fetching weather data (WeatherScreen). Status:", xhr.status);
                    statusMessage = "Error fetching weather data. Status: " + xhr.status;
                    if (xhr.status === 503) { 
                        statusMessage = "Weather data not yet available."; 
                    }
                    currentWeatherData = null;
                }
            }
        }
        xhr.open("GET", SettingsService.httpBaseUrl + "/api/weather"); 
        xhr.send();
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
        id: flickableArea
        anchors.fill: parent
        contentHeight: contentColumn.implicitHeight 
        clip: true 
        flickableDirection: Flickable.VerticalFlick 

        ColumnLayout { 
            id: contentColumn 
            width: parent.width * 0.95 
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

            // --- Current Weather Component ---
            CurrentWeather {
                id: currentWeather
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignHCenter
                weatherData: currentWeatherData
                statusMessage: weatherScreen.statusMessage
                lottieIconsBase: weatherScreen.lottieIconsBase
                lottiePlayerPath: weatherScreen.lottiePlayerPath
                visible: weatherScreen.statusMessage === ""
            }

            // --- Forecast Component ---
            ForecastDisplay {
                id: forecastDisplay
                Layout.topMargin: 40
                Layout.fillWidth: true
                forecastData: currentWeatherData ? 
                              (currentWeatherData.daily ? currentWeatherData.daily.slice(2, 8) : []) : []
                statusMessage: weatherScreen.statusMessage
                pngIconsBase: weatherScreen.pngIconsBase
                visible: weatherScreen.statusMessage === ""
            }
        }
    }
}
