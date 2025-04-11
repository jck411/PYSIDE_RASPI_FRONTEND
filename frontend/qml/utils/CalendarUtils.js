// CalendarUtils.js - Shared utility functions for calendar components

// Process multi-day events to determine layout
function processMultiDayEvents(days) {
    if (!days || days.length === 0) {
        return []
    }
    
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
}

// Calculate proper height for cells based on content
function calculateDayCellHeight(events, headerHeight, eventHeight, spacing) {
    if (!events || events.length === 0) {
        return headerHeight + spacing * 2
    }
    
    return headerHeight + (events.length * (eventHeight + spacing)) + spacing
}

// Calculate the optimal height for a day cell with ALL events visible
function calculateOptimalDayCellHeight(dayData, headerHeight, eventHeight, spacing, padding) {
    if (!dayData || !dayData.events || dayData.events.length === 0) {
        return headerHeight + padding * 2;
    }
    
    const eventCount = dayData.events.length;
    const eventsHeight = eventCount * (eventHeight + spacing);
    
    return headerHeight + eventsHeight + padding * 2;
}

// Determine if a day cell should use scrolling based on available height
function shouldUseScrolling(dayData, maxHeight, headerHeight, eventHeight, spacing, padding) {
    if (!dayData || !dayData.events || dayData.events.length <= 3) {
        return false; // Don't use scrolling for 3 or fewer events
    }
    
    const optimalHeight = calculateOptimalDayCellHeight(dayData, headerHeight, eventHeight, spacing, padding);
    return optimalHeight > maxHeight;
}

// Calculate a reasonable cell height when using scrolling
function calculateScrollingCellHeight(availableHeight, maxHeightPercentage) {
    // Use at most maxHeightPercentage of available height
    return Math.min(availableHeight * (maxHeightPercentage || 0.4), availableHeight);
}

// Format time display consistently 
function formatEventTime(timeString) {
    if (!timeString) return ""
    
    try {
        // Parse ISO string
        var date = new Date(timeString)
        
        // Format hour and minute
        var hours = date.getHours()
        var minutes = date.getMinutes().toString().padStart(2, '0')
        
        return hours + ":" + minutes
    } catch (error) {
        console.error("Error formatting time:", error)
        return ""
    }
}

// Helper function to determine text color based on background brightness
function getTextColorForBackground(backgroundColor) {
    // Get RGB components (assuming backgroundColor is a color object with r, g, b properties)
    var r = backgroundColor.r
    var g = backgroundColor.g
    var b = backgroundColor.b
    
    // Calculate luminance using standard formula
    var luminance = 0.299 * r + 0.587 * g + 0.114 * b
    
    // Return white for dark backgrounds, black for light backgrounds
    return luminance > 0.5 ? "#000000" : "#ffffff"
}

// Filter events for a specific day, returning only non-multi-day events
function getSingleDayEvents(dayData) {
    if (!dayData || !dayData.events) return []
    
    return dayData.events.filter(function(event) {
        return event && !event.is_multi_day
    })
}

// Get a display string for an event
function getEventDisplayText(event) {
    if (!event) return ""
    
    var timeString = ""
    if (!event.all_day && event.start_time) {
        timeString = formatEventTime(event.start_time) + " "
    }
    
    return timeString + (event.title || "Untitled")
}

// Helper function to create a lighter version of a color for event backgrounds
function getLighterColor(color, factor) {
    if (!factor) factor = 1.8 // Default lightening factor
    return Qt.lighter(color, factor)
}

// Determine the maximum row needed for multi-day events
function getMaxMultiDayRow(events) {
    if (!events || events.length === 0) return 0
    
    var maxRow = 0
    for (var i = 0; i < events.length; i++) {
        maxRow = Math.max(maxRow, events[i].row)
    }
    return maxRow + 1 // +1 because rows are 0-indexed
}

// Extract cell data for a specific day
function extractCellData(dayData) {
    if (!dayData) return null
    
    return {
        date: dayData.date,
        dateStr: dayData.date_str,
        day: dayData.day,
        dayName: dayData.dayName,
        dayNumber: dayData.dayNumber,
        isCurrentMonth: dayData.isCurrentMonth,
        isToday: dayData.isToday,
        dayPosition: dayData.day_position,
        events: dayData.events || [],
        multiDayEvents: dayData.multiDayEvents || []
    }
} 