import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import MyTheme 1.0

BaseScreen {
    id: clockScreen
    
    // Set the controls file for this screen
    screenControls: "ClockControls.qml"
    title: "Clock"
    
    // Content specific to the clock screen
    Rectangle {
        anchors.fill: parent
        color: "transparent"

        ColumnLayout {
            anchors.centerIn: parent
            anchors.verticalCenterOffset: -parent.height * 0.1  // Move 10% up from the center
            spacing: 20

            Text {
                id: timeText
                Layout.alignment: Qt.AlignCenter
                color: ThemeManager.text_primary_color
                font.pixelSize: 72
                font.bold: true
                text: "00:00:00"
            }

            Text {
                id: dateText
                Layout.alignment: Qt.AlignCenter
                color: ThemeManager.text_primary_color
                font.pixelSize: 28
                text: "January 1, 2023"
            }
        }

        Timer {
            interval: 1000
            running: true
            repeat: true
            triggeredOnStart: true
            onTriggered: {
                var date = new Date()
                timeText.text = date.toLocaleTimeString(Qt.locale(), "hh:mm:ss")
                dateText.text = date.toLocaleDateString(Qt.locale(), "MMMM d, yyyy")
            }
        }
    }
}
