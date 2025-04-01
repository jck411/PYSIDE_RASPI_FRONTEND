import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

BaseControls {
    id: weatherControls
    
    // Reference to the parent screen
    property var screen: null
    
    // Navigation buttons for weather screens
    TouchFriendlyButton {
        id: currentWeatherButton
        source: "../icons/weather.svg"
        text: "Current Weather"
        opacity: screen && screen.currentView === "current" ? 1.0 : 0.6
        onClicked: {
            if (screen) {
                screen.currentView = "current"
            }
        }
    }
    
    TouchFriendlyButton {
        id: forecastButton
        source: "../icons/calendar.svg"
        text: "Forecast"
        opacity: screen && screen.currentView === "forecast" ? 1.0 : 0.6
        onClicked: {
            if (screen) {
                screen.currentView = "forecast"
            }
        }
    }
    
    // Refresh button
    TouchFriendlyButton {
        id: refreshButton
        source: "../icons/refresh.svg"
        text: "Refresh"
        onClicked: {
            if (screen) {
                screen.fetchWeather()
            }
        }
    }
}
