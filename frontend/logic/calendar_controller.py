import sys
# Revert imports: Remove QAbstractListModel related ones
from PySide6.QtCore import QObject, Signal, Slot, Property, QDate, QLocale, QTimer # Add QTimer
from datetime import datetime, timedelta
import calendar
from .google_calendar import GoogleCalendarClient

# Revert inheritance to QObject
class CalendarController(QObject):
    """
    Controller class to manage calendar data and logic for the QML frontend.
    Handles month navigation, event fetching from Google Calendar, and calendar visibility.
    """
    # Restore original signals
    currentMonthYearChanged = Signal()
    availableCalendarsChanged = Signal()
    daysInMonthModelChanged = Signal() # Signal for the main grid model
    syncStatusChanged = Signal(str)  # New signal for sync status

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_date = QDate.currentDate()
        self._locale = QLocale() # Use system default locale for month names
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
        self._current_date = self._current_date.addMonths(1)
        print(f"Navigating to next month: {self._current_date.toString('yyyy-MM')}")
        self._update_events_and_model()
        self.currentMonthYearChanged.emit()
        # Delay model signal emission slightly
        QTimer.singleShot(0, self.daysInMonthModelChanged.emit)

    @Slot()
    def goToPreviousMonth(self):
        self._current_date = self._current_date.addMonths(-1)
        print(f"Navigating to previous month: {self._current_date.toString('yyyy-MM')}")
        self._update_events_and_model()
        self.currentMonthYearChanged.emit()
        # Delay model signal emission slightly
        QTimer.singleShot(0, self.daysInMonthModelChanged.emit)

    @Slot()
    def goToToday(self):
        today = QDate.currentDate()
        if self._current_date.month() != today.month() or self._current_date.year() != today.year():
            self._current_date = today
            print(f"Navigating to today: {self._current_date.toString('yyyy-MM')}")
            self._update_events_and_model()
            self.currentMonthYearChanged.emit()
            # Delay model signal emission slightly
            QTimer.singleShot(0, self.daysInMonthModelChanged.emit)

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
        updated = False
        for cal in self._available_calendars:
            if cal["id"] == calendarId:
                if cal["is_visible"] != isVisible:
                    cal["is_visible"] = isVisible
                    updated = True
                    print(f"Set visibility for {cal['name']} ({calendarId}) to {isVisible}")
                break

        if updated:
            self._update_events_and_model(fetch_new_events=False) # Don't re-fetch, just refilter
            self.availableCalendarsChanged.emit()
            # Delay model signal emission slightly
            QTimer.singleShot(0, self.daysInMonthModelChanged.emit)

    # --- Helper Methods ---

    def _update_events_and_model(self, fetch_new_events=True):
        """Fetches/refreshes events and recalculates the days model."""
        if fetch_new_events:
            if not self._available_calendars:
                self._available_calendars = self._get_google_calendars()
                # Filter out any blocked calendars
                blocked_names = self._google_client.BLOCKED_CALENDAR_NAMES
                self._available_calendars = [cal for cal in self._available_calendars 
                                           if cal["name"] not in blocked_names]
            self._all_events = self._get_google_events()
        
        self._filtered_events = self._filter_events()
        self._days_in_month_model = self._calculate_days_model()

    def _filter_events(self):
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

    # Rename calculation method back
    def _calculate_days_model(self):
        """ Calculates the list of day dictionaries for the grid view. """
        # (Content remains the same)
        days_model = []
        today = QDate.currentDate()
        year = self._current_date.year()
        month = self._current_date.month()
        first_day_of_month = QDate(year, month, 1)
        start_day_offset = first_day_of_month.dayOfWeek() - 1
        grid_start_date = first_day_of_month.addDays(-start_day_offset)
        current_grid_date = grid_start_date

        for _ in range(42): # 6 weeks * 7 days
            day_data = {
                "date_str": current_grid_date.toString("yyyy-MM-dd"),
                "dayNumber": current_grid_date.day(),
                "isCurrentMonth": current_grid_date.month() == month,
                "isToday": current_grid_date == today,
                "events": []
            }
            date_str = day_data["date_str"]
            for event in self._filtered_events:
                event_date_str = None
                if event.get("start_time"):
                    event_date_str = event["start_time"][:10]
                elif event.get("all_day"):
                     if current_grid_date.day() == 15 and current_grid_date.month() == month: # Mock logic
                          event_date_str = date_str
                if event_date_str == date_str:
                    day_data["events"].append(event)

            days_model.append(day_data)
            current_grid_date = current_grid_date.addDays(1)
        return days_model


# Restore original example usage block
if __name__ == "__main__":
    controller = CalendarController()
    print(f"Month: {controller.currentMonthName} {controller.currentYear}")
    print(f"Calendars: {controller.availableCalendarsModel}")
    # print(f"Filtered Events: {controller._filtered_events}") # Filtered events are now inside days model
    print(f"Day Model (first 7 days): {controller.daysInMonthModel[:7]}")

    controller.goToNextMonth()
    print(f"\nMonth: {controller.currentMonthName} {controller.currentYear}")
    print(f"Day Model (first 7 days): {controller.daysInMonthModel[:7]}")

    controller.setCalendarVisibility("cal3", True) # Make Family visible
    print(f"\nCalendars: {controller.availableCalendarsModel}")
    print(f"Day Model (day 15 events): {[d for d in controller.daysInMonthModel if d['dayNumber'] == 15 and d['isCurrentMonth']][0]['events']}")