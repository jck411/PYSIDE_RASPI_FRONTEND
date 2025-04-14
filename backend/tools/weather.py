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
                resp.raise_for_status() # type: ignore
            
            # Parse JSON data
            forecast_data = forecast_response.json() # type: ignore
            forecast_hourly_data = forecast_hourly_response.json() # type: ignore
            grid_forecast_data = grid_forecast_response.json() # type: ignore

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

async def fetch_ow_current(lat, lon, units, lang):
    """
    Fetch current weather data from OpenWeatherMap API asynchronously.

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
        logger.error("OpenWeatherMap API key not found.")
        return None # Return None instead of raising ValueError in async context

    # For current weather only
    url = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&appid={api_key}&units={units}&lang={lang}&exclude=minutely,hourly,daily,alerts"
    headers = {"Accept": "application/json"}
    timeout = 10.0

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            logger.info(f"Fetching OpenWeatherMap current data for lat={lat}, lon={lon} from {url}")
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            data["source"] = "OpenWeatherMap"
            logger.info(f"Successfully fetched OpenWeatherMap current data for lat={lat}, lon={lon}")
            return data
    except Exception as e:
        logger.error(f"Error fetching OpenWeatherMap data: {e}")
        return None

async def fetch_weather(
    lat=DEFAULT_LAT, 
    lon=DEFAULT_LON, 
    data_type="current", 
    units="imperial",
    lang="en",
    detail_level="simple" # New parameter
):
    """
    Fetch weather data based on the requested type.
    Uses OpenWeatherMap for current weather and NWS for forecasts.
    
    Args:
        lat: Latitude coordinates
        lon: Longitude coordinates
        data_type: Type of weather data to fetch ("current", "forecast", or "both").
        units: Units of measurement (metric, imperial, standard).
        lang: Language for the response.
        detail_level: Level of detail required ("simple" or "detailed"). Default is "simple".
        
    Returns:
        Weather data from the appropriate API(s)
    """
    result = {}
    
    tasks = []
    fetch_current = data_type in ["current", "both"]
    fetch_forecast = data_type in ["forecast", "both"]

    if fetch_current:
        # Use OpenWeatherMap for current weather (now async)
        tasks.append(fetch_ow_current(lat, lon, units, lang))
        
    if fetch_forecast:
        # Use NWS for forecast data (already async)
        tasks.append(fetch_nws_data(lat, lon))

    if tasks:
        # Run fetches concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        current_data = None
        forecast_data = None
        
        task_index = 0
        if fetch_current:
            if isinstance(results[task_index], Exception):
                logger.error(f"Error fetching current weather: {results[task_index]}")
            else:
                current_data = results[task_index]
            task_index += 1
            
        if fetch_forecast:
            if isinstance(results[task_index], Exception):
                 logger.error(f"Error fetching forecast weather: {results[task_index]}")
            else:
                forecast_data = results[task_index]

        # Process current data based on detail_level
        if current_data and isinstance(current_data, dict): # Explicit check for Pylance
            current_processed = {}
            ow_current = current_data.get("current", {}) # Data is nested under 'current' key from fetch_ow_current
            if ow_current:
                current_processed["description"] = ow_current.get("weather", [{}])[0].get("description", "N/A")
                current_processed["temp"] = ow_current.get("temp", "N/A")
                current_processed["feels_like"] = ow_current.get("feels_like", "N/A")
                current_processed["source"] = current_data.get("source", "OpenWeatherMap") # Keep source

                if detail_level == "detailed":
                    current_processed["humidity"] = ow_current.get("humidity", "N/A")
                    current_processed["pressure"] = ow_current.get("pressure", "N/A")
                    current_processed["wind_speed"] = ow_current.get("wind_speed", "N/A")
                    current_processed["wind_deg"] = ow_current.get("wind_deg", "N/A")
                    current_processed["visibility"] = ow_current.get("visibility", "N/A")
                    current_processed["uvi"] = ow_current.get("uvi", "N/A")
                    # Add sunrise/sunset if needed, converting from timestamp
                    # sunrise_ts = ow_current.get("sunrise")
                    # sunset_ts = ow_current.get("sunset")

            result["current"] = current_processed if current_processed else {"error": "Could not process current weather data."}


        # Process forecast data based on detail_level
        if forecast_data and isinstance(forecast_data, dict): # Explicit check for Pylance
            forecast_processed = {}
            try:
                # Prioritize the narrative forecast periods
                periods = forecast_data.get("forecast", {}).get("properties", {}).get("periods", [])
                if periods:
                    num_periods = 4 if detail_level == "simple" else 14 # Simple: ~2 days, Detailed: ~7 days
                    forecast_processed["periods"] = periods[:num_periods]
                    forecast_processed["source"] = forecast_data.get("source", "NWS") # Keep source
                    forecast_processed["generated_at"] = forecast_data.get("forecast", {}).get("properties", {}).get("generatedAt")
                    forecast_processed["elevation"] = forecast_data.get("forecast", {}).get("properties", {}).get("elevation")

                else:
                     forecast_processed = {"error": "No forecast periods found in NWS data."}

            except Exception as e:
                logger.error(f"Error processing NWS forecast data: {e}")
                forecast_processed = {"error": f"Error processing forecast data: {e}"}

            result["forecast"] = forecast_processed

    if not result:
        return {"error": "Failed to fetch or process weather data from any source."}
    
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
                "required": ["lat", "lon", "data_type", "units", "lang", "detail_level"],
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
                        "description": "Language for the response (e.g., en, es, fr). Default is 'en'.",
                    },
                    "detail_level": {
                        "type": "string",
                        "description": "Level of detail required: 'simple' for a brief summary, 'detailed' for more information. Default is 'simple'.",
                        "enum": ["simple", "detailed"],
                    }
                },
                "additionalProperties": False
            },
        },
    } 