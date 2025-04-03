#!/usr/bin/env python3
import requests
import sys
import json
from datetime import datetime
from zoneinfo import ZoneInfo

# Coordinates for Winter Park, FL (ZIP 32789)
latitude = 28.598
longitude = -81.339
base_url = "https://api.weather.gov"

# Required headers: /points endpoint uses JSON-LD; others use JSON.
headers_points = {
    "User-Agent": "WeatherTerminalApp/1.0 (youremail@example.com)",
    "Accept": "application/ld+json",
}
headers_json = {
    "User-Agent": "WeatherTerminalApp/1.0 (youremail@example.com)",
    "Accept": "application/json",
}


def c_to_f(c):
    """Convert Celsius to Fahrenheit."""
    return c * 9 / 5 + 32


def mps_to_mph(mps):
    """Convert meters per second to miles per hour."""
    return mps * 2.23694


def format_time(iso_str):
    """Convert ISO-8601 time string (UTC) to local Eastern Time in a friendly format."""
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        dt_local = dt.astimezone(ZoneInfo("America/New_York"))
        return dt_local.strftime("%A, %b %d at %I:%M %p")
    except Exception:
        return iso_str


def get_points_data(lat, lon):
    """Retrieve grid point data from the NWS /points endpoint."""
    url = f"{base_url}/points/{lat},{lon}"
    response = requests.get(url, headers=headers_points)
    response.raise_for_status()
    return response.json()


def get_forecast_data(forecast_url):
    """Retrieve forecast data from the provided forecast URL."""
    response = requests.get(forecast_url, headers=headers_json)
    response.raise_for_status()
    return response.json()


def get_observation_data(stations_url):
    """Retrieve current observations from the first available observation station."""
    response = requests.get(stations_url, headers=headers_json)
    response.raise_for_status()
    stations = response.json().get("features", [])
    if not stations:
        raise Exception("No observation stations found.")
    # Use the first station from the list
    station_url = stations[0]["properties"].get("@id")
    if not station_url:
        raise Exception("No valid station URL found.")
    obs_url = f"{station_url}/observations/latest"
    obs_response = requests.get(obs_url, headers=headers_json)
    obs_response.raise_for_status()
    return obs_response.json()


def print_raw_forecast(forecast_data):
    """Print raw forecast JSON data."""
    print("\n=== Raw Forecast Data ===\n")
    print(json.dumps(forecast_data, indent=2))
    print("\n" + "=" * 50)


def print_readable_forecast(forecast_data):
    """Print a more detailed human-readable version of the forecast."""
    periods = forecast_data.get("properties", {}).get("periods", [])
    if not periods:
        print("No forecast periods available.")
        return

    # Get the current local Eastern Time for display
    current_local_time = datetime.now(ZoneInfo("America/New_York")).strftime(
        "%A, %b %d at %I:%M %p"
    )

    print("\n=== Human-Readable Forecast ===\n")
    print(f"Current Time: {current_local_time}\n")

    for period in periods:
        name = period.get("name", "N/A")
        start_time = format_time(period.get("startTime", "N/A"))
        end_time = format_time(period.get("endTime", "N/A"))
        temp = period.get("temperature", "N/A")
        temp_unit = period.get("temperatureUnit", "")
        wind_speed = period.get("windSpeed", "N/A")
        wind_dir = period.get("windDirection", "N/A")
        icon = period.get("icon", "N/A")
        short_forecast = period.get("shortForecast", "N/A")
        detailed_forecast = period.get("detailedForecast", "N/A")

        print(f"Period: {name}")
        print(f"  Start Time:         {start_time}")
        print(f"  End Time:           {end_time}")
        print(f"  Temperature:        {temp} {temp_unit}")
        print(f"  Wind:               {wind_speed} from {wind_dir}")
        print(f"  Short Forecast:     {short_forecast}")
        print(f"  Detailed Forecast:  {detailed_forecast}")
        print(f"  Icon URL:           {icon}\n")
    print("=" * 50)


def print_raw_current(obs_data):
    """Print raw current observation JSON data."""
    print("\n=== Raw Current Observation Data ===\n")
    print(json.dumps(obs_data, indent=2))
    print("\n" + "=" * 50)


def print_readable_current(obs_data):
    """Print a human-readable summary of current weather observations."""
    props = obs_data.get("properties", {})
    timestamp = format_time(props.get("timestamp", "N/A"))
    temp_c = props.get("temperature", {}).get("value")
    temperature_f = c_to_f(temp_c) if temp_c is not None else "N/A"
    humidity = props.get("relativeHumidity", {}).get("value", "N/A")
    wind_speed_mps = props.get("windSpeed", {}).get("value")
    wind_speed_mph = mps_to_mph(wind_speed_mps) if wind_speed_mps is not None else "N/A"
    wind_direction = props.get("windDirection", {}).get("value", "N/A")
    conditions = props.get("textDescription", "N/A")

    print("\n=== Human-Readable Current Observations ===\n")
    print(f"As of {timestamp}, the current conditions are:")
    if isinstance(temperature_f, float):
        print(f"  Temperature: {temperature_f:.1f} °F")
    else:
        print(f"  Temperature: {temperature_f} °F")
    if isinstance(wind_speed_mph, float):
        print(f"  Wind: {wind_speed_mph:.1f} mph from {wind_direction}°")
    else:
        print(f"  Wind: {wind_speed_mph} mph from {wind_direction}°")
    print(f"  Humidity: {humidity} %")
    print(f"  Conditions: {conditions}")
    print("\n" + "=" * 50)


def main():
    try:
        # Step 1: Get grid point data.
        points_data = get_points_data(latitude, longitude)
    except Exception as e:
        print(f"Error retrieving grid point data: {e}")
        sys.exit(1)

    forecast_url = points_data.get("forecast")
    stations_url = points_data.get("observationStations")
    if not forecast_url or not stations_url:
        print(
            "Error: Forecast or observationStations URL not found in the /points response."
        )
        sys.exit(1)

    try:
        # Step 2: Get forecast data.
        forecast_data = get_forecast_data(forecast_url)
    except Exception as e:
        print(f"Error retrieving forecast data: {e}")
        sys.exit(1)

    try:
        # Step 3: Get current observation data.
        obs_data = get_observation_data(stations_url)
    except Exception as e:
        print(f"Error retrieving observation data: {e}")
        sys.exit(1)

    # Print raw JSON outputs.
    print_raw_forecast(forecast_data)
    print_raw_current(obs_data)

    # Then print human-readable summaries.
    print_readable_forecast(forecast_data)
    print_readable_current(obs_data)


if __name__ == "__main__":
    main()
