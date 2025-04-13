from datetime import datetime
import pytz
from timezonefinder import TimezoneFinder


def get_time(lat=28.5383, lon=-81.3792):
    """
    Get the current time for a specific location based on coordinates.
    
    Args:
        lat: Latitude coordinate
        lon: Longitude coordinate
        
    Returns:
        Current time string in the format HH:MM:SS
    """
    tf = TimezoneFinder()
    tz_name = tf.timezone_at(lat=lat, lng=lon)
    if not tz_name:
        raise ValueError("Time zone could not be determined for the given coordinates.")
    local_tz = pytz.timezone(tz_name)
    local_time = datetime.now(local_tz)
    return local_time.strftime("%H:%M:%S")


def get_schema():
    """
    Return the schema definition for the get_time function.
    """
    return {
        "type": "function",
        "function": {
            "name": "get_time",
            "description": "Fetch the current time based on location coordinates",
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