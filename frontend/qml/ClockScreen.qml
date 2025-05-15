import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import MyTheme 1.0
import MyServices 1.0

BaseScreen {
    id: clockScreen
    property string filename: "ClockScreen.qml"
    
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
                
                // Play alarm sound
                if (typeof AudioManager !== 'undefined' && typeof AudioManager.play_alarm_sound === 'function') {
                    AudioManager.play_alarm_sound()
                }
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
            width: Math.min(parent.width * 0.85, 420)
            height: 270
            
            // Dim the background with a semi-transparent overlay
            Overlay.modal: Rectangle {
                color: Qt.rgba(0, 0, 0, 0.7)
            }
            
            // Dialog properties
            property string alarmId: ""
            property string alarmName: "Alarm"
            
            // Apply theme
            palette.window: ThemeManager.dialog_background_color
            palette.windowText: ThemeManager.text_primary_color
            palette.button: ThemeManager.button_color
            palette.buttonText: ThemeManager.button_text_color
            
            background: Rectangle {
                color: ThemeManager.dialog_background_color
                radius: 12
                border.color: ThemeManager.border_color
                border.width: 1
            }
            
            header: Rectangle {
                color: ThemeManager.dialog_header_color
                height: 55
                radius: 12
                
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
                    font.pixelSize: 20
                    font.bold: true
                    anchors.centerIn: parent
                }
            }
            
            // Content area
            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 16
                spacing: 24
                
                Item { Layout.fillHeight: true }
                
                // Current time
                Text {
                    text: {
                        const now = new Date()
                        return now.toLocaleTimeString(Qt.locale(), "hh:mm:ss AP")
                    }
                    font.pixelSize: 32
                    font.bold: true
                    color: ThemeManager.text_primary_color
                    Layout.alignment: Qt.AlignHCenter
                }
                
                // Alarm name
                Text {
                    text: alarmName
                    font.pixelSize: 22
                    color: ThemeManager.text_primary_color
                    horizontalAlignment: Text.AlignHCenter
                    Layout.fillWidth: true
                    Layout.alignment: Qt.AlignHCenter
                    wrapMode: Text.WordWrap
                }
                
                Item { Layout.fillHeight: true }
            }
            
            // Dialog buttons
            footer: Rectangle {
                height: 80
                color: "transparent"
                
                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 12
                    spacing: 15
                    
                    Button {
                        text: "Snooze (10 min)"
                        Layout.fillWidth: true
                        Layout.preferredHeight: 46
                        
                        contentItem: Text {
                            text: parent.text
                            font.pixelSize: 16
                            font.bold: true
                            color: ThemeManager.accent_text_color
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                        
                        background: Rectangle {
                            radius: 10
                            color: ThemeManager.accent_color
                        }
                        
                        onClicked: {
                            // Create a new one-time alarm for 10 minutes from now
                            const alarmData = AlarmController.getAlarm(alarmId)
                            if (alarmData) {
                                const now = new Date()
                                var snoozeHour = now.getHours()
                                var snoozeMinute = now.getMinutes() + 10
                                
                                // Handle minute overflow
                                if (snoozeMinute >= 60) {
                                    snoozeMinute = snoozeMinute - 60
                                    snoozeHour = (snoozeHour + 1) % 24
                                }
                                
                                AlarmController.addAlarm(
                                    alarmData.name + " (Snoozed)",
                                    snoozeHour,
                                    snoozeMinute,
                                    true,
                                    ["ONCE"]
                                )
                            }
                            close()
                        }
                    }
                    
                    Button {
                        text: "Dismiss"
                        Layout.fillWidth: true
                        Layout.preferredHeight: 46
                        
                        contentItem: Text {
                            text: parent.text
                            font.pixelSize: 16
                            font.bold: true
                            color: ThemeManager.accent_text_color
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                        
                        background: Rectangle {
                            radius: 10
                            color: ThemeManager.accent_color
                        }
                        
                        onClicked: {
                            close()
                        }
                    }
                }
            }
            
            // Update time every second
            Timer {
                interval: 1000
                repeat: true
                running: notificationDialog.visible
                onTriggered: {
                    // Force update of the time display
                    notificationDialog.update()
                }
            }
            
            // Function to force update
            function update() {
                // This is a dummy function to force a redraw of the time display
                visible = visible
            }
        }
    }
    
    // Create the notification dialog when needed
    property var notificationDialog: null
    
    function openNotificationDialog(alarmId, alarmName) {
        if (!notificationDialog) {
            notificationDialog = notificationDialogComponent.createObject(Overlay.overlay)
            
            // Connect to when the dialog is closed
            notificationDialog.closed.connect(function() {
                if (typeof AudioManager !== 'undefined' && typeof AudioManager.stop_playback === 'function') {
                    AudioManager.stop_playback()
                }
            })
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
