from PySide6.QtCore import QObject, Signal, Property, Slot, QTimer, QTime, QUrl, QStandardPaths
import time
import logging
import os
import json
from datetime import datetime, timedelta

# Constants for file paths
CONFIG_DIR_NAME = "SmartScreenConfig"
TIMER_FILE_NAME = "timers.json"

# Function to ensure the config directory exists
def ensure_config_directory():
    config_path = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.ConfigLocation)
    app_config_dir = os.path.join(config_path, CONFIG_DIR_NAME)
    os.makedirs(app_config_dir, exist_ok=True)
    return app_config_dir

# Function to get the full path to the timer file
def get_timer_file_path():
    return os.path.join(ensure_config_directory(), TIMER_FILE_NAME)

class TimerController(QObject):
    # Signals
    timer_updated = Signal()
    timer_finished = Signal(str) # Emit timer name on finish
    timer_state_changed = Signal() # Generic signal for running/paused state changes

    def __init__(self, parent=None):
        super().__init__(parent)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.setInterval(1000) # Tick every second

        self._name = "Timer" # Default name
        self._duration = 0 # Total duration in seconds
        self._remaining_seconds = 0
        self._is_running = False
        self._is_paused = False

        # TODO: Consider loading active timers on startup if persistence is needed

    # --- Properties ---

    @Property(str, notify=timer_updated)
    def name(self):
        return self._name

    @Property(int, notify=timer_updated)
    def duration(self):
        return self._duration

    @Property(int, notify=timer_updated)
    def remaining_seconds(self):
        return self._remaining_seconds

    @Property(bool, notify=timer_state_changed)
    def is_running(self):
        return self._is_running

    @Property(bool, notify=timer_state_changed)
    def is_paused(self):
        return self._is_paused

    @Property(str, notify=timer_updated)
    def remaining_time_str(self):
        """Formats remaining time as HH:MM:SS or MM:SS."""
        total_seconds = self._remaining_seconds
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"

    # --- Slots (Callable from QML/Python) ---

    @Slot(int, int, int, str)
    def set_timer(self, hours: int, minutes: int, seconds: int, name: str = "Timer"):
        """Sets the timer duration and name, does not start it."""
        if self._is_running or self._is_paused:
            logging.warning("Cannot set timer while another is active. Stopping current timer.")
            self.stop_timer() # Stop current timer if setting a new one

        self._duration = hours * 3600 + minutes * 60 + seconds
        self._remaining_seconds = self._duration
        self._name = name if name else "Timer"
        logging.info(f"Timer set: Name='{self._name}', Duration={self._duration}s")
        self.timer_updated.emit()

    @Slot()
    def start_timer(self):
        """Starts the timer if duration is set and it's not already running."""
        if self._duration <= 0:
            logging.warning("Cannot start timer: duration not set or is zero.")
            return
        if self._is_running:
            logging.warning("Timer already running.")
            return

        if self._is_paused:
            # Resuming
            self._is_paused = False
            self._is_running = True
            self._timer.start()
            logging.info(f"Timer resumed: Name='{self._name}'")
        else:
            # Starting fresh
            # Ensure remaining seconds is reset to full duration IF timer wasn't just paused
            if not self._is_paused: # This check might be redundant if we always reset duration on set_timer/stop_timer
                 self._remaining_seconds = self._duration
            self._is_running = True
            self._is_paused = False
            self._timer.start()
            logging.info(f"Timer started: Name='{self._name}', Remaining={self._remaining_seconds}s")

        self.timer_state_changed.emit()
        self.timer_updated.emit() # Update time display immediately

    @Slot()
    def pause_timer(self):
        """Pauses the timer if it is running."""
        if not self._is_running:
            logging.warning("Cannot pause: Timer is not running.")
            return

        self._timer.stop()
        self._is_running = False
        self._is_paused = True
        logging.info(f"Timer paused: Name='{self._name}', Remaining={self._remaining_seconds}s")
        self.timer_state_changed.emit()

    @Slot()
    def stop_timer(self):
        """Stops the timer and resets its state."""
        was_active = self._is_running or self._is_paused
        self._timer.stop()
        self._is_running = False
        self._is_paused = False
        # Reset remaining time to 0, keep duration and name for potential restart
        self._remaining_seconds = 0
        logging.info(f"Timer stopped: Name='{self._name}'")
        if was_active:
            self.timer_state_changed.emit()
        # Always emit updated signal to ensure display clears or resets
        self.timer_updated.emit()

    @Slot(int)
    def extend_timer(self, seconds: int):
        """Adds more time to a running or paused timer."""
        if not self._is_running and not self._is_paused:
            logging.warning("Cannot extend: No active timer.")
            return
        if seconds <= 0:
            logging.warning("Cannot extend: Invalid number of seconds.")
            return

        self._remaining_seconds += seconds
        # Should we update self._duration? Let's say no, duration is the *original* set duration.
        logging.info(f"Timer extended: Name='{self._name}', Added={seconds}s, New Remaining={self._remaining_seconds}s")

        self.timer_updated.emit()

        # If timer had finished (remaining was 0) and we extend, restart it?
        # Let's make it automatically resume if it was paused and becomes > 0
        # Or automatically start if it was stopped (at 0) and becomes > 0
        if self._remaining_seconds > 0 and not self._is_running:
             if self._is_paused:
                 self.start_timer() # Resume if paused
             # else: # If it was stopped (at 0), should extend start it automatically?
             #    self.start_timer() # Let's try this behavior
                 # Or maybe require manual start after extending a finished timer?

    # --- Private Methods ---

    def _tick(self):
        """Called by QTimer every second."""
        if self._is_running and self._remaining_seconds > 0:
            self._remaining_seconds -= 1
            self.timer_updated.emit()

            if self._remaining_seconds <= 0:
                self._timer.stop()
                self._is_running = False
                finished_name = self._name
                logging.info(f"Timer finished: Name='{finished_name}'")
                # Reset state *before* emitting finished signal
                # Keep name/duration, reset running state and remaining seconds
                self._is_running = False
                self._is_paused = False
                self._remaining_seconds = 0 # Reset to 0 on finish
                self.timer_state_changed.emit()
                self.timer_updated.emit() # Update display to 00:00
                self.timer_finished.emit(finished_name) # Emit signal *after* state is reset

        else:
            # Safety stop if timer somehow runs with 0 seconds or not in running state
            if self._timer.isActive():
                self._timer.stop()
                self._is_running = False
                # Ensure state is consistent if we land here unexpectedly
                if self._remaining_seconds < 0: self._remaining_seconds = 0
                if self._is_paused: self._is_paused = False
                self.timer_state_changed.emit()
                self.timer_updated.emit()


