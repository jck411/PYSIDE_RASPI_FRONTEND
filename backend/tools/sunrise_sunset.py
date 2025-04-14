import os
import logging
from dotenv import load_dotenv

# Import existing fetcher function instead of duplicating code
from backend.weather.fetcher import fetch_sunrise_sunset

logger = logging.getLogger(__name__)

load_dotenv()

# Default coordinates (Winter Park, FL)
DEFAULT_LAT = os.getenv("DEFAULT_LAT", "28.5988")
DEFAULT_LON = os.getenv("DEFAULT_LON", "-81.3583")

async def get_sunrise_sunset(lat=DEFAULT_LAT, lon=DEFAULT_LON):
    """
    Get sunrise and sunset times for a specific location based on coordinates.
    Uses the sunrise-sunset.org API.
    
    Args:
        lat: Latitude coordinate as a string or number
        lon: Longitude coordinate as a string or number
        
    Returns:
        Dictionary containing sunrise and sunset times in ISO 8601 format, or
        an error message if the API request fails.
    """
    try:
        # Convert numbers to strings if needed
        lat_str = str(lat) if not isinstance(lat, str) else lat
        lon_str = str(lon) if not isinstance(lon, str) else lon
        
        # Call the existing fetch_sunrise_sunset function
        result = await fetch_sunrise_sunset(lat_str, lon_str)
        
        if result:
            return {
                "sunrise": result["sunrise"],
                "sunset": result["sunset"],
                "status": "success"
            }
        else:
            return {
                "error": "Failed to fetch sunrise/sunset data",
                "status": "error"
            }
    except Exception as e:
        logger.error(f"Error in get_sunrise_sunset: {e}")
        return {
            "error": f"An error occurred: {str(e)}",
            "status": "error"
        }

def get_schema():
    """
    Return the schema definition for the get_sunrise_sunset function.
    """
    return {
        "type": "function",
        "function": {
            "name": "get_sunrise_sunset",
            "description": "Get sunrise and sunset times for a specific location",
            "strict": True,
            "parameters": {
                "type": "object",
                "properties": {
                    "lat": {"type": "string", "description": "Latitude coordinate of the location"},
                    "lon": {"type": "string", "description": "Longitude coordinate of the location"}
                },
                "required": ["lat", "lon"],
                "additionalProperties": False
            }
        }
    } 