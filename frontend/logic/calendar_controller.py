import sys
from PySide6.QtCore import QObject, Signal, Slot, Property, QDate, QLocale, QTimer
from datetime import datetime, timedelta
import calendar
from .google_calendar import GoogleCalendarClient
from .date_utils import DateUtils
from .calendar_view_strategies import (
    MonthViewStrategy, 
    WeekViewStrategy, 
    DayViewStrategy, 
    ThreeDayViewStrategy
)

class CalendarController(QObject):
    """
    Controller class to manage calendar data and logic for the QML frontend.
    Handles month navigation, event fetching from Google Calendar, and calendar visibility.
    Pre-calculates event positions for efficient rendering.
    """
    # Signal declarations
    currentMonthYearChanged = Signal()
    availableCalendarsChanged = Signal()
    daysInMonthModelChanged = Signal()
    syncStatusChanged = Signal(str)
    viewModeChanged = Signal(str)
    currentRangeDaysChanged = Signal()
    currentRangeDisplayChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_date = QDate.currentDate()
        self._locale = QLocale()
        self._google_client = GoogleCalendarClient()
        self._available_calendars = []
        self._all_events = []
        self._filtered_events = []
        self._days_in_month_model = []
        self._sync_status = "Not synced"
        
        # Initialize view strategies
        self._view_strategies = {
            "month": MonthViewStrategy(),
            "week": WeekViewStrategy(),
            "day": DayViewStrategy(),
            "3day": ThreeDayViewStrategy()
        }
        
        # View mode: "month", "week", "3day", "day"
        self._view_mode = "month"
        
        # Date range for custom views
        self._range_start_date = None
        self._range_end_date = None
        self._range_days = []
        
        # Initialize date range
        self._update_date_range()

        # Initial data load
        self._update_events_and_model()

    # --- Properties exposed to QML ---

    @Property(str, notify=currentMonthYearChanged)
    def currentMonthName(self):
        return self._locale.monthName(self._current_date.month(), QLocale.LongFormat)

    @Property(int, notify=currentMonthYearChanged)
    def currentYear(self):
        return self._current_date.year()

    @Property("QVariantList", notify=availableCalendarsChanged)
    def availableCalendarsModel(self):
        return self._available_calendars

    @Property("QVariantList", notify=daysInMonthModelChanged)
    def daysInMonthModel(self):
        """ Provides the model for the calendar grid (list of day dictionaries). """
        return self._days_in_month_model
        
    @Property(str, notify=viewModeChanged)
    def viewMode(self):
        """Return the current view mode."""
        return self._view_mode
        
    @Property("QVariantList", notify=currentRangeDaysChanged)
    def currentRangeDays(self):
        """Return the days in the current date range (for week/3day/day views)."""
        return self._range_days
        
    @Property(str, notify=currentRangeDisplayChanged)
    def currentRangeDisplay(self):
        """Return a formatted string of the current date range."""
        if self._view_mode in self._view_strategies:
            strategy = self._view_strategies[self._view_mode]
            return strategy.format_date_range_display(self, self._range_start_date, self._range_end_date)
        else:
            # Fallback for unknown view modes
            if self._view_mode == "month":
                return f"{self.currentMonthName} {self.currentYear}"
            elif not self._range_start_date or not self._range_end_date:
                return ""
            else:
                return DateUtils.format_date_range(self._range_start_date, self._range_end_date)

    @Property(str, notify=syncStatusChanged)
    def syncStatus(self):
        return self._sync_status

    # --- Slots callable from QML ---
    
    @Slot(str)
    def setViewMode(self, mode):
        """Set the calendar view mode."""
        if mode in self._view_strategies and mode != self._view_mode:
            self._view_mode = mode
            # Update date range for the new view mode
            self._update_date_range()
            self.viewModeChanged.emit(self._view_mode)
            self.currentRangeDaysChanged.emit()
            self.currentRangeDisplayChanged.emit()
        elif mode not in self._view_strategies:
            print(f"Warning: Attempted to set unknown view mode '{mode}'")
            
    @Slot()
    def cycleViewMode(self):
        """Cycle through available view modes in the order: month -> week -> day -> month"""
        current_mode = self._view_mode
        
        # Define the cycle order based on available strategies
        modes = list(self._view_strategies.keys())
        if not modes:
            # Fallback if no strategies are defined
            return
            
        # Prioritize the standard order of modes if they exist
        preferred_order = ["month", "week", "day", "3day"]
        sorted_modes = [mode for mode in preferred_order if mode in modes]
        
        # Add any additional modes not in preferred order
        for mode in modes:
            if mode not in sorted_modes:
                sorted_modes.append(mode)
        
        # Find current index and get next mode
        try:
            current_index = sorted_modes.index(current_mode)
            next_index = (current_index + 1) % len(sorted_modes)
            next_mode = sorted_modes[next_index]
        except ValueError:
            # If current mode not found, default to first mode
            next_mode = sorted_modes[0]
        
        # Set the new mode
        self.setViewMode(next_mode)
        
    @Slot(str, str)
    def goToSpecificDate(self, date_str, view_mode="day"):
        """Navigate to a specific date and set the view mode.
        
        Args:
            date_str: Date string in format 'yyyy-MM-dd'
            view_mode: View mode to set ('month', 'week', 'day', etc.)
        """
        try:
            # Parse the date
            date = QDate.fromString(date_str, "yyyy-MM-dd")
            if not date.isValid():
                print(f"Invalid date: {date_str}")
                return
                
            # Set the current date
            self._current_date = date
            
            # Set the view mode, defaulting to day view if the specified mode is not available
            if view_mode in self._view_strategies:
                self._view_mode = view_mode
            else:
                # Try to use 'day' view as fallback, or the first available strategy
                fallback_mode = "day" if "day" in self._view_strategies else next(iter(self._view_strategies), None)
                if fallback_mode:
                    self._view_mode = fallback_mode
                    print(f"Warning: View mode '{view_mode}' not found, using '{fallback_mode}' instead")
                else:
                    print(f"Error: No view strategies available")
                    return
                
            # Update date range for the new view mode
            self._update_date_range()
            
            # Update models
            self._update_events_and_model()
            
            # Emit signals for UI updates
            self.currentMonthYearChanged.emit()
            self.currentRangeDisplayChanged.emit()
            self.daysInMonthModelChanged.emit()
            self.currentRangeDaysChanged.emit()
            self.viewModeChanged.emit(self._view_mode)
            
        except Exception as e:
            print(f"Error navigating to date {date_str}: {e}")

    @Slot()
    def goToNextMonth(self):
        """Move to next month."""
        try:
            # Signal month change first (before any model changes)
            self._current_date = self._current_date.addMonths(1)
            self._update_date_range()
            self.currentMonthYearChanged.emit()
            self.currentRangeDisplayChanged.emit()
            
            # Update model
            self._update_events_and_model()
            self.daysInMonthModelChanged.emit()
            self.currentRangeDaysChanged.emit()
        except Exception as e:
            print(f"Error in goToNextMonth: {e}")
            
    @Slot()
    def moveDateRangeForward(self):
        """Move the date range forward using the appropriate strategy."""
        if self._view_mode in self._view_strategies:
            # Get the strategy for the current view mode
            strategy = self._view_strategies[self._view_mode]
            
            # Use the strategy to navigate forward
            self._current_date = strategy.navigate_forward(self, self._current_date)
            self._update_date_range()
            
            # Update signals
            self.currentMonthYearChanged.emit()
            self.currentRangeDaysChanged.emit()
            self.currentRangeDisplayChanged.emit()
            
            # For month view, we need to update the events and model
            if self._view_mode == "month":
                self._update_events_and_model()
                self.daysInMonthModelChanged.emit()
        else:
            print(f"Warning: Unknown view mode '{self._view_mode}' for navigation")

    @Slot()
    def goToPreviousMonth(self):
        """Move to previous month."""
        try:
            # Signal month change first (before any model changes)
            self._current_date = self._current_date.addMonths(-1)
            self._update_date_range()
            self.currentMonthYearChanged.emit()
            self.currentRangeDisplayChanged.emit()
            
            # Update model
            self._update_events_and_model()
            self.daysInMonthModelChanged.emit()
            self.currentRangeDaysChanged.emit()
        except Exception as e:
            print(f"Error in goToPreviousMonth: {e}")
            
    @Slot()
    def moveDateRangeBackward(self):
        """Move the date range backward using the appropriate strategy."""
        if self._view_mode in self._view_strategies:
            # Get the strategy for the current view mode
            strategy = self._view_strategies[self._view_mode]
            
            # Use the strategy to navigate backward
            self._current_date = strategy.navigate_backward(self, self._current_date)
            self._update_date_range()
            
            # Update signals
            self.currentMonthYearChanged.emit()
            self.currentRangeDaysChanged.emit()
            self.currentRangeDisplayChanged.emit()
            
            # For month view, we need to update the events and model
            if self._view_mode == "month":
                self._update_events_and_model()
                self.daysInMonthModelChanged.emit()
        else:
            print(f"Warning: Unknown view mode '{self._view_mode}' for navigation")

    @Slot()
    def goToToday(self):
        """Go to current month/date."""
        try:
            current_date = QDate.currentDate()
            if (self._current_date != current_date):
                # Signal change first (before any model changes)
                self._current_date = current_date
                self._update_date_range()
                self.currentMonthYearChanged.emit()
                self.currentRangeDisplayChanged.emit()
                
                # Update model
                self._update_events_and_model()
                self.daysInMonthModelChanged.emit()
                self.currentRangeDaysChanged.emit()
        except Exception as e:
            print(f"Error in goToToday: {e}")

    @Slot()
    def refreshEvents(self):
        """Refresh calendar data from Google Calendar."""
        try:
            self._sync_status = "Syncing..."
            self.syncStatusChanged.emit(self._sync_status)
            
            # Fetch calendars and events
            self._available_calendars = self._get_google_calendars()
            
            # Filter out any blocked calendars that might have been previously loaded
            blocked_names = self._google_client.BLOCKED_CALENDAR_NAMES
            self._available_calendars = [cal for cal in self._available_calendars 
                                        if cal["name"] not in blocked_names]
            
            self._all_events = self._get_google_events()
            
            self._update_events_and_model(fetch_new_events=False)
            self.availableCalendarsChanged.emit()
            QTimer.singleShot(0, self.daysInMonthModelChanged.emit)
            
            # Update range days for custom views
            self._update_range_days()
            self.currentRangeDaysChanged.emit()
            
            self._sync_status = "Synced"
            self.syncStatusChanged.emit(self._sync_status)
        except Exception as e:
            self._sync_status = f"Error: {str(e)}"
            self.syncStatusChanged.emit(self._sync_status)

    @Slot(str, bool)
    def setCalendarVisibility(self, calendarId, isVisible):
        """Set the visibility of a calendar."""
        updated = False
        for cal in self._available_calendars:
            if cal["id"] == calendarId:
                if cal["is_visible"] != isVisible:
                    cal["is_visible"] = isVisible
                    updated = True
                break

        if updated:
            self._update_events_and_model(fetch_new_events=False)
            self.availableCalendarsChanged.emit()
            QTimer.singleShot(0, self.daysInMonthModelChanged.emit)
            
            # Update range days for custom views
            self._update_range_days()
            self.currentRangeDaysChanged.emit()

    # --- Helper Methods ---
    
    def _update_date_range(self):
        """Update the date range based on the current view mode and date."""
        # Get the strategy for the current view mode
        if self._view_mode in self._view_strategies:
            # Let the strategy handle date range calculation
            strategy = self._view_strategies[self._view_mode]
            strategy.update_date_range(self, self._current_date)
        else:
            # Fallback for unknown view modes
            print(f"Warning: Unknown view mode '{self._view_mode}', defaulting to day view")
            self._range_start_date = QDate(self._current_date)
            self._range_end_date = QDate(self._current_date)
        
        # Update range days
        self._update_range_days()
        
    def _update_range_days(self):
        """Update the range days model for custom views."""
        if self._view_mode == "month":
            self._range_days = []
            return
            
        if not self._range_start_date or not self._range_end_date:
            self._range_days = []
            return
            
        # Create range days
        result = []
        current_date = self._range_start_date
        today = QDate.currentDate()
        
        while current_date <= self._range_end_date:
            # Get events for this day
            date_str = DateUtils.to_string(current_date, DateUtils.FORMAT_ISO)
            
            # Find regular events for this day
            regular_events = []
            multi_day_events = []
            
            for event in self._filtered_events:
                event_start_date = DateUtils.to_qdate(event.get("start_date", ""))
                event_end_date = DateUtils.to_qdate(event.get("end_date", ""))
                
                # Skip if dates are invalid
                if not event_start_date or not event_end_date or not event_start_date.isValid() or not event_end_date.isValid():
                    continue
                    
                # Check if event is on this day
                if event_start_date <= current_date and current_date <= event_end_date:
                    # Clone the event to avoid modifying the original
                    event_copy = event.copy()
                    
                    # Mark if this is a multi-day event
                    is_multi_day = DateUtils.days_between(event_start_date, event_end_date) > 0
                    
                    if is_multi_day:
                        event_copy["is_multi_day"] = True
                        event_copy["isStart"] = DateUtils.is_same_day(event_start_date, current_date)
                        event_copy["isEnd"] = DateUtils.is_same_day(event_end_date, current_date)
                        multi_day_events.append(event_copy)
                    else:
                        event_copy["is_multi_day"] = False
                        
                        # Add time formatting for day view
                        if "start_time" in event and event["start_time"]:
                            try:
                                start_time = datetime.fromisoformat(event["start_time"])
                                event_copy["timeDisplay"] = DateUtils.to_string(start_time, DateUtils.FORMAT_TIME)
                            except (ValueError, TypeError):
                                event_copy["timeDisplay"] = ""
                                
                        regular_events.append(event_copy)
            
            # Create day data
            day_data = {
                "date": current_date.toPython(),
                "date_str": date_str,
                "day": str(current_date.day()),
                "dayName": self._locale.standaloneDayName(current_date.dayOfWeek(), QLocale.ShortFormat),
                "isToday": current_date == today,
                "events": regular_events,
                "multiDayEvents": multi_day_events
            }
            
            result.append(day_data)
            current_date = current_date.addDays(1)
            
        self._range_days = result

    def _update_events_and_model(self, fetch_new_events=True):
        """Fetches/refreshes events and recalculates the days model."""
        try:
            # Keep a copy of the old model in case we need to revert
            old_model = self._days_in_month_model.copy() if self._days_in_month_model else []
            
            if fetch_new_events:
                if not self._available_calendars:
                    self._available_calendars = self._get_google_calendars()
                    # Filter out any blocked calendars
                    blocked_names = self._google_client.BLOCKED_CALENDAR_NAMES
                    self._available_calendars = [cal for cal in self._available_calendars 
                                               if cal["name"] not in blocked_names]
                self._all_events = self._get_google_events()
            
            # Process events first without changing the model
            self._filtered_events = self._filter_events()
            new_model = self._calculate_days_model()
            
            # Only update model if we have a valid new model
            if new_model:
                self._days_in_month_model = new_model
            else:
                if not old_model:
                    # If we don't have an old model to revert to, create a basic empty grid
                    self._days_in_month_model = self._create_empty_grid()
                else:
                    self._days_in_month_model = old_model
                    
            # Update range days for custom views
            self._update_range_days()
        except Exception as e:
            print(f"Error updating calendar model: {e}")
            # If there was an error, make sure we have at least an empty grid
            if not self._days_in_month_model:
                self._days_in_month_model = self._create_empty_grid()

    def _create_empty_grid(self):
        """Creates a basic empty grid with just dates, no events."""
        days_model = []
        today = QDate.currentDate()
        year = self._current_date.year()
        month = self._current_date.month()
        first_day_of_month = QDate(year, month, 1)
        start_day_offset = first_day_of_month.dayOfWeek() - 1
        grid_start_date = first_day_of_month.addDays(-start_day_offset)
        
        # Fill in basic day data
        current_grid_date = grid_start_date
        for day_idx in range(42): # 6 weeks * 7 days
            week_idx = day_idx // 7
            day_position = day_idx % 7
            
            day_data = {
                "date_str": current_grid_date.toString("yyyy-MM-dd"),
                "dayNumber": current_grid_date.day(),
                "isCurrentMonth": current_grid_date.month() == month,
                "isToday": current_grid_date == today,
                "events": [],
                "day_idx": day_idx,
                "week_idx": week_idx,
                "day_position": day_position,
                "multi_day_events": []
            }
            
            days_model.append(day_data)
            current_grid_date = current_grid_date.addDays(1)
            
        return days_model

    def _filter_events(self):
        """Filter events based on calendar visibility."""
        visible_calendar_ids = {cal["id"] for cal in self._available_calendars if cal["is_visible"]}
        return [event for event in self._all_events if event["calendar_id"] in visible_calendar_ids]

    def _get_google_calendars(self):
        """Fetch calendars from Google Calendar API."""
        try:
            calendars = self._google_client.get_calendars()
            return [{
                "id": cal["id"],
                "name": cal["name"],
                "color": cal["color"],
                "is_visible": True  # Default to visible
            } for cal in calendars]
        except Exception as e:
            print(f"Error fetching calendars: {e}")
            return []

    def _get_google_events(self):
        """Fetch events from Google Calendar API for the current month view."""
        try:
            # Calculate date range for the current month view
            first_day = QDate(self._current_date.year(), self._current_date.month(), 1)
            last_day = QDate(self._current_date.year(), self._current_date.month(), 
                           self._current_date.daysInMonth())
            
            # Add padding for the grid view (6 weeks)
            start_date = first_day.addDays(-(first_day.dayOfWeek() - 1))
            end_date = last_day.addDays(42 - (last_day.dayOfWeek() + last_day.daysInMonth() - first_day.day()))
            
            all_events = []
            for calendar in self._available_calendars:
                if calendar["is_visible"]:
                    events = self._google_client.get_events(
                        calendar["id"],
                        datetime.combine(start_date.toPython(), datetime.min.time()),
                        datetime.combine(end_date.toPython(), datetime.max.time())
                    )
                    # Ensure each event has a proper color from its calendar
                    for event in events:
                        # If event doesn't have a specific color, use the calendar color
                        if not event["color"]:
                            event["color"] = calendar["color"]
                        # Add the calendar display name to the event
                        event["calendar_name"] = calendar["name"]
                    all_events.extend(events)
            
            return all_events
        except Exception as e:
            print(f"Error fetching events: {e}")
            return []

    def _extract_event_dates(self, event):
        """Extract and validate start/end dates from an event."""
        try:
            # Parse the start date using DateUtils
            if event.get("start_time"):
                event["start_date"] = DateUtils.extract_iso_date(event["start_time"])
            else:
                # Skip events without start time
                return False
                
            # Parse the end date using DateUtils
            if event.get("end_time"):
                event["end_date"] = DateUtils.extract_iso_date(event["end_time"])
            else:
                # For events with no end time, use start date
                event["end_date"] = event["start_date"]
                
            # Validate the dates
            start_date = DateUtils.to_qdate(event["start_date"])
            end_date = DateUtils.to_qdate(event["end_date"])
            
            return start_date and end_date and start_date.isValid() and end_date.isValid()
        except Exception as e:
            print(f"Error extracting event dates: {str(e)}")
            return False

    def _create_basic_grid(self):
        """Creates the basic 6x7 grid with dates for the month view."""
        weeks_data = []
        days_model = []
        
        # Setup year, month, and date constants
        year = self._current_date.year()
        month = self._current_date.month()
        today = QDate.currentDate()
        first_day_of_month = QDate(year, month, 1)
        start_day_offset = first_day_of_month.dayOfWeek() - 1
        grid_start_date = first_day_of_month.addDays(-start_day_offset)
        
        # Setup week containers
        for week_idx in range(6):
            week_data = {
                "week_idx": week_idx,
                "days": [],
                "multi_day_events": []
            }
            weeks_data.append(week_data)
        
        # Fill in day data
        current_grid_date = grid_start_date
        for day_idx in range(42):  # 6 weeks * 7 days
            week_idx = day_idx // 7
            day_position = day_idx % 7
            
            day_data = {
                "date_str": current_grid_date.toString("yyyy-MM-dd"),
                "dayNumber": current_grid_date.day(),
                "isCurrentMonth": current_grid_date.month() == month,
                "isToday": current_grid_date == today,
                "events": [],
                "day_idx": day_idx,
                "week_idx": week_idx,
                "day_position": day_position,
                "multi_day_events": []  # Will be populated later
            }
            
            days_model.append(day_data)
            weeks_data[week_idx]["days"].append(day_data)
            current_grid_date = current_grid_date.addDays(1)
        
        return days_model, weeks_data, grid_start_date
        
    def _assign_events_to_days(self, days_model, grid_start_date, weeks_data):
        """Maps events to specific days in the grid."""
        event_to_days = {}  # Maps event IDs to day indices
        
        for event in self._filtered_events:
            # Get start and end dates for the event
            try:
                # Extract and validate date information
                if not self._extract_event_dates(event):
                    continue
                    
                start_date = DateUtils.to_qdate(event["start_date"])
                end_date = DateUtils.to_qdate(event["end_date"])
                
                # Adjust end date for all-day events
                if event.get("all_day", False) and end_date and end_date.isValid():
                    end_date = end_date.addDays(-1)
                    event["end_date"] = DateUtils.to_string(end_date, DateUtils.FORMAT_ISO)
                    
                # Calculate grid positions
                days_difference_start = grid_start_date.daysTo(start_date)
                days_difference_end = grid_start_date.daysTo(end_date)
                
                # Skip events outside our grid
                if days_difference_end < 0 or days_difference_start >= 42:
                    continue
                    
                # Enforce bounds within our grid
                grid_start_idx = max(0, days_difference_start)
                grid_end_idx = min(41, days_difference_end)
                
                # Mark multi-day status
                is_multi_day = grid_end_idx > grid_start_idx
                event_copy = event.copy()
                event_copy["is_multi_day"] = is_multi_day
                
                # Track which days this event appears in
                if event["id"] not in event_to_days:
                    event_to_days[event["id"]] = []
                    
                # Add this event to all relevant days
                for day_idx in range(grid_start_idx, grid_end_idx + 1):
                    days_model[day_idx]["events"].append(event_copy)
                    event_to_days[event["id"]].append(day_idx)
                    
                # Handle multi-day events separately
                if is_multi_day:
                    event_copy["span_days"] = grid_end_idx - grid_start_idx + 1
                    
                    # Process multi-day spans across weeks
                    start_week = grid_start_idx // 7
                    end_week = grid_end_idx // 7
                    
                    # For each week this event spans, create a separate entry
                    for week_idx in range(start_week, end_week + 1):
                        # Calculate the start column within this week
                        if week_idx == start_week:
                            start_col = grid_start_idx % 7
                        else:
                            start_col = 0
                            
                        # Calculate the end column within this week
                        if week_idx == end_week:
                            end_col = grid_end_idx % 7
                        else:
                            end_col = 6
                        
                        # Add this segment to the week's multi-day events
                        week_event = event_copy.copy()
                        week_event["start_col"] = start_col
                        week_event["end_col"] = end_col
                        week_event["continues_left"] = (week_idx > start_week)
                        week_event["continues_right"] = (week_idx < end_week)
                        
                        # Add to list for layout row assignment
                        weeks_data[week_idx]["multi_day_events"].append(week_event)
            except Exception as e:
                # Skip event on error
                continue
                
        return event_to_days, weeks_data
        
    def _assign_event_layout_rows(self, events):
        """Assigns layout rows to multi-day events to avoid visual overlaps."""
        # Sort events by length (descending) and then start time
        events.sort(key=lambda e: (-((e["end_col"] - e["start_col"]) + 1), e["start_time"]))
        
        # Track which positions (row,col) are used
        used_positions = set()  # Set of (row,col) tuples
        
        for event in events:
            # Find the first available row that spans all columns needed
            found_row = -1
            for row_idx in range(10):  # Limit to 10 rows max
                # Check if this row is available for the entire span
                row_available = True
                for col in range(event["start_col"], event["end_col"] + 1):
                    if (row_idx, col) in used_positions:
                        row_available = False
                        break
                        
                if row_available:
                    found_row = row_idx
                    break
            
            # Assign this event to the found row
            if found_row >= 0:
                event["layout_row"] = found_row
                # Mark positions as used
                for col in range(event["start_col"], event["end_col"] + 1):
                    used_positions.add((found_row, col))
            else:
                # If no row found, put it in row 0 (overflows)
                event["layout_row"] = 0
                
    def _process_multi_day_events(self, weeks_data):
        """Handles layout and positioning of multi-day events."""
        # Assign layout rows for each week's events
        for week_data in weeks_data:
            if week_data["multi_day_events"]:
                self._assign_event_layout_rows(week_data["multi_day_events"])
        
        # Add multi-day events to the day objects for easy reference
        for week_idx, week_data in enumerate(weeks_data):
            for day in week_data["days"]:
                # Reference the week's multi-day events from each day
                day["multi_day_events"] = week_data["multi_day_events"]
                
    def _calculate_days_model(self):
        """ 
        Calculates the list of day dictionaries for the grid view.
        Pre-calculates event positions for the UI.
        """
        try:
            # Create the basic grid structure
            days_model, weeks_data, grid_start_date = self._create_basic_grid()
            
            # Process events and assign them to days
            event_to_days, weeks_data = self._assign_events_to_days(days_model, grid_start_date, weeks_data)
            
            # Process multi-day events and calculate their layout
            self._process_multi_day_events(weeks_data)
            
            return days_model
        except Exception as e:
            print(f"Error calculating days model: {e}")
            # Fallback to empty grid on error
            return self._create_empty_grid()


if __name__ == "__main__":
    controller = CalendarController()
    print(f"Month: {controller.currentMonthName} {controller.currentYear}")
    print(f"Calendars: {controller.availableCalendarsModel}")
    print(f"Day Model (first 7 days): {controller.daysInMonthModel[:7]}")

    controller.goToNextMonth()
    print(f"\nMonth: {controller.currentMonthName} {controller.currentYear}")
    print(f"Day Model (first 7 days): {controller.daysInMonthModel[:7]}")

    controller.setCalendarVisibility("cal3", True)
    print(f"\nCalendars: {controller.availableCalendarsModel}")
    print(f"Day Model (day 15 events): {[d for d in controller.daysInMonthModel if d['dayNumber'] == 15 and d['isCurrentMonth']][0]['events']}")
