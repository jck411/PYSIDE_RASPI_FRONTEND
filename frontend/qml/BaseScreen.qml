import QtQuick 2.15
import QtQuick.Controls 2.15
import MyTheme 1.0

Item {
    id: baseScreen
    
    // Common property for all screens to specify their controls
    property string screenControls: ""
    
    // Common property for screen title
    property string title: ""
    
    /* 
     * NOTE: All screens that extend BaseScreen should also define:
     * property string filename: "ScreenName.qml"
     * 
     * This helps MainWindow identify screens more efficiently with direct property access
     * rather than parsing URLs or using object names.
     */
    
    // Base rectangle that fills the screen with theme background color
    Rectangle {
        id: screenBackground
        anchors.fill: parent
        color: ThemeManager.background_color
        
        // Content placeholder - to be overridden by child screens
        Item {
            id: contentArea
            anchors.fill: parent
            anchors.margins: 8
        }
    }
    
    // Common mouse area for handling clicks on empty areas
    MouseArea {
        anchors.fill: parent
        z: -1
        // Can be used by child screens to handle background clicks
        onClicked: {
            // Default behavior can be overridden
        }
    }
}
