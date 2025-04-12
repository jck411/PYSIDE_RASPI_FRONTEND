import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import MyTheme 1.0
import MyServices 1.0 // Import the services module
import "components" // Import our components directory

Item {
    id: calendarScreen

    // Property to tell MainWindow which controls to load
    property string screenControls: "CalendarControls.qml"
    property bool debugLogging: false // Disable for production
    
    // Add view mode property - will be connected to controller
    property string viewMode: "month" // Default view: "month", "week", "3day", "day"
    
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
        
        // Listen for view mode changes from controller
        function onViewModeChanged(newMode) {
            if (newMode === "day" && calendarScreen.viewMode !== "day") {
                // Store previous view mode when switching to day view
                calendarScreen.previousViewMode = calendarScreen.viewMode;
            }
            calendarScreen.viewMode = newMode;
            if (debugLogging) {
                console.log("View mode changed to: " + newMode);
            }
        }
    }

    // Cycle through view modes
    function cycleViewMode() {
        switch(viewMode) {
            case "month": 
                viewMode = "week"; 
                break;
            case "week": 
                viewMode = "3day"; 
                break;
            case "3day":
            default: 
                viewMode = "month"; 
                break;
        }
        
        // Update controller's view mode
        CalendarController.setViewMode(viewMode);
        
        if (debugLogging) {
            console.log("View mode changed to: " + viewMode);
        }
    }
    
    // Store previous view mode when navigating to day view
    property string previousViewMode: "month"

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

                // Back button (only visible in day view)
                Rectangle {
                    id: backButton
                    width: 40
                    height: 40
                    visible: calendarScreen.viewMode === "day"
                    color: "transparent"
                    Layout.alignment: Qt.AlignVCenter
                    
                    Image {
                        id: backIcon
                        anchors.centerIn: parent
                        source: "file://" + PathProvider.getAbsolutePath("frontend/icons/arroarrow_back_D9D9D9.svg")
                        width: 24
                        height: 24
                        sourceSize.width: 24
                        sourceSize.height: 24
                        fillMode: Image.PreserveAspectFit
                    }
                    
                    MouseArea {
                        anchors.fill: parent
                        onClicked: {
                            // Return to previous view (month or week)
                            CalendarController.setViewMode(calendarScreen.previousViewMode);
                        }
                        
                        // Tooltip
                        ToolTip {
                            visible: parent.containsMouse
                            text: "Back to " + calendarScreen.previousViewMode + " view"
                            delay: 500
                        }
                    }
                }

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

                // --- VIEW TOGGLE ICON (to the left of month/year text) ---
                Rectangle {
                    id: viewToggleButton
                    width: 40
                    height: 40
                    color: "transparent"
                    Layout.alignment: Qt.AlignVCenter
                    
                    // View mode toggle icon
                    Image {
                        id: viewToggleIcon
                        anchors.centerIn: parent
                        source: "file://" + PathProvider.getAbsolutePath("frontend/icons/date_range.svg")
                        width: 24
                        height: 24
                        sourceSize.width: 24
                        sourceSize.height: 24
                        fillMode: Image.PreserveAspectFit
                    }
                    
                    // Small indicator showing current view mode
                    Rectangle {
                        anchors.right: parent.right
                        anchors.bottom: parent.bottom
                        anchors.rightMargin: 2
                        anchors.bottomMargin: 2
                        width: viewModeBadge.width + 6
                        height: viewModeBadge.height + 4
                        radius: height / 2
                        color: ThemeManager.button_primary_color
                        
                        Text {
                            id: viewModeBadge
                            anchors.centerIn: parent
                            text: {
                                switch(calendarScreen.viewMode) {
                                    case "month": return "M";
                                    case "week": return "W";
                                    case "3day": return "3D";
                                    case "day": return "D";
                                    default: return "";
                                }
                            }
                            font.pixelSize: 10
                            font.bold: true
                            color: "white"
                        }
                    }
                    
                    // Mouse area for the toggle button
                    MouseArea {
                        anchors.fill: parent
                        onClicked: {
                            calendarScreen.cycleViewMode();
                        }
                        
                        // Tooltip
                        ToolTip {
                            visible: parent.containsMouse
                            text: "Toggle Calendar View (Month/Week/3-Day)"
                            delay: 500
                        }
                    }
                }

                // --- Month/Year Text (Moved to the right) ---
                Text {
                    text: CalendarController.currentRangeDisplay
                    font.pixelSize: 18
                    font.bold: true
                    color: ThemeManager.text_primary_color // Use defined theme color
                    Layout.alignment: Qt.AlignVCenter
                }
            }
        }

        // Calendar Views Container
        Item {
            id: calendarViewsContainer
            Layout.fillWidth: true
            Layout.fillHeight: true

            // Month Calendar View (only shown in month view)
            UnifiedCalendarView {
                id: unifiedCalendar
                anchors.fill: parent
                model: CalendarController.daysInMonthModel
                debugOutput: calendarScreen.debugLogging
                visible: calendarScreen.viewMode === "month"
            }
            
            // Week Calendar View (shown in week, 3day, day views)
            WeekCalendarView {
                id: weekCalendarView
                anchors.fill: parent
                model: CalendarController.currentRangeDays
                debugOutput: calendarScreen.debugLogging
                visible: calendarScreen.viewMode !== "month"
            }
        }
    }
}
