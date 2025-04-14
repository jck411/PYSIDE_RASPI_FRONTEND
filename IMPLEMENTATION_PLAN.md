# Alarm Clock Feature Implementation Plan

This plan outlines the steps to implement the client-side alarm clock functionality using an event-driven approach with PySide.

## 1. Alarm Data Management (`utils/alarm_manager.py`)

-   [ ] Create `utils/alarm_manager.py`.
-   [ ] Define `AlarmManager` class inheriting from `QObject`.
-   [ ] Define alarm data structure (e.g., `id`, `hour`, `minute`, `label`, `days_of_week` (set), `is_enabled`). Use UUID for `id`.
-   [ ] Implement configuration file path logic (e.g., using `QStandardPaths` or similar for platform-independent config location like `~/.config/YourAppName/alarms.json`).
-   [ ] Implement `_load_alarms()` method:
    -   [ ] Read from JSON file.
    -   [ ] Handle file not found gracefully (return empty list).
    -   [ ] Handle JSON decoding errors.
-   [ ] Implement `_save_alarms()` method:
    -   [ ] Write current alarms list to JSON file.
    -   [ ] Ensure directory exists.
-   [ ] Implement `get_all_alarms()` method.
-   [ ] Implement `get_alarm(alarm_id)` method.
-   [ ] Implement `add_alarm(hour, minute, label, days_of_week, is_enabled=True)` method:
    -   [ ] Generate unique ID.
    -   [ ] Add alarm to internal list.
    -   [ ] Call `_save_alarms()`.
-   [ ] Implement `update_alarm(alarm_id, **changes)` method:
    -   [ ] Find alarm by ID.
    -   [ ] Update specified fields.
    -   [ ] Call `_save_alarms()`.
-   [ ] Implement `delete_alarm(alarm_id)` method:
    -   [ ] Remove alarm by ID.
    -   [ ] Call `_save_alarms()`.
-   [ ] Define `alarmsChanged = Signal()` in `AlarmManager`.
-   [ ] Emit `alarmsChanged` signal in `add_alarm`, `update_alarm`, and `delete_alarm` after `_save_alarms()`.
-   [ ] Add basic unit tests for `AlarmManager`.

## 2. Alarm Checking Service (`services/alarm_checker.py`)

-   [ ] Create `services/alarm_checker.py`.
-   [ ] Define `AlarmChecker` class inheriting from `QObject`.
-   [ ] Inject `AlarmManager` instance (or provide access method).
-   [ ] Add `QTimer` instance.
-   [ ] Implement timer configuration (e.g., interval of 10-30 seconds).
-   [ ] Implement `start()` and `stop()` methods for the timer.
-   [ ] Define `alarmTriggered = Signal(dict)` signal (payload contains alarm details).
-   [ ] Implement `_check_alarms()` slot connected to `QTimer.timeout`.
-   [ ] Inside `_check_alarms()`:
    -   [ ] Get current local time (`datetime.now()`).
    -   [ ] Get day of the week index (Monday=0 or Sunday=0, be consistent).
    -   [ ] Get all enabled alarms from `AlarmManager`.
    -   [ ] Iterate through enabled alarms.
    -   [ ] Compare current time (hour, minute) and day of week with alarm settings.
    -   [ ] Implement state management to track recently triggered alarms (e.g., store `(alarm_id, trigger_timestamp)`) to avoid re-triggering within the same minute. Check this state before emitting.
    -   [ ] If an alarm matches and hasn't been recently triggered, emit `alarmTriggered` with alarm details. Update triggered state.
-   [ ] Consider connecting to `AlarmManager.alarmsChanged` to clear the triggered state if an alarm is modified or deleted.

## 3. UI Integration (`ui/screens/ClockScreen.py`)

-   [ ] Instantiate `AlarmManager` (likely passed in or accessed via a central app object).
-   [ ] Instantiate `AlarmChecker` (passing `AlarmManager`).
-   [ ] Connect a UI update slot (e.g., `_refresh_alarm_list`) to `AlarmManager.alarmsChanged`.
-   [ ] Implement `_refresh_alarm_list()`:
    -   [ ] Clear existing alarm display.
    -   [ ] Get all alarms using `AlarmManager.get_all_alarms()`.
    -   [ ] Populate a `QListWidget` or similar with alarm details (Time, Label, Days).
    -   [ ] Include an enable/disable toggle (e.g., `QCheckBox`) for each alarm. Connect its `stateChanged` signal to `AlarmManager.update_alarm`.
    -   [ ] Include a delete button for each alarm. Connect its `clicked` signal to `AlarmManager.delete_alarm`.
-   [ ] Implement an "Add Alarm" button.
-   [ ] Create a new dialog or widget (`ui/dialogs/AddAlarmDialog.py`?) for adding/editing alarms:
    -   [ ] Include time input (e.g., `QTimeEdit`).
    -   [ ] Include label input (`QLineEdit`).
    -   [ ] Include day selection (e.g., checkboxes for Mon-Sun).
    -   [ ] Handle "Save" and "Cancel". On Save, call `AlarmManager.add_alarm`.
-   [ ] Modify the "Edit" functionality (could reuse Add/Edit dialog) triggered from the alarm list.
-   [ ] Connect a notification slot (e.g., `_handle_alarm_trigger`) to `AlarmChecker.alarmTriggered`.
-   [ ] Implement `_handle_alarm_trigger(alarm_details)`:
    -   [ ] Display a notification (e.g., `QMessageBox` or a custom non-blocking notification widget).
    -   [ ] Optionally, implement sound playback (requires additional library like `playsound` or `PyQt5.QtMultimedia`).

## 4. Application Integration

-   [ ] Ensure `AlarmManager` and `AlarmChecker` instances are created at application startup (e.g., in `main.py` or the main window class).
-   [ ] Ensure the `AlarmChecker` timer is started using `AlarmChecker.start()`.
-   [ ] Ensure proper cleanup (e.g., stopping the timer) on application exit.

## 5. Documentation

-   [ ] Update `ARCHITECTURE.md` to describe the new `AlarmManager`, `AlarmChecker`, UI components, and their interactions for the alarm feature. 