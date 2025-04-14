import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import MyTheme 1.0

Popup {
    id: alarmPopup
    
    modal: true
    closePolicy: Popup.CloseOnEscape
    
    // Center in parent
    x: (parent.width - width) / 2
    y: (parent.height - height) / 2
    
    // Size
    width: Math.min(parent.width - 40, 400)
    height: 250
    
    // Dialog properties
    property string alarmId: ""
    property string alarmName: "Alarm"
    
    // Signals
    signal dismissed()
    signal snoozed()
    
    // Dialog content
    Rectangle {
        anchors.fill: parent
        color: ThemeManager.dialog_background_color
        radius: 10
        border.color: ThemeManager.border_color
        border.width: 1
        
        // Header
        Rectangle {
            id: popupHeader
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
            height: 50
            color: ThemeManager.dialog_header_color
            radius: 10
            
            // Only make the top corners rounded
            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                height: parent.height / 2
                color: parent.color
            }
            
            Text {
                text: "Alarm"
                color: ThemeManager.text_primary_color
                font.pixelSize: 18
                font.bold: true
                anchors.centerIn: parent
            }
        }
        
        // Content area
        ColumnLayout {
            anchors.top: popupHeader.bottom
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: popupFooter.top
            anchors.margins: 20
            spacing: 20
            
            Item { Layout.fillHeight: true }
            
            // Current time
            Text {
                id: timeText
                text: {
                    const now = new Date()
                    return now.toLocaleTimeString(Qt.locale(), "hh:mm:ss AP")
                }
                font.pixelSize: 28
                font.bold: true
                color: ThemeManager.text_primary_color
                Layout.alignment: Qt.AlignHCenter
            }
            
            // Alarm name
            Text {
                text: alarmName
                font.pixelSize: 20
                color: ThemeManager.text_primary_color
                horizontalAlignment: Text.AlignHCenter
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignHCenter
                wrapMode: Text.WordWrap
            }
            
            Item { Layout.fillHeight: true }
        }
        
        // Footer with buttons
        Rectangle {
            id: popupFooter
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            height: 60
            color: "transparent"
            
            RowLayout {
                anchors.fill: parent
                anchors.margins: 10
                spacing: 10
                
                Button {
                    text: "Snooze (5 min)"
                    Layout.fillWidth: true
                    
                    onClicked: {
                        alarmPopup.snoozed()
                        alarmPopup.close()
                    }
                }
                
                Button {
                    text: "Dismiss"
                    Layout.fillWidth: true
                    
                    onClicked: {
                        alarmPopup.dismissed()
                        alarmPopup.close()
                    }
                }
            }
        }
    }
    
    // Update time every second
    Timer {
        interval: 1000
        repeat: true
        running: alarmPopup.visible
        onTriggered: {
            // Force update of the time text
            timeText.text = new Date().toLocaleTimeString(Qt.locale(), "hh:mm:ss AP")
        }
    }
}
