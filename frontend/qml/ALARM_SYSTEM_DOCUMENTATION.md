# Alarm Clock System Documentation

## System Overview

The alarm clock functionality is part of a PySide6-based Raspberry Pi frontend application. It implements a modern, customizable alarm clock with theme support, day selection for repeated alarms, and a flexible backend for alarm storage and triggering.

The alarm system follows a Model-View-Controller (MVC) architecture:
- **Model**: Implemented by `AlarmManager` which handles alarm data storage and retrieval
- **View**: Implemented through QML files that define the UI components
- **Controller**: `AlarmController` bridges between the QML UI and the backend `AlarmManager`

## Efficient Alarm Triggering System

The alarm system uses a precise timer-based approach rather than periodic checking:

1. **Direct Timer Scheduling**:
   - Each alarm has its own dedicated QTimer
   - Timers are scheduled to trigger at the exact time of the alarm
   - No periodic polling or checking required

2. **Resource Efficiency**:
   - CPU usage is minimized as there's no constant checking
   - Only active when alarms are about to trigger
   - Scales efficiently with the number of alarms

3. **Precision**:
   - Alarms trigger at the exact scheduled time
   - No delay due to polling intervals
   - Millisecond-level precision

4. **Automatic Rescheduling**:
   - Recurring alarms automatically reschedule after triggering
   - One-time alarms are disabled after triggering
   - System handles date boundaries and day-of-week patterns

## Key Files and Their Roles

### Backend / Python Files

1. **utils/alarm_manager_v2.py**:
   - Core alarm data management with efficient timer scheduling
   - Persists alarms to JSON files
   - Handles CRUD operations (Create, Read, Update, Delete)
   - Creates and manages precise timers for each alarm
   - Emits signals when alarms change or trigger

2. **frontend/logic/alarm_controller_v2.py**:
   - Python-QML bridge for alarm functionality
   - Implements a proper QAbstractListModel for efficient data binding
   - Exposes alarm operations to QML
   - Translates between Python and QML data formats
   - Connects signals between backend and frontend
   - Maintains compatibility with existing QML code

3. **frontend/theme_manager.py**:
   - Manages theming for the entire application
   - Provides color properties used by alarm UI components
   - Handles theme switching (light/dark mode)

4. **frontend/style.py**:
   - Defines color palettes for different themes
   - Contains color definitions used throughout the app

### Frontend / QML Files

1. **frontend/qml/AlarmScreen.qml**:
   - Main alarm screen UI
   - Displays list of alarms
   - Provides "Add Alarm" functionality
   - Handles alarm editing and deletion
   - Contains integrated edit panel that slides up from bottom
   - Includes notification dialog for triggered alarms

2. **frontend/qml/AlarmControls.qml**:
   - Navigation controls for the alarm screen
   - Provides a button to navigate back to the clock screen
   - Integrates with the main navigation system

