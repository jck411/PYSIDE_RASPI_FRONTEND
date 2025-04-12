#!/usr/bin/env python3
import httpx
import os
import logging
from dotenv import load_dotenv
import asyncio

# Load environment variables from .env file, if present.
load_dotenv()

# Default to Winter Park, FL (for forecasts)
DEFAULT_LAT = os.getenv("DEFAULT_LAT", "28.5988")
DEFAULT_LON = os.getenv("DEFAULT_LON", "-81.3583")

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def fetch_weather_data(lat: str = DEFAULT_LAT, lon: str = DEFAULT_LON) -> dict | None:
    """
    Fetches weather data from the National Weather Service API asynchronously.
    
    The following API calls are made:
      1. Get point metadata (includes URLs for forecast, forecastHourly, forecastGridData, observationStations)
      2. Get the narrative forecast (from the forecast URL)
      3. Get the hourly forecast (from the forecastHourly URL)
      4. Get the grid forecast (from the forecastGridData URL)
      5. Get the list of observation stations and then the latest observation
         from the first station.
    
    Returns:
        A dictionary with keys:
          - "observations": current observation data
          - "forecast_narrative": narrative forecast data
          - "forecast_hourly": hourly forecast data
          - "grid_forecast": detailed grid forecast data
        or None if an error occurs.
    """
    base_url = "https://api.weather.gov"
    headers = {
        "User-Agent": "RaspberryPi-WeatherApp/1.0 (pyside-weather-app)",
        "Accept": "application/json",
    }

    try:
        # 1. Get point metadata
        points_url = f"{base_url}/points/{lat},{lon}"
        logger.info(f"Fetching gridpoints for lat={lat}, lon={lon} from {points_url}")

        async with httpx.AsyncClient() as client:
            points_response = await client.get(points_url, headers=headers)
            points_response.raise_for_status()
            points_data = points_response.json()

            properties = points_data.get("properties", {})
            forecast_url         = properties.get("forecast")
            forecast_hourly_url  = properties.get("forecastHourly")
            grid_forecast_url    = properties.get("forecastGridData")
            observation_stations = properties.get("observationStations")

            if not (forecast_url and forecast_hourly_url and grid_forecast_url and observation_stations):
                logger.error("One or more required URLs not found in the points response")
                return None

            # 2. Get narrative forecast data
            logger.info(f"Fetching narrative forecast from {forecast_url}")
            forecast_response = await client.get(forecast_url, headers=headers)
            forecast_response.raise_for_status()
            forecast_data = forecast_response.json()

            # 3. Get hourly forecast data
            logger.info(f"Fetching hourly forecast from {forecast_hourly_url}")
            forecast_hourly_response = await client.get(forecast_hourly_url, headers=headers)
            forecast_hourly_response.raise_for_status()
            forecast_hourly_data = forecast_hourly_response.json()

            # 4. Get detailed grid forecast data
            logger.info(f"Fetching grid forecast from {grid_forecast_url}")
            grid_forecast_response = await client.get(grid_forecast_url, headers=headers)
            grid_forecast_response.raise_for_status()
            grid_forecast_data = grid_forecast_response.json()

            # 5. Get observation stations and then the latest observation
            logger.info(f"Fetching observation stations from {observation_stations}")
            stations_response = await client.get(observation_stations, headers=headers)
            stations_response.raise_for_status()
            stations_data = stations_response.json()

            features = stations_data.get("features", [])
            if not features:
                logger.error("No observation stations found")
                return None

            # Use the first station available
            station = features[0]
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

            # Combine data from all endpoints
            combined_data = {
                "observations": obs_data.get("properties", {}),
                "forecast_narrative": forecast_data,
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


if __name__ == "__main__":
    from datetime import datetime

    def print_observations(obs):
        print("\n🟢 Current Observation")
        print("------------------------")
        print(f"Time:        {obs.get('timestamp', 'N/A')}")
        print(f"Description: {obs.get('textDescription', 'N/A')}")
        temp_c = obs.get('temperature', {}).get('value')
        if temp_c is not None:
            temp_f = temp_c * 9 / 5 + 32
            print(f"Temperature: {temp_c:.1f} °C / {temp_f:.1f} °F")
        else:
            print("Temperature: N/A")
        wind = obs.get('windSpeed', {}).get('value')
        if wind is not None:
            print(f"Wind Speed:  {wind:.1f} m/s")
        else:
            print("Wind Speed:  N/A")

    def print_narrative(forecast):
        print("\n🌤️ Narrative Forecast")
        print("------------------------")
        periods = forecast.get("properties", {}).get("periods", [])
        for p in periods[:5]:  # just show next 5 periods
            print(f"{p['name']}: {p['detailedForecast']}")

    def print_hourly(hourly):
        print("\n🕐 Hourly Forecast (Next 24 Hours)")
        print("-------------------------------------------------------------")
        print(f"{'Time':<20} {'Temp':<8} {'Forecast'}")
        print("-------------------------------------------------------------")
        periods = hourly.get("properties", {}).get("periods", [])[:24]
        for p in periods:
            time_str = p.get("startTime", "").replace("Z", "+00:00")
            time_fmt = datetime.fromisoformat(time_str).strftime("%m-%d %H:%M")
            temp = f"{p['temperature']}{p['temperatureUnit']}"
            forecast = p.get("shortForecast", "")
            print(f"{time_fmt:<20} {temp:<8} {forecast}")
        print("-------------------------------------------------------------")

    def print_grid(grid):
        print("\n📊 Grid Forecast (Next 24 Hours)")
        print("--------------------------------------------------------------------------")
        print(f"{'Time':<20} {'POP%':<6} {'QPF(mm)':<10} {'SkyCover%':<12} {'Humidity%':<10}")
        print("--------------------------------------------------------------------------")
        props = grid.get("properties", {})
        vals = {
            "pop": props.get("probabilityOfPrecipitation", {}).get("values", []),
            "qpf": props.get("quantitativePrecipitation", {}).get("values", []),
            "sky": props.get("skyCover", {}).get("values", []),
            "rh":  props.get("relativeHumidity", {}).get("values", []),
        }
        for i in range(min(24, *map(len, vals.values()))):
            time_str = vals["pop"][i]["validTime"].split("/")[0].replace("Z", "+00:00")
            time_fmt = datetime.fromisoformat(time_str).strftime("%m-%d %H:%M")
            row = [
                str(vals["pop"][i].get("value", "N/A")).rjust(5),
                str(vals["qpf"][i].get("value", "N/A")).rjust(9),
                str(vals["sky"][i].get("value", "N/A")).rjust(11),
                str(vals["rh"][i].get("value", "N/A")).rjust(9),
            ]
            print(f"{time_fmt:<20} {' '.join(row)}")
        print("--------------------------------------------------------------------------")

    import asyncio

    async def main():
        data = await fetch_weather_data()
        if data:
            print_observations(data.get("observations"))
            print_narrative(data.get("forecast_narrative"))
            print_hourly(data.get("forecast_hourly"))
            print_grid(data.get("grid_forecast"))
        else:
            print("❌ Failed to fetch weather data.")

    asyncio.run(main())