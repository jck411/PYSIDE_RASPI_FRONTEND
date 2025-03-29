import QtQuick 2.15
import QtQuick.Controls 2.15
import MyTheme 1.0

BaseScreen {
    id: weatherScreen
    
    // Set the controls file for this screen
    screenControls: "WeatherControls.qml"
    title: "Weather"
    
    // Override the content area
    Rectangle {
        id: weatherContent
        anchors.fill: parent
        color: "transparent"
        
        Text {
            text: "Weather Screen Placeholder"
            color: ThemeManager.text_primary_color
            anchors.centerIn: parent
        }
    }
}
