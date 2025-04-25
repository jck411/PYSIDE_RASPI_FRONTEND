import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import MyServices 1.0

BaseControls {
    id: alarmControls
    
    // Reference to the main StackView for navigation
    property var mainStackView: null
    
    // Initialize controls when component is completed
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
                    console.error("AlarmControls: mainStackView reference is null!");
                }
            });
        }
        
        // Alarm button (shows current screen but can be used to refresh alarm view)
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
                    console.error("AlarmControls: mainStackView reference is null!");
                }
            });
        }
        
        // Timer button
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
                    console.error("AlarmControls: mainStackView reference is null!");
                }
            });
        }
    }
    
    // Function to create a standard control button
    function createButton(iconSource, tooltipText, size) {
        var component = Qt.createComponent("TouchFriendlyButton.qml");
        if (component.status === Component.Ready) {
            var button = component.createObject(alarmControls, {
                "source": iconSource,
                "text": tooltipText
            });
            return button;
        }
        console.error("Error creating button:", component.errorString());
        return null;
    }
    
    // No need for findAlarmScreen function as we navigate directly using mainStackView
}
