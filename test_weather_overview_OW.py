#!/usr/bin/env python3
"""
weather_combined_2calls.py

Fetches current weather + minutely rain forecast (1 API call),
and human-readable overview (1 API call) from OpenWeather One Call 3.0.

Total: 2 API calls.

Requirements:
    pip3 install requests python-dotenv
"""

import os
import sys
import json
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load API key
ENV_PATH = '/home/jack/PYSIDE_RASPI_FRONTEND/.env'
load_dotenv(ENV_PATH)
API_KEY = os.getenv('OPENWEATHER_API_KEY')
if not API_KEY:
    sys.exit(f"Error: OPENWEATHER_API_KEY not found in {ENV_PATH}")

# Winter Park, FL
LAT = 28.600000
LON = -81.339240

params = {
    'lat': LAT,
    'lon': LON,
    'appid': API_KEY,
    'units': 'imperial',
    'lang': 'en',
    'exclude': 'hourly,daily,alerts'  # keep current + minutely
}

### --- One Call for Current + Minutely ---
onecall_url = "https://api.openweathermap.org/data/3.0/onecall"
resp = requests.get(onecall_url, params=params)
if resp.status_code != 200:
    print(f"One Call API Error {resp.status_code}: {resp.text}")
    sys.exit(1)

data = resp.json()
current = data.get("current", {})
minutely = data.get("minutely", [])

# Current Weather
dt = datetime.fromtimestamp(current.get('dt', 0), tz=timezone.utc).astimezone().strftime('%Y-%m-%d %H:%M')
sunrise = datetime.fromtimestamp(current.get('sunrise', 0), tz=timezone.utc).astimezone().strftime('%H:%M')
sunset = datetime.fromtimestamp(current.get('sunset', 0), tz=timezone.utc).astimezone().strftime('%H:%M')
weather = current.get('weather', [{}])[0]

print(f"=== Current Weather for Winter Park, FL ===")
print(f"Time: {dt}")
print(f"Weather: {weather.get('description', 'N/A').capitalize()}")
print(f"Temperature: {current.get('temp', 'N/A')}°F (Feels like {current.get('feels_like', 'N/A')}°F)")
print(f"Humidity: {current.get('humidity', 'N/A')}%")
print(f"Pressure: {current.get('pressure', 'N/A')} hPa")
print(f"Dew Point: {current.get('dew_point', 'N/A')}°F")
print(f"UV Index: {current.get('uvi', 'N/A')}")
print(f"Cloudiness: {current.get('clouds', 'N/A')}%")
print(f"Visibility: {current.get('visibility', 'N/A')} meters")
print(f"Wind: {current.get('wind_speed', 'N/A')} mph at {current.get('wind_deg', 'N/A')}°")
print(f"Wind Gust: {current.get('wind_gust', 'N/A')} mph")
print(f"Sunrise: {sunrise}")
print(f"Sunset: {sunset}")

# Minutely Forecast
if minutely:
    print("\n=== Minute-by-Minute Rain Forecast ===")
    for m in minutely[:30]:
        t = datetime.fromtimestamp(m['dt'], tz=timezone.utc).astimezone().strftime('%H:%M')
        rain_mm = m['precipitation']
        print(f"{t} — {rain_mm:.2f} mm")
else:
    print("\nNo minutely rain data available.")

### --- Overview (Second API Call) ---
overview_url = "https://api.openweathermap.org/data/3.0/onecall/overview"
overview_resp = requests.get(overview_url, params=params)
if overview_resp.status_code != 200:
    print(f"\nOverview API Error {overview_resp.status_code}: {overview_resp.text}")
    sys.exit(1)

overview_data = overview_resp.json()
overview_text = overview_data.get("weather_overview")

print("\n=== Weather Overview for Winter Park, FL ===")
print(overview_text if overview_text else "No weather overview available.")
