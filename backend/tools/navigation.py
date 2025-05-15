import logging
from typing import Dict, Any, Optional

from backend.websocket.navigation_handler import navigation_handler

logger = logging.getLogger(__name__)

class NavigationRequest:
    """
    Data class to represent a navigation request that will be sent to the frontend.
    """
    def __init__(self, screen: str, params: Optional[Dict[str, Any]] = None):
        self.screen = screen
        self.params = params or {}

async def navigate_to_screen(screen: str, extra_params: Optional[Dict[str, Any]] = None, connection=None) -> Dict[str, Any]:
    """
    Function for the LLM to call to request navigation to a specific screen.
    
    Args:
        screen: The screen to navigate to (e.g., "chat", "weather", "clock", etc.)
        extra_params: Optional parameters to pass to the screen
        connection: Optional websocket connection to send the request to. If None, sends to all.
        
    Returns:
        Dict with status of the navigation request
    """
    # Map of screen names to QML file names
    screen_mapping = {
        "chat": "ChatScreen.qml",
        "weather": "WeatherScreen.qml",
        "calendar": "CalendarScreen.qml",
        "clock": "ClockScreen.qml",
        "alarm": "AlarmScreen.qml",
        "alarms": "AlarmScreen.qml",
        "timer": "TimerScreen.qml",
        "photos": "PhotoScreen.qml",
        "settings": "SettingsScreen.qml"
    }
    
    # Map of special sub-screen names to their parent screens and view parameters
    subscreen_mapping = {
        "hourly weather": ("WeatherScreen.qml", {"viewType": "hourly"}),
        "hourly forecast": ("WeatherScreen.qml", {"viewType": "hourly"}),
        "weather graph": ("WeatherScreen.qml", {"viewType": "hourly"}),
        "hourly graph": ("WeatherScreen.qml", {"viewType": "hourly"}),
        "7 day weather": ("WeatherScreen.qml", {"viewType": "sevenday"}),
        "7 day forecast": ("WeatherScreen.qml", {"viewType": "sevenday"}),
        "7-day weather": ("WeatherScreen.qml", {"viewType": "sevenday"}),
        "7-day forecast": ("WeatherScreen.qml", {"viewType": "sevenday"}),
        "seven day weather": ("WeatherScreen.qml", {"viewType": "sevenday"}),
        "seven day forecast": ("WeatherScreen.qml", {"viewType": "sevenday"}),
        "weekly weather": ("WeatherScreen.qml", {"viewType": "sevenday"}),
        "weekly forecast": ("WeatherScreen.qml", {"viewType": "sevenday"}),
        "current weather": ("WeatherScreen.qml", {"viewType": "current"})
    }
    
    # Convert the screen name to lowercase for case-insensitive matching
    screen_lower = screen.lower().strip()
    logger.info(f"[NavigationTool] Navigation request received for: {screen_lower}")
    
    # Check if this is a request for a sub-screen
    if screen_lower in subscreen_mapping:
        target_screen, view_params = subscreen_mapping[screen_lower]
        
        # Merge any additional parameters provided
        if extra_params:
            merged_params = {**view_params, **extra_params}
        else:
            merged_params = view_params
            
        logger.info(f"[NavigationTool] Sub-screen match found: {screen_lower} -> {target_screen} with params {merged_params}")
        
        # Create and send the navigation request
        try:
            await navigation_handler.send_navigation_request(target_screen, merged_params, connection)
            
            return {
                "status": "success",
                "message": f"Navigation request to {target_screen} with view type {merged_params['viewType']} sent",
                "screen": target_screen,
                "params": merged_params
            }
        except Exception as e:
            logger.error(f"[NavigationTool] Error sending navigation request: {e}")
            return {
                "status": "error",
                "message": f"Failed to send navigation request: {str(e)}"
            }
    
    # First try exact matching in the main screen mapping
    if screen_lower in screen_mapping:
        target_screen = screen_mapping[screen_lower]
        logger.info(f"[NavigationTool] Exact match found: {target_screen}")
    else:
        # Try more flexible matching if exact match failed
        target_screen = None
        
        # Try prefix match (e.g., if user says "alarm" we should match "AlarmScreen.qml")
        for key, value in screen_mapping.items():
            if key.startswith(screen_lower) or screen_lower.startswith(key):
                target_screen = value
                logger.info(f"[NavigationTool] Prefix match found: {key} -> {target_screen}")
                break
                
        # If no prefix match, try to find if the screen name is in any of the mapping keys
        if not target_screen:
            screen_words = screen_lower.split()
            for word in screen_words:
                if word in screen_mapping:
                    target_screen = screen_mapping[word]
                    logger.info(f"[NavigationTool] Word match found: {word} -> {target_screen}")
                    break
    
    if not target_screen:
        # Try a more flexible search in subscreen mapping
        for key, (sub_screen, _) in subscreen_mapping.items():
            if key.startswith(screen_lower) or screen_lower in key:
                target_screen = sub_screen
                logger.info(f"[NavigationTool] Partial subscreen match found: {screen_lower} matches {key} -> {target_screen}")
                
                # If it's a weather view but doesn't specify which view, default to current
                if target_screen == "WeatherScreen.qml" and not extra_params:
                    extra_params = {"viewType": "current"}
                break
    
    if not target_screen:
        # Still no match found
        logger.warning(f"[NavigationTool] Unknown screen name: {screen}")
        valid_screens = list(screen_mapping.keys()) + list(subscreen_mapping.keys())
        return {
            "status": "error",
            "message": f"Unknown screen name: {screen}. Valid screens are: {', '.join(valid_screens)}"
        }
    
    # Create a navigation request to be sent to the frontend
    nav_request = NavigationRequest(target_screen, extra_params)
    
    # Send the navigation request to connected frontends
    try:
        await navigation_handler.send_navigation_request(target_screen, extra_params, connection)
        logger.info(f"[NavigationTool] Navigation request sent: {target_screen}")
        
        return {
            "status": "success",
            "message": f"Navigation request to {target_screen} sent",
            "screen": target_screen,
            "params": extra_params
        }
    except Exception as e:
        logger.error(f"[NavigationTool] Error sending navigation request: {e}")
        return {
            "status": "error",
            "message": f"Failed to send navigation request: {str(e)}"
        }

