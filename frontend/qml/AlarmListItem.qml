import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import MyTheme 1.0
import MyServices 1.0

Rectangle {
    id: alarmItem
    width: parent.width
    height: 60
    // Add default 0 for index if not provided by ListView
    property int index: 0
    
    color: index % 2 === 0 ? 
        (ThemeManager.card_alternate_color !== undefined ? ThemeManager.card_alternate_color : ThemeManager.card_color) : 
        ThemeManager.card_color
    radius: 6
    
    // Properties from model
    property string alarmId: ""
    property string alarmName: ""
    property string alarmTime: ""
    property bool alarmEnabled: true
    property var recurrence: []
    property string recurrenceText: ""
    
    // Signal when deleting
    signal deleted()
    signal edited()
    
    // Calculate human-readable recurrence text
    function getRecurrenceText(recurrenceArray) {
        if (!recurrenceArray || recurrenceArray.length === 0) {
            return "Once"
        }
        
        if (recurrenceArray.includes("DAILY")) {
            return "Daily"
        }
        
        if (recurrenceArray.includes("WEEKDAYS")) {
            return "Weekdays"
        }
        
        if (recurrenceArray.includes("WEEKENDS")) {
            return "Weekends"
        }
        
        if (recurrenceArray.includes("ONCE")) {
            return "Once"
        }
        
        // Custom days
        const days = []
        const dayNames = {
            "MON": "Mon", 
            "TUE": "Tue", 
            "WED": "Wed", 
            "THU": "Thu", 
            "FRI": "Fri", 
            "SAT": "Sat", 
            "SUN": "Sun"
        }
        
        for (let day of recurrenceArray) {
            if (dayNames[day]) {
                days.push(dayNames[day])
            }
        }
        
        return days.join(", ")
    }
    
    Component.onCompleted: {
        recurrenceText = getRecurrenceText(recurrence)
    }
    
    RowLayout {
        anchors.fill: parent
        anchors.margins: 8
        spacing: 10
        
        // Enabled toggle switch
        Switch {
            id: enabledSwitch
            checked: alarmEnabled
            onToggled: {
                AlarmController.setAlarmEnabled(alarmId, checked)
            }
        }
        
        // Alarm time and name
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 2
            
            Text {
                text: alarmTime
                font.pixelSize: 20
                font.bold: true
                color: ThemeManager.text_primary_color
            }
            
            Text {
                text: alarmName
                font.pixelSize: 14
                color: ThemeManager.text_secondary_color
            }
        }
        
        // Recurrence pattern
        Text {
            text: recurrenceText
            font.pixelSize: 14
            color: ThemeManager.text_secondary_color
            Layout.alignment: Qt.AlignRight | Qt.AlignVCenter
        }
        
        // Controls
        RowLayout {
            spacing: 8
            Layout.alignment: Qt.AlignRight | Qt.AlignVCenter
            
            // Edit button
            RoundButton {
                id: editButton
                icon.source: "../icons/edit.svg"
                icon.width: 20
                icon.height: 20
                icon.color: ThemeManager.text_primary_color
                
                ToolTip.visible: hovered
                ToolTip.text: "Edit alarm"
                ToolTip.delay: 500
                
                onClicked: {
                    edited()
                }
                
                background: Rectangle {
                    color: editButton.hovered ? ThemeManager.button_hover_color : "transparent"
                    radius: width / 2
                }
            }
            
            // Delete button
            RoundButton {
                id: deleteButton
                icon.source: "../icons/delete.svg"
                icon.width: 20
                icon.height: 20
                icon.color: ThemeManager.text_primary_color
                
                ToolTip.visible: hovered
                ToolTip.text: "Delete alarm"
                ToolTip.delay: 500
                
                onClicked: {
                    deleted()
                }
                
                background: Rectangle {
                    color: deleteButton.hovered ? ThemeManager.button_hover_color : "transparent"
                    radius: width / 2
                }
            }
        }
    }
}
