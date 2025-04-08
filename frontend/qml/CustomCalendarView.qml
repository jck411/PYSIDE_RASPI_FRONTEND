import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import MyTheme 1.0

// Custom calendar view for showing week, 3-day, and day views
Item {
    id: customCalendarView
    
    // Properties
    property var model: [] // Range days model from controller
    property bool debugOutput: false // For development debugging
    
    // Show placeholder if no data
    Text {
        anchors.centerIn: parent
        text: "No calendar data available"
        color: ThemeManager.text_secondary_color
        font.pixelSize: 16
        visible: !model || model.length === 0
    }
    
    // Main layout
    Column {
        anchors.fill: parent
        spacing: 0
        visible: model && model.length > 0
        
        // Day headers row
        Row {
            id: dayHeadersRow
            width: parent.width
            height: 50
            
            // Repeater for day headers
            Repeater {
                model: customCalendarView.model
                
                Rectangle {
                    width: dayHeadersRow.width / customCalendarView.model.length
                    height: parent.height
                    color: ThemeManager.background_color
                    border.color: ThemeManager.input_border_color
                    border.width: 1
                    
                    Column {
                        anchors.centerIn: parent
                        spacing: 2
                        
                        // Day name (Mon, Tue, etc)
                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            text: modelData.dayName
                            font.pixelSize: 14
                            font.bold: true
                            color: ThemeManager.text_primary_color
                        }
                        
                        // Date (e.g., "15")
                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            text: modelData.day
                            font.pixelSize: 18
                            color: modelData.isToday ? ThemeManager.button_primary_color : ThemeManager.text_primary_color
                            font.bold: modelData.isToday
                        }
                    }
                }
            }
        }
        
        // Day cells with events
        Item {
            id: dayCellsContainer
            width: parent.width
            height: parent.height - dayHeadersRow.height
            
            // Row of day cells
            Row {
                anchors.fill: parent
                
                // Repeater for day cells
                Repeater {
                    model: customCalendarView.model
                    
                    Rectangle {
                        id: customDayCell
                        width: dayCellsContainer.width / customCalendarView.model.length
                        height: parent.height
                        color: modelData.isToday ? 
                              Qt.rgba(
                                ThemeManager.button_primary_color.r,
                                ThemeManager.button_primary_color.g,
                                ThemeManager.button_primary_color.b,
                                0.1
                              ) : 
                              ThemeManager.background_color
                        border.color: ThemeManager.input_border_color
                        border.width: 1
                        
                        // Mouse area to handle clicks/taps on day cells
                        MouseArea {
                            anchors.fill: parent
                            onClicked: {
                                if (modelData && modelData.date_str) {
                                    // Navigate to day view for this date
                                    CalendarController.goToSpecificDate(modelData.date_str, "day");
                                }
                            }
                            // Visual feedback on hover
                            hoverEnabled: true
                            
                            // Tooltip shows that clicking opens day view
                            ToolTip {
                                visible: parent.containsMouse
                                text: "View events for this day"
                                delay: 500
                            }
                        }
                        
                        // Scroll view for events
                        ScrollView {
                            id: eventsScrollView
                            anchors.fill: parent
                            anchors.margins: 5
                            clip: true
                            ScrollBar.vertical.policy: ScrollBar.AsNeeded
                            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                            
                            // Events column
                            Column {
                                id: eventsColumn
                                width: eventsScrollView.width
                                spacing: 5
                                
                                // Multi-day events
                                Repeater {
                                    model: modelData.multiDayEvents || []
                                    
                                    Rectangle {
                                        width: eventsColumn.width
                                        height: 60
                                        color: modelData.color || "#7847f5" // Default color for multi-day
                                        radius: 4
                                        
                                        Column {
                                            anchors.fill: parent
                                            anchors.margins: 4
                                            spacing: 2
                                            
                                            // Show continuation indicators
                                            Row {
                                                visible: !modelData.isStart || !modelData.isEnd
                                                width: parent.width
                                                spacing: 5
                                                
                                                Text {
                                                    visible: !modelData.isStart
                                                    text: "←"
                                                    font.pixelSize: 10
                                                    color: "white"
                                                }
                                                
                                                Text {
                                                    text: !modelData.isStart ? "continues from previous day" : 
                                                         !modelData.isEnd ? "continues to next day" : ""
                                                    font.pixelSize: 10
                                                    color: "white"
                                                }
                                                
                                                Text {
                                                    visible: !modelData.isEnd
                                                    text: "→"
                                                    font.pixelSize: 10
                                                    color: "white"
                                                }
                                            }
                                            
                                            // Title
                                            Text {
                                                width: parent.width
                                                text: modelData.title
                                                font.pixelSize: 14
                                                font.bold: true
                                                wrapMode: Text.WordWrap
                                                elide: Text.ElideRight
                                                maximumLineCount: 2
                                                color: "white"
                                            }
                                        }
                                    }
                                }
                                
                                // Single-day events
                                Repeater {
                                    model: modelData.events || []
                                    
                                    Rectangle {
                                        width: eventsColumn.width
                                        height: 60
                                        color: modelData.color || "#4287f5" // Default color for regular events
                                        radius: 4
                                        
                                        Column {
                                            anchors.fill: parent
                                            anchors.margins: 4
                                            spacing: 2
                                            
                                            // Time if available
                                            Text {
                                                visible: modelData.timeDisplay && modelData.timeDisplay !== ""
                                                text: modelData.timeDisplay || ""
                                                font.pixelSize: 12
                                                font.bold: true
                                                color: "white"
                                            }
                                            
                                            // Title
                                            Text {
                                                width: parent.width
                                                text: modelData.title
                                                font.pixelSize: 14
                                                font.bold: true
                                                wrapMode: Text.WordWrap
                                                elide: Text.ElideRight
                                                maximumLineCount: 2
                                                color: "white"
                                            }
                                        }
                                    }
                                }
                                
                                // Empty state message when no events
                                Text {
                                    visible: (!modelData.events || modelData.events.length === 0) && 
                                            (!modelData.multiDayEvents || modelData.multiDayEvents.length === 0)
                                    text: "No events"
                                    color: ThemeManager.text_secondary_color
                                    font.pixelSize: 14
                                    width: eventsColumn.width
                                    horizontalAlignment: Text.AlignHCenter
                                    topPadding: 20
                                }
                            }
                        }
                    }
                }
            }
        }
    }
} 