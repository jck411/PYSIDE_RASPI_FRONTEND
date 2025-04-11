# Calendar Migration Guide: CustomCalendarView to WeekCalendarView

This guide outlines the steps required to migrate from the legacy `CustomCalendarView.qml` to the newer `WeekCalendarView.qml` component that supports improved vertical scrolling and better handles days with many events.

## Overview

The `WeekCalendarView.qml` component has been redesigned to:
- Properly handle vertical scrolling for days with many events
- Support multi-day events consistently
- Improve accessibility and usability
- Share common code with `MonthCalendarView.qml` via the `BaseCalendarView.qml`

## Step-by-Step Migration Plan

### 1. Update CalendarScreen.qml

Replace the CustomCalendarView import and instantiation with WeekCalendarView:

```qml
// OLD:
import "CustomCalendarView.qml"
// ...
CustomCalendarView {
    id: customCalendarView
    visible: viewMode !== "month"
    anchors.fill: parent
    model: CalendarController.currentRangeDays
}

// NEW:
import "components/WeekCalendarView.qml"
// ...
WeekCalendarView {
    id: weekCalendarView
    visible: viewMode !== "month"
    anchors.fill: parent
    model: CalendarController.currentRangeDays
}
```

### 2. Update CalendarController Signal Connections

Update any signal connections in CalendarScreen.qml to work with the new component:

```qml
// OLD:
Connections {
    target: customCalendarView
    function onDayClicked(dayData) {
        // Handle day clicked
    }
    function onEventClicked(eventData) {
        // Handle event clicked
    }
}

// NEW:
Connections {
    target: weekCalendarView
    function onDayClicked(dayData) {
        // Handle day clicked (same implementation)
    }
    function onEventClicked(eventData) {
        // Handle event clicked (same implementation)
    }
}
```

### 3. Check CSS/Style Integration

The new WeekCalendarView uses ThemeManager properties consistently. Verify the following in your theme implementation:

- `ThemeManager.background_color`
- `ThemeManager.input_background_color`
- `ThemeManager.text_primary_color`
- `ThemeManager.text_secondary_color`
- `ThemeManager.button_primary_color`
- `ThemeManager.input_border_color`

### 4. Verify Data Model Compatibility

Ensure your calendar data model includes:

- `date`: ISO date string
- `date_str`: Date string format used by controller
- `day`: Day number as string
- `dayName`: Weekday name 
- `isToday`: Boolean indicating if this is today
- `events`: Array of event objects with proper fields
- `multiDayEvents`: Array of multi-day event objects

### 5. Test View Mode Transitions

Verify the transitions between month and week views, ensuring:
- Correct navigation between month/week/day views
- Proper selection highlighting
- Consistent event display

### 6. Performance Testing

Test with various event densities:
- Days with 1-3 events
- Days with 5-10 events
- Days with 15+ events to verify scrolling behavior

## Differences to Be Aware Of

### Event Display

The new WeekCalendarView:
- Shows more events by default with scrolling
- Handles multi-day events more consistently
- Has better touch handling for event selection

### Layout & Scrolling

- Vertical scrolling now occurs at two levels:
  - Within individual day cells when a day has many events
  - At the overall calendar level when the view expands beyond the available space
- Cell heights are more consistent across the week

## Fallback Plan

If issues arise during migration, you can temporarily revert by:
1. Restoring the original CustomCalendarView import and instantiation
2. Restoring any original signal connections
3. Keeping both view implementations until the transition is complete

## Timeline

Recommended implementation approach:
1. Create a development branch for testing
2. Implement changes in CalendarScreen.qml
3. Test thoroughly with various event configurations
4. Deploy the changes once all tests pass 