import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import MyServices 1.0
import MyTheme 1.0

RowLayout {
    id: photoControls
    spacing: 8
    
    property var screen
    
    // Previous button
    Button {
        text: "Previous"
        onClicked: {
            PhotoController.go_to_previous()
        }
    }
    
    // Play/Pause button
    Button {
        text: PhotoController.is_running ? "Pause" : "Play"
        onClicked: {
            if (PhotoController.is_running) {
                PhotoController.stop_slideshow()
            } else {
                PhotoController.start_slideshow()
            }
        }
        
        // Update button text based on slideshow state
        Connections {
            target: PhotoController
            function onSlideshowRunningChanged(running) {
                parent.text = running ? "Pause" : "Play"
            }
        }
    }
    
    // Next button
    Button {
        text: "Next"
        onClicked: {
            PhotoController.advance_to_next()
        }
    }
    
    // Flexible space
    Item {
        Layout.fillWidth: true
    }
    
    // Back button
    Button {
        text: "Back"
        onClicked: {
            // Navigate back to the previous screen
            if (screen && screen.stackView) {
                screen.stackView.pop()
            }
        }
    }
} 