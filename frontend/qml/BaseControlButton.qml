import QtQuick 2.15
import QtQuick.Controls 2.15
import MyTheme 1.0

AbstractButton {
    id: baseButton
    
    // Increase touch area
    implicitWidth: 60
    implicitHeight: 50
    
    // Touch-specific properties
    focusPolicy: Qt.NoFocus
    hoverEnabled: true
    
    // Visual feedback background
    Rectangle {
        id: buttonBackground
        anchors.fill: parent
        color: baseButton.pressed || baseButton.checked ? 
               Qt.rgba(ThemeManager.button_primary_color.r, 
                      ThemeManager.button_primary_color.g, 
                      ThemeManager.button_primary_color.b, 0.2) : "transparent"
        radius: 8

        Behavior on color {
            ColorAnimation { duration: 100 }
        }
    }

    // Multi-touch area
    MultiPointTouchArea {
        anchors.fill: parent
        anchors.margins: -10
        mouseEnabled: true
        minimumTouchPoints: 1
        maximumTouchPoints: 1
        
        onPressed: baseButton.pressed = true
        onReleased: {
            baseButton.pressed = false
            baseButton.clicked()
        }
        onTouchUpdated: {
            // Handle touch point updates if needed
        }
    }
}
