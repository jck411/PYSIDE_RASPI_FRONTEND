import QtQuick 2.15
import QtQuick.Controls 2.15
import MyTheme 1.0
// QtQuick.Effects import removed

Item {
    id: root
    
    // Properties
    property alias source: image.source
    property alias text: tooltip.text
    property bool checked: false
    property bool checkable: false
    signal clicked()
    
    // More compact size
    implicitWidth: 50
    implicitHeight: 40
    
    // Visual background rectangle
    Rectangle {
        id: background
        anchors.fill: parent
        anchors.margins: 2
        color: touchArea.pressed ? Qt.rgba(ThemeManager.button_primary_color.r, 
                                         ThemeManager.button_primary_color.g, 
                                         ThemeManager.button_primary_color.b, 0.3) 
                                : (root.checked ? Qt.rgba(ThemeManager.button_primary_color.r, 
                                                       ThemeManager.button_primary_color.g, 
                                                       ThemeManager.button_primary_color.b, 0.2) 
                                              : "transparent")
        radius: 8
        
        // Add animation for smoother visual feedback
        Behavior on color {
            ColorAnimation { duration: 100 }
        }
    }
    
    // Icon image
    Image {
        id: image
        anchors.centerIn: parent
        width: 24
        height: 24
        sourceSize.width: 24
        sourceSize.height: 24
        
        // layer.enabled removed
        // layer.effect removed
    }
    
    // DropShadow effect removed
    
    // Touch area with ripple effect
    MouseArea {
        id: touchArea
        anchors.fill: parent
        anchors.margins: -10  // Extend touch area beyond visual boundaries
        hoverEnabled: true
        
        onPressed: {
            if (ripple.visible) ripple.restart()
        }
        
        onClicked: {
            if (root.checkable) {
                root.checked = !root.checked
            }
            root.clicked()
        }
    }
    
    // Visual ripple effect for touch feedback
    Rectangle {
        id: ripple
        property real size: 0
        
        function restart() {
            size = 0
            visible = true
            rippleAnimation.restart()
        }
        
        x: (parent.width - width) / 2
        y: (parent.height - height) / 2
        width: size
        height: size
        radius: size / 2
        color: Qt.rgba(ThemeManager.button_primary_color.r, 
                     ThemeManager.button_primary_color.g, 
                     ThemeManager.button_primary_color.b, 0.4)
        visible: false
        
        NumberAnimation {
            id: rippleAnimation
            target: ripple
            property: "size"
            from: 5
            to: root.width * 1.5
            duration: 300
            easing.type: Easing.OutQuad
            onFinished: ripple.visible = false
        }
    }
    
    // Tooltip
    ToolTip {
        id: tooltip
        visible: touchArea.containsMouse
        delay: 500
    }
}