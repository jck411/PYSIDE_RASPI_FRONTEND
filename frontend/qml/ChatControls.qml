import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

// Controls component for Chat Screen
BaseControls {
    id: chatControls
    spacing: 5  // Match the spacing from BaseControls
    
    TouchFriendlyButton {
        id: sttButton
        property bool isListening: false
        source: isListening ? "../icons/stt_on.svg" : "../icons/stt_off.svg"
        text: isListening ? "STT On" : "STT Off"
        onClicked: {
            isListening = !isListening
            screen.chatLogic.toggleSTT()
        }
    }
    
    TouchFriendlyButton {
        id: ttsButton
        property bool isEnabled: false
        source: isEnabled ? "../icons/sound_on.svg" : "../icons/sound_off.svg"
        text: isEnabled ? "TTS On" : "TTS Off"
        onClicked: {
            isEnabled = !isEnabled
            screen.chatLogic.toggleTTS()
        }
    }
    
    TouchFriendlyButton {
        id: stopButton
        source: "../icons/stop_all.svg"
        text: "Stop"
        onClicked: screen.chatLogic.stopAll()
    }
    
    TouchFriendlyButton {
        id: clearButton
        source: "../icons/clear_all.svg"
        text: "Clear"
        onClicked: {
            screen.chatLogic.clearChat()
            screen.chatModel.clear()
        }
    }
    
    // Add a spacer to prevent stretching
    Item {
        Layout.fillWidth: true
    }

    // Connect signals from ChatLogic to update button states
    Connections {
        target: screen ? screen.chatLogic : null
        
        function onSttStateChanged(enabled) {
            sttButton.isListening = enabled
        }
        
        function onTtsStateChanged(enabled) {
            ttsButton.isEnabled = enabled
        }
    }
}
