import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import MyTheme 1.0
import MyServices 1.0 // Import services to access CalendarController
// Removed incorrect import for BaseControls. TouchFriendlyButton should be found implicitly.

RowLayout {
    id: calendarControls
    spacing: 15 // Increased spacing for clarity
    property var screen // This property might be used by MainWindow, keep it

    // --- Navigation Buttons ---
    TouchFriendlyButton {
        id: prevMonthButton
        // text: "<" // Using icon source instead if available, or keep text
        source: "file://" + PathProvider.getAbsolutePath("frontend/icons/arrow_left.svg") // Use PathProvider
        text: "Previous Month" // Correct property for tooltip
        onClicked: CalendarController.goToPreviousMonth()
        Layout.preferredWidth: 50 // Adjust size as needed
    }

    TouchFriendlyButton {
        id: todayButton
        text: "Today" // This sets the button text AND the tooltip text via alias
        // tooltip: "Go to Current Month" // Redundant if text is set
        onClicked: CalendarController.goToToday()
    }

    TouchFriendlyButton {
        id: nextMonthButton
        // text: ">" // Using icon source instead if available, or keep text
        source: "file://" + PathProvider.getAbsolutePath("frontend/icons/arrow_right.svg") // Use PathProvider
        text: "Next Month" // Correct property for tooltip
        onClicked: CalendarController.goToNextMonth()
        Layout.preferredWidth: 50 // Adjust size as needed
    }

    // Spacer to push calendar list to the right (adjust layout as needed)
    Item { Layout.fillWidth: true }

    // --- Calendar Visibility List ---
    Rectangle { // Add a background for the list area
        Layout.preferredWidth: 200 // Adjust width as needed
        Layout.fillHeight: true
        color: ThemeManager.secondary_background_color || "lightgrey" // Fallback
        radius: 5
        clip: true // Ensure content stays within bounds

        ListView {
            id: calendarListView
            anchors.fill: parent
            anchors.margins: 5
            model: CalendarController.availableCalendarsModel // Bind to the controller's model
            spacing: 5

            delegate: RowLayout {
                width: parent.width // Fill the width of the ListView
                spacing: 8

                CheckBox {
                    id: visibilityCheckbox
                    checked: modelData.is_visible // Bind checked state to model
                    // Use onCheckStateChanged for better reliability with binding
                    onCheckStateChanged: {
                        if (checkState !== Qt.PartiallyChecked) { // Avoid intermediate state if any
                           CalendarController.setCalendarVisibility(modelData.id, checked)
                        }
                    }
                    // Tooltip for accessibility
                    ToolTip.visible: hovered
                    ToolTip.text: "Toggle visibility for " + modelData.name
                }

                Rectangle { // Color indicator
                    width: 12
                    height: 12
                    radius: 6
                    color: modelData.color // Use color from model
                    border.color: Qt.darker(modelData.color)
                    border.width: 1
                    Layout.alignment: Qt.AlignVCenter
                }

                Text {
                    text: modelData.name // Display calendar name
                    color: ThemeManager.text_primary_color || "black" // Fallback
                    elide: Text.ElideRight // Elide if name is too long
                    Layout.fillWidth: true
                    Layout.alignment: Qt.AlignVCenter
                }
            }

            ScrollIndicator.vertical: ScrollIndicator { } // Add scroll indicator if list is long
        }
    }
}