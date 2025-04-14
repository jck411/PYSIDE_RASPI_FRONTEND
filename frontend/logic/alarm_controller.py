#!/usr/bin/env python3
import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from PySide6.QtCore import QObject, Signal, Slot, QTimer, QTime, QDateTime, QDate
from PySide6.QtCore import QAbstractListModel, Qt, QModelIndex

class AlarmModel(QAbstractListModel):
    """
    A proper QAbstractListModel implementation for alarms
    """
    IdRole = Qt.UserRole + 1
    NameRole = Qt.UserRole + 2
    HourRole = Qt.UserRole + 3
    MinuteRole = Qt.UserRole + 4
    EnabledRole = Qt.UserRole + 5
    RecurrenceRole = Qt.UserRole + 6
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._alarms = []
        
    def rowCount(self, parent=QModelIndex()):
        return len(self._alarms)
        
    def data(self, index, role):
        if not index.isValid() or index.row() >= len(self._alarms):
            return None
            
        alarm = self._alarms[index.row()]
        
        if role == self.IdRole:
            return alarm["id"]
        elif role == self.NameRole:
            return alarm["name"]
        elif role == self.HourRole:
            return alarm["hour"]
        elif role == self.MinuteRole:
            return alarm["minute"]
        elif role == self.EnabledRole:
            return alarm["enabled"]
        elif role == self.RecurrenceRole:
            return alarm["recurrence"]
        
        return None
        
    def roleNames(self):
        return {
            self.IdRole: b"id",
            self.NameRole: b"name",
            self.HourRole: b"hour",
            self.MinuteRole: b"minute",
            self.EnabledRole: b"enabled",
            self.RecurrenceRole: b"recurrence"
        }
        
    def setAlarms(self, alarms):
        self.beginResetModel()
        self._alarms = alarms
        self.endResetModel()
        
    def getAlarm(self, index):
        if 0 <= index < len(self._alarms):
            return self._alarms[index]
        return None

