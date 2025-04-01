import os
from datetime import datetime
import requests
import pytz
from timezonefinder import TimezoneFinder
from dotenv import load_dotenv
from zoneinfo import ZoneInfo

load_dotenv()

def fetch_weather(lat=28.5383, lon=-81.3792, exclude="minutely", units="imperial", lang="en"):
    """
    Fetches weather data from National Weather Service API.
    
    Args:
        lat: Latitude for the weather location.
        lon: Longitude for the weather location.
        exclude: Not used for NWS API but kept for compatibility.
        units: 'imperial' for Fahrenheit or 'metric' for Celsius.
        lang: Not used for NWS API but kept for compatibility.
        
    Returns:
        A dictionary containing the weather data.
    """
    # Convert lat/lon to strings if they're not already
    lat_str = str(lat)
    lon_str = str(lon)
    
    base_url = "https://api.weather.gov"
    headers = {
        "User-Agent": "WeatherTerminalApp/1.0 (youremail@example.com)",
        "Accept": "application/ld+json"
    }
    headers_json = {
        "User-Agent": "WeatherTerminalApp/1.0 (youremail@example.com)",
        "Accept": "application/json"
    }
    
    # Step 1: Get grid point data
    points_url = f"{base_url}/points/{lat_str},{lon_str}"
    points_response = requests.get(points_url, headers=headers)
    points_response.raise_for_status()
    points_data = points_response.json()
    
    forecast_url = points_data.get("forecast")
    stations_url = points_data.get("observationStations")
    if not forecast_url or not stations_url:
        raise ValueError("Forecast or observationStations URL not found in the /points response.")
    
    # Step 2: Get forecast data
    forecast_response = requests.get(forecast_url, headers=headers_json)
    forecast_response.raise_for_status()
    forecast_data = forecast_response.json()
    
    # Step 3: Get current observation data
    stations_response = requests.get(stations_url, headers=headers_json)
    stations_response.raise_for_status()
    stations = stations_response.json().get("features", [])
    if not stations:
        raise ValueError("No observation stations found.")
    
    # Use the first station from the list
    station_url = stations[0]["properties"].get("@id")
    if not station_url:
        raise ValueError("No valid station URL found.")
    
    obs_url = f"{station_url}/observations/latest"
    obs_response = requests.get(obs_url, headers=headers_json)
    obs_response.raise_for_status()
    obs_data = obs_response.json()
    
    # Format the data to match the expected structure
    return format_nws_data(forecast_data, obs_data, units)

def format_nws_data(forecast_data, obs_data, units="imperial"):
    """
    Format NWS API data to match the structure expected by the application.
    
    Args:
        forecast_data: Forecast data from NWS API.
        obs_data: Current observation data from NWS API.
        units: 'imperial' for Fahrenheit or 'metric' for Celsius.
        
    Returns:
        Formatted weather data dictionary.
    """
    # Extract current observation data
    props = obs_data.get("properties", {})
    temp_c = props.get("temperature", {}).get("value")
    
    # Convert temperature based on units
    if units == "imperial":
        temperature = c_to_f(temp_c) if temp_c is not None else None
    else:
        temperature = temp_c
    
    humidity = props.get("relativeHumidity", {}).get("value", "N/A")
    wind_speed_mps = props.get("windSpeed", {}).get("value")
    wind_direction = props.get("windDirection", {}).get("value", "N/A")
    conditions = props.get("textDescription", "N/A")
    
    # Convert wind speed based on units
    if units == "imperial":
        wind_speed = mps_to_mph(wind_speed_mps) if wind_speed_mps is not None else "N/A"
    else:
        wind_speed = wind_speed_mps
    
    # Format current weather
    current = {
        "dt": int(datetime.now().timestamp()),
        "temp": temperature,
        "feels_like": temperature,  # NWS doesn't provide feels_like directly
        "humidity": humidity,
        "wind_speed": wind_speed,
        "wind_deg": wind_direction,
        "weather": [
            {
                "main": conditions,
                "description": conditions,
                "icon": map_nws_icon(props.get("icon"))
            }
        ]
    }
    
    # Format forecast data
    daily = []
    periods = forecast_data.get("properties", {}).get("periods", [])
    
    # Process forecast periods
    day_index = 0
    while day_index < len(periods):
        if day_index + 1 < len(periods):
            day_period = periods[day_index]
            night_period = periods[day_index + 1]
            
            # Skip if the periods don't match a day/night pair
            if "night" not in night_period.get("name", "").lower():
                day_index += 1
                continue
            
            # Get temperatures
            day_temp = day_period.get("temperature")
            night_temp = night_period.get("temperature")
            
            # Convert temperatures if needed
            if units == "metric" and day_period.get("temperatureUnit") == "F":
                day_temp = f_to_c(day_temp) if day_temp is not None else None
                night_temp = f_to_c(night_temp) if night_temp is not None else None
            
            # Estimate precipitation probability
            pop = estimate_precipitation_probability(
                day_period.get("shortForecast", ""),
                day_period.get("detailedForecast", "")
            )
            
            daily_entry = {
                "dt": convert_nws_date_to_unix(day_period.get("startTime")),
                "temp": {
                    "day": day_temp,
                    "min": night_temp,
                    "max": day_temp
                },
                "weather": [
                    {
                        "main": day_period.get("shortForecast", "Unknown"),
                        "description": day_period.get("shortForecast", "Unknown"),
                        "icon": map_nws_icon(day_period.get("icon"))
                    }
                ],
                "pop": pop
            }
            
            daily.append(daily_entry)
            day_index += 2  # Move to the next day (skip night)
        else:
            # Handle the case with an odd number of periods
            day_index += 1
    
    # Return data in a structure similar to OpenWeatherMap for compatibility
    return {
        "current": current,
        "daily": daily,
        "lat": float(obs_data.get("geometry", {}).get("coordinates", [0, 0])[1]),
        "lon": float(obs_data.get("geometry", {}).get("coordinates", [0, 0])[0]),
        "timezone": "America/New_York"  # Default to Eastern Time
    }

def c_to_f(c):
    """Convert Celsius to Fahrenheit."""
    if c is None:
        return None
    return c * 9/5 + 32

def f_to_c(f):
    """Convert Fahrenheit to Celsius."""
    if f is None:
        return None
    return (f - 32) * 5/9

def mps_to_mph(mps):
