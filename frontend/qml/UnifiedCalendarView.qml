import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import MyTheme 1.0

// Unified calendar view that handles both day cells and multi-day events
Item {
    id: unifiedCalendarView
    
    // Properties
    property var model: null // Calendar data model from controller
    property int cellWidth: width / 7
    property int cellHeight: height / 6
    
    // Height allocated for day numbers at the top of each cell
    property int dayNumberHeight: 20
    
    // Height for each multi-day event row
    property int multiDayEventHeight: 18
    
    // Spacing between event rows
    property int eventSpacing: 2
    
    // Maximum number of multi-day event rows to display per week
    property int maxMultiDayRows: 4
    
    // Maximum number of single-day events to display per day
    property int maxEventsPerDay: 5
    
    // Color for the "more events" indicator
    property color moreEventsColor: "#777"
    
    // Disable debug output for production
    property bool debugOutput: false
    
    // Keep old weeks during model change to prevent flickering
    property var oldWeeks: []
    
    // Set up weeks array when model changes
    property var weeks: []
    
    // Timer to process model changes safely
    Timer {
        id: modelChangeTimer
        interval: 10
        running: false
        repeat: false
        onTriggered: processModelChange()
    }
    
    // Safely process model changes
    function processModelChange() {
        // Save current weeks as oldWeeks
        oldWeeks = weeks
        
        // Defensive check for model validity
        if (!model) {
            if (debugOutput) console.log("Calendar model is null or undefined")
            weeks = []
            return
        }
        
        if (model && model.length > 0) {
            // Group days into weeks
            var newWeeks = []
            for (let i = 0; i < 6; i++) {
                let weekDays = model.slice(i * 7, (i + 1) * 7)
                if (weekDays.length > 0) {
                    newWeeks.push(weekDays)
                }
            }
            weeks = newWeeks
        } else {
            weeks = []
        }
    }
    
    // Handle model changes by using a timer to decouple from binding loop
    onModelChanged: modelChangeTimer.restart()
    
    // Show loading indicator during model processing
    Rectangle {
        anchors.centerIn: parent
        width: 160
        height: 40
        color: ThemeManager.background_color
        border.color: ThemeManager.input_border_color
        border.width: 1
        radius: 5
        visible: modelChangeTimer.running
        
        RowLayout {
            anchors.centerIn: parent
            spacing: 10
            
            BusyIndicator {
                running: modelChangeTimer.running
                Layout.preferredWidth: 24
                Layout.preferredHeight: 24
            }
            
            Text {
                text: "Updating calendar..."
                color: ThemeManager.text_primary_color
                font.pixelSize: 14
            }
        }
    }
    
    // Show placeholder if no data
    Text {
        anchors.centerIn: parent
        text: "No calendar data available"
        color: ThemeManager.text_secondary_color
        font.pixelSize: 16
        visible: !model || model.length === 0 || weeks.length === 0
    }
    
    // Main column of week rows
    Column {
        id: weeksColumn
        anchors.fill: parent
        spacing: 0
        visible: model && model.length > 0 && weeks.length > 0
        
        // Render each week
        Repeater {
            model: unifiedCalendarView.weeks
            
            // Week container
            Item {
                id: weekContainer
                width: unifiedCalendarView.width
                height: unifiedCalendarView.cellHeight
                
                // Week index for reference
                property int weekIndex: index
                
                // Days in this week
                property var weekDays: modelData || []
                
                // Multi-day events for this week - safely handle missing data
                property var multiDayEvents: {
                    if (weekDays && weekDays.length > 0 && weekDays[0]) {
                        // Check if we have the multi_day_events property directly on the day
                        if (weekDays[0].multi_day_events) {
                            return weekDays[0].multi_day_events;
                        }
                        // Or if it's in a week_data property
                        else if (weekDays[0].week_data && weekDays[0].week_data.multi_day_events) {
                            return weekDays[0].week_data.multi_day_events;
                        }
                    }
                    return []; // Safe default
                }
                
                // Day cells in the week
                Row {
                    anchors.fill: parent
                    spacing: 0
                    
                    // Render each day cell
                    Repeater {
                        model: weekContainer.weekDays
                        
                        // Individual day cell
                        Rectangle {
                            id: dayCell
                            width: unifiedCalendarView.cellWidth
                            height: unifiedCalendarView.cellHeight
                            color: modelData && modelData.isCurrentMonth ? 
                                   ThemeManager.background_color : 
                                   ThemeManager.input_background_color
                            
                            // Special border for today's date
                            border.color: modelData && modelData.isToday ? 
                                         ThemeManager.button_primary_color : 
                                         ThemeManager.input_border_color
                            border.width: modelData && modelData.isToday ? 2 : 1
                            
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
                            
                            // Highlight rectangle for today
                            Rectangle {
                                visible: modelData && modelData.isToday
                                anchors.fill: parent
                                anchors.margins: 2
                                color: "transparent"
                                border.color: ThemeManager.button_primary_color
                                border.width: 1
                                radius: 2
                            }
                            
                            // Day number
                            Text {
                                id: dayNumberText
                                anchors {
                                    top: parent.top
                                    left: parent.left
                                    right: parent.right
                                    margins: 4
                                }
                                height: unifiedCalendarView.dayNumberHeight
                                text: modelData ? modelData.dayNumber : ""
                                font.pixelSize: 12
                                font.bold: modelData && modelData.isToday
                                color: modelData && modelData.isToday ? 
                                       ThemeManager.button_primary_color : 
                                       (modelData && modelData.isCurrentMonth ? 
                                        ThemeManager.text_primary_color : 
                                        ThemeManager.text_secondary_color)
                                horizontalAlignment: Text.AlignHCenter
                            }
                            
                            // Calculate how many multi-day event rows we need to reserve space for
                            property int reservedMultiDayRows: {
                                if (!modelData || !modelData.day_position || weekContainer.multiDayEvents.length === 0) {
                                    return 0;
                                }
                                
                                let maxRow = -1;
                                for (let i = 0; i < weekContainer.multiDayEvents.length; i++) {
                                    const event = weekContainer.multiDayEvents[i];
                                    if (event && event.start_col !== undefined && event.end_col !== undefined && 
                                        event.start_col <= modelData.day_position && 
                                        event.end_col >= modelData.day_position) {
                                        maxRow = Math.max(maxRow, event.layout_row || 0);
                                    }
                                }
                                return Math.min(maxRow + 1, unifiedCalendarView.maxMultiDayRows);
                            }
                            
                            // Filter to get only single-day events for this cell
                            property var singleDayEvents: {
                                if (!modelData || !modelData.events) {
                                    return [];
                                }
                                return modelData.events.filter(e => e && !e.is_multi_day);
                            }
                            
                            // Single-day events container
                            ListView {
                                id: eventListView
                                anchors {
                                    top: dayNumberText.bottom
                                    left: parent.left
                                    right: parent.right
                                    bottom: parent.bottom
                                    margins: 2
                                }
                                
                                // Calculate top margin to accommodate multi-day events
                                anchors.topMargin: dayCell.reservedMultiDayRows * 
                                                 (unifiedCalendarView.multiDayEventHeight + 
                                                  unifiedCalendarView.eventSpacing) + 2
                                
                                // List properties
                                clip: true
                                spacing: 2
                                interactive: false // Disable scrolling
                                
                                // Only display single-day events
                                model: {
                                    // Limit the number of events shown
                                    const maxVisible = unifiedCalendarView.maxEventsPerDay;
                                    return dayCell.singleDayEvents.slice(0, maxVisible);
                                }
                                
                                // Event delegate
                                delegate: Rectangle {
                                    id: eventItem
                                    width: eventListView.width
                                    height: eventText.implicitHeight + 4
                                    radius: 3
                                    
                                    // Get color from the event
                                    property color eventColor: modelData && modelData.color ? modelData.color : "#1a73e8"
                                    
                                    // Use a lighter version for background
                                    color: Qt.lighter(eventColor, 1.8)
                                    border.color: eventColor
                                    border.width: 1
                                    
                                    // Event content
                                    RowLayout {
                                        anchors.fill: parent
                                        anchors.margins: 2
                                        spacing: 4
                                        
                                        // Color indicator
                                        Rectangle {
                                            width: 4
                                            Layout.fillHeight: true
                                            color: eventItem.eventColor
                                            radius: 2
                                        }
                                        
                                        // Event title and time
                                        Text {
                                            id: eventText
                                            Layout.fillWidth: true
                                            font.pixelSize: 10
                                            
                                            // Format the text with time if available
                                            text: {
                                                if (!modelData) return "";
                                                
                                                let timeString = "";
                                                if (!modelData.all_day && modelData.start_time) {
                                                    const dtParts = modelData.start_time.split('T');
                                                    if (dtParts.length > 1) {
                                                        const timeParts = dtParts[1].split(':');
                                                        if (timeParts.length >= 2) {
                                                            timeString = timeParts[0] + ":" + timeParts[1] + " ";
                                                        }
                                                    }
                                                }
                                                return timeString + (modelData.title || "");
                                            }
                                            
                                            // Dynamic text color based on background brightness
                                            color: {
                                                const r = eventItem.color.r;
                                                const g = eventItem.color.g;
                                                const b = eventItem.color.b;
                                                const luminance = 0.299 * r + 0.587 * g + 0.114 * b;
                                                return luminance > 0.5 ? "#000000" : "#ffffff";
                                            }
                                            
                                            elide: Text.ElideRight
                                            verticalAlignment: Text.AlignVCenter
                                        }
                                    }
                                }
                                
                                // "More events" indicator
                                footer: Rectangle {
                                    visible: dayCell.singleDayEvents.length > unifiedCalendarView.maxEventsPerDay
                                    width: eventListView.width
                                    height: visible ? 15 : 0
                                    color: "transparent"
                                    
                                    Text {
                                        anchors.fill: parent
                                        text: "+" + (dayCell.singleDayEvents.length - unifiedCalendarView.maxEventsPerDay) + " more"
                                        color: unifiedCalendarView.moreEventsColor
                                        font.pixelSize: 10
                                        horizontalAlignment: Text.AlignRight
                                        verticalAlignment: Text.AlignVCenter
                                    }
                                }
                            }
                        }
                    }
                }
                
                // Multi-day events layer
                Item {
                    id: multiDayEventsLayer
                    anchors.fill: parent
                    
                    // Render each multi-day event
                    Repeater {
                        model: weekContainer.multiDayEvents
                        
                        Rectangle {
                            id: multiDayEvent
                            visible: modelData !== undefined
                            
                            // Position based on the event's calculated layout
                            x: (modelData && modelData.start_col !== undefined) ? 
                               modelData.start_col * unifiedCalendarView.cellWidth : 0
                            y: ((modelData && modelData.layout_row !== undefined) ? 
                               modelData.layout_row : 0) * 
                               (unifiedCalendarView.multiDayEventHeight + unifiedCalendarView.eventSpacing) + 
                               unifiedCalendarView.dayNumberHeight + 2
                            
                            // Calculate width based on columns
                            width: (modelData && modelData.start_col !== undefined && modelData.end_col !== undefined) ? 
                                   (modelData.end_col - modelData.start_col + 1) * 
                                   unifiedCalendarView.cellWidth - 4 : 0
                            height: unifiedCalendarView.multiDayEventHeight
                            
                            // Event color styling
                            color: (modelData && modelData.color) ? Qt.lighter(modelData.color, 1.8) : "#e8f0fe"
                            border.color: (modelData && modelData.color) ? modelData.color : "#1a73e8"
                            border.width: 1
                            radius: 3
                            
                            // Continuation indicators
                            Rectangle {
                                visible: modelData && modelData.continues_left
                                height: parent.height
                                width: 6
                                color: parent.color
                                anchors.left: parent.left
                                anchors.leftMargin: -3
                                z: -1
                            }
                            
                            Rectangle {
                                visible: modelData && modelData.continues_right
                                height: parent.height
                                width: 6
                                color: parent.color
                                anchors.right: parent.right
                                anchors.rightMargin: -3
                                z: -1
                            }
                            
                            // Event content
                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 4
                                anchors.rightMargin: 4
                                spacing: 4
                                
                                // Color indicator
                                Rectangle {
                                    width: 4
                                    Layout.fillHeight: true
                                    color: (modelData && modelData.color) ? modelData.color : "#1a73e8"
                                    radius: 2
                                }
                                
                                // Event title
                                Text {
                                    Layout.fillWidth: true
                                    text: (modelData && modelData.title) ? modelData.title : ""
                                    font.pixelSize: 10
                                    elide: Text.ElideRight
                                    // Dynamic text color based on background brightness
                                    color: {
                                        if (!modelData || !modelData.color) return "#000000";
                                        
                                        const eventColor = modelData.color;
                                        const bgColor = Qt.lighter(eventColor, 1.8);
                                        const r = bgColor.r;
                                        const g = bgColor.g;
                                        const b = bgColor.b;
                                        const luminance = 0.299 * r + 0.587 * g + 0.114 * b;
                                        return luminance > 0.5 ? "#000000" : "#ffffff";
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    
    // Call initial model processing when component is complete
    Component.onCompleted: {
        if (model) {
            processModelChange()
        }
    }
} 