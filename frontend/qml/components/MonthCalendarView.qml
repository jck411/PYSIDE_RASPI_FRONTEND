import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import MyTheme 1.0
import "../utils/CalendarUtils.js" as Utils

// Month view implementation based on BaseCalendarView
BaseCalendarView {
    id: monthCalendarView
    
    // Properties
    cellWidth: width / 7
    cellHeight: height / 6
    
    // Height for weekday headers at the top of the view
    property int weekdayHeaderHeight: 40
    
    // Height allocated for multi-day events at the top of each week
    property int multiDayEventSectionHeight: 0
    
    // Maximum number of multi-day event rows to display per week
    property int maxMultiDayRows: 2
    
    // Keep old weeks during model change to prevent flickering
    property var oldWeeks: []
    
    // Set up weeks array when model changes
    property var weeks: []
    
    // Weekday names for static headers (used when no model is available yet)
    property var defaultWeekdays: ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    
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
            
            // After weeks are set, process multi-day events for each week
            renderView()
        } else {
            weeks = []
        }
    }
    
    // Handle model changes by using a timer to decouple from binding loop
    onModelChanged: {
        if (debugOutput) console.log("Month calendar model changed, length:", model ? model.length : 0)
        modelChangeTimer.restart()
    }
    
    // Implement the renderView method
    function renderView() {
        // Reset the content container
        for (let i = contentContainer.children.length - 1; i >= 0; i--) {
            contentContainer.children[i].destroy()
        }
        
        // No rendering if no data
        if (!weeks || weeks.length === 0) {
            if (debugOutput) console.log("No weeks to render")
            return
        }
        
        if (debugOutput) console.log("Rendering month view with weeks:", weeks.length)
        
        // Set content container height to fit all weeks plus the weekday header
        contentContainer.height = monthCalendarView.height // Initial height
        
        // Create weekday headers row
        var weekdayHeadersRow = Qt.createQmlObject(
            'import QtQuick 2.15; Row { width: parent.width; height: ' + weekdayHeaderHeight + '; spacing: 0 }',
            contentContainer
        )
        
        // Create headers for each day of the week
        // Use first week's days for the headers
        var headerDays = weeks[0] || []
        
        for (let dayIndex = 0; dayIndex < 7; dayIndex++) {
            var dayData = null
            if (dayIndex < headerDays.length) {
                dayData = headerDays[dayIndex]
            }
            
            // Create the weekday header component
            var headerComponent = Qt.createComponent("WeekdayHeader.qml")
            if (headerComponent.status === Component.Ready) {
                var header = headerComponent.createObject(weekdayHeadersRow, {
                    width: weekdayHeadersRow.width / 7,
                    height: weekdayHeadersRow.height,
                    dayData: dayData,
                    // Use default day name if no data available
                    dayName: dayData ? dayData.dayName : defaultWeekdays[dayIndex],
                    // Don't show day numbers in month view header
                    dayNumber: ""
                })
            }
        }
        
        // Create a component for the column of weeks
        var weeksColumn = Qt.createQmlObject(
            'import QtQuick 2.15; Column { id: weeksColumn; width: parent.width; spacing: 0 }',
            contentContainer
        )
        
        // Position weeks column below headers
        weeksColumn.y = weekdayHeaderHeight
        
        // Render each week in the column
        for (let weekIndex = 0; weekIndex < weeks.length; weekIndex++) {
            var weekDays = weeks[weekIndex]
            
            // Process multi-day events for this week
            var multiDayEvents = processMultiDayEvents(weekDays)
            
            // Calculate height needed for multi-day events
            var maxMultiDayRow = 0
            for (let i = 0; i < multiDayEvents.length; i++) {
                maxMultiDayRow = Math.max(maxMultiDayRow, multiDayEvents[i].row)
            }
            maxMultiDayRow = Math.min(maxMultiDayRow + 1, maxMultiDayRows) // +1 because rows are 0-indexed
            var multiDayEventSectionHeight = maxMultiDayRow * (multiDayEventHeight + 2)
            
            // Create week container
            var weekContainer = Qt.createQmlObject(
                'import QtQuick 2.15; Item { id: weekContainer; width: parent.width; property int maxDayCellHeight: 0 }',
                weeksColumn
            )
            
            // Initial week height (will be adjusted based on content)
            weekContainer.height = cellHeight + multiDayEventSectionHeight
            
            // Create the day cells row
            var dayCellsRow = Qt.createQmlObject(
                'import QtQuick 2.15; Row { width: parent.width; spacing: 0 }',
                weekContainer
            )
            
            // Position day cells below multi-day events
            dayCellsRow.y = multiDayEventSectionHeight
            dayCellsRow.height = cellHeight
            
            // Create day cells
            for (let dayIndex = 0; dayIndex < weekDays.length; dayIndex++) {
                var dayData = weekDays[dayIndex]
                
                // Use direct path to the DayCell component
                var dayCellComponent = Qt.createComponent("DayCell.qml")
                if (dayCellComponent.status === Component.Ready) {
                    var dayCell = dayCellComponent.createObject(dayCellsRow, {
                        width: cellWidth,
                        height: dayCellsRow.height,
                        dayData: dayData,
                        isCurrentView: dayData.isCurrentMonth,
                        isToday: dayData.isToday,
                        availableHeight: cellHeight * 1.5 // Allow cells to expand up to 1.5x default height
                    })
                    
                    // Connect day cell signals
                    dayCell.MouseArea.onClicked.connect(function() {
                        monthCalendarView.dayClicked(dayData)
                    })
                    
                    // Track max height for the row using explicit function
                    // instead of relying on property bindings
                    var cellContentHeight = dayCell.contentHeight
                    if (cellContentHeight > weekContainer.maxDayCellHeight) {
                        weekContainer.maxDayCellHeight = cellContentHeight
                    }
                } else if (dayCellComponent.status === Component.Error) {
                    if (debugOutput) console.error("Error creating DayCell:", dayCellComponent.errorString())
                }
            }
            
            // Adjust day cells height based on maximum content using a defined function
            // to avoid binding loops
            function adjustDayCellHeights() {
                dayCellsRow.height = Math.max(cellHeight, weekContainer.maxDayCellHeight)
                weekContainer.height = dayCellsRow.y + dayCellsRow.height
                
                // Adjust all cells to match row height
                for (let i = 0; i < dayCellsRow.children.length; i++) {
                    let cell = dayCellsRow.children[i]
                    if (cell && cell.height !== undefined) {
                        cell.height = dayCellsRow.height
                    }
                }
            }
            
            // Call the adjustment function after cell creation
            adjustDayCellHeights()
            
            // Create multi-day events container
            var multiDayContainer = Qt.createQmlObject(
                'import QtQuick 2.15; Item { width: parent.width; height: parent.height }',
                weekContainer
            )
            
            // Render multi-day events
            for (let i = 0; i < Math.min(multiDayEvents.length, maxMultiDayRows * 7); i++) {
                var eventData = multiDayEvents[i]
                if (eventData.row < maxMultiDayRows) { // Only show events up to maxMultiDayRows
                    var multiDayComponent = Qt.createComponent("MultiDayEvent.qml")
                    if (multiDayComponent.status === Component.Ready) {
                        var multiDayEvent = multiDayComponent.createObject(multiDayContainer, {
                            eventData: eventData,
                            totalColumns: 7,
                            eventHeight: multiDayEventHeight
                        })
                        
                        // Connect event signal
                        multiDayEvent.eventClicked.connect(function(data) {
                            monthCalendarView.eventClicked(data)
                        })
                    } else if (multiDayComponent.status === Component.Error) {
                        if (debugOutput) console.error("Error creating MultiDayEvent:", multiDayComponent.errorString())
                    }
                }
            }
        }
        
        // Update content container height to include header plus weeks
        contentContainer.height = weekdayHeaderHeight + weeksColumn.height
        
        // Ensure ScrollView has proper policies
        Component.onCompleted: {
            scrollView.ScrollBar.vertical.policy = ScrollBar.AsNeeded
            scrollView.ScrollBar.horizontal.policy = ScrollBar.AlwaysOff
        }
    }
    
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
    
    // Initialize first render when component is created
    Component.onCompleted: {
        if (model && model.length > 0) {
            processModelChange()
        }
    }
} 