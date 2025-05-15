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
import asyncio
from datetime import datetime, timezone
from dotenv import load_dotenv
from backend.weather.fetcher import get_http_client

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
        # Get the shared client with appropriate timeout
        client = await get_http_client(timeout=12.0)
        
        # Create the tasks for concurrent execution
        onecall_task = client.get(onecall_url, params=params)
        overview_task = client.get(overview_url, params=params)
        
        logger.debug(f"Requesting OneCall URL: {onecall_url} with params: {params}")
        logger.debug(f"Requesting Overview URL: {overview_url} with params: {params}")
        logger.info(f"Fetching OpenWeatherMap data concurrently for lat={lat}, lon={lon}")
        
        # Use wait_for to ensure we have a timeout for the gather operation
        responses = await asyncio.wait_for(
            asyncio.gather(
                onecall_task, 
                overview_task,
                return_exceptions=True
            ),
            timeout=15.0  # Overall timeout for both API calls
        )
        
        # Check for exceptions
        for i, resp in enumerate(responses):
            if isinstance(resp, Exception):
                logger.error(f"Error in OpenWeatherMap request {i}: {resp}")
                # Don't return None immediately, try to use partial data if possible
        
        # Process responses
        onecall_response, overview_response = responses
        
        # Parse JSON data from valid responses
        onecall_data = {}
        overview_data = {}
        
        # Only process valid responses
        if not isinstance(onecall_response, Exception):
            try:
                onecall_response.raise_for_status()
                onecall_data = onecall_response.json()
                logger.debug("Successfully parsed OneCall response")
            except (httpx.HTTPStatusError, ValueError) as e:
                logger.error(f"Error processing OneCall response: {e}")
                
        if not isinstance(overview_response, Exception):
            try:
                overview_response.raise_for_status()
                overview_data = overview_response.json()
                logger.debug("Successfully parsed Overview response")
            except (httpx.HTTPStatusError, ValueError) as e:
                logger.error(f"Error processing Overview response: {e}")
        
        # Extract required data - handle missing fields safely
        current = onecall_data.get("current", {})
        minutely = onecall_data.get("minutely", [])
        weather_overview = overview_data.get("weather_overview", "No weather overview available.")
        
        # Return the combined data - return partial data even if some calls failed
        combined_data = {
            "current": current,
            "minutely": minutely,
            "weather_overview": weather_overview
        }
        
        # If we have no useful data, log a warning
        if not current and not weather_overview:
            logger.warning("Both OpenWeatherMap API calls failed, returning minimal data")
            
        logger.info("Successfully fetched OpenWeatherMap data")
        return combined_data
            
    except asyncio.TimeoutError:
        logger.error("Timeout fetching OpenWeatherMap data")
    except httpx.RequestError as exc:
        logger.error(f"Request error fetching OpenWeatherMap data: {exc}")
    except httpx.HTTPStatusError as exc:
        logger.error(f"HTTP error response {exc.response.status_code} from OpenWeatherMap API")
    except Exception as exc:
        logger.error(f"Unexpected error fetching OpenWeatherMap data: {exc}")

    return None 