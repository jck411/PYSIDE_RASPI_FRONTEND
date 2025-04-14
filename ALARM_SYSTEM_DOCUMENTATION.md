# Alarm Clock System Documentation

## System Overview

The alarm clock functionality is part of a PySide6-based Raspberry Pi frontend application. It implements a modern, customizable alarm clock with theme support, day selection for repeated alarms, and a flexible backend for alarm storage and triggering.

The alarm system follows a Model-View-Controller (MVC) architecture:
- **Model**: Implemented by `AlarmManager` which handles alarm data storage and retrieval
- **View**: Implemented through QML files that define the UI components
- **Controller**: `AlarmController` bridges between the QML UI and the backend `AlarmManager`

## Key Files and Their Roles

### Backend / Python Files

1. **utils/alarm_manager.py**:
   - Core alarm data management
   - Persists alarms to JSON files
   - Handles CRUD operations (Create, Read, Update, Delete)
   - Emits signals when alarms change

2. **frontend/controllers/alarm_controller.py**:
   - Python-QML bridge for alarm functionality
   - Exposes alarm operations to QML
   - Translates between Python and QML data formats
   - Connects signals between backend and frontend
   - Implements both snake_case (Python) and camelCase (QML) method versions

3. **frontend/theme_manager.py**:
   - Manages theming for the entire application
   - Provides color properties used by alarm UI components
   - Handles theme switching (light/dark mode)

4. **frontend/style.py**:
   - Defines color palettes for different themes
   - Contains color definitions used throughout the app

5. **services/alarm_checker.py**:
   - Background service that checks when alarms should trigger
   - Runs on a timer to periodically check alarm times
   - Emits signals when an alarm should be triggered

### Frontend / QML Files

1. **frontend/qml/AlarmScreen.qml**:
   - Main alarm screen UI
   - Displays list of alarms
   - Provides "Add Alarm" functionality
   - Handles alarm editing and deletion

2. **frontend/qml/dialogs/AddAlarmDialog.qml**:
   - Dialog for adding/editing alarms
   - Time selection UI (hour/minute tumblers)
   - Day selection for repeating alarms
   - Label input

3. **frontend/qml/ClockScreen.qml**:
   - Parent screen containing clock display
   - References AlarmScreen for alarm functionality
   - Handles alarm notifications

4. **frontend/qml/MainWindow.qml**:
   - Main application window
   - Manages screen navigation
   - Connects to ThemeManager for theming

## Data Structure and Flow

### Alarm Data Format

Alarms are stored and managed as JSON objects with the following structure:

```json
{
  "id": "unique-uuid-string",
  "hour": 8,                     // 0-23 hour
  "minute": 30,                  // 0-59 minute
  "label": "Wake up",            // Optional label text
  "days_of_week": [0, 1, 2, 3, 4], // Days when alarm repeats (0=Monday, 6=Sunday)
  "enabled": true                // Whether alarm is active
}
```

### Data Flow

1. **Creation Flow**:
   - User inputs data in QML UI (AlarmScreen.qml)
   - QML calls `AlarmController.addAlarm()` method
   - Controller calls `AlarmManager.add_alarm()`
   - AlarmManager creates a record with a UUID and persists it
   - AlarmManager emits `alarmsChanged` signal
   - Signal propagates to Controller, which emits to QML
   - QML refreshes the ListView to display the new alarm

2. **Update Flow**:
   - User modifies an alarm in QML UI
   - QML calls `AlarmController.updateAlarm()`
   - Controller calls `AlarmManager.update_alarm()`
   - AlarmManager updates the record and persists changes
   - Signal chain similar to creation flow

3. **Trigger Flow**:
   - AlarmChecker periodically compares current time with alarm times
   - When an alarm should trigger, AlarmChecker emits a signal
   - Signal is forwarded to Controller, which emits to QML
   - QML displays a notification dialog

## Key Components

### AlarmManager Class

The central manager for alarm data with these key methods:

- `get_all_alarms()`: Returns all alarms
- `get_alarm(alarm_id)`: Gets a specific alarm by ID
- `add_alarm(hour, minute, label, days_of_week, is_enabled)`: Creates a new alarm
- `update_alarm(alarm_id, **changes)`: Updates an existing alarm
- `delete_alarm(alarm_id)`: Deletes an alarm

Signals:
- `alarmsChanged`: Emitted when alarms are added, updated, or deleted

### AlarmController Class

Bridges Python and QML with these key methods:

