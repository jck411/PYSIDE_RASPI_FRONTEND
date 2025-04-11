import QtQuick 2.15
import QtQuick.Controls 2.15
import MyTheme 1.0
import "../utils/CalendarUtils.js" as Utils

// Generic calendar event component
Rectangle {
    id: calendarEvent
    
    // Event data properties
    property var eventData: null
    property bool isAllDay: eventData ? eventData.all_day : false
    property bool isMultiDay: eventData ? (eventData.is_multi_day || false) : false
    property string title: eventData ? (eventData.title || "Untitled") : "Untitled"
    property string startTime: eventData ? eventData.start_time : ""
    property string timeDisplay: eventData ? (eventData.timeDisplay || "") : ""
    property color eventColor: eventData ? (eventData.color || "#4285F4") : "#4285F4"
    
    // Visual properties
    property int eventHeight: 18
    property bool showTime: !isAllDay
    
    // Sizing
    height: eventHeight
    radius: 2
    color: eventColor
    
    // Emit signal when clicked
    signal eventClicked(var eventData)
    
    // Content - time and title
    Text {
        id: eventText
        anchors {
            left: parent.left
            right: parent.right
            verticalCenter: parent.verticalCenter
            leftMargin: 4
            rightMargin: 4
        }
        
        // Display time + title or just title depending on event type
        text: {
            if (!showTime) return title
            
            if (timeDisplay) {
                return timeDisplay + " " + title
            } else if (startTime) {
                return Utils.formatEventTime(startTime) + " " + title
            } else {
                return title
            }
        }
        color: "white"
        font.pixelSize: 11
        elide: Text.ElideRight
    }
    
    // Make events clickable
    MouseArea {
        anchors.fill: parent
        onClicked: {
            calendarEvent.eventClicked(eventData)
        }
        
        // Hover effect
        hoverEnabled: true
        onEntered: parent.opacity = 0.9
        onExited: parent.opacity = 1.0
    }
} 