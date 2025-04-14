import os
import logging
from dotenv import load_dotenv

# Import existing fetcher function for National Weather Service data
from backend.weather.fetcher import fetch_weather_data

logger = logging.getLogger(__name__)

load_dotenv()

# Default coordinates (Winter Park, FL)
DEFAULT_LAT = os.getenv("DEFAULT_LAT", "28.5988")
DEFAULT_LON = os.getenv("DEFAULT_LON", "-81.3583")

async def get_weather_forecast(
    lat=DEFAULT_LAT, 
    lon=DEFAULT_LON, 
    detail_level="simple"
):
    """
    Get weather forecast data for a specific location.
    Uses the National Weather Service API for forecast data.
    
    Args:
        lat: Latitude coordinate as a string or number
        lon: Longitude coordinate as a string or number
        detail_level: Level of detail required ("simple" or "detailed"). Default is "simple".
        
    Returns:
        Dictionary containing weather forecast data, or
        an error message if the API request fails.
    """
    try:
        # Convert parameters to strings if needed
        lat_str = str(lat) if not isinstance(lat, str) else lat
        lon_str = str(lon) if not isinstance(lon, str) else lon
        
        # Use existing fetcher for NWS data
        nws_data = await fetch_weather_data(lat_str, lon_str)
        
        if nws_data:
            forecast_processed = {}
            try:
                # Extract and format only what the LLM needs
                periods = nws_data.get("forecast", {}).get("properties", {}).get("periods", [])
                if periods:
                    num_periods = 4 if detail_level == "simple" else 14 # Simple: ~2 days, Detailed: ~7 days
                    forecast_processed["periods"] = periods[:num_periods]
                    forecast_processed["source"] = "NWS" # Keep source
                    
                    # Only include these for detailed level
                    if detail_level == "detailed":
                        forecast_processed["generated_at"] = nws_data.get("forecast", {}).get("properties", {}).get("generatedAt")
                        forecast_processed["elevation"] = nws_data.get("forecast", {}).get("properties", {}).get("elevation")
                else:
                    forecast_processed = {"error": "No forecast periods found in NWS data."}
            except Exception as e:
                logger.error(f"Error processing NWS forecast data: {e}")
                forecast_processed = {"error": f"Error processing forecast data: {e}"}

            return forecast_processed
        
        return {"error": "Failed to fetch forecast data"}
    
    except Exception as e:
        logger.error(f"Error in get_weather_forecast: {e}")
        return {"error": f"An error occurred: {str(e)}"}

def get_schema():
    """
    Return the schema definition for the get_weather_forecast function.
    """
    return {
        "type": "function",
        "function": {
            "name": "get_weather_forecast",
            "description": "Get weather forecast data for a specific location",
            "strict": True,
            "parameters": {
                "type": "object",
                "properties": {
                    "lat": {"type": "string", "description": "Latitude coordinate of the location"},
                    "lon": {"type": "string", "description": "Longitude coordinate of the location"},
                    "detail_level": {
                        "type": "string", 
                        "enum": ["simple", "detailed"],
                        "description": "Level of detail required ('simple' or 'detailed')"
                    }
                },
                "required": ["lat", "lon", "detail_level"],
                "additionalProperties": False
            }
        }
    } 