def get_schema():
    """
    Return the schema definition for the navigation function.
    """
    return {
        "type": "function",
        "function": {
            "name": "navigate_to_screen",
            "description": "Navigate to a specific screen in the application. Use this when the user asks to see or go to a different screen.",
            "parameters": {
                "type": "object",
                "properties": {
                    "screen": {
                        "type": "string",
                        "description": "The screen to navigate to. Basic screens: chat, weather, calendar, clock, alarm, alarms, timer, photos, settings. Weather supports sub-screens: 'hourly weather', 'hourly forecast', '7 day weather', '7 day forecast', 'current weather'."
                    },
                    "extra_params": {
                        "type": "object",
                        "description": "Optional parameters to pass to the screen. For weather, you can use {\"viewType\": \"hourly\"}, {\"viewType\": \"sevenday\"}, or {\"viewType\": \"current\"}. For calendar, you can use {\"view\": \"month\"}, {\"view\": \"week\"}, or {\"view\": \"day\"}."
                    }
                },
                "required": ["screen"]
            },
            # Dependency metadata for parallel execution
            "dependencies": [],  # Navigation doesn't depend on other tools
            "provides": ["navigation_result"],  # Provides navigation result
            "parallel_safe": True  # Can be run in parallel with other operations
        }
    }

# For testing and documentation
if __name__ == "__main__":
    import asyncio
    
    async def test_navigation():
        # Test valid navigation
        result = await navigate_to_screen("weather")
        print(f"Navigation to weather: {result}")
        
        # Test with extra params
        result = await navigate_to_screen("calendar", {"view": "month"})
        print(f"Navigation to calendar with params: {result}")
        
        # Test invalid screen
        result = await navigate_to_screen("invalid_screen")
        print(f"Navigation to invalid screen: {result}")
    
    asyncio.run(test_navigation()) 