# Example usage (for testing purposes)
if __name__ == '__main__':
    from PySide6.QtCore import QCoreApplication
    import sys

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    app = QCoreApplication(sys.argv)

    controller = TimerController()

    def on_finish(name):
        logging.info(f"!!! Timer '{name}' Finished Notification !!!")
        # In real app, trigger QML notification dialog here
        # app.quit() # Quit after finishing for test

    def on_update():
        logging.info(f"Update: Remaining={controller.remaining_time_str}, Running={controller.is_running}, Paused={controller.is_paused}")

    def on_state_change():
         logging.info(f"State Change: Running={controller.is_running}, Paused={controller.is_paused}")


    controller.timer_finished.connect(on_finish)
    controller.timer_updated.connect(on_update)
    controller.timer_state_changed.connect(on_state_change)

    # --- Test Scenarios ---
    # 1. Set and Start
    controller.set_timer(0, 0, 5, "Test Timer 1")
    controller.start_timer()

    # 2. Pause and Resume (use QTimer.singleShot to schedule actions)
    # QTimer.singleShot(2000, controller.pause_timer)
    # QTimer.singleShot(4000, controller.start_timer) # Resume

    # 3. Stop
    # QTimer.singleShot(3000, controller.stop_timer)

    # 4. Extend Running
    # QTimer.singleShot(2000, lambda: controller.extend_timer(5))

    # 5. Extend Paused
    # controller.set_timer(0, 0, 8, "Test Timer PauseExtend")
    # controller.start_timer()
    # QTimer.singleShot(3000, controller.pause_timer)
    # QTimer.singleShot(5000, lambda: controller.extend_timer(5)) # Extend while paused
    # QTimer.singleShot(7000, controller.start_timer) # Resume

    # 6. Set New Timer while running (should stop old one)
    # QTimer.singleShot(3000, lambda: controller.set_timer(0, 0, 3, "New Timer"))
    # QTimer.singleShot(3500, controller.start_timer)


    sys.exit(app.exec()) 