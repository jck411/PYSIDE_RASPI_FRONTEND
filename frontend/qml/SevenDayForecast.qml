import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import MyTheme 1.0

// Seven Day Forecast Display Component
Item {
    id: sevenDayForecast
    width: parent.width
    implicitHeight: forecastColumnLayout.implicitHeight
    
    // --- Properties ---
    property var forecastPeriods: null
    property string statusMessage: ""
    property string pngIconsBase: ""
    
    // --- Functions ---
    // Format date to display day of week and date (e.g., "Mon 07/15")
    function formatForecastDate(timeString) {
        var date = new Date(timeString);
        var days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
        var dayName = days[date.getDay()];
        var month = ("0" + (date.getMonth() + 1)).slice(-2); 
        var dayNum = ("0" + date.getDate()).slice(-2);
        return dayName + " " + month + "/" + dayNum;
    }
    
    // Function to map NWS icon URLs to PNG icon filenames
    function mapWeatherIconToPng(iconUrl) {
        // Day Icons Mapping
        const dayIconMap = {
            "https://api.weather.gov/icons/land/day/skc": "clear-day.png",
            "https://api.weather.gov/icons/land/day/few": "partly-cloudy-day.png",
            "https://api.weather.gov/icons/land/day/sct": "partly-cloudy-day.png",
            "https://api.weather.gov/icons/land/day/bkn": "cloudy.png",
            "https://api.weather.gov/icons/land/day/ovc": "overcast-day.png",
            "https://api.weather.gov/icons/land/day/wind_skc": "clear-day.png",
            "https://api.weather.gov/icons/land/day/wind_few": "partly-cloudy-day.png",
            "https://api.weather.gov/icons/land/day/wind_sct": "partly-cloudy-day.png",
            "https://api.weather.gov/icons/land/day/wind_bkn": "cloudy.png",
            "https://api.weather.gov/icons/land/day/wind_ovc": "overcast-day.png",
            "https://api.weather.gov/icons/land/day/snow": "snow.png",
            "https://api.weather.gov/icons/land/day/rain_snow": "sleet.png",
            "https://api.weather.gov/icons/land/day/rain_sleet": "sleet.png",
            "https://api.weather.gov/icons/land/day/snow_sleet": "sleet.png",
            "https://api.weather.gov/icons/land/day/fzra": "rain.png",
            "https://api.weather.gov/icons/land/day/rain_fzra": "rain.png",
            "https://api.weather.gov/icons/land/day/snow_fzra": "rain.png",
            "https://api.weather.gov/icons/land/day/sleet": "sleet.png",
            "https://api.weather.gov/icons/land/day/rain": "rain.png",
            "https://api.weather.gov/icons/land/day/rain_showers": "rain.png",
            "https://api.weather.gov/icons/land/day/rain_showers_hi": "extreme-day-rain.png",
            "https://api.weather.gov/icons/land/day/tsra": "thunderstorms-day.png",
            "https://api.weather.gov/icons/land/day/tsra_sct": "thunderstorms-day-overcast.png",
            "https://api.weather.gov/icons/land/day/tsra_hi": "thunderstorms-day-extreme.png",
            "https://api.weather.gov/icons/land/day/tornado": "tornado.png",
            "https://api.weather.gov/icons/land/day/hurricane": "hurricane.png",
            "https://api.weather.gov/icons/land/day/tropical_storm": "hurricane.png",
            "https://api.weather.gov/icons/land/day/dust": "dust-day.png",
            "https://api.weather.gov/icons/land/day/smoke": "smoke.png",
            "https://api.weather.gov/icons/land/day/haze": "haze-day.png",
            "https://api.weather.gov/icons/land/day/hot": "sun-hot.png",
            "https://api.weather.gov/icons/land/day/cold": "thermometer-mercury-cold.png",
            "https://api.weather.gov/icons/land/day/blizzard": "extreme-day-snow.png",
            "https://api.weather.gov/icons/land/day/fog": "fog-day.png"
        };
        
        // Night Icons Mapping
        const nightIconMap = {
            "https://api.weather.gov/icons/land/night/skc": "clear-night.png",
            "https://api.weather.gov/icons/land/night/few": "partly-cloudy-night.png",
            "https://api.weather.gov/icons/land/night/sct": "partly-cloudy-night.png",
            "https://api.weather.gov/icons/land/night/bkn": "cloudy.png",
            "https://api.weather.gov/icons/land/night/ovc": "overcast-night.png",
            "https://api.weather.gov/icons/land/night/wind_skc": "clear-night.png",
            "https://api.weather.gov/icons/land/night/wind_few": "partly-cloudy-night.png",
            "https://api.weather.gov/icons/land/night/wind_sct": "partly-cloudy-night.png",
            "https://api.weather.gov/icons/land/night/wind_bkn": "cloudy.png",
            "https://api.weather.gov/icons/land/night/wind_ovc": "overcast-night.png",
            "https://api.weather.gov/icons/land/night/snow": "snow.png",
            "https://api.weather.gov/icons/land/night/rain_snow": "sleet.png",
            "https://api.weather.gov/icons/land/night/rain_sleet": "sleet.png",
            "https://api.weather.gov/icons/land/night/snow_sleet": "sleet.png",
            "https://api.weather.gov/icons/land/night/fzra": "rain.png",
            "https://api.weather.gov/icons/land/night/rain_fzra": "rain.png",
            "https://api.weather.gov/icons/land/night/snow_fzra": "rain.png",
            "https://api.weather.gov/icons/land/night/sleet": "sleet.png",
            "https://api.weather.gov/icons/land/night/rain": "rain.png",
            "https://api.weather.gov/icons/land/night/rain_showers": "overcast-night-rain.png",
            "https://api.weather.gov/icons/land/night/rain_showers_hi": "extreme-night-rain.png",
            "https://api.weather.gov/icons/land/night/tsra": "thunderstorms-night.png",
            "https://api.weather.gov/icons/land/night/tsra_sct": "thunderstorms-night-overcast.png",
            "https://api.weather.gov/icons/land/night/tsra_hi": "thunderstorms-night-extreme.png",
            "https://api.weather.gov/icons/land/night/tornado": "tornado.png",
            "https://api.weather.gov/icons/land/night/hurricane": "hurricane.png",
            "https://api.weather.gov/icons/land/night/tropical_storm": "hurricane.png",
            "https://api.weather.gov/icons/land/night/dust": "dust-night.png",
            "https://api.weather.gov/icons/land/night/smoke": "smoke.png",
            "https://api.weather.gov/icons/land/night/haze": "haze-night.png",
            "https://api.weather.gov/icons/land/night/hot": "thermometer-warmer.png",
            "https://api.weather.gov/icons/land/night/cold": "thermometer-mercury-cold.png",
            "https://api.weather.gov/icons/land/night/blizzard": "extreme-night-snow.png",
            "https://api.weather.gov/icons/land/night/fog": "fog-night.png"
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
                    return pngIconsBase + dayIconMap[key];
                }
            }
        } else if (baseUrl.includes("/night/")) {
            for (const key in nightIconMap) {
                if (baseUrl.startsWith(key)) {
                    return pngIconsBase + nightIconMap[key];
                }
            }
        }
        
        // Default fallback
        console.warn("No PNG icon mapping found for:", iconUrl);
        return pngIconsBase + "thermometer.png";
    }
    
    // --- UI Layout ---
    ColumnLayout {
        id: forecastColumnLayout
        width: parent.width
        spacing: 3
        visible: statusMessage === "" && forecastPeriods && forecastPeriods.length > 0
        
        // Status message when no data available
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
        
        // Each day's forecast as a row
        Repeater {
            // Skip the first 2 periods (shown on 72-hour screen) and show the next 12 periods
            model: forecastPeriods ? 
                   (forecastPeriods.length > 2 ? 
                    Math.min(12, forecastPeriods.length - 2) : 0) : 0
            
            delegate: Rectangle {
                id: forecastRow
                Layout.fillWidth: true
                Layout.preferredHeight: 50
                Layout.bottomMargin: 2
                color: index % 2 === 0 ? 
                       Qt.rgba(0, 0, 0, 0.1) : 
                       Qt.rgba(0, 0, 0, 0.05)
                radius: 4
                
                // Use GridLayout for better alignment
                GridLayout {
                    anchors.fill: parent
                    anchors.margins: 10
                    columns: 5
                    columnSpacing: 8
                    rowSpacing: 0
                    
                    // COLUMN 1: Date
                    Text {
                        Layout.preferredWidth: 70
                        Layout.fillHeight: true
                        text: formatForecastDate(forecastPeriods[index + 2].startTime)
                        color: ThemeManager.text_primary_color
                        font.pixelSize: 14
                        font.bold: true
                        verticalAlignment: Text.AlignVCenter
                    }
                    
                    // COLUMN 2: Day/Night indicator (simple text, no colored background)
                    Text {
                        Layout.preferredWidth: 40
                        Layout.fillHeight: true
                        text: forecastPeriods[index + 2].isDaytime ? "Day" : "Night"
                        color: ThemeManager.text_secondary_color
                        font.pixelSize: 12
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    
                    // COLUMN 3: Weather icon
                    Image {
                        Layout.preferredWidth: 40
                        Layout.preferredHeight: 40
                        Layout.alignment: Qt.AlignVCenter
                        source: mapWeatherIconToPng(forecastPeriods[index + 2].icon)
                        fillMode: Image.PreserveAspectFit
                    }
                    
                    // COLUMN 4: Temperature
                    Text {
                        Layout.preferredWidth: 45
                        Layout.fillHeight: true
                        text: forecastPeriods[index + 2].temperature + "°" + forecastPeriods[index + 2].temperatureUnit
                        color: ThemeManager.text_primary_color
                        font.pixelSize: 15
                        font.bold: true
                        verticalAlignment: Text.AlignVCenter
                    }
                    
                    // COLUMN 5: Forecast description
                    Text {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        text: forecastPeriods[index + 2].detailedForecast
                        color: ThemeManager.text_secondary_color
                        font.pixelSize: 13
                        wrapMode: Text.WordWrap
                        elide: Text.ElideRight
                        maximumLineCount: 3
                        verticalAlignment: Text.AlignVCenter
                    }
                }
            }
        }
    }
} 