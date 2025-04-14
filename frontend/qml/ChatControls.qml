import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick 6.2 // Needed for Timer

import MyServices 1.0 // Import ChatService

// Controls component for Chat Screen
BaseControls {
    id: chatControls
    spacing: 5  // Match the spacing from BaseControls
    
    // Properties for UI timer state
    property int totalDurationMs: 0
    property int remainingMs: 0
    property bool timerRunning: false

    // Get initial states on completion
    Component.onCompleted: {
        try {
            // Get TTS State
            ttsButton.isEnabled = ChatService.isTtsEnabled()
            console.log("ChatControls initial TTS state:", ttsButton.isEnabled)
            
            // Get STT State
            sttButton.isListening = ChatService.isSttEnabled()
            console.log("ChatControls initial STT state:", sttButton.isListening)
            
            // Get Timer State (only if STT is initially active)
            if (sttButton.isListening) {
                chatControls.timerRunning = ChatService.isSttInactivityTimerRunning()
                chatControls.remainingMs = ChatService.getSttInactivityTimeRemaining()
                console.log("ChatControls initial Timer state - Running:", chatControls.timerRunning, "Remaining:", chatControls.remainingMs)
                // Ensure remainingMs is not negative or excessively large if backend returns weird values
                if (chatControls.remainingMs < 0) chatControls.remainingMs = 0;
            } else {
                chatControls.timerRunning = false
                chatControls.remainingMs = 0
            }
            
        } catch (e) {
            console.error("ChatControls: Error getting initial state:", e)
            // Reset all relevant states on error
            ttsButton.isEnabled = false 
            sttButton.isListening = false
            chatControls.timerRunning = false
            chatControls.remainingMs = 0
        }
    }

    // Timer for UI countdown updates
    Timer {
        id: uiTimer
        interval: 1000 // Update every second
        repeat: true
        running: chatControls.timerRunning
        onTriggered: {
            if (chatControls.remainingMs > 0) {
                chatControls.remainingMs -= 1000;
                if (chatControls.remainingMs < 0) {
                    chatControls.remainingMs = 0;
                }
            } 
            // Timer automatically stops when running is false or if remainingMs hits 0
            // Backend handles the actual STT stop
        }
    }
    
    TouchFriendlyButton {
        id: sttButton
        property bool isListening: false
        source: "../icons/mic.svg"
        text: isListening ? "Listening..." : "Tap to Speak"
        
        opacity: isListening ? 1.0 : 0.5
        
        onClicked: {
            ChatService.toggleSTT()
        }
    }
    
    TouchFriendlyButton {
        id: ttsButton
        property bool isEnabled: false
        source: isEnabled ? "../icons/sound_on.svg" : "../icons/sound_off.svg"
        text: isEnabled ? "TTS On" : "TTS Off"
        onClicked: {
            isEnabled = !isEnabled
            ChatService.toggleTTS()
        }
    }
    
    TouchFriendlyButton {
        id: stopButton
        source: "../icons/stop_all.svg"
        text: "Stop"
        onClicked: ChatService.stopAll()
    }
    
    TouchFriendlyButton {
        id: clearButton
        source: "../icons/clear_all.svg"
        text: "Clear"
        onClicked: {
            ChatService.clearChat()
        }
    }
    
    // Add a spacer to prevent stretching
    Item {
        Layout.fillWidth: true
    }

    // --- Countdown Timer UI --- 
    Text {
        id: countdownText
        text: Math.ceil(chatControls.remainingMs / 1000) + "s" // Display whole seconds remaining
        // font.pixelSize: sttButton.font.pixelSize // Original binding - can fail on load
        // Use a fallback if sttButton.font isn't ready
        font.pixelSize: sttButton.font ? sttButton.font.pixelSize : 14 
        color: "#565f89" // Updated color to match icons
        font.bold: true
        anchors.verticalCenter: parent.verticalCenter // Align with parent row
        visible: chatControls.timerRunning && chatControls.remainingMs > 0
        Layout.preferredWidth: 40 // Give it some fixed width
        horizontalAlignment: Text.AlignRight // Align text to the right within its space
    }
    // --- End Countdown Timer UI --- 

    // Connect signals from ChatService to update button states
    Connections {
        target: ChatService
        ignoreUnknownSignals: true
        
        function onSttStateChanged(listening) {
            // console.log("ChatControls received sttStateChanged: ", listening)
            sttButton.isListening = listening
            // Also stop UI timer if STT is manually disabled
            if (!listening && chatControls.timerRunning) {
                chatControls.timerRunning = false;
                chatControls.remainingMs = 0;
            }
        }
        
        function onTtsStateChanged(enabled) {
            // console.log("ChatControls received ttsStateChanged: ", enabled)
            ttsButton.isEnabled = enabled
        }
        
        // --- Inactivity Timer Signals --- 
        function onInactivityTimerStarted(durationMs) {
            // console.log("UI Timer Started: duration=", durationMs)
            chatControls.totalDurationMs = durationMs;
            chatControls.remainingMs = durationMs;
            chatControls.timerRunning = true; // Starts the QML Timer
        }
        
        function onInactivityTimerStopped() {
            // console.log("UI Timer Stopped")
            chatControls.timerRunning = false; // Stops the QML Timer
            chatControls.remainingMs = 0;
            chatControls.totalDurationMs = 0;
        }
        // --- End Inactivity Timer Signals --- 
    }
}
