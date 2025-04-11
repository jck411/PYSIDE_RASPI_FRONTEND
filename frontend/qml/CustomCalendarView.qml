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
    
    // Height for multi-day event row
    property int multiDayEventHeight: 25
    
    // Spacing between multi-day events
    property int multiDayEventSpacing: 5
    
    // Margin at top of cells for multi-day events
    property int multiDayTopMargin: 5
    
    // Show placeholder if no data
    Text {
        anchors.centerIn: parent
        text: "No calendar data available"
        color: ThemeManager.text_secondary_color
        font.pixelSize: 16
        visible: !model || model.length === 0
    }
    
    // Process model to extract all multi-day events for the entire view
    property var allMultiDayEvents: {
        if (!model || model.length === 0) return [];
        
        // Collect all multi-day events
        var events = [];
        
        // First, identify all multi-day events and their spans
        for (var i = 0; i < model.length; i++) {
            var day = model[i];
            if (day && day.multiDayEvents) {
                for (var j = 0; j < day.multiDayEvents.length; j++) {
                    var event = day.multiDayEvents[j];
                    if (event && event.id) {
                        // Find if we've already processed this event
                        var existingIdx = -1;
                        for (var k = 0; k < events.length; k++) {
                            if (events[k].id === event.id) {
                                existingIdx = k;
                                break;
                            }
                        }
                        
                        if (existingIdx < 0) {
                            // New event - add it with position info
                            events.push({
                                id: event.id,
                                title: event.title,
                                color: event.color || "#7847f5",
                                startCol: i,
                                endCol: event.isEnd ? i : model.length - 1,
                                row: 0  // Will be assigned in layout phase
                            });
                        } else {
                            // Update end column if this day marks the end
                            if (event.isEnd) {
                                events[existingIdx].endCol = i;
                            }
                        }
                    }
                }
            }
        }
        
        // Sort events by duration (longest first) to improve layout
        events.sort(function(a, b) {
            var spanA = a.endCol - a.startCol;
            var spanB = b.endCol - b.startCol;
            return spanB - spanA;  // Descending order
        });
        
        // Assign rows to avoid overlapping (simple greedy algorithm)
        var usedRows = [];
        for (var m = 0; m < events.length; m++) {
            var evt = events[m];
            var row = 0;
            
            // Find first available row
            while (true) {
                var rowAvailable = true;
                for (var n = 0; n < usedRows.length; n++) {
                    var usedEvt = usedRows[n];
                    if (usedEvt.row === row &&
                        !(evt.endCol < usedEvt.startCol || evt.startCol > usedEvt.endCol)) {
                        rowAvailable = false;
                        break;
                    }
                }
                
                if (rowAvailable) {
                    break;
                }
                row++;
            }
            
            evt.row = row;
            usedRows.push(evt);
        }
        
        return events;
    }
    
    // Calculate maximum row needed for multi-day events
    property int maxMultiDayRow: {
        if (!allMultiDayEvents || allMultiDayEvents.length === 0) return 0;
        
        var maxRow = 0;
        for (var i = 0; i < allMultiDayEvents.length; i++) {
            maxRow = Math.max(maxRow, allMultiDayEvents[i].row);
        }
        return maxRow + 1; // +1 because rows are 0-indexed
    }
    
    // Height needed for the multi-day events section
    property int multiDayEventsHeight: maxMultiDayRow * (multiDayEventHeight + multiDayEventSpacing)
    
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
        
        // Day cells with events - wrapped in ScrollView for vertical scrolling
        ScrollView {
            id: dayCellsScrollView
            width: parent.width
            height: parent.height - dayHeadersRow.height
            clip: true
            ScrollBar.vertical.policy: ScrollBar.AsNeeded
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
            
            // Container to allow content to expand vertically
            Item {
                id: dayCellsContainer
                width: parent.width
                // Dynamic height based on content, allowing expansion
                implicitHeight: dayRowLayout.implicitHeight
                
                // Row of day cells
                Row {
                    id: dayRowLayout
                    width: parent.width
                    
                    // Repeater for day cells
                    Repeater {
                        model: customCalendarView.model
                        
                        Rectangle {
                            id: customDayCell
                            width: dayCellsContainer.width / customCalendarView.model.length
                            // Reserve space for multi-day events at the top
                            property int topReservedHeight: customCalendarView.multiDayEventsHeight + customCalendarView.multiDayTopMargin
                            // Allow rectangle to expand based on content height
                            implicitHeight: topReservedHeight + eventsColumn.height + 10 // Add padding
                            height: Math.max(implicitHeight, parent.height)
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
                            
                            // Events column - single-day events only
                            Column {
                                id: eventsColumn
                                anchors.left: parent.left
                                anchors.right: parent.right
                                anchors.top: parent.top
                                anchors.topMargin: customDayCell.topReservedHeight
                                anchors.margins: 5
                                spacing: 5
                                
                                // Single-day events only
                                Repeater {
                                    model: modelData.events ? modelData.events.filter(e => !e.is_multi_day) : []
                                    
                                    Rectangle {
                                        width: eventsColumn.width
                                        // Allow dynamic height based on content
                                        height: eventSingleDayContent.height + 8 // Add padding
                                        color: modelData.color || "#4287f5" // Default color for regular events
                                        radius: 4
                                        
                                        Column {
                                            id: eventSingleDayContent
                                            anchors.left: parent.left
                                            anchors.right: parent.right
                                            anchors.top: parent.top
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
                                            
                                            // Title - allow more lines to show full content
                                            Text {
                                                width: parent.width
                                                text: modelData.title
                                                font.pixelSize: 14
                                                font.bold: true
                                                wrapMode: Text.WordWrap
                                                elide: Text.ElideRight
                                                // Increase to show more content
                                                maximumLineCount: 10
                                                color: "white"
                                            }
                                        }
                                    }
                                }
                                
                                // Empty state message when no events
                                Text {
                                    visible: (!modelData.events || modelData.events.filter(e => !e.is_multi_day).length === 0)
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
                
                // Multi-day events layer that sits on top of the cells but visually inside them
                // This is a separate visual layer to allow events to span across cell borders
                Item {
                    id: multiDayEventsLayer
                    anchors.fill: parent
                    
                    // Render each multi-day event
                    Repeater {
                        model: customCalendarView.allMultiDayEvents
                        
                        Rectangle {
                            id: multiDayEvent
                            // Calculate position based on the day columns
                            x: modelData.startCol * (parent.width / customCalendarView.model.length)
                            y: customCalendarView.multiDayTopMargin + 
                               modelData.row * (customCalendarView.multiDayEventHeight + customCalendarView.multiDayEventSpacing)
                            // Calculate width based on day span
                            width: (modelData.endCol - modelData.startCol + 1) * (parent.width / customCalendarView.model.length) - 4
                            height: customCalendarView.multiDayEventHeight
                            color: modelData.color
                            radius: 4
                            // Ensure multi-day events appear on top of cell borders
                            z: 1
                            
                            // Event content
                            RowLayout {
                                anchors.fill: parent
                                anchors.margins: 4
                                spacing: 4
                                
                                // Color indicator
                                Rectangle {
                                    width: 4
                                    Layout.fillHeight: true
                                    color: Qt.darker(multiDayEvent.color, 1.2)
                                    radius: 2
                                }
                                
                                // Event title
                                Text {
                                    Layout.fillWidth: true
                                    text: modelData.title
                                    font.pixelSize: 12
                                    font.bold: true
                                    elide: Text.ElideRight
                                    color: "white"
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
