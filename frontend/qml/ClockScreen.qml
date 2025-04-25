import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import MyTheme 1.0
import MyServices 1.0

BaseScreen {
    id: clockScreen
    
    // Set the controls file for this screen
    screenControls: "ClockControls.qml"
    title: "Clock"
    
    // Properties for alarm handling
    property var alarmListModel: []
    
    // Function to refresh alarm list
    function refreshAlarmList() {
        alarmListModel = AlarmController.getAlarms()
    }
    
    // Function to format alarm time
    function formatAlarmTime(hour, minute) {
        const date = new Date()
        date.setHours(hour)
        date.setMinutes(minute)
        date.setSeconds(0)
        return date.toLocaleTimeString(Qt.locale(), "hh:mm AP")
    }
    
    // Handle alarm triggered signal
    Connections {
        target: AlarmController
        
        function onAlarmTriggered(alarmId, alarmName) {
            const alarm = AlarmController.getAlarm(alarmId)
            if (alarm) {
                // Show notification dialog
                openNotificationDialog(alarmId, alarmName)
                
                // TODO: Play sound or implement other notification mechanisms
            }
        }
        
        function onAlarmsChanged() {
            refreshAlarmList()
        }
    }
    
    // Main content area - Clock View
    Rectangle {
        anchors.fill: parent
        color: "transparent"
        
        ColumnLayout {
            anchors.centerIn: parent
            spacing: 20

            Text {
                id: timeText
                Layout.alignment: Qt.AlignCenter
                color: ThemeManager.text_primary_color
                font.pixelSize: 100
                font.bold: true
                text: "00:00:00"
            }

            Text {
                id: dateText
                Layout.alignment: Qt.AlignCenter
                color: ThemeManager.text_primary_color
                font.pixelSize: 36
                text: "January 1, 2023"
            }
            
            // Additional date/time info
            Text {
                id: dayText
                Layout.alignment: Qt.AlignCenter
                color: ThemeManager.text_secondary_color
                font.pixelSize: 24
                text: "Monday"
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
                dayText.text = date.toLocaleDateString(Qt.locale(), "dddd")
            }
        }
    }
    
    // Define the notification dialog component
    Component {
        id: notificationDialogComponent
        
        Dialog {
            id: notificationDialog
            
            title: "Alarm"
            modal: true
            closePolicy: Popup.NoAutoClose // Prevent closing by clicking outside or pressing Escape
            
            // Center in parent
            x: (parent.width - width) / 2
            y: (parent.height - height) / 2
            
            // Size
            width: Math.min(parent.width - 40, 400)
            height: 250
            
            // Dim the background with a semi-transparent overlay
            Overlay.modal: Rectangle {
                color: Qt.rgba(0, 0, 0, 0.6) // Semi-transparent black
            }
            
            // Dialog properties
            property string alarmId: ""
            property string alarmName: "Alarm"
            property var alarmTime: new Date()
            
            // Dialog signals
            signal dismissed()
            signal snoozed()
            
            // Apply theme
            palette.window: ThemeManager.dialog_background_color
            palette.windowText: ThemeManager.text_primary_color
            palette.button: ThemeManager.button_color
            palette.buttonText: ThemeManager.button_text_color
            
            background: Rectangle {
                color: ThemeManager.dialog_background_color
                radius: 10
                border.color: ThemeManager.border_color
                border.width: 1
            }
            
            header: Rectangle {
                color: ThemeManager.dialog_header_color
                height: 50
                radius: 10
                
                // Only make the top corners rounded
                Rectangle {
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.bottom: parent.bottom
                    height: parent.height / 2
                    color: parent.color
                }
                
                Label {
                    text: notificationDialog.title
                    color: ThemeManager.text_primary_color
                    font.pixelSize: 18
                    font.bold: true
                    anchors.centerIn: parent
                }
            }
            
            // Content area
            ColumnLayout {
                anchors.fill: parent
                spacing: 20
                
                Item { Layout.fillHeight: true }
                
                // Current time
                Text {
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
            
            // Dialog buttons
            footer: RowLayout {
                spacing: 10
                Layout.fillWidth: true
                
                Button {
                    text: "Snooze (5 min)"
                    Layout.preferredWidth: 150
                    Layout.alignment: Qt.AlignHCenter
                    
                    contentItem: Text {
                        text: parent.text
                        font: parent.font
                        color: ThemeManager.accent_text_color
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    
                    background: Rectangle {
                        radius: 8
                        color: ThemeManager.accent_color
                    }
                    
                    onClicked: {
                        snoozed()
                        close()
                    }
                }
                
                Button {
                    text: "Dismiss"
                    Layout.preferredWidth: 120
                    Layout.alignment: Qt.AlignHCenter
                    
                    contentItem: Text {
                        text: parent.text
                        font: parent.font
                        color: ThemeManager.accent_text_color
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    
                    background: Rectangle {
                        radius: 8
                        color: ThemeManager.accent_color
                    }
                    
                    onClicked: {
                        dismissed()
                        close()
                    }
                }
            }
            
            // Handle signals
            onSnoozed: {
                // Create a new one-time alarm for 5 minutes from now
                const alarmData = AlarmController.getAlarm(alarmId)
                if (alarmData) {
                    const now = new Date()
                    const snoozeHour = now.getHours()
                    const snoozeMinute = now.getMinutes() + 5
                    
                    AlarmController.addAlarm(
                        alarmData.name + " (Snoozed)",
                        snoozeHour,
                        snoozeMinute,
                        true,
                        ["ONCE"]
                    )
                }
            }
            
            // Update time every second
            Timer {
                interval: 1000
                repeat: true
                running: notificationDialog.visible
                onTriggered: {
                    // Force update of the time text by toggling a property
                    notificationDialog.alarmTime = new Date()
                }
            }
        }
    }
    
    // Create the notification dialog when needed
    property var notificationDialog: null
    
    function openNotificationDialog(alarmId, alarmName) {
        if (!notificationDialog) {
            notificationDialog = notificationDialogComponent.createObject(Overlay.overlay)
        }
        
        notificationDialog.alarmId = alarmId
        notificationDialog.alarmName = alarmName
        notificationDialog.open()
    }
    
    // Initialize the alarm list when component completes
    Component.onCompleted: {
        refreshAlarmList()
    }
}
