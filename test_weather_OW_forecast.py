#!/usr/bin/env python3
"""
compare_rain_forecasts.py

Compares hourly vs daily rain probabilities from OpenWeather One Call 3.0
for Winter Park, FL. Useful for understanding why forecasts might differ.

Requirements:
    pip3 install requests python-dotenv
"""

import os
import sys
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load .env
load_dotenv("/home/jack/PYSIDE_RASPI_FRONTEND/.env")
API_KEY = os.getenv("OPENWEATHER_API_KEY")
if not API_KEY:
    sys.exit("OPENWEATHER_API_KEY missing in .env")

LAT, LON = 28.600000, -81.339240

BASE_URL = "https://api.openweathermap.org/data/3.0/onecall"
COMMON = {
    "lat": LAT,
    "lon": LON,
    "appid": API_KEY,
    "units": "imperial",
    "lang": "en",
}

# Fetch hourly data (24h)
hourly_resp = requests.get(BASE_URL, params={**COMMON, "exclude": "current,minutely,daily,alerts"})
hourly_data = hourly_resp.json().get("hourly", [])[:24]

# Fetch daily data (next 2 days)
daily_resp = requests.get(BASE_URL, params={**COMMON, "exclude": "current,minutely,hourly,alerts"})
daily_data = daily_resp.json().get("daily", [])[:3]

# Format time helper
def ftime(ts): return datetime.fromtimestamp(ts, tz=timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M")

# Compare and print
print("=== 🌦️ Rain Forecast Comparison (Winter Park, FL) ===")

# Daily summary
for i, day in enumerate(daily_data[1:3], start=1):
    dt = datetime.fromtimestamp(day['dt'], tz=timezone.utc).astimezone().strftime('%A %Y-%m-%d')
    pop = day.get('pop', 0) * 100
    rain = day.get('rain', 0)
    desc = day['weather'][0]['description'].capitalize()
    print(f"\n📅 {dt}")
    print(f"  Daily forecast: {desc}")
    print(f"  • Chance of rain: {pop:.0f}%")
    if rain: print(f"  • Rain: {rain:.2f} mm")

    # Hourly pop average for that day
    hourly_same_day = [h for h in hourly_data if
                       datetime.fromtimestamp(h['dt'], tz=timezone.utc).astimezone().day ==
                       datetime.fromtimestamp(day['dt'], tz=timezone.utc).astimezone().day]

    if not hourly_same_day:
        print("  ⚠️ No hourly data available for this day.")
        continue

    rain_hours = [h for h in hourly_same_day if h.get('pop', 0) > 0]
    avg_pop = sum(h.get('pop', 0) for h in hourly_same_day) / len(hourly_same_day) * 100
    max_pop = max((h.get('pop', 0) for h in hourly_same_day), default=0) * 100

    print(f"  Hourly summary: {len(rain_hours)}/24 hours show rain")
    print(f"  • Max chance (hourly): {max_pop:.0f}%")
    print(f"  • Avg chance (hourly): {avg_pop:.0f}%")

    if (pop == 0 and max_pop >= 30) or (pop >= 50 and max_pop == 0):
        print("  ⚠️ Rain mismatch: daily vs hourly forecast differ.")
