import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import MyTheme 1.0

// Base calendar view component with shared functionality
// for both month and week/day views
Item {
    id: baseCalendarView

    // Common properties
    property var model: null
    property bool debugOutput: false
    property int cellWidth
    property int cellHeight
    property int multiDayEventHeight: 20
    property int dayNumberHeight: 20
    property int eventSpacing: 2
    property var processedMultiDayEvents: []
    
    // Signal for event interactions
    signal eventClicked(var eventData)
    signal dayClicked(var dayData)
    
    // ScrollView container wrapping all content
    ScrollView {
        id: scrollView
        anchors.fill: parent
        clip: true
        // Configure scrollbars
        ScrollBar.vertical.policy: ScrollBar.AsNeeded
        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
        
        // Content container
        Item {
            id: contentContainer
            width: parent.width
            // Height will be determined by child implementations
            // Default minimum height to match parent
            implicitHeight: parent.height
        }
    }
    
    // Expose contentContainer to derived views
    property alias contentContainer: contentContainer
    
    // Calculate proper height for cells based on content
    function calculateDayCellHeight(events, headerHeight, eventHeight, spacing) {
        if (!events || events.length === 0) {
            return headerHeight + spacing * 2
        }
        
        return headerHeight + (events.length * (eventHeight + spacing)) + spacing
    }
    
    // Process model to extract multi-day events
    function processMultiDayEvents(days) {
        if (debugOutput) console.log("Processing multi-day events")
        
        if (!days || days.length === 0) {
            return []
        }
        
        try {
            // Collect all multi-day events
            var events = []
            
            // First, identify all multi-day events and their spans
            for (var i = 0; i < days.length; i++) {
                var day = days[i]
                if (day && day.multiDayEvents) {
                    for (var j = 0; j < day.multiDayEvents.length; j++) {
                        var event = day.multiDayEvents[j]
                        if (event && event.id) {
                            // Find if we've already processed this event
                            var existingIdx = -1
                            for (var k = 0; k < events.length; k++) {
                                if (events[k].id === event.id) {
                                    existingIdx = k
                                    break
                                }
                            }
                            
                            if (existingIdx < 0) {
                                // New event - add it with position info
                                events.push({
                                    id: event.id,
                                    title: event.title,
                                    color: event.color || "#7847f5",
                                    startCol: i,
                                    endCol: event.isEnd ? i : days.length - 1,
                                    row: 0  // Will be assigned in layout phase
                                })
                            } else {
                                // Update end column if this day marks the end
                                if (event.isEnd) {
                                    events[existingIdx].endCol = i
                                }
                            }
                        }
                    }
                }
            }
            
            // Sort events by duration (longest first) to improve layout
            events.sort(function(a, b) {
                var spanA = a.endCol - a.startCol
                var spanB = b.endCol - b.startCol
                return spanB - spanA  // Descending order
            })
            
            // Assign rows to avoid overlapping (simple greedy algorithm)
            var usedRows = []
            for (var m = 0; m < events.length; m++) {
                var evt = events[m]
                var row = 0
                
                // Find first available row
                while (true) {
                    var rowAvailable = true
                    for (var n = 0; n < usedRows.length; n++) {
                        var usedEvt = usedRows[n]
                        if (usedEvt.row === row &&
                            !(evt.endCol < usedEvt.startCol || evt.startCol > usedEvt.endCol)) {
                            rowAvailable = false
                            break
                        }
                    }
                    
                    if (rowAvailable) {
                        break
                    }
                    row++
                }
                
                evt.row = row
                usedRows.push(evt)
            }
            
            return events
        } catch (error) {
            if (debugOutput) console.error("Error processing multi-day events:", error)
            return []
        }
    }
    
    // Virtual method to be implemented by derived views
    function renderView() {
        console.warn("BaseCalendarView.renderView() should be overridden")
    }
    
    // Initialize rendering when model changes
    onModelChanged: {
        if (debugOutput) console.log("BaseCalendarView model changed")
    }
} 