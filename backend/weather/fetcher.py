import httpx
import os
import logging
import asyncio
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Winter Park coordinates (for forecast data)
DEFAULT_LAT = os.getenv("DEFAULT_LAT", "28.5988")
DEFAULT_LON = os.getenv("DEFAULT_LON", "-81.3583")

# Orlando International Airport (KMCO) coordinates - used only for observations
KMCO_LAT = "28.4256"
KMCO_LON = "-81.3089"

logger = logging.getLogger(__name__)

# Global httpx client instance for connection reuse
_http_client = None

async def get_http_client(timeout=10.0):
    """
    Get or create a shared httpx client with connection pooling.
    
    Args:
        timeout: Request timeout in seconds
        
    Returns:
        An httpx AsyncClient instance
    """
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(
            timeout=timeout,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )
    return _http_client

async def close_http_client():
    """
    Close the global httpx client if it exists.
    Should be called during application shutdown.
    """
    global _http_client
    if _http_client is not None and not _http_client.is_closed:
        await _http_client.aclose()
        _http_client = None

async def fetch_sunrise_sunset(lat: str, lon: str) -> dict | None:
    """
    Fetch sunrise and sunset times for a given latitude and longitude
    using the sunrise-sunset.org API.

    Args:
        lat: Latitude as a string.
        lon: Longitude as a string.

    Returns:
        A dictionary like:
        {
            "sunrise": "2025-04-12T10:43:12+00:00",
            "sunset":  "2025-04-12T23:56:33+00:00"
        }
        Or None if the request fails.
    """
    url = "https://api.sunrise-sunset.org/json"
    params = {
        "lat": lat,
        "lng": lon,
        "formatted": 0  # Use ISO 8601 format with UTC offset
    }

    try:
        client = await get_http_client()
        response = await asyncio.wait_for(
            client.get(url, params=params),
            timeout=8.0  # Specific timeout for this operation
        )
        response.raise_for_status()
        data = response.json()

        if data["status"] == "OK":
            return {
                "sunrise": data["results"]["sunrise"],
                "sunset": data["results"]["sunset"],
            }
        else:
            logger.error(f"Sunrise-sunset API returned non-OK status: {data['status']}")
            return None

    except asyncio.TimeoutError:
        logger.error("Timeout fetching sunrise/sunset data")
    except httpx.RequestError as exc:
        logger.error(f"Request error fetching sunrise/sunset: {exc}")
    except httpx.HTTPStatusError as exc:
        logger.error(f"HTTP error fetching sunrise/sunset: {exc.response.status_code}")
    except Exception as e:
        logger.error(f"Unexpected error fetching sunrise/sunset: {e}")

    return None


