import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

BaseControls {
    id: weatherControls
    
    // Weather-specific controls can be added here
    
    // Example of how to add a weather-specific button:
    // Component.onCompleted: {
    //     var refreshButton = createButton("../icons/refresh.svg", "Refresh Weather", 24);
    //     if (refreshButton) {
    //         refreshButton.onClicked.connect(function() {
    //             // Refresh weather data
    //         });
    //     }
    // }
}
