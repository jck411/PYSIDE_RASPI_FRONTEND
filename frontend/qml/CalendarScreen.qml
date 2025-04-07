import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import MyTheme 1.0
import MyServices 1.0 // Import the services module

Item {
    id: calendarScreen

    // Property to tell MainWindow which controls to load
    property string screenControls: "CalendarControls.qml"
    property bool debugLogging: false // Disable for production
    
    // Handle model changes
    Connections {
        target: CalendarController
        function onDaysInMonthModelChanged() {
            if (debugLogging) {
                var modelLength = CalendarController.daysInMonthModel ? 
                      CalendarController.daysInMonthModel.length : "null"
                console.log("Calendar model changed, length: " + modelLength)
            }
        }
        
        function onCurrentMonthYearChanged() {
            if (debugLogging) {
                console.log("Month/Year changed to: " + 
                      CalendarController.currentMonthName + " " + 
                      CalendarController.currentYear)
            }
        }
        
        function onAvailableCalendarsChanged() {
            if (debugLogging) {
                var calCount = CalendarController.availableCalendarsModel ? 
                      CalendarController.availableCalendarsModel.length : "null"
                console.log("Available calendars changed, count: " + calCount)
            }
        }
    }

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
                        id: calendarRepeater
                        model: CalendarController.availableCalendarsModel
                        delegate: RowLayout { // Delegate for each calendar checkbox
                            spacing: 4

                            CheckBox {
                                id: visibilityCheckbox
                                checked: modelData.is_visible
                                onCheckStateChanged: {
                                    if (checkState !== Qt.PartiallyChecked) {
                                        if (calendarScreen.debugLogging) {
                                            console.log("Setting visibility for " + 
                                                 modelData.name + " to " + checked)
                                        }
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
                    horizontalAlignment: Text.AlignRight // Align to the right
                    verticalAlignment: Text.AlignVCenter
                }
                // Connections to update monthYearText when the value changes
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

        // Unified Calendar View
        UnifiedCalendarView {
            id: unifiedCalendar
            Layout.fillWidth: true
            Layout.fillHeight: true // Take remaining space
            model: CalendarController.daysInMonthModel
            debugOutput: calendarScreen.debugLogging
        }
    }
}
