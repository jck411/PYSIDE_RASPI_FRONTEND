import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import MyTheme 1.0
import MyServices 1.0
import "components"

BaseScreen {
    id: timerScreen
    
    // Set the controls file for this screen
    screenControls: "TimerControls.qml"
    title: "Timer"
    
    // Temporary storage for tumbler values before setting the timer
    property int currentHours: 0
    property int currentMinutes: 0
    property int currentSeconds: 0
    property string currentName: "Timer" // Default name
    
    // Connect to TimerController signals for notification
    Connections {
        target: TimerController
        function onTimer_finished(timerName) {
            // Use the name from the signal
            timerNotification.mainText = timerName + " finished!"
            
            // Play alarm sound before showing notification
            if (typeof AudioManager !== 'undefined' && typeof AudioManager.play_alarm_sound === 'function') {
                AudioManager.play_alarm_sound()
            } else {
                console.warn("AudioManager not available or play_alarm_sound not found.")
            }
            
            // Open notification after setting up the sound
            timerNotification.open()
        }
        // Optional: You might want to react to other signals like timer_updated
        // function onTimer_updated() { ... }
        // function onTimer_state_changed() { ... }
    }
    
    // Main layout
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 20 // Reduced spacing slightly
        
        // Timer Name Display (Visible when active)
        Text {
            Layout.alignment: Qt.AlignCenter
            text: TimerController.name // Display name from controller
            font.pixelSize: 24
            font.bold: true
            color: ThemeManager.text_primary_color
            visible: TimerController.is_running || TimerController.is_paused
            elide: Text.ElideRight
            maximumLineCount: 1
            width: parent.width * 0.8 // Ensure it doesn't overflow
        }
        
        // Active timer display (only visible when timer is running or paused)
        Rectangle {
            Layout.alignment: Qt.AlignCenter
            Layout.preferredWidth: parent.width * 0.8
            Layout.preferredHeight: 120
            color: ThemeManager.background_secondary_color
            radius: 10
            // Bind visibility to TimerController state
            visible: TimerController.is_running || TimerController.is_paused
            
            Text {
                id: activeTimerDisplay
                anchors.centerIn: parent
                // Bind text to TimerController's formatted string property
                text: TimerController.remaining_time_str
                font.pixelSize: 60
                font.bold: true
                color: ThemeManager.text_primary_color
            }
        }
        
        // Timer status text (only when running/paused)
        Text {
            // Bind text and visibility to TimerController state
            text: TimerController.is_paused ? "Timer Paused" : (TimerController.is_running ? "Timer Running" : "")
            font.pixelSize: 20
            color: ThemeManager.text_secondary_color
            Layout.alignment: Qt.AlignHCenter
            visible: TimerController.is_running || TimerController.is_paused
        }
        
        // Timer setup panel (visible when timer is not running or paused)
        Rectangle {
            id: timerSetupPanel
            Layout.fillWidth: true
            Layout.preferredHeight: timerSetupContent.implicitHeight + 40 // Adjust height dynamically
            color: ThemeManager.background_color
            // Bind visibility to TimerController state
            visible: !TimerController.is_running && !TimerController.is_paused
            radius: 10
            Layout.topMargin: 10 // Add some margin
            
            ColumnLayout {
                id: timerSetupContent
                width: parent.width
                anchors.horizontalCenter: parent.horizontalCenter // Center content
                anchors.top: parent.top
                anchors.topMargin: 20
                anchors.bottom: parent.bottom
                anchors.bottomMargin: 20
                spacing: 20
                
                // Header
                Text {
                    text: "Set Timer"
                    font.pixelSize: 24
                    font.bold: true
                    color: ThemeManager.text_primary_color
                    Layout.alignment: Qt.AlignHCenter
                }
                
                // Timer Name Input
                TextField {
                    id: timerNameInput
                    Layout.alignment: Qt.AlignHCenter
                    Layout.preferredWidth: parent.width * 0.8
                    placeholderText: "Timer Name (optional)"
                    text: timerScreen.currentName // Bind to temp property
                    color: ThemeManager.text_primary_color
                    background: Rectangle {
                        color: ThemeManager.background_secondary_color
                        radius: 5
                        border.color: ThemeManager.accent_color // Add slight border
                        border.width: 1
                    }
                    onTextChanged: {
                        timerScreen.currentName = text // Update temp property
                    }
                }
                
                // Time selection with Tumblers
                Rectangle {
                    Layout.alignment: Qt.AlignHCenter
                    Layout.preferredWidth: parent.width * 0.9 // Slightly wider for better fit
                    Layout.preferredHeight: 150
                    color: ThemeManager.background_secondary_color
                    radius: 10
                    
                    RowLayout {
                        anchors.centerIn: parent
                        spacing: 10 // Reduced tumbler spacing
                        
                        // Hour tumbler
                        Tumbler {
                            id: hoursTumbler
                            model: 24
                            visibleItemCount: 3
                            height: 120
                            width: 80
                            currentIndex: timerScreen.currentHours // Bind to temp property
                            
                            delegate: Text {
                                text: String(modelData).padStart(2, '0')
                                color: ThemeManager.text_primary_color
                                font.pixelSize: hoursTumbler.currentIndex === index ? 30 : 20
                                font.bold: hoursTumbler.currentIndex === index
                                opacity: 1.0 - Math.abs(Tumbler.displacement) / (hoursTumbler.visibleItemCount / 2)
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                            
                            onCurrentIndexChanged: {
                                timerScreen.currentHours = currentIndex // Update temp property
                            }
                        }
                        
                        // Separator
                        Text {
                            text: ":"
                            font.pixelSize: 40; font.bold: true
                            color: ThemeManager.text_primary_color
                            Layout.alignment: Qt.AlignVCenter
                        }
                        
                        // Minute tumbler
                        Tumbler {
                            id: minutesTumbler
                            model: 60
                            visibleItemCount: 3
                            height: 120
                            width: 80
                            currentIndex: timerScreen.currentMinutes // Bind to temp property
                            
                            delegate: Text {
                                text: String(modelData).padStart(2, '0')
                                color: ThemeManager.text_primary_color
                                font.pixelSize: minutesTumbler.currentIndex === index ? 30 : 20
                                font.bold: minutesTumbler.currentIndex === index
                                opacity: 1.0 - Math.abs(Tumbler.displacement) / (minutesTumbler.visibleItemCount / 2)
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                            
                            onCurrentIndexChanged: {
                                timerScreen.currentMinutes = currentIndex // Update temp property
                            }
                        }
                        
                        // Separator
                        Text {
                            text: ":"
                            font.pixelSize: 40; font.bold: true
                            color: ThemeManager.text_primary_color
                            Layout.alignment: Qt.AlignVCenter
                        }
                        
                        // Second tumbler
                        Tumbler {
                            id: secondsTumbler
                            model: 60
                            visibleItemCount: 3
                            height: 120
                            width: 80
                            currentIndex: timerScreen.currentSeconds // Bind to temp property
                            
                            delegate: Text {
                                text: String(modelData).padStart(2, '0')
                                color: ThemeManager.text_primary_color
                                font.pixelSize: secondsTumbler.currentIndex === index ? 30 : 20
                                font.bold: secondsTumbler.currentIndex === index
                                opacity: 1.0 - Math.abs(Tumbler.displacement) / (secondsTumbler.visibleItemCount / 2)
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                            
                            onCurrentIndexChanged: {
                                timerScreen.currentSeconds = currentIndex // Update temp property
                            }
                        }
                    } // End RowLayout (Tumblers)
                } // End Rectangle (Tumblers Container)
            } // End ColumnLayout (timerSetupContent)
        } // End Rectangle (timerSetupPanel)
        
        // --- Action Buttons Row ---
        RowLayout {
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: parent.width * 0.8
            spacing: 20
            // Show this row only when NOT running AND NOT paused (Setup Mode)
            // AND at least one time value is greater than 0
            visible: !TimerController.is_running && !TimerController.is_paused &&
                    (timerScreen.currentHours > 0 || timerScreen.currentMinutes > 0 || timerScreen.currentSeconds > 0)

            // Start Button (Setup Mode)
            Button {
                text: "Start Timer"
                Layout.fillWidth: false // Don't fill width
                Layout.preferredWidth: 200 // Set a fixed width
                Layout.preferredHeight: 40 // Make slightly smaller
                Layout.alignment: Qt.AlignHCenter
                // Remove enabled condition since row is already hidden when timer is 0

                contentItem: Text {
                    text: parent.text
                    font.pixelSize: 16; font.bold: true // Slightly smaller text
                    color: ThemeManager.accent_text_color
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }

                background: Rectangle {
                    radius: 8
                    color: ThemeManager.accent_color
                }

                onClicked: {
                    // Set the timer first using current values from screen
                    TimerController.set_timer(timerScreen.currentHours,
                                             timerScreen.currentMinutes,
                                             timerScreen.currentSeconds,
                                             timerScreen.currentName)
                    // Then start it
                    TimerController.start_timer()
                }
            }
        }

        // --- Active Timer Controls Row ---
        RowLayout {
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: parent.width * 0.8
            spacing: 15
            // Show this row only when running OR paused
            visible: TimerController.is_running || TimerController.is_paused

            // Pause Button (Visible when running)
            Button {
                text: "Pause"
                Layout.fillWidth: true
                Layout.preferredHeight: 45
                visible: TimerController.is_running && !TimerController.is_paused

                contentItem: Text {
                    text: parent.text
                    font.pixelSize: 16; font.bold: true
                    color: ThemeManager.text_primary_color
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                
                background: Rectangle { 
                    radius: 8
                    color: ThemeManager.background_secondary_color
                    border.color: ThemeManager.border_color
                    border.width: 1
                }

                onClicked: TimerController.pause_timer()
            }

            // Resume Button (Visible when paused)
            Button {
                text: "Resume"
                Layout.fillWidth: true
                Layout.preferredHeight: 45
                visible: TimerController.is_paused

                contentItem: Text {
                    text: parent.text
                    font.pixelSize: 16; font.bold: true
                    color: ThemeManager.text_primary_color
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                
                background: Rectangle { 
                    radius: 8
                    color: ThemeManager.background_secondary_color
                    border.color: ThemeManager.border_color
                    border.width: 1
                }

                onClicked: TimerController.start_timer() // Start resumes if paused
            }

            // Extend Button (+30 sec) - Example
            Button {
                text: "+30s"
                Layout.preferredWidth: 80 // Fixed width for extend
                Layout.preferredHeight: 45

                contentItem: Text {
                    text: parent.text
                    font.pixelSize: 16; font.bold: true
                    color: ThemeManager.text_primary_color
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                
                background: Rectangle { 
                    radius: 8
                    color: ThemeManager.background_secondary_color
                    border.color: ThemeManager.border_color
                    border.width: 1
                }

                onClicked: TimerController.extend_timer(30)
            }

            // Stop/Cancel Button
            Button {
                text: "Cancel"
                Layout.fillWidth: true
                Layout.preferredHeight: 45

                contentItem: Text {
                    text: parent.text
                    font.pixelSize: 16; font.bold: true
                    color: ThemeManager.text_primary_color
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                
                background: Rectangle { 
                    radius: 8
                    color: ThemeManager.background_secondary_color
                    border.color: ThemeManager.border_color
                    border.width: 1
                }

                onClicked: TimerController.stop_timer()
            }
        }

        // Spacer to push controls down if needed, or adjust layout spacing
        Item { Layout.fillHeight: true }
    } // End Main ColumnLayout
    
    // Use the shared NotificationDialog component instead of custom implementation
    NotificationDialog {
        id: timerNotification
        title: "Timer Finished"
        
        // Set dialog content
        mainText: "Your timer has finished."
        subText: ""
        
        // Configure button
        primaryButtonText: "Dismiss"
        hasSecondaryButton: false
        
        // Define action directly
        primaryAction: function() {
            // Close the dialog
            close()
        }
        
        // Audio management - only place to stop audio
        onClosed: {
            if (typeof AudioManager !== 'undefined' && typeof AudioManager.stop_playback === 'function') {
                AudioManager.stop_playback()
            }
        }
    }
} 