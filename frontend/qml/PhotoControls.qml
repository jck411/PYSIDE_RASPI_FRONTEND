import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import MyServices 1.0
import MyTheme 1.0

RowLayout {
    id: photoControls
    spacing: 10
    
    property var screen
    
    // Previous button
    TouchFriendlyButton {
        id: previousButton
        source: "../icons/chevron_left.svg"
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
        source: PhotoController.is_running ? "../icons/pause_presentation.svg" : "../icons/play_circle.svg"
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
                playPauseButton.source = running ? "../icons/pause_presentation.svg" : "../icons/play_circle.svg"
                playPauseButton.text = running ? "Pause" : "Play"
            }
        }
    }
    
    // Next button
    TouchFriendlyButton {
        id: nextButton
        source: "../icons/chevron_right.svg"
        text: "Next"
        implicitWidth: 60
        implicitHeight: 40
        onClicked: {
            PhotoController.advance_to_next()
        }
    }
    
    // Flexible space
    Item {
        Layout.fillWidth: true
    }
    
    // Back button
    TouchFriendlyButton {
        id: backButton
        source: "../icons/back.svg"
        text: "Back"
        implicitWidth: 60
        implicitHeight: 40
        onClicked: {
            // Navigate back to the previous screen
            if (screen && screen.stackView) {
                screen.stackView.pop()
            }
        }
    }
} 