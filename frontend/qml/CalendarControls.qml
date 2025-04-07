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

    // Navigation buttons using TouchFriendlyButton
    TouchFriendlyButton {
        id: prevMonthButton
        source: "file://" + PathProvider.getAbsolutePath("frontend/icons/arroarrow_back_D9D9D9.svg")
        text: "Previous Month"
        Layout.preferredWidth: 50
        onClicked: CalendarController.goToPreviousMonth()
    }
    
    TouchFriendlyButton {
        id: todayButton
        source: "file://" + PathProvider.getAbsolutePath("frontend/icons/today.svg")
        text: "Go to Current Month"
        Layout.preferredWidth: 50
        onClicked: CalendarController.goToToday()
    }
    
    TouchFriendlyButton {
        id: nextMonthButton
        source: "file://" + PathProvider.getAbsolutePath("frontend/icons/arrow_forward_D9D9D9.svg")
        text: "Next Month"
        Layout.preferredWidth: 50
        onClicked: CalendarController.goToNextMonth()
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