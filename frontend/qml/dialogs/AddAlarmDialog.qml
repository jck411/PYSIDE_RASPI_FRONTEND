import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import MyTheme 1.0
import MyServices 1.0

Dialog {
    id: addAlarmDialog
    modal: true
    title: "Add Alarm"
    width: Math.min(parent.width * 0.9, 500)
    height: Math.min(parent.height * 0.9, 600)
    
    // Center in parent
    x: (parent.width - width) / 2
    y: (parent.height - height) / 2
    
    // Use Dialog's standard buttons
    standardButtons: Dialog.Save | Dialog.Cancel
    
    property var selectedDays: [] // Holds the indices of selected days (0=Mon, 6=Sun)
    
    // Function to reset fields when opened
    function reset() {
        // Default to current time + 5 minutes, rounded to nearest 5
        var now = new Date()
        var hour = now.getHours()
        var minute = Math.ceil((now.getMinutes() + 5) / 5) * 5
        
        // Handle minute overflow
        if (minute >= 60) {
            minute = minute - 60
            hour = (hour + 1) % 24
        }
        
        // Set tumbler positions
        hourTumbler.currentIndex = hour
        minuteTumbler.currentIndex = Math.floor(minute / 5)
        
        labelField.text = ""
        
        // Reset day selection
        for (var i = 0; i < dayRepeater.count; i++) {
            dayRepeater.itemAt(i).checked = false
        }
        
        // Common patterns
        weekdaysButton.highlighted = false
        weekendButton.highlighted = false
        everydayButton.highlighted = false
        
        updateSelectedDays()
    }
    
    // Function to update the selectedDays property based on checkboxes
    function updateSelectedDays() {
        var days = []
        for (var i = 0; i < dayRepeater.count; i++) {
            if (dayRepeater.itemAt(i).checked) {
                days.push(i)
            }
        }
        selectedDays = days
    }
    
    // Update selection based on pattern buttons
    function updateDayPattern(pattern) {
        for (var i = 0; i < dayRepeater.count; i++) {
            var btn = dayRepeater.itemAt(i)
            if (pattern === "weekdays") {
                btn.checked = (i >= 0 && i <= 4)
                weekdaysButton.highlighted = true
                weekendButton.highlighted = false
                everydayButton.highlighted = false
            } else if (pattern === "weekend") {
                btn.checked = (i === 5 || i === 6)
                weekdaysButton.highlighted = false
                weekendButton.highlighted = true
                everydayButton.highlighted = false
            } else if (pattern === "everyday") {
                btn.checked = true
                weekdaysButton.highlighted = false
                weekendButton.highlighted = false
                everydayButton.highlighted = true
            }
        }
        updateSelectedDays()
    }
    
    // Reset fields when the dialog becomes visible
    onVisibleChanged: {
        if (visible) {
            reset()
        }
    }
    
    // Background using theme colors
    background: Rectangle {
        color: ThemeManager.background_color
        radius: 10
    }
    
    // Style the header if needed
    header: Rectangle {
        color: ThemeManager.background_secondary_color
        height: headerText.height + 20
        
        Text {
            id: headerText
            text: addAlarmDialog.title
            font.pixelSize: 18
            font.bold: true
            color: ThemeManager.text_primary_color
            anchors.centerIn: parent
        }
    }
    
    // Style the footer (buttons)
    footer: DialogButtonBox {
        standardButtons: addAlarmDialog.standardButtons
        background: Rectangle {
            color: ThemeManager.background_secondary_color
        }
        
        // Style the buttons
        delegate: Button {
            id: dialogButton
            
            contentItem: Text {
                text: dialogButton.text
                font: dialogButton.font
                color: dialogButton.pressed ? ThemeManager.accent_text_color : ThemeManager.text_primary_color
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
            
            background: Rectangle {
                color: {
                    if (dialogButton.DialogButtonBox.buttonRole === DialogButtonBox.AcceptRole) {
                        return dialogButton.pressed ? Qt.darker(ThemeManager.accent_color, 1.2) : ThemeManager.accent_color
                    } else {
                        return dialogButton.pressed ? ThemeManager.background_secondary_color : ThemeManager.background_input_color
                    }
                }
                border.color: ThemeManager.border_color
                border.width: 1
                radius: 4
            }
        }
    }
    
    contentItem: Item {
        anchors.fill: parent
        
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 20
            spacing: 30
            
            // Time selection with Tumblers
            Rectangle {
                Layout.alignment: Qt.AlignHCenter
                Layout.preferredWidth: parent.width * 0.8
                Layout.preferredHeight: 150
                color: ThemeManager.background_secondary_color
                radius: 10
                
                RowLayout {
                    anchors.centerIn: parent
                    spacing: 10
                    
                    // Hour tumbler
                    Tumbler {
                        id: hourTumbler
                        model: 24
                        visibleItemCount: 3
                        height: 120
                        width: 80
                        
                        delegate: Text {
                            text: String(modelData).padStart(2, '0')
                            color: ThemeManager.text_primary_color
                            font.pixelSize: hourTumbler.currentIndex === index ? 30 : 20
                            font.bold: hourTumbler.currentIndex === index
                            opacity: 1.0 - Math.abs(Tumbler.displacement) / (hourTumbler.visibleItemCount / 2)
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                        
                        background: Item {
                            // Center highlight rectangle
                            Rectangle {
                                anchors.centerIn: parent
                                width: parent.width
                                height: hourTumbler.height / hourTumbler.visibleItemCount
                                color: Qt.alpha(ThemeManager.accent_color, 0.1)
                            }
                        }
                    }
                    
                    // Separator
                    Text {
                        text: ":"
                        font.pixelSize: 40
                        font.bold: true
                        color: ThemeManager.text_primary_color
                    }
                    
                    // Minute tumbler (5-minute increments)
                    Tumbler {
                        id: minuteTumbler
                        model: 12 // 0, 5, 10, ..., 55
                        visibleItemCount: 3
                        height: 120
                        width: 80
                        
                        delegate: Text {
                            text: String(modelData * 5).padStart(2, '0')
                            color: ThemeManager.text_primary_color
                            font.pixelSize: minuteTumbler.currentIndex === index ? 30 : 20
                            font.bold: minuteTumbler.currentIndex === index
                            opacity: 1.0 - Math.abs(Tumbler.displacement) / (minuteTumbler.visibleItemCount / 2)
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                        
                        background: Item {
                            // Center highlight rectangle
                            Rectangle {
                                anchors.centerIn: parent
                                width: parent.width
                                height: minuteTumbler.height / minuteTumbler.visibleItemCount
                                color: Qt.alpha(ThemeManager.accent_color, 0.1)
                            }
                        }
                    }
                    
                    // Fine-tuning for minutes
                    ColumnLayout {
                        spacing: 5
                        
                        // Minute up button
                        Button {
                            Layout.preferredWidth: 40
                            Layout.preferredHeight: 40
                            text: "+"
                            font.pixelSize: 16
                            
                            contentItem: Text {
                                text: parent.text
                                font: parent.font
                                color: parent.pressed ? ThemeManager.accent_text_color : ThemeManager.text_primary_color
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                            
                            background: Rectangle {
                                radius: width / 2
                                color: parent.pressed ? ThemeManager.accent_color : ThemeManager.background_input_color
                                border.color: ThemeManager.border_color
                                border.width: 1
                            }
                            
                            onClicked: {
                                var currentMinute = minuteTumbler.currentIndex * 5
                                currentMinute = (currentMinute + 1) % 60
                                minuteTumbler.currentIndex = Math.floor(currentMinute / 5)
                            }
                        }
                        
                        // Current exact minute
                        Text {
                            Layout.alignment: Qt.AlignHCenter
                            text: {
                                var base = minuteTumbler.currentIndex * 5
                                return String(base).padStart(2, '0')
                            }
                            color: ThemeManager.text_primary_color
                            font.pixelSize: 16
                        }
                        
                        // Minute down button
                        Button {
                            Layout.preferredWidth: 40
                            Layout.preferredHeight: 40
                            text: "−" // Unicode minus sign
                            font.pixelSize: 16
                            
                            contentItem: Text {
                                text: parent.text
                                font: parent.font
                                color: parent.pressed ? ThemeManager.accent_text_color : ThemeManager.text_primary_color
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                            
                            background: Rectangle {
                                radius: width / 2
                                color: parent.pressed ? ThemeManager.accent_color : ThemeManager.background_input_color
                                border.color: ThemeManager.border_color
                                border.width: 1
                            }
                            
                            onClicked: {
                                var currentMinute = minuteTumbler.currentIndex * 5
                                currentMinute = (currentMinute - 1 + 60) % 60
                                minuteTumbler.currentIndex = Math.floor(currentMinute / 5)
                            }
                        }
                    }
                }
            }
            
            // Label
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 5
                
                Label {
                    text: "Alarm Label"
                    font.pixelSize: 16
                    color: ThemeManager.text_primary_color
                }
                
                TextField {
                    id: labelField
                    Layout.fillWidth: true
                    placeholderText: "Enter alarm label (optional)"
                    font.pixelSize: 16
                    color: ThemeManager.text_primary_color
                    
                    background: Rectangle {
                        radius: 5
                        color: ThemeManager.background_input_color
                        border.color: labelField.focus ? ThemeManager.accent_color : ThemeManager.border_color
                        border.width: 1
                    }
                }
            }
            
            // Day selection
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 15
                
                Label {
                    text: "Repeat on:"
                    font.pixelSize: 16
                    color: ThemeManager.text_primary_color
                }
                
                // Convenient pattern buttons
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 10
                    
                    Button {
                        id: weekdaysButton
                        text: "Weekdays"
                        Layout.fillWidth: true
                        onClicked: updateDayPattern("weekdays")
                        
                        contentItem: Text {
                            text: parent.text
                            font: parent.font
                            color: parent.pressed || parent.highlighted ? 
                                ThemeManager.accent_text_color : ThemeManager.text_primary_color
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                        
                        background: Rectangle {
                            radius: 4
                            color: parent.pressed || parent.highlighted ? 
                                ThemeManager.accent_color : ThemeManager.background_secondary_color
                            border.color: ThemeManager.border_color
                            border.width: 1
                        }
                    }
                    
                    Button {
                        id: weekendButton
                        text: "Weekend"
                        Layout.fillWidth: true
                        onClicked: updateDayPattern("weekend")
                        
                        contentItem: Text {
                            text: parent.text
                            font: parent.font
                            color: parent.pressed || parent.highlighted ? 
                                ThemeManager.accent_text_color : ThemeManager.text_primary_color
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                        
                        background: Rectangle {
                            radius: 4
                            color: parent.pressed || parent.highlighted ? 
                                ThemeManager.accent_color : ThemeManager.background_secondary_color
                            border.color: ThemeManager.border_color
                            border.width: 1
                        }
                    }
                    
                    Button {
                        id: everydayButton
                        text: "Every Day"
                        Layout.fillWidth: true
                        onClicked: updateDayPattern("everyday")
                        
                        contentItem: Text {
                            text: parent.text
                            font: parent.font
                            color: parent.pressed || parent.highlighted ? 
                                ThemeManager.accent_text_color : ThemeManager.text_primary_color
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                        
                        background: Rectangle {
                            radius: 4
                            color: parent.pressed || parent.highlighted ? 
                                ThemeManager.accent_color : ThemeManager.background_secondary_color
                            border.color: ThemeManager.border_color
                            border.width: 1
                        }
                    }
                }
                
                // Individual day toggles - modern circular buttons
                GridLayout {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 80
                    columns: 7
                    rowSpacing: 10
                    columnSpacing: 10
                    
                    property var dayLabels: ["M", "T", "W", "T", "F", "S", "S"]
                    
                    Repeater {
                        id: dayRepeater
                        model: 7
                        
                        // Circular day toggle button
                        Rectangle {
                            id: dayToggle
                            property bool checked: false
                            property string dayText: GridLayout.dayLabels[index]
                            
                            Layout.preferredWidth: 50
                            Layout.preferredHeight: 50
                            Layout.alignment: Qt.AlignHCenter
                            radius: width / 2
                            
                            color: checked ? ThemeManager.accent_color : "transparent"
                            border.color: checked ? "transparent" : ThemeManager.border_color
                            border.width: 1
                            
                            // Weekend days have a special color when not selected
                            Rectangle {
                                visible: !parent.checked && (index === 5 || index === 6)
                                anchors.fill: parent
                                radius: width / 2
                                color: Qt.alpha(ThemeManager.accent_color, 0.2)
                                z: -1
                            }
                            
                            Text {
                                anchors.centerIn: parent
                                text: parent.dayText
                                color: parent.checked ? ThemeManager.accent_text_color : ThemeManager.text_primary_color
                                font.pixelSize: 20
                                font.bold: true
                            }
                            
                            MouseArea {
                                anchors.fill: parent
                                onClicked: {
                                    parent.checked = !parent.checked
                                    updateSelectedDays()
                                    
                                    // Reset highlights on pattern buttons
                                    weekdaysButton.highlighted = false
                                    weekendButton.highlighted = false
                                    everydayButton.highlighted = false
                                }
                            }
                        }
                    }
                }
            }
            
            // Summary text
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 60
                color: ThemeManager.background_secondary_color
                radius: 5
                visible: selectedDays.length > 0
                
                Text {
                    anchors.centerIn: parent
                    width: parent.width - 20
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.WordWrap
                    color: ThemeManager.text_secondary_color
                    font.pixelSize: 14
                    
                    text: {
                        if (selectedDays.length === 0) return ""
                        if (selectedDays.length === 7) return "Alarm will repeat every day"
                        if (selectedDays.length === 5 && 
                            selectedDays.indexOf(5) === -1 && 
                            selectedDays.indexOf(6) === -1) 
                                return "Alarm will repeat on weekdays"
                        if (selectedDays.length === 2 && 
                            selectedDays.indexOf(5) !== -1 && 
                            selectedDays.indexOf(6) !== -1) 
                                return "Alarm will repeat on weekends"
                        
                        var dayNames = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                        var days = []
                        for (var i = 0; i < selectedDays.length; i++) {
                            days.push(dayNames[selectedDays[i]])
                        }
                        return "Alarm will repeat on " + days.join(", ")
                    }
                }
            }
            
            // Spacer
            Item {
                Layout.fillHeight: true
            }
        }
    }
    
    // Handle OK/Save button click
    onAccepted: {
        var hour = hourTumbler.currentIndex
        var minute = minuteTumbler.currentIndex * 5
        
        console.log("Adding alarm:", hour + ":" + minute, 
                    "Label:", labelField.text, "Days:", selectedDays)
        
        // Call the controller to add the alarm
        AlarmController.add_alarm(
            hour,
            minute,
            labelField.text,
            selectedDays,
            true // Default to enabled
        )
    }
} 