Python-style methods:
- `add_alarm(hour, minute, label, days_list, is_enabled)`
- `update_alarm(alarm_id, changes)`
- `delete_alarm(alarm_id)`
- `set_alarm_enabled(alarm_id, enabled)`

QML-friendly camelCase aliases:
- `addAlarm(label, hour, minute, is_enabled, days_list)`
- `updateAlarm(alarm_id, label, hour, minute, is_enabled, days_list)`
- `deleteAlarm(alarm_id)`
- `setAlarmEnabled(alarm_id, enabled)`
- `getAlarms()` and `getAlarm(alarm_id)`

Signals:
- `alarmsChanged`: Forwarded to QML for UI updates
- `alarmTriggered(alarm_id, alarm_label)`: Emitted when an alarm triggers

### AlarmScreen QML Components

Key UI components:

1. **Alarm ListView**:
   - Displays all alarms in a scrollable list
   - Each alarm item shows time, label, and repeat pattern
   - Features toggle switches and delete buttons

2. **Edit Panel**:
   - Slides up from bottom when editing/adding
   - Contains time selection, label field, and day selection

3. **Day Selection UI**:
   - Interactive day buttons for selecting repeat days
   - "Weekdays", "Weekend", and "Every Day" convenience buttons

4. **Notification Dialog**:
   - Appears when an alarm triggers
   - Shows alarm label and current time
   - Provides dismiss/snooze options

## Theme Integration

The alarm UI uses the application's theming system for consistent appearance:

- `ThemeManager` provides color properties to QML
- UI components like buttons, backgrounds, and text use theme colors
- Colors update dynamically when theme changes
- Both light and dark themes are supported

Key theme properties used:
- `background_color`: Main background
- `background_secondary_color`: Section backgrounds
- `accent_color`: Highlighted elements
- `text_primary_color`: Main text
- `text_secondary_color`: Less prominent text
- `border_color`: Element borders
- `danger_color`: Delete buttons

## Formatting and Utility Functions

Key utility functions in QML:

1. **formatTime(hour, minute)**:
   - Formats time values as "HH:MM" with zero-padding
   - Handles conversion of numeric values to display format

2. **formatDays(daysList)**:
   - Formats day arrays into human-readable text
   - Special handling for common patterns:
     - "Weekdays" for Monday-Friday
     - "Weekend" for Saturday-Sunday
     - "Every Day" for all days
     - Individual day names for custom patterns
   - Robust handling of various data formats

## Key Interactions and User Flows

1. **Viewing Alarms**:
   - Alarms are displayed in a ListView
   - Each shows time, label, and repeat pattern
   - Toggle switches control enable/disable state

2. **Adding an Alarm**:
   - User taps "Add new alarm"
   - Edit panel slides up
   - User sets time, label, repeat days
   - User taps "Add" button
   - New alarm is added and list refreshes

3. **Editing an Alarm**:
   - User taps an existing alarm
   - Edit panel slides up with current values
   - User modifies as needed
   - User taps "Update" button
   - Changes are saved and list refreshes

4. **Deleting an Alarm**:
   - User taps delete button (×) on an alarm
   - Alarm is removed immediately
   - List refreshes

5. **When an Alarm Triggers**:
   - Notification dialog appears
   - Shows alarm label and current time
   - User can dismiss or snooze

## Error Handling and Edge Cases

The implementation includes robust error handling:

1. **Data Type Safety**:
   - All QML <-> Python data conversions are handled safely
   - Defensive checks for undefined/null values
   - Type conversion for numeric values

2. **Missing Properties**:
   - Fallbacks for undefined theme properties
   - Default values for missing alarm attributes

3. **Array/Collection Handling**:
   - Safe handling of arrays and collections
   - Conversion between Python sets and QML arrays

## Performance Considerations

1. **Model Updates**:
   - ListView model is efficiently updated only when needed
   - Temporary detachment during updates prevents flickering

2. **UI Rendering**:
   - Efficient use of Rectangle elements
   - Minimal use of expensive effects

3. **Theme Changes**:
   - Property binding for immediate theme updates
   - Efficient color property updates

## Implementation Notes

1. **Signal Connection Pattern**:
   - Modern QML connection syntax using `function onSignalName()`
   - Clear signal flow from backend to frontend

2. **Property Binding**:
   - Strategic use of QML property binding
   - Direct function calls for data that needs refresh control

3. **Component Reuse**:
   - Modular design for UI components
   - Reusable formatting functions

