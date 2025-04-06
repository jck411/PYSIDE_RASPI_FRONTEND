import sys
# Revert imports: Remove QAbstractListModel related ones
from PySide6.QtCore import QObject, Signal, Slot, Property, QDate, QLocale, QTimer # Add QTimer
from datetime import datetime, timedelta
import calendar

# Revert inheritance to QObject
class CalendarController(QObject):
    """
    Controller class to manage calendar data and logic for the QML frontend.
    Handles month navigation, event fetching (mocked initially), and calendar visibility.
    """
    # Restore original signals
    currentMonthYearChanged = Signal()
    availableCalendarsChanged = Signal()
    daysInMonthModelChanged = Signal() # Signal for the main grid model

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_date = QDate.currentDate()
        self._locale = QLocale() # Use system default locale for month names

        self._available_calendars = [
            {"id": "cal1", "name": "Personal", "color": "#FF5733", "is_visible": True},
            {"id": "cal2", "name": "Work", "color": "#337BFF", "is_visible": True},
            {"id": "cal3", "name": "Family", "color": "#33FF57", "is_visible": False},
        ]
        self._all_events = [] # Initialize empty, fetch later
        self._filtered_events = [] # Initialize empty
        # Rename internal data store back
        self._days_in_month_model = [] # Initialize empty

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

    # Restore the daysInMonthModel property
    @Property("QVariantList", notify=daysInMonthModelChanged)
    def daysInMonthModel(self):
        """ Provides the model for the calendar grid (list of day dictionaries). """
        return self._days_in_month_model

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
            self._all_events = self._get_mock_events()
        self._filtered_events = self._filter_events()
        # Remove model reset signals, assign directly to original variable name
        self._days_in_month_model = self._calculate_days_model() # Rename calculation method back
        # Signals are emitted by the calling slots

    def _filter_events(self):
        visible_calendar_ids = {cal["id"] for cal in self._available_calendars if cal["is_visible"]}
        return [event for event in self._all_events if event["calendar_id"] in visible_calendar_ids]

    def _get_mock_events(self):
        # (Content remains the same)
        year = self._current_date.year()
        month = self._current_date.month()
        mock_events = []
        if month == 4 and year == 2025: # Example for April 2025
             mock_events.extend([
                {"id": "e1", "calendar_id": "cal1", "title": "Doctor's Appointment", "start_time": f"{year}-04-07T09:15:00", "end_time": f"{year}-04-07T10:00:00", "all_day": False, "color": "#FF5733"},
                {"id": "e2", "calendar_id": "cal2", "title": "Office Days", "start_time": None, "end_time": None, "all_day": True, "color": "#337BFF"},
                {"id": "e3", "calendar_id": "cal2", "title": "Team Sync", "start_time": f"{year}-04-10T14:00:00", "end_time": f"{year}-04-10T15:00:00", "all_day": False, "color": "#337BFF"},
                {"id": "e4", "calendar_id": "cal3", "title": "Mom's Birthday", "start_time": None, "end_time": None, "all_day": True, "color": "#33FF57"},
                {"id": "e5", "calendar_id": "cal1", "title": "Pay Bills", "start_time": f"{year}-04-15T00:00:00", "end_time": f"{year}-04-15T23:59:59", "all_day": True, "color": "#FFBD33"},
                {"id": "e6", "calendar_id": "cal1", "title": "Gym Session", "start_time": f"{year}-04-25T18:30:00", "end_time": f"{year}-04-25T19:30:00", "all_day": False, "color": "#FF5733"},
             ])
        mock_events.append(
             {"id": "egen", "calendar_id": "cal1", "title": "Monthly Review", "start_time": f"{year}-{month:02d}-20T11:00:00", "end_time": f"{year}-{month:02d}-20T12:00:00", "all_day": False, "color": "#FF5733"}
        )
        return mock_events

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