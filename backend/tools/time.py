from datetime import datetime
import pytz
from timezonefinder import TimezoneFinder
import logging

logger = logging.getLogger(__name__)

async def get_time(lat=28.5383, lon=-81.3792):
    """
    Get the current time and date for a specific location based on coordinates.
    
    Args:
        lat: Latitude coordinate
        lon: Longitude coordinate
        
    Returns:
        Dictionary containing the current time information
    """
    try:
        tf = TimezoneFinder()
        tz_name = tf.timezone_at(lat=lat, lng=lon)
        if not tz_name:
            raise ValueError("Time zone could not be determined for the given coordinates.")
        
        local_tz = pytz.timezone(tz_name)
        local_datetime = datetime.now(local_tz)
        
        # Return a dictionary with time information
        return {
            "time": local_datetime.strftime("%H:%M:%S"),
            "date": local_datetime.strftime("%Y-%m-%d"),
            "day_of_week": local_datetime.strftime("%A"),
            "month": local_datetime.strftime("%B"),
            "timezone": tz_name
        }
    except Exception as e:
        logger.error(f"Error in get_time: {e}")
        return {"error": f"An error occurred: {str(e)}"}


def get_schema():
    """
    Return the schema definition for the get_time function.
    """
    return {
        "type": "function",
        "function": {
            "name": "get_time",
            "description": "Get the current time and date based on location coordinates",
            "strict": True,
            "parameters": {
                "type": "object",
                "required": ["lat", "lon"],
                "properties": {
                    "lat": {"type": "number", "description": "Latitude coordinate of the location"},
                    "lon": {"type": "number", "description": "Longitude coordinate of the location"},
                },
                "additionalProperties": False,
            },
        },
    } 