# Calendar Screen Implementation

The CalendarScreen provides an intuitive calendar interface with simplified navigation between views:

## Key Features
- **Two Primary View Modes:**
  - **Month View:** Traditional calendar grid displaying the entire month
  - **Week View:** Focused 7-day view showing more event details
- **Day View Navigation:**
  - Tapping/clicking on any day cell in month or week view navigates to that day's detailed view
  - Back button appears in day view to return to the previous view (month or week)
- **Seamless View Transitions:**
  - The system remembers which view (month or week) was active before entering day view
  - When returning from day view, the user is taken back to their previous context
- **Simple Toggle:**
  - A calendar icon with a badge indicating the current view mode (M/W/D) allows quick switching between views

## Current Implementation
The calendar implementation consists of:
- `CalendarScreen.qml`: Main container that switches between view modes
- `UnifiedCalendarView.qml`: Implements the month view with a grid layout 
- `CustomCalendarView.qml`: Implements week/day views with a column layout
- `CalendarController.py`: Backend class that provides data models and navigation logic

## Refactoring Guidelines

The calendar implementation should be refactored to address several issues:

1. **Vertical Cell Expansion:**
   - Currently, day cells have fixed heights which truncate event display
   - Cells should expand vertically when events can't fit in the fixed space
   - Implement with ScrollView or proper height calculations based on event count

2. **Scrolling for Expanded Content:** 
   - When expanded cells exceed available screen space, the view should be scrollable
   - This requires proper configuration of ScrollView containers with correct policies

3. **Component Architecture:**
   - Extract reusable components:
     - `BaseCalendarView.qml`: Shared base functionality
     - `DayCell.qml`: Reusable day cell component
     - `CalendarEvent.qml`: Single-day event component
     - `MultiDayEvent.qml`: Multi-day event component
     - `WeekdayHeader.qml`: Weekday header component

4. **Implementation Challenges:**
   - ListView vs. ScrollView for events: Use ScrollView with Column for better scrolling
   - Dynamic height calculation: Account for multi-day events at the top of cells
   - Nested ScrollViews: Can cause input handling issues with event propagation
   - Segmentation faults: Be careful when modifying existing code, test incrementally

5. **Data Model Structure:**
   - Day objects include:
     - `date`: ISO date string
     - `day`: Day number as string
     - `isCurrentMonth`: Whether this day is in the current month
     - `isToday`: Whether this day is today
     - `events`: Array of event objects
     - `multiDayEvents`: Special handling for events spanning multiple days

## Future Implementation Approach

When implementing the refactoring:

1. Start by defining shared utility functions in a JavaScript file
2. Implement improvements to the existing views first before extracting components
3. Extract components one at a time, testing thoroughly after each extraction
4. Implement vertical scrolling at the appropriate level (calendar view vs. day cell)
5. Test thoroughly with many events in a single day 