import logging
import sys
import os
from typing import List, Dict, Any, Optional, Set

# Try importing necessary PySide6 components
try:
    from PySide6.QtCore import QObject, Signal, Slot, Property, QVariant, QUrl, QAbstractListModel, Qt
    from PySide6.QtQml import QmlElement
    # QVariantList and QVariantMap are just QVariant in parameter annotations
    QVariantList = QVariant
    QVariantMap = QVariant

except ImportError:
    print("PySide6 is not installed. Please install it to use this module.")
    # Define dummy classes if PySide6 is not available
    class QObject:
        def __init__(self, parent=None): pass
    class Signal: 
        def __init__(self, *args, **kwargs): pass
        def connect(self, *args, **kwargs): pass
        def emit(self, *args, **kwargs): pass
    def Slot(*args, **kwargs): return lambda func: func # Dummy decorator
    def Property(*args, **kwargs): return lambda func: func # Dummy decorator
    class QVariant: pass
    class QUrl: pass
    class QAbstractListModel:
        def __init__(self, parent=None): pass
    class Qt: 
        class ItemDataRole:
             UserRole = 0 # Dummy enum value
    def QmlElement(cls): return cls # Dummy decorator
    QVariantList = QVariant
    QVariantMap = QVariant

# Ensure the project root is in the Python path for imports
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Use absolute imports
from utils.alarm_manager import AlarmManager
from services.alarm_checker import AlarmChecker

logger = logging.getLogger(__name__)

# If using QML, it's often best to expose lists as models
# We might need to create a simple QAbstractListModel wrapper later
# For now, let's expose as a generic QVariantList (list of dicts)

