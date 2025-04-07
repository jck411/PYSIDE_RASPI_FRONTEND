import sys
from PySide6.QtCore import QObject, Signal, Slot, Property, QDate, QLocale, QTimer
from datetime import datetime, timedelta
import calendar
from .google_calendar import GoogleCalendarClient

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

    @Property(str, notify=syncStatusChanged)
    def syncStatus(self):
        return self._sync_status

    # --- Slots callable from QML ---

    @Slot()
    def goToNextMonth(self):
        """Move to next month."""
        try:
            # Signal month change first (before any model changes)
            self._current_date = self._current_date.addMonths(1)
            self.currentMonthYearChanged.emit()
            
            # Update model
            self._update_events_and_model()
            self.daysInMonthModelChanged.emit()
        except Exception as e:
            print(f"Error in goToNextMonth: {e}")

    @Slot()
    def goToPreviousMonth(self):
        """Move to previous month."""
        try:
            # Signal month change first (before any model changes)
            self._current_date = self._current_date.addMonths(-1)
            self.currentMonthYearChanged.emit()
            
            # Update model
            self._update_events_and_model()
            self.daysInMonthModelChanged.emit()
        except Exception as e:
            print(f"Error in goToPreviousMonth: {e}")

    @Slot()
    def goToToday(self):
        """Go to current month."""
        try:
            current_date = QDate.currentDate()
            if (self._current_date.month() != current_date.month() or
                    self._current_date.year() != current_date.year()):
                # Signal month change first (before any model changes)
                self._current_date = current_date
                self.currentMonthYearChanged.emit()
                
                # Update model
                self._update_events_and_model()
                self.daysInMonthModelChanged.emit()
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

    # --- Helper Methods ---

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

    def _calculate_days_model(self):
        """ 
        Calculates the list of day dictionaries for the grid view.
        Pre-calculates event positions for the UI.
        """
        # Initialize data structure for weeks
        weeks_data = []
        
        # First, create the basic 6x7 grid with dates
        days_model = []
        today = QDate.currentDate()
        year = self._current_date.year()
        month = self._current_date.month()
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
                "multi_day_events": []  # Will be populated later
            }
            
            days_model.append(day_data)
            weeks_data[week_idx]["days"].append(day_data)
            current_grid_date = current_grid_date.addDays(1)
        
        # Process events
        event_to_days = {}  # Maps event IDs to day indices
        
        for event in self._filtered_events:
            # Get start and end dates
            try:
                # Parse the dates
                if event.get("start_time"):
                    start_date_str = event["start_time"].split("T")[0] if "T" in event["start_time"] else event["start_time"]
                    event["start_date"] = start_date_str
                else:
                    # Skip events without start time
                    continue
                    
                if event.get("end_time"):
                    end_date_str = event["end_time"].split("T")[0] if "T" in event["end_time"] else event["end_time"]
                    event["end_date"] = end_date_str
                else:
                    # For events with no end time, use start date
                    event["end_date"] = event["start_date"]
                    
                start_date = QDate.fromString(event["start_date"], "yyyy-MM-dd")
                end_date = QDate.fromString(event["end_date"], "yyyy-MM-dd")
                
                # If all-day event, Google Calendar sets the end date to the day after
                if event.get("all_day", False) and end_date.isValid():
                    end_date = end_date.addDays(-1)
                    event["end_date"] = end_date.toString("yyyy-MM-dd")
                    
                # Validate dates
                if not start_date.isValid() or not end_date.isValid():
                    continue
                
                # Calculate start/end position in the grid
                days_difference_start = grid_start_date.daysTo(start_date)
                days_difference_end = grid_start_date.daysTo(end_date)
                
                # Skip if the event is completely outside our grid
                if days_difference_end < 0 or days_difference_start >= 42:
                    continue
            except Exception as e:
                continue

            # Enforce bounds within our grid (for events that extend beyond it)
            grid_start_idx = max(0, days_difference_start)
            grid_end_idx = min(41, days_difference_end)
            
            # Mark as multi-day if spanning multiple days
            is_multi_day = grid_end_idx > grid_start_idx
            
            # Add a marker for multi-day status to the event
            event_copy = event.copy()
            event_copy["is_multi_day"] = is_multi_day
            
            # For multi-day events, we need special handling
            if is_multi_day:
                event_copy["span_days"] = grid_end_idx - grid_start_idx + 1
                
                # Find which weeks this event spans
                start_week = grid_start_idx // 7
                end_week = grid_end_idx // 7
                
                # For each week this event spans, create a separate entry
                for week_idx in range(start_week, end_week + 1):
                    # Calculate the start column (day position) within this week
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
                    
                    # Queue it for layout row assignment
                    weeks_data[week_idx]["multi_day_events"].append(week_event)
            
            # Add this event to all relevant days
            for day_idx in range(grid_start_idx, grid_end_idx + 1):
                days_model[day_idx]["events"].append(event_copy)
                
                # Track which days each event appears in
                if event["id"] not in event_to_days:
                    event_to_days[event["id"]] = []
                event_to_days[event["id"]].append(day_idx)
        
        # Now, assign layout rows for multi-day events in each week
        for week_data in weeks_data:
            # Sort events by length (descending) and then start time
            week_data["multi_day_events"].sort(
                key=lambda e: (-((e["end_col"] - e["start_col"]) + 1), e["start_time"])
            )
            
            # Track which positions (row,col) are used
            used_positions = set()  # Set of (row,col) tuples
            
            for event in week_data["multi_day_events"]:
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
        
        # Add multi-day events to the day objects for easy reference
        for week_idx, week_data in enumerate(weeks_data):
            for day in week_data["days"]:
                # Reference the week's multi-day events from each day
                day["multi_day_events"] = week_data["multi_day_events"]
        
        return days_model


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