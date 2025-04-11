# Calendar Architecture: Strategy Pattern Implementation

## Overview

The calendar system has been refactored to use the Strategy Pattern for view modes and navigation. This document explains the architecture and provides guidance for future developers.

## Core Components

### CalendarController

The main controller class that:
- Maintains the current date, events, and view state
- Exposes properties and methods to QML
- Delegates view-specific behavior to the appropriate strategy

### View Strategies

Strategy classes that implement view-specific behaviors:
- `MonthViewStrategy`: Grid view of a full month
- `WeekViewStrategy`: Horizontal view of a 7-day week
- `DayViewStrategy`: Detailed view of a single day
- `ThreeDayViewStrategy`: Three-day rolling view

Each strategy implements these key methods:
- `update_date_range`: Calculate start/end dates for the view
- `navigate_forward`: Move forward (next month/week/day) 
- `navigate_backward`: Move backward (prev month/week/day)
- `format_date_range_display`: Format the date range for UI display
- `create_range_days` (optional): Custom day model creation
- `calculate_days_model` (optional): Custom grid model calculation
- `get_event_fetch_range` (optional): Custom event fetching date range

## Navigation Flow

1. User triggers navigation (next/previous buttons)
2. `moveDateRangeForward` or `moveDateRangeBackward` is called
3. Controller retrieves the strategy for the current view mode
4. Strategy's navigation method updates the current date
5. Date range is recalculated based on the updated date
6. UI is updated with the new date range

## Events Processing

1. Events are fetched from Google Calendar API
2. Events are filtered by calendar visibility
3. Events are assigned to days in the model
4. Multi-day events are processed for layout
5. The model is exposed to QML for rendering

## Adding a New View Mode

To add a new view mode:
1. Create a new strategy class in `calendar_view_strategies.py`
2. Implement the required methods (navigation, date range calculation)
3. Add the strategy to the `_view_strategies` dictionary in CalendarController
4. Update QML components to handle the new view mode

## Connecting to QML

The calendar controller exposes:
- `currentRangeDisplay`: Formatted date range string
- `currentRangeDays`: List of days in the current range
- `daysInMonthModel`: Grid model for month view
- Navigation methods (`moveDateRangeForward`, etc.)
- View mode switching methods (`setViewMode`, `cycleViewMode`)

## Benefits of This Architecture

1. **Extensibility**: New view modes can be added without modifying the core controller
2. **Maintainability**: View-specific logic is isolated in separate strategy classes
3. **Consistency**: Common operations like navigation follow the same pattern across views
4. **Flexibility**: Strategies can override specific methods while inheriting defaults

## Sample Implementation of Custom View

```python
class CustomViewStrategy:
    def update_date_range(self, controller, current_date):
        # Calculate start/end date for this view
        controller._range_start_date = start_date
        controller._range_end_date = end_date
        
    def navigate_forward(self, controller, current_date):
        # Calculate next date in sequence
        return current_date.addDays(X)
        
    def navigate_backward(self, controller, current_date):
        # Calculate previous date in sequence
        return current_date.addDays(-X)
        
    def format_date_range_display(self, controller, start_date, end_date):
        # Return formatted string for display
        return "Custom format: ..."
```
