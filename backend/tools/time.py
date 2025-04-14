from datetime import datetime, timedelta, date
import pytz
from timezonefinder import TimezoneFinder
import logging
import asyncio
import calendar
from typing import Dict, Optional, Any, Callable

logger = logging.getLogger(__name__)

class TimeContextManager:
    """
    Manages time context updates for LLM interactions.
    
    This class ensures the LLM always has access to current time information
    by automatically updating a time context object that can be included
    in message context.
    """
    def __init__(self, default_lat=28.5383, default_lon=-81.3792, update_interval=60):
        """
        Initialize the time context manager.
        
        Args:
            default_lat: Default latitude coordinate
            default_lon: Default longitude coordinate
            update_interval: How often to update the time context (in seconds)
        """
        self.default_lat = default_lat
        self.default_lon = default_lon
        self.update_interval = update_interval
        self.time_context: Dict[str, Any] = {}
        self.tf = TimezoneFinder()
        self._update_task: Optional[asyncio.Task] = None
        self._running = False
        self.on_time_update_callbacks: list[Callable[[Dict[str, Any]], None]] = []
        
    async def start(self):
        """Start the automatic time context updates."""
        if self._running:
            return
            
        self._running = True
        # Update immediately before starting the loop
        await self._update_time_context()
        self._update_task = asyncio.create_task(self._update_loop())
        logger.info("Time context manager started")
        
    async def stop(self):
        """Stop the automatic time context updates."""
        if not self._running:
            return
            
        self._running = False
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass
            self._update_task = None
        logger.info("Time context manager stopped")
    
    def register_update_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """
        Register a callback to be called when time context is updated.
        
        Args:
            callback: Function to call with updated time context
        """
        self.on_time_update_callbacks.append(callback)
    
    def unregister_update_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """
        Unregister a previously registered callback.
        
        Args:
            callback: Function to remove from callback list
        """
        if callback in self.on_time_update_callbacks:
            self.on_time_update_callbacks.remove(callback)
    
    async def _update_loop(self):
        """Run the update loop to periodically refresh time information."""
        while self._running:
            try:
                await asyncio.sleep(self.update_interval)
                await self._update_time_context()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in time context update loop: {e}")
                await asyncio.sleep(5)  # Sleep briefly before retrying
    
    async def _update_time_context(self):
        """Update the time context with current time information."""
        try:
            time_data = await get_time(self.default_lat, self.default_lon, format="detailed")
            self.time_context = time_data
            
            # Update all callbacks with new time data
            for callback in self.on_time_update_callbacks:
                try:
                    callback(self.time_context)
                except Exception as e:
                    logger.error(f"Error in time update callback: {e}")
                    
            logger.debug(f"Time context updated: {self.time_context['summary'] if 'summary' in self.time_context else 'No summary available'}")
        except Exception as e:
            logger.error(f"Failed to update time context: {e}")
    
    def get_current_time_context(self) -> Dict[str, Any]:
        """
        Get the current time context.
        
        Returns:
            Dictionary containing current time information
        """
        return self.time_context.copy()
        
    async def update_coordinates(self, lat: float, lon: float):
        """
        Update the location coordinates and refresh time information.
        
        Args:
            lat: New latitude coordinate
            lon: New longitude coordinate
        """
        self.default_lat = lat
        self.default_lon = lon
        await self._update_time_context()

async def get_time(lat=28.5383, lon=-81.3792, format="detailed"):
    """
    Get current time and date information for a specific location.
    
    Args:
        lat: Latitude coordinate
        lon: Longitude coordinate
        format: Response format - "detailed" for all info, "basic" for just current time
        
    Returns:
        Dictionary containing time information
    """
    try:
        tf = TimezoneFinder()
        tz_name = tf.timezone_at(lat=lat, lng=lon)
        if not tz_name:
            raise ValueError("Time zone could not be determined for the given coordinates.")
        
        local_tz = pytz.timezone(tz_name)
        local_datetime = datetime.now(local_tz)
        
        # Basic time information
        current_time = local_datetime.strftime("%H:%M:%S")
        current_date = local_datetime.strftime("%Y-%m-%d")
        day_of_week = local_datetime.strftime("%A")
        month_name = local_datetime.strftime("%B")
        year = local_datetime.strftime("%Y")
        
        # Create response
        result = {
            "current": {
                "time": current_time,
                "date": current_date,
                "day_of_week": day_of_week,
                "month": month_name,
                "year": year,
            "timezone": tz_name
            },
            "summary": f"It is {current_time} on {day_of_week}, {month_name} {local_datetime.day}, {year} in timezone {tz_name}."
        }
        
        # Return the response based on the requested format
        if format.lower() == "basic":
            return {
                "time": current_time,
                "date": current_date,
                "summary": result["summary"]
            }
        
        return result
        
    except Exception as e:
        logger.error(f"Error in get_time: {e}")
        return {"error": f"An error occurred: {str(e)}"}


def get_schema():
    """
    Return the schema definitions for time-related functions.
    """
    return {
        "type": "function",
        "function": {
            "name": "get_time",
            "description": "Get current time and date information for a specific location. Use this for any time-related queries.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lat": {
                        "type": "number",
                        "description": "Latitude coordinate of the location (default: Orlando, FL)"
                    },
                    "lon": {
                        "type": "number",
                        "description": "Longitude coordinate of the location (default: Orlando, FL)"
                    },
                    "format": {
                        "type": "string",
                        "enum": ["detailed", "basic"],
                        "description": "Response format - detailed for all info, basic for just current time"
                    }
                },
                "required": []
            }
        }
    } 