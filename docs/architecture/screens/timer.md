# Timer Screen Implementation

The TimerScreen provides a countdown timer with intuitive controls:

## Timer Functionality
The application manages countdown timers with a flexible interface:

- **TimerScreen**: Dedicated UI for creating and managing timers
  - Shows active timer with hours, minutes, seconds countdown
  - Includes tumbler controls for setting time values
  - Supports timer naming for identification
  - Provides controls for pause, resume, and cancel operations
- **TimerController**: Core class that manages timer state and operations
  - Handles countdown logic with a QTimer for accurate timing
  - Emits signals for timer completion and state changes
  - Provides methods for starting, pausing, stopping, and extending timers
  - Implements a persistent timer state across application sessions
  - Automatically navigates to the TimerScreen when a timer is started, resumed, paused, stopped, or extended.
  - **Function Call API**: Provides a schema-based API for LLM integration
    - Supports direct timer creation via `create_timer()` method
    - Accepts parameters for name, hours, minutes, seconds, and auto-start option
    - Returns structured response with success status and message
    - Can be called from any part of the application without UI navigation
    - Integrates with chat interface for natural language timer creation
- **Sound Notifications**: Plays configurable alert sounds when timer completes
  - Uses application's AudioManager for consistent sound handling
  - Supports customizable sound selection via settings
- **Integration with Chat**: Allows timer creation through natural language
  - Parses timer commands like "set timer for 5 minutes"
  - Processes function call requests with structured timer parameters
  - Voice commands are integrated directly via the TimerCommandProcessor
  - Supports various command formats like "set timer to 15 minutes" or "set timer for 10 minutes"
  - Improved flexibility for cancellation commands (e.g., "cancel" or "cancel timer") in TimerCommandProcessor.
  - Responds to timer commands with natural language responses
  - Prevents navigation-only behavior by processing timer commands before navigation commands

## Timer UI Components

- **Time Selection Interface**: Uses tumblers to select hours, minutes, and seconds
  - Hour tumbler with values from 0-23
  - Minute tumbler with values from 0-59
  - Second tumbler with values from 0-59
  - Tumblers follow the same styling as the alarm edit interface

- **Quick Preset Buttons**: Preset time durations for common use cases
  - 1 minute preset
  - 5 minute preset
  - 10 minute preset
  - 30 minute preset
  - Clicking a preset immediately sets the tumblers to the corresponding time

- **Timer Controls**:
  - Start button to begin the countdown
  - Pause button to temporarily halt the countdown
  - Resume button to continue after pausing
  - Reset button to stop and reset the timer
  - Buttons dynamically show/hide based on the timer's current state

- **Timer Display**: Shows the remaining time in large, easy-to-read format
  - Display format automatically switches between MM:SS and HH:MM:SS as needed
  - Updates every second while the timer is running

- **Timer Notification**: When the timer completes, a notification dialog appears
  - Plays an alarm sound using the same AudioManager as the alarm feature
  - Notification includes a dismiss button to close the dialog and stop the sound

- **Navigation**: The screen includes the same navigation structure as Clock and Alarm screens
  - Clock button to navigate to the ClockScreen
  - Alarm button to navigate to the AlarmScreen
  - Timer button for the current screen

The timer implementation is purely client-side within QML, using the built-in Timer component for the countdown functionality. This provides a responsive user experience without requiring backend processing.

The UI follows the same design principles as the Clock and Alarm screens, maintaining visual consistency through the use of:
- Consistent color scheme from ThemeManager
- Matching font styles and sizes
- Similar layout structure and component spacing
- Consistent button styling with accent colors for primary actions
- Uniform dialog design for notifications 