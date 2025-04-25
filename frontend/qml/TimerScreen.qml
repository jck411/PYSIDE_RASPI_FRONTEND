import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import MyTheme 1.0
import MyServices 1.0

BaseScreen {
    id: timerScreen
    
    // Set the controls file for this screen
    screenControls: "TimerControls.qml"
    title: "Timer"
    
    // Timer properties
    property bool isTimerRunning: false
    property bool isTimerPaused: false
    property int timerHours: 0
    property int timerMinutes: 0
    property int timerSeconds: 0
    property int remainingSeconds: 0
    
    // Format time as MM:SS or HH:MM:SS
    function formatTime(totalSeconds) {
        const hours = Math.floor(totalSeconds / 3600)
        const minutes = Math.floor((totalSeconds % 3600) / 60)
        const seconds = totalSeconds % 60
        
        if (hours > 0) {
            return String(hours).padStart(2, '0') + ":" + 
                   String(minutes).padStart(2, '0') + ":" + 
                   String(seconds).padStart(2, '0')
        } else {
            return String(minutes).padStart(2, '0') + ":" + 
                   String(seconds).padStart(2, '0')
        }
    }
    
    // Start the timer
    function startTimer() {
        if (!isTimerRunning && !isTimerPaused) {
            // Calculate total seconds
            const totalSeconds = timerHours * 3600 + timerMinutes * 60 + timerSeconds
            
            // Make sure we have a non-zero time
            if (totalSeconds <= 0) return
            
            remainingSeconds = totalSeconds
            isTimerRunning = true
            isTimerPaused = false
            countdownTimer.start()
        } else if (isTimerPaused) {
            // Resume from paused state
            isTimerPaused = false
            isTimerRunning = true
            countdownTimer.start()
        }
    }
    
    // Pause the timer
    function pauseTimer() {
        if (isTimerRunning) {
            isTimerPaused = true
            isTimerRunning = false
            countdownTimer.stop()
        }
    }
    
    // Stop and reset the timer
    function stopTimer() {
        isTimerRunning = false
        isTimerPaused = false
        countdownTimer.stop()
        remainingSeconds = 0
    }
    
    // Timer finished notification
    function showTimerFinishedNotification() {
        timerNotification.open()
        // Play alarm sound if AudioManager is available
        if (typeof AudioManager !== 'undefined' && typeof AudioManager.play_alarm_sound === 'function') {
            AudioManager.play_alarm_sound()
        }
    }
    
    // Main countdown timer
    Timer {
        id: countdownTimer
        interval: 1000
        repeat: true
        onTriggered: {
            if (remainingSeconds > 0) {
                remainingSeconds--
            }
            
            if (remainingSeconds <= 0) {
                stopTimer()
                showTimerFinishedNotification()
            }
        }
    }
    
    // Main layout
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 30
        
        // Active timer display (only visible when timer is running or paused)
        Rectangle {
            Layout.alignment: Qt.AlignCenter
            Layout.preferredWidth: parent.width * 0.8
            Layout.preferredHeight: 120
            color: ThemeManager.background_secondary_color
            radius: 10
            visible: isTimerRunning || isTimerPaused
            
            Text {
                id: activeTimerDisplay
                anchors.centerIn: parent
                text: formatTime(remainingSeconds)
                font.pixelSize: 60
                font.bold: true
                color: ThemeManager.text_primary_color
            }
        }
        
        // Timer status text (only when running/paused)
        Text {
            text: isTimerPaused ? "Timer Paused" : (isTimerRunning ? "Timer Running" : "")
            font.pixelSize: 20
            color: ThemeManager.text_secondary_color
            Layout.alignment: Qt.AlignHCenter
            visible: isTimerRunning || isTimerPaused
        }
        
        // Timer setup panel (similar to alarm edit panel, only visible when not running)
        Rectangle {
            id: timerSetupPanel
            Layout.fillWidth: true
            Layout.preferredHeight: timerSetupContent.height + 20
            color: ThemeManager.background_color
            visible: !isTimerRunning && !isTimerPaused
            radius: 10
            
            ColumnLayout {
                id: timerSetupContent
                width: parent.width
                anchors.centerIn: parent
                spacing: 20
                
                // Header
                Text {
                    text: "Set Timer"
                    font.pixelSize: 24
                    font.bold: true
                    color: ThemeManager.text_primary_color
                    Layout.alignment: Qt.AlignHCenter
                }
                
                // Time selection with Tumblers
                Rectangle {
                    Layout.alignment: Qt.AlignHCenter
                    Layout.preferredWidth: parent.width * 0.8
                    Layout.preferredHeight: 150
                    color: ThemeManager.background_secondary_color
                    radius: 10
                    
                    RowLayout {
                        anchors.centerIn: parent
                        spacing: 20
                        
                        // Hour tumbler
                        Tumbler {
                            id: hoursTumbler
                            model: 24
                            visibleItemCount: 3
                            height: 120
                            width: 80
                            
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
                                timerHours = currentIndex
                            }
                        }
                        
                        // Separator
                        Text {
                            text: ":"
                            font.pixelSize: 40
                            font.bold: true
                            color: ThemeManager.text_primary_color
                        }
                        
                        // Minute tumbler
                        Tumbler {
                            id: minutesTumbler
                            model: 60
                            visibleItemCount: 3
                            height: 120
                            width: 80
                            
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
                                timerMinutes = currentIndex
                            }
                        }
                        
                        // Separator
                        Text {
                            text: ":"
                            font.pixelSize: 40
                            font.bold: true
                            color: ThemeManager.text_primary_color
                        }
                        
                        // Second tumbler
                        Tumbler {
                            id: secondsTumbler
                            model: 60
                            visibleItemCount: 3
                            height: 120
                            width: 80
                            
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
                                timerSeconds = currentIndex
                            }
                        }
                    }
                }
                
                // Quick preset buttons row
                Rectangle {
                    Layout.alignment: Qt.AlignHCenter
                    Layout.preferredWidth: parent.width * 0.8
                    Layout.preferredHeight: 100
                    color: ThemeManager.background_secondary_color
                    radius: 10
                    
                    GridLayout {
                        anchors.fill: parent
                        anchors.margins: 5
                        columnSpacing: 5
                        rowSpacing: 5
                        columns: 3
                        
                        // 10 seconds preset
                        Button {
                            text: "10 sec"
                            Layout.fillWidth: true
                            
                            contentItem: Text {
                                text: parent.text
                                font: parent.font
                                color: ThemeManager.text_primary_color
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                            
                            background: Rectangle {
                                radius: 8
                                color: ThemeManager.background_secondary_color
                            }
                            
                            onClicked: {
                                timerHours = 0
                                timerMinutes = 0
                                timerSeconds = 10
                                hoursTumbler.currentIndex = 0
                                minutesTumbler.currentIndex = 0
                                secondsTumbler.currentIndex = 10
                            }
                        }
                        
                        // 30 seconds preset
                        Button {
                            text: "30 sec"
                            Layout.fillWidth: true
                            
                            contentItem: Text {
                                text: parent.text
                                font: parent.font
                                color: ThemeManager.text_primary_color
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                            
                            background: Rectangle {
                                radius: 8
                                color: ThemeManager.background_secondary_color
                            }
                            
                            onClicked: {
                                timerHours = 0
                                timerMinutes = 0
                                timerSeconds = 30
                                hoursTumbler.currentIndex = 0
                                minutesTumbler.currentIndex = 0
                                secondsTumbler.currentIndex = 30
                            }
                        }
                        
                        // 1 minute preset
                        Button {
                            text: "1 min"
                            Layout.fillWidth: true
                            
                            contentItem: Text {
                                text: parent.text
                                font: parent.font
                                color: ThemeManager.text_primary_color
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                            
                            background: Rectangle {
                                radius: 8
                                color: ThemeManager.background_secondary_color
                            }
                            
                            onClicked: {
                                timerHours = 0
                                timerMinutes = 1
                                timerSeconds = 0
                                hoursTumbler.currentIndex = 0
                                minutesTumbler.currentIndex = 1
                                secondsTumbler.currentIndex = 0
                            }
                        }
                        
                        // 5 minute preset
                        Button {
                            text: "5 min"
                            Layout.fillWidth: true
                            
                            contentItem: Text {
                                text: parent.text
                                font: parent.font
                                color: ThemeManager.text_primary_color
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                            
                            background: Rectangle {
                                radius: 8
                                color: ThemeManager.background_secondary_color
                            }
                            
                            onClicked: {
                                timerHours = 0
                                timerMinutes = 5
                                timerSeconds = 0
                                hoursTumbler.currentIndex = 0
                                minutesTumbler.currentIndex = 5
                                secondsTumbler.currentIndex = 0
                            }
                        }
                        
                        // 10 minute preset
                        Button {
                            text: "10 min"
                            Layout.fillWidth: true
                            
                            contentItem: Text {
                                text: parent.text
                                font: parent.font
                                color: ThemeManager.text_primary_color
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                            
                            background: Rectangle {
                                radius: 8
                                color: ThemeManager.background_secondary_color
                            }
                            
                            onClicked: {
                                timerHours = 0
                                timerMinutes = 10
                                timerSeconds = 0
                                hoursTumbler.currentIndex = 0
                                minutesTumbler.currentIndex = 10
                                secondsTumbler.currentIndex = 0
                            }
                        }
                        
                        // 30 minute preset
                        Button {
                            text: "30 min"
                            Layout.fillWidth: true
                            
                            contentItem: Text {
                                text: parent.text
                                font: parent.font
                                color: ThemeManager.text_primary_color
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                            
                            background: Rectangle {
                                radius: 8
                                color: ThemeManager.background_secondary_color
                            }
                            
                            onClicked: {
                                timerHours = 0
                                timerMinutes = 30
                                timerSeconds = 0
                                hoursTumbler.currentIndex = 0
                                minutesTumbler.currentIndex = 30
                                secondsTumbler.currentIndex = 0
                            }
                        }
                    }
                }
                
                // Action buttons row at the bottom
                RowLayout {
                    Layout.alignment: Qt.AlignHCenter
                    Layout.preferredWidth: parent.width * 0.6
                    Layout.topMargin: 20
                    spacing: 20
                    
                    // Start button
                    Button {
                        text: "Start"
                        Layout.preferredWidth: 120
                        Layout.alignment: Qt.AlignHCenter
                        
                        contentItem: Text {
                            text: parent.text
                            font: parent.font
                            color: ThemeManager.accent_text_color
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                        
                        background: Rectangle {
                            radius: 8
                            color: ThemeManager.accent_color
                        }
                        
                        onClicked: startTimer()
                    }
                }
            }
        }
        
        // Running/Paused timer control buttons
        RowLayout {
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: parent.width * 0.8
            spacing: 20
            visible: isTimerRunning || isTimerPaused
            
            // Pause button (only visible when timer is running)
            Button {
                text: "Pause"
                Layout.preferredWidth: 120
                Layout.alignment: Qt.AlignHCenter
                visible: isTimerRunning && !isTimerPaused
                
                contentItem: Text {
                    text: parent.text
                    font: parent.font
                    color: ThemeManager.accent_text_color
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                
                background: Rectangle {
                    radius: 8
                    color: ThemeManager.accent_color
                }
                
                onClicked: pauseTimer()
            }
            
            // Resume button (only visible when timer is paused)
            Button {
                text: "Resume"
                Layout.preferredWidth: 120
                Layout.alignment: Qt.AlignHCenter
                visible: isTimerPaused
                
                contentItem: Text {
                    text: parent.text
                    font: parent.font
                    color: ThemeManager.accent_text_color
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                
                background: Rectangle {
                    radius: 8
                    color: ThemeManager.accent_color
                }
                
                onClicked: startTimer()
            }
            
            // Reset button (always visible when timer is running or paused)
            Button {
                text: "Reset"
                Layout.preferredWidth: 120
                Layout.alignment: Qt.AlignHCenter
                
                contentItem: Text {
                    text: parent.text
                    font: parent.font
                    color: ThemeManager.accent_text_color
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                
                background: Rectangle {
                    radius: 8
                    color: ThemeManager.accent_color
                }
                
                onClicked: stopTimer()
            }
        }
        
        // Spacer to push content to the top
        Item {
            Layout.fillHeight: true
        }
    }
    
    // Timer finished notification dialog
    Dialog {
        id: timerNotification
        title: "Timer Finished"
        modal: true
        closePolicy: Popup.NoAutoClose // Prevent closing by clicking outside or pressing Escape
        
        // Center in parent
        x: (parent.width - width) / 2
        y: (parent.height - height) / 2
        
        // Size
        width: Math.min(parent.width - 40, 400)
        height: 200
        
        // Dim the background with a semi-transparent overlay
        Overlay.modal: Rectangle {
            color: Qt.rgba(0, 0, 0, 0.6) // Semi-transparent black
        }
        
        // Apply theme
        palette.window: ThemeManager.dialog_background_color
        palette.windowText: ThemeManager.text_primary_color
        palette.button: ThemeManager.button_color
        palette.buttonText: ThemeManager.button_text_color
        
        background: Rectangle {
            color: ThemeManager.dialog_background_color
            radius: 10
            border.color: ThemeManager.border_color
            border.width: 1
        }
        
        header: Rectangle {
            color: ThemeManager.dialog_header_color
            height: 50
            radius: 10
            
            // Only make the top corners rounded
            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                height: parent.height / 2
                color: parent.color
            }
            
            Label {
                text: timerNotification.title
                color: ThemeManager.text_primary_color
                font.pixelSize: 18
                font.bold: true
                anchors.centerIn: parent
            }
        }
        
        // Content area
        contentItem: Item {
            ColumnLayout {
                anchors.fill: parent
                spacing: 20
                
                Item { Layout.fillHeight: true }
                
                Text {
                    text: "Time's up!"
                    font.pixelSize: 28
                    font.bold: true
                    color: ThemeManager.text_primary_color
                    Layout.alignment: Qt.AlignHCenter
                }
                
                Item { Layout.fillHeight: true }
            }
        }
        
        // Dialog buttons
        footer: RowLayout {
            spacing: 10
            Layout.fillWidth: true
            
            Button {
                text: "Dismiss"
                Layout.fillWidth: true
                
                contentItem: Text {
                    text: parent.text
                    font: parent.font
                    color: ThemeManager.accent_text_color
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                
                background: Rectangle {
                    radius: 8
                    color: ThemeManager.accent_color
                }
                
                onClicked: {
                    timerNotification.close()
                    // Stop audio if AudioManager is available
                    if (typeof AudioManager !== 'undefined' && typeof AudioManager.stop_playback === 'function') {
                        AudioManager.stop_playback()
                    }
                }
            }
        }
    }
} 