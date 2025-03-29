import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import MyTheme 1.0

Item {
    id: settingsScreen
    property string title: "Settings"
    
    // Property to tell MainWindow which controls to load
    property string screenControls: "SettingsControls.qml"
    
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
                        text: "Application Settings"
                        font.pixelSize: 20
                        font.bold: true
                        color: ThemeManager.text_primary_color
                    }
                }
                
                // Dynamic settings categories from model
                Repeater {
                    model: settingsModel // This will be registered in main.py
                    
                    delegate: Rectangle {
                        Layout.fillWidth: true
                        height: categoryColumn.height + 32
                        color: ThemeManager.input_background_color
                        radius: 8
                        
                        ColumnLayout {
                            id: categoryColumn
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.top: parent.top
                            anchors.margins: 16
                            spacing: 8
                            
                            Text {
                                text: model.displayName
                                font.pixelSize: 16
                                font.bold: true
                                color: ThemeManager.text_primary_color
                            }
                            
                            // Settings within this category
                            Repeater {
                                model: model.settings
                                
                                delegate: RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 16
                                    
                                    Text {
                                        text: modelData.displayName + ":"
                                        color: ThemeManager.text_primary_color
                                        Layout.preferredWidth: 150
                                        elide: Text.ElideRight
                                        
                                        ToolTip.visible: descriptionMouseArea.containsMouse
                                        ToolTip.text: modelData.description
                                        
                                        MouseArea {
                                            id: descriptionMouseArea
                                            anchors.fill: parent
                                            hoverEnabled: true
                                        }
                                    }
                                    
                                    // Dynamic component based on setting type
                                    Loader {
                                        Layout.fillWidth: true
                                        
                                        sourceComponent: {
                                            switch(modelData.valueType) {
                                                case "bool":
                                                    return switchComponent
                                                case "int":
                                                case "float":
                                                    return sliderComponent
                                                case "string":
                                                    return textFieldComponent
                                                default:
                                                    return null
                                            }
                                        }
                                        
                                        property var setting: modelData
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
    
    // Components for different setting types
    Component {
        id: switchComponent
        
        Switch {
            checked: setting.value
            onCheckedChanged: {
                if (checked !== setting.value) {
                    setting.value = checked
                }
            }
        }
    }
    
    Component {
        id: sliderComponent
        
        ColumnLayout {
            spacing: 4
            
            Slider {
                id: slider
                Layout.fillWidth: true
                from: {
                    if (setting.valueType === "int") {
                        if (setting.name === "sample_rate") return 8000
                        if (setting.name === "block_size") return 1000
                        if (setting.name === "endpointing") return 100
                        return 0
                    }
                    return 0
                }
                to: {
                    if (setting.valueType === "int") {
                        if (setting.name === "sample_rate") return 48000
                        if (setting.name === "block_size") return 8000
                        if (setting.name === "endpointing") return 2000
                        return 100
                    }
                    return 1
                }
                stepSize: setting.valueType === "int" ? 1 : 0.1
                value: setting.value
                
                onMoved: {
                    if (setting.valueType === "int") {
                        setting.value = Math.round(value)
                    } else {
                        setting.value = value
                    }
                }
            }
            
            Text {
                text: setting.valueType === "int" ? Math.round(slider.value).toString() : slider.value.toFixed(1)
                color: ThemeManager.text_secondary_color
                font.pixelSize: 12
                Layout.alignment: Qt.AlignRight
            }
        }
    }
    
    Component {
        id: textFieldComponent
        
        TextField {
            text: setting.value || ""
            placeholderText: "Enter value..."
            
            onEditingFinished: {
                if (text !== setting.value) {
                    setting.value = text
                }
            }
            
            background: Rectangle {
                color: ThemeManager.input_background_color
                border.width: 1
                border.color: ThemeManager.input_border_color
                radius: 4
            }
            
            color: ThemeManager.text_primary_color
        }
    }
}
