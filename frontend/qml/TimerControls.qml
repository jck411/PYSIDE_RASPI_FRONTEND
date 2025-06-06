import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import MyServices 1.0

BaseControls {
    id: timerControls
    
    // Reference to the main StackView for navigation
    property var mainStackView: null
    
    // Create navigation buttons when component completes
    Component.onCompleted: {
        // Clock button
        var clockButton = createButton(
            "../icons/clock.svg", 
            "Clock", 
            24
        );
        
        if (clockButton) {
            clockButton.onClicked.connect(function() {
                if (mainStackView) {
                    mainStackView.replace("ClockScreen.qml")
                } else {
                    console.error("TimerControls: mainStackView reference is null!");
                }
            });
        }
        
        // Alarm button
        var alarmButton = createButton(
            "../icons/alarms_active.svg", 
            "Alarms", 
            24
        );
        
        if (alarmButton) {
            alarmButton.onClicked.connect(function() {
                if (mainStackView) {
                    mainStackView.replace("AlarmScreen.qml")
                } else {
                    console.error("TimerControls: mainStackView reference is null!");
                }
            });
        }
        
        // Timer button (shows current screen but can be used to return to timer view)
        var timerButton = createButton(
            "../icons/timer.svg", 
            "Timer", 
            24
        );
        
        if (timerButton) {
            timerButton.onClicked.connect(function() {
                if (mainStackView) {
                    mainStackView.replace("TimerScreen.qml")
                } else {
                    console.error("TimerControls: mainStackView reference is null!");
                }
            });
        }
    }
} 