async def fetch_weather_data(
    lat: str = DEFAULT_LAT, lon: str = DEFAULT_LON
) -> dict | None:
    """
    Fetches weather data from National Weather Service API.
    Uses Winter Park for forecasts but gets observations from KMCO.

    Args:
        lat: Latitude for the weather location (forecasts).
        lon: Longitude for the weather location (forecasts).

    Returns:
        A dictionary containing the weather data, or None if an error occurs.
        The dictionary includes:
          - "properties": current observation data from KMCO
          - "forecast": narrative forecast data from Winter Park
          - "forecast_hourly": hourly forecast data from Winter Park
          - "grid_forecast": detailed grid forecast data from Winter Park
          - "sunrise_sunset": sunrise and sunset data from the location
    """
    base_url = "https://api.weather.gov"
    headers = {
        "User-Agent": "RaspberryPi-WeatherApp/1.0 (pyside-weather-app)",
        "Accept": "application/json",
    }

    try:
        # Create a client with extended timeout for NWS API
        client = await get_http_client(timeout=15.0)
            
        # First, get the grid point information for Winter Park (for forecasts)
        points_url = f"{base_url}/points/{lat},{lon}"
        logger.info(f"Fetching gridpoints for Winter Park lat={lat}, lon={lon} from {points_url}")
        
        # Use explicit timeout for each request stage
        points_response = await asyncio.wait_for(
            client.get(points_url, headers=headers),
            timeout=12.0
        )
        points_response.raise_for_status()
        points_data = points_response.json()

        # Extract URLs for all needed forecast endpoints
        properties = points_data.get("properties", {})
        forecast_url = properties.get("forecast")
        forecast_hourly_url = properties.get("forecastHourly")
        grid_forecast_url = properties.get("forecastGridData")
        
        # Now get grid point information for KMCO (for observations)
        kmco_points_url = f"{base_url}/points/{KMCO_LAT},{KMCO_LON}"
        logger.info(f"Fetching gridpoints for KMCO lat={KMCO_LAT}, lon={KMCO_LON} from {kmco_points_url}")
        
        kmco_points_response = await asyncio.wait_for(
            client.get(kmco_points_url, headers=headers),
            timeout=12.0
        )
        kmco_points_response.raise_for_status()
        kmco_points_data = kmco_points_response.json()
        
        # Get observation stations URL for KMCO
        kmco_properties = kmco_points_data.get("properties", {})
        observation_stations_url = kmco_properties.get("observationStations")
        
        # Validate all required URLs are present
        if not all([forecast_url, forecast_hourly_url, grid_forecast_url, observation_stations_url]):
            logger.error("One or more required URLs not found in points responses")
            return None

        # Create tasks for concurrent fetching
        forecast_task = client.get(forecast_url, headers=headers)
        forecast_hourly_task = client.get(forecast_hourly_url, headers=headers)
        grid_forecast_task = client.get(grid_forecast_url, headers=headers)
        stations_task = client.get(observation_stations_url, headers=headers)
        
        # Also fetch sunrise/sunset data
        sunrise_sunset_task = fetch_sunrise_sunset(lat, lon)
        
        logger.info(f"Fetching all forecast data concurrently")
        
        # Use wait_for with gather to apply timeout to all concurrent tasks
        responses = await asyncio.wait_for(
            asyncio.gather(
                forecast_task,
                forecast_hourly_task,
                grid_forecast_task,
                stations_task,
                sunrise_sunset_task,
                return_exceptions=True
            ),
            timeout=20.0  # Overall timeout for all parallel requests
        )
        
        # Check for exceptions
        for i, resp in enumerate(responses):
            if isinstance(resp, Exception):
                logger.error(f"Error in concurrent request {i}: {resp}")
                # Continue with others rather than returning None immediately
        
        # Process responses
        forecast_response, forecast_hourly_response, grid_forecast_response, stations_response, sunrise_sunset_data = responses
        
        # Validate HTTP responses
        for i, resp in enumerate([forecast_response, forecast_hourly_response, grid_forecast_response, stations_response]):
            if isinstance(resp, Exception):
                logger.error(f"Request {i} failed: {resp}")
                continue  # Try to continue with other data
            
            # Only raise_for_status if not an exception
            if not isinstance(resp, Exception):
                resp.raise_for_status()
        
        # Only process data if we have valid responses
        if (isinstance(forecast_response, Exception) or
            isinstance(forecast_hourly_response, Exception) or
            isinstance(grid_forecast_response, Exception) or
            isinstance(stations_response, Exception)):
            logger.error("One or more critical weather API requests failed")
            # Continue anyway to get partial data
        
        # Parse JSON data from valid responses
        forecast_data = forecast_response.json() if not isinstance(forecast_response, Exception) else {}
        forecast_hourly_data = forecast_hourly_response.json() if not isinstance(forecast_hourly_response, Exception) else {}
        grid_forecast_data = grid_forecast_response.json() if not isinstance(grid_forecast_response, Exception) else {}
        stations_data = stations_response.json() if not isinstance(stations_response, Exception) else {}

        # Process stations data from KMCO (if available)
        if not isinstance(stations_response, Exception) and stations_data.get("features") and len(stations_data["features"]) > 0:
            # Look for KMCO station in the list or use the first one as fallback
            station = None
            for feature in stations_data["features"]:
                station_id = feature["properties"].get("stationIdentifier", "")
                if station_id == "KMCO":
                    logger.info("Found KMCO station in observation stations list")
                    station = feature
                    break
            
            # If KMCO not found, use the first station as fallback
            if not station:
                logger.info("KMCO station not found, using first available station")
                station = stations_data["features"][0]
                
            station_url = station["properties"].get("@id") or station.get("id")
            if station_url:
                station_id = station["properties"].get("stationIdentifier", "Unknown")
                logger.info(f"Using observation station: {station_id}")

                observations_url = f"{station_url}/observations/latest"
                logger.info(f"Fetching latest observations from {observations_url}")
                
                try:
                    obs_response = await asyncio.wait_for(
                        client.get(observations_url, headers=headers),
                        timeout=10.0
                    )
                    obs_response.raise_for_status()
                    obs_data = obs_response.json()
                    
                    # Return the combined data
                    combined_data = {
                        "properties": obs_data.get("properties", {}),
                        "forecast": forecast_data,
                        "forecast_hourly": forecast_hourly_data,
                        "grid_forecast": grid_forecast_data,
                        "sunrise_sunset": sunrise_sunset_data
                    }
                    logger.info(f"Successfully fetched observations from {station_id} and forecast data for Winter Park")
                    return combined_data
                    
                except (asyncio.TimeoutError, httpx.RequestError, httpx.HTTPStatusError) as e:
                    logger.error(f"Error fetching observations: {e}")
                    # Return partial data even if observations fail
                    return {
                        "properties": {},
                        "forecast": forecast_data,
                        "forecast_hourly": forecast_hourly_data,
                        "grid_forecast": grid_forecast_data,
                        "sunrise_sunset": sunrise_sunset_data
                    }

    except asyncio.TimeoutError:
        logger.error("Timeout fetching weather data")
    except httpx.RequestError as exc:
        logger.error(f"Request error fetching weather: {exc}")
    except httpx.HTTPStatusError as exc:
        logger.error(f"HTTP error fetching weather: {exc.response.status_code}")
    except Exception as exc:
        logger.error(f"Unexpected error fetching weather: {exc}")

    return None


