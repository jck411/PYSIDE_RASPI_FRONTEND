import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtMultimedia 6.0
import QtQuick.Window 2.15
import QtQml 2.15
import MyTheme 1.0
import MyServices 1.0

Item {
    id: photoScreen
    objectName: "photoScreen"  // Add an object name so MainWindow can identify this screen
    
    // Property to tell MainWindow which controls to load
    property string screenControls: "PhotoControls.qml"
    
    // Track if showing video
    property bool showingVideo: false
    property string currentVideoPath: ""
    property string currentImagePath: ""
    property string currentBlurredBackground: ""
    property string currentDateText: ""
    
    // Get reference to the mainWindow
    function getMainWindow() {
        // Start with this component
        var component = photoScreen;
        
        // Go up the parent chain until we find the Window
        while (component) {
            // Check if this is the main window (has the topBarTransparent property)
            // We need a reliable property. Let's assume MainWindow has an 'id: mainWindow'
            if (component.objectName === "mainWindow") { // Check objectName instead
                return component;
            }
            // Check if this is the main window (has the topBarTransparent property) - Reverted this check
            // if (component.topBarTransparent !== undefined) {
            //     return component;
            // }
            component = component.parent;
        }
        return null;
    }
    
    Component.onCompleted: {
        console.log("PhotoScreen loaded")
        
        // Transparency logic moved to MainWindow
        
        // Load the controller and request the initial media item
        PhotoController.start_slideshow()
        
        // Force display of the first item
        if (PhotoController.media_files && PhotoController.media_files.length > 0) {
            var firstItem = PhotoController.media_files[0]
            PhotoController.currentMediaChanged(firstItem[0], firstItem[1])
        }
    }

    Component.onDestruction: {
        console.log("PhotoScreen unloading")
        try {
            // Transparency logic moved to MainWindow
            
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
    
    // Create a background that adapts to theme - fallback when no image is loaded
    Rectangle {
        id: fallbackBackground
        anchors.fill: parent
        visible: !backgroundImage.visible
        gradient: Gradient {
            GradientStop { 
                position: 0.0; 
                color: ThemeManager.background_color 
            }
            GradientStop { 
                position: 1.0; 
                color: ThemeManager.is_dark_mode ? "#000000" : "#1a1b26" 
            }
        }
    }
    
    // Blurred background image - shown when displaying photos
    Image {
        id: backgroundImage
        // anchors.fill: parent // Replaced with specific anchors
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.topMargin: -50 // Pull up by topBar height
        height: parent.height + 50 // Increase height to compensate
        visible: source != "" && !showingVideo
        source: currentBlurredBackground ? "file://" + currentBlurredBackground : ""
        fillMode: Image.PreserveAspectCrop // Crop the background to fill
        
        // Note: The dark overlay was previously removed here.
    }

    Rectangle {
        // anchors.fill: parent // Replaced with specific anchors
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.topMargin: -50 // Pull up by topBar height
        height: parent.height + 50 // Increase height to compensate
        // anchors.margins: 10 // Removed margins to allow full height fill
        color: "transparent"

        // Image component - shown when displaying photos
        Image {
            id: photoImage
            visible: !showingVideo
            anchors.fill: parent
            fillMode: Image.PreserveAspectFit // Fit the image without cropping
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
            font.bold: true
        }
        
        // Date display (bottom left) - shown when displaying photos
        Rectangle {
            id: dateTextBackground
            visible: currentDateText !== "" && (photoImage.status === Image.Ready || showingVideo)
            anchors.left: parent.left
            anchors.bottom: parent.bottom
            anchors.leftMargin: 20
            anchors.bottomMargin: 20
            color: Qt.rgba(0, 0, 0, 0.5)  // Original dark semi-transparent background
            radius: 4
            border.width: 0 // Remove border
            // border.color: "#565f89" // No longer needed
            width: dateText.width + 20
            height: dateText.height + 10
            
            Text {
                id: dateText
                anchors.centerIn: parent
                text: currentDateText
                color: "#565f89"
                font.pixelSize: 14 // Keep the smaller font size
                font.family: "Arial"
                font.bold: true
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
            } else {
                // Handle image
                mediaPlayer.stop() // Stop video if switching to image
                videoTimer.stop()  // Stop fallback timer
                currentImagePath = mediaPath
                photoImage.source = "file://" + mediaPath
            }
        }
        
        function onBlurredBackgroundChanged(blurredPath) {
            console.log("Blurred background updated:", blurredPath)
            currentBlurredBackground = blurredPath // Update local property for the internal background Image
        }
        
        function onDateTextChanged(dateText) {
            console.log("Date text updated:", dateText)
            currentDateText = dateText
        }
    }
}
