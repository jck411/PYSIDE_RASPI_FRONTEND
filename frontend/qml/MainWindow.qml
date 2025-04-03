import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Window 2.15
// import QtQuick.Controls.Material 2.15 // No longer needed
// import MyScreens 1.0 // REMOVED - Module no longer defined/needed here
import MyTheme 1.0  // Import our ThemeManager
import MyServices 1.0 // Need this for SettingsService
// import MyServices 1.0 // No longer needed for ErrorHandler, check if SettingsService is used directly here
import "." // Import the current directory to find TouchFriendlyButton.qml

Window {
    id: mainWindow
    width: 800
    height: 480
    color: ThemeManager.background_color
    title: qsTr("PiPhoto")
    visible: true
    
    // Property to track current screen
    property var currentScreen: null

    Component.onCompleted: {
        // Set initial state based on settings
        var startFullscreen = SettingsService.getSetting('ui.WINDOW_CONFIG.fullscreen', false)
        if (startFullscreen) {
            mainWindow.showFullScreen()
            mainWindow.title = "" // Ensure title is clear if starting fullscreen
        } else {
            mainWindow.showNormal()
            // Initial title will be set by onCurrentItemChanged when StackView loads
        }
        PhotoController.set_dark_mode(ThemeManager.is_dark_mode)
    }
    
    ColumnLayout {
        anchors.fill: parent
        spacing: 0
        
        // Top navigation bar
        Rectangle {
            id: topBar
            height: 50
            color: ThemeManager.background_color
            Layout.fillWidth: true
            
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 10
                anchors.rightMargin: 30
                spacing: 5
                
                // Screen-specific controls
                Loader {
                    id: screenControlsLoader
                    Layout.fillHeight: true
                    Layout.preferredWidth: 200
                    
                    // Handle component loading status
                    onStatusChanged: {
                        if (status === Loader.Ready && item) {
                            item.screen = stackView.currentItem
                        }
                    }
                }
                
                Item { 
                    Layout.fillWidth: true 
                    Layout.preferredWidth: 50
                } // Spacer
                
                // Navigation icons
                TouchFriendlyButton {
                    id: chatButton
                    source: "../icons/chat.svg"
                    text: "Chat"
                    onClicked: stackView.replace("ChatScreen.qml")
                }

                TouchFriendlyButton {
                    id: weatherButton
                    source: "../icons/weather.svg"
                    text: "Weather"
                    onClicked: stackView.replace("WeatherScreen.qml")
                }

                TouchFriendlyButton {
                    id: calendarButton
                    source: "../icons/calendar.svg"
                    text: "Calendar"
                    onClicked: stackView.replace("CalendarScreen.qml")
                }

                TouchFriendlyButton {
                    id: clockButton
                    source: "../icons/clock.svg"
                    text: "Clock"
                    onClicked: stackView.replace("ClockScreen.qml")
                }

                TouchFriendlyButton {
                    id: photosButton
                    source: "../icons/photos.svg"
                    text: "Photos"
                    onClicked: stackView.replace("PhotoScreen.qml")
                }

                TouchFriendlyButton {
                    id: themeToggleButton
                    source: ThemeManager.is_dark_mode ? "../icons/light_mode.svg" : "../icons/dark_mode.svg"
                    text: ThemeManager.is_dark_mode ? "Switch to Light Mode" : "Switch to Dark Mode"
                    onClicked: ThemeManager.toggle_theme()
                }

                TouchFriendlyButton {
                    id: settingsButton
                    source: "../icons/settings.svg"
                    text: "Settings"
                    onClicked: stackView.replace("SettingsScreen.qml")
                }
            }
        }
        
        StackView {
            id: stackView
            Layout.fillWidth: true
            Layout.fillHeight: true
            initialItem: "ChatScreen.qml"
            
            onCurrentItemChanged: {
                currentScreen = currentItem
                
                // Only load controls after current item is fully loaded
                if (currentItem && currentItem.screenControls) {
                    // First clear the old component
                    screenControlsLoader.source = ""
                    // Then load the new one
                    screenControlsLoader.source = currentItem.screenControls
                    
                    // Update the window title if the screen has a title
                    if (currentItem.title) {
                        // Only set title if not fullscreen
                        if (SettingsService.getSetting('ui.WINDOW_CONFIG.fullscreen', false) === false) {
                            mainWindow.title = currentItem.title
                        } else {
                            mainWindow.title = "" // Clear title in fullscreen
                        }
                    }
                }
            }
        }
    }

    // Error Notification Snackbar - REMOVED
    /*
    Snackbar {
        id: errorSnackbar
        anchors.bottom: parent.bottom
        anchors.horizontalCenter: parent.horizontalCenter
        width: parent.width * 0.8 // Take 80% of the window width
        timeout: 5000 // Show for 5 seconds

        contentItem: Label {
            text: errorSnackbar.text // Display the text property of the Snackbar
            color: "white"
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.Wrap // Wrap text if needed
        }

        background: Rectangle {
            color: "#D32F2F" // Material Design error color (red)
            radius: 4
        }
    }
    */

    // Connect to ErrorHandler signal - REMOVED
    /*
    Connections {
        target: ErrorHandler
        function onErrorOccurred(error_type, user_message) {
            console.log("QML received error: ", error_type, " - ", user_message)
            errorSnackbar.text = user_message // Set the text to display
            errorSnackbar.open() // Show the snackbar
        }
    }
    */

    // Need a connection to react to setting changes
    Connections {
        target: SettingsService
        function onSettingChanged(key, value) {
            if (key === 'ui.WINDOW_CONFIG.fullscreen') {
                console.log("MainWindow reacting to fullscreen change:", value)
                // Use showFullScreen/showNormal methods
                if (value) {
                    mainWindow.showFullScreen()
                } else {
                    mainWindow.showNormal()
                }
                
                // Update title logic (remains the same)
                if (stackView.currentItem && stackView.currentItem.title) {
                    if (value === false) {
                        mainWindow.title = stackView.currentItem.title
                    } else {
                        mainWindow.title = ""
                    }
                }
            }
        }
    }

    // Connect ThemeManager to PhotoController
    Connections {
        target: ThemeManager
        function onIsDarkModeChanged() {
            PhotoController.set_dark_mode(ThemeManager.is_dark_mode)
        }
    }
}
