import QtQuick 2.15
import QtQuick.Layouts 1.15
import MyTheme 1.0

Rectangle {
    id: eventItem
    width: parent.width // Take the width of the container (ListView in DayCell)
    height: eventText.implicitHeight + 4 // Adjust height based on text content
    radius: 3
    // Use the eventColor property, accessed via the component id 'eventItem'
    color: Qt.lighter(eventItem.eventColor || ThemeManager.input_background_color, 1.5) // Use property, theme fallback
    border.color: eventItem.eventColor || ThemeManager.input_border_color // Use property, theme fallback
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
    property color eventColor: modelData.color // Renamed property

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
            color: eventItem.eventColor || ThemeManager.input_border_color // Use property, theme fallback
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
            // Use fixed dark text color if event has a specific background color for contrast,
            // otherwise use the theme's primary text color.
            color: eventItem.eventColor ? "#1a1b26" : ThemeManager.text_primary_color
            elide: Text.ElideRight
            Layout.fillWidth: true
            verticalAlignment: Text.AlignVCenter
        }
    }
}