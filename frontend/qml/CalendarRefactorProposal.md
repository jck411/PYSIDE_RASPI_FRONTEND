# Calendar Refactoring Guide for New LLM

## Current State Analysis

The calendar feature in this PySide6 application currently has significant implementation issues that need to be addressed. Here's a detailed breakdown of the current state and requirements:

### Current Structure

The calendar implementation consists of:

1. **CalendarScreen.qml**: Main container that switches between view modes
2. **UnifiedCalendarView.qml**: Month view implementation (grid layout)
3. **CustomCalendarView.qml**: Week/day view implementation (column layout)
4. **CalendarController.py**: Backend logic that provides data models to the QML views

### Core Requirements to Fix

1. **Vertical Cell Expansion**: Cells must expand vertically when events can't fit
   - Currently, cells have fixed/limited heights
   - Events beyond a certain count are cut off or only shown as "+X more"

2. **Scrolling for Expanded Content**: 
   - When expanded cells exceed available screen space, the view should be scrollable
   - This should work in both month and week/day views

### Technical Issues

1. **Inconsistent Event Handling**:
   - Multi-day events are processed differently in each view
   - Event limit handling varies between views
   - Vertical expansion logic is incomplete

2. **QML Architecture Problems**:
   - Tight coupling between layout and rendering
   - Duplicated logic for similar problems
   - Inefficient model processing
   - Lack of component reuse

## Detailed Refactoring Plan

### Component Hierarchy

```
- frontend/qml/
  |- CalendarScreen.qml                # Main screen container
  |- components/
     |- BaseCalendarView.qml           # Shared base functionality
     |- CalendarEvent.qml              # Generic event component
     |- MultiDayEvent.qml              # Multi-day specific event
     |- DayCell.qml                    # Cell component for days
     |- WeekdayHeader.qml              # Weekday header component
     |- MonthCalendarView.qml          # Month view implementation
     |- WeekCalendarView.qml           # Week/day view implementation
  |- utils/
     |- CalendarUtils.js               # Shared utility functions
```

### Key Implementation Details

#### 1. BaseCalendarView.qml

This component should handle:
- Common model processing
- Signal definitions (eventClicked, dayClicked)
- ScrollView implementation for vertical scrolling
- Property definitions shared across views
- Base rendering functions to be overridden

```qml
// Essential properties
property var model: null
property bool debugOutput: false
property int cellWidth
property int cellHeight
property int multiDayEventHeight
property var processedMultiDayEvents: []

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
        // Height must be determined by child implementations
    }
}

// Virtual method to be implemented
function renderView() {
    console.warn("BaseCalendarView.renderView() should be overridden")
}
```

#### 2. CalendarUtils.js

Implement critical shared functions:

```javascript
// Process multi-day events to determine layout
function processMultiDayEvents(days) {
    // 1. Extract multi-day events from days array
    // 2. Sort by duration (longest first)
    // 3. Assign rows to avoid overlapping
    // 4. Return processed array with layout information
}

// Calculate correct height for cells based on content
function calculateDayCellHeight(events, headerHeight, eventHeight, spacing) {
    // Determine proper height based on event count
}

// Format time display consistently 
function formatEventTime(timeString) {
    // Parse and format time string
}
```

#### 3. DayCell.qml

A reusable cell component that:
- Handles day number display
- Renders events for this day
- Properly calculates dynamic height based on content
- Supports visual styling for current month, today, etc.

```qml
Rectangle {
    id: dayCell
    
    // Required properties
    property var dayData
    property bool isCurrentView
    property bool isToday
    
    // Calculate proper height based on content
    property int contentHeight: dayNumberHeight + eventsColumn.height + padding
    
    // Implement cell that can dynamically expand based on content
}
```

#### 4. Integration in CalendarScreen.qml

```qml
// Month view container
Item {
    id: monthViewContainer
    visible: viewMode === "month"
    
    MonthCalendarView {
        id: monthCalendarView
        anchors.fill: parent
        model: CalendarController.daysInMonthModel
    }
}

// Week view container
Item {
    id: weekViewContainer
    visible: viewMode !== "month"
    
    WeekCalendarView {
        id: weekCalendarView
        anchors.fill: parent
        model: CalendarController.currentRangeDays
    }
}
```

## Implementation Challenges & Nuances

When implementing this refactoring, be aware of these specific challenges:

### 1. Model Data Structure

The data model structure is complex and not consistently documented:

```javascript
// Sample model structure (each day object)
{
    date: "2025-04-28",       // ISO date string
    date_str: "20250428",     // Date string format used by controller
    day: "28",                // Day number as string
    dayName: "Mon",           // Weekday name
    dayNumber: 28,            // Day number as integer
    isCurrentMonth: true,     // Whether this day is in the current month
    isToday: false,           // Whether this day is today
    day_position: 0,          // Position in the week (0-6)
    
    // Events for this day - complex nested structure
    events: [
        {
            id: "evt123",
            title: "Meeting",
            color: "#4287f5",
            all_day: false,
            is_multi_day: false,
            start_time: "2025-04-28T10:00:00",
            timeDisplay: "10:00"
        }
    ],
    
    // Multi-day events specific data formats
    multiDayEvents: [
        {
            id: "evt456",
            title: "Conference",
            color: "#7847f5",
            is_multi_day: true,
            daySpan: 3,
            isStart: true,
            isEnd: false
        }
    ]
}
```

### 2. ScrollView Implementation Pitfalls

The QML ScrollView has several implementation nuances:

- Content height must be correctly calculated and propagated to parent
- Clipping behavior can cause rendering issues if not properly set
- ScrollBar policies must be explicitly configured
- ScrollView nesting can cause unexpected behavior

### 3. Dynamic Height Calculation

Calculating heights dynamically is tricky:

- Must account for multi-day event rows at the top of cells
- Need to handle empty cells properly
- Must propagate height changes up the component hierarchy
- Need event height calculation based on content (variable text size)

### 4. Event Rendering Edge Cases

Watch out for these edge cases:

- Events spanning across week boundaries in month view
- All-day events vs. timed events display differences
- Color contrast for event text readability
- Text elision and wrapping rules
- Event overlap handling in dense calendars

### 5. QML Property Binding Loop Pitfalls

QML property binding loops are a common issue:

- Avoid circular dependencies in height calculations
- Use explicit height calculations where needed instead of relying on implicit bindings
- Consider using delayed property assignments for complex calculations

### 6. State Management

State management across calendar views is challenging:

- Ensure view mode transitions maintain scroll position where appropriate
- Handle date selection consistently across views
- Maintain event selection state when switching views
- Process data model changes efficiently to avoid flickering

## Testing Steps

To properly verify the implementation:

1. Test with calendars containing many events in a single day (10+)
2. Verify multi-day events render correctly across week boundaries
3. Confirm scrolling works in month view with many events
4. Test week view with varied event counts across days
5. Validate day numbers, events, and all content renders correctly
6. Ensure proper styling of today, current month, and non-current month days

## Important Note on Component References

The QML component resolution can be tricky. When referencing components:

- Use proper import paths relative to the importing file
- Watch out for import path differences between components
- Remember that components in subdirectories need explicit imports

In MonthCalendarView.qml and WeekCalendarView.qml, use:
```qml
import "../components"  // To import other components in the same directory
import "../utils/CalendarUtils.js" as Utils  // For the utils
```
