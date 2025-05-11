# Navigation System

The application includes a natural language navigation system that allows users to navigate between screens using conversational commands.

## Natural Language Navigation Features

- **Conversational Navigation Commands**: Users can navigate the application with natural language commands:
  - "Show me the weather"
  - "Go to calendar"
  - "Open photos" 
  - "I want to see the clock"
  - "Show alarm screen"
  - "Show timer"
  - "Display settings"

- **Sub-Screen Navigation**: The system supports navigation to specific sub-screens:
  - "Show hourly weather" - navigates to the hourly weather graph
  - "Show 7 day forecast" - navigates to the 7-day forecast view
  - "Show current weather" - navigates to the main weather view
  - Additional sub-screens for other components can be easily added

- **Dual Navigation Mechanisms**:
  1. **Direct UI Command Processing**: Commands entered in the chat input are intercepted and processed before being sent to the LLM
  2. **LLM Tool Calling**: The LLM can call navigation functions directly using the function calling API

- **Precise Command Matching**:
  - Multi-tiered matching algorithm to prevent navigation to incorrect screens
  - Pattern-based extraction of screen names from natural language
  - Whole-word and exact keyword matching to minimize false positives
  - Prefix matching for partial commands (e.g., "alarm" matches "alarms")
  - Detailed logging for troubleshooting navigation issues

- **Consistent Navigation Patterns**:
  - All screens use the same navigation system
  - Natural language commands are processed consistently
  - The system handles variations in phrasing and wording
  - Commands work regardless of capitalization or precise wording

## Navigation Architecture

- **NavigationController**: Core controller that manages natural language navigation
  - Maps keywords to screen names
  - Processes natural language commands using regex patterns
  - Uses multiple matching algorithms for precision and flexibility
  - Special handling for sub-screen navigation with parameters
  - Emits signals to trigger screen navigation
  - Handles backend navigation requests with parameters

- **Integration with Chat Interface**:
  - ChatController intercepts navigation commands before sending to LLM
  - Provides immediate response to navigation requests
  - Prevents unnecessary LLM API calls for basic navigation

- **LLM Function Calling**:
  - Backend defines a `navigate_to_screen` function
  - LLM can call this function to trigger navigation
  - Function accepts screen name and optional parameters
  - Multi-tiered matching to handle various screen name formats
  - Parameters can be passed to control screen behavior (e.g., viewType for weather screens)

- **MainWindow Integration**:
  - Listens for navigation signals
  - Updates the StackView to show requested screens
  - Handles navigation with parameters for advanced use cases
  - Passes parameters to screens as component properties

- **Screen Parameter Handling**:
  - Screens check for _navigationParams during Component.onCompleted
  - Parameters control initial view state, like which sub-view to show
  - Common pattern enables consistent handling across all screens 