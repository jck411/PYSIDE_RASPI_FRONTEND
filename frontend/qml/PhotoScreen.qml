import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtMultimedia 6.0
import QtQuick.Window 2.15
import QtQml 2.15
import MyTheme 1.0
import MyServices 1.0

Item {
    // exitRequested signal removed
    id: photoScreen
    objectName: "photoScreen"  // Add an object name so MainWindow can identify this screen
    property string filename: "PhotoScreen.qml"

    // Handle visibility changes to pause/resume the slideshow timer
    onVisibleChanged: {
        if (visible) {
            console.log("PhotoScreen became visible, attempting to resume timer.")
            PhotoController.resume_timer()
        } else {
            console.log("PhotoScreen became hidden, pausing timer.")
            PhotoController.pause_timer()
        }
    }
    
    // Property to tell MainWindow which controls to load
    property string screenControls: "PhotoControls.qml"
    
    // Track if showing video
    property bool showingVideo: false
    property string currentVideoPath: ""
    property string currentImagePath: ""      // Path of the currently visible image
    property string currentBlurredBackground: ""
    property string currentDateText: ""
    property bool isImage1Active: true        // Track which image is currently active
    
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

    // Removed handleImageStatusChange helper function
    
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

        // --- Dual Image Display for Crossfade ---
        Image {
            id: photoImage1
            visible: !showingVideo
            anchors.fill: parent
            fillMode: Image.PreserveAspectFit
            asynchronous: true
            cache: false
            opacity: isImage1Active ? 1.0 : 0.0

            Behavior on opacity {
                NumberAnimation {
                    duration: 1000
                    easing.type: Easing.InOutQuad
                }
            }

            onStatusChanged: {
                if (status === Image.Error) {
                    console.error("Image 1 failed to load:", source)
                } else if (status === Image.Ready) {
                    console.log("Image 1 loaded successfully:", source)
                    // If this image just loaded and isn't currently active, make it active
                    if (!isImage1Active) {
                        isImage1Active = true;
                    }
                }
            }
        }

        Image {
            id: photoImage2
            visible: !showingVideo
            anchors.fill: parent
            fillMode: Image.PreserveAspectFit
            asynchronous: true
            cache: false
            opacity: isImage1Active ? 0.0 : 1.0

            Behavior on opacity {
                NumberAnimation {
                    duration: 1000
                    easing.type: Easing.InOutQuad
                }
            }

            onStatusChanged: {
                if (status === Image.Error) {
                    console.error("Image 2 failed to load:", source)
                } else if (status === Image.Ready) {
                    console.log("Image 2 loaded successfully:", source)
                    // If this image just loaded and isn't currently active, make it active
                    if (isImage1Active) {
                        isImage1Active = false;
                    }
                }
            }
        }
        // --- End Dual Image Display ---
        
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
            // Visible if not showing video AND neither image is ready
            visible: !showingVideo && 
                     (isImage1Active ? photoImage1.status !== Image.Ready : photoImage2.status !== Image.Ready)
            text: "No media available"
            color: ThemeManager.text_primary_color
            anchors.centerIn: parent
            font.pixelSize: 24
            font.bold: true
        }
        
        // Clock display (bottom left)
        Text {
            id: photoScreenTimeText // Unique ID
            anchors.left: parent.left
            anchors.bottom: parent.bottom
            anchors.leftMargin: 20
            anchors.bottomMargin: 20
            text: "00:00:00" // Initial text
            color: "#FFFFFF" // White text
            font.pixelSize: 20 // Slightly larger than date, but smaller than main clock
            font.family: "Arial"
            font.bold: true
            style: Text.Outline // Add outline style
            styleColor: "#000000" // Black outline color
            visible: true // Always visible
        }

        // Date display (bottom right) - shown when displaying photos
        Rectangle {
            id: dateTextBackground
            // Visible if date text exists AND (video is showing OR either image is ready)
            visible: currentDateText !== "" && 
                    (showingVideo || 
                    (isImage1Active ? photoImage1.status === Image.Ready : photoImage2.status === Image.Ready))
            // anchors.left: parent.left // Removed left anchor
            anchors.right: parent.right // Added right anchor
            anchors.bottom: parent.bottom
            // anchors.leftMargin: 20 // Removed left margin
            anchors.rightMargin: 20 // Added right margin
            anchors.bottomMargin: 20
            color: "transparent" // Remove background color
            radius: 4
            border.width: 0 // Remove border
            // border.color: "#565f89" // No longer needed
            width: dateText.width + 20
            height: dateText.height + 10
            
            Text {
                id: dateText
                anchors.centerIn: parent
                text: currentDateText
                color: "#FFFFFF" // Make text white for better contrast with outline
                font.pixelSize: 14 // Keep the smaller font size
                font.family: "Arial"
                font.bold: true
                style: Text.Outline // Add outline style
                styleColor: "#000000" // Black outline color
            }
        }
        
        // Click handler for manual navigation (only for images)
        MouseArea {
            anchors.fill: parent
            enabled: !showingVideo
            onClicked: {
                // Advance to next media on click
                advanceToNext()
            }
        }
    }
    
    // Simple functions to handle navigation
    function advanceToNext() {
        // Simply use the controller's method
        PhotoController.advance_to_next()
    }
    
    function goToPrevious() {
        // Simply use the controller's method
        PhotoController.go_to_previous()
    }
    
    // Timer for the bottom-left clock
    Timer {
        id: photoScreenClockTimer // Unique ID
        interval: 1000
        running: true
        repeat: true
        triggeredOnStart: true
        onTriggered: {
            var date = new Date()
            // Update only the time text element we just added
            if (typeof photoScreenTimeText !== 'undefined' && photoScreenTimeText) {
                 photoScreenTimeText.text = date.toLocaleTimeString(Qt.locale(), "hh:mm:ss")
            }
        }
    }

    // Handle media changes from controller
    Connections {
        target: PhotoController
        
        function onCurrentMediaChanged(mediaPath, isVideo) {
            console.log("Enhanced onCurrentMediaChanged - Path:", mediaPath, "isVideo:", isVideo);
            showingVideo = isVideo;
            
            if (isVideo) {
                currentVideoPath = mediaPath;
                // Clear both image sources when showing video
                photoImage1.source = "";
                photoImage2.source = "";
                mediaPlayer.stop();
                videoTimer.restart();
                mediaPlayer.source = "file://" + mediaPath;
                mediaPlayer.play();
            } else {
                mediaPlayer.stop(); // Stop video if switching to image
                videoTimer.stop();  // Stop fallback timer
                currentImagePath = mediaPath; // Update path
                
                // Load the new image into the inactive image element
                if (isImage1Active) {
                    photoImage2.source = "file://" + mediaPath;
                } else {
                    photoImage1.source = "file://" + mediaPath;
                }
                
                // We'll toggle the active state in the image's onStatusChanged handler
                // when the new image is actually loaded and ready to be displayed
            }
        } // End of onCurrentMediaChanged function
        
        function onBlurredBackgroundChanged(blurredPath) {
            console.log("Blurred background updated:", blurredPath)
            currentBlurredBackground = blurredPath // Update local property for the internal background Image
        }
        
        function onDateTextChanged(dateText) {
            console.log("Date text updated:", dateText)
            currentDateText = dateText
        }
    } // End Connections

    // Exit button moved to PhotoControls.qml
} // End main Item (photoScreen)
