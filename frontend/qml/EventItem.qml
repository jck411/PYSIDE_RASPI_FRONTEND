import QtQuick 2.15
import QtQuick.Layouts 1.15
import MyTheme 1.0

Rectangle {
    id: eventItem
    width: parent.width // Take the width of the container (ListView in DayCell)
    height: eventText.implicitHeight + 4 // Adjust height based on text content
    radius: 3
    // Use the eventColor property, accessed via the component id 'eventItem'
    property color eventColor: modelData.color || "#1a73e8" // Default to Google blue
    
    // Use a much lighter version of the color for background
    color: Qt.lighter(eventColor, 1.8) // Make it much lighter for better text contrast
    
    // Use original color for border
    border.color: eventColor
    border.width: 1
    clip: true // Ensure text doesn't overflow bounds

    // Log modelData on completion
    Component.onCompleted: {
        // console.log("EventItem completed. modelData:", JSON.stringify(modelData)) // Full stringify might be too verbose
        console.log("EventItem completed. modelData keys:", modelData ? Object.keys(modelData) : "undefined")
    }

    // Restore properties bound to modelData
    property string title: modelData.title
    // Modify binding to log modelData and explicitly check start_time value
    property string startTime: {
        console.log("Binding startTime. modelData keys:", modelData ? Object.keys(modelData) : "undefined");
        // Explicitly check if start_time exists and is not null/undefined
        if (modelData && modelData.start_time) {
            return modelData.start_time;
        } else {
            return ""; // Default to empty string
        }
    }
    property bool allDay: modelData.all_day

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 4
        anchors.rightMargin: 4
        anchors.topMargin: 2
        anchors.bottomMargin: 2
        spacing: 4

        // Optional: Small color bar indicator
        Rectangle {
            width: 4
            Layout.fillHeight: true
            color: eventItem.eventColor
            radius: 2
        }

        Text {
            id: eventText
            // Simplified binding for debugging
            // Restore complex binding, using modelData directly
            text: {
                var timeString = "";
                // Only show time if not allDay and startTime is valid
                // Add checks for modelData existence
                if (modelData && !eventItem.allDay && eventItem.startTime) { // Use properties
                    var dtParts = modelData.start_time.split('T');
                    if (dtParts.length > 1) {
                        var timeParts = dtParts[1].split(':');
                        if (timeParts.length >= 2) {
                            timeString = timeParts[0] + ":" + timeParts[1] + " ";
                        }
                    }
                }
                return timeString + (modelData ? eventItem.title : "..."); // Use property
            }
            font.pixelSize: 10 // "Small print"
            // Improved text color calculation based on background color
            // Always use a color that contrasts with the background
            color: {
                // Calculate luminance to determine if we need dark or light text
                var r = eventItem.color.r
                var g = eventItem.color.g
                var b = eventItem.color.b
                var luminance = 0.299 * r + 0.587 * g + 0.114 * b
                
                // Use dark text on light backgrounds, light text on dark backgrounds
                return luminance > 0.5 ? "#000000" : "#ffffff"
            }
            elide: Text.ElideRight
            Layout.fillWidth: true
            verticalAlignment: Text.AlignVCenter
        }
    }
}