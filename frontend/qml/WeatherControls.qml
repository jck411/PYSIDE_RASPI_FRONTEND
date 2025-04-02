import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import MyTheme 1.0

BaseControls {
    id: weatherControls
    
    // Reference to the parent screen
    property var screen: null
    
    // Navigation buttons for weather screens
    Button {
        id: currentWeatherButton
        text: "72 Hour"
        font.pixelSize: 16
        font.bold: true
        implicitWidth: 90
        implicitHeight: 40
        
        background: Rectangle {
            color: screen && screen.currentView === "current" 
                ? Qt.rgba(ThemeManager.button_primary_color.r, 
                         ThemeManager.button_primary_color.g, 
                         ThemeManager.button_primary_color.b, 0.3) 
                : Qt.rgba(0, 0, 0, 0.1)
            radius: 8
            border.width: 1
            border.color: screen && screen.currentView === "current"
                ? ThemeManager.button_primary_color
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
                screen.currentView = "current"
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
            color: screen && screen.currentView === "forecast" 
                ? Qt.rgba(ThemeManager.button_primary_color.r, 
                         ThemeManager.button_primary_color.g, 
                         ThemeManager.button_primary_color.b, 0.3) 
                : Qt.rgba(0, 0, 0, 0.1)
            radius: 8
            border.width: 1
            border.color: screen && screen.currentView === "forecast"
                ? ThemeManager.button_primary_color
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
