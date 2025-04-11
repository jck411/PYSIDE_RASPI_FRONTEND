import QtQuick 2.15
import QtQuick.Controls 2.15
import MyTheme 1.0
import "../utils/CalendarUtils.js" as Utils

Rectangle {
    id: dayCell
    
    // Required properties
    property var dayData: null
    property bool isCurrentView: true
    property bool isToday: false
    property bool enableHoverEffects: true
    property int maxEventsToShow: 10 // Controls when to use scrolling vs limit indicators
    
    // Style properties
    property color backgroundColor: isCurrentView ? 
                                   ThemeManager.background_color : 
                                   ThemeManager.input_background_color
    property color todayBorderColor: ThemeManager.button_primary_color
    property color normalBorderColor: ThemeManager.input_border_color
    property color textColor: ThemeManager.text_primary_color
    
    // Event styling
    property int eventHeight: 18
    property int dayNumberHeight: 20
    property int eventSpacing: 2
    property int padding: 4
    
    // Expose events for external access
    property var events: dayData ? (dayData.events || []) : []
    
    // Available height for the cell (to be set by parent component)
    property int availableHeight: height
    
    // Flag to determine if we should use scrolling or show +X more
    property bool useScrolling: false // Will be set programmatically to avoid binding loops
    
    // Store calculated content height to avoid binding loops
    property int _calculatedContentHeight: dayNumberHeight + padding * 2
    
    // Height to be read by parent components
    property int contentHeight: _calculatedContentHeight
    
    // Optimal height if all events were shown (used by parent component)
    property int optimalHeight: 0 // Will be set programmatically to avoid binding loops
    
    // Fill with background color
    color: backgroundColor
    
    // Special border for today's date
    border.color: isToday ? todayBorderColor : normalBorderColor
    border.width: isToday ? 2 : 1
    
    // Calculate heights when component completes or properties change
    Component.onCompleted: recalculateHeights()
    onDayDataChanged: recalculateHeights()
    onAvailableHeightChanged: recalculateHeights()
    
    // Explicit calculation function to avoid binding loops
    function recalculateHeights() {
        if (!dayData || !dayData.events) {
            optimalHeight = dayNumberHeight + padding * 2
            _calculatedContentHeight = optimalHeight
            useScrolling = false
            return
        }
        
        // Calculate optimal height for all events
        optimalHeight = Utils.calculateOptimalDayCellHeight(dayData, dayNumberHeight, eventHeight, eventSpacing, padding)
        
        // Determine if scrolling should be used
        useScrolling = Utils.shouldUseScrolling(dayData, availableHeight, dayNumberHeight, eventHeight, eventSpacing, padding)
        
        // Set content height based on scrolling decision
        if (useScrolling) {
            _calculatedContentHeight = Utils.calculateScrollingCellHeight(availableHeight, 0.5)
        } else {
            var eventsToShow = Math.min(dayData.events.length, maxEventsToShow)
            _calculatedContentHeight = dayNumberHeight + (eventsToShow * (eventHeight + eventSpacing)) + padding * 2
        }
    }
    
    // Day number display
    Text {
        id: dayNumber
        anchors {
            top: parent.top
            left: parent.left
            topMargin: padding
            leftMargin: padding
        }
        text: dayData ? dayData.day : ""
        font.pixelSize: 14
        font.bold: isToday
        color: isToday ? todayBorderColor : textColor
    }
    
    // Events container with scrolling
    ScrollView {
        id: eventsScrollView
        anchors {
            top: dayNumber.bottom
            left: parent.left
            right: parent.right
            bottom: parent.bottom
            topMargin: 2
            leftMargin: padding
            rightMargin: padding
            bottomMargin: padding
        }
        clip: true
        ScrollBar.vertical.policy: useScrolling ? ScrollBar.AsNeeded : ScrollBar.AlwaysOff
        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
        
        // List of events
        Column {
            id: eventsColumn
            width: parent.width
            spacing: eventSpacing
            
            // Only render events if we have day data
            Repeater {
                // If not using scrolling, limit the number of events shown
                model: dayData && dayData.events ? 
                       (useScrolling ? dayData.events.length : Math.min(dayData.events.length, maxEventsToShow)) : 0
                
                // Individual event rectangle
                Rectangle {
                    width: eventsColumn.width
                    height: eventHeight
                    radius: 2
                    color: dayData.events[index].color || "#4285F4"
                    
                    // Event title and time
                    Text {
                        anchors {
                            left: parent.left
                            right: parent.right
                            verticalCenter: parent.verticalCenter
                            leftMargin: 4
                            rightMargin: 4
                        }
                        text: {
                            var event = dayData.events[index]
                            var title = event.title || "Untitled"
                            
                            if (event.timeDisplay) {
                                return event.timeDisplay + " " + title
                            } else if (event.start_time) {
                                return Utils.formatEventTime(event.start_time) + " " + title
                            } else {
                                return title
                            }
                        }
                        color: "white"
                        font.pixelSize: 11
                        elide: Text.ElideRight
                    }
                    
                    // Make events clickable
                    MouseArea {
                        anchors.fill: parent
                        onClicked: {
                            // Emit event clicked signal
                            var eventData = dayData.events[index]
                            // Find the CalendarView in the parent hierarchy
                            var calendarView = findCalendarView(dayCell)
                            if (calendarView) {
                                calendarView.eventClicked(eventData)
                            }
                        }
                    }
                }
            }
            
            // "More events" indicator - only show when not using scrolling
            Rectangle {
                width: eventsColumn.width
                height: eventHeight
                color: "transparent"
                visible: !useScrolling && dayData && dayData.events && 
                         dayData.events.length > maxEventsToShow
                
                Text {
                    anchors.centerIn: parent
                    text: dayData && dayData.events ? 
                          "+" + (dayData.events.length - maxEventsToShow) + " more" : ""
                    color: ThemeManager.text_secondary_color
                    font.pixelSize: 11
                }
                
                // Make clickable to show all events
                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        // Find the CalendarView in the parent hierarchy
                        var calendarView = findCalendarView(dayCell)
                        if (calendarView) {
                            calendarView.dayClicked(dayData)
                        }
                    }
                }
            }
        }
    }
    
    // Mouse area for detecting clicks on the cell itself
    MouseArea {
        id: cellMouseArea
        anchors.fill: parent
        z: -1 // Below other mouse areas
        onClicked: {
            if (dayData) {
                // Find the CalendarView in the parent hierarchy
                var calendarView = findCalendarView(dayCell)
                if (calendarView) {
                    calendarView.dayClicked(dayData)
                }
            }
        }
    }
    
    // Expose the mouse area for external connections
    property alias MouseArea: cellMouseArea
    
    // Helper function to find the calendar view in parent hierarchy
    function findCalendarView(item) {
        if (!item) return null
        
        // Check if the current item is a calendar view
        if (item.eventClicked && item.dayClicked) {
            return item
        }
        
        // If not, check the parent
        if (item.parent) {
            return findCalendarView(item.parent)
        }
        
        return null
    }
} 