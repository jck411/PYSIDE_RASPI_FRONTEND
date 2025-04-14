import logging
from typing import Dict, Any, List, Optional
import asyncio
from PySide6.QtCore import QObject, Signal, Slot

logger = logging.getLogger(__name__)

class TimeContextProvider(QObject):
    """
    Provides time context to LLM messages.
    
    This class connects to the backend TimeContextManager to ensure
    that every LLM interaction includes current time information.
    """
    timeContextUpdated = Signal(dict)  # Signal emitted when time context changes
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._time_context: Dict[str, Any] = {}
        self._time_manager = None
        
    async def initialize(self):
        """Initialize the time context provider with the backend manager."""
        try:
            # Import backend time manager here to avoid circular imports
            from backend.tools.time import TimeContextManager
            
            # Create the time context manager
            self._time_manager = TimeContextManager(update_interval=60)  # Update every minute
            
            # Register a callback for time updates
            self._time_manager.register_update_callback(self._handle_time_update)
            
            # Start the time manager
            await self._time_manager.start()
            logger.info("Time context provider initialized")
            
            return True
        except Exception as e:
            logger.error(f"Error initializing time context provider: {e}")
            return False
    
    def _handle_time_update(self, time_data: Dict[str, Any]):
        """Handle time updates from the time manager."""
        self._time_context = time_data
        self.timeContextUpdated.emit(time_data)
        logger.debug(f"Time context updated: {time_data}")
    
    def enrich_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Add time context to the messages for the LLM.
        
        Args:
            messages: List of message dictionaries to enrich
            
        Returns:
            Enriched messages with time context
        """
        if not self._time_context:
            logger.warning("No time context available for message enrichment")
            return messages
        
        # Validate that the messages list isn't empty
        if not messages:
            logger.warning("Empty messages list provided for enrichment")
            return messages
            
        # Create a copy of messages to avoid modifying the original
        enriched_messages = messages.copy()
        
        # Check that all messages in the enriched_messages list have a 'role' field
        for msg in enriched_messages:
            if 'role' not in msg:
                logger.error(f"Message missing 'role' field: {msg}")
                # Note: we're not attempting to fix this here - it indicates a deeper issue
                return messages  # Return original messages to avoid breaking things further

        # Create a system message with time context if none exists
        has_system_message = any(msg.get("role") == "system" for msg in enriched_messages)
        
        if has_system_message:
            # Add time information to existing system message
            for msg in enriched_messages:
                if msg.get("role") == "system":
                    # Update the content to include time information
                    existing_content = msg.get("content", "")
                    time_info = self._format_time_info()
                    
                    # Check if time info already exists or needs to be updated
                    if "Current time information:" not in existing_content:
                        msg["content"] = f"{existing_content}\n\nCurrent time information: {time_info}"
                    else:
                        # Replace existing time info with updated info
                        parts = existing_content.split("Current time information:")
                        msg["content"] = f"{parts[0].rstrip()}\n\nCurrent time information: {time_info}"
                    break
        else:
            # Create a new system message with time context
            time_system_msg = {
                "role": "system",
                "content": f"Current time information: {self._format_time_info()}"
            }
            # Insert at the beginning of the message list
            enriched_messages.insert(0, time_system_msg)
        
        logger.debug(f"Messages enriched with time context. Count: {len(enriched_messages)}")
        return enriched_messages
    
    def _format_time_info(self) -> str:
        """Format time information as a human-readable string."""
        if not self._time_context:
            return "Unknown"
        
        try:
            time = self._time_context.get("time", "Unknown")
            date = self._time_context.get("date", "Unknown")
            day = self._time_context.get("day_of_week", "Unknown")
            month = self._time_context.get("month", "Unknown")
            timezone = self._time_context.get("timezone", "Unknown")
            
            # Include additional time metrics
            days_until_end_of_month = self._time_context.get("days_until_end_of_month", "Unknown")
            days_until_end_of_year = self._time_context.get("days_until_end_of_year", "Unknown")
            is_leap_year = self._time_context.get("is_leap_year", False)
            
            base_info = f"It is {time} on {day}, {month} {date} in timezone {timezone}."
            additional_info = f"There are {days_until_end_of_month} days until the end of the month and {days_until_end_of_year} days until the end of the year."
            leap_year_info = f"The current year is {'a leap year' if is_leap_year else 'not a leap year'}."
            
            return f"{base_info} {additional_info} {leap_year_info}"
        except Exception as e:
            logger.error(f"Error formatting time info: {e}")
            return "Time information unavailable."
    
    @Slot(result=dict)
    def getCurrentTimeContext(self) -> Dict[str, Any]:
        """
        Get the current time context as a dictionary.
        
        Returns:
            Dictionary containing current time information
        """
        return self._time_context.copy()
    
    async def cleanup(self):
        """Clean up resources when shutting down."""
        if self._time_manager:
            await self._time_manager.stop() 