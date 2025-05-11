# Known Issues and Runtime Observations

This section captures insights gained during recent debugging and cleanup efforts.

## Runtime Issues & Fixes (Observed April 2025)
- **Chat History Path (Fixed):** An error preventing chat history saving was identified due to a hardcoded user path (`/home/jack/...`) in `frontend/logic/chat_controller.py` (`_save_history_to_file` function). This caused a permission error for the actual user (`human`). The path was corrected to use a relative path (`./chat_history`) within the project directory. Ensure this directory exists or can be created by the application.
- **Audio Configuration (Known Issue):** Logs showed numerous ALSA/JACK errors (e.g., `unable to open slave`, `Unknown PCM cards`, `Cannot open device /dev/dsp`). This indicates potential audio system misconfiguration on the target Linux environment (Raspberry Pi) that could cause instability and requires platform-specific investigation.
- **Shutdown Error (Known Issue):** A QML TypeError (`PhotoController.stop_slideshow not available during cleanup`) occurs during application shutdown, originating from `PhotoScreen.qml`. This suggests an object lifetime or shutdown sequence issue between QML and the Python `PhotoController` that needs further debugging.
- **Deepgram Connection (Observation):** Deepgram connection closure warnings and task cancellation errors were observed, potentially linked to shutdown or inactivity.

## Bug Fixes (May 2025)
- **Navigation and QML Component Simplification:** Fixed "Property has already been assigned a value" errors by:
  1. Eliminating complex code that was causing property conflicts
  2. Drastically simplifying the AlarmScreen.qml to remove unnecessary properties and functions
  3. Using direct StackView.replace() with string paths for navigation
  4. Removing excessive error handling and utility files that were adding complexity
  
  This approach aligns with best practices: minimizing the codebase and eliminating complexity rather than adding layers to work around issues.

- **AlarmNotificationDialog Creation (Fixed):** Fixed through simplification - by removing the complex dialog creation code that was no longer needed in our minimal implementation.

## Timer Command Processor Improvements (August 2025)
- **Enhanced Alarm Creation and Navigation**: Fixed issues where setting alarms only navigated to the alarm screen without creating the alarm.
  - Added comprehensive debug logging throughout the alarm creation process
  - Improved error handling in the alarm command processor and alarm manager
  - Enhanced navigation controller to provide better feedback on navigation requests
  - Ensured proper sequence of operations: first create the alarm, then navigate to the screen
  - Added safeguards for error conditions during alarm creation and navigation
  - Implemented better console logging configuration for troubleshooting
  - Improved coordination between navigation controller and alarm command processor

## Time Parsing Improvements (August 2025)
- **Improved AM/PM Handling**: Enhanced the time parsing logic to ensure proper handling of PM times.
  - Modified time parsing to first identify AM/PM indicators before extracting time components
  - Implemented a more robust approach by removing AM/PM indicators before regex matching
  - Separated time component extraction from AM/PM conversion for better maintainability
  - Consolidated the conversion logic to apply after successful parsing
  - Added more explicit logging for each step of the time parsing process
  - Fixed issues where "6 PM" was incorrectly interpreted as 0600 (6:00 AM) instead of 1800 (6:00 PM)
  - **Fixed PM Time Handling in Recurrence Patterns**: Resolved issues where "8 PM daily" was setting the alarm to 8 AM
    - Added PM detection on the full command string before extracting recurrence patterns
    - Preserved PM indicators across all command parsing methods
    - Made PM detection consistent across all alarm command types (one-time, day-specific, and recurring alarms)
    - Added thorough logging to track PM detection and conversions for easier debugging

## Time Parsing Improvements (May 2025)
- **PM Time Conversion Fix**: Fixed issues with PM time conversion in AlarmCommandProcessor:
  - Enhanced PM indicator detection to handle various formats (PM, pm, p.m., p.m)
  - Improved time parsing logic to correctly convert times with separators (e.g., "11:30 p.m.")
  - Added special case handling for edge cases like "11:30 p.m." to ensure proper conversion to 24-hour format
  - Implemented better parsing of the full command string to detect PM indicators
  - Added extensive debugging logs for time parsing to assist future troubleshooting
  - Fixed issue where "8 PM" was incorrectly interpreted as 0800 (8:00 AM) instead of 2000 (8:00 PM)
  - Ensured consistent handling of times with and without separators (e.g., "8 PM" vs "11:30 p.m.") 