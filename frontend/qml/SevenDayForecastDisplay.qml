import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import MyTheme 1.0
import MyServices 1.0 // Assuming PathProvider might be needed indirectly or for consistency

// 7-Day Forecast Display Component
Item {
    id: sevenDayForecastDisplay
    width: parent.width
    implicitHeight: mainColumnLayout.implicitHeight

    // --- Properties ---
    property var forecastData: null // Expects an array of 7 daily forecast objects
    property string pngIconsBase: "" // Base path for PNG icons, e.g., "file:///path/to/icons/weather/PNG/"
    property string statusMessage: "" // Optional status message

    // --- Signals ---
    // signal dayForecastClicked(int index) // Add if needed later

    // --- Functions ---
    // NWS PNG Icon Mapping Function (To be implemented based on user provided mapping)
    function getNwsPngIconPath(nwsIconUrl) {
        // Placeholder mapping - needs full implementation
        console.log("Mapping NWS Icon URL:", nwsIconUrl);

        // Basic example: Extract filename part (needs refinement)
        if (!nwsIconUrl) return pngIconsBase + "not-available.png";

        // --- Full Mapping Logic Goes Here ---
        // Example structure:
        const iconMap = {
            // Day Icons Mapping (from user prompt)
            "https://api.weather.gov/icons/land/day/skc?size=medium": "clear-day.png",
            "https://api.weather.gov/icons/land/day/few?size=medium": "partly-cloudy-day.png",
            "https://api.weather.gov/icons/land/day/sct?size=medium": "partly-cloudy-day.png",
            "https://api.weather.gov/icons/land/day/bkn?size=medium": "cloudy.png",
            "https://api.weather.gov/icons/land/day/ovc?size=medium": "overcast-day.png",
            "https://api.weather.gov/icons/land/day/wind_skc?size=medium": "clear-day.png",
            "https://api.weather.gov/icons/land/day/wind_few?size=medium": "partly-cloudy-day.png",
            "https://api.weather.gov/icons/land/day/wind_sct?size=medium": "partly-cloudy-day.png",
            "https://api.weather.gov/icons/land/day/wind_bkn?size=medium": "cloudy.png",
            "https://api.weather.gov/icons/land/day/wind_ovc?size=medium": "overcast-day.png",
            "https://api.weather.gov/icons/land/day/snow?size=medium": "snow.png",
            "https://api.weather.gov/icons/land/day/rain_snow?size=medium": "sleet.png",
            "https://api.weather.gov/icons/land/day/rain_sleet?size=medium": "sleet.png",
            "https://api.weather.gov/icons/land/day/snow_sleet?size=medium": "sleet.png",
            "https://api.weather.gov/icons/land/day/fzra?size=medium": "rain.png", // Assuming fzra maps to rain
            "https://api.weather.gov/icons/land/day/rain_fzra?size=medium": "rain.png",
            "https://api.weather.gov/icons/land/day/snow_fzra?size=medium": "rain.png",
            "https://api.weather.gov/icons/land/day/sleet?size=medium": "sleet.png",
            "https://api.weather.gov/icons/land/day/rain?size=medium": "rain.png",
            "https://api.weather.gov/icons/land/day/rain_showers?size=medium": "rain.png", // Assuming rain_showers maps to rain
            "https://api.weather.gov/icons/land/day/rain_showers_hi?size=medium": "extreme-day-rain.png",
            "https://api.weather.gov/icons/land/day/tsra?size=medium": "thunderstorms-day.png",
            "https://api.weather.gov/icons/land/day/tsra_sct?size=medium": "thunderstorms-day-overcast.png",
            "https://api.weather.gov/icons/land/day/tsra_hi?size=medium": "thunderstorms-day-extreme.png",
            "https://api.weather.gov/icons/land/day/tornado?size=medium": "tornado.png",
            "https://api.weather.gov/icons/land/day/hurricane?size=medium": "hurricane.png",
            "https://api.weather.gov/icons/land/day/tropical_storm?size=medium": "hurricane.png",
            "https://api.weather.gov/icons/land/day/dust?size=medium": "dust-day.png",
            "https://api.weather.gov/icons/land/day/smoke?size=medium": "smoke.png",
            "https://api.weather.gov/icons/land/day/haze?size=medium": "haze-day.png",
            "https://api.weather.gov/icons/land/day/hot?size=medium": "sun-hot.png", // Assuming hot maps to sun-hot
            "https://api.weather.gov/icons/land/day/cold?size=medium": "thermometer-mercury-cold.png",
            "https://api.weather.gov/icons/land/day/blizzard?size=medium": "extreme-day-snow.png",
            "https://api.weather.gov/icons/land/day/fog?size=medium": "fog-day.png",
            // Night Icons Mapping (from user prompt)
            "https://api.weather.gov/icons/land/night/skc?size=medium": "clear-night.png",
            "https://api.weather.gov/icons/land/night/few?size=medium": "partly-cloudy-night.png",
            "https://api.weather.gov/icons/land/night/sct?size=medium": "partly-cloudy-night.png",
            "https://api.weather.gov/icons/land/night/bkn?size=medium": "cloudy.png",
            "https://api.weather.gov/icons/land/night/ovc?size=medium": "overcast-night.png",
            "https://api.weather.gov/icons/land/night/wind_skc?size=medium": "clear-night.png",
            "https://api.weather.gov/icons/land/night/wind_few?size=medium": "partly-cloudy-night.png",
            "https://api.weather.gov/icons/land/night/wind_sct?size=medium": "partly-cloudy-night.png",
            "https://api.weather.gov/icons/land/night/wind_bkn?size=medium": "cloudy.png",
            "https://api.weather.gov/icons/land/night/wind_ovc?size=medium": "overcast-night.png",
            "https://api.weather.gov/icons/land/night/snow?size=medium": "snow.png",
            "https://api.weather.gov/icons/land/night/rain_snow?size=medium": "sleet.png",
            "https://api.weather.gov/icons/land/night/rain_sleet?size=medium": "sleet.png",
            "https://api.weather.gov/icons/land/night/snow_sleet?size=medium": "sleet.png",
            "https://api.weather.gov/icons/land/night/fzra?size=medium": "rain.png", // Assuming fzra maps to rain
            "https://api.weather.gov/icons/land/night/rain_fzra?size=medium": "rain.png",
            "https://api.weather.gov/icons/land/night/snow_fzra?size=medium": "rain.png",
            "https://api.weather.gov/icons/land/night/sleet?size=medium": "sleet.png",
            "https://api.weather.gov/icons/land/night/rain?size=medium": "rain.png",
            "https://api.weather.gov/icons/land/night/rain_showers?size=medium": "overcast-night-rain.png",
            "https://api.weather.gov/icons/land/night/rain_showers_hi?size=medium": "extreme-night-rain.png",
            "https://api.weather.gov/icons/land/night/tsra?size=medium": "thunderstorms-night.png",
            "https://api.weather.gov/icons/land/night/tsra_sct?size=medium": "thunderstorms-night-overcast.png",
            "https://api.weather.gov/icons/land/night/tsra_hi?size=medium": "thunderstorms-night-extreme.png",
            "https://api.weather.gov/icons/land/night/tornado?size=medium": "tornado.png",
            "https://api.weather.gov/icons/land/night/hurricane?size=medium": "hurricane.png",
            "https://api.weather.gov/icons/land/night/tropical_storm?size=medium": "hurricane.png",
            "https://api.weather.gov/icons/land/night/dust?size=medium": "dust-night.png",
            "https://api.weather.gov/icons/land/night/smoke?size=medium": "smoke.png",
            "https://api.weather.gov/icons/land/night/haze?size=medium": "haze-night.png",
            "https://api.weather.gov/icons/land/night/hot?size=medium": "thermometer-warmer.png", // Assuming hot maps to warmer
            "https://api.weather.gov/icons/land/night/cold?size=medium": "thermometer-mercury-cold.png",
            "https://api.weather.gov/icons/land/night/blizzard?size=medium": "extreme-night-snow.png",
            "https://api.weather.gov/icons/land/night/fog?size=medium": "fog-night.png"
        };

        // Need to handle potential variations in URL (e.g., probability, different sizes)
        let baseUrl = nwsIconUrl;
        if (baseUrl.includes("?size=")) {
            baseUrl = baseUrl.split("?size=")[0] + "?size=medium"; // Normalize to medium size for lookup
        }
        // Handle potential probability values like ",30"
        if (baseUrl.includes(",")) {
             baseUrl = baseUrl.split(",")[0] + "?size=medium";
        }


        if (iconMap[baseUrl]) {
            return pngIconsBase + iconMap[baseUrl];
        } else {
            console.warn("No PNG icon mapping found for:", nwsIconUrl, "Base URL used:", baseUrl);
            return pngIconsBase + "not-available.png"; // Default fallback
        }
    }

    // --- UI Layout ---
    ColumnLayout {
        id: mainColumnLayout
        width: parent.width
        spacing: 10 // Spacing between daily rows
        visible: statusMessage === "" && forecastData && forecastData.length > 0

        Repeater {
            model: forecastData

            delegate: RowLayout {
                width: parent.width
                spacing: 10 // Spacing between elements in a row

                // Day Name
                Text {
                    id: dayNameText
                    text: modelData.name // Assuming data has 'name' like "Mon" or "Monday"
                    color: ThemeManager.text_primary_color
                    font.pixelSize: 16
                    font.bold: true
                    Layout.minimumWidth: 50 // Ensure consistent width for day name
                    Layout.alignment: Qt.AlignVCenter
                }

                // Weather Icon
                Image {
                    id: forecastIcon
                    width: 40; height: 40 // Smaller icon size for row layout
                    source: getNwsPngIconPath(modelData.icon) // Assuming data has 'icon' URL
                    Layout.alignment: Qt.AlignVCenter
                    fillMode: Image.PreserveAspectFit
                    sourceSize.width: 40; sourceSize.height: 40
                }

                // Short Forecast Description
                Text {
                    id: shortForecastText
                    text: modelData.shortForecast // Assuming data has 'shortForecast'
                    color: ThemeManager.text_secondary_color
                    font.pixelSize: 14
                    Layout.fillWidth: true // Take remaining space
                    Layout.alignment: Qt.AlignVCenter
                    wrapMode: Text.WordWrap // Wrap if necessary
                    elide: Text.ElideRight
                }

                // High / Low Temperature
                Text {
                    id: tempText
                    // Assuming data has 'temperature' and 'temperatureUnit' or similar
                    text: modelData.temperature + modelData.temperatureUnit // Example: "75°F"
                          // Might need more complex logic if high/low are separate fields
                    color: ThemeManager.text_primary_color
                    font.pixelSize: 16
                    Layout.minimumWidth: 60 // Ensure consistent width for temp
                    Layout.alignment: Qt.AlignVCenter | Qt.AlignRight
                    horizontalAlignment: Text.AlignRight
                }

                // Optional: Add MouseArea for click interaction later
                // MouseArea {
                //     anchors.fill: parent
                //     onClicked: {
                //         sevenDayForecastDisplay.dayForecastClicked(index);
                //     }
                //     cursorShape: Qt.PointingHandCursor
                // }
            }
        }
    }

    // Status Text (visible only when loading or error)
    Text {
        id: statusTextDisplay
        anchors.centerIn: parent
        text: statusMessage
        visible: statusMessage !== ""
        color: ThemeManager.text_secondary_color
        font.pixelSize: 16
        horizontalAlignment: Text.AlignHCenter
        wrapMode: Text.WordWrap
    }
}