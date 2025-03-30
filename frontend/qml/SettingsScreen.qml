import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import MyTheme 1.0
import MyServices 1.0

Item {
    id: settingsScreen
    property string title: "Settings"
    
    // Property to tell MainWindow which controls to load
    property string screenControls: "SettingsControls.qml"
    
    // Store the current value for STT Auto Send
    property bool autoSendEnabled: false
    // Store the current value for Show Input Box
    property bool showInputBoxEnabled: true
    
    Component.onCompleted: {
        // Get initial values from the SettingsService
        try {
            autoSendEnabled = SettingsService.getSetting('stt.STT_CONFIG.auto_submit_utterances', false)
            console.log("Auto Send setting initial value:", autoSendEnabled)
            showInputBoxEnabled = SettingsService.getSetting('chat.CHAT_CONFIG.show_input_box', true)
            console.log("Show Input Box setting initial value:", showInputBoxEnabled)
        } catch (e) {
            console.error("Error getting initial values from SettingsService:", e)
        }
    }
    
    Rectangle {
        anchors.fill: parent
        color: ThemeManager.background_color

        ScrollView {
            id: settingsScrollView
            anchors.fill: parent
            anchors.margins: 16
            clip: true
            
            ColumnLayout {
                width: settingsScreen.width - 32
                spacing: 16
                
                // Header
                Rectangle {
                    Layout.fillWidth: true
                    height: 50
                    color: ThemeManager.input_background_color
                    radius: 8
                    
                    Text {
                        anchors.centerIn: parent
                        text: "Speech-to-Text Settings"
                        font.pixelSize: 20
                        font.bold: true
                        color: ThemeManager.text_primary_color
                    }
                }
                
                // Speech-to-Text Category
                Rectangle {
                    Layout.fillWidth: true
                    height: sttColumn.height + 32
                    color: ThemeManager.input_background_color
                    radius: 8
                    
                    ColumnLayout {
                        id: sttColumn
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.margins: 16
                        spacing: 8
                        
                        // Only keep the Auto Send setting
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 16
                            
                            Text {
                                text: "Auto Send:"
                                color: ThemeManager.text_primary_color
                                Layout.preferredWidth: 150
                                elide: Text.ElideRight
                                
                                ToolTip.visible: autoSendMouseArea.containsMouse
                                ToolTip.text: "Automatically submit complete utterances to chat without putting them in the input box"
                                
                                MouseArea {
                                    id: autoSendMouseArea
                                    anchors.fill: parent
                                    hoverEnabled: true
                                }
                            }
                            
                            Switch {
                                id: autoSendSwitch
                                checked: autoSendEnabled
                                
                                onToggled: {
                                    // Call the SettingsService method
                                    var success = SettingsService.setSetting('stt.STT_CONFIG.auto_submit_utterances', checked)
                                    if (success) {
                                        autoSendEnabled = checked
                                        console.log("Auto Send setting changed via SettingsService to:", checked)
                                    } else {
                                        console.error("Failed to update Auto Send setting via SettingsService")
                                        // Revert the switch position without triggering events
                                        autoSendSwitch.checked = Qt.binding(function() { return autoSendEnabled; })
                                    }
                                }
                            }
                        }
                    }
                }
                
                // Chat Category Header
                Rectangle {
                    Layout.fillWidth: true
                    height: 50
                    color: ThemeManager.input_background_color
                    radius: 8
                    
                    Text {
                        anchors.centerIn: parent
                        text: "Chat Settings"
                        font.pixelSize: 20
                        font.bold: true
                        color: ThemeManager.text_primary_color
                    }
                }
                
                // Chat Settings Category
                Rectangle {
                    Layout.fillWidth: true
                    height: chatColumn.height + 32
                    color: ThemeManager.input_background_color
                    radius: 8
                    
                    ColumnLayout {
                        id: chatColumn
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.margins: 16
                        spacing: 8
                        
                        // Show Input Box Setting
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 16
                            
                            Text {
                                text: "Show Input Box:"
                                color: ThemeManager.text_primary_color
                                Layout.preferredWidth: 150
                                elide: Text.ElideRight
                                
                                ToolTip.visible: showInputBoxMouseArea.containsMouse
                                ToolTip.text: "Show or hide the text input field at the bottom of the chat screen"
                                
                                MouseArea {
                                    id: showInputBoxMouseArea
                                    anchors.fill: parent
                                    hoverEnabled: true
                                }
                            }
                            
                            Switch {
                                id: showInputBoxSwitch
                                checked: showInputBoxEnabled
                                
                                onToggled: {
                                    // Call the SettingsService method to update the show/hide setting
                                    var successShowHide = SettingsService.setSetting('chat.CHAT_CONFIG.show_input_box', checked)
                                    if (successShowHide) {
                                        showInputBoxEnabled = checked
                                        console.log("Show Input Box setting changed via SettingsService to:", checked)
                                        
                                        // ---> NEW LOGIC: Force Auto Send ON if Input Box is hidden <---
                                        if (!checked) { // If the input box is now hidden (checked is false)
                                            console.log("Input box hidden, ensuring Auto Send is ON.")
                                            var currentAutoSend = SettingsService.getSetting('stt.STT_CONFIG.auto_submit_utterances', false)
                                            if (!currentAutoSend) {
                                                var successAutoSend = SettingsService.setSetting('stt.STT_CONFIG.auto_submit_utterances', true)
                                                if (successAutoSend) {
                                                    console.log("Successfully forced Auto Send ON.")
                                                    // Update the local property and UI state for the Auto Send switch
                                                    autoSendEnabled = true 
                                                    // autoSendSwitch.checked will update automatically due to binding
                                                } else {
                                                    console.error("CRITICAL: Failed to force Auto Send ON when hiding input box! STT might not work correctly.")
                                                    // Optional: Could revert the hide action here, but might be confusing.
                                                    // showInputBoxSwitch.checked = Qt.binding(function() { return showInputBoxEnabled; }) 
                                                }
                                            } else {
                                                console.log("Auto Send was already ON.")
                                            }
                                        }
                                        // ---> END NEW LOGIC <---
                                        
                                    } else {
                                        console.error("Failed to update Show Input Box setting via SettingsService")
                                        // Revert the switch position without triggering events
                                        showInputBoxSwitch.checked = Qt.binding(function() { return showInputBoxEnabled; })
                                    }
                                }
                            }
                        }
                    }
                }
                
                // Spacer at bottom
                Item {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    height: 20
                }
            }
        }
    }
}
