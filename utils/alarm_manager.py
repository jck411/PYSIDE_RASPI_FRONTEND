import os
import json
import uuid
import logging
import copy # Added for deep copy
from typing import List, Dict, Any, Optional, Set

# Try importing necessary PySide6 components
try:
    from PySide6.QtCore import QObject, Signal, QStandardPaths
except ImportError:
    print("PySide6 is not installed. Please install it to use this module.")
    # Define dummy classes if PySide6 is not available, mainly for static analysis or environments without Qt
    class QObject:
        def __init__(self, parent=None): pass
    class Signal:
        def __init__(self, *args, **kwargs): pass
        def emit(self, *args, **kwargs): pass

logger = logging.getLogger(__name__)

# Define the structure of an alarm - consider using a dataclass or TypedDict in Python 3.8+
# For now, using a dictionary format for simplicity and JSON compatibility.
# Example: {'id': 'uuid-string', 'hour': 8, 'minute': 0, 'label': 'Work', 'days_of_week': {0, 1, 2, 3, 4}, 'is_enabled': True}
# Days of week: Monday=0, Sunday=6 (matching datetime.weekday())


class AlarmManager(QObject):
    """
    Manages CRUD operations and persistence for client-side alarms.
    Emits signals when the alarm list changes.
    """
    alarmsChanged = Signal()  # Signal emitted when alarms are added, updated, or deleted

    def __init__(self, app_name: str = "YourAppName", parent=None):
        """
        Initializes the AlarmManager.

        Args:
            app_name: The name of the application, used for the config directory.
            parent: Optional parent QObject.
        """
        super().__init__(parent)
        self._app_name = app_name
        self._alarms: List[Dict[str, Any]] = []
        self._config_path = self._get_config_path()
        self._alarms_file = os.path.join(self._config_path, "alarms.json")
        
        self._load_alarms()

    def _get_config_path(self) -> str:
        """Determines the appropriate configuration directory."""
        try:
            # Prefer using QStandardPaths if available
            path = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppConfigLocation)
            if not path: # Fallback if QStandardPaths returns empty
                 path = os.path.join(os.path.expanduser("~"), ".config", self._app_name)
        except NameError:
             # Fallback if QStandardPaths is not available
             path = os.path.join(os.path.expanduser("~"), ".config", self._app_name)
             
        os.makedirs(path, exist_ok=True)
        logger.info(f"Using configuration path: {path}")
        return path

    def _load_alarms(self):
        """Loads alarms from the JSON file."""
        try:
            if os.path.exists(self._alarms_file):
                with open(self._alarms_file, 'r') as f:
                    loaded_alarms = json.load(f)
                    # Convert days_of_week from list (in JSON) back to set
                    for alarm in loaded_alarms:
                        if 'days_of_week' in alarm and isinstance(alarm['days_of_week'], list):
                            alarm['days_of_week'] = set(alarm['days_of_week'])
                        else:
                            # Handle missing or invalid days_of_week, maybe default to empty set or log warning
                            alarm['days_of_week'] = set() 
                    self._alarms = loaded_alarms
                    logger.info(f"Loaded {len(self._alarms)} alarms from {self._alarms_file}")
            else:
                logger.info(f"Alarm file not found ({self._alarms_file}). Starting with empty list.")
                self._alarms = []
        except json.JSONDecodeError:
            logger.error(f"Error decoding JSON from {self._alarms_file}. Starting with empty list.", exc_info=True)
            # Consider backing up the corrupted file here
            self._alarms = []
        except Exception as e:
            logger.error(f"Failed to load alarms: {e}", exc_info=True)
            self._alarms = []

    def _save_alarms(self):
        """Saves the current list of alarms to the JSON file."""
        try:
            # Ensure config directory exists (should be handled by init, but good practice)
            os.makedirs(self._config_path, exist_ok=True)
            
            # Create a temporary list suitable for JSON (convert sets to lists)
            alarms_to_save = []
            for alarm in self._alarms:
                alarm_copy = alarm.copy()
                if 'days_of_week' in alarm_copy and isinstance(alarm_copy['days_of_week'], set):
                    alarm_copy['days_of_week'] = sorted(list(alarm_copy['days_of_week'])) # Save as sorted list
                alarms_to_save.append(alarm_copy)

            with open(self._alarms_file, 'w') as f:
                json.dump(alarms_to_save, f, indent=4)
            logger.debug(f"Saved {len(self._alarms)} alarms to {self._alarms_file}")
        except IOError as e:
            logger.error(f"Error writing alarms to {self._alarms_file}: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Failed to save alarms: {e}", exc_info=True)

    def get_all_alarms(self) -> List[Dict[str, Any]]:
        """Returns a deep copy of the list of all alarms."""
        return copy.deepcopy(self._alarms)

    def get_alarm(self, alarm_id: str) -> Optional[Dict[str, Any]]:
        """Gets a specific alarm by its ID."""
        for alarm in self._alarms:
            if alarm.get('id') == alarm_id:
                return copy.deepcopy(alarm)
        logger.warning(f"Alarm with ID {alarm_id} not found.")
        return None

    def add_alarm(self, hour: int, minute: int, label: str, days_of_week: Set[int], is_enabled: bool = True) -> Optional[Dict[str, Any]]:
        """Adds a new alarm to the list and saves.

        Args:
            hour: The hour of the alarm (0-23).
            minute: The minute of the alarm (0-59).
            label: A text label for the alarm.
            days_of_week: A set of integers representing days (Monday=0, Sunday=6).
            is_enabled: Whether the alarm is active by default.

        Returns:
            The newly created alarm dictionary, or None if validation fails.
        """
        # Basic validation
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
             logger.error(f"Invalid time provided: {hour}:{minute}")
             return None
        if not isinstance(days_of_week, set) or not all(0 <= day <= 6 for day in days_of_week):
             logger.error(f"Invalid days_of_week provided: {days_of_week}")
             return None
             
        new_alarm_id = str(uuid.uuid4())
        new_alarm = {
            'id': new_alarm_id,
            'hour': hour,
            'minute': minute,
            'label': label,
            'days_of_week': days_of_week,
            'is_enabled': is_enabled
        }
        self._alarms.append(new_alarm)
        self._save_alarms()
        self.alarmsChanged.emit()
        logger.info(f"Added new alarm: ID={new_alarm_id}, Time={hour:02d}:{minute:02d}")
        return copy.deepcopy(new_alarm)

    def update_alarm(self, alarm_id: str, **changes: Any) -> bool:
        """Updates specified fields of an existing alarm and saves.

        Args:
            alarm_id: The ID of the alarm to update.
            **changes: Keyword arguments for the fields to update (e.g., label='New Label', is_enabled=False).

        Returns:
            True if the alarm was found and updated, False otherwise.
        """
        alarm_to_update = None
        for alarm in self._alarms:
            if alarm.get('id') == alarm_id:
                alarm_to_update = alarm
                break

        if alarm_to_update is None:
            logger.warning(f"Attempted to update non-existent alarm ID: {alarm_id}")
            return False

        updated = False
        valid_keys = {'hour', 'minute', 'label', 'days_of_week', 'is_enabled'}
        for key, value in changes.items():
            if key in valid_keys:
                 # Add validation for specific keys if necessary (e.g., time ranges, day types)
                if key == 'days_of_week' and isinstance(value, list):
                    value = set(value) # Allow list input, convert to set
                if key in ('hour', 'minute', 'label', 'is_enabled', 'days_of_week') and alarm_to_update.get(key) != value:
                    alarm_to_update[key] = value
                    updated = True
            else:
                 logger.warning(f"Attempted to update invalid field '{key}' for alarm ID: {alarm_id}")

        if updated:
            self._save_alarms()
            self.alarmsChanged.emit()
            logger.info(f"Updated alarm ID: {alarm_id}")
            return True
        else:
             logger.info(f"No changes applied to alarm ID: {alarm_id}")
             return False # Return False if no actual changes were made

    def delete_alarm(self, alarm_id: str) -> bool:
        """Deletes an alarm by its ID and saves.

        Args:
            alarm_id: The ID of the alarm to delete.

        Returns:
            True if the alarm was found and deleted, False otherwise.
        """
        initial_length = len(self._alarms)
        self._alarms = [alarm for alarm in self._alarms if alarm.get('id') != alarm_id]
        
        if len(self._alarms) < initial_length:
            self._save_alarms()
            self.alarmsChanged.emit()
            logger.info(f"Deleted alarm ID: {alarm_id}")
            return True
        else:
            logger.warning(f"Attempted to delete non-existent alarm ID: {alarm_id}")
            return False

