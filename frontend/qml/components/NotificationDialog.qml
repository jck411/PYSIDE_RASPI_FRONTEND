import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import MyTheme 1.0

// Reusable notification dialog component with consistent styling
Dialog {
    id: notificationDialog
    modal: true
    closePolicy: Popup.NoAutoClose // Prevent closing by clicking outside or pressing Escape
    
    // Center in parent and set size
    anchors.centerIn: parent
    width: Math.min(parent.width * 0.85, 420)
    height: 220
    
    // Solid black overlay for modal background
    Overlay.modal: Rectangle {
        color: "black" 
        opacity: 1.0 // Ensure full opacity
    }
    
    // Custom properties
    property string notificationTitle: "Notification"
    property string mainText: ""
    property string subText: ""
    property bool hasSecondaryButton: false
    property string primaryButtonText: "Dismiss"
    property string secondaryButtonText: "Secondary"
    property var primaryAction: function() { close(); }
    property var secondaryAction: null
    
    // Footer with one or two buttons
    footer: Rectangle {
        height: 70
        color: "transparent"
        
        Row {
            anchors.centerIn: parent
            width: parent.width * 0.9
            height: 46
            spacing: parent.width * 0.05
            
            // Secondary button (conditional)
            Button {
                text: notificationDialog.secondaryButtonText
                width: notificationDialog.hasSecondaryButton ? parent.width * 0.47 : 0
                height: parent.height
                visible: notificationDialog.hasSecondaryButton
                
                contentItem: Text {
                    text: parent.text
                    font.pixelSize: 16
                    font.bold: true
                    color: ThemeManager.accent_text_color
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                
                background: Rectangle {
                    radius: 10
                    color: ThemeManager.accent_color
                }
                
                onClicked: {
                    if (notificationDialog.secondaryAction) {
                        notificationDialog.secondaryAction()
                    }
                }
            }
            
            // Primary button
            Button {
                text: notificationDialog.primaryButtonText
                width: notificationDialog.hasSecondaryButton ? parent.width * 0.47 : parent.width
                height: parent.height
                
                contentItem: Text {
                    text: parent.text
                    font.pixelSize: 16
                    font.bold: true
                    color: ThemeManager.accent_text_color
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                
                background: Rectangle {
                    radius: 10
                    color: ThemeManager.accent_color
                }
                
                onClicked: {
                    notificationDialog.primaryAction()
                }
            }
        }
    }
    
    // Apply theme styling directly using standard Dialog properties
    background: Rectangle {
        color: ThemeManager.dialog_background_color
        radius: 12
        border.color: ThemeManager.border_color
        border.width: 1
    }
    
    // Header with rounded corners
    header: Rectangle {
        color: ThemeManager.dialog_header_color
        height: 55
        radius: 12
        
        // Only make the top corners rounded
        Rectangle {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            height: parent.height / 2
            color: parent.color
        }
        
        Label {
            text: notificationDialog.title
            color: ThemeManager.text_primary_color
            font.pixelSize: 20
            font.bold: true
            anchors.centerIn: parent
        }
    }
    
    // Content area with main and sub text
    contentItem: Item {
        Column {
            anchors.centerIn: parent
            width: parent.width - 32
            spacing: 20
            
            Text {
                text: notificationDialog.mainText
                font.pixelSize: 32
                font.bold: true
                color: ThemeManager.text_primary_color
                horizontalAlignment: Text.AlignHCenter
                width: parent.width
                wrapMode: Text.WordWrap
            }
            
            Text {
                text: notificationDialog.subText
                font.pixelSize: 22
                color: ThemeManager.text_secondary_color
                horizontalAlignment: Text.AlignHCenter
                width: parent.width
                visible: text !== ""
            }
        }
    }
} 