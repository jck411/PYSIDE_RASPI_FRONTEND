import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import MyTheme 1.0
import MyServices 1.0

BaseScreen {
    id: alarmScreen
    
    // Set the controls file for this screen
    screenControls: "AlarmControls.qml"
    title: "Alarms"
    
    // Minimal content to display
    Rectangle {
        anchors.fill: parent
                color: "transparent"
                
                Text {
                    anchors.centerIn: parent
            text: "Alarm Screen"
                    font.pixelSize: 32
                                                color: ThemeManager.text_primary_color
        }
    }
}