3. **frontend/qml/ClockScreen.qml**:
   - Parent screen containing clock display
   - References AlarmScreen for alarm functionality
   - Provides navigation to the alarm screen

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
  "label": "Wake up",            // Alarm label text
  "hour": 8,                     // 0-23 hour
  "minute": 30,                  // 0-59 minute
  "is_enabled": true,            // Whether alarm is active
  "days_of_week": [0, 1, 2, 3, 4]  // Days when alarm repeats (0=Monday, 6=Sunday)
}
```

Note: The controller translates between this internal format and the QML-friendly format:
- `label` in backend → `name` in QML
- `is_enabled` in backend → `enabled` in QML
- `days_of_week` in backend → `recurrence` in QML

### Data Flow

1. **Creation Flow**:
   - User taps "Add new alarm" in AlarmScreen.qml
   - Edit panel slides up from bottom
   - User sets time, label, and repeat days
   - User taps "Add" button
   - QML calls `AlarmController.addAlarm()` method
   - Controller creates a record with a UUID and persists it
   - Controller emits `alarmsChanged` signal
   - QML refreshes the ListView to display the new alarm

2. **Update Flow**:
   - User taps an existing alarm in AlarmScreen.qml
   - Edit panel slides up with current values
   - User modifies as needed
   - User taps "Update" button
   - QML calls `AlarmController.updateAlarm()`
   - Controller updates the record and persists changes
   - Signal chain similar to creation flow

3. **Trigger Flow**:
   - When an alarm's scheduled time is reached, its dedicated timer fires
   - The AlarmManager emits an `alarmTriggered` signal with the alarm data
   - The Controller receives this signal and forwards it to QML
   - QML displays a notification dialog and plays the alarm sound
   - For recurring alarms, a new timer is automatically scheduled for the next occurrence

## Key Components

### AlarmManager Class

The central manager for alarm data with these key methods:

- `get_all_alarms()`: Returns all alarms
- `get_alarm(alarm_id)`: Gets a specific alarm by ID
- `add_alarm(hour, minute, label, days_of_week, is_enabled)`: Creates a new alarm
- `update_alarm(alarm_id, **changes)`: Updates an existing alarm
- `delete_alarm(alarm_id)`: Deletes an alarm
- `set_alarm_enabled(alarm_id, enabled)`: Toggles an alarm's enabled state
- `clear_all_alarms()`: Deletes all alarms

Signals:
- `alarmsChanged`: Emitted when alarms are added, updated, or deleted
- `alarmTriggered`: Emitted when an alarm triggers

### AlarmController Class

Bridges Python and QML with these key methods:

- `addAlarm(name, hour, minute, enabled, recurrence)`: Creates a new alarm
- `updateAlarm(alarm_id, name, hour, minute, enabled, recurrence)`: Updates an existing alarm
- `deleteAlarm(alarm_id)`: Deletes an alarm
- `setAlarmEnabled(alarm_id, enabled)`: Toggles an alarm's enabled state
- `getAlarm(alarm_id)`: Gets a specific alarm by ID
- `getAlarms()`: Gets all alarms
- `alarmModel()`: Returns a QAbstractListModel for use in QML ListView
- `clearAllAlarms()`: Deletes all alarms

Signals:
- `alarmsChanged`: Emitted when alarms are added, updated, or deleted
- `alarmTriggered(alarm_id, alarm_name)`: Emitted when an alarm triggers

### AlarmModel Class

A QAbstractListModel implementation that provides efficient data binding for QML:

- Defines roles for each alarm property (id, name, hour, minute, enabled, recurrence)
- Provides methods for updating the model data
- Ensures proper role mapping between Python and QML

### AlarmScreen QML Components

Key UI components:

1. **Alarm ListView**:
   - Displays all alarms in a scrollable list
   - Each alarm item shows time, label, and repeat pattern
   - Features toggle switches and delete buttons

2. **Edit Panel**:
   - Slides up from bottom when editing/adding
   - Contains time selection, label field, and day selection
   - Provides "Add" or "Update" button based on context

3. **Day Selection UI**:
   - Interactive day buttons for selecting repeat days
   - "Weekdays", "Weekend", and "Every Day" convenience buttons

4. **Notification Dialog**:
   - Appears when an alarm triggers
   - Shows alarm label and current time
   - Provides dismiss option

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
   - Alarm sound plays
   - Shows alarm label and current time
   - User can dismiss (which stops the sound)

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
   - Conversion between Python lists and QML arrays

4. **Timer Management**:
   - Proper cleanup of timers when alarms are deleted or disabled
   - Handling of edge cases like time changes or system sleep

## Performance Considerations

1. **Model Updates**:
   - ListView model is efficiently updated using QAbstractListModel
   - Temporary detachment during updates prevents flickering

2. **UI Rendering**:
   - Efficient use of Rectangle elements
   - Minimal use of expensive effects

3. **Theme Changes**:
   - Property binding for immediate theme updates
   - Efficient color property updates

4. **Timer Efficiency**:
   - Single-shot timers that only activate when needed
   - No continuous polling or checking
   - Automatic cleanup to prevent memory leaks

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

4. **Timer Management**:
   - Each alarm has its own dedicated QTimer
   - Timers are single-shot and precisely scheduled
   - Automatic rescheduling for recurring alarms

## Customization Guide

### Changing Colors and Themes

The alarm system uses the application's theming system for consistent appearance. To customize colors:

1. **Modify Theme Colors in style.py**:
   ```python
   # In frontend/style.py
   LIGHT_THEME = {
       "background_color": "#FFFFFF",
       "background_secondary_color": "#F5F5F5",
       "accent_color": "#007BFF",  # Change this to your preferred accent color
       "text_primary_color": "#333333",
       "text_secondary_color": "#666666",
       "border_color": "#DDDDDD",
       "danger_color": "#DC3545"   # Change this for delete buttons
   }
   
   DARK_THEME = {
       "background_color": "#121212",
       "background_secondary_color": "#1E1E1E",
       "accent_color": "#0D6EFD",  # Change this to your preferred accent color
       "text_primary_color": "#FFFFFF",
       "text_secondary_color": "#AAAAAA",
       "border_color": "#333333",
       "danger_color": "#DC3545"   # Change this for delete buttons
   }
   ```

2. **Use Theme Properties in QML**:
   All UI components in AlarmScreen.qml use ThemeManager properties. For example:
   ```qml
   Rectangle {
       color: ThemeManager.background_secondary_color
       border.color: ThemeManager.border_color
   }
   
   Text {
       color: ThemeManager.text_primary_color
   }
   
   Button {
       background: Rectangle {
           color: ThemeManager.accent_color
       }
       contentItem: Text {
           color: ThemeManager.accent_text_color
       }
   }
   ```

3. **Add New Theme Properties**:
   If you need additional theme properties:
   - Add them to the theme dictionaries in style.py
   - Expose them in ThemeManager.py
   - Use them in QML components

### Changing Icons

The alarm system uses SVG icons for buttons and controls. To customize icons:

1. **Replace Icon Files**:
   - Icons are stored in `frontend/icons/`
   - Replace existing SVG files with your own (keep the same filenames)
   - Or add new icons and update the references in QML

2. **Update Icon References in QML**:
   ```qml
   // In AlarmControls.qml
   var clockButton = createButton(
       "../icons/clock.svg",  // Change this path to your custom icon
       "Show Clock",
       24
   );
   
   // In AlarmScreen.qml
   Rectangle {
       // ...
       Text {
           text: "+"  // This could be replaced with an Image using an SVG
       }
   }
   ```

3. **Adjust Icon Sizes**:
   ```qml
   Image {
       source: "../icons/your_custom_icon.svg"
       width: 24  // Adjust size as needed
       height: 24
       sourceSize.width: 24
       sourceSize.height: 24
   }
   ```

### Customizing the UI Layout

To modify the layout of the alarm screen:

1. **Edit Panel Customization**:
   - Modify the `editPanel` Rectangle in AlarmScreen.qml
   - Adjust the height, animation, and content layout

2. **Alarm List Item Customization**:
   - Modify the delegate Rectangle in the ListView
   - Adjust the height, spacing, and content layout

3. **Day Selection UI Customization**:
   - Modify the `dayGrid` GridLayout in AlarmScreen.qml
   - Adjust the columns, spacing, and button size

4. **Notification Dialog Customization**:
   - Modify the `alarmNotification` Dialog in AlarmScreen.qml
   - Adjust the size, content, and button layout

## Future Development Tips

### Adding New Features

1. **Adding Snooze Functionality**:
   - Modify the notification dialog to include a snooze button
   - Add a method to AlarmController to create a one-time alarm for snoozing
   ```qml
   Button {
       text: "Snooze (5 min)"
       onClicked: {
           // Get current time
           var now = new Date()
           var snoozeHour = now.getHours()
           var snoozeMinute = now.getMinutes() + 5
           
           // Handle minute overflow
           if (snoozeMinute >= 60) {
               snoozeMinute -= 60
               snoozeHour = (snoozeHour + 1) % 24
           }
           
           // Create a one-time alarm
           AlarmController.addAlarm(
               alarmNotification.alarmTitle + " (Snoozed)",
               snoozeHour,
               snoozeMinute,
               true,
               []  // Empty array for one-time alarm
           )
           
           alarmNotification.close()
       }
   }
   ```

2. **Adding Alarm Sounds**:
   - Create a sound player class in Python
   - Add methods to play, pause, and stop sounds
   - Expose the sound player to QML
   - Add sound selection to the alarm edit panel
   ```python
   # Example sound player class
   class SoundPlayer(QObject):
       @Slot(str)
       def play_sound(self, sound_name):
           # Play the sound
           pass
       
       @Slot()
       def stop_sound(self):
           # Stop the sound
           pass
   ```

3. **Adding Alarm Categories**:
   - Extend the alarm data model to include a category field
   - Add category selection to the edit panel
   - Update the ListView delegate to display the category
   - Add filtering by category

### Improving Performance

1. **Optimize Model Updates**:
   - Use beginResetModel() and endResetModel() for bulk updates
   - Use dataChanged() signal for individual item updates
   - Avoid unnecessary model resets

2. **Lazy Loading**:
   - Load alarm details only when needed
   - Use a placeholder for alarm list items until they're visible

3. **Reduce Property Bindings**:
   - Minimize complex property bindings
   - Use functions for complex calculations instead of bindings

4. **Timer Optimization**:
   - For very distant alarms, consider using a placeholder timer
   - Reschedule timers after system time changes

### Debugging Tips

1. **QML Debugging**:
   - Add console.log() statements to track property values and function calls
   - Use the QML Debugger in Qt Creator for visual debugging

2. **Python Debugging**:
   - Add logging statements to track method calls and data flow
   - Use the Python debugger (pdb) for step-by-step debugging

3. **Model Debugging**:
   - Log model data before and after updates
   - Verify role names and data types

4. **Timer Debugging**:
   - Log timer creation, scheduling, and triggering
   - Verify timer intervals and trigger times

## Troubleshooting Common Issues

### UI Not Updating After Model Changes

**Symptoms**: Changes to alarms don't appear in the UI immediately.

**Solutions**:
1. Ensure the `alarmsChanged` signal is being emitted
2. Verify the ListView model is being updated correctly
3. Check for errors in the console log
4. Try forcing a model reset:
   ```qml
   // In AlarmScreen.qml
   function onAlarmsChanged() {
       alarmListView.model = null
       alarmListView.model = AlarmController.alarmModel()
   }
   ```

### Alarm Not Triggering

**Symptoms**: Alarms don't trigger at the scheduled time.

**Solutions**:
1. Check if the alarm is enabled
2. Verify the alarm data is correct (hour, minute, days_of_week)
3. Check if the timer is being created and scheduled correctly
4. Verify the system time is correct
5. Check for errors in the console log

### Theme Colors Not Applied

**Symptoms**: UI components don't use the correct theme colors.

**Solutions**:
1. Verify ThemeManager is properly registered in main.py
2. Check if the theme properties are being accessed correctly in QML
3. Ensure the theme is being set correctly in ThemeManager
4. Check for errors in the console log

## Recent Improvements

The alarm system has been significantly improved with the following changes:

1. **Efficient Timer-Based Alarm Triggering**:
   - Replaced periodic checking with precise timer scheduling
   - Each alarm now has its own dedicated timer
   - Timers are scheduled to trigger at the exact alarm time
   - Significantly reduced CPU usage and improved battery life
   - Increased precision for alarm triggering

2. **Improved Architecture**:
   - New AlarmManager v2 with direct timer management
   - New AlarmController v2 that maintains QML compatibility
   - Better separation of concerns between components
   - More robust error handling and edge case management

3. **Enhanced Performance**:
   - Eliminated polling overhead
   - Reduced background CPU usage
   - More efficient memory usage
   - Better scaling with large numbers of alarms

4. **Improved User Experience**:
   - More precise alarm triggering
   - Consistent behavior across system states
   - Integrated audio playback for alarms
   - Better handling of recurring alarms

These improvements have resulted in a more reliable, efficient, and user-friendly alarm system.
