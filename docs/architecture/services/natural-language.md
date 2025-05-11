# Natural Language Command Processors

The application implements several natural language command processors that enable conversational control of various features.

## TimerCommandProcessor

The `TimerCommandProcessor` class handles natural language commands for the timer functionality. It uses regular expressions to match user input patterns like "set timer for 5 minutes" or "how much time is left on the timer". When a command is recognized, it calls the appropriate methods on the `TimerController` to perform the requested action, and then emits a signal with a response message that gets added to the chat history.

Key features:
- Setting timers with specific durations
- Starting/pausing/resuming timers
- Canceling timers
- Checking time remaining on active timers
- Support for various command formats and patterns

## AlarmCommandProcessor

The `AlarmCommandProcessor` class provides natural language processing for alarm functionality. Similar to the `TimerCommandProcessor`, it uses regex patterns to match user input like "set alarm for 7am" or "list all alarms". When a command is recognized, it calls the appropriate methods on the `AlarmController` to perform the requested action, and emits a signal with a response message that gets added to the chat history.

Key features of the `AlarmCommandProcessor`:
- Setting alarms with specific times (12-hour or 24-hour format)
- Setting recurring alarms (daily, weekdays, weekends, or specific days)
- Naming alarms
- Listing all alarms
- Enabling/disabling alarms
- Deleting alarms

### Time Parsing Improvements (May 2025)
- **PM Time Conversion Fix**: Fixed issues with PM time conversion in AlarmCommandProcessor:
  - Enhanced PM indicator detection to handle various formats (PM, pm, p.m., p.m)
  - Improved time parsing logic to correctly convert times with separators (e.g., "11:30 p.m.")
  - Added special case handling for edge cases like "11:30 p.m." to ensure proper conversion to 24-hour format
  - Implemented better parsing of the full command string to detect PM indicators
  - Added extensive debugging logs for time parsing to assist future troubleshooting
  - Fixed issue where "8 PM" was incorrectly interpreted as 0800 (8:00 AM) instead of 2000 (8:00 PM)
  - Ensured consistent handling of times with and without separators (e.g., "8 PM" vs "11:30 p.m.")

### Time Parsing Improvements (August 2025)
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

## Integration with Application Architecture

The command processors require instances of their respective controllers to be passed to their constructors:

```python
# Create the AlarmCommandProcessor and connect it to the AlarmController
alarm_command_processor_instance = AlarmCommandProcessor(alarm_controller_instance)

# Connect AlarmCommandProcessor to ChatController for processing alarm commands
chat_controller_instance.alarm_command_processor = alarm_command_processor_instance
```

This architecture allows the command processors to focus on language parsing while delegating actual functionality to the controllers.

## Processing Workflow

1. User enters a natural language command in the chat interface
2. ChatController receives the input and sends it to the appropriate command processor 
3. Command processor uses regex patterns to match and extract parameters from the command
4. If matched, the processor calls the appropriate controller method with the extracted parameters
5. The processor emits a signal with a response message that gets added to the chat history
6. If no match is found, the input is passed on to the LLM for processing

This architecture provides a fast, responsive way to handle common commands without requiring LLM processing, while still falling back to the LLM for more complex queries. 