#!/usr/bin/env python3
"""
OpenWeatherMap API Fetcher

Fetches current weather + minutely forecast (1 API call),
and human-readable overview (1 API call) from OpenWeather One Call 3.0.

Total: 2 API calls per fetch.
"""

import os
import logging
import httpx
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get API key
API_KEY = os.getenv("OPENWEATHER_API_KEY")
if not API_KEY:
    logging.error("OPENWEATHER_API_KEY not found in environment variables")

# Winter Park coordinates (default)
DEFAULT_LAT = os.getenv("DEFAULT_LAT", "28.5988")
DEFAULT_LON = os.getenv("DEFAULT_LON", "-81.3583")

logger = logging.getLogger(__name__)

async def fetch_openweather_data(lat: str = DEFAULT_LAT, lon: str = DEFAULT_LON) -> dict | None:
    """
    Fetches weather data from OpenWeatherMap API using One Call 3.0.
    Makes two API calls:
    1. Current weather + minutely rain forecast
    2. Human-readable weather overview
    
    Args:
        lat: Latitude for the weather location
        lon: Longitude for the weather location
        
    Returns:
        A dictionary containing the weather data, or None if an error occurs.
        The dictionary includes:
          - "current": current weather data
          - "minutely": minute-by-minute rain forecast (if available)
          - "weather_overview": human-readable weather summary
    """
    if not API_KEY:
        logger.error("OPENWEATHER_API_KEY not set in environment variables")
        return None
        
    # Parameters for API calls
    params = {
        'lat': lat,
        'lon': lon,
        'appid': API_KEY,
        'units': 'imperial',
        'lang': 'en',
        'exclude': 'hourly,daily,alerts'  # keep current + minutely
    }
    
    # API endpoints
    onecall_url = "https://api.openweathermap.org/data/3.0/onecall"
    overview_url = "https://api.openweathermap.org/data/3.0/onecall/overview"
    
    try:
        # Create a single client for all requests with timeout
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Use asyncio.gather to make both API calls concurrently
            import asyncio
            
            # Fetch weather data concurrently
            onecall_task = client.get(onecall_url, params=params)
            overview_task = client.get(overview_url, params=params)
            
            logger.info(f"Fetching OpenWeatherMap data concurrently for lat={lat}, lon={lon}")
            responses = await asyncio.gather(
                onecall_task, 
                overview_task,
                return_exceptions=True
            )
            
            # Check for exceptions
            for i, resp in enumerate(responses):
                if isinstance(resp, Exception):
                    logger.error(f"Error in OpenWeatherMap request {i}: {resp}")
                    return None
            
            # Process responses
            onecall_response, overview_response = responses
            
            # Validate responses
            for resp in [onecall_response, overview_response]:
                resp.raise_for_status()
            
            # Parse JSON data
            onecall_data = onecall_response.json()
            overview_data = overview_response.json()
            
            # Extract required data
            current = onecall_data.get("current", {})
            minutely = onecall_data.get("minutely", [])
            weather_overview = overview_data.get("weather_overview", "No weather overview available.")
            
            # Return the combined data
            combined_data = {
                "current": current,
                "minutely": minutely,
                "weather_overview": weather_overview
            }
            
            logger.info("Successfully fetched OpenWeatherMap data")
            return combined_data
            
    except httpx.RequestError as exc:
        logger.error(f"An error occurred while requesting {exc.request.url!r}: {exc}")
    except httpx.HTTPStatusError as exc:
        logger.error(
            f"Error response {exc.response.status_code} while requesting {exc.request.url!r}: {exc.response.text}"
        )
    except Exception as exc:
        logger.error(f"An unexpected error occurred: {exc}")

    return None 