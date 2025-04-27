import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import MyTheme 1.0
import MyServices 1.0
import "components"

BaseScreen {
    id: alarmScreen
    
    // Set the controls file for this screen
    screenControls: "AlarmControls.qml"
    title: "Alarms"
    
    property bool isEditMode: false
    property var currentEditingAlarm: null
    property var selectedDays: []
    
    // Function to format time (HH:MM)
    function formatTime(hour, minute) {
        // Simple alternative to sprintf for padding numbers
        var hourStr = hour < 10 ? "0" + hour : "" + hour;
        var minuteStr = minute < 10 ? "0" + minute : "" + minute;
        return hourStr + ":" + minuteStr;
    }
    
    // Function to format days of the week
    function formatDays(daysList) {
        // Handle null, undefined or empty arrays
        if (!daysList || daysList.length === 0) return "Once";
        
        // Make sure we're working with a proper array
        let days = Array.isArray(daysList) ? daysList : [];
        
        // Handle string values like "ONCE", "DAILY", "WEEKDAYS", "WEEKENDS"
        if (days.includes("ONCE")) return "Once";
        if (days.includes("DAILY")) return "Every Day";
        if (days.includes("WEEKDAYS")) return "Weekdays";
        if (days.includes("WEEKENDS")) return "Weekends";
        
        // Special cases
        if (days.length === 7) return "Every Day";
        
        // Safe includes check with type conversion
        function safeIncludes(arr, val) {
            return arr.some(item => {
                if (typeof item === 'string' && typeof val === 'number') {
                    // Handle string day names
                    const dayMap = {"MON": 0, "TUE": 1, "WED": 2, "THU": 3, "FRI": 4, "SAT": 5, "SUN": 6};
                    return dayMap[item] === val;
                } else if (typeof item === 'number' && typeof val === 'string') {
                    // Handle numeric day indices
                    const dayMap = {0: "MON", 1: "TUE", 2: "WED", 3: "THU", 4: "FRI", 5: "SAT", 6: "SUN"};
                    return item === dayMap.indexOf(val);
                }
                return Number(item) === Number(val);
            });
        }
        
        // Check for weekdays (0-4) or weekend (5-6) patterns
        if (days.length === 5 && 
            safeIncludes(days, 0) && 
            safeIncludes(days, 1) && 
            safeIncludes(days, 2) && 
            safeIncludes(days, 3) && 
            safeIncludes(days, 4)) {
            return "Weekdays";
        }
        
        if (days.length === 2 && 
            safeIncludes(days, 5) && 
            safeIncludes(days, 6)) {
            return "Weekends";
        }
        
        // For any other pattern, list the days
        const dayNames = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
        const dayMap = {"MON": 0, "TUE": 1, "WED": 2, "THU": 3, "FRI": 4, "SAT": 5, "SUN": 6};
        
        // Convert to numbers, sort, and map to names
        const convertedDays = days.map(d => {
            if (typeof d === 'string' && dayMap[d] !== undefined) {
                return dayMap[d];
            }
            return Number(d);
        })
        .filter(d => !isNaN(d) && d >= 0 && d <= 6)
        .sort((a, b) => a - b);
        
        return convertedDays.map(dayIndex => dayNames[dayIndex] || "").filter(n => n).join(", ") || "Once";
    }
    
    // Update selected days property based on checkboxes
    function updateSelectedDays() {
        var days = []
        for (var i = 0; i < dayRepeater.count; i++) {
            if (dayRepeater.itemAt(i).checked) {
                days.push(i)
            }
        }
        selectedDays = days
    }
    
    // Update day checkboxes based on a pattern
    function updateDayPattern(pattern) {
        for (var i = 0; i < dayRepeater.count; i++) {
            var btn = dayRepeater.itemAt(i)
            if (pattern === "weekdays") {
                btn.checked = (i >= 0 && i <= 4)
            } else if (pattern === "weekend") {
                btn.checked = (i === 5 || i === 6)
            } else if (pattern === "everyday") {
                btn.checked = true
            }
        }
        updateSelectedDays()
    }
    
    // Function to start editing an alarm
    function editAlarm(alarm) {
        // Set edit mode
        isEditMode = true
        currentEditingAlarm = alarm
        
        // Set the edit fields
        hourTumbler.currentIndex = alarm.hour
        minuteTumbler.currentIndex = alarm.minute
        labelField.text = alarm.label || ""
        
        // Update day selections
        for (var i = 0; i < dayRepeater.count; i++) {
            dayRepeater.itemAt(i).checked = alarm.days_of_week.includes(i)
        }
        updateSelectedDays()
        
        // Show edit panel
        editPanel.visible = true
    }
    
    // Function to start adding a new alarm
    function startNewAlarm() {
        // Reset edit mode
        isEditMode = false
        currentEditingAlarm = null
        
        // Default to current time + 5 minutes, rounded to nearest 5
        var now = new Date()
        var hour = now.getHours()
        var minute = now.getMinutes() + 1
        if (minute >= 60) {
            minute = 0
            hour = (hour + 1) % 24
        }
        hourTumbler.currentIndex = hour
        minuteTumbler.currentIndex = minute
        labelField.text = ""
        
        // Reset day selection
        for (var i = 0; i < dayRepeater.count; i++) {
            dayRepeater.itemAt(i).checked = false
        }
        updateSelectedDays()
        
        // Show edit panel
        editPanel.visible = true
    }
    
    // Save the alarm (add or update)
    function saveAlarm() {
        var hour = hourTumbler.currentIndex
        var minute = minuteTumbler.currentIndex
        var label = labelField.text.trim() || "Alarm"
        var days = selectedDays.length > 0 ? selectedDays : []
        
        console.log("Adding alarm:", hour + ":" + minute, "Label:", label, "Days:", days)
        
        if (isEditMode && currentEditingAlarm) {
            // Update existing alarm
            AlarmController.updateAlarm(
                currentEditingAlarm.id,
                label,
                hour,
                minute,
                true, // Enabled
                days
            )
        } else {
            // Add new alarm - adjust parameters to match the controller
            // Check what signature is expected
            if (typeof AlarmController.addAlarm === 'function') {
                if (AlarmController.addAlarm.length === 5) {
                    AlarmController.addAlarm(
                        hour,
                        minute,
                        label,
                        days,
                        true // Enabled
                    )
                } else {
                    // Try with label first, which seems to be what the logic controller expects
                    AlarmController.addAlarm(
                        label,
                        hour,
                        minute,
                        true, // Enabled
                        days
                    )
                }
            }
        }
        
        // Hide edit panel
        editPanel.visible = false
    }
    
    // Cancel editing
    function cancelEditing() {
        editPanel.visible = false
    }

    // Handle alarm trigger notification and other alarm controller signals
    Connections {
        target: AlarmController
        function onAlarmTriggered(alarmId, alarmLabel) {
            alarmNotification.alarmId = alarmId
            alarmNotification.alarmName = alarmLabel || "Alarm"
            AudioManager.play_alarm_sound()
            alarmNotification.open()
        }
        
        function onAlarmsChanged() {
            console.log("Alarms changed, refreshing model")
            
            // Force refresh of the ListView model using alarmModel
            alarmListView.model = null
            alarmListView.model = AlarmController.alarmModel()
        }
    }
    
    // Main layout
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20 // Add padding to all edges
        spacing: 0
        
        // Alarm List 
        ListView {
            id: alarmListView
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.margins: 10
            clip: true
            spacing: 15
            
            // Use the QAbstractListModel
            Component.onCompleted: {
                console.log("Setting model to AlarmController.alarmModel()");
                model = AlarmController.alarmModel();
            }
            
            delegate: Rectangle {
                width: alarmListView.width
                height: 80
                color: ThemeManager.background_secondary_color
                radius: 10
                
                // Direct access to model data
                property string alarmId: model.id
                property string alarmName: model.name || "Alarm"
                property int alarmHour: model.hour
                property int alarmMinute: model.minute
                property bool alarmEnabled: model.enabled
                property var alarmRecurrence: model.recurrence
                
                Component.onCompleted: {
                    console.log("Created delegate for item:", JSON.stringify({
                        id: alarmId,
                        name: alarmName,
                        hour: alarmHour,
                        minute: alarmMinute
                    }));
                }
                
                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        // Create a consistent object to pass to editAlarm
                        editAlarm({
                            id: alarmId,
                            name: alarmName,
                            hour: alarmHour,
                            minute: alarmMinute,
                            enabled: alarmEnabled,
                            days_of_week: alarmRecurrence,
                            recurrence: alarmRecurrence
                        })
                    }
                }
                
                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 20
                    anchors.rightMargin: 20
                    spacing: 20

                    // Alarm Time
                    Text {
                        text: formatTime(alarmHour, alarmMinute)
                        font.pixelSize: 28
                        font.bold: true
                        color: ThemeManager.text_primary_color
                        Layout.alignment: Qt.AlignVCenter
                    }

                    // Alarm Label and Days
                    ColumnLayout {
                        Layout.fillWidth: true
                        Layout.alignment: Qt.AlignVCenter
                        spacing: 2
                        
                        Text {
                            text: alarmName
                            font.pixelSize: 18
                            color: ThemeManager.text_primary_color
                            elide: Text.ElideRight
                            Layout.fillWidth: true
                        }
                        Text {
                            text: formatDays(alarmRecurrence)
                            font.pixelSize: 14
                            color: ThemeManager.text_secondary_color
                            Layout.fillWidth: true
                        }
                    }

                    // Enable Switch
                    Switch {
                        checked: alarmEnabled
                        Layout.alignment: Qt.AlignVCenter
                        onClicked: AlarmController.setAlarmEnabled(alarmId, checked)
                    }

                    // Delete Button
                    Button {
                        text: "×" // Unicode multiplication sign as a cleaner X
                        font.pixelSize: 20
                        font.bold: true
                        Layout.preferredWidth: 40
                        Layout.preferredHeight: 40
                        Layout.alignment: Qt.AlignVCenter
                        
                        contentItem: Text {
                            text: parent.text
                            font: parent.font
                            color: ThemeManager.accent_text_color
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                        
                        background: Rectangle {
                            color: parent.pressed ? Qt.darker(ThemeManager.danger_color, 1.2) : ThemeManager.danger_color
                            radius: width / 2
                        }
                        
                        onClicked: {
                            console.log("Delete button clicked for alarm with ID:", alarmId)
                            console.log("Full model data:", JSON.stringify({
                                id: alarmId,
                                name: alarmName,
                                hour: alarmHour,
                                minute: alarmMinute
                            }))
                            
                            // Only attempt to delete if we have a valid ID
                            if (alarmId && alarmId.length > 0) {
                                AlarmController.deleteAlarm(alarmId)
                            } else {
                                console.error("Cannot delete alarm with invalid ID:", alarmId)
                            }
                        }
                    }
                }
            }
            
            // Footer component - "Add new alarm" button
            footer: Column {
                width: alarmListView.width
                spacing: 10
                
                // Remove Rectangle background, use only MouseArea and RowLayout
                MouseArea {
                    width: parent.width
                    height: 80
                    onClicked: startNewAlarm()
                    
                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 20
                        anchors.rightMargin: 20
                        spacing: 20
                        
                        // Add button - SVG icon only
                        Item {
                            width: 40
                            height: 40
                            Image {
                                anchors.centerIn: parent
                                source: "../icons/alarm_add.svg"
                                width: 32
                                height: 32
                                fillMode: Image.PreserveAspectFit
                            }
                        }
                        
                        // Text
                        Text {
                            text: "Add new alarm"
                            font.pixelSize: 18
                            color: ThemeManager.text_primary_color
                            Layout.fillWidth: true
                        }
                    }
                }
            }
        }
        
        // Edit Panel - Slides up from bottom when adding/editing
        Rectangle {
            id: editPanel
            Layout.fillWidth: true
            Layout.preferredHeight: editPanelContent.height + 20
            color: ThemeManager.background_color
            visible: false
            
            // Add slide-up animation
            states: State {
                name: "visible"
                when: editPanel.visible
                PropertyChanges { target: editPanel; y: parent.height - editPanel.height }
            }
            
            transitions: Transition {
                NumberAnimation { properties: "y"; duration: 200; easing.type: Easing.OutQuad }
            }
            
            ColumnLayout {
                id: editPanelContent
                width: parent.width
                anchors.centerIn: parent
                spacing: 20
                
                // Time selection with Tumblers
                Rectangle {
                    Layout.alignment: Qt.AlignHCenter
                    Layout.preferredWidth: parent.width * 0.8
                    Layout.preferredHeight: 150
                    color: ThemeManager.background_secondary_color
                    radius: 10
                    
                    RowLayout {
                        anchors.centerIn: parent
                        spacing: 20
                        
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
                        }
                        
                        // Separator
                        Text {
                            text: ":"
                            font.pixelSize: 40
                            font.bold: true
                            color: ThemeManager.text_primary_color
                        }
                        
                        // Minute tumbler
                        Tumbler {
                            id: minuteTumbler
                            model: 60
                            visibleItemCount: 3
                            height: 120
                            width: 80
                            
                            delegate: Text {
                                text: String(modelData).padStart(2, '0')
                                color: ThemeManager.text_primary_color
                                font.pixelSize: minuteTumbler.currentIndex === index ? 30 : 20
                                font.bold: minuteTumbler.currentIndex === index
                                opacity: 1.0 - Math.abs(Tumbler.displacement) / (minuteTumbler.visibleItemCount / 2)
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                        }
                    }
                }
                
                // Label Field
                ColumnLayout {
                    Layout.alignment: Qt.AlignHCenter
                    Layout.preferredWidth: parent.width * 0.8
                    spacing: 5
                    
                    Text {
                        text: "Alarm Label"
                        font.pixelSize: 16
                        color: ThemeManager.text_primary_color
                    }
                    
                    TextField {
                        id: labelField
                        Layout.fillWidth: true
                        placeholderText: "Enter label (optional)"
                        font.pixelSize: 16
                        color: ThemeManager.text_primary_color
                        
                        background: Rectangle {
                            radius: 5
                            color: ThemeManager.background_secondary_color
                        }
                    }
                }
                
                // Repeat options - button row 
                ColumnLayout {
                    Layout.alignment: Qt.AlignHCenter
                    Layout.preferredWidth: parent.width * 0.8
                    spacing: 10
                    
                    Text {
                        text: "Repeat on:"
                        font.pixelSize: 16
                        color: ThemeManager.text_primary_color
                    }
                    
                    // Quick selection buttons
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 10
                        
                        Button {
                            text: "Weekdays"
                            Layout.fillWidth: true
                            onClicked: updateDayPattern("weekdays")
                            
                            contentItem: Text {
                                text: parent.text
                                font: parent.font
                                color: ThemeManager.text_primary_color
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                            
                            background: Rectangle {
                                radius: 8
                                color: ThemeManager.background_secondary_color
                            }
                        }
                        
                        Button {
                            text: "Weekend"
                            Layout.fillWidth: true
                            onClicked: updateDayPattern("weekend")
                            
                            contentItem: Text {
                                text: parent.text
                                font: parent.font
                                color: ThemeManager.text_primary_color
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                            
                            background: Rectangle {
                                radius: 8
                                color: ThemeManager.background_secondary_color
                            }
                        }
                        
                        Button {
                            text: "Every Day"
                            Layout.fillWidth: true
                            onClicked: updateDayPattern("everyday")
                            
                            contentItem: Text {
                                text: parent.text
                                font: parent.font
                                color: ThemeManager.text_primary_color
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                            
                            background: Rectangle {
                                radius: 8
                                color: ThemeManager.background_secondary_color
                            }
                        }
                    }
                    
                    // Day selection
                    GridLayout {
                        id: dayGrid
                        Layout.fillWidth: true
                        Layout.preferredHeight: 80
                        columns: 7
                        rowSpacing: 10
                        columnSpacing: 10
                        
                        property var dayLabels: ["M", "T", "W", "T", "F", "S", "S"]
                        
                        Repeater {
                            id: dayRepeater
                            model: 7
                            
                            Rectangle {
                                id: dayToggle
                                property bool checked: false
                                property string dayText: dayGrid.dayLabels[index]
                                
                                Layout.preferredWidth: 40
                                Layout.preferredHeight: 40
                                Layout.alignment: Qt.AlignHCenter
                                radius: width / 2
                                
                                color: checked ? ThemeManager.accent_color : ThemeManager.background_secondary_color
                                
                                Text {
                                    anchors.centerIn: parent
                                    text: parent.dayText
                                    color: parent.checked ? ThemeManager.accent_text_color : ThemeManager.text_primary_color
                                    font.pixelSize: 16
                                    font.bold: true
                                }
                                
                                MouseArea {
                                    anchors.fill: parent
                                    onClicked: {
                                        parent.checked = !parent.checked
                                        updateSelectedDays()
                                    }
                                }
                            }
                        }
                    }
                }
                
                // Action buttons
                RowLayout {
                    Layout.alignment: Qt.AlignHCenter
                    Layout.preferredWidth: parent.width * 0.8
                    spacing: 20
                    
                    Button {
                        text: "Cancel"
                        Layout.fillWidth: true
                        
                        contentItem: Text {
                            text: parent.text
                            font: parent.font
                            color: ThemeManager.text_primary_color
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                        
                        background: Rectangle {
                            radius: 8
                            color: ThemeManager.background_secondary_color
                        }
                        
                        onClicked: cancelEditing()
                    }
                    
                    Button {
                        text: isEditMode ? "Update" : "Add"
                        Layout.fillWidth: true
                        
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
                        
                        onClicked: saveAlarm()
                    }
                }
            }
        }
    }
    
    // Use the shared NotificationDialog component
    NotificationDialog {
        id: alarmNotification
        title: "Alarm"
        
        // Dynamic text properties
        property string alarmId: ""
        property string alarmName: ""
        
        // Timer to update the displayed time
        Timer {
            id: notificationTimer
            interval: 1000
            running: alarmNotification.visible
            repeat: true
            onTriggered: {
                let now = new Date()
                let hours = now.getHours()
                let minutes = now.getMinutes()
                let ampm = hours >= 12 ? "PM" : "AM"
                
                // Convert to 12-hour format
                hours = hours % 12
                hours = hours ? hours : 12 // the hour '0' should be '12'
                
                // Format with leading zeros
                let minutesStr = minutes < 10 ? '0' + minutes : minutes
                
                // Update the display
                alarmNotification.mainText = hours + ":" + minutesStr + " " + ampm
                alarmNotification.subText = alarmNotification.alarmName
            }
        }
        
        // Configure buttons
        primaryButtonText: "Dismiss"
        hasSecondaryButton: true
        secondaryButtonText: "Snooze (10 min)"
        
        // Define the actions directly rather than connecting to signals
        primaryAction: function() {
            // Just close the dialog - audio stopping is handled in onClosed
            close()
        }
        
        secondaryAction: function() {
            // Create a new one-time alarm for 10 minutes from now
            var now = new Date()
            var snoozeHour = now.getHours()
            var snoozeMinute = now.getMinutes() + 10
            
            // Handle minute overflow
            if (snoozeMinute >= 60) {
                snoozeMinute = snoozeMinute - 60
                snoozeHour = (snoozeHour + 1) % 24
            }
            
            AlarmController.addAlarm(
                alarmNotification.alarmName + " (Snoozed)",
                snoozeHour,
                snoozeMinute,
                true,
                ["ONCE"]
            )
            
            // Close dialog - audio stopping is handled in onClosed
            close()
        }
        
        // Cleanup on close - this is the ONLY place we stop audio
        onClosed: {
            if (typeof AudioManager !== 'undefined' && typeof AudioManager.stop_playback === 'function') {
                AudioManager.stop_playback()
            }
        }
    }
}
