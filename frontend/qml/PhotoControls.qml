 import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import MyServices 1.0
import MyTheme 1.0

import QtQuick 2.15

Rectangle {
    id: photoControlsRoot
    color: Qt.rgba(0, 0, 0, 0.3) // Subtle transparent black background
    radius: 5 // Rounded corners
    implicitWidth: photoControlsLayout.implicitWidth + 20 // Add horizontal padding
    implicitHeight: photoControlsLayout.implicitHeight + 10 // Add vertical padding

    property alias screen: photoControlsLayout.screen
    property alias mainStackView: photoControlsLayout.mainStackView

    RowLayout {
        id: photoControlsLayout // New ID for the layout
        anchors.centerIn: parent // Center the layout within the background
        spacing: 5 // Slightly increased spacing for better look with background

    property var screen
    property var mainStackView: null // Reference to MainWindow's StackView

    // Previous button
    TouchFriendlyButton {
        id: previousButton
        source: "../icons/arrow_left.svg"
        text: "Previous"
        implicitWidth: 60
        implicitHeight: 40
        onClicked: {
            PhotoController.go_to_previous()
        }
    }
    
    // Play/Pause button
    TouchFriendlyButton {
        id: playPauseButton
        source: PhotoController.is_running ? "../icons/pause_circle.svg" : "../icons/play_circle.svg.svg"
        text: PhotoController.is_running ? "Pause" : "Play"
        implicitWidth: 60
        implicitHeight: 40
        onClicked: {
            if (PhotoController.is_running) {
                PhotoController.stop_slideshow()
            } else {
                PhotoController.start_slideshow()
            }
        }
        
        // Update button text and icon based on slideshow state
        Connections {
            target: PhotoController
            function onSlideshowRunningChanged(running) {
                playPauseButton.source = running ? "../icons/pause_circle.svg" : "../icons/play_circle.svg.svg"
                playPauseButton.text = running ? "Pause" : "Play"
            }
        }
    }
    
    // Next button
    TouchFriendlyButton {
        id: nextButton
        source: "../icons/arrow_right.svg"
        text: "Next"
        implicitWidth: 60
        implicitHeight: 40
        onClicked: {
            PhotoController.advance_to_next()
        }
    }
    
    // Exit Button
    TouchFriendlyButton {
        id: exitPhotoButton
        source: "../icons/exit_to_app.svg"
        text: "Exit Photos"
        implicitWidth: 60
        implicitHeight: 40
        onClicked: {
            if (mainStackView) {
                 console.log("PhotoControls: Navigating to ClockScreen using mainStackView");
                 mainStackView.replace("ClockScreen.qml");
            } else {
                 console.error("PhotoControls: mainStackView reference is null!");
            }
        }
    }
    } // End RowLayout
} // End Rectangle