import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import MyTheme 1.0
// Removed explicit import for EventItem.qml - should be found implicitly

Rectangle {
    id: dayCell
    width: 100 // Example size, GridView will manage this
    height: 100 // Example size
    // Access model data via role names (defined in CalendarController)
    // Add fallbacks for ThemeManager colors
    color: modelData.isCurrentMonth ? ThemeManager.background_color : ThemeManager.input_background_color // Use defined theme colors
    border.color: ThemeManager.input_border_color // Use defined theme color for border
    border.width: 1

    // Restore properties bound to modelData
    property int dayNumber: modelData.dayNumber
    property bool isCurrentMonth: modelData.isCurrentMonth
    property bool isToday: modelData.isToday
    property var events: modelData.events // Holds list of event dictionaries for this day

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 4
        spacing: 2

        // Display Day Number
        Text {
            id: dayNumberText
            // Bind back to properties
            text: dayCell.dayNumber > 0 ? dayCell.dayNumber : ""
            font.pixelSize: 12
            font.bold: dayCell.isToday // Highlight today's date
            // Add fallbacks for ThemeManager colors
            color: dayCell.isToday ? ThemeManager.button_primary_color : (dayCell.isCurrentMonth ? ThemeManager.text_primary_color : ThemeManager.text_secondary_color) // Use defined theme colors
            Layout.alignment: Qt.AlignHCenter // Center day number horizontally
        }

        // Restore Event List View
        ListView {
            id: eventListView
            Layout.fillWidth: true
            Layout.fillHeight: true // Take remaining vertical space
            clip: true // Prevent delegates from drawing outside bounds
            model: dayCell.events // Bind to the events property passed via modelData
            spacing: 2 // Spacing between event items

            delegate: EventItem {
                // Properties are implicitly passed via modelData from the events list
                width: eventListView.width // Ensure delegate fills width
            }

            // Optional: Add scroll indicator if needed, though space is limited
            // ScrollIndicator.vertical: ScrollIndicator { }

            // Hide if there are no events
            visible: dayCell.events && dayCell.events.length > 0
        }
    }
}