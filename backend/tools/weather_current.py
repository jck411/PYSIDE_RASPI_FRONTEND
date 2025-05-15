import os
import logging
from dotenv import load_dotenv

# Import existing fetcher function for OpenWeatherMap data
from backend.weather.openweather_fetcher import fetch_openweather_data

logger = logging.getLogger(__name__)

load_dotenv()

# Default coordinates (Winter Park, FL)
DEFAULT_LAT = os.getenv("DEFAULT_LAT", "28.5988")
DEFAULT_LON = os.getenv("DEFAULT_LON", "-81.3583")

async def get_weather_current(
    lat=DEFAULT_LAT, 
    lon=DEFAULT_LON, 
    units="imperial",
    lang="en",
    detail_level="simple"
):
    """
    Get current weather conditions for a specific location.
    Uses OpenWeatherMap API for current conditions data.
    
    Args:
        lat: Latitude coordinate as a string or number
        lon: Longitude coordinate as a string or number
        units: Units of measurement (metric, imperial, standard)
        lang: Language for the response
        detail_level: Level of detail required ("simple" or "detailed")
        
    Returns:
        Dictionary containing current weather data, or
        an error message if the API request fails.
    """
    try:
        # Convert parameters to strings if needed
        lat_str = str(lat) if not isinstance(lat, str) else lat
        lon_str = str(lon) if not isinstance(lon, str) else lon
        
        # Use existing fetcher for OpenWeatherMap data
        ow_data = await fetch_openweather_data(lat_str, lon_str)
        
        if ow_data:
            current_processed = {}
            current = ow_data.get("current", {})
            
            if current:
                # Basic info for all detail levels
                try:
                    current_processed["description"] = current.get("weather", [{}])[0].get("description", "N/A")
                    current_processed["temp"] = current.get("temp", "N/A")
                    current_processed["feels_like"] = current.get("feels_like", "N/A")
                    current_processed["source"] = "OpenWeatherMap"
                    
                    # Additional data for detailed level
                    if detail_level == "detailed":
                        current_processed["humidity"] = current.get("humidity", "N/A")
                        current_processed["pressure"] = current.get("pressure", "N/A")
                        current_processed["wind_speed"] = current.get("wind_speed", "N/A")
                        current_processed["wind_deg"] = current.get("wind_deg", "N/A")
                        current_processed["weather_overview"] = ow_data.get("weather_overview", "N/A")
                except Exception as e:
                    logger.error(f"Error processing OpenWeatherMap current data: {e}")
                    current_processed = {"error": f"Error processing current weather data: {e}"}
            
            # Return the processed current weather data
            return current_processed or {"error": "Could not process current weather data."}
        
        return {"error": "Failed to fetch current weather data"}
    
    except Exception as e:
        logger.error(f"Error in get_weather_current: {e}")
        return {"error": f"An error occurred: {str(e)}"}

def get_schema():
    """
    Return the schema definition for the get_weather_current function.
    """
    return {
        "type": "function",
        "function": {
            "name": "get_weather_current",
            "description": "Get current weather conditions for a specific location",
            "strict": True,
            "parameters": {
                "type": "object",
                "properties": {
                    "lat": {"type": "string", "description": "Latitude coordinate of the location"},
                    "lon": {"type": "string", "description": "Longitude coordinate of the location"},
                    "units": {
                        "type": "string", 
                        "enum": ["metric", "imperial", "standard"],
                        "description": "Units of measurement (metric, imperial, standard)"
                    },
                    "lang": {
                        "type": "string", 
                        "description": "Language for the response"
                    },
                    "detail_level": {
                        "type": "string", 
                        "enum": ["simple", "detailed"],
                        "description": "Level of detail required ('simple' or 'detailed')"
                    }
                },
                "required": ["lat", "lon", "units", "lang", "detail_level"],
                "additionalProperties": False
            },
            # Dependency metadata
            "dependencies": [],  # Current weather doesn't depend on other tools
            "provides": ["current_weather"],  # Provides current weather data
            "parallel_safe": True  # Can be run in parallel with other operations
        }
    } 