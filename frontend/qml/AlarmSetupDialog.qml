import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import MyTheme 1.0
import MyServices 1.0

Dialog {
    id: alarmDialog
    
    title: editMode ? "Edit Alarm" : "New Alarm"
    modal: true
    
    // Center in parent
    x: (parent.width - width) / 2
    y: (parent.height - height) / 2
    
    // Size
    width: Math.min(parent.width - 40, 480)
    height: dialogContent.implicitHeight + footer.implicitHeight + 40
    
    // Dialog properties
    property bool editMode: false
    property string editAlarmId: ""
    property string initialName: ""
    property int initialHour: 7
    property int initialMinute: 0
    property bool initialEnabled: true
    property var initialRecurrence: ["ONCE"]
    
    // Constants
    property var daysOfWeek: ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
    property var dayNames: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    // Dialog signals
    signal finished()
    
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
    
    // Reset initial values
    function resetToDefaults() {
        nameField.text = ""
        hoursTumbler.currentIndex = 7
        minutesTumbler.currentIndex = 0
        onceOption.checked = true
        customDaysRepeater.itemAt(0).checked = false
        customDaysRepeater.itemAt(1).checked = false
        customDaysRepeater.itemAt(2).checked = false
        customDaysRepeater.itemAt(3).checked = false
        customDaysRepeater.itemAt(4).checked = false
        customDaysRepeater.itemAt(5).checked = false
        customDaysRepeater.itemAt(6).checked = false
    }
    
    // Load values from an existing alarm
    function loadAlarm(alarmId) {
        const alarm = AlarmController.getAlarm(alarmId)
        if (!alarm) return
        
        editMode = true
        editAlarmId = alarmId
        
        nameField.text = alarm.name
        hoursTumbler.currentIndex = alarm.hour
        minutesTumbler.currentIndex = alarm.minute
        
        // Set the correct recurrence option
        if (!alarm.recurrence || alarm.recurrence.length === 0 || alarm.recurrence.includes("ONCE")) {
            onceOption.checked = true
        } else if (alarm.recurrence.includes("DAILY")) {
            dailyOption.checked = true
        } else if (alarm.recurrence.includes("WEEKDAYS")) {
            weekdaysOption.checked = true
        } else if (alarm.recurrence.includes("WEEKENDS")) {
            weekendsOption.checked = true
        } else {
            customOption.checked = true
            
            // Reset all checkboxes
            for (let i = 0; i < daysOfWeek.length; i++) {
                const checkbox = customDaysRepeater.itemAt(i)
                if (checkbox) {
                    checkbox.checked = false
                }
            }
            
            // Check the days in the recurrence pattern
            for (let day of alarm.recurrence) {
                const index = daysOfWeek.indexOf(day)
                if (index >= 0) {
                    const checkbox = customDaysRepeater.itemAt(index)
                    if (checkbox) {
                        checkbox.checked = true
                    }
                }
            }
        }
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
            text: alarmDialog.title
            color: ThemeManager.text_primary_color
            font.pixelSize: 18
            font.bold: true
            anchors.centerIn: parent
        }
    }
    
    // Main dialog content
    ColumnLayout {
        id: dialogContent
        anchors.fill: parent
        anchors.margins: 16
        spacing: 20
        
        // Time selection with tumblers
        RowLayout {
            Layout.alignment: Qt.AlignHCenter
            spacing: 10
            
                Tumbler {
                    id: hoursTumbler
                    model: 24
                    currentIndex: initialHour
                    
                    delegate: Text {
                        text: modelData.toString().padStart(2, "0")
                        font.pixelSize: Tumbler.tumbler.hovered ? 24 : 22
                        opacity: 1.0 - Math.abs(Tumbler.displacement) / (Tumbler.tumbler.visibleItemCount / 2)
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        color: ThemeManager.text_primary_color
                    }
                    
                    visibleItemCount: 3
                    height: 120
                }
            
            Label {
                text: ":"
                font.pixelSize: 32
                font.bold: true
                color: ThemeManager.text_primary_color
            }
            
            Tumbler {
                id: minutesTumbler
                model: 60
                currentIndex: initialMinute
                
                delegate: Text {
                    text: modelData.toString().padStart(2, "0")
                    font.pixelSize: Tumbler.tumbler.hovered ? 24 : 22
                    opacity: 1.0 - Math.abs(Tumbler.displacement) / (Tumbler.tumbler.visibleItemCount / 2)
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    color: ThemeManager.text_primary_color
                }
                
                visibleItemCount: 3
                height: 120
            }
        }
        
        // Alarm name field
        RowLayout {
            Label {
                text: "Name:"
                color: ThemeManager.text_primary_color
            }
            
            TextField {
                id: nameField
                Layout.fillWidth: true
                placeholderText: "Alarm name"
                text: initialName
                color: ThemeManager.text_primary_color
                
                background: Rectangle {
                    radius: 4
                    border.color: ThemeManager.border_color
                    border.width: 1
                    color: ThemeManager.input_background_color
                }
            }
        }
        
        // Recurrence options
        GroupBox {
            title: "Repeat"
            Layout.fillWidth: true
            
            ColumnLayout {
                width: parent.width
                spacing: 5
                
                RadioButton {
                    id: onceOption
                    text: "Once"
                    checked: true
                    
                    contentItem: Text {
                        text: onceOption.text
                        font: onceOption.font
                        color: ThemeManager.text_primary_color
                        leftPadding: onceOption.indicator.width + onceOption.spacing
                        verticalAlignment: Text.AlignVCenter
                    }
                }
                
                RadioButton {
                    id: dailyOption
                    text: "Daily"
                    
                    contentItem: Text {
                        text: dailyOption.text
                        font: dailyOption.font
                        color: ThemeManager.text_primary_color
                        leftPadding: dailyOption.indicator.width + dailyOption.spacing
                        verticalAlignment: Text.AlignVCenter
                    }
                }
                
                RadioButton {
                    id: weekdaysOption
                    text: "Weekdays (Mon-Fri)"
                    
                    contentItem: Text {
                        text: weekdaysOption.text
                        font: weekdaysOption.font
                        color: ThemeManager.text_primary_color
                        leftPadding: weekdaysOption.indicator.width + weekdaysOption.spacing
                        verticalAlignment: Text.AlignVCenter
                    }
                }
                
                RadioButton {
                    id: weekendsOption
                    text: "Weekends (Sat-Sun)"
                    
                    contentItem: Text {
                        text: weekendsOption.text
                        font: weekendsOption.font
                        color: ThemeManager.text_primary_color
                        leftPadding: weekendsOption.indicator.width + weekendsOption.spacing
                        verticalAlignment: Text.AlignVCenter
                    }
                }
                
                RadioButton {
                    id: customOption
                    text: "Custom"
                    
                    contentItem: Text {
                        text: customOption.text
                        font: customOption.font
                        color: ThemeManager.text_primary_color
                        leftPadding: customOption.indicator.width + customOption.spacing
                        verticalAlignment: Text.AlignVCenter
                    }
                }
                
                // Custom days selection
                GridLayout {
                    columns: 4
                    visible: customOption.checked
                    Layout.fillWidth: true
                    Layout.topMargin: 10
                    
                    Repeater {
                        id: customDaysRepeater
                        model: dayNames
                        
                        delegate: CheckBox {
                            id: dayCheckbox
                            text: modelData
                            Layout.fillWidth: true
                            
                            property string day: daysOfWeek[index]
                            
                            contentItem: Text {
                                text: dayCheckbox.text
                                font: dayCheckbox.font
                                color: ThemeManager.text_primary_color
                                leftPadding: dayCheckbox.indicator.width + dayCheckbox.spacing
                                verticalAlignment: Text.AlignVCenter
                            }
                        }
                    }
                }
            }
        }
    }
    
    // Dialog buttons
    footer: DialogButtonBox {
        id: footer
        standardButtons: Dialog.Save | Dialog.Cancel
        alignment: Qt.AlignRight
        spacing: 10
        padding: 10
        
        background: Rectangle {
            color: "transparent"
        }
        
        onAccepted: {
            // Get recurrence pattern based on selection
            let recurrence = []
            if (onceOption.checked) {
                recurrence = ["ONCE"]
            } else if (dailyOption.checked) {
                recurrence = ["DAILY"]
            } else if (weekdaysOption.checked) {
                recurrence = ["WEEKDAYS"]
            } else if (weekendsOption.checked) {
                recurrence = ["WEEKENDS"]
            } else if (customOption.checked) {
                // Collect selected days
                for (let i = 0; i < daysOfWeek.length; i++) {
                    const checkbox = customDaysRepeater.itemAt(i)
                    if (checkbox && checkbox.checked) {
                        recurrence.push(checkbox.day)
                    }
                }
                
                // If no days selected, default to once
                if (recurrence.length === 0) {
                    recurrence = ["ONCE"]
                }
            }
            
            // Add or update alarm
            if (editMode) {
                AlarmController.updateAlarm(
                    editAlarmId,
                    nameField.text || "Alarm",
                    hoursTumbler.currentIndex,
                    minutesTumbler.currentIndex,
                    true,
                    recurrence
                )
            } else {
                AlarmController.addAlarm(
                    nameField.text || "Alarm",
                    hoursTumbler.currentIndex,
                    minutesTumbler.currentIndex,
                    true,
                    recurrence
                )
            }
            
            finished()
            resetToDefaults()
            close()
        }
        
        onRejected: {
            finished()
            resetToDefaults()
            close()
        }
        
        // Style dialog buttons
        delegate: Button {
            id: dialogButton
            
            background: Rectangle {
                radius: 4
                color: dialogButton.down
                    ? ThemeManager.button_pressed_color
                    : (dialogButton.hovered
                        ? ThemeManager.button_hover_color
                        : ThemeManager.button_color)
            }
            
            contentItem: Text {
                text: dialogButton.text
                color: ThemeManager.button_text_color
                font.pixelSize: 14
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
        }
    }
}
