import logging
import datetime
from typing import Dict, Set, Tuple

# Try importing necessary PySide6 components
try:
    from PySide6.QtCore import QObject, Signal, QTimer
except ImportError:
    print("PySide6 is not installed. Please install it to use this module.")
    # Define dummy classes if PySide6 is not available
    class QObject:
        def __init__(self, parent=None): pass
    class Signal:
        def __init__(self, *args, **kwargs): pass
        def emit(self, *args, **kwargs): pass
    class QTimer:
        def __init__(self, parent=None): pass
        def timeout(self): return Signal()
        def setInterval(self, ms): pass
        def start(self): pass
        def stop(self): pass

# Assuming AlarmManager is in the utils directory relative to the project root
from utils.alarm_manager import AlarmManager

logger = logging.getLogger(__name__)

class AlarmChecker(QObject):
    """
    Periodically checks for due alarms using AlarmManager and emits a signal.
    Ensures alarms only trigger once per minute.
    """
    alarmTriggered = Signal(dict)  # Signal emitted with the details of the triggered alarm

    # Store triggered alarms as (alarm_id, triggered_minute_timestamp)
    # Use datetime object representing the start of the minute it was triggered
    _recently_triggered_alarms: Dict[str, datetime.datetime]

    def __init__(self, alarm_manager: AlarmManager, check_interval_ms: int = 10000, parent=None):
        """
        Initializes the AlarmChecker.

        Args:
            alarm_manager: An instance of AlarmManager to get alarm data.
            check_interval_ms: How often to check for alarms in milliseconds (default: 10000ms = 10s).
            parent: Optional parent QObject.
        """
        super().__init__(parent)
        if not isinstance(alarm_manager, AlarmManager):
            raise TypeError("alarm_manager must be an instance of AlarmManager")
            
        self._alarm_manager = alarm_manager
        self._recently_triggered_alarms = {}
        
        self._timer = QTimer(self)
        self._timer.setInterval(check_interval_ms)
        self._timer.timeout.connect(self._check_alarms)
        
        logger.info(f"AlarmChecker initialized with interval {check_interval_ms}ms.")

    def start(self):
        """Starts the periodic alarm checking."""
        if not self._timer.isActive():
            logger.info("Starting AlarmChecker timer.")
            # Perform an initial check immediately
            self._check_alarms()
            self._timer.start()
        else:
             logger.warning("AlarmChecker timer is already running.")

    def stop(self):
        """Stops the periodic alarm checking."""
        if self._timer.isActive():
            logger.info("Stopping AlarmChecker timer.")
            self._timer.stop()
        else:
            logger.info("AlarmChecker timer is already stopped.")

    def _cleanup_triggered_state(self, current_minute: datetime.datetime):
        """Removes old entries from the triggered state dictionary."""
        # Keep track of alarms triggered *only within the last minute*
        # (or slightly more to account for timing variations)
        cutoff_time = current_minute - datetime.timedelta(seconds=70) 
        ids_to_remove = [
            alarm_id for alarm_id, triggered_time in self._recently_triggered_alarms.items()
            if triggered_time < cutoff_time
        ]
        for alarm_id in ids_to_remove:
            del self._recently_triggered_alarms[alarm_id]
        if ids_to_remove:
            logger.debug(f"Cleaned up {len(ids_to_remove)} old triggered alarm states.")
            
    def _check_alarms(self):
        """The core logic that checks if any alarms are due."""
        try:
            now = datetime.datetime.now()
            current_minute_start = now.replace(second=0, microsecond=0)
            current_hour = now.hour
            current_minute = now.minute
            current_day_of_week = now.weekday()  # Monday is 0, Sunday is 6

            logger.debug(f"Checking alarms at {now.strftime('%Y-%m-%d %H:%M:%S')}, Day: {current_day_of_week}")

            # Clean up state before checking
            self._cleanup_triggered_state(current_minute_start)

            all_alarms = self._alarm_manager.get_all_alarms()
            enabled_alarms = [alarm for alarm in all_alarms if alarm.get('is_enabled', False)]

            if not enabled_alarms:
                 # logger.debug("No enabled alarms found.")
                 return
                 
            triggered_count = 0
            for alarm in enabled_alarms:
                alarm_id = alarm.get('id')
                if not alarm_id:
                    continue # Skip alarms without an ID

                # Check if already triggered in the current minute
                if alarm_id in self._recently_triggered_alarms and \
                   self._recently_triggered_alarms[alarm_id] == current_minute_start:
                    # logger.debug(f"Alarm {alarm_id} already triggered this minute.")
                    continue

                alarm_hour = alarm.get('hour')
                alarm_minute = alarm.get('minute')
                alarm_days = alarm.get('days_of_week', set())

                # Check for time match
                time_match = (alarm_hour == current_hour and alarm_minute == current_minute)
                
                # Check for day match
                day_match = (current_day_of_week in alarm_days)

                if time_match and day_match:
                    logger.info(f"Alarm Triggered! ID: {alarm_id}, Label: {alarm.get('label', '')}")
                    # Store the *start* of the minute it triggered to prevent re-triggering in the same minute
                    self._recently_triggered_alarms[alarm_id] = current_minute_start 
                    self.alarmTriggered.emit(alarm) # Emit signal with full alarm details
                    triggered_count += 1
                    
            if triggered_count > 0:
                 logger.debug(f"Finished check, {triggered_count} alarms triggered this cycle.")
                 
        except Exception as e:
            # Catch broad exceptions to prevent the timer from stopping
            logger.error(f"Error during alarm check: {e}", exc_info=True)

