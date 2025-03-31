import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import MyTheme 1.0

Item {
    id: forecastRoot
    width: parent.width // Take available width
    // REMOVE explicit height: Let parent ColumnLayout manage height

    // --- Properties Passed from Parent (WeatherScreen) ---
    property var currentWeatherData: null
    property string statusMessage: "" // Assume parent handles overall status
    property string svgIconsBase: "file:///home/jack/PYSIDE_RASPI_FRONTEND/frontend/icons/weather/" // Default path

    // --- SVG Icon Mapping Function ---
    function getWeatherSvgIconPath(owmIconCode, weatherDescription) {
        // Map based on description first, then fall back to icon codes
        if (weatherDescription) {
            console.log("Mapping weather description:", weatherDescription);
            if (weatherDescription.includes("clear")) {
                return svgIconsBase + "clear-day.svg";
            } else if (weatherDescription.includes("few clouds")) {
                return svgIconsBase + "partly-cloudy-day.svg";
            } else if (weatherDescription.includes("scattered clouds")) {
                return svgIconsBase + "cloudy.svg";
            } else if (weatherDescription.includes("broken clouds")) {
                return svgIconsBase + "overcast-day.svg";
            } else if (weatherDescription.includes("overcast")) {
                return svgIconsBase + "overcast-day.svg";
            } else if (weatherDescription.includes("rain") || weatherDescription.includes("drizzle")) {
                return svgIconsBase + "partly-cloudy-day-rain.svg";
            } else if (weatherDescription.includes("thunderstorm")) {
                return svgIconsBase + "thunderstorms-day.svg";
            } else if (weatherDescription.includes("snow")) {
                return svgIconsBase + "partly-cloudy-day-snow.svg";
            } else if (weatherDescription.includes("mist") || weatherDescription.includes("fog")) {
                return svgIconsBase + "mist.svg";
            }
        }
        
        // Fall back to original icon code mapping
        const iconMap = {
            "01d": "clear-day.svg",
            "01n": "clear-night.svg",
            "02d": "partly-cloudy-day.svg",
            "02n": "partly-cloudy-night.svg",
            "03d": "cloudy.svg",
            "03n": "cloudy.svg", // Same icon for day/night scattered clouds
            "04d": "overcast-day.svg",
            "04n": "overcast-night.svg",
            "09d": "drizzle.svg", // Using drizzle for shower rain day
            "09n": "drizzle.svg", // Using drizzle for shower rain night
            "10d": "partly-cloudy-day-rain.svg",
            "10n": "partly-cloudy-night-rain.svg",
            "11d": "thunderstorms-day.svg",
            "11n": "thunderstorms-night.svg",
            "13d": "partly-cloudy-day-snow.svg", // Assuming partly cloudy snow for day
            "13n": "partly-cloudy-night-snow.svg", // Assuming partly cloudy snow for night
            "50d": "mist.svg",
            "50n": "mist.svg" // Same icon for day/night mist
        };
        
        if (!iconMap[owmIconCode]) {
            console.warn("Unknown weather icon code for SVG:", owmIconCode);
            return svgIconsBase + "not-available.svg"; // Default fallback SVG
        }
        
        return svgIconsBase + iconMap[owmIconCode];
    }

    // --- Date Formatting Function ---
    function formatDateToDay(unixTimestamp) {
        // Multiply by 1000 because JavaScript Date expects milliseconds
        var date = new Date(unixTimestamp * 1000);
        var days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
        var dayName = days[date.getDay()];
        // Get month (0-indexed) and day, add leading zeros if needed
        var month = ("0" + (date.getMonth() + 1)).slice(-2);
        var dayNum = ("0" + date.getDate()).slice(-2);
        return dayName + " " + month + "/" + dayNum;
    }

    // --- UI Elements ---
    // Directly use RowLayout, positioned by parent ColumnLayout in WeatherScreen
    RowLayout {
        id: forecastRowLayout
        // Let parent ColumnLayout manage width and position
        // anchors.horizontalCenter: parent.horizontalCenter // Managed by parent layout
        Layout.fillWidth: true // Make the RowLayout use the full width provided by parent
        spacing: 15 // Increased spacing between forecast days

        // Visibility handled by the parent component (ForecastDisplay) in WeatherScreen
        visible: forecastRoot.statusMessage === "" && forecastRoot.currentWeatherData && forecastRoot.currentWeatherData.daily && forecastRoot.currentWeatherData.daily.length > 0

                Repeater {
                    // Take days 2-7 to show more varied weather conditions
                    model: {
                        console.log("Full daily data:", currentWeatherData ? currentWeatherData.daily : "No data");
                        var slicedData = currentWeatherData ? (currentWeatherData.daily ? currentWeatherData.daily.slice(2, 8) : []) : [];
                        console.log("Sliced forecast data:", slicedData);
                        return slicedData;
                    }

                    delegate: Column {
                        Layout.fillWidth: true // Distribute width evenly
                        Layout.alignment: Qt.AlignTop // Align items to the top
                        spacing: 5

                        // Day and Date
                        Text {
                            text: {
                                console.log("Processing day:", modelData);
                                console.log("Day PoP:", modelData.pop);
                                return formatDateToDay(modelData.dt);
                            }
                            color: ThemeManager.text_primary_color
                            font.pixelSize: 14
                            horizontalAlignment: Text.AlignHCenter
                            anchors.horizontalCenter: parent.horizontalCenter
                        }

                        // Weather Icon (SVG)
                        Image {
                            id: forecastIcon
                            width: 50
                            height: 50
                            source: getWeatherSvgIconPath(modelData.weather[0].icon, modelData.weather[0].description)
                            anchors.horizontalCenter: parent.horizontalCenter
                            fillMode: Image.PreserveAspectFit
                            sourceSize.width: 50
                            sourceSize.height: 50
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
                            text: {
                                console.log("Day data:", modelData);
                                console.log("PoP value:", modelData.pop);
                                console.log("PoP type:", typeof modelData.pop);
                                var popValue = modelData.pop;
                                console.log("Raw PoP value:", popValue);
                                var percentage = popValue !== undefined ? Math.round(popValue * 100) : 0;
                                console.log("Calculated percentage:", percentage);
                                return popValue !== undefined ? (percentage + "% rain") : "";
                            }
                            color: ThemeManager.text_secondary_color
                            font.pixelSize: 12
                            horizontalAlignment: Text.AlignHCenter
                            anchors.horizontalCenter: parent.horizontalCenter
                            visible: modelData.pop !== undefined
                        }
                    } // End Repeater
                } // End RowLayout
// Remove extra closing braces from previous refactoring
} // End RowLayout
} // Add missing closing brace for root Item