class AlarmController(QObject):
    """
    Controller class for managing alarm functionality.
    Handles creation, modification, deletion, and triggering of alarms.
    Uses an event-based approach with a single timer that recalculates
    when the next alarm should trigger.
    """
    # Signals
    alarmTriggered = Signal(str, str)  # ID, name
    alarmsChanged = Signal()
    
    def __init__(self):
        super().__init__()
        self._alarms = []
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._handle_alarm_triggered)
        self._data_dir = Path(os.path.dirname(os.path.abspath(__file__))).parent / "data"
        self._data_dir.mkdir(exist_ok=True)  # Ensure data directory exists
        self._alarms_file = self._data_dir / "alarms.json"
        
        # Create the model
        self._alarm_model = AlarmModel(self)
        
        self._load_alarms()
        self._schedule_next_alarm()
    
    @Slot(str, int, int, bool, list, result=str)
    def addAlarm(self, name, hour, minute, enabled, recurrence):
        """
        Add a new alarm
        
        Args:
            name: Display name for the alarm
            hour: Hour (0-23)
            minute: Minute (0-59)
            enabled: Whether the alarm is active
            recurrence: List of days to repeat (e.g., ["MON", "WED", "FRI"], ["DAILY"], ["ONCE"])
            
        Returns:
            ID of the new alarm
        """
        print(f"qml: Adding alarm: {hour}:{minute} Label: {name} Days: {recurrence}")
        alarm_id = str(uuid.uuid4())
        alarm = {
            "id": alarm_id,
            "name": name,
            "hour": hour,
            "minute": minute,
            "enabled": enabled,
            "recurrence": recurrence
        }
        self._alarms.append(alarm)
        self._save_alarms()
        self._schedule_next_alarm()  # Recalculate timer
        
        # Update the model
        self._alarm_model.setAlarms(self._alarms)
        
        self.alarmsChanged.emit()
        return alarm_id
    
    @Slot(str, str, int, int, bool, list)
    def updateAlarm(self, alarm_id, name, hour, minute, enabled, recurrence):
        """
        Update an existing alarm
        
        Args:
            alarm_id: ID of the alarm to update
            name: Display name for the alarm
            hour: Hour (0-23)
            minute: Minute (0-59)
            enabled: Whether the alarm is active
            recurrence: List of days to repeat
        """
        for alarm in self._alarms:
            if alarm["id"] == alarm_id:
                alarm["name"] = name
                alarm["hour"] = hour
                alarm["minute"] = minute
                alarm["enabled"] = enabled
                alarm["recurrence"] = recurrence
                break
        
        self._save_alarms()
        self._schedule_next_alarm()  # Recalculate timer
        
        # Update the model
        self._alarm_model.setAlarms(self._alarms)
        
        self.alarmsChanged.emit()
    
    @Slot(str, bool)
    def setAlarmEnabled(self, alarm_id, enabled):
        """
        Enable or disable an alarm
        
        Args:
            alarm_id: ID of the alarm to update
            enabled: New enabled state
        """
        for alarm in self._alarms:
            if alarm["id"] == alarm_id:
                alarm["enabled"] = enabled
                break
        
        self._save_alarms()
        self._schedule_next_alarm()  # Recalculate timer
        
        # Update the model
        self._alarm_model.setAlarms(self._alarms)
        
        self.alarmsChanged.emit()
    
    @Slot(str)
    def deleteAlarm(self, alarm_id):
        """
        Delete an alarm
        
        Args:
            alarm_id: ID of the alarm to delete
        """
        print(f"qml: Deleting alarm with ID: {alarm_id}")
        old_length = len(self._alarms)
        self._alarms = [a for a in self._alarms if a["id"] != alarm_id]
        new_length = len(self._alarms)
        
        if new_length < old_length:
            print(f"qml: Successfully deleted alarm, removed {old_length - new_length} item(s)")
        else:
            print(f"qml: Failed to delete alarm with ID: {alarm_id}, no matching alarm found")
            
        self._save_alarms()
        self._schedule_next_alarm()  # Recalculate timer
        
        # Update the model
        self._alarm_model.setAlarms(self._alarms)
        
        self.alarmsChanged.emit()
    
    @Slot(result=list)
    def getAlarms(self):
        """
        Get the list of all alarms
        
        Returns:
            List of alarm objects
        """
        return self._alarms
    
    @Slot(result="QObject*")
    def alarmModel(self):
        """
        Get the proper QAbstractListModel for alarms
        
        Returns:
            AlarmModel instance
        """
        return self._alarm_model
    
    @Slot(str, result=dict)
    def getAlarm(self, alarm_id):
        """
        Get a specific alarm by ID
        
        Args:
            alarm_id: ID of the alarm to retrieve
            
        Returns:
            Alarm object or None if not found
        """
        for alarm in self._alarms:
            if alarm["id"] == alarm_id:
                return alarm
        return None
    
    @Slot()
    def clearAllAlarms(self):
        """
        Delete all alarms and start fresh
        """
        print("Clearing all alarms from the system")
        self._alarms = []
        self._save_alarms()
        self._schedule_next_alarm()
        
        # Update the model
        self._alarm_model.setAlarms(self._alarms)
        
        self.alarmsChanged.emit()
        return True
    
    def _handle_alarm_triggered(self):
        """
        Handle when an alarm time is reached
        """
        current_time = QTime.currentTime()
        current_date = QDate.currentDate()
        day_of_week = current_date.dayOfWeek()
        
        # Convert Qt day of week (1-7, Monday=1) to our format
        days = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
        current_day = days[day_of_week - 1]
        
        # Find alarms that should trigger now
        triggered_alarms = []
        for alarm in self._alarms:
            if not alarm["enabled"]:
                continue
                
            alarm_time = QTime(alarm["hour"], alarm["minute"])
            time_diff = current_time.msecsTo(alarm_time)
            
            # Check if time matches (allowing for a small window)
            if abs(time_diff) > 60000:  # More than a minute difference
                continue
                
            # Check recurrence pattern
            recurrence = alarm["recurrence"]
            if "DAILY" in recurrence:
                triggered_alarms.append(alarm)
            elif "WEEKDAYS" in recurrence and current_day in ["MON", "TUE", "WED", "THU", "FRI"]:
                triggered_alarms.append(alarm)
            elif "WEEKENDS" in recurrence and current_day in ["SAT", "SUN"]:
                triggered_alarms.append(alarm)
            elif "ONCE" in recurrence or not recurrence:
                triggered_alarms.append(alarm)
                # Disable one-time alarms after they trigger
                alarm["enabled"] = False
            elif current_day in recurrence:
                triggered_alarms.append(alarm)
        
        # Emit signals for triggered alarms
        for alarm in triggered_alarms:
            self.alarmTriggered.emit(alarm["id"], alarm["name"])
        
        if triggered_alarms:
            self._save_alarms()
            
            # Update the model
            self._alarm_model.setAlarms(self._alarms)
            
            self.alarmsChanged.emit()
        
        # Reschedule for next alarm
        self._schedule_next_alarm()
    
    def _calculate_next_alarm_time(self):
        """
        Find the next alarm time among all active alarms
        
        Returns:
            QDateTime of the next alarm to trigger, or None if no active alarms
        """
        if not self._alarms:
            return None
            
        enabled_alarms = [a for a in self._alarms if a["enabled"]]
        if not enabled_alarms:
            return None
            
        now = QDateTime.currentDateTime()
        current_date = now.date()
        current_time = now.time()
        current_day_idx = current_date.dayOfWeek() - 1  # 0-6, Monday=0
        days = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
        
        # Find the next alarm to trigger
        next_alarm_dt = None
        
        for alarm in enabled_alarms:
            alarm_time = QTime(alarm["hour"], alarm["minute"])
            recurrence = alarm["recurrence"]
            
            # Handle different recurrence patterns
            if "ONCE" in recurrence or not recurrence:
                # For one-time alarms, check if it's today and not passed
                alarm_dt = QDateTime(current_date, alarm_time)
                if alarm_dt > now:
                    if next_alarm_dt is None or alarm_dt < next_alarm_dt:
                        next_alarm_dt = alarm_dt
            
            elif "DAILY" in recurrence:
                # For daily alarms
                alarm_dt = QDateTime(current_date, alarm_time)
                if alarm_dt <= now:
                    # Move to tomorrow
                    alarm_dt = alarm_dt.addDays(1)
                if next_alarm_dt is None or alarm_dt < next_alarm_dt:
                    next_alarm_dt = alarm_dt
            
            elif "WEEKDAYS" in recurrence:
                # For weekday alarms
                day_offset = 0
                while day_offset < 7:
                    check_date = current_date.addDays(day_offset)
                    check_day_idx = check_date.dayOfWeek() - 1
                    is_weekday = check_day_idx < 5  # Monday-Friday
                    
                    if is_weekday:
                        alarm_dt = QDateTime(check_date, alarm_time)
                        if alarm_dt > now:
                            if next_alarm_dt is None or alarm_dt < next_alarm_dt:
                                next_alarm_dt = alarm_dt
                            break
                    day_offset += 1
            
            elif "WEEKENDS" in recurrence:
                # For weekend alarms
                day_offset = 0
                while day_offset < 7:
                    check_date = current_date.addDays(day_offset)
                    check_day_idx = check_date.dayOfWeek() - 1
                    is_weekend = check_day_idx >= 5  # Saturday-Sunday
                    
                    if is_weekend:
                        alarm_dt = QDateTime(check_date, alarm_time)
                        if alarm_dt > now:
                            if next_alarm_dt is None or alarm_dt < next_alarm_dt:
                                next_alarm_dt = alarm_dt
                            break
                    day_offset += 1
            
            else:
                # For custom day patterns
                day_offset = 0
                while day_offset < 7:
                    check_date = current_date.addDays(day_offset)
                    check_day_idx = check_date.dayOfWeek() - 1
                    check_day = days[check_day_idx]
                    
                    if check_day in recurrence:
                        alarm_dt = QDateTime(check_date, alarm_time)
                        if alarm_dt > now:
                            if next_alarm_dt is None or alarm_dt < next_alarm_dt:
                                next_alarm_dt = alarm_dt
                            break
                    day_offset += 1
        
        return next_alarm_dt
    
    def _schedule_next_alarm(self):
        """
        Set timer to trigger at the next alarm time
        """
        next_time = self._calculate_next_alarm_time()
        if next_time:
            now = QDateTime.currentDateTime()
            ms_until_next = now.msecsTo(next_time)
            
            if ms_until_next > 0:
                self._timer.stop()
                self._timer.setSingleShot(True)
                self._timer.setInterval(ms_until_next)
                self._timer.start()
    
    def _load_alarms(self):
        """
        Load alarms from storage
        """
        if not self._alarms_file.exists():
            self._alarms = []
            return
            
        try:
            with open(self._alarms_file, 'r') as file:
                self._alarms = json.load(file)
                
            # Update the model
            self._alarm_model.setAlarms(self._alarms)
        except (json.JSONDecodeError, FileNotFoundError):
            self._alarms = []
    
    def _save_alarms(self):
        """
        Save alarms to storage
        """
        with open(self._alarms_file, 'w') as file:
            json.dump(self._alarms, file, indent=2)
