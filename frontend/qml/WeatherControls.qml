import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import MyTheme 1.0
import MyServices 1.0

BaseControls {
    id: weatherControls
    
    // Reference to the parent screen
    property var screen: null
    
    // Reference to the main stack view - will be set by MainWindow
    property var mainStackView: null
    
    // Navigation buttons for weather screens
    Button {
        id: currentWeatherButton
        text: "72 Hour"
        font.pixelSize: 16
        font.bold: true
        implicitWidth: 90
        implicitHeight: 40
        
        background: Rectangle {
            color: "transparent" // Remove background color change on selection
            radius: 8
            border.width: 1
            border.color: screen && screen.currentView === "current"
                ? "#565f89" // Set specific border color when selected
                : "transparent"
        }
        
        contentItem: Text {
            text: currentWeatherButton.text
            font: currentWeatherButton.font
            color: ThemeManager.text_primary_color
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }
        
        onClicked: {
            if (screen) {
                screen.currentView = "current";
            } else if (mainStackView) {
                // If screen isn't set, use navigation controller to navigate
                NavigationController.navigateWithParams("WeatherScreen.qml", {"viewType": "current"});
            }
        }
    }
    
    Button {
        id: hourlyButton
        text: "Hourly"
        font.pixelSize: 16
        font.bold: true
        implicitWidth: 90
        implicitHeight: 40
        
        background: Rectangle {
            color: "transparent"
            radius: 8
            border.width: 1
            border.color: screen && screen.currentView === "hourly"
                ? "#565f89"
                : "transparent"
        }
        
        contentItem: Text {
            text: hourlyButton.text
            font: hourlyButton.font
            color: ThemeManager.text_primary_color
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }
        
        onClicked: {
            if (screen) {
                screen.currentView = "hourly";
            } else if (mainStackView) {
                // If screen isn't set, use navigation controller to navigate
                NavigationController.navigateWithParams("WeatherScreen.qml", {"viewType": "hourly"});
            }
        }
    }
    
    Button {
        id: forecastButton
        text: "7 Day"
        font.pixelSize: 16
        font.bold: true
        implicitWidth: 90
        implicitHeight: 40
        
        background: Rectangle {
            color: "transparent" // Remove background color change on selection
            radius: 8
            border.width: 1
            border.color: screen && screen.currentView === "forecast"
                ? "#565f89" // Set specific border color when selected
                : "transparent"
        }
        
        contentItem: Text {
            text: forecastButton.text
            font: forecastButton.font
            color: ThemeManager.text_primary_color
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }
        
        onClicked: {
            if (screen) {
                screen.currentView = "forecast";
            } else if (mainStackView) {
                // If screen isn't set, use navigation controller to navigate
                NavigationController.navigateWithParams("WeatherScreen.qml", {"viewType": "sevenday"});
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
                screen.fetchWeather(true)
            }
        }
    }
}
