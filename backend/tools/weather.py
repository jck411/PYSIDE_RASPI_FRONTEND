import os
import requests
import httpx
import asyncio
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

load_dotenv()

# Default coordinates (Winter Park, FL)
DEFAULT_LAT = os.getenv("DEFAULT_LAT", "28.5988")
DEFAULT_LON = os.getenv("DEFAULT_LON", "-81.3583")

async def fetch_nws_data(lat, lon):
    """
    Fetch weather forecast data from National Weather Service API.
    
    Args:
        lat: Latitude coordinates
        lon: Longitude coordinates
        
    Returns:
        Weather forecast data from NWS API
    """
    base_url = "https://api.weather.gov"
    headers = {
        "User-Agent": "RaspberryPi-WeatherApp/1.0 (pyside-weather-app)",
        "Accept": "application/json",
    }
    timeout = 10.0
    
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            # First, get the grid point information
            points_url = f"{base_url}/points/{lat},{lon}"
            logger.info(f"Fetching gridpoints for lat={lat}, lon={lon} from {points_url}")
            
            points_response = await client.get(points_url, headers=headers)
            points_response.raise_for_status()
            points_data = points_response.json()

            # Extract URLs for all needed forecast endpoints
            properties = points_data.get("properties", {})
            forecast_url = properties.get("forecast")
            forecast_hourly_url = properties.get("forecastHourly")
            grid_forecast_url = properties.get("forecastGridData")
            
            # Validate all required URLs are present
            if not all([forecast_url, forecast_hourly_url, grid_forecast_url]):
                logger.error("One or more required URLs not found in points response")
                return None

            # Fetch forecast data concurrently
            forecast_task = client.get(forecast_url, headers=headers)
            forecast_hourly_task = client.get(forecast_hourly_url, headers=headers)
            grid_forecast_task = client.get(grid_forecast_url, headers=headers)
            
            # Wait for all to complete
            responses = await asyncio.gather(
                forecast_task,
                forecast_hourly_task,
                grid_forecast_task,
                return_exceptions=True
            )
            
            # Check for exceptions
            for i, resp in enumerate(responses):
                if isinstance(resp, Exception):
                    logger.error(f"Error in concurrent request {i}: {resp}")
                    return None
            
            # Process responses
            forecast_response, forecast_hourly_response, grid_forecast_response = responses
            
            # Validate responses
            for resp in [forecast_response, forecast_hourly_response, grid_forecast_response]:
                resp.raise_for_status()
            
            # Parse JSON data
            forecast_data = forecast_response.json()
            forecast_hourly_data = forecast_hourly_response.json()
            grid_forecast_data = grid_forecast_response.json()

            # Return the combined forecast data
            combined_data = {
                "forecast": forecast_data,
                "forecast_hourly": forecast_hourly_data,
                "grid_forecast": grid_forecast_data,
                "source": "NWS"
            }
            logger.info(f"Successfully fetched NWS forecast data for lat={lat}, lon={lon}")

            return combined_data

    except Exception as e:
        logger.error(f"Error fetching NWS data: {e}")
        return None

def fetch_ow_current(lat, lon, units, lang):
    """
    Fetch current weather data from OpenWeatherMap API.
    
    Args:
        lat: Latitude coordinates
        lon: Longitude coordinates
        units: Units of measurement (metric, imperial, standard)
        lang: Language for the response
        
    Returns:
        Current weather data from OpenWeatherMap API
    """
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        raise ValueError(
            "API key not found. Please set OPENWEATHER_API_KEY in your .env file."
        )
    
    # For current weather only
    url = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&appid={api_key}&units={units}&lang={lang}&exclude=minutely,hourly,daily,alerts"
    
    try:
        response = requests.get(url, timeout=10.0)
        response.raise_for_status()
        data = response.json()
        data["source"] = "OpenWeatherMap"
        return data
    except Exception as e:
        logger.error(f"Error fetching OpenWeatherMap data: {e}")
        return None

async def fetch_weather(
    lat=DEFAULT_LAT, 
    lon=DEFAULT_LON, 
    data_type="current", 
    units="imperial", 
    lang="en"
):
    """
    Fetch weather data based on the requested type.
    Uses OpenWeatherMap for current weather and NWS for forecasts.
    
    Args:
        lat: Latitude coordinates
        lon: Longitude coordinates
        data_type: Type of weather data to fetch ("current", "forecast", or "both")
        units: Units of measurement (metric, imperial, standard)
        lang: Language for the response
        
    Returns:
        Weather data from the appropriate API(s)
    """
    result = {}
    
    if data_type in ["current", "both"]:
        # Use OpenWeatherMap for current weather
        current_data = fetch_ow_current(lat, lon, units, lang)
        if current_data:
            result["current"] = current_data
    
    if data_type in ["forecast", "both"]:
        # Use NWS for forecast data (async)
        forecast_data = await fetch_nws_data(lat, lon)
        if forecast_data:
            result["forecast"] = forecast_data
    
    if not result:
        return {"error": "Failed to fetch weather data from any source."}
    
    return result


def get_schema():
    """
    Return the schema definition for the fetch_weather function.
    """
    return {
        "type": "function",
        "function": {
            "name": "fetch_weather",
            "description": "Fetch weather data from OpenWeatherMap (current) or National Weather Service (forecasts)",
            "strict": True,
            "parameters": {
                "type": "object",
                "required": ["lat", "lon", "data_type", "units", "lang"],
                "properties": {
                    "lat": {"type": "number", "description": "Latitude coordinate of the location"},
                    "lon": {"type": "number", "description": "Longitude coordinate of the location"},
                    "data_type": {
                        "type": "string", 
                        "description": "Type of weather data to fetch: 'current' for current conditions (OpenWeatherMap), 'forecast' for forecasts (NWS), or 'both' for all data",
                        "enum": ["current", "forecast", "both"]
                    },
                    "units": {
                        "type": "string",
                        "description": "Units of measurement: metric (Celsius), imperial (Fahrenheit), standard (Kelvin)",
                        "enum": ["metric", "imperial", "standard"]
                    },
                    "lang": {
                        "type": "string",
                        "description": "Language for the response (e.g., en, es, fr)",
                    },
                },
                "additionalProperties": False,
            },
        },
    } 