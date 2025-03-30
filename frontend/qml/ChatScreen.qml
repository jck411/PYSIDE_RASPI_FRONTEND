import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

// import MyScreens 1.0 // REMOVED - Module no longer defined/needed here
import MyTheme 1.0  // Import our ThemeManager
import MyServices 1.0 // Needed for SettingsService AND ChatService

BaseScreen {
    id: chatScreen
    title: "Chat Interface"
    
    // Property to hold the setting value
    property bool showInputBox: true
    
    // Properties to expose chat logic (singleton) and model to controls
    // property alias chatLogic: ChatService // REMOVED - Conflicting alias
    property alias chatModel: chatModel
    
    // Set the controls file for this screen
    screenControls: "ChatControls.qml"
    
    Component.onCompleted: {
        // Get initial value for input box visibility
        try {
            showInputBox = SettingsService.getSetting("chat.CHAT_CONFIG.show_input_box", true)
            console.log("ChatScreen initial showInputBox value:", showInputBox)
            
            // Load initial chat history FROM THE SINGLETON
            var history = ChatService.getChatHistory() // <-- Use ChatService
            console.log("ChatScreen loading initial history from ChatService with " + history.length + " messages.")
            // Clear existing model before loading potentially stale data (important!)
            chatModel.clear()
            for (var i = 0; i < history.length; ++i) {
                chatModel.append(history[i])
            }
            if (history.length > 0 && chatView.autoScroll) {
                chatView.positionViewAtEnd()
            }
            
        } catch (e) {
            console.error("Error during ChatScreen Component.onCompleted:", e)
        }
    }
    
    // Optional: Connect to setting changes if needed at runtime
    Connections {
        target: SettingsService
        function onSettingChanged(path, value) {
            if (path === "chat.CHAT_CONFIG.show_input_box") {
                showInputBox = value
                console.log("ChatScreen updated showInputBox value:", value)
            }
        }
    }

    // Connections for ChatService specific signals (like history clear)
    // Target the ChatService singleton directly
    Connections {
        target: ChatService // <-- Use ChatService

        onHistoryCleared: {
            console.log("ChatScreen: Received historyCleared signal. Clearing model.")
            chatModel.clear()
        }

        // Handlers for real-time updates while screen is visible
        // These signals are emitted by the ChatService singleton
        onMessageReceived: function(text) {
            chatModel.append({"text": text, "isUser": false})
            if (chatView.autoScroll) {
                chatView.positionViewAtEnd()
            }
        }
        
        onMessageChunkReceived: function(text, isFinal) {
            var lastIndex = chatModel.count - 1
            if (lastIndex >= 0 && !chatModel.get(lastIndex).isUser) {
                chatModel.setProperty(lastIndex, "text", text)
            } else {
                chatModel.append({"text": text, "isUser": false})
            }
            
            if (isFinal) {
                console.log("Message stream complete")
            }
            
            if (chatView.autoScroll) {
                chatView.positionViewAtEnd()
            }
        }
        
        onConnectionStatusChanged: function(connected) {
            console.log("Connection changed => " + connected)
            chatScreen.title = connected ? "Chat Interface - Connected" : "Chat Interface - Disconnected"
        }
        
        onSttInputTextReceived: function(text) {
            inputField.text = text
        }
        
        onUserMessageAutoSubmitted: function(text) {
            chatModel.append({"text": text, "isUser": true})
            if (chatView.autoScroll) {
                chatView.positionViewAtEnd()
            }
        }
    }

    Rectangle {
        anchors.fill: parent
        color: "transparent"

        Rectangle {
            anchors.fill: parent
            anchors.margins: 8
            color: "transparent"
            
            ColumnLayout {
                anchors.fill: parent
                spacing: 8
                
                ListView {
                    id: chatView
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    spacing: 8
                    property bool autoScroll: true
                    
                    model: ListModel {
                        id: chatModel
                    }
                    
                    delegate: Rectangle {
                        width: ListView.view ? ListView.view.width - 16 : 0
                        color: model.isUser ? ThemeManager.user_bubble_color : ThemeManager.assistant_bubble_color
                        radius: 8
                        height: contentLabel.paintedHeight + 16
                        
                        anchors.right: model.isUser ? parent.right : undefined
                        anchors.left: model.isUser ? undefined : parent.left
                        anchors.rightMargin: model.isUser ? 8 : 0
                        anchors.leftMargin: model.isUser ? 0 : 8
                        
                        Text {
                            id: contentLabel
                            text: model.text
                            wrapMode: Text.Wrap
                            width: parent.width - 16
                            color: ThemeManager.text_primary_color
                            anchors.margins: 8
                            anchors.centerIn: parent
                        }
                    }
                    
                    MouseArea {
                        anchors.fill: parent
                        propagateComposedEvents: true
                        
                        onWheel: function(wheel) {
                            if (wheel.angleDelta.y < 0 && chatView.atYEnd) {
                                chatView.autoScroll = true
                            } else if (wheel.angleDelta.y > 0) {
                                chatView.autoScroll = false
                            }
                            wheel.accepted = false
                        }
                    }
                }
                
                RowLayout {
                    id: inputAreaRow
                    visible: showInputBox
                    
                    spacing: 8
                    TextField {
                        id: inputField
                        placeholderText: "Type your message..."
                        Layout.fillWidth: true
                        
                        background: Rectangle {
                            color: ThemeManager.input_background_color
                            radius: 4
                            border.width: 1
                            border.color: ThemeManager.input_border_color
                        }
                        
                        color: ThemeManager.text_primary_color
                        selectByMouse: true
                        
                        Keys.onPressed: function(event) {
                            if ((event.key === Qt.Key_Return || event.key === Qt.Key_Enter) && 
                                !(event.modifiers & Qt.ShiftModifier)) {
                                sendButton.clicked()
                                event.accepted = true
                            }
                        }
                    }
                    
                    Button {
                        id: sendButton
                        Layout.preferredWidth: 40
                        Layout.preferredHeight: 40
                        background: Rectangle {
                            color: "transparent"
                            radius: 5
                        }
                        onClicked: {
                            let userText = inputField.text.trim()
                            if (userText.length > 0) {
                                chatModel.append({ "text": userText, "isUser": true })
                                inputField.text = ""
                                ChatService.sendMessage(userText) // <-- Use ChatService
                                chatView.autoScroll = true
                                chatView.positionViewAtEnd()
                            }
                        }
                        
                        Image {
                            anchors.centerIn: parent
                            source: "../icons/send.svg"
                            width: 24
                            height: 24
                            sourceSize.width: 24
                            sourceSize.height: 24
                        }
                        
                        ToolTip.visible: hovered
                        ToolTip.text: "Send"
                    }
                }
            }
        }

        MouseArea {
            anchors.fill: parent
            z: -1
            onClicked: {
                inputField.forceActiveFocus()
            }
        }
    }
}

