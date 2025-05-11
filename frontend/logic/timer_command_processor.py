#!/usr/bin/env python3
import re
import logging
from PySide6.QtCore import QObject, Signal, Slot, Property

# Configure logging
logger = logging.getLogger(__name__)

class TimerCommandProcessor(QObject):
    """
    Processes natural language commands for the timer functionality.
    
    This class handles commands like "start countdown timer", "pause timer",
    "how much time left on timer", etc. and converts them to appropriate
    timer controller actions.
    """
    
    # Signals
    timerStateQueried = Signal(str)  # Signal emitted when timer state is queried, with response text
    regularUpdateRequested = Signal(int)  # Signal with update interval in seconds
    regularUpdateStopped = Signal()  # Signal to stop regular updates
    
    def __init__(self, timer_controller, parent=None):
        super().__init__(parent)
        self._timer_controller = timer_controller
        self._initialize_command_patterns()
        logger.info("[TimerCommandProcessor] Initialized")
        self._regular_reporting = False
        self._report_interval = 0
    
    def _initialize_command_patterns(self):
        """Initialize command patterns for recognizing timer commands"""
        
        unit_regex = r"(h(?:ours?)?|hr|hrs|m(?:inutes?)?|min|mins|s(?:econds?)?|sec|secs)"
        timer_identifier_regex = r"(?:(?:countdown|stopwatch)(?:\s+timer)?|(?:countdown\s+)?timer)"
        action_verb_regex = r"(?:start|begin|set)"
        optional_article_regex = r"(?:\s+(?:a|the))?"
        optional_for_to_regex = r"(?:\s+for|\s+to)?"
        required_for_named_regex = r"(?:\s+(?:for|called|named))"
        optional_conjunction_regex = r"(?:\s+(?:and|with))?"
        direct_command_keyword_regex = r"(?:countdown|stopwatch)"

        # Regex for duration: matches digits or common spelled-out numbers
        # For simplicity, covering one to twenty, and tens up to sixty.
        # More complex phrases like "one hundred" or "twenty five" would require a more advanced parser.
        duration_words = "one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty"
        duration_regex = rf"(\d+|{duration_words})"

        self._timer_control_patterns = [
            # --- Patterns starting with action verbs like "start", "set", "begin" ---
            # Verb + Timer ID + Name + Duration: e.g., "set timer T_NAME for X unit"
            (rf"{action_verb_regex}{optional_article_regex}\s+{timer_identifier_regex}{required_for_named_regex}\s+(.+?)(?:\s+for)?\s+{duration_regex}\s+{unit_regex}", self._start_timer_with_name_and_duration),
            # Verb + Timer ID + Multiple Units: e.g., "set timer for X unit and Y unit"
            (rf"{action_verb_regex}{optional_article_regex}\s+{timer_identifier_regex}(?:\s+for)?\s+{duration_regex}\s+{unit_regex}{optional_conjunction_regex}\s+{duration_regex}\s+{unit_regex}", self._start_timer_with_multiple_units),
            # Verb + Timer ID + Duration: e.g., "set timer for X unit"
            (rf"{action_verb_regex}{optional_article_regex}\s+{timer_identifier_regex}{optional_for_to_regex}\s+{duration_regex}\s+{unit_regex}", self._start_timer_with_duration),
            # Verb + Timer ID (default): e.g., "start timer"
            (rf"{action_verb_regex}{optional_article_regex}\s+{timer_identifier_regex}", self._start_timer_default),

            # --- Patterns starting directly with "countdown" or "stopwatch" ---
            # Direct Keyword + Name + Duration: e.g., "countdown T_NAME for X unit"
            (rf"{direct_command_keyword_regex}{required_for_named_regex}\s+(.+?)(?:\s+for)?\s+{duration_regex}\s+{unit_regex}", self._start_timer_with_name_and_duration),
            # Direct Keyword + Multiple Units: e.g., "countdown X unit and Y unit"
            (rf"{direct_command_keyword_regex}\s+{duration_regex}\s+{unit_regex}{optional_conjunction_regex}\s+{duration_regex}\s+{unit_regex}", self._start_timer_with_multiple_units),
            # Direct Keyword + Duration: e.g., "countdown X unit"
            (rf"{direct_command_keyword_regex}\s+{duration_regex}\s+{unit_regex}", self._start_timer_with_duration),
            # Direct Keyword (default): e.g., "countdown"
            (rf"{direct_command_keyword_regex}", self._start_timer_default),
            
            # --- Existing Pause/Resume/Cancel commands (typically use "timer" explicitly but could be reviewed if needed) ---
            (rf"(?:pause|stop|halt|freeze)(?:\s+(?:the|my))?\s+{timer_identifier_regex}", self._pause_timer),
            (rf"(?:resume|continue|restart|unpause)(?:\s+(?:the|my))?\s+{timer_identifier_regex}", self._resume_timer),
            (rf"(?:cancel|reset|clear|end)(?:\s+(?:the|my))?(?:\s+{timer_identifier_regex})?", self._stop_timer),
            
            # --- Add time command ---
            (rf"(?:add|give|extend)(?:\s+(?:the|my))?\s+{timer_identifier_regex}(?:\s+by)?\s+{duration_regex}\s+{unit_regex}", self._extend_timer),
        ]
        
        # Timer query commands
        self._timer_query_patterns = [
            # Time remaining queries
            (r"(?:how\s+much\s+time\s+(?:is|are)\s+(?:left|remaining)(?:\s+on)?|what(?:'s|\s+is)\s+(?:the\s+)?(?:remaining\s+)?time(?:\s+left)?(?:\s+on)?|time\s+left(?:\s+on)?)(?:\s+(?:the|my))?\s+(?:countdown\s+)?timer", self._query_time_remaining),
            (r"(?:what(?:'s|\s+is)(?:\s+the\s+status\s+of|\s+the\s+state\s+of)?|status\s+of|state\s+of)(?:\s+(?:the|my))?\s+(?:countdown\s+)?timer", self._query_timer_status),
        ]
        
        # Timer reporting commands
        self._timer_reporting_patterns = [
            # Regular update commands
            (r"(?:announce|tell\s+me|read\s+out|say|speak|report)(?:\s+(?:the|my))?\s+timer(?:\s+status)?(?:\s+every)\s+(\d+)\s+(seconds?|minutes?)", self._set_regular_updates),
            (r"(?:stop|end|cancel|disable)(?:\s+(?:the|my))?\s+timer(?:\s+status)?(?:\s+announcements|updates|reports?)", self._stop_regular_updates),
        ]
    
    @Slot(str)
    def processCommand(self, command):
        """
        Process a natural language command related to the timer.
        
        Args:
            command: String containing the natural language command
            
        Returns:
            bool: True if a timer command was recognized and processed
        """
        if not command or not isinstance(command, str):
            return False
        
        # Convert to lowercase for case-insensitive matching
        command = command.lower().strip()
        logger.debug(f"[TimerCommandProcessor] Processing command: '{command}'")
        
        # Check all pattern groups
        
        # First check control patterns
        for pattern, handler in self._timer_control_patterns:
            matches = re.search(pattern, command)
            if matches:
                logger.debug(f"[TimerCommandProcessor] Matched control pattern: {pattern}")
                return handler(matches)
        
        # Then check query patterns
        for pattern, handler in self._timer_query_patterns:
            matches = re.search(pattern, command)
            if matches:
                logger.debug(f"[TimerCommandProcessor] Matched query pattern: {pattern}")
                return handler(matches)
        
        # Finally check reporting patterns
        for pattern, handler in self._timer_reporting_patterns:
            matches = re.search(pattern, command)
            if matches:
                logger.debug(f"[TimerCommandProcessor] Matched reporting pattern: {pattern}")
                return handler(matches)
        
        logger.debug(f"[TimerCommandProcessor] No timer command patterns matched for: '{command}'")
        return False
    
    # === Timer control command handlers ===
    
    def _normalize_unit(self, unit_val_raw):
        """Normalize a unit string to 'hour', 'minute', or 'second'."""
        unit_val = unit_val_raw.lower()
        if unit_val in ["hour", "hours", "hr", "hrs", "h"]:
            return "hour"
        elif unit_val in ["minute", "minutes", "min", "mins", "m"]:
            return "minute"
        elif unit_val in ["second", "seconds", "sec", "secs", "s"]:
            return "second"
        else:
            logger.warning(f"Unrecognized time unit: {unit_val_raw}")
            return None

    def _parse_duration(self, duration_str_raw):
        """Convert a duration string (digit or word) to an integer."""
        if not duration_str_raw: return None
        duration_str = duration_str_raw.lower()
        word_to_num = {
            "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
            "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
            "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
            "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20,
            "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60
        }
        if duration_str in word_to_num:
            return word_to_num[duration_str]
        try:
            return int(duration_str)
        except ValueError:
            logger.warning(f"Could not parse duration: '{duration_str_raw}'")
            return None

    def _start_timer_with_duration(self, matches):
        """Handle command to start timer with a simple duration"""
        duration_str = matches.group(1)
        unit_val_raw = matches.group(2)
        
        duration = self._parse_duration(duration_str)
        if duration is None:
            self.timerStateQueried.emit(f"Sorry, I didn't understand the duration '{duration_str}'.")
            return True
            
        normalized_unit = self._normalize_unit(unit_val_raw)
        if not normalized_unit:
            self.timerStateQueried.emit(f"Sorry, I didn't understand the time unit '{unit_val_raw}'.")
            return True
            
        hours, minutes, seconds = 0, 0, 0
        
        if normalized_unit == "hour":
            hours = duration
        elif normalized_unit == "minute":
            minutes = duration
        elif normalized_unit == "second":
            seconds = duration
        
        logger.info(f"[TimerCommandProcessor] Starting timer for {hours}h {minutes}m {seconds}s")
        
        if hours == 0 and minutes == 0 and seconds == 0:
            self.timerStateQueried.emit("I can't set a timer for zero duration. Please specify a valid time.")
            return True
        
        # Set and start the timer
        self._timer_controller.set_timer(hours, minutes, seconds, "Timer")
        self._timer_controller.start_timer()
        
        time_str = self._format_duration_string(hours, minutes, seconds)
        self.timerStateQueried.emit(f"Timer started for {time_str}.")
        
        return True
    
    def _start_timer_with_multiple_units(self, matches):
        """Handle command to start timer with multiple time units (e.g., 1 hour 30 minutes)"""
        first_duration_str = matches.group(1)
        first_unit_raw = matches.group(2)
        second_duration_str = matches.group(3)
        second_unit_raw = matches.group(4)

        first_duration = self._parse_duration(first_duration_str)
        second_duration = self._parse_duration(second_duration_str)

        if first_duration is None or second_duration is None:
            err_dur = first_duration_str if first_duration is None else second_duration_str
            self.timerStateQueried.emit(f"Sorry, I didn't understand the duration '{err_dur}'.")
            return True

        norm_first_unit = self._normalize_unit(first_unit_raw)
        norm_second_unit = self._normalize_unit(second_unit_raw)

        if not norm_first_unit or not norm_second_unit:
            err_unit = first_unit_raw if not norm_first_unit else second_unit_raw
            self.timerStateQueried.emit(f"Sorry, I didn't understand the time unit '{err_unit}'.")
            return True

        hours, minutes, seconds = 0, 0, 0
        
        # Process first unit
        if norm_first_unit == "hour":
            hours = first_duration
        elif norm_first_unit == "minute":
            minutes = first_duration
        elif norm_first_unit == "second":
            seconds = first_duration
        
        # Process second unit
        if norm_second_unit == "hour": # Should not typically happen for second unit if first is not hour, but handle defensively
            if hours == 0: hours = second_duration # Or add if mixed like "1 minute 1 hour" - current regex implies order
            else: logger.warning("Second unit as hour after first unit as hour is unusual.") # Or error
        elif norm_second_unit == "minute":
            minutes = second_duration
        elif norm_second_unit == "second":
            seconds = second_duration
        
        logger.info(f"[TimerCommandProcessor] Starting timer for {hours}h {minutes}m {seconds}s")
        
        # Set and start the timer
        self._timer_controller.set_timer(hours, minutes, seconds, "Timer")
        self._timer_controller.start_timer()
        
        time_str = self._format_duration_string(hours, minutes, seconds)
        self.timerStateQueried.emit(f"Timer started for {time_str}.")
        
        return True
    
    def _start_timer_with_name_and_duration(self, matches):
        """Handle command to start timer with name and duration"""
        name = matches.group(1).strip()
        duration_str = matches.group(2)
        unit_val_raw = matches.group(3)

        duration = self._parse_duration(duration_str)
        if duration is None:
            self.timerStateQueried.emit(f"Sorry, I didn't understand the duration '{duration_str}'.")
            return True

        normalized_unit = self._normalize_unit(unit_val_raw)
        if not normalized_unit:
            self.timerStateQueried.emit(f"Sorry, I didn't understand the time unit '{unit_val_raw}'.")
            return True
            
        hours, minutes, seconds = 0, 0, 0
        
        if normalized_unit == "hour":
            hours = duration
        elif normalized_unit == "minute":
            minutes = duration
        elif normalized_unit == "second":
            seconds = duration
        
        logger.info(f"[TimerCommandProcessor] Starting timer '{name}' for {hours}h {minutes}m {seconds}s")
        
        if hours == 0 and minutes == 0 and seconds == 0:
            self.timerStateQueried.emit("I can't set a timer for zero duration. Please specify a valid time.")
            return True
        
        # Set and start the timer
        self._timer_controller.set_timer(hours, minutes, seconds, name)
        self._timer_controller.start_timer()
        
        time_str = self._format_duration_string(hours, minutes, seconds)
        self.timerStateQueried.emit(f"Timer '{name}' started for {time_str}.")
        
        return True
    
    def _start_timer_default(self, matches):
        """Handle command to start timer without specifying duration"""
        if self._timer_controller.is_paused:
            # Resume paused timer
            self._timer_controller.start_timer()
            self.timerStateQueried.emit("Timer resumed.")
        elif self._timer_controller.is_running:
            self.timerStateQueried.emit("Timer is already running.")
        elif self._timer_controller.duration > 0:
            # Restart with previously set duration
            self._timer_controller.start_timer()
            remaining = self._timer_controller.remaining_time_str
            self.timerStateQueried.emit(f"Timer started with previously set duration of {remaining}.")
        else:
            self.timerStateQueried.emit("Please specify a duration for the timer, for example 'set timer for 5 minutes'.")
        
        return True
    
    def _pause_timer(self, matches):
        """Handle command to pause the timer"""
        if self._timer_controller.is_running:
            self._timer_controller.pause_timer()
            remaining = self._timer_controller.remaining_time_str
            self.timerStateQueried.emit(f"Timer paused with {remaining} remaining.")
        elif self._timer_controller.is_paused:
            self.timerStateQueried.emit("Timer is already paused.")
        else:
            self.timerStateQueried.emit("No active timer to pause.")
        
        return True
    
    def _resume_timer(self, matches):
        """Handle command to resume the timer"""
        if self._timer_controller.is_paused:
            self._timer_controller.start_timer()
            remaining = self._timer_controller.remaining_time_str
            self.timerStateQueried.emit(f"Timer resumed with {remaining} remaining.")
        elif self._timer_controller.is_running:
            self.timerStateQueried.emit("Timer is already running.")
        else:
            self.timerStateQueried.emit("No paused timer to resume.")
        
        return True
    
    def _stop_timer(self, matches):
        """Handle command to stop/cancel the timer"""
        if self._timer_controller.is_running or self._timer_controller.is_paused:
            timer_name = self._timer_controller.name
            self._timer_controller.stop_timer()
            self.timerStateQueried.emit(f"Timer '{timer_name}' has been cancelled.")
            
            # Also stop any active reporting
            if self._regular_reporting:
                self._stop_regular_updates(None)
        else:
            self.timerStateQueried.emit("No active timer to cancel.")
        
        return True
    
    def _extend_timer(self, matches):
        """Handle command to extend the timer"""
        duration_str = matches.group(1)
        unit_val_raw = matches.group(2)

        duration = self._parse_duration(duration_str)
        if duration is None:
            self.timerStateQueried.emit(f"Sorry, I didn't understand the duration '{duration_str}'.")
            return True

        normalized_unit = self._normalize_unit(unit_val_raw)
        if not normalized_unit:
            self.timerStateQueried.emit(f"Sorry, I didn't understand the time unit '{unit_val_raw}'.")
            return True
            
        seconds_to_add = 0
        
        if normalized_unit == "hour":
            seconds_to_add = duration * 3600
        elif normalized_unit == "minute":
            seconds_to_add = duration * 60
        elif normalized_unit == "second":
            seconds_to_add = duration
        
        if self._timer_controller.is_running or self._timer_controller.is_paused:
            self._timer_controller.extend_timer(seconds_to_add)
            
            time_str = ""
            if normalized_unit == "hour":
                time_str = f"{duration} hour{'s' if duration > 1 else ''}"
            elif normalized_unit == "minute":
                time_str = f"{duration} minute{'s' if duration > 1 else ''}"
            elif normalized_unit == "second":
                time_str = f"{duration} second{'s' if duration > 1 else ''}"
                
            remaining = self._timer_controller.remaining_time_str
            self.timerStateQueried.emit(f"Timer extended by {time_str}. New remaining time: {remaining}.")
        else:
            self.timerStateQueried.emit("No active timer to extend.")
        
        return True
    
    # === Timer query command handlers ===
    
    def _query_time_remaining(self, matches):
        """Handle query about remaining time"""
        if self._timer_controller.is_running:
            remaining = self._timer_controller.remaining_time_str
            self.timerStateQueried.emit(f"Timer is running with {remaining} remaining.")
        elif self._timer_controller.is_paused:
            remaining = self._timer_controller.remaining_time_str
            self.timerStateQueried.emit(f"Timer is paused with {remaining} remaining.")
        else:
            self.timerStateQueried.emit("No active timer is running.")
        
        return True
    
    def _query_timer_status(self, matches):
        """Handle query about timer status"""
        if self._timer_controller.is_running:
            timer_name = self._timer_controller.name
            remaining = self._timer_controller.remaining_time_str
            self.timerStateQueried.emit(f"Timer '{timer_name}' is running with {remaining} remaining.")
        elif self._timer_controller.is_paused:
            timer_name = self._timer_controller.name
            remaining = self._timer_controller.remaining_time_str
            self.timerStateQueried.emit(f"Timer '{timer_name}' is paused with {remaining} remaining.")
        else:
            self.timerStateQueried.emit("No timer is currently active.")
        
        return True
    
    # === Timer reporting command handlers ===
    
    def _set_regular_updates(self, matches):
        """Handle command to set regular timer status updates"""
        interval = int(matches.group(1))
        unit = matches.group(2).lower().rstrip('s')
        
        seconds = interval
        if unit == "minute":
            seconds = interval * 60
            
        interval_text = f"{interval} {unit}{'s' if interval > 1 else ''}"
        
        if seconds < 5:
            self.timerStateQueried.emit(f"The minimum update interval is 5 seconds. Setting updates to every 5 seconds.")
            seconds = 5
            interval_text = "5 seconds"
        
        if not (self._timer_controller.is_running or self._timer_controller.is_paused):
            self.timerStateQueried.emit("No active timer to report on. Please start a timer first.")
            return True
            
        # Store the reporting interval
        self._regular_reporting = True
        self._report_interval = seconds
        
        # Emit signal with the interval
        self.regularUpdateRequested.emit(seconds)
        
        self.timerStateQueried.emit(f"I'll announce the timer status every {interval_text}.")
        return True
    
    def _stop_regular_updates(self, matches):
        """Handle command to stop regular timer status updates"""
        if self._regular_reporting:
            self._regular_reporting = False
            self._report_interval = 0
            
            # Emit signal to stop updates
            self.regularUpdateStopped.emit()
            
            self.timerStateQueried.emit("Timer status announcements have been stopped.")
        else:
            self.timerStateQueried.emit("Timer status announcements were not active.")
        
        return True
    
    # === Helper methods ===
    
    def _format_duration_string(self, hours, minutes, seconds):
        """Format a nice duration string from hours, minutes and seconds"""
        parts = []
        
        if hours > 0:
            parts.append(f"{hours} hour{'s' if hours > 1 else ''}")
        
        if minutes > 0:
            parts.append(f"{minutes} minute{'s' if minutes > 1 else ''}")
        
        if seconds > 0:
            parts.append(f"{seconds} second{'s' if seconds > 1 else ''}")
        
        if len(parts) > 1:
            return f"{', '.join(parts[:-1])} and {parts[-1]}"
        elif parts:
            return parts[0]
        else:
            return "0 seconds" 