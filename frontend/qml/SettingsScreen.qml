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
    
    // Store the current value here
    property bool autoSendEnabled: false
    
    Component.onCompleted: {
        // Get the initial value from the SettingsService
        try {
            autoSendEnabled = SettingsService.getSetting('stt.STT_CONFIG.auto_submit_utterances', false)
            console.log("Auto Send setting initial value:", autoSendEnabled)
        } catch (e) {
            console.error("Error getting Auto Send value from SettingsService:", e)
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
