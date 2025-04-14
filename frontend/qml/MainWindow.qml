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
// Removing the navigation utility import since we're using direct navigation
// import "utils/ScreenNavigation.js" as Navigation

Window {
    id: mainWindow
    width: 800
    height: 480
    color: ThemeManager.background_color
    title: qsTr("PiPhoto")
    visible: true
    objectName: "mainWindow" // Keep objectName

    // Property to track current screen
    property var currentScreen: null
    property bool topBarTransparent: false // Keep property
    property bool isFullScreen: visibility === Window.FullScreen // Track fullscreen state

    // Update title when visibility changes
    onVisibilityChanged: {
        if (stackView && stackView.currentItem && stackView.currentItem.title) {
            if (visibility === Window.FullScreen) {
                mainWindow.title = ""
            } else {
                mainWindow.title = stackView.currentItem.title
            }
        }
    }

    Component.onCompleted: {
        // Initial settings - use Windowed by default for stability
        visibility = Window.Windowed
        
        // Initial theme setup
        PhotoController.set_dark_mode(ThemeManager.is_dark_mode)
    }
    
    // --- Main Layout ---
    ColumnLayout {
        id: mainColumnLayout // Added ID for clarity
        anchors.fill: parent
        spacing: 0
        
        // Top navigation bar
        Rectangle {
            id: topBar
            height: 50
            // Use opacity binding for transparency
            color: ThemeManager.background_color // Keep theme color
            // opacity: topBarTransparent ? 0 : 1 // Remove opacity control from topBar itself
            Layout.fillWidth: true
            // z: 2 // Not needed here

            RowLayout { // Contains standard nav icons
                id: standardNavLayout // Give it an ID
                visible: !topBarTransparent // Hide this layout when bar should be transparent
                anchors.fill: parent
                anchors.leftMargin: 10
                anchors.rightMargin: 30
                spacing: 5
                
                // Loader is now outside this RowLayout/Rectangle
                
                Item { // Spacer - Adjust width if needed now loader is gone
                    Layout.fillWidth: true 
                    Layout.preferredWidth: 250 // Increased spacer width
                } 
                
                // Navigation icons with simplified direct navigation
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
                    id: photosButton
                    source: "../icons/photos.svg"
                    text: "Photos"
                    onClicked: stackView.replace("PhotoScreen.qml")
                }
                
                TouchFriendlyButton {
                    id: clockButton
                    source: "../icons/clock.svg"
                    text: "Clock"
                    onClicked: stackView.replace("ClockScreen.qml")
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
            
            } // End RowLayout
        } // End topBar Rectangle
        
        // StackView positioned below topBar by ColumnLayout
        StackView {
            id: stackView // This is the correct StackView
            Layout.fillWidth: true
            Layout.fillHeight: true
            // We need to provide an initial string path, but we'll replace it properly in Component.onCompleted
            initialItem: "ChatScreen.qml"
            
            onCurrentItemChanged: {
                currentScreen = currentItem
                
                // Load controls into the external Loader
                if (currentItem && currentItem.screenControls) {
                    screenControlsLoader.source = "" // Clear first
                    screenControlsLoader.source = currentItem.screenControls
                } else {
                     screenControlsLoader.source = "" // Clear if no controls specified
                }
                
                // Update title
                if (currentItem && currentItem.title) {
                    if (!isFullScreen) {
                        mainWindow.title = currentItem.title
                    } else {
                        mainWindow.title = "" 
                    }
                }
                
                // Set top bar transparency based on the current screen
                if (currentItem && currentItem.objectName === "photoScreen") {
                    topBarTransparent = true;
                } else {
                    topBarTransparent = false;
                }
            }
        } // End StackView
    } // End ColumnLayout
    // --- End Main Layout ---

    // Exit signal connection removed

    // --- Floating Screen Controls Loader ---
    Loader { // Positioned absolutely, outside ColumnLayout
        id: screenControlsLoader
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.leftMargin: 10 // Align with topBar content
        anchors.topMargin: 5   // Align vertically within bar height (approx)
        height: 40             // Height matching buttons inside bar
        width: 250             // Provide reasonable width (adjust as needed)
        z: 3                   // Ensure it's above the topBar

        onStatusChanged: {
            if (status === Loader.Ready && item) {
                console.log("ScreenControlsLoader: Loading screen controls, stackView exists:", stackView !== null);
                
                // Pass screen reference
                item.screen = stackView.currentItem;
                
                // Pass stackView reference if property exists
                if (item.hasOwnProperty("mainStackView")) {
                    console.log("ScreenControlsLoader: Setting mainStackView property on controls");
                    item.mainStackView = stackView;
                }
            }
        }
    }
    // --- End Loader ---

    // Error Notification Snackbar - REMOVED
    /* ... */

    // Connect to ErrorHandler signal - REMOVED
    /* ... */

    // Need a connection to react to setting changes
    Connections {
        target: SettingsService
        function onSettingChanged(key, value) {
            if (key === 'ui.WINDOW_CONFIG.fullscreen') {
                console.log("MainWindow reacting to fullscreen change:", value)
                isFullScreen = Boolean(value)
                if (Boolean(value) === true) {
                    // Switch to fullscreen mode
                    visibility = Window.FullScreen
                } else {
                    // Switch to normal windowed mode
                    visibility = Window.Windowed
                }
                
                if (stackView.currentItem && stackView.currentItem.title) {
                    if (Boolean(value) === false) {
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
