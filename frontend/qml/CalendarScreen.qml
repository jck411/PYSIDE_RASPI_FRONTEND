import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import MyTheme 1.0
import MyServices 1.0 // Import the services module
// Removed explicit import for DayCell.qml - should be found implicitly in the same directory

Item {
    id: calendarScreen

    // Property to tell MainWindow which controls to load
    property string screenControls: "CalendarControls.qml"

    // For calculating cell sizes
    property int gridColumns: 7
    property int gridRows: 6 // Standard 6 weeks display

    anchors.fill: parent

    ColumnLayout {
        id: mainLayout
        anchors.fill: parent
        spacing: 5 // Reduced spacing

        // Header: Month and Year
        Rectangle {
            id: headerRect
            Layout.fillWidth: true
            Layout.preferredHeight: 40
            color: ThemeManager.secondary_background_color || "lightgrey" // Fallback

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 10
                anchors.rightMargin: 10

                Text {
                    id: monthYearText
                    // Use controller properties directly
                    text: CalendarController.currentMonthName + " " + CalendarController.currentYear
                    font.pixelSize: 20
                    font.bold: true
                    color: ThemeManager.text_primary_color || "black" // Fallback
                    Layout.fillWidth: true
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter

                    // Ensure text updates when controller signals change
                    Connections {
                        target: CalendarController
                        function onCurrentMonthYearChanged() {
                            monthYearText.text = CalendarController.currentMonthName + " " + CalendarController.currentYear;
                        }
                    }
                }
            }
        }

        // Weekday Labels
        RowLayout {
            id: weekdayHeader
            Layout.fillWidth: true
            spacing: 0 // No spacing between labels

            Repeater {
                model: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"] // Or use Locale for names
                delegate: Rectangle {
                    Layout.fillWidth: true // Distribute width evenly
                    Layout.preferredHeight: 25
                    color: ThemeManager.background_color || "white" // Fallback
                    border.color: ThemeManager.outline_color || "grey" // Fallback
                    border.width: 1

                    Text {
                        text: modelData
                        anchors.centerIn: parent
                        font.pixelSize: 12
                        font.bold: true
                        color: ThemeManager.text_secondary_color || "darkgrey" // Fallback
                    }
                }
            }
        }


        // Calendar Grid View
        GridView {
            id: calendarGrid
            Layout.fillWidth: true
            Layout.fillHeight: true // Take remaining space
            clip: true // Prevent delegates spilling out

            // Calculate cell size based on available space and grid dimensions
            // Subtracting small amount for potential borders/spacing issues
            cellWidth: (width - 1) / calendarScreen.gridColumns
            cellHeight: (height - 1) / calendarScreen.gridRows

            // Bind directly to the controller instance, as it IS the model now
            model: CalendarController.daysInMonthModel // Bind back to the property

            delegate: DayCell {
                // Properties are implicitly passed via modelData
                width: calendarGrid.cellWidth
                height: calendarGrid.cellHeight
            }

            // Restore explicit Connections for model changes
             Connections {
                 target: CalendarController
                 function onDaysInMonthModelChanged() {
                     // Optional: Add logging if needed
                     // console.log("Calendar Grid: Model Changed")
                 }
             }
        }
    }
}
