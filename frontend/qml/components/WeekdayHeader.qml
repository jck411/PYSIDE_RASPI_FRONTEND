import QtQuick 2.15
import QtQuick.Controls 2.15
import MyTheme 1.0

// Header component for displaying weekday names in calendar views
Rectangle {
    id: weekdayHeader
    
    // Properties
    property var dayData: null
    property string dayName: dayData ? dayData.dayName : ""
    property string dayNumber: dayData ? dayData.day : ""
    property bool isToday: dayData ? dayData.isToday : false
    
    // Flag to control whether to show day numbers (used for month vs week views)
    property bool showDayNumber: dayNumber !== ""
    
    // Style properties
    property color backgroundColor: ThemeManager.background_color
    property color borderColor: ThemeManager.input_border_color
    property color textColor: ThemeManager.text_primary_color
    property color todayColor: ThemeManager.button_primary_color
    
    // Visual appearance
    color: backgroundColor
    border.color: borderColor
    border.width: 1
    
    // Content layout
    Column {
        anchors.centerIn: parent
        spacing: 2
        
        // Day name (Mon, Tue, etc)
        Text {
            id: dayNameText
            anchors.horizontalCenter: parent.horizontalCenter
            text: dayName
            font.pixelSize: showDayNumber ? 14 : 16
            font.bold: true
            color: isToday ? todayColor : textColor
        }
        
        // Date (e.g., "15") - only shown when showDayNumber is true
        Text {
            id: dayNumberText
            anchors.horizontalCenter: parent.horizontalCenter
            text: dayNumber
            visible: showDayNumber
            font.pixelSize: 18
            color: isToday ? todayColor : textColor
            font.bold: isToday
        }
    }
    
    // Add subtle highlight for today
    Rectangle {
        visible: isToday
        anchors.fill: parent
        color: todayColor
        opacity: 0.1
        z: -1
    }
} 