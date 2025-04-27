import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Window 2.15
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
    
    // Properties for sound settings
    property string alarmSound: "alarm.raw"
    property string timerSound: "timer.raw"
    property bool alarmRepeatEnabled: false
    property bool timerRepeatEnabled: false
    property var availableSounds: ["alarm.raw", "timer.raw"]
    
    Component.onCompleted: {
        // Get initial values from the SettingsService
        try {
            autoSendEnabled = Boolean(SettingsService.getSetting('stt.STT_CONFIG.auto_submit_utterances', false))
            console.log("Auto Send setting initial value:", autoSendEnabled)
            showInputBoxEnabled = Boolean(SettingsService.getSetting('chat.CHAT_CONFIG.show_input_box', true))
            console.log("Show Input Box setting initial value:", showInputBoxEnabled)
            
            // Get sound settings with defaults
            alarmSound = SettingsService.getStringSetting('alarm.ALARM_CONFIG.sound_file', "alarm.raw")
            timerSound = SettingsService.getStringSetting('timer.TIMER_CONFIG.sound_file', "timer.raw")
            alarmRepeatEnabled = Boolean(SettingsService.getSetting('alarm.ALARM_CONFIG.repeat_sound', false))
            timerRepeatEnabled = Boolean(SettingsService.getSetting('timer.TIMER_CONFIG.repeat_sound', false))
            console.log("Loaded sound settings - Alarm:", alarmSound, "Timer:", timerSound)
            console.log("Repeat settings - Alarm:", alarmRepeatEnabled, "Timer:", timerRepeatEnabled)
            
            // Load available sounds from the system
            var soundsList = AudioManager.getAvailableSounds()
            if (soundsList && soundsList.length > 0) {
                availableSounds = soundsList
                console.log("Available sounds:", JSON.stringify(availableSounds))
            }
        } catch (e) {
            console.error("Error getting initial values from SettingsService:", e)
        }
    }
    
    // Function to save a sound setting
    function saveSoundSetting(path, value) {
        var success = SettingsService.setStringSetting(path, value)
        if (success) {
            console.log("Sound setting saved:", path, value)
        } else {
            console.error("Failed to save sound setting:", path, value)
        }
        return success
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
                                    var success = SettingsService.setSetting('stt.STT_CONFIG.auto_submit_utterances', checked)
                                    if (success) {
                                        autoSendEnabled = checked
                                        console.log("Auto Send setting changed via SettingsService to:", checked)

                                        // If Auto Send was turned OFF, force Show Input Box ON
                                        if (!checked) {
                                            console.log("Auto Send turned OFF, forcing Input Box to be shown.")
                                            var successShowInput = SettingsService.setSetting('chat.CHAT_CONFIG.show_input_box', true)
                                            if (successShowInput) {
                                                showInputBoxEnabled = true // Update local property
                                                console.log("Successfully forced Show Input Box ON.")
                                            } else {
                                                console.error("Failed to force Show Input Box ON when turning Auto Send OFF.")
                                                // Optionally revert autoSendSwitch state, but might be confusing
                                                // autoSendSwitch.checked = Qt.binding(function() { return autoSendEnabled; })
                                            }
                                        }
                                        // No need for the previous logic that checked current state
                                        
                                    } else {
                                        console.error("Failed to update Auto Send setting via SettingsService")
                                        autoSendSwitch.checked = Qt.binding(function() { return autoSendEnabled; })
                                    }
                                }
                            }
                        }
                    }
                }
                
                // UI Category Header (Renamed from Chat)
                Rectangle {
                    Layout.fillWidth: true
                    height: 50
                    color: ThemeManager.input_background_color
                    radius: 8
                    
                    Text {
                        anchors.centerIn: parent
                        text: "UI Settings" // Renamed from "Chat Settings"
                        font.pixelSize: 20
                        font.bold: true
                        color: ThemeManager.text_primary_color
                    }
                }
                
                // UI Settings Category (Renamed from Chat)
                Rectangle {
                    Layout.fillWidth: true
                    // Adjust height dynamically based on content, maybe using childrenRect? Or just add more fixed height.
                    // For simplicity now, let's increase fixed height guess slightly. We can refine later.
                    // It's better to use implicitHeight of the ColumnLayout inside.
                    // height: chatColumn.height + 32 // Old way
                    implicitHeight: uiColumn.implicitHeight + 32 // Calculate based on inner layout
                    Layout.preferredHeight: implicitHeight // Use implicitHeight for layout
                    color: ThemeManager.input_background_color
                    radius: 8
                    
                    ColumnLayout {
                        // id: chatColumn // Renamed ID
                        id: uiColumn
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.margins: 16
                        spacing: 8
                        
                        // Show Input Box Setting
                        RowLayout {
                            id: showInputBoxRow
                            Layout.fillWidth: true
                            spacing: 16
                            visible: autoSendSwitch.checked
                            
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
                                    } else {
                                        console.error("Failed to update Show Input Box setting via SettingsService")
                                        showInputBoxSwitch.checked = Qt.binding(function() { return showInputBoxEnabled; })
                                    }
                                }
                            }
                        }

                        // Fullscreen Setting 
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 16

                            Text {
                                text: "Fullscreen:"
                                color: ThemeManager.text_primary_color
                                Layout.preferredWidth: 150
                                elide: Text.ElideRight

                                ToolTip.visible: fullscreenMouseArea.containsMouse
                                ToolTip.text: "Toggle fullscreen mode and hide the title bar"

                                MouseArea {
                                    id: fullscreenMouseArea
                                    anchors.fill: parent
                                    hoverEnabled: true
                                }
                            }

                            Switch {
                                id: fullscreenSwitch
                                // Bind directly to the window visibility state
                                checked: Window.window ? Window.window.visibility === Window.FullScreen : false
                                
                                onToggled: {
                                    // Directly control window visibility
                                    if (Window.window) {
                                        Window.window.visibility = checked ? Window.FullScreen : Window.Windowed
                                        console.log("Fullscreen toggled from settings to:", checked)
                                    }
                                }
                            }
                        }
                        
                        // Auto Day/Night Theme Setting
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 16

                            Text {
                                text: "Auto Day/Night Theme:"
                                color: ThemeManager.text_primary_color
                                Layout.preferredWidth: 150
                                elide: Text.ElideRight

                                ToolTip.visible: autoThemeModeMouseArea.containsMouse
                                ToolTip.text: "Automatically switch between light and dark themes based on sunrise/sunset"

                                MouseArea {
                                    id: autoThemeModeMouseArea
                                    anchors.fill: parent
                                    hoverEnabled: true
                                }
                            }

                            Switch {
                                id: autoThemeModeSwitch
                                checked: ThemeManager.auto_theme_mode
                                
                                onToggled: {
                                    // Toggle auto theme mode
                                    var result = ThemeManager.toggle_auto_theme_mode()
                                    console.log("Auto theme mode toggled to:", result)
                                }
                            }
                        }
                    }
                }
                
                // Sound Settings Header
                Rectangle {
                    Layout.fillWidth: true
                    height: 50
                    color: ThemeManager.input_background_color
                    radius: 8
                    
                    Text {
                        anchors.centerIn: parent
                        text: "Sound Settings"
                        font.pixelSize: 20
                        font.bold: true
                        color: ThemeManager.text_primary_color
                    }
                }
                
                // Sound Settings Category
                Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: soundSettingsColumn.implicitHeight + 32
                    Layout.preferredHeight: implicitHeight
                    color: ThemeManager.input_background_color
                    radius: 8
                    
                    ColumnLayout {
                        id: soundSettingsColumn
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.margins: 16
                        spacing: 16
                        
                        // Alarm Sound Setting
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 8
                            
                            RowLayout {
                                Layout.fillWidth: true
                                
                                Text {
                                    text: "Alarm Sound:"
                                    color: ThemeManager.text_primary_color
                                    Layout.preferredWidth: 150
                                    elide: Text.ElideRight
                                    
                                    ToolTip.visible: alarmSoundMouseArea.containsMouse
                                    ToolTip.text: "Select the notification sound for alarms"
                                    
                                    MouseArea {
                                        id: alarmSoundMouseArea
                                        anchors.fill: parent
                                        hoverEnabled: true
                                    }
                                }
                                
                                ComboBox {
                                    id: alarmSoundComboBox
                                    model: availableSounds
                                    Layout.fillWidth: true
                                    currentIndex: availableSounds.indexOf(alarmSound)
                                    
                                    onActivated: {
                                        var selectedSound = model[currentIndex]
                                        if (selectedSound !== alarmSound) {
                                            if (saveSoundSetting('alarm.ALARM_CONFIG.sound_file', selectedSound)) {
                                                alarmSound = selectedSound
                                            } else {
                                                // Revert if save failed
                                                currentIndex = availableSounds.indexOf(alarmSound)
                                            }
                                        }
                                    }
                                }
                                
                                Button {
                                    id: alarmTestButton
                                    property bool playing: false
                                    text: playing ? "Stop" : "Test"
                                    Layout.preferredWidth: 80
                                    
                                    onClicked: {
                                        if (playing) {
                                            // Stop playing
                                            if (typeof AudioManager !== 'undefined' && typeof AudioManager.stop_playback === 'function') {
                                                AudioManager.stop_playback()
                                            }
                                            playing = false
                                        } else {
                                            // Start playing
                                            if (typeof AudioManager !== 'undefined' && typeof AudioManager.playSound === 'function') {
                                                AudioManager.playSound(alarmSoundComboBox.currentText)
                                            } else {
                                                // Fallback to regular alarm sound
                                                AudioManager.play_alarm_sound()
                                            }
                                            playing = true
                                        }
                                    }
                                }
                            }
                            
                            // Add Repeat Alarm Sound option
                            RowLayout {
                                Layout.fillWidth: true
                                Layout.leftMargin: 150 // Align with input field
                                spacing: 16
                                
                                Text {
                                    text: "Repeat Sound:"
                                    color: ThemeManager.text_primary_color
                                    Layout.preferredWidth: 120
                                    elide: Text.ElideRight
                                    
                                    ToolTip.visible: repeatAlarmMouseArea.containsMouse
                                    ToolTip.text: "Play alarm sound on repeat until dismissed"
                                    
                                    MouseArea {
                                        id: repeatAlarmMouseArea
                                        anchors.fill: parent
                                        hoverEnabled: true
                                    }
                                }
                                
                                Switch {
                                    id: repeatAlarmSwitch
                                    checked: alarmRepeatEnabled
                                    
                                    onToggled: {
                                        var success = SettingsService.setSetting('alarm.ALARM_CONFIG.repeat_sound', checked)
                                        if (success) {
                                            alarmRepeatEnabled = checked
                                            console.log("Alarm repeat sound setting changed to:", checked)
                                        } else {
                                            console.error("Failed to update alarm repeat sound setting")
                                            repeatAlarmSwitch.checked = Qt.binding(function() { return alarmRepeatEnabled; })
                                        }
                                    }
                                }
                            }
                        }
                        
                        // Timer Sound Setting
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 8
                            
                            RowLayout {
                                Layout.fillWidth: true
                                
                                Text {
                                    text: "Timer Sound:"
                                    color: ThemeManager.text_primary_color
                                    Layout.preferredWidth: 150
                                    elide: Text.ElideRight
                                    
                                    ToolTip.visible: timerSoundMouseArea.containsMouse
                                    ToolTip.text: "Select the notification sound for timers"
                                    
                                    MouseArea {
                                        id: timerSoundMouseArea
                                        anchors.fill: parent
                                        hoverEnabled: true
                                    }
                                }
                                
                                ComboBox {
                                    id: timerSoundComboBox
                                    model: availableSounds
                                    Layout.fillWidth: true
                                    currentIndex: availableSounds.indexOf(timerSound)
                                    
                                    onActivated: {
                                        var selectedSound = model[currentIndex]
                                        if (selectedSound !== timerSound) {
                                            if (saveSoundSetting('timer.TIMER_CONFIG.sound_file', selectedSound)) {
                                                timerSound = selectedSound
                                            } else {
                                                // Revert if save failed
                                                currentIndex = availableSounds.indexOf(timerSound)
                                            }
                                        }
                                    }
                                }
                                
                                Button {
                                    id: timerTestButton
                                    property bool playing: false
                                    text: playing ? "Stop" : "Test"
                                    Layout.preferredWidth: 80
                                    
                                    onClicked: {
                                        if (playing) {
                                            // Stop playing
                                            if (typeof AudioManager !== 'undefined' && typeof AudioManager.stop_playback === 'function') {
                                                AudioManager.stop_playback()
                                            }
                                            playing = false
                                        } else {
                                            // Start playing
                                            if (typeof AudioManager !== 'undefined' && typeof AudioManager.playSound === 'function') {
                                                AudioManager.playSound(timerSoundComboBox.currentText)
                                            } else {
                                                // Fallback to regular alarm sound
                                                AudioManager.play_alarm_sound()
                                            }
                                            playing = true
                                        }
                                    }
                                }
                            }
                            
                            // Add Repeat Timer Sound option
                            RowLayout {
                                Layout.fillWidth: true
                                Layout.leftMargin: 150 // Align with input field
                                spacing: 16
                                
                                Text {
                                    text: "Repeat Sound:"
                                    color: ThemeManager.text_primary_color
                                    Layout.preferredWidth: 120
                                    elide: Text.ElideRight
                                    
                                    ToolTip.visible: repeatTimerMouseArea.containsMouse
                                    ToolTip.text: "Play timer sound on repeat until dismissed"
                                    
                                    MouseArea {
                                        id: repeatTimerMouseArea
                                        anchors.fill: parent
                                        hoverEnabled: true
                                    }
                                }
                                
                                Switch {
                                    id: repeatTimerSwitch
                                    checked: timerRepeatEnabled
                                    
                                    onToggled: {
                                        var success = SettingsService.setSetting('timer.TIMER_CONFIG.repeat_sound', checked)
                                        if (success) {
                                            timerRepeatEnabled = checked
                                            console.log("Timer repeat sound setting changed to:", checked)
                                        } else {
                                            console.error("Failed to update timer repeat sound setting")
                                            repeatTimerSwitch.checked = Qt.binding(function() { return timerRepeatEnabled; })
                                        }
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
