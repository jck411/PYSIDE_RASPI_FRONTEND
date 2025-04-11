from PySide6.QtCore import QDate
from datetime import datetime, timedelta
import calendar

class DateUtils:
    """
    Utility class for date operations, handling conversions between
    QDate, Python datetime, and string representations.
    """
    
    # Standard format strings
    FORMAT_ISO = "yyyy-MM-dd"
    FORMAT_MONTH_YEAR = "{month} {year}"
    FORMAT_DATE_RANGE = "{start} - {end}"
    FORMAT_FULL_DATE = "%B %d, %Y"
    FORMAT_SHORT_DATE = "%b %d"
    FORMAT_TIME = "%I:%M %p"
    
    @staticmethod
    def to_qdate(date_obj_or_str):
        """Convert Python datetime or string to QDate."""
        if isinstance(date_obj_or_str, str):
            return QDate.fromString(date_obj_or_str, DateUtils.FORMAT_ISO)
        elif isinstance(date_obj_or_str, datetime):
            return QDate.fromString(date_obj_or_str.strftime("%Y-%m-%d"), DateUtils.FORMAT_ISO)
        elif isinstance(date_obj_or_str, QDate):
            return date_obj_or_str
        return None
    
    @staticmethod
    def to_python_date(qdate_or_str):
        """Convert QDate or string to Python datetime."""
        if isinstance(qdate_or_str, str):
            try:
                return datetime.strptime(qdate_or_str, "%Y-%m-%d")
            except ValueError:
                return None
        elif isinstance(qdate_or_str, QDate) and qdate_or_str.isValid():
            return qdate_or_str.toPython()
        elif isinstance(qdate_or_str, datetime):
            return qdate_or_str
        return None
    
    @staticmethod
    def to_string(date_obj, format_str=FORMAT_ISO):
        """Convert date object to string with specified format."""
        if isinstance(date_obj, QDate) and date_obj.isValid():
            return date_obj.toString(format_str)
        elif isinstance(date_obj, datetime):
            # Convert Python format strings to QDate format strings if needed
            if format_str == DateUtils.FORMAT_ISO:
                return date_obj.strftime("%Y-%m-%d")
            elif format_str == DateUtils.FORMAT_FULL_DATE:
                return date_obj.strftime("%B %d, %Y")
            elif format_str == DateUtils.FORMAT_SHORT_DATE:
                return date_obj.strftime("%b %d")
            return date_obj.strftime(format_str)
        return ""
    
    @staticmethod
    def extract_iso_date(datetime_str):
        """Extract ISO date portion from datetime string."""
        if not datetime_str:
            return ""
        return datetime_str.split("T")[0] if "T" in datetime_str else datetime_str
    
    @staticmethod
    def get_start_of_month(year, month):
        """Get QDate for first day of month."""
        return QDate(year, month, 1)
    
    @staticmethod
    def get_end_of_month(year, month):
        """Get QDate for last day of month."""
        days_in_month = calendar.monthrange(year, month)[1]
        return QDate(year, month, days_in_month)
    
    @staticmethod
    def get_month_grid_dates(year, month):
        """
        Get all dates needed for a calendar month grid view (6 weeks).
        Returns tuple of (start_date, end_date, grid_dates)
        """
        first_day = DateUtils.get_start_of_month(year, month)
        last_day = DateUtils.get_end_of_month(year, month)
        
        # Find the Monday before or on the first day of month
        start_day_offset = first_day.dayOfWeek() - 1  # 1 = Monday
        grid_start_date = first_day.addDays(-start_day_offset)
        
        # Calculate end date (42 days from start = 6 weeks)
        grid_end_date = grid_start_date.addDays(41)
        
        # Generate all dates in the grid
        grid_dates = []
        current_date = QDate(grid_start_date)
        while current_date <= grid_end_date:
            grid_dates.append(QDate(current_date))
            current_date = current_date.addDays(1)
            
        return (grid_start_date, grid_end_date, grid_dates)
    
    @staticmethod
    def get_week_dates(reference_date):
        """
        Get all dates for a week containing the reference date.
        Returns tuple of (start_date, end_date, week_dates)
        """
        qdate = DateUtils.to_qdate(reference_date)
        if not qdate or not qdate.isValid():
            return (None, None, [])
            
        # Find Monday of this week
        day_of_week = qdate.dayOfWeek()  # 1 = Monday, 7 = Sunday
        start_date = qdate.addDays(-(day_of_week - 1))
        end_date = start_date.addDays(6)
        
        # Generate all dates in the week
        week_dates = []
        current_date = QDate(start_date)
        while current_date <= end_date:
            week_dates.append(QDate(current_date))
            current_date = current_date.addDays(1)
            
        return (start_date, end_date, week_dates)
    
    @staticmethod
    def format_date_range(start_date, end_date):
        """Format a date range for display."""
        start = DateUtils.to_python_date(start_date)
        end = DateUtils.to_python_date(end_date)
        
        if not start or not end:
            return ""
        
        # Convert to date objects if they're datetime objects
        start_date_obj = start.date() if hasattr(start, 'date') else start
        end_date_obj = end.date() if hasattr(end, 'date') else end
            
        # Same day
        if start_date_obj == end_date_obj:
            return start.strftime(DateUtils.FORMAT_FULL_DATE)
            
        # Same month and year
        if start.month == end.month and start.year == end.year:
            return f"{start.strftime('%B %d')} - {end.day}, {end.year}"
            
        # Different months
        return f"{start.strftime(DateUtils.FORMAT_SHORT_DATE)} - {end.strftime(DateUtils.FORMAT_FULL_DATE)}"
    
    @staticmethod
    def is_same_day(date1, date2):
        """Check if two dates represent the same day."""
        d1 = DateUtils.to_python_date(date1)
        d2 = DateUtils.to_python_date(date2)
        if not d1 or not d2:
            return False
            
        # Convert to date objects if they're datetime objects
        date1_obj = d1.date() if hasattr(d1, 'date') else d1
        date2_obj = d2.date() if hasattr(d2, 'date') else d2
        
        return date1_obj == date2_obj
    
    @staticmethod
    def days_between(start_date, end_date):
        """Calculate number of days between two dates."""
        start = DateUtils.to_qdate(start_date)
        end = DateUtils.to_qdate(end_date)
        if not start.isValid() or not end.isValid():
            return 0
        return start.daysTo(end)
