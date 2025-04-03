import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtMultimedia 6.0
import MyTheme 1.0
import MyServices 1.0

Item {
    id: photoScreen
    
    // Property to tell MainWindow which controls to load
    property string screenControls: "PhotoControls.qml"
    
    // Track if showing video
    property bool showingVideo: false
    property string currentVideoPath: ""
    
    Component.onCompleted: {
        console.log("PhotoScreen loaded")
        PhotoController.start_slideshow()
    }

    Component.onDestruction: {
        console.log("PhotoScreen unloading")
        try {
            if (showingVideo && mediaPlayer) {
                mediaPlayer.stop()
            }
            // Check if PhotoController exists and has stop_slideshow function
            if (PhotoController && typeof PhotoController.stop_slideshow === 'function') {
                PhotoController.stop_slideshow()
            } else {
                console.log("PhotoController.stop_slideshow not available during cleanup")
            }
        } catch (e) {
            console.error("Error during cleanup:", e)
        }
    }
    
    Rectangle {
        anchors.fill: parent
        color: ThemeManager.background_color

        // Image component - shown when displaying photos
        Image {
            id: photoImage
            visible: !showingVideo
            anchors.fill: parent
            fillMode: Image.PreserveAspectFit
            asynchronous: true
            cache: false
            
            // Fade transition effect
            Behavior on opacity {
                NumberAnimation { duration: 500 }
            }
            
            // Apply fade-in effect when loaded
            onStatusChanged: {
                if (status === Image.Ready) {
                    opacity = 0
                    opacity = 1
                }
            }
        }
        
        // Video components for QtMultimedia 6.0
        MediaPlayer {
            id: mediaPlayer
            audioOutput: AudioOutput {}
            videoOutput: videoOutput
            
            onPlaybackStateChanged: function(state) {
                console.log("Media playback state changed:", state)
                if (state === MediaPlayer.StoppedState) {
                    // Signal the controller that video has finished
                    console.log("Video playback stopped")
                    PhotoController.video_finished()
                }
            }
            
            onErrorOccurred: function(error, errorString) {
                console.error("Media player error:", error, errorString)
                // If media player fails, use the fallback timer to advance
                videoTimer.start()
            }
        }
        
        VideoOutput {
            id: videoOutput
            anchors.fill: parent
            visible: showingVideo
            fillMode: VideoOutput.PreserveAspectFit
        }
        
        // Timer as fallback for videos that fail to load/play
        Timer {
            id: videoTimer
            interval: 10000  // 10 seconds as fallback for video playback
            running: false
            onTriggered: {
                PhotoController.video_finished()
            }
        }
        
        // No media message - shown when no media available
        Text {
            visible: photoImage.status !== Image.Ready && !showingVideo
            text: "No media available"
            color: ThemeManager.text_primary_color
            anchors.centerIn: parent
            font.pixelSize: 24
        }
        
        // Content information overlay - shown at bottom of screen
        Rectangle {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            height: 40
            color: Qt.rgba(0, 0, 0, 0.5) // Semi-transparent background
            visible: photoImage.status === Image.Ready || showingVideo
            
            Text {
                id: mediaInfoText
                anchors.fill: parent
                anchors.margins: 10
                color: "white"
                elide: Text.ElideMiddle
                font.pixelSize: 14
            }
        }
        
        // Click handler for manual navigation (only for images)
        MouseArea {
            anchors.fill: parent
            enabled: !showingVideo
            onClicked: {
                // Advance to next media on click
                PhotoController.advance_to_next()
            }
        }
    }
    
    // Handle media changes from controller
    Connections {
        target: PhotoController
        
        function onCurrentMediaChanged(mediaPath, isVideo) {
            console.log("Loading media:", mediaPath, "isVideo:", isVideo)
            showingVideo = isVideo
            currentVideoPath = mediaPath
            
            if (isVideo) {
                // Handle video - mediaPath should be the full path to the video file
                // Stop any currently playing media first
                mediaPlayer.stop()
                
                // Start a timer as fallback in case video doesn't play properly
                videoTimer.restart()
                
                // Load and play the video
                console.log("Setting video source:", "file://" + mediaPath)
                mediaPlayer.source = "file://" + mediaPath
                mediaPlayer.play()
                
                mediaInfoText.text = "Video: " + mediaPath.split('/').pop()
            } else {
                // Handle image
                mediaPlayer.stop()
                photoImage.source = "file://" + mediaPath
                mediaInfoText.text = "Photo: " + mediaPath.split('/').pop()
            }
        }
    }
}
