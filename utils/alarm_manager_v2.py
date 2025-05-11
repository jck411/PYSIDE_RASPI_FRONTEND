#!/usr/bin/env python3
import json
import os
import uuid
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Union

from PySide6.QtCore import QObject, Signal, Slot, QTimer, QTime, QDateTime, QDate

logger = logging.getLogger(__name__)

class AlarmManager(QObject):
    """
    Efficient alarm manager that schedules precise timers for each alarm.
    Instead of periodically checking all alarms, this implementation
    calculates the exact time each alarm should trigger and sets a timer
    for that specific time.
    """
    # Signals
    alarmTriggered = Signal(dict)  # Full alarm data
    alarmsChanged = Signal()
    
    def __init__(self, app_name="AlarmManager"):
        super().__init__()
        self._alarms = []
        self._alarm_timers = {}  # Dict of alarm_id -> QTimer
        self._app_name = app_name
        
        # Set up data directory and file path
        self._data_dir = Path(os.path.dirname(os.path.abspath(__file__))).parent / "frontend" / "data"
        self._data_dir.mkdir(exist_ok=True)  # Ensure data directory exists
        self._alarms_file = self._data_dir / "alarms.json"
        
        # Load existing alarms
        self._load_alarms()
        
        # Schedule all enabled alarms
        self._schedule_all_alarms()
        
        logger.info(f"AlarmManager initialized with {len(self._alarms)} alarms")
    
    def get_all_alarms(self) -> List[Dict[str, Any]]:
        """
        Get all alarms.
        
        Returns:
            List of alarm dictionaries
        """
        return self._alarms
    
    def get_alarm(self, alarm_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific alarm by ID.
        
        Args:
            alarm_id: ID of the alarm to retrieve
            
        Returns:
            Alarm dictionary or None if not found
        """
        for alarm in self._alarms:
            if alarm.get('id') == alarm_id:
                return alarm
        return None
    
    def add_alarm(self, hour: int, minute: int, label: str, 
                 days_of_week: Union[List[int], Set[int]], is_enabled: bool = True) -> str:
        """
        Add a new alarm.
        
        Args:
            hour: Hour (0-23)
            minute: Minute (0-59)
            label: Display name for the alarm
            days_of_week: List or set of days to repeat (0=Monday, 6=Sunday)
            is_enabled: Whether the alarm is active
            
        Returns:
            ID of the new alarm
        """
        logger.debug(f"AlarmManager.add_alarm called with hour={hour}, minute={minute}, label='{label}', days_of_week={days_of_week}, is_enabled={is_enabled}")
        
        # Validate inputs
        if not (0 <= hour <= 23):
            logger.error(f"Hour must be between 0 and 23, got {hour}")
            raise ValueError(f"Hour must be between 0 and 23, got {hour}")
        if not (0 <= minute <= 59):
            logger.error(f"Minute must be between 0 and 59, got {minute}")
            raise ValueError(f"Minute must be between 0 and 59, got {minute}")
        
        # Convert days_of_week to a set for consistent handling
        if isinstance(days_of_week, list):
            days_of_week = set(days_of_week)
            logger.debug(f"Converted days_of_week list to set: {days_of_week}")
        
        # Create new alarm
        alarm_id = str(uuid.uuid4())
        logger.debug(f"Generated new alarm ID: {alarm_id}")
        
        alarm = {
            'id': alarm_id,
            'hour': hour,
            'minute': minute,
            'label': label,
            'days_of_week': days_of_week,
            'is_enabled': is_enabled
        }
        
        logger.debug(f"Created alarm object: {alarm}")
        
        # Add to list and save
        self._alarms.append(alarm)
        logger.debug(f"Added alarm to internal list, now have {len(self._alarms)} alarms")
        
        try:
            self._save_alarms()
            logger.debug(f"Successfully saved alarms to file")
        except Exception as e:
            logger.error(f"Error saving alarms: {e}", exc_info=True)
        
        # Schedule the alarm if enabled
        if is_enabled:
            try:
                self._schedule_alarm(alarm)
                logger.debug(f"Successfully scheduled alarm")
            except Exception as e:
                logger.error(f"Error scheduling alarm: {e}", exc_info=True)
        
        # Emit signal
        logger.debug(f"Emitting alarmsChanged signal")
        self.alarmsChanged.emit()
        
        logger.info(f"Added alarm: {label} at {hour:02d}:{minute:02d}, days: {days_of_week}")
        return alarm_id
    
    def update_alarm(self, alarm_id: str, **changes) -> bool:
        """
        Update an existing alarm.
        
        Args:
            alarm_id: ID of the alarm to update
            **changes: Keyword arguments with fields to update
            
        Returns:
            True if alarm was found and updated, False otherwise
        """
        # Find the alarm
        alarm = None
        for a in self._alarms:
            if a.get('id') == alarm_id:
                alarm = a
                break
        
        if not alarm:
            logger.warning(f"Cannot update alarm {alarm_id}: not found")
            return False
        
        # Validate hour and minute if provided
        if 'hour' in changes and not (0 <= changes['hour'] <= 23):
            raise ValueError(f"Hour must be between 0 and 23, got {changes['hour']}")
        if 'minute' in changes and not (0 <= changes['minute'] <= 59):
            raise ValueError(f"Minute must be between 0 and 59, got {changes['minute']}")
        
        # Convert days_of_week to a set if provided
        if 'days_of_week' in changes and isinstance(changes['days_of_week'], list):
            changes['days_of_week'] = set(changes['days_of_week'])
        
        # Check if we need to reschedule
        needs_reschedule = (
            'hour' in changes or 
            'minute' in changes or 
            'days_of_week' in changes or
            ('is_enabled' in changes and changes['is_enabled'] != alarm.get('is_enabled', False))
        )
        
        # Cancel existing timer if we're rescheduling
        if needs_reschedule and alarm_id in self._alarm_timers:
            self._cancel_alarm_timer(alarm_id)
        
        # Update the alarm
        alarm.update(changes)
        
        # Reschedule if needed
        if needs_reschedule and alarm.get('is_enabled', False):
            self._schedule_alarm(alarm)
        
        # Save changes
        self._save_alarms()
        
        # Emit signal
        self.alarmsChanged.emit()
        
        logger.info(f"Updated alarm {alarm_id}: {changes}")
        return True
    
    def delete_alarm(self, alarm_id: str) -> bool:
        """
        Delete an alarm.
        
        Args:
            alarm_id: ID of the alarm to delete
            
        Returns:
            True if alarm was found and deleted, False otherwise
        """
        # Find the alarm
        found = False
        for i, alarm in enumerate(self._alarms):
            if alarm.get('id') == alarm_id:
                self._alarms.pop(i)
                found = True
                break
        
        if not found:
            logger.warning(f"Cannot delete alarm {alarm_id}: not found")
            return False
        
        # Cancel timer if it exists
        if alarm_id in self._alarm_timers:
            self._cancel_alarm_timer(alarm_id)
        
        # Save changes
        self._save_alarms()
        
        # Emit signal
        self.alarmsChanged.emit()
        
        logger.info(f"Deleted alarm {alarm_id}")
        return True
    
    def set_alarm_enabled(self, alarm_id: str, enabled: bool) -> bool:
        """
        Enable or disable an alarm.
        
        Args:
            alarm_id: ID of the alarm to update
            enabled: New enabled state
            
        Returns:
            True if alarm was found and updated, False otherwise
        """
        return self.update_alarm(alarm_id, is_enabled=enabled)
    
    def clear_all_alarms(self) -> None:
        """
        Delete all alarms.
        """
        # Cancel all timers
        for alarm_id in list(self._alarm_timers.keys()):
            self._cancel_alarm_timer(alarm_id)
        
        # Clear the list
        self._alarms = []
        
        # Save changes
        self._save_alarms()
        
        # Emit signal
        self.alarmsChanged.emit()
        
        logger.info("Cleared all alarms")
    
    def _load_alarms(self) -> None:
        """
        Load alarms from storage.
        """
        if not self._alarms_file.exists():
            self._alarms = []
            return
            
        try:
            with open(self._alarms_file, 'r') as file:
                alarms = json.load(file)
                
                # Convert recurrence to days_of_week if needed (for compatibility)
                for alarm in alarms:
                    if 'recurrence' in alarm and 'days_of_week' not in alarm:
                        # Handle string values like "DAILY", "WEEKDAYS", "WEEKENDS"
                        recurrence = alarm['recurrence']
                        if isinstance(recurrence, list) and all(isinstance(x, int) for x in recurrence):
                            # Already numeric days, just copy
                            alarm['days_of_week'] = set(recurrence)
                        elif "DAILY" in recurrence:
                            alarm['days_of_week'] = {0, 1, 2, 3, 4, 5, 6}  # All days
                        elif "WEEKDAYS" in recurrence:
                            alarm['days_of_week'] = {0, 1, 2, 3, 4}  # Monday-Friday
                        elif "WEEKENDS" in recurrence:
                            alarm['days_of_week'] = {5, 6}  # Saturday-Sunday
                        elif "ONCE" in recurrence or not recurrence:
                            # For one-time alarms, use current day
                            current_day = datetime.now().weekday()
                            alarm['days_of_week'] = {current_day}
                        else:
                            # Try to convert string day names to indices
                            day_map = {"MON": 0, "TUE": 1, "WED": 2, "THU": 3, "FRI": 4, "SAT": 5, "SUN": 6}
                            days = set()
                            for day in recurrence:
                                if day in day_map:
                                    days.add(day_map[day])
                            alarm['days_of_week'] = days if days else {0}  # Default to Monday if conversion fails
                
                self._alarms = alarms
                logger.info(f"Loaded {len(self._alarms)} alarms from {self._alarms_file}")
        except Exception as e:
            logger.error(f"Error loading alarms: {e}")
            self._alarms = []
    
    def _save_alarms(self) -> None:
        """
        Save alarms to storage.
        """
        try:
            # Convert sets to lists for JSON serialization
            alarms_to_save = []
            for alarm in self._alarms:
                alarm_copy = alarm.copy()
                if 'days_of_week' in alarm_copy and isinstance(alarm_copy['days_of_week'], set):
                    alarm_copy['days_of_week'] = sorted(list(alarm_copy['days_of_week']))
                alarms_to_save.append(alarm_copy)
            
            with open(self._alarms_file, 'w') as file:
                json.dump(alarms_to_save, file, indent=2)
                
            logger.info(f"Saved {len(self._alarms)} alarms to {self._alarms_file}")
        except Exception as e:
            logger.error(f"Error saving alarms: {e}")
    
    def _schedule_all_alarms(self) -> None:
        """
        Schedule all enabled alarms.
        """
        for alarm in self._alarms:
            if alarm.get('is_enabled', False):
                self._schedule_alarm(alarm)
    
    def _schedule_alarm(self, alarm: Dict[str, Any]) -> None:
        """
        Schedule a timer for the next occurrence of an alarm.
        
        Args:
            alarm: Alarm dictionary
        """
        alarm_id = alarm.get('id')
        if not alarm_id:
            logger.error("Cannot schedule alarm without ID")
            return
        
        # Calculate when this alarm should next trigger
        next_trigger = self._calculate_next_trigger(alarm)
        if not next_trigger:
            logger.warning(f"Could not determine next trigger time for alarm {alarm_id}")
            return
        
        # Calculate milliseconds until trigger
        now = datetime.now()
        delta = next_trigger - now
        ms_until_trigger = int(delta.total_seconds() * 1000)
        
        if ms_until_trigger <= 0:
            logger.warning(f"Alarm {alarm_id} calculated to trigger in the past, rescheduling for tomorrow")
            # Try again with tomorrow
            next_trigger = self._calculate_next_trigger(alarm, start_date=now.date() + timedelta(days=1))
            if not next_trigger:
                return
            delta = next_trigger - now
            ms_until_trigger = int(delta.total_seconds() * 1000)
        
        # Create a single-shot timer
        timer = QTimer()
        timer.setSingleShot(True)
        timer.setInterval(ms_until_trigger)
        
        # Connect to our handler
        timer.timeout.connect(lambda: self._handle_alarm_triggered(alarm_id))
        
        # Store the timer
        self._alarm_timers[alarm_id] = timer
        
        # Start the timer
        timer.start()
        
        trigger_time = next_trigger.strftime('%Y-%m-%d %H:%M:%S')
        logger.info(f"Scheduled alarm {alarm_id} to trigger at {trigger_time} (in {ms_until_trigger/1000:.1f}s)")
    
    def _cancel_alarm_timer(self, alarm_id: str) -> None:
        """
        Cancel the timer for an alarm.
        
        Args:
            alarm_id: ID of the alarm
        """
        if alarm_id in self._alarm_timers:
            timer = self._alarm_timers[alarm_id]
            timer.stop()
            timer.deleteLater()
            del self._alarm_timers[alarm_id]
            logger.info(f"Cancelled timer for alarm {alarm_id}")
    
    def _calculate_next_trigger(self, alarm: Dict[str, Any], 
                               start_date: Optional[datetime.date] = None) -> Optional[datetime]:
        """
        Calculate the next time an alarm should trigger.
        
        Args:
            alarm: Alarm dictionary
            start_date: Optional date to start calculation from (defaults to today)
            
        Returns:
            Datetime of next trigger, or None if it cannot be determined
        """
        hour = alarm.get('hour')
        minute = alarm.get('minute')
        days_of_week = alarm.get('days_of_week')
        
        if hour is None or minute is None or not days_of_week:
            return None
        
        # Convert to set if it's a list
        if isinstance(days_of_week, list):
            days_of_week = set(days_of_week)
        
        # Start from today or specified date
        now = datetime.now()
        current_date = start_date if start_date else now.date()
        current_time = now.time()
        
        # Check the next 7 days (to handle all possible day patterns)
        for day_offset in range(7):
            check_date = current_date + timedelta(days=day_offset)
            check_day_idx = check_date.weekday()  # 0=Monday, 6=Sunday
            
            # Skip if this day is not in the alarm's days_of_week
            if check_day_idx not in days_of_week:
                continue
            
            # Create a datetime for this alarm occurrence
            alarm_datetime = datetime.combine(check_date, datetime.min.time())
            alarm_datetime = alarm_datetime.replace(hour=hour, minute=minute)
            
            # If it's today, check if the time has passed
            if day_offset == 0 and alarm_datetime <= now:
                continue
            
            # Found the next occurrence
            return alarm_datetime
        
        # If we get here, no valid trigger time was found
        return None
    
    def _handle_alarm_triggered(self, alarm_id: str) -> None:
        """
        Handle when an alarm triggers.
        
        Args:
            alarm_id: ID of the triggered alarm
        """
        # Find the alarm
        alarm = self.get_alarm(alarm_id)
        if not alarm:
            logger.warning(f"Alarm {alarm_id} triggered but not found in alarm list")
            return
        
        logger.info(f"Alarm triggered: {alarm_id} - {alarm.get('label', '')}")
        
        # Emit signal with the alarm data
        self.alarmTriggered.emit(alarm)
        
        # For one-time alarms, disable after triggering
        days_of_week = alarm.get('days_of_week', set())
        if len(days_of_week) <= 1:  # One day or empty set
            logger.info(f"One-time alarm {alarm_id} triggered, disabling")
            self.update_alarm(alarm_id, is_enabled=False)
        else:
            # Reschedule for next occurrence
            self._schedule_alarm(alarm)
