import httpx
import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
# Default to Winter Park, FL
DEFAULT_LAT = os.getenv("DEFAULT_LAT", "28.5988")  
DEFAULT_LON = os.getenv("DEFAULT_LON", "-81.3583")

logger = logging.getLogger(__name__)

async def fetch_weather_data(lat: str = DEFAULT_LAT, lon: str = DEFAULT_LON) -> dict | None:
    """
    Fetches weather data from OpenWeatherMap One Call API 3.0.

    Args:
        lat: Latitude for the weather location.
        lon: Longitude for the weather location.

    Returns:
        A dictionary containing the weather data, or None if an error occurs.
    """
    if not OPENWEATHER_API_KEY:
        logger.error("OpenWeatherMap API key not found in environment variables.")
        return None

    # OpenWeatherMap One Call API 3.0 endpoint
    # See: https://openweathermap.org/api/one-call-3
    url = f"https://api.openweathermap.org/data/3.0/onecall"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": OPENWEATHER_API_KEY,
        "units": "imperial",  # Use Fahrenheit
        # You can exclude parts of the data if not needed, e.g., exclude=minutely,hourly
        # "exclude": "minutely,alerts" 
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
            data = response.json()
            logger.info(f"Successfully fetched weather data for lat={lat}, lon={lon}")
            return data
    except httpx.RequestError as exc:
        logger.error(f"An error occurred while requesting {exc.request.url!r}: {exc}")
    except httpx.HTTPStatusError as exc:
        logger.error(f"Error response {exc.response.status_code} while requesting {exc.request.url!r}: {exc.response.text}")
    except Exception as exc:
        logger.error(f"An unexpected error occurred: {exc}")
    
    return None

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