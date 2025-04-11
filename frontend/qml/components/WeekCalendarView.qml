import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import MyTheme 1.0
import "../utils/CalendarUtils.js" as Utils

// Week view implementation based on BaseCalendarView
BaseCalendarView {
    id: weekCalendarView
    
    // Properties
    property int dayHeaderHeight: 50
    property bool debugOutput: false
    
    // Height for multi-day event section
    property int multiDayEventsHeight: maxMultiDayRow * (multiDayEventHeight + 2)
    
    // Maximum height for event section - to prevent excessive expansion
    property int maxDayContentHeight: height - dayHeaderHeight - multiDayEventsHeight - 20
    
    // Default height for day content when no events are present
    property int defaultDayContentHeight: 200
    
    // Threshold for when to start using scrolling
    property int eventScrollThreshold: 6
    
    // Processed multi-day events
    property var allMultiDayEvents: []
    
    // Calculate maximum row needed for multi-day events
    property int maxMultiDayRow: {
        if (!allMultiDayEvents || allMultiDayEvents.length === 0) return 0
        
        var maxRow = 0
        for (var i = 0; i < allMultiDayEvents.length; i++) {
            maxRow = Math.max(maxRow, allMultiDayEvents[i].row)
        }
        return maxRow + 1 // +1 because rows are 0-indexed
    }
    
    // Process the model when it changes
    onModelChanged: {
        if (model && model.length > 0) {
            // Process multi-day events
            allMultiDayEvents = processMultiDayEvents(model)
            
            // Render the view
            renderView()
        } else {
            allMultiDayEvents = []
        }
    }
    
    // Implement the renderView method
    function renderView() {
        // Reset the content container
        for (let i = contentContainer.children.length - 1; i >= 0; i--) {
            contentContainer.children[i].destroy()
        }
        
        // No rendering if no data
        if (!model || model.length === 0) return
        
        // Set content container width to parent width
        contentContainer.width = weekCalendarView.width
        
        // Create day headers row
        var dayHeadersRow = Qt.createQmlObject(
            'import QtQuick 2.15; Row { width: parent.width; height: ' + dayHeaderHeight + '; spacing: 0 }',
            contentContainer
        )
        
        // Create headers for each day
        for (let dayIndex = 0; dayIndex < model.length; dayIndex++) {
            var dayData = model[dayIndex]
            
            // Create the weekday header component
            var headerComponent = Qt.createComponent("WeekdayHeader.qml")
            if (headerComponent.status === Component.Ready) {
                var header = headerComponent.createObject(dayHeadersRow, {
                    width: dayHeadersRow.width / model.length,
                    height: dayHeadersRow.height,
                    dayData: dayData,
                    showDayNumber: true
                })
            }
        }
        
        // Create day cells container below headers
        var dayCellsContainer = Qt.createQmlObject(
            'import QtQuick 2.15; Item { width: parent.width }',
            contentContainer
        )
        dayCellsContainer.y = dayHeaderHeight

        // Create cells row
        var dayCellsRow = Qt.createQmlObject(
            'import QtQuick 2.15; Row { width: parent.width; spacing: 0 }',
            dayCellsContainer
        )
        
        // Create cells for each day
        for (let dayIndex = 0; dayIndex < model.length; dayIndex++) {
            var dayData = model[dayIndex]
            var cellWidth = dayCellsRow.width / model.length
            
            // Create day cell container
            var dayCellContainer = Qt.createQmlObject(
                'import QtQuick 2.15; import MyTheme 1.0; Rectangle { ' +
                '    color: ThemeManager.background_color; ' +
                '    width: ' + cellWidth + '; ' +
                '    border.color: ThemeManager.input_border_color; ' +
                '    border.width: 1; ' +
                '}',
                dayCellsRow
            )
            
            // Update border for today after creation
            if (dayData && dayData.isToday) {
                dayCellContainer.border.color = ThemeManager.button_primary_color;
                dayCellContainer.border.width = 2;
            }
            
            // Create ScrollView for events with proper top margin for multi-day events
            var eventsScrollView = Qt.createQmlObject(
                'import QtQuick 2.15; import QtQuick.Controls 2.15; ' +
                'ScrollView { ' +
                '    width: parent.width; ' +
                '    y: ' + (multiDayEventsHeight + 4) + '; ' +
                '    clip: true; ' +
                '    ScrollBar.vertical.policy: ScrollBar.AsNeeded; ' +
                '    ScrollBar.horizontal.policy: ScrollBar.AlwaysOff; ' +
                '}',
                dayCellContainer
            )
            
            // Create events column inside the ScrollView
            var eventsColumn = Qt.createQmlObject(
                'import QtQuick 2.15; Column { width: parent.width - 16; anchors.horizontalCenter: parent.horizontalCenter; spacing: 2 }',
                eventsScrollView
            )
            
            // Create event items
            if (dayData && dayData.events) {
                // Make day cell clickable
                var mouseTrap = Qt.createQmlObject(
                    'import QtQuick 2.15; MouseArea { anchors.fill: parent; z: -1 }',
                    dayCellContainer
                )
                
                // Connect click to dayClicked signal
                mouseTrap.clicked.connect(function() {
                    weekCalendarView.dayClicked(dayData)
                })
                
                for (let eventIndex = 0; eventIndex < dayData.events.length; eventIndex++) {
                    var event = dayData.events[eventIndex]
                    
                    // Skip multi-day events as they're handled separately
                    if (event.is_multi_day) continue
                    
                    // Create the event component
                    var eventComponent = Qt.createComponent("CalendarEvent.qml")
                    if (eventComponent.status === Component.Ready) {
                        var calendarEvent = eventComponent.createObject(eventsColumn, {
                            width: eventsColumn.width,
                            eventData: event
                        })
                        
                        // Connect event signal
                        calendarEvent.eventClicked.connect(function(data) {
                            weekCalendarView.eventClicked(data)
                        })
                    }
                }
            }
            
            // Calculate appropriate content height based on number of events
            var idealContentHeight
            
            if (!dayData || !dayData.events || dayData.events.length === 0) {
                idealContentHeight = defaultDayContentHeight
            } else {
                // Calculate based on event count
                idealContentHeight = Math.min(
                    dayData.events.length * (multiDayEventHeight + 2) + 16, // Ideal height based on events
                    maxDayContentHeight // Cap at maximum height
                )
                
                // Ensure we have at least default height
                idealContentHeight = Math.max(idealContentHeight, defaultDayContentHeight)
            }
            
            // Set scroll view height
            eventsScrollView.height = idealContentHeight
            
            // Set initial cell height
            dayCellContainer.height = idealContentHeight
        }
        
        // Render multi-day events
        for (let i = 0; i < allMultiDayEvents.length; i++) {
            var eventData = allMultiDayEvents[i]
            var multiDayComponent = Qt.createComponent("MultiDayEvent.qml")
            if (multiDayComponent.status === Component.Ready) {
                var multiDayEvent = multiDayComponent.createObject(dayCellsContainer, {
                    eventData: eventData,
                    totalColumns: model.length,
                    eventHeight: multiDayEventHeight,
                    y: (eventData.row * (multiDayEventHeight + 2))
                })
                
                // Connect event signal
                multiDayEvent.eventClicked.connect(function(data) {
                    weekCalendarView.eventClicked(data)
                })
            }
        }
        
        // Update container heights
        dayCellsContainer.height = multiDayEventsHeight + dayCellsRow.height
        contentContainer.height = dayHeaderHeight + multiDayEventsHeight + dayCellsRow.height
    }
    
    // Show placeholder if no data
    Text {
        anchors.centerIn: parent
        text: "No calendar data available"
        color: ThemeManager.text_secondary_color
        font.pixelSize: 16
        visible: !model || model.length === 0
    }
    
    // Ensure ScrollView has proper policies
    Component.onCompleted: {
        scrollView.ScrollBar.vertical.policy = ScrollBar.AsNeeded
        scrollView.ScrollBar.horizontal.policy = ScrollBar.AlwaysOff
    }
} 