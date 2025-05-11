import logging
from PySide6.QtCore import QObject, Signal, Slot, Property
import re
import json

logger = logging.getLogger(__name__)

class NavigationController(QObject):
    """
    Controller that handles natural language navigation commands for the frontend UI.
    
    This class maps natural language commands like "show chat" or "go to weather"
    to the appropriate screen navigation actions.
    """
    
    # Signal emitted when a navigation command is recognized
    navigationRequested = Signal(str)  # Emits the QML screen name to navigate to
    navigationWithParamsRequested = Signal(str, dict)  # Emits screen name and params dictionary
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._initialize_navigation_maps()
        logger.info("[NavigationController] Initialized")
        
        # Connect to our own signals for logging
        self.navigationRequested.connect(self._log_navigation)
        self.navigationWithParamsRequested.connect(self._log_navigation_with_params)
    
    def _initialize_navigation_maps(self):
        """Initialize the mapping dictionaries for navigation commands"""
        
        # Map of keywords to screen names
        self._screen_keywords = {
            # Chat screen keywords
            "chat": "ChatScreen.qml",
            "conversation": "ChatScreen.qml",
            "assistant": "ChatScreen.qml",
            "talk": "ChatScreen.qml",
            
            # Weather screen keywords
            "weather": "WeatherScreen.qml",
            "forecast": "WeatherScreen.qml",
            "temperature": "WeatherScreen.qml",
            
            # Weather sub-screens (these will be handled specially)
            "hourly weather": "WeatherScreen.qml|hourly",
            "hourly forecast": "WeatherScreen.qml|hourly",
            "weather graph": "WeatherScreen.qml|hourly",
            "hourly graph": "WeatherScreen.qml|hourly",
            "7 day weather": "WeatherScreen.qml|sevenday",
            "7 day forecast": "WeatherScreen.qml|sevenday",
            "7-day weather": "WeatherScreen.qml|sevenday",
            "7-day forecast": "WeatherScreen.qml|sevenday",
            "seven day weather": "WeatherScreen.qml|sevenday",
            "seven day forecast": "WeatherScreen.qml|sevenday",
            "weekly weather": "WeatherScreen.qml|sevenday",
            "weekly forecast": "WeatherScreen.qml|sevenday",
            "current weather": "WeatherScreen.qml|current",
            
            # Calendar screen keywords
            "calendar": "CalendarScreen.qml",
            "schedule": "CalendarScreen.qml",
            "events": "CalendarScreen.qml",
            "appointments": "CalendarScreen.qml",
            
            # Clock screen keywords
            "clock": "ClockScreen.qml",
            "time": "ClockScreen.qml",
            
            # Alarm screen keywords
            "alarm": "AlarmScreen.qml",
            "alarms": "AlarmScreen.qml",
            "wake": "AlarmScreen.qml",
            
            # Timer screen keywords
            "timer": "TimerScreen.qml",
            "countdown": "TimerScreen.qml",
            "stopwatch": "TimerScreen.qml",
            
            # Photo screen keywords
            "photo": "PhotoScreen.qml",
            "photos": "PhotoScreen.qml",
            "pictures": "PhotoScreen.qml",
            "gallery": "PhotoScreen.qml",
            "slideshow": "PhotoScreen.qml",
            "images": "PhotoScreen.qml",
            
            # Settings screen keywords
            "settings": "SettingsScreen.qml",
            "preferences": "SettingsScreen.qml",
            "options": "SettingsScreen.qml",
            "configuration": "SettingsScreen.qml",
        }
        
        # Common command patterns - improved to be more specific and handle more variations
        self._command_patterns = [
            # Basic navigation commands
            r"(?:show|display|open|go to|navigate to|take me to|switch to|view)\s+(?:the\s+)?(\w+(?:\s+\w+)*)(?:\s+screen|\s+page|\s+view)?$",
            
            # Commands with "I want to" prefix
            r"(?:i want to see|i want to view|i want to go to|i would like to see|show me)\s+(?:the\s+)?(\w+(?:\s+\w+)*)(?:\s+screen|\s+page|\s+view)?$",
            
            # Direct commands (just the screen name)
            r"^(\w+(?:\s+\w+)*)(?:\s+screen|\s+page|\s+view)$",
            
            # Commands starting with "can you"
            r"(?:can you|could you)(?:\s+please)?\s+(?:show|display|open|go to|navigate to|take me to|switch to|view)\s+(?:the\s+)?(\w+(?:\s+\w+)*)(?:\s+screen|\s+page|\s+view)?",
        ]
        
        logger.info(f"[NavigationController] Initialized with {len(self._screen_keywords)} keyword mappings and {len(self._command_patterns)} command patterns")
    
    @Slot(str)
    def processNavigationCommand(self, command):
        """
        Process a natural language navigation command and emit a signal if recognized.
        
        Args:
            command: String containing the natural language command
        
        Returns:
            bool: True if a navigation command was recognized and processed
        """
        if not command or not isinstance(command, str):
            return False
        
        # Convert to lowercase for case-insensitive matching
        command = command.lower().strip()
        logger.debug(f"[NavigationController] Processing command: '{command}'")
        
        # Try to match the command against our patterns
        for pattern in self._command_patterns:
            matches = re.search(pattern, command)
            if matches:
                keyword = matches.group(1).strip()
                logger.debug(f"[NavigationController] Pattern matched, extracted keyword: '{keyword}'")
                return self._navigate_by_keyword(keyword)
        
        # If no pattern matched, check for exact keyword matches
        # Use spaces to ensure we match whole words, not substrings
        command_with_spaces = f" {command} "
        for keyword, screen in self._screen_keywords.items():
            keyword_pattern = f" {keyword} "
            if keyword_pattern in command_with_spaces:
                logger.debug(f"[NavigationController] Exact keyword match found: '{keyword}'")
                return self._navigate_by_keyword(keyword)
        
        # Last resort: check if any command word is a keyword
        command_words = command.split()
        for word in command_words:
            if word in self._screen_keywords:
                logger.debug(f"[NavigationController] Found keyword as single word in command: '{word}'")
                return self._navigate_by_keyword(word)
        
        logger.debug(f"[NavigationController] No navigation patterns matched for: '{command}'")
        return False
    
    def _navigate_by_keyword(self, keyword):
        """
        Navigate to the screen associated with the keyword if found.
        
        Args:
            keyword: String containing the navigation keyword
        
        Returns:
            bool: True if navigation was successful, False otherwise
        """
        # Direct keyword matching
        if keyword in self._screen_keywords:
            screen_name = self._screen_keywords[keyword]
            
            # Check if this is a special case for weather sub-screens
            if "|" in screen_name:
                screen_parts = screen_name.split("|")
                base_screen = screen_parts[0]
                view_type = screen_parts[1]
                logger.info(f"[NavigationController] Navigating to {base_screen} with view: {view_type}")
                
                # Use the special signal that includes parameters
                self.navigationWithParamsRequested.emit(base_screen, {"viewType": view_type})
                return True
            else:
                # Standard navigation
                logger.info(f"[NavigationController] Navigating to {screen_name} via keyword: {keyword}")
                self.navigationRequested.emit(screen_name)
                return True
        
        # Try to find a more precise partial match
        # Look for keywords that contain the entire search term as a word
        for k, screen in self._screen_keywords.items():
            # Check if the keyword is a complete substring of k
            # or if k is a complete substring of the keyword
            if (
                # The entire keyword is contained within k
                f" {keyword} " in f" {k} " or
                # The keyword is at the start of k
                k.startswith(keyword + " ") or
                # The keyword is at the end of k
                k.endswith(" " + keyword) or
                # The keyword is exactly k
                k == keyword
            ):
                # Check if this is a special case for weather sub-screens
                if "|" in screen:
                    screen_parts = screen.split("|")
                    base_screen = screen_parts[0]
                    view_type = screen_parts[1]
                    logger.info(f"[NavigationController] Navigating to {base_screen} with view: {view_type} via precise partial match: {k}")
                    
                    # Use the special signal that includes parameters
                    self.navigationWithParamsRequested.emit(base_screen, {"viewType": view_type})
                    return True
                else:
                    # Standard navigation
                    logger.info(f"[NavigationController] Navigating to {screen} via precise partial match: {k}")
                    self.navigationRequested.emit(screen)
                    return True
        
        # More flexible matching as fallback
        # This is less precise but helps with variations like "weather forecast" matching "forecast"
        for k, screen in self._screen_keywords.items():
            # Only match if the entire word k is contained within the keyword phrase
            if f" {k} " in f" {keyword} ":
                # Check if this is a special case for weather sub-screens
                if "|" in screen:
                    screen_parts = screen.split("|")
                    base_screen = screen_parts[0]
                    view_type = screen_parts[1]
                    logger.info(f"[NavigationController] Navigating to {base_screen} with view: {view_type} via keyword contained in phrase: {k}")
                    
                    # Use the special signal that includes parameters
                    self.navigationWithParamsRequested.emit(base_screen, {"viewType": view_type})
                    return True
                else:
                    # Standard navigation
                    logger.info(f"[NavigationController] Navigating to {screen} via keyword contained in phrase: {k}")
                    self.navigationRequested.emit(screen)
                    return True
        
        logger.warning(f"[NavigationController] No navigation target found for keyword: {keyword}")
        return False
    
    @Slot(str, str)
    def handleBackendNavigationRequest(self, screen_name, params_json="{}"):
        """
        Handle a navigation request from the backend.
        
        This method is called when the backend sends a navigation request to the frontend,
        typically in response to an LLM tool call.
        
        Args:
            screen_name: The name of the screen to navigate to
            params_json: JSON string containing parameters for the screen
        """
        try:
            params = json.loads(params_json) if params_json else {}
        except json.JSONDecodeError:
            logger.error(f"[NavigationController] Invalid JSON in params: {params_json}")
            params = {}
        
        # Check if the screen name is a QML file or a keyword
        if screen_name.endswith(".qml"):
            logger.info(f"[NavigationController] Backend navigation to {screen_name} with params: {params}")
            if params:
                self.navigationWithParamsRequested.emit(screen_name, params)
            else:
                self.navigationRequested.emit(screen_name)
            return True
        else:
            # Direct keyword matching for backend requests - must be exact
            screen_name_lower = screen_name.lower()
            if screen_name_lower in self._screen_keywords:
                screen = self._screen_keywords[screen_name_lower]
                logger.info(f"[NavigationController] Backend navigation to {screen} via exact keyword match")
                if params:
                    self.navigationWithParamsRequested.emit(screen, params)
                else:
                    self.navigationRequested.emit(screen)
                return True
                
            # Try for prefix match (e.g., "alarm" should match "AlarmScreen.qml")
            for keyword, screen in self._screen_keywords.items():
                if keyword.startswith(screen_name_lower) or screen_name_lower.startswith(keyword):
                    logger.info(f"[NavigationController] Backend navigation to {screen} via prefix match: {keyword}")
                    if params:
                        self.navigationWithParamsRequested.emit(screen, params)
                    else:
                        self.navigationRequested.emit(screen)
                    return True
            
            # No match found
            logger.warning(f"[NavigationController] No screen found for backend request: {screen_name}")
            return False 
    
    def _log_navigation(self, screen_name):
        """Log navigation requests for debugging"""
        logger.debug(f"[NavigationController] Navigation signal emitted for screen: {screen_name}")
    
    def _log_navigation_with_params(self, screen_name, params):
        """Log navigation with params requests for debugging"""
        logger.debug(f"[NavigationController] Navigation with params signal emitted for screen: {screen_name}, params: {params}") 