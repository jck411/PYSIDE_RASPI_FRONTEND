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
    // Group navigation buttons in their own layout for closer spacing
    RowLayout {
        spacing: 5 // Reduced spacing between nav buttons

        TouchFriendlyButton {
            id: prevMonthButton
            // text: "<" // Using icon source instead if available, or keep text
            source: "file://" + PathProvider.getAbsolutePath("frontend/icons/arroarrow_back_D9D9D9.svg") // Use specific back arrow
            text: "Previous Month" // Tooltip text via alias
            onClicked: CalendarController.goToPreviousMonth()
            Layout.preferredWidth: 50 // Adjust size as needed
        }

        TouchFriendlyButton {
            id: todayButton
            // text: "Today" // Remove original tooltip text
            source: "file://" + PathProvider.getAbsolutePath("frontend/icons/today.svg") // Set the icon source
            text: "Go to Current Month" // Set the tooltip text via the 'text' alias
            onClicked: CalendarController.goToToday()
            Layout.preferredWidth: 50 // Ensure consistent width with other icon buttons
        }

        TouchFriendlyButton {
            id: nextMonthButton
            // text: ">" // Using icon source instead if available, or keep text
            source: "file://" + PathProvider.getAbsolutePath("frontend/icons/arrow_forward_D9D9D9.svg") // Use specific forward arrow
            text: "Next Month" // Tooltip text via alias
            onClicked: CalendarController.goToNextMonth()
            Layout.preferredWidth: 50 // Adjust size as needed
        }
    }

    // --- Refresh Button ---
    TouchFriendlyButton {
        id: refreshButton
        source: "../icons/refresh.svg" // Relative path from qml folder
        text: "Refresh Calendar Events" // Tooltip text
        onClicked: {
            // Assuming this method exists on the CalendarController
            // Please verify or provide the correct method name if different
            CalendarController.refreshEvents()
        }
        Layout.preferredWidth: 50 // Consistent width with other icon buttons
    }
}