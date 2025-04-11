import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import MyTheme 1.0
import MyServices 1.0 // Import services to access CalendarController
// Removed incorrect import for BaseControls. TouchFriendlyButton should be found implicitly.

RowLayout {
    id: calendarControls
    spacing: 10
    property var screen // This property might be used by MainWindow, keep it
    
    // Function to get the current view mode from the screen
    function getCurrentViewMode() {
        return screen ? screen.viewMode : "month";
    }

    // Navigation buttons using TouchFriendlyButton
    TouchFriendlyButton {
        id: prevButton
        source: "file://" + PathProvider.getAbsolutePath("frontend/icons/arroarrow_back_D9D9D9.svg")
        text: {
            var mode = getCurrentViewMode();
            if (mode === "month") return "Previous Month";
            else if (mode === "week") return "Previous Week";
            else if (mode === "3day") return "Previous 3 Days";
            else return "Previous Day";
        }
        Layout.preferredWidth: 50
        onClicked: CalendarController.moveDateRangeBackward()
    }
    
    TouchFriendlyButton {
        id: todayButton
        source: "file://" + PathProvider.getAbsolutePath("frontend/icons/today.svg")
        text: "Go to Today"
        Layout.preferredWidth: 50
        onClicked: CalendarController.goToToday()
    }
    
    TouchFriendlyButton {
        id: nextButton
        source: "file://" + PathProvider.getAbsolutePath("frontend/icons/arrow_forward_D9D9D9.svg")
        text: {
            var mode = getCurrentViewMode();
            if (mode === "month") return "Next Month";
            else if (mode === "week") return "Next Week";
            else if (mode === "3day") return "Next 3 Days";
            else return "Next Day";
        }
        Layout.preferredWidth: 50
        onClicked: CalendarController.moveDateRangeForward()
    }
    
    TouchFriendlyButton {
        id: refreshButton
        source: "file://" + PathProvider.getAbsolutePath("frontend/icons/refresh.svg")
        text: "Refresh Calendar Events"
        Layout.preferredWidth: 50
        onClicked: CalendarController.refreshEvents()
    }
    
    // Spacer to push sync status to the right
    Item {
        Layout.fillWidth: true
    }
    
    // Sync status text
    Text {
        text: CalendarController.syncStatus
        color: ThemeManager.text_secondary_color
        font.pixelSize: 14
        Layout.alignment: Qt.AlignVCenter
    }
}
