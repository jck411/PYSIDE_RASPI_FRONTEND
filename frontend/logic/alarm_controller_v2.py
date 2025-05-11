#!/usr/bin/env python3
import json
import os
import uuid
from datetime import datetime
from pathlib import Path
import logging

from PySide6.QtCore import QObject, Signal, Slot, QTimer, QTime, QDateTime, QDate
from PySide6.QtCore import QAbstractListModel, Qt, QModelIndex, QByteArray

from utils.alarm_manager_v2 import AlarmManager

logger = logging.getLogger(__name__)

class AlarmModel(QAbstractListModel):
    """
    A proper QAbstractListModel implementation for alarms
    """
    IdRole = Qt.ItemDataRole.UserRole + 1
    NameRole = Qt.ItemDataRole.UserRole + 2
    HourRole = Qt.ItemDataRole.UserRole + 3
    MinuteRole = Qt.ItemDataRole.UserRole + 4
    EnabledRole = Qt.ItemDataRole.UserRole + 5
    RecurrenceRole = Qt.ItemDataRole.UserRole + 6
    
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
            return alarm.get("id", "")
        elif role == self.NameRole:
            return alarm.get("label", "")  # Use 'label' from v2 manager
        elif role == self.HourRole:
            return alarm.get("hour", 0)
        elif role == self.MinuteRole:
            return alarm.get("minute", 0)
        elif role == self.EnabledRole:
            return alarm.get("is_enabled", False)  # Use 'is_enabled' from v2 manager
        elif role == self.RecurrenceRole:
            # Convert days_of_week set/list to a list for QML
            days = alarm.get("days_of_week", [])
            if isinstance(days, set):
                days = sorted(list(days))
            return days
        
        return None
        
    def roleNames(self):
        return {
            self.IdRole: QByteArray(b"id"),
            self.NameRole: QByteArray(b"name"),  # Keep as 'name' for QML compatibility
            self.HourRole: QByteArray(b"hour"),
            self.MinuteRole: QByteArray(b"minute"),
            self.EnabledRole: QByteArray(b"enabled"),  # Keep as 'enabled' for QML compatibility
            self.RecurrenceRole: QByteArray(b"recurrence")  # Keep as 'recurrence' for QML compatibility
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
    Uses the efficient AlarmManager v2 which schedules precise timers for each alarm.
    Provides a QML-friendly interface that maintains compatibility with existing code.
    """
    # Signals
    alarmTriggered = Signal(str, str)  # ID, name
    alarmsChanged = Signal()
    
    def __init__(self):
        super().__init__()
        
        # Create the alarm manager
        self._alarm_manager = AlarmManager(app_name="AlarmController")
        
        # Connect to alarm manager signals
        self._alarm_manager.alarmTriggered.connect(self._handle_alarm_triggered_from_manager)
        self._alarm_manager.alarmsChanged.connect(self._handle_alarms_changed_from_manager)
        
        # Create the model
        self._alarm_model = AlarmModel(self)
        
        # Initialize the model with current alarms
        self._update_model()
        
        logger.info("AlarmController initialized")
    
    @Slot(str, int, int, bool, list, result=str)
    def addAlarm(self, name, hour, minute, enabled, recurrence):
        """
        Add a new alarm
        
        Args:
            name: Display name for the alarm
            hour: Hour (0-23)
            minute: Minute (0-59)
            enabled: Whether the alarm is active
            recurrence: List of days to repeat (e.g., [0, 2, 4] for Mon, Wed, Fri)
            
        Returns:
            ID of the new alarm
        """
        logger.info(f"Adding alarm: {hour}:{minute} Label: {name} Days: {recurrence}")
        
        try:
            # Convert recurrence to days_of_week format
            logger.debug(f"Converting recurrence to days_of_week format: {recurrence}")
            days_of_week = self._convert_recurrence_to_days(recurrence)
            logger.debug(f"Converted days_of_week: {days_of_week}")
            
            # Add the alarm using the manager
            logger.debug(f"Calling alarm_manager.add_alarm with hour={hour}, minute={minute}, label='{name}', days_of_week={days_of_week}, is_enabled={enabled}")
            alarm_id = self._alarm_manager.add_alarm(
                hour=hour,
                minute=minute,
                label=name,
                days_of_week=days_of_week,
                is_enabled=enabled
            )
            
            logger.info(f"Successfully added alarm with ID: {alarm_id}")
            # Model will be updated via the alarmsChanged signal
            return alarm_id
            
        except Exception as e:
            logger.error(f"Error adding alarm: {e}", exc_info=True)
            return ""
    
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
        logger.info(f"Updating alarm {alarm_id}: {hour}:{minute} Label: {name} Days: {recurrence}")
        
        try:
            # Convert recurrence to days_of_week format
            days_of_week = self._convert_recurrence_to_days(recurrence)
            
            # Update the alarm using the manager
            self._alarm_manager.update_alarm(
                alarm_id=alarm_id,
                hour=hour,
                minute=minute,
                label=name,
                days_of_week=days_of_week,
                is_enabled=enabled
            )
            
            # Model will be updated via the alarmsChanged signal
            
        except Exception as e:
            logger.error(f"Error updating alarm: {e}")
    
    @Slot(str, bool)
    def setAlarmEnabled(self, alarm_id, enabled):
        """
        Enable or disable an alarm
        
        Args:
            alarm_id: ID of the alarm to update
            enabled: New enabled state
        """
        logger.info(f"Setting alarm {alarm_id} enabled: {enabled}")
        
        try:
            # Update the alarm using the manager
            self._alarm_manager.set_alarm_enabled(alarm_id, enabled)
            
            # Model will be updated via the alarmsChanged signal
            
        except Exception as e:
            logger.error(f"Error setting alarm enabled: {e}")
    
    @Slot(str)
    def deleteAlarm(self, alarm_id):
        """
        Delete an alarm
        
        Args:
            alarm_id: ID of the alarm to delete
        """
        logger.info(f"Deleting alarm with ID: {alarm_id}")
        
        try:
            # Delete the alarm using the manager
            success = self._alarm_manager.delete_alarm(alarm_id)
            
            if success:
                logger.info(f"Successfully deleted alarm {alarm_id}")
            else:
                logger.warning(f"Failed to delete alarm with ID: {alarm_id}, no matching alarm found")
            
            # Model will be updated via the alarmsChanged signal
            
        except Exception as e:
            logger.error(f"Error deleting alarm: {e}")
    
    @Slot(result=list)
    def getAlarms(self):
        """
        Get the list of all alarms
        
        Returns:
            List of alarm objects
        """
        # Get alarms from the manager
        alarms = self._alarm_manager.get_all_alarms()
        
        # Convert to QML-friendly format
        qml_alarms = []
        for alarm in alarms:
            qml_alarm = self._convert_alarm_to_qml(alarm)
            qml_alarms.append(qml_alarm)
            
        return qml_alarms
    
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
        # Get the alarm from the manager
        alarm = self._alarm_manager.get_alarm(alarm_id)
        
        # Convert to QML-friendly format if found
        if alarm:
            return self._convert_alarm_to_qml(alarm)
            
        return None
    
    @Slot()
    def clearAllAlarms(self):
        """
        Delete all alarms and start fresh
        """
        logger.info("Clearing all alarms from the system")
        
        try:
            # Clear all alarms using the manager
            self._alarm_manager.clear_all_alarms()
            
            # Model will be updated via the alarmsChanged signal
            
        except Exception as e:
            logger.error(f"Error clearing alarms: {e}")
    
    def _handle_alarm_triggered_from_manager(self, alarm):
        """
        Handle when an alarm is triggered from the manager
        
        Args:
            alarm: Alarm dictionary from the manager
        """
        alarm_id = alarm.get('id', '')
        alarm_label = alarm.get('label', 'Alarm')
        
        logger.info(f"Alarm triggered from manager: {alarm_id} - {alarm_label}")
        
        # Emit the signal for QML
        self.alarmTriggered.emit(alarm_id, alarm_label)
    
    def _handle_alarms_changed_from_manager(self):
        """
        Handle when alarms are changed in the manager
        """
        logger.info("Alarms changed in manager, updating model")
        
        # Update the model
        self._update_model()
        
        # Emit the signal for QML
        self.alarmsChanged.emit()
    
    def _update_model(self):
        """
        Update the model with the current alarms from the manager
        """
        # Get alarms from the manager
        alarms = self._alarm_manager.get_all_alarms()
        
        # Set the alarms in the model
        self._alarm_model.setAlarms(alarms)
    
    def _convert_recurrence_to_days(self, recurrence):
        """
        Convert QML recurrence format to days_of_week format
        
        Args:
            recurrence: List of days or special strings from QML
            
        Returns:
            Set of day indices (0=Monday, 6=Sunday)
        """
        # Handle special string values
        if isinstance(recurrence, list):
            # If it's already a list of integers, just convert to set
            if all(isinstance(x, int) for x in recurrence):
                return set(recurrence)
                
            # Check for special strings
            if "DAILY" in recurrence:
                return {0, 1, 2, 3, 4, 5, 6}  # All days
            elif "WEEKDAYS" in recurrence:
                return {0, 1, 2, 3, 4}  # Monday-Friday
            elif "WEEKENDS" in recurrence:
                return {5, 6}  # Saturday-Sunday
            elif "ONCE" in recurrence or not recurrence:
                # For one-time alarms, use current day
                current_day = datetime.now().weekday()
                return {current_day}
                
            # Try to convert string day names to indices
            day_map = {"MON": 0, "TUE": 1, "WED": 2, "THU": 3, "FRI": 4, "SAT": 5, "SUN": 6}
            days = set()
            for day in recurrence:
                if isinstance(day, str) and day in day_map:
                    days.add(day_map[day])
                elif isinstance(day, int) and 0 <= day <= 6:
                    days.add(day)
            
            return days if days else {0}  # Default to Monday if conversion fails
            
        # Default to current day for one-time alarms
        current_day = datetime.now().weekday()
        return {current_day}
    
    def _convert_alarm_to_qml(self, alarm):
        """
        Convert alarm from manager format to QML-friendly format
        
        Args:
            alarm: Alarm dictionary from the manager
            
        Returns:
            QML-friendly alarm dictionary
        """
        # Convert days_of_week to recurrence
        days_of_week = alarm.get('days_of_week', set())
        if isinstance(days_of_week, set):
            recurrence = sorted(list(days_of_week))
        else:
            recurrence = days_of_week
            
        # Create QML-friendly alarm
        qml_alarm = {
            "id": alarm.get('id', ''),
            "name": alarm.get('label', 'Alarm'),  # 'label' in manager -> 'name' in QML
            "hour": alarm.get('hour', 0),
            "minute": alarm.get('minute', 0),
            "enabled": alarm.get('is_enabled', False),  # 'is_enabled' in manager -> 'enabled' in QML
            "recurrence": recurrence  # 'days_of_week' in manager -> 'recurrence' in QML
        }
        
        return qml_alarm
