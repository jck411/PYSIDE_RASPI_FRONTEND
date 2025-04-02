import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import MyTheme 1.0

// Forecast Display Component
Item {
    id: forecastDisplay
    width: parent.width
    implicitHeight: forecastRowLayout.implicitHeight
    
    // --- Properties ---
    property var forecastData: null
    property string statusMessage: ""
    property string pngIconsBase: ""
    
    // --- Signals ---
    signal forecastItemClicked(int index)
    
    // --- Functions ---
    // Date Formatting Function
    function formatDateToDay(unixTimestamp) {
        var date = new Date(unixTimestamp * 1000);
        var days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
        var dayName = days[date.getDay()];
        var month = ("0" + (date.getMonth() + 1)).slice(-2); 
        var dayNum = ("0" + date.getDate()).slice(-2);
        return dayName + " " + month + "/" + dayNum;
    }
    
    // PNG Icon Mapping Function
    function getWeatherPngIconPath(owmIconCode, weatherDescription) {
        console.log("Mapping weather:", weatherDescription, "Icon code:", owmIconCode);
        
        // Map based on description first, then fall back to icon codes
        if (weatherDescription) {
            if (weatherDescription.includes("clear")) {
                return pngIconsBase + "clear-day.png";
            } else if (weatherDescription.includes("few clouds")) {
                return pngIconsBase + "partly-cloudy-day.png";
            } else if (weatherDescription.includes("scattered clouds")) {
                return pngIconsBase + "cloudy.png";
            } else if (weatherDescription.includes("broken clouds")) {
                return pngIconsBase + "overcast-day.png";
            } else if (weatherDescription.includes("overcast")) {
                return pngIconsBase + "overcast-day.png";
            } else if (weatherDescription.includes("rain") || weatherDescription.includes("drizzle")) {
                return pngIconsBase + "partly-cloudy-day-rain.png";
            } else if (weatherDescription.includes("thunderstorm")) {
                return pngIconsBase + "thunderstorms-day.png";
            } else if (weatherDescription.includes("snow")) {
                return pngIconsBase + "snow.png";
            } else if (weatherDescription.includes("mist") || weatherDescription.includes("fog")) {
                return pngIconsBase + "mist.png";
            }
        }
        
        // Fall back to icon code mapping if description doesn't match
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
        
        console.log("Mapped to icon:", iconMap[owmIconCode]);
        return pngIconsBase + iconMap[owmIconCode];
    }
    
    // --- UI Layout ---
    RowLayout {
        id: forecastRowLayout
        width: parent.width
        spacing: 15
        visible: statusMessage === "" && forecastData && forecastData.length > 0

        Repeater {
            model: forecastData

            delegate: Item {
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignTop
                height: forecastColumn.height
                width: forecastColumn.width
                
                // Add mouse area for entire forecast item
                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        forecastDisplay.forecastItemClicked(index);
                    }
                    cursorShape: Qt.PointingHandCursor
                }
                
                Column {
                    id: forecastColumn
                    width: parent.width
                    spacing: 5
                
                    // Day and Date
                    Text {
                        text: formatDateToDay(modelData.dt)
                        color: ThemeManager.text_primary_color
                        font.pixelSize: 14 
                        horizontalAlignment: Text.AlignHCenter
                        anchors.horizontalCenter: parent.horizontalCenter
                    }

                    // Weather Icon
                    Image {
                        id: forecastIcon
                        width: 50; height: 50
                        source: modelData && modelData.weather && modelData.weather.length > 0 ? 
                                getWeatherPngIconPath(modelData.weather[0].icon, modelData.weather[0].description) :
                                pngIconsBase + "not-available.png"
                        anchors.horizontalCenter: parent.horizontalCenter
                        fillMode: Image.PreserveAspectFit
                        sourceSize.width: 50; sourceSize.height: 50
                    }

                    // High / Low Temperature
                    Text {
                        text: modelData && modelData.temp ? 
                              (Math.round(modelData.temp.max || 0) + "° / " + Math.round(modelData.temp.min || 0) + "°") :
                              "N/A"
                        color: ThemeManager.text_secondary_color
                        font.pixelSize: 14
                        horizontalAlignment: Text.AlignHCenter
                        anchors.horizontalCenter: parent.horizontalCenter
                    }

                    // Chance of Rain (PoP)
                    Text {
                        text: modelData && modelData.pop !== undefined ? 
                              (Math.round(modelData.pop * 100) + "% rain") :
                              "N/A"
                        color: ThemeManager.text_secondary_color
                        font.pixelSize: 12 
                        horizontalAlignment: Text.AlignHCenter
                        anchors.horizontalCenter: parent.horizontalCenter
                        visible: true 
                    }
                }
            }
        }
    }
}