# Example Usage (for testing purposes)
if __name__ == '__main__':
    # Basic logging setup for testing
    logging.basicConfig(level=logging.DEBUG) 

    # Requires a QApplication for QTimer and signals
    try:
        from PySide6.QtCore import QCoreApplication, QTimer
        import sys
        app = QCoreApplication(sys.argv)
    except ImportError:
        print("Install PySide6 for full testing including QTimer and signals.")
        app = None

    # Create a dummy AlarmManager for testing
    class DummyAlarmManager(AlarmManager):
        def __init__(self):
            # Avoid QObject init if no app
            if QCoreApplication is not None:
                 super().__init__(app_name="AlarmCheckerTest")
            else:
                self._alarms = [] # Just need the list
                
            # Override load/save to avoid file IO for this test
            self._alarms = [
                {'id': 'wake', 'hour': datetime.datetime.now().hour, 'minute': datetime.datetime.now().minute, 'label': 'Test Wake Now', 'days_of_week': {datetime.datetime.now().weekday()}, 'is_enabled': True},
                {'id': 'sleep', 'hour': 23, 'minute': 0, 'label': 'Test Sleep Later', 'days_of_week': {0, 1, 2, 3, 4, 5, 6}, 'is_enabled': True},
                {'id': 'disabled', 'hour': datetime.datetime.now().hour, 'minute': datetime.datetime.now().minute, 'label': 'Test Disabled Now', 'days_of_week': {datetime.datetime.now().weekday()}, 'is_enabled': False},
            ]
            print("Using DummyAlarmManager with alarms:")
            print(self._alarms)

        def _load_alarms(self): pass
        def _save_alarms(self): pass
        # get_all_alarms is inherited and should work

    dummy_manager = DummyAlarmManager()
    checker = AlarmChecker(alarm_manager=dummy_manager, check_interval_ms=5000) # Check every 5s

    def handle_trigger(alarm_data):
        print(f"\n*** ALARM RECEIVED (Slot) ***")
        print(f"  ID: {alarm_data.get('id')}")
        print(f"  Label: {alarm_data.get('label')}")
        print(f"  Time: {alarm_data.get('hour'):02d}:{alarm_data.get('minute'):02d}")
        print(f"***************************\n")

    # Connect the signal
    if QCoreApplication is not None:
         checker.alarmTriggered.connect(handle_trigger)
         checker.start()
         print("AlarmChecker started. Waiting for triggers (check interval 5s)... Press Ctrl+C to stop.")
         
         # Run the application event loop
         sys.exit(app.exec())
    else:
         print("Cannot run QTimer or connect signals without PySide6 and QCoreApplication.")
         # Manual check for basic logic test without timer
         print("\n--- Manual Check 1 ---")
         checker._check_alarms()
         print("\n--- Manual Check 2 (should not re-trigger immediately) ---")
         checker._check_alarms()
         import time
         print("\n--- Manual Check 3 (after 70s, should allow re-trigger if time still matches) ---")
         # Need to manipulate time or state for a real test here
         # time.sleep(70)
         # checker._check_alarms()
         print("Skipping sleep test as it requires manual time adjustment.")

    print("Alarm Checker testing done.") 