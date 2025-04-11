import QtQuick 2.15
import QtQuick.Controls 2.15
import MyTheme 1.0

// Component for multi-day events that span across multiple cells
Rectangle {
    id: multiDayEvent
    
    // Event data properties
    property var eventData: null
    property string title: eventData ? (eventData.title || "Untitled") : "Untitled"
    property color eventColor: eventData ? (eventData.color || "#7847f5") : "#7847f5"
    
    // Layout properties
    property int startCol: eventData ? eventData.startCol : 0
    property int endCol: eventData ? eventData.endCol : 0
    property int row: eventData ? eventData.row : 0
    property int totalColumns: 7 // Default for week view
    
    // Visual properties
    property int eventHeight: 20
    property bool rounded: true
    property int cornerRadius: rounded ? 2 : 0
    
    // Calculate width based on column span
    property int columnWidth: parent.width / totalColumns
    property int eventSpan: endCol - startCol + 1
    
    // Position calculations
    x: startCol * columnWidth
    y: row * (eventHeight + 2) // +2 for spacing
    width: eventSpan * columnWidth - 2 // -2 for spacing
    height: eventHeight
    
    // Visual appearance
    radius: cornerRadius
    color: eventColor
    
    // Emit signal when clicked
    signal eventClicked(var eventData)
    
    // Event title
    Text {
        anchors {
            left: parent.left
            right: parent.right
            verticalCenter: parent.verticalCenter
            leftMargin: 4
            rightMargin: 4
        }
        text: title
        color: "white"
        font.pixelSize: 11
        elide: Text.ElideRight
    }
    
    // Make events clickable
    MouseArea {
        anchors.fill: parent
        onClicked: {
            multiDayEvent.eventClicked(eventData)
        }
        
        // Hover effect
        hoverEnabled: true
        onEntered: parent.opacity = 0.9
        onExited: parent.opacity = 1.0
    }
} 