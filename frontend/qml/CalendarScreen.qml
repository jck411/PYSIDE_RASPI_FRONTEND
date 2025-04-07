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

        // Header: Month and Year + Calendar Selection
        Rectangle {
            id: headerRect
            Layout.fillWidth: true // Takes full width
            Layout.preferredHeight: 50 // Increased height slightly for checkboxes
            color: ThemeManager.input_background_color // Use defined theme color for header background

            // Use RowLayout for horizontal arrangement
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 10
                anchors.rightMargin: 10
                spacing: 10 // Spacing between items

                // --- Calendar Visibility Checkboxes ---
                RowLayout { // Use another RowLayout for the checkboxes themselves
                    id: calendarSelectionLayout
                    spacing: 8
                    Layout.alignment: Qt.AlignVCenter // Vertically center the checkboxes

                    Repeater {
                        model: CalendarController.availableCalendarsModel
                        delegate: RowLayout { // Delegate for each calendar checkbox
                            spacing: 4

                            CheckBox {
                                id: visibilityCheckbox
                                checked: modelData.is_visible
                                onCheckStateChanged: {
                                    if (checkState !== Qt.PartiallyChecked) {
                                        CalendarController.setCalendarVisibility(modelData.id, checked)
                                    }
                                }
                                // Tooltip for accessibility
                                ToolTip.visible: hovered
                                ToolTip.text: "Toggle visibility for " + modelData.name
                            }

                            Rectangle { // Color indicator
                                width: 12; height: 12; radius: 6
                                color: modelData.color
                                border.color: Qt.darker(modelData.color); border.width: 1
                                Layout.alignment: Qt.AlignVCenter
                            }

                            Text {
                                text: modelData.name
                                color: ThemeManager.text_primary_color // Use defined theme color
                                Layout.alignment: Qt.AlignVCenter
                            }
                        }
                    }
                }

                // Spacer to push Month/Year text to the right
                Item { Layout.fillWidth: true }

                // --- Month/Year Text (Moved to the right) ---
                Text {
                    id: monthYearText
                    text: CalendarController.currentMonthName + " " + CalendarController.currentYear
                    font.pixelSize: 20
                    font.bold: true
                    color: ThemeManager.text_primary_color // Use defined theme color
                    // Layout.fillWidth: false // No longer fills width
                    horizontalAlignment: Text.AlignRight // Align to the right
                    verticalAlignment: Text.AlignVCenter
                }
                // Connections block remains the same, attached to monthYearText
                Connections {
                    target: CalendarController
                    function onCurrentMonthYearChanged() {
                        monthYearText.text = CalendarController.currentMonthName + " " + CalendarController.currentYear;
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
                    color: ThemeManager.background_color // Use defined theme color
                    border.color: ThemeManager.input_border_color // Use defined theme color for border
                    border.width: 1

                    Text {
                        text: modelData
                        anchors.centerIn: parent
                        font.pixelSize: 12
                        font.bold: true
                        color: ThemeManager.text_secondary_color // Use defined theme color
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
