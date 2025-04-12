import httpx
import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Default to Winter Park, FL
DEFAULT_LAT = os.getenv("DEFAULT_LAT", "28.5988")
DEFAULT_LON = os.getenv("DEFAULT_LON", "-81.3583")

logger = logging.getLogger(__name__)


async def fetch_weather_data(
    lat: str = DEFAULT_LAT, lon: str = DEFAULT_LON
) -> dict | None:
    """
    Fetches weather data from National Weather Service API.

    Args:
        lat: Latitude for the weather location.
        lon: Longitude for the weather location.

    Returns:
        A dictionary containing the weather data, or None if an error occurs.
        The dictionary includes:
          - "properties": current observation data
          - "forecast": narrative forecast data
          - "forecast_hourly": hourly forecast data
          - "grid_forecast": detailed grid forecast data
    """
    base_url = "https://api.weather.gov"
    headers = {
        "User-Agent": "RaspberryPi-WeatherApp/1.0 (pyside-weather-app)",
        "Accept": "application/json",
    }

    try:
        # First, get the grid point information
        points_url = f"{base_url}/points/{lat},{lon}"
        logger.info(f"Fetching gridpoints for lat={lat}, lon={lon} from {points_url}")

        async with httpx.AsyncClient() as client:
            # Get grid points
            points_response = await client.get(points_url, headers=headers)
            points_response.raise_for_status()
            points_data = points_response.json()

            # Extract URLs for all needed endpoints
            properties = points_data.get("properties", {})
            forecast_url = properties.get("forecast")
            forecast_hourly_url = properties.get("forecastHourly")
            grid_forecast_url = properties.get("forecastGridData")
            observation_stations_url = properties.get("observationStations")

            # Validate all required URLs are present
            if not forecast_url:
                logger.error("Forecast URL not found in points response")
                return None
            if not forecast_hourly_url:
                logger.error("Hourly forecast URL not found in points response")
                return None
            if not grid_forecast_url:
                logger.error("Grid forecast URL not found in points response")
                return None
            if not observation_stations_url:
                logger.error("Observation stations URL not found in points response")
                return None

            # Get narrative forecast data
            logger.info(f"Fetching forecast from {forecast_url}")
            forecast_response = await client.get(forecast_url, headers=headers)
            forecast_response.raise_for_status()
            forecast_data = forecast_response.json()

            # Get hourly forecast data
            logger.info(f"Fetching hourly forecast from {forecast_hourly_url}")
            forecast_hourly_response = await client.get(forecast_hourly_url, headers=headers)
            forecast_hourly_response.raise_for_status()
            forecast_hourly_data = forecast_hourly_response.json()

            # Get detailed grid forecast data
            logger.info(f"Fetching grid forecast from {grid_forecast_url}")
            grid_forecast_response = await client.get(grid_forecast_url, headers=headers)
            grid_forecast_response.raise_for_status()
            grid_forecast_data = grid_forecast_response.json()

            # Get observation stations
            logger.info(
                f"Fetching observation stations from {observation_stations_url}"
            )
            stations_response = await client.get(
                observation_stations_url, headers=headers
            )
            stations_response.raise_for_status()
            stations_data = stations_response.json()

            if not stations_data.get("features") or len(stations_data["features"]) == 0:
                logger.error("No observation stations found")
                return None

            # Get the first station's observations
            station = stations_data["features"][0]
            # Try to get the station URL: check for "@id" or fallback to the "id" property
            station_url = station["properties"].get("@id") or station.get("id")
            if not station_url:
                logger.error("Station URL not found")
                return None

            observations_url = f"{station_url}/observations/latest"
            logger.info(f"Fetching latest observations from {observations_url}")
            obs_response = await client.get(observations_url, headers=headers)
            obs_response.raise_for_status()
            obs_data = obs_response.json()

            # Return the raw NWS API data for the new UI
            # Maintain backward compatibility while adding new data
            combined_data = {
                "properties": obs_data.get("properties", {}),
                "forecast": forecast_data,
                "forecast_hourly": forecast_hourly_data,
                "grid_forecast": grid_forecast_data,
            }
            logger.info(f"Successfully fetched complete weather data for lat={lat}, lon={lon}")

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