## Known Issues and Troubleshooting

### Alarm Deletion Issues

1. **Missing Alarm IDs**:
   - **Symptom**: Deletion of alarms fails with error message "Failed to delete alarm with ID: , no matching alarm found"
   - **Cause**: The ListView delegate in AlarmScreen.qml is not correctly binding to the alarm ID property from the model
   - **Details**: The property binding for alarmId attempts to access `model.id` which may be missing or undefined in some cases
   - **Debugging**: ListView delegate logs "Model ID for item:" to console but shows undefined or empty values

2. **Controller/Model Inconsistency**:
   - **Symptom**: Data structure mismatches between the two separate AlarmController implementations
   - **Cause**: System has two controller implementations:
     - `frontend/controllers/alarm_controller.py` (registered in main.py)
     - `frontend/logic/alarm_controller.py` (contains AlarmModel class but is not used)
   - **Impact**: Confusion about which controller should handle which operations and potential property name mismatches

3. **Property Name Mismatches**:
   - **Symptom**: QML code tries to access both `model.id` and other variations like `model.name` vs `model.label`
   - **Cause**: Inconsistent property naming in the data model vs the QML expectations
   - **Example**: The QML delegate tries multiple fallbacks:
     ```qml
     property string alarmName: model.name || model.label || "Alarm"
     property var alarmRecurrence: model.recurrence || model.days_of_week || []
     ```

### Model Binding Issues

1. **Improper ListView Model Update**:
   - **Symptom**: Changes to alarms don't always refresh properly in the UI
   - **Cause**: Inconsistent approach to updating the model:
     - Sometimes using `AlarmController.getAlarms()`
     - Other times using `AlarmController.alarmModel()`
   - **Impact**: Potential for UI to be out of sync with actual data

2. **QAbstractListModel vs QVariantList**:
   - **Symptom**: Role name mismatches in data access
   - **Cause**: The code mixes two approaches:
     - A proper QAbstractListModel implementation (AlarmModel)
     - A simpler QVariantList approach (returning list of dictionaries)
   - **Result**: Confusion in the delegate about which property names to use

### Recommended Fixes

1. **Standardize on a Single Controller**:
   - Select either `controllers/alarm_controller.py` or `logic/alarm_controller.py`
   - Ensure consistent property naming between Python and QML

2. **Debug Alarm Deletion**:
   - Add additional logging in the delete button handler
   - Ensure proper ID binding in the delegate
   - Fix property access to consistently use the correct property names

3. **Consistent Model Approach**:
   - Standardize on either QAbstractListModel or QVariantList
   - Update the QML delegate to match the selected approach
   - Ensure proper role/property mapping

4. **Clearer Error Handling**:
   - Add more descriptive error messages
   - Implement input validation on the controller side
   - Add user feedback when operations fail

### Specific Issue: Alarm Deletion Failure

The primary issue observed is with alarm deletion, which fails with the error message: "Failed to delete alarm with ID: , no matching alarm found".

#### Code Analysis

The issue occurs in the `AlarmScreen.qml` file's ListView delegate around line 365:

```qml
property string alarmId: {
    var id = model.id || "";
    console.log("Model ID for item:", JSON.stringify(model));
    return id;
}
```

And in the delete button's click handler:

```qml
onClicked: {
    console.log("Delete button clicked for alarm with ID:", alarmId)
    console.log("Full model data:", JSON.stringify({
        id: alarmId,
        name: alarmName,
        hour: alarmHour,
        minute: alarmMinute
    }))
    
    // Only attempt to delete if we have a valid ID
    if (alarmId && alarmId.length > 0) {
        AlarmController.deleteAlarm(alarmId)
    } else {
        console.error("Cannot delete alarm with invalid ID:", alarmId)
    }
}
```

The problem is that the `model.id` property is not being correctly passed to the QML delegate from the Python controller. This happens because:

1. The `frontend/controllers/alarm_controller.py` returns alarms as a list of dictionaries through `getAlarms()` method
2. But the AlarmScreen.qml is also trying to use `model = AlarmController.alarmModel()` which expects a proper QAbstractListModel

#### Problem Analysis

The console logs show empty IDs being passed to the deleteAlarm function:

```
Failed to delete alarm with ID: , no matching alarm found
```

This is caused by the mismatch between the property names used in the model and those expected by the QML delegate.

#### Proposed Fixes

**Option 1: Fix Property Access in QML Delegate**

