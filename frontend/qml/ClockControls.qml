import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import MyServices 1.0

BaseControls {
    id: clockControls
    
    // Reference to the main StackView for navigation
    property var mainStackView: null
    
    // Create the Show Alarms button when component completes
    Component.onCompleted: {
        // Show Alarms button
        var alarmButton = createButton(
            "../icons/alarms_active.svg", 
            "Show Alarms", 
            24
        );
        
        if (alarmButton) {
            alarmButton.onClicked.connect(function() {
                if (mainStackView) {
                    // Use string path directly, no try/catch or extra logging
                    mainStackView.replace("AlarmScreen.qml")
                } else {
                    console.error("ClockControls: mainStackView reference is null!");
                }
            });
        }
    }
}
