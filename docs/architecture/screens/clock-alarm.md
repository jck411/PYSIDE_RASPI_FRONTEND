# Clock and Alarm Implementation

## Clock and Alarm Architecture
The application provides both time display and alarm management functionality:

- **ClockScreen**: Focused on displaying the current time and date with a large, easy-to-read digital display
  - Shows hours, minutes, seconds in a large font
  - Displays current date (month, day, year)
  - Shows the day of the week

- **AlarmScreen**: Dedicated screen for managing alarms
  - Displays a list of configured alarms with time, name, and recurrence pattern
  - Provides controls to add, edit, and delete alarms
  - Supports various recurrence patterns (Once, Daily, Weekdays, Weekends, Custom)
  - Includes improved property binding for alarm IDs to ensure reliable alarm deletion
  - Uses multiple fallbacks for property access to handle different controller implementations
  
- **Alarm Notifications**: When an alarm triggers, a notification dialog is shown
  - The notification appears over any screen that's currently active
  - Offers options to dismiss or snooze the alarm
  - Snoozing an alarm creates a new one-time alarm for 5 minutes later

- **AlarmController**: Manages alarm data and functionality
  - Located in `frontend/logic/alarm_controller.py`
  - Provides methods for adding, updating, and deleting alarms
  - Handles alarm persistence via JSON file storage
  - Exposes signals to QML for alarm triggering and list updates
  - Follows camelCase naming conventions for QML-exposed methods
  - Enhanced error handling and validation for alarm management operations
  - Improved debugging for alarm deletion with detailed logging

- **Sound Notification Settings**: Configurable sound notifications for alarms and timers
  - Each feature (alarm/timer) can have its own distinct notification sound
  - Sounds can be selected from available .raw files in the sounds directory
  - Settings are persisted using the SettingsService
  - Includes test functionality to preview sounds before saving
  - Automatically detects available sound files in the sounds directory
  - Settings UI is integrated into the SettingsScreen with other application settings

## Clock Screen Implementation
The ClockScreen provides time/date display plus an integrated alarm management system:

- **Dual-View Interface**: The ClockScreen has two main screens, accessed via dedicated navigation buttons:
  - ClockScreen: Large, prominent time/date display
  - AlarmScreen: List of alarms with management controls

- **Navigation Controls**: Both screens have a consistent set of navigation buttons:
  - Clock button: Navigates to the ClockScreen
  - Alarm button: Navigates to the AlarmScreen
  - Both controls appear in the same position across both screens for consistent navigation

- **Alarm Management**: Users can create, edit, disable, and delete alarms
  - One-time alarms for specific times
  - Recurring alarms with various patterns:
    - Daily alarms
    - Weekday alarms (Mon-Fri)
    - Weekend alarms (Sat-Sun)
    - Custom day selection for any combination of days

- **UI Components**:
  - Alarm list with visual indicators for recurrence patterns
  - Time selection interface using tumbler controls for intuitive time picking
  - Alarm setup dialog with various recurrence options
  - Notification dialog with snooze functionality
  - Dedicated navigation buttons for moving between clock and alarm screens
  - Floating action button for adding new alarms, positioned in the bottom-right of the alarm list
  - Modern UI with theme-aware styling

## Alarm Edit Screen Layout Update (May 2025)
- **Improved Layout**: The alarm edit screen layout was restructured to use a more intuitive arrangement
  - The screen title and name field are positioned side by side at the top of the form
  - Save and Cancel buttons are now positioned at the bottom right of the screen
  - The main content area is organized into three distinct columns:
    - Left column: Time selection with hour/minute tumblers
    - Middle column: Repeat options (Once, Daily, Weekdays, etc.)
    - Right column: Custom day selection (only visible when "Custom" is selected)
  - Column headings are precisely aligned at the same height for visual consistency
  - Content in each column starts at the same vertical position with consistent spacing
- **Enhanced Usability**: The new layout is more consistent with standard form design patterns
  - Improved visual hierarchy with the heading and name field at the top
  - Action buttons (Save/Cancel) are consistently positioned at the bottom right
  - Content organized into logical columns that flow left-to-right
  - Custom days appear as an extension of the repeat options when needed
  - Better use of screen space for a cleaner, more organized interface
  - Consistent spacing and alignment across all form sections

## Alarm Screen UI Enhancement (May 2025)
- **In-List Add Button**: Replaced the floating action button with an integrated "Add new alarm" button within the alarm list
- **Consistent Visual Design**: The add button uses the same styling as alarm list items for visual consistency
- **SVG Icon Integration**: Incorporated the `alarm_add.svg` icon for better visual recognition
- **Improved Usability**: The add button now appears at the bottom of the alarm list, making it easy to find and use
- **Alternating Colors**: The add button respects the same alternating color scheme as the alarm items
- **Simplified Interaction**: Clean implementation that retains theme-consistent styling
- **Implementation Details**: The add button is implemented as a footer component in the ListView with:
  - Matching height and visual style to alarm list items for consistency
  - Proper color alternation based on the number of items in the list
  - Clear visual indication of its purpose with icon and text
  - Same interaction pattern as alarm items (tap/click to activate)
  - Responsive layout that adapts to different screen sizes 