```qml
// In AlarmScreen.qml, modify the delegate property:
property string alarmId: {
    // Try all possible property names used in the system
    var id = model.id || model.alarm_id || (typeof modelData !== 'undefined' ? modelData.id : "");
    // More verbose logging for debugging
    console.log("Alarm item ID resolution:", 
        "model.id =", model.id, 
        "model.alarm_id =", model.alarm_id,
        "modelData =", typeof modelData !== 'undefined' ? JSON.stringify(modelData) : "undefined");
    return id;
}
```

**Option 2: Standardize on QAbstractListModel**

1. Replace the current mixed approach with a consistent use of the `AlarmModel` class from `frontend/logic/alarm_controller.py`
2. Ensure the `roleNames()` method correctly maps the roles to the expected property names:

```python
def roleNames(self):
    return {
        self.IdRole: b"id",
        self.NameRole: b"name",
        self.HourRole: b"hour",
        self.MinuteRole: b"minute",
        self.EnabledRole: b"enabled",
        self.RecurrenceRole: b"recurrence"
    }
```

3. Update the QML to use this model consistently:

```qml
Component.onCompleted: {
    // Use the proper QAbstractListModel
    model = AlarmController.alarmModel();
}
```

**Option 3: Add Debugging Code**

Add additional logging in both Python controller and QML to diagnose the exact issue:

```python
# In the delete_alarm method of alarm_controller.py
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
```

## Implementation Plan

To resolve the identified issues, especially the alarm deletion problem, we recommend the following implementation plan:

### Phase 1: Immediate Fixes

1. **Fix Alarm ID Binding in AlarmScreen.qml**:
   ```qml
   // Replace the current alarmId property in ListView delegate
   property string alarmId: {
       // Try all possible property names used in the system
       var id = model.id || model.alarm_id || (typeof modelData !== 'undefined' ? modelData.id : "");
       // More verbose logging for debugging
       console.log("Alarm item ID resolution:", 
           "model.id =", model.id, 
           "model.alarm_id =", model.alarm_id,
           "modelData =", typeof modelData !== 'undefined' ? JSON.stringify(modelData) : "undefined");
       return id;
   }
   ```

2. **Fix Controller Response in deleteAlarm Method**:
   ```python
   # In frontend/controllers/alarm_controller.py
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
   ```

### Phase 2: Standardize Model Approach

1. **Choose One Controller Implementation**:
   - Migrate to using `frontend/logic/alarm_controller.py` which has a proper QAbstractListModel implementation
   - Or enhance the current `frontend/controllers/alarm_controller.py` with a similar model class

2. **Update Main.py Registration**:
   ```python
   # In frontend/main.py
   # Register AlarmController instance as a singleton
   alarm_controller_instance = AlarmController()
   qmlRegisterSingletonInstance(
       AlarmController,
       "MyServices",
       1,
       0,
       "AlarmController",  # Name exposed to QML
       alarm_controller_instance,
   )
   ```

3. **Standardize on QAbstractListModel in AlarmScreen.qml**:
   ```qml
   // In AlarmScreen.qml's ListView
   Component.onCompleted: {
       console.log("Setting model to AlarmController.alarmModel()");
       model = AlarmController.alarmModel();
   }
   
   // And modify the delegate to use roles directly:
   delegate: Rectangle {
       // ...
       property string alarmId: model.id
       property string alarmName: model.name
       property int alarmHour: model.hour
       property int alarmMinute: model.minute
       property bool alarmEnabled: model.enabled
       property var alarmRecurrence: model.recurrence
   }
   ```

### Phase 3: Comprehensive Testing

1. **Test Cases**:
   - Create multiple alarms with different configurations
   - Test deletion of each alarm individually
   - Test updating alarms
   - Verify proper ListView updates after each operation

2. **Edge Case Handling**:
   - Add code to handle empty or invalid alarm IDs more gracefully
   - Add visual feedback when operations fail
   - Implement confirmation dialogs for destructive operations

3. **Performance Testing**:
   - Ensure model updates are efficient
   - Verify that large numbers of alarms can be managed without performance issues

### Phase 4: Documentation Update

1. **Update Architecture Document**:
   - Document the chosen approach between the two controllers
   - Add diagrams showing the data flow between Python and QML

2. **Add Developer Notes**:
   - Include clear guidance on how to extend the alarm system
   - Document the property binding conventions used in the QML

3. **Create Troubleshooting Guide**:
   - Add common issues and solutions
   - Include debugging tips for QML-Python interaction
