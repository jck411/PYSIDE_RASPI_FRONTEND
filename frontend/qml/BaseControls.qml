import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Row {
    id: baseControls
    spacing: 5  // Reduced from 8 to 5 to match the main navigation spacing
    
    // Reference to the screen this controls
    property var screen
    
    // Function to create a standard control button
    function createButton(iconSource, tooltipText, size) {
        var component = Qt.createComponent("TouchFriendlyButton.qml");
        if (component.status === Component.Ready) {
            var button = component.createObject(baseControls, {
                "source": iconSource,
                "text": tooltipText
            });
            return button;
        }
        console.error("Error creating button:", component.errorString());
        return null;
    }
    
    // Common spacer used in most control layouts (moved to the end)
    Item {
        id: spacer
        Layout.fillWidth: true
    }
}