# The following functions are kept for backward compatibility if needed
def celsius_to_fahrenheit(celsius):
    """Convert Celsius to Fahrenheit"""
    if celsius is None:
        return None
    return (celsius * 9 / 5) + 32


def convert_nws_date_to_unix(date_string):
    """Convert NWS ISO date string to Unix timestamp"""
    if not date_string:
        return None
    try:
        from datetime import datetime
        import time

        dt = datetime.fromisoformat(date_string.replace("Z", "+00:00"))
        return int(time.mktime(dt.timetuple()))
    except Exception as e:
        logger.error(f"Error converting date {date_string}: {e}")
        return int(time.time())  # Return current time as fallback


def estimate_precipitation_probability(short_forecast, detailed_forecast):
    """
    Estimate precipitation probability from forecast text
    NWS doesn't always provide direct probability values, so we need to extract from text
    """
    probability = 0.0

    # Check for percentage mentions in text
    import re

    # Look for patterns like "30 percent chance of rain" or "chance of rain 30 percent"
    percentage_matches = re.findall(
        r"(\d+)\s*percent(?:\s*chance)?", detailed_forecast.lower()
    )
    if percentage_matches:
        # Use the highest percentage found
        probability = max([float(p) / 100 for p in percentage_matches])
    else:
        # Estimate based on wording
        if "slight chance" in detailed_forecast.lower():
            probability = 0.2
        elif "chance" in detailed_forecast.lower():
            probability = 0.4
        elif "likely" in detailed_forecast.lower():
            probability = 0.7
        elif any(
            term in detailed_forecast.lower()
            for term in ["rain", "showers", "thunderstorms", "snow"]
        ):
            probability = 0.9

    return probability


# Function map_nws_icon_to_owm removed - NWS icons are used directly now


# Example usage (for testing)
# if __name__ == "__main__":
#     import asyncio
#     async def main():
#         weather_data = await fetch_weather_data()
#         if weather_data:
#             print("Current Temperature:", weather_data.get('current', {}).get('temp'))
#             # print(weather_data) # Print full response for inspection
#         else:
#             print("Failed to fetch weather data.")
#     asyncio.run(main())
