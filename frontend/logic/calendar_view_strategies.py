"""
Calendar View Strategies Module

This module implements the Strategy Pattern for different calendar view modes.
Each strategy encapsulates the behavior specific to a particular view mode
(month, week, day) and provides a consistent interface for the CalendarController.

This approach has several advantages:
1. Eliminates scattered conditional logic throughout the controller
2. Makes adding new view modes easier (just add a new strategy class)
3. Improves maintainability by organizing related code together
4. Supports the DRY principle by consolidating view-specific logic
"""

from abc import ABC, abstractmethod
from PySide6.QtCore import QDate
from .date_utils import DateUtils

class CalendarViewStrategy(ABC):
    """
    Abstract base class defining the interface for calendar view strategies.
    Each view mode (month, week, day) implements this interface.
    """
    
    @abstractmethod
    def update_date_range(self, controller, current_date):
        """
        Calculate and update the date range for this view.
        
        Args:
            controller: The CalendarController instance
            current_date: The current reference QDate
        """
        pass
    
    @abstractmethod
    def format_date_range_display(self, controller, start_date, end_date):
        """
        Format the date range for display.
        
        Args:
            controller: The CalendarController instance
            start_date: Start QDate of the range
            end_date: End QDate of the range
            
        Returns:
            str: Formatted date range string
        """
        pass
    
    @abstractmethod
    def navigate_forward(self, controller, current_date):
        """
        Navigate forward in this view.
        
        Args:
            controller: The CalendarController instance
            current_date: The current reference QDate
            
        Returns:
            QDate: The new reference date after navigation
        """
        pass
    
    @abstractmethod
    def navigate_backward(self, controller, current_date):
        """
        Navigate backward in this view.
        
        Args:
            controller: The CalendarController instance
            current_date: The current reference QDate
            
        Returns:
            QDate: The new reference date after navigation
        """
        pass


class MonthViewStrategy(CalendarViewStrategy):
    """Strategy implementation for month view."""
    
    def update_date_range(self, controller, current_date):
        """
        Month view doesn't use range_start/end_date directly.
        It uses the days_in_month_model which is calculated separately.
        """
        # No specific date range to update for month view
        pass
    
    def format_date_range_display(self, controller, start_date, end_date):
        """Format month and year display for month view."""
        return f"{controller.currentMonthName} {controller.currentYear}"
    
    def navigate_forward(self, controller, current_date):
        """Move to the next month."""
        return current_date.addMonths(1)
    
    def navigate_backward(self, controller, current_date):
        """Move to the previous month."""
        return current_date.addMonths(-1)


class WeekViewStrategy(CalendarViewStrategy):
    """Strategy implementation for week view."""
    
    def update_date_range(self, controller, current_date):
        """Update date range to show a full week."""
        start_date, end_date, _ = DateUtils.get_week_dates(current_date)
        controller._range_start_date = start_date
        controller._range_end_date = end_date
    
    def format_date_range_display(self, controller, start_date, end_date):
        """Format date range for week view."""
        if not start_date or not end_date:
            return ""
        return DateUtils.format_date_range(start_date, end_date)
    
    def navigate_forward(self, controller, current_date):
        """Move to the next week."""
        return current_date.addDays(7)
    
    def navigate_backward(self, controller, current_date):
        """Move to the previous week."""
        return current_date.addDays(-7)


class DayViewStrategy(CalendarViewStrategy):
    """Strategy implementation for single day view."""
    
    def update_date_range(self, controller, current_date):
        """Update date range to show a single day."""
        controller._range_start_date = QDate(current_date)
        controller._range_end_date = QDate(current_date)
    
    def format_date_range_display(self, controller, start_date, end_date):
        """Format date display for single day view."""
        if not start_date:
            return ""
        return DateUtils.format_date_range(start_date, start_date)
    
    def navigate_forward(self, controller, current_date):
        """Move to the next day."""
        return current_date.addDays(1)
    
    def navigate_backward(self, controller, current_date):
        """Move to the previous day."""
        return current_date.addDays(-1)


class ThreeDayViewStrategy(CalendarViewStrategy):
    """Strategy implementation for three-day view."""
    
    def update_date_range(self, controller, current_date):
        """Update date range to show three days."""
        controller._range_start_date = QDate(current_date)
        controller._range_end_date = QDate(current_date.addDays(2))
    
    def format_date_range_display(self, controller, start_date, end_date):
        """Format date range for three-day view."""
        if not start_date or not end_date:
            return ""
        return DateUtils.format_date_range(start_date, end_date)
    
    def navigate_forward(self, controller, current_date):
        """Move forward by three days."""
        return current_date.addDays(3)
    
    def navigate_backward(self, controller, current_date):
        """Move backward by three days."""
        return current_date.addDays(-3)