class AlarmController(QObject):
    """
    Acts as a bridge between the Python alarm logic (manager, checker) and the QML UI.
    Exposes alarm data and control functions to QML.
    """
    # Signal to notify QML that the list of alarms has changed
    alarmsChanged = Signal()
    
    # Signal to notify QML when an alarm is triggered
    # Payload could be the alarm dict or specific fields like id/label
    alarmTriggered = Signal(str, str) # Emitting id and label for simplicity

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Create instances of the manager and checker
        # TODO: Consider making AlarmManager a singleton or passing it in if shared elsewhere
        self._alarm_manager = AlarmManager(app_name="RaspiFrontend") # Use a specific app name
        self._alarm_checker = AlarmChecker(alarm_manager=self._alarm_manager)
        
        # Connect internal signals to emit QML-facing signals
        self._alarm_manager.alarmsChanged.connect(self._on_alarms_changed_internal)
        self._alarm_checker.alarmTriggered.connect(self._on_alarm_triggered_internal)
        
        # Start the checker
        self._alarm_checker.start()
        
        logger.info("AlarmController initialized.")

    # --- Internal Signal Handlers --- 

    def _on_alarms_changed_internal(self):
        """Called when the AlarmManager signals a change."""
        logger.debug("Internal: Alarms changed, emitting alarmsChanged signal for QML.")
        self.alarmsChanged.emit() # Notify QML that the property needs refreshing

    def _on_alarm_triggered_internal(self, alarm_dict: Dict[str, Any]):
        """Called when the AlarmChecker signals a trigger."""
        alarm_id = alarm_dict.get('id', 'unknown')
        alarm_label = alarm_dict.get('label', '')
        logger.info(f"Internal: Alarm triggered ({alarm_id}), emitting alarmTriggered signal for QML.")
        self.alarmTriggered.emit(alarm_id, alarm_label)
        
    # --- QML Callable Properties and Slots --- 

    # Property to expose the list of alarms to QML
    # Returns a QVariantList (Python list is automatically converted)
    # QML will access this as `alarmController.alarmsModel`
    @Property(QVariant, notify=alarmsChanged)
    def alarmsModel(self):
        # QML often works best with models. For complex lists,
        # creating a QAbstractListModel is better. For now, return list of dicts.
        alarms = self._alarm_manager.get_all_alarms()
        # Convert sets to lists for QML compatibility
        for alarm in alarms:
             if isinstance(alarm.get('days_of_week'), set):
                alarm['days_of_week'] = sorted(list(alarm['days_of_week']))
        logger.debug(f"Providing {len(alarms)} alarms to QML model.")
        return alarms # PySide automatically converts to QVariantList

    # Slot to add a new alarm from QML
    # Note: QML doesn't directly support passing sets. We'll use a list for days.
    @Slot(int, int, str, QVariantList, bool)
    def add_alarm(self, hour: int, minute: int, label: str, days_list: List[int], is_enabled: bool = True):
        logger.info(f"QML requested add_alarm: {hour}:{minute}, {label}, Days: {days_list}")
        days_set = set(days_list) # Convert list from QML to set for manager
        new_alarm = self._alarm_manager.add_alarm(hour, minute, label, days_set, is_enabled)
        if new_alarm:
             logger.info(f"Alarm added successfully via QML. ID: {new_alarm['id']}")
        else:
             logger.error("Failed to add alarm via QML.")
             
    # QML-friendly camelCase alias for add_alarm
    @Slot(str, int, int, bool, QVariantList)
    def addAlarm(self, label: str, hour: int, minute: int, is_enabled: bool, days_list: List[int]):
        logger.info(f"QML requested addAlarm: {label}, {hour}:{minute}, Enabled: {is_enabled}, Days: {days_list}")
        # Make sure we match the parameter order expected by add_alarm
        # add_alarm expects: (hour, minute, label, days_list, is_enabled)
        self.add_alarm(hour, minute, label, days_list, is_enabled)
        logger.info(f"Successfully added alarm through QML interface")
             
    # Slot to delete an alarm from QML
    @Slot(str)
    def delete_alarm(self, alarm_id: str):
        logger.info(f"QML requested delete_alarm: '{alarm_id}'")
        
        # Validation
        if not alarm_id or not isinstance(alarm_id, str) or not alarm_id.strip():
            logger.error(f"Invalid alarm ID received for deletion: '{alarm_id}'")
            return False
            
        # Log all existing IDs for comparison
        all_alarms = self._alarm_manager.get_all_alarms()
        existing_ids = [a.get('id', 'MISSING_ID') for a in all_alarms]
        logger.debug(f"Existing alarm IDs: {existing_ids}")
        
        # Attempt deletion
        success = self._alarm_manager.delete_alarm(alarm_id.strip())
        if success:
            logger.info(f"Alarm '{alarm_id}' deleted successfully via QML.")
        else:
            logger.warning(f"Failed to delete alarm '{alarm_id}' via QML (not found)")
            
        return success
            
    # QML-friendly camelCase alias for delete_alarm
    @Slot(str)
    def deleteAlarm(self, alarm_id: str):
        return self.delete_alarm(alarm_id)
            
    # Slot to update an alarm from QML (e.g., toggling enabled state)
    # Using QVariantMap (dict) for flexibility in updates
    @Slot(str, QVariantMap)
    def update_alarm(self, alarm_id: str, changes: Dict[str, Any]):
        logger.info(f"QML requested update_alarm: {alarm_id}, Changes: {changes}")
        # Convert days list back to set if present in changes
        if 'days_of_week' in changes and isinstance(changes['days_of_week'], list):
            changes['days_of_week'] = set(changes['days_of_week'])
            
        success = self._alarm_manager.update_alarm(alarm_id, **changes)
        if success:
            logger.info(f"Alarm {alarm_id} updated successfully via QML.")
        else:
            logger.warning(f"Failed to update alarm {alarm_id} via QML or no changes made.")

    # QML-friendly camelCase alias for update_alarm
    @Slot(str, str, int, int, bool, QVariantList)
    def updateAlarm(self, alarm_id: str, label: str, hour: int, minute: int, is_enabled: bool, days_list: List[int]):
        changes = {
            'label': label,
            'hour': hour,
            'minute': minute,
            'is_enabled': is_enabled,
            'days_of_week': days_list
        }
        return self.update_alarm(alarm_id, changes)

    # Convenience slot to just toggle the enabled state
    @Slot(str, bool)
    def set_alarm_enabled(self, alarm_id: str, enabled: bool):
        logger.info(f"QML requested set_alarm_enabled: {alarm_id}, Enabled: {enabled}")
        self.update_alarm(alarm_id, changes={'is_enabled': enabled})
        
    # QML-friendly camelCase alias for set_alarm_enabled
    @Slot(str, bool)
    def setAlarmEnabled(self, alarm_id: str, enabled: bool):
        return self.set_alarm_enabled(alarm_id, enabled)
        
    # Get all alarms - QML friendly alias
    @Slot(result=QVariant)
    def getAlarms(self):
        alarms = self._alarm_manager.get_all_alarms()
        # Convert sets to lists for QML compatibility
        for alarm in alarms:
            if isinstance(alarm.get('days_of_week'), set):
                alarm['days_of_week'] = sorted(list(alarm['days_of_week']))
        return alarms
        
    # Get specific alarm - QML friendly alias
    @Slot(str, result=QVariant)
    def getAlarm(self, alarm_id: str):
        alarm = self._alarm_manager.get_alarm(alarm_id)
        if alarm and isinstance(alarm.get('days_of_week'), set):
            alarm['days_of_week'] = sorted(list(alarm['days_of_week']))
        return alarm
        
    # Make sure to stop the checker timer when the controller is destroyed (if necessary)
    def __del__(self):
        logger.info("AlarmController being destroyed, stopping checker.")
        self.stop_checker() # Ensure checker is stopped
        
    @Slot()
    def stop_checker(self):
        """Explicitly stops the alarm checker timer."""
        if self._alarm_checker:
             self._alarm_checker.stop()

# Example of how to register in main.py (or similar setup file):
# from PySide6.QtQml import QQmlApplicationEngine
# from frontend.controllers.alarm_controller import AlarmController
# 
# engine = QQmlApplicationEngine()
# alarm_controller = AlarmController()
# engine.rootContext().setContextProperty("alarmController", alarm_controller)
# engine.load(QUrl.fromLocalFile('path/to/your/main.qml'))
# # Make sure alarm_controller is kept alive, e.g., by assigning to a member variable
# # Remember to call alarm_controller.stop_checker() on application exit