# Example Usage (for testing purposes)
if __name__ == '__main__':
    # This part runs only when the script is executed directly
    # Requires PySide6 to be installed for Signals to work properly
    
    # Basic logging setup for testing
    logging.basicConfig(level=logging.INFO)

    # Dummy application to test signals (requires a QApplication)
    try:
        from PySide6.QtCore import QCoreApplication
        import sys
        app = QCoreApplication(sys.argv)
    except ImportError:
        print("Install PySide6 for full testing including signals.")
        app = None # No app, signals won't function fully

    alarm_manager = AlarmManager(app_name="TestAlarmApp")

    def on_alarms_changed():
        print("\n>>> Alarms changed! Current alarms:")
        # Convert sets to lists for printing consistency
        current_alarms = alarm_manager.get_all_alarms()
        for alarm in current_alarms:
            if isinstance(alarm.get('days_of_week'), set):
                alarm['days_of_week'] = sorted(list(alarm['days_of_week']))
        print(json.dumps(current_alarms, indent=2))

    # Connect the signal to the slot
    if QCoreApplication is not None: # Check if QApplication exists
        alarm_manager.alarmsChanged.connect(on_alarms_changed)

    # TODO: Add calls to test add_alarm, update_alarm, delete_alarm once implemented
    
    print("Initial alarms:")
    print(json.dumps(alarm_manager.get_all_alarms(), indent=2))

    # Test adding alarms
    print("\n--- Testing Add ---")
    alarm1 = alarm_manager.add_alarm(hour=7, minute=0, label="Wake Up", days_of_week={0, 1, 2, 3, 4}, is_enabled=True)
    alarm2 = alarm_manager.add_alarm(hour=22, minute=30, label="Bedtime", days_of_week={0, 1, 2, 3, 4, 5, 6}, is_enabled=False)
    alarm3 = alarm_manager.add_alarm(hour=9, minute=0, label="Weekend", days_of_week={5, 6})
    invalid_alarm = alarm_manager.add_alarm(hour=25, minute=0, label="Invalid Time", days_of_week={0})
    
    if alarm1:
        print(f"\n--- Testing Get ({alarm1['id']}) ---")
        retrieved = alarm_manager.get_alarm(alarm1['id'])
        if retrieved:
             retrieved['days_of_week'] = sorted(list(retrieved['days_of_week'])) # for print
             print(json.dumps(retrieved, indent=2))
        else:
             print("Failed to retrieve alarm1")

    if alarm2:
        print(f"\n--- Testing Update ({alarm2['id']}) ---")
        update_success = alarm_manager.update_alarm(alarm2['id'], is_enabled=True, label="Go to Bed NOW")
        print(f"Update successful: {update_success}")
        update_noop = alarm_manager.update_alarm(alarm2['id'], label="Go to Bed NOW") # No change
        print(f"Update no-op successful: {update_noop}")
        update_invalid_field = alarm_manager.update_alarm(alarm2['id'], invalid_field="test")
        print(f"Update invalid field successful: {update_invalid_field}")
        update_nonexistent = alarm_manager.update_alarm("non-existent-id", label="Test")
        print(f"Update non-existent successful: {update_nonexistent}")

    if alarm3:
        print(f"\n--- Testing Delete ({alarm3['id']}) ---")
        delete_success = alarm_manager.delete_alarm(alarm3['id'])
        print(f"Delete successful: {delete_success}")
        delete_again = alarm_manager.delete_alarm(alarm3['id'])
        print(f"Delete again successful: {delete_again}")
        delete_nonexistent = alarm_manager.delete_alarm("non-existent-id")
        print(f"Delete non-existent successful: {delete_nonexistent}")

    print("\nFinal alarms:")
    final_alarms = alarm_manager.get_all_alarms()
    for alarm in final_alarms:
        if isinstance(alarm.get('days_of_week'), set):
             alarm['days_of_week'] = sorted(list(alarm['days_of_week']))
    print(json.dumps(final_alarms, indent=2))
    
    # Keep the app running briefly if it exists, to allow signals to process (won't work without event loop)
    # if app:
    #     from PySide6.QtCore import QTimer
    #     QTimer.singleShot(100, app.quit) 
    #     app.exec() 

    print("Alarm Manager testing done.") 