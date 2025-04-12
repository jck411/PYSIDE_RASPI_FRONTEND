#!/usr/bin/env python3
import requests
from datetime import datetime

# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------
# Replace with your own email or contact info as per NWS API policy
USER_AGENT      = "OrlandoWeatherScript (youremail@example.com)"
LATITUDE        = "28.5383"
LONGITUDE       = "-81.3792"
FORECAST_HOURS  = 24  # How many hours ahead to show

# -------------------------------------------------------------------
# NWS API Interaction Functions
# -------------------------------------------------------------------
def get_point_metadata(lat, lon):
    """
    Query the NWS /points endpoint for metadata about the given lat/lon.
    Returns a JSON dict with URLs for stations, forecastHourly, forecastGridData, etc.
    """
    url = f"https://api.weather.gov/points/{lat},{lon}"
    response = requests.get(url, headers={"User-Agent": USER_AGENT})
    response.raise_for_status()
    return response.json()

def get_nearest_station(stations_url):
    """
    Given the observationStations URL from point metadata,
    fetch the list of stations and return the first station's ID and URL.
    """
    resp = requests.get(stations_url, headers={"User-Agent": USER_AGENT})
    resp.raise_for_status()
    data = resp.json()
    features = data.get("features", [])
    if not features:
        raise RuntimeError("No observation stations found for this location.")
    first = features[0]
    station_id  = first["properties"]["stationIdentifier"]
    station_url = first["id"]
    return station_id, station_url

def get_latest_observation(station_url):
    """
    Fetch the latest live observation from the given station URL.
    Endpoint: {station_url}/observations/latest
    """
    url = f"{station_url}/observations/latest"
    resp = requests.get(url, headers={"User-Agent": USER_AGENT})
    resp.raise_for_status()
    return resp.json()

def get_hourly_forecast(forecast_hourly_url):
    """
    Fetch the hourly forecast summary (text, temp, icon) from:
    forecastHourly URL in point metadata.
    """
    resp = requests.get(forecast_hourly_url, headers={"User-Agent": USER_AGENT})
    resp.raise_for_status()
    return resp.json()

def get_grid_forecast(grid_url):
    """
    Fetch the detailed grid forecast data (POP, QPF, skyCover, relativeHumidity)
    from the forecastGridData URL in point metadata.
    """
    resp = requests.get(grid_url, headers={"User-Agent": USER_AGENT})
    resp.raise_for_status()
    return resp.json()

# -------------------------------------------------------------------
# Printing Helper Functions
# -------------------------------------------------------------------
def print_current_observation(obs_json):
    """
    Print the current observation details:
      - timestamp
      - textDescription
      - temperature (°C and °F)
      - windSpeed (m/s)
    """
    props = obs_json.get("properties", {})
    obs_time     = props.get("timestamp", "Unknown time")
    description  = props.get("textDescription", "No description")
    temp_c       = props.get("temperature", {}).get("value")
    wind_speed   = props.get("windSpeed", {}).get("value")

    # Convert to Fahrenheit
    if temp_c is not None:
        temp_f = temp_c * 9/5 + 32
    else:
        temp_f = None

    print("\nCurrent Observation:")
    print("----------------------")
    print(f"Time:        {obs_time}")
    print(f"Description: {description}")
    if temp_c is not None:
        print(f"Temperature: {temp_c:.1f} °C / {temp_f:.1f} °F")
    else:
        print("Temperature: N/A")
    if wind_speed is not None:
        print(f"Wind Speed:  {wind_speed:.1f} m/s")
    else:
        print("Wind Speed:  N/A")
    print("----------------------\n")

def print_hourly_forecast(hourly_json, hours=FORECAST_HOURS):
    """
    Print an hourly forecast summary for the next `hours`:
      - startTime (formatted)
      - temperature + unit
      - shortForecast text
      - icon URL
    """
    periods = hourly_json.get("properties", {}).get("periods", [])[:hours]
    print(f"Hourly Forecast (Next {hours} Hours):")
    print("--------------------------------------------------------------------------------")
    print(f"{'Time':<20} {'Temp':<8} {'Short Forecast':<35} {'Icon'}")
    print("--------------------------------------------------------------------------------")
    for pr in periods:
        # Parse and format time
        raw = pr.get("startTime", "")
        try:
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            time_str = dt.strftime("%Y-%m-%d %H:%M")
        except Exception:
            time_str = raw

        temp = f"{pr.get('temperature','N/A')}{pr.get('temperatureUnit','')}"
        sf   = pr.get("shortForecast", "")
        icon = pr.get("icon", "")
        print(f"{time_str:<20} {temp:<8} {sf:<35} {icon}")
    print("--------------------------------------------------------------------------------\n")

def print_grid_forecast(grid_json, hours=FORECAST_HOURS):
    """
    Print detailed grid forecast for the next `hours`, including:
      - Probability of Precipitation (POP %)
      - Quantitative Precipitation (QPF, mm)
      - Sky Cover (%)
      - Relative Humidity (%)
    """
    props     = grid_json.get("properties", {})
    pop_vals  = props.get("probabilityOfPrecipitation", {}).get("values", [])
    qpf_vals  = props.get("quantitativePrecipitation", {}).get("values", [])
    sky_vals  = props.get("skyCover", {}).get("values", [])
    rh_vals   = props.get("relativeHumidity", {}).get("values", [])

    # Determine how many entries we can show
    counts = [len(pop_vals), len(qpf_vals), len(sky_vals), len(rh_vals)]
    max_hours = min(counts) if counts else 0
    show_hours = min(hours, max_hours)

    if show_hours == 0:
        print("No detailed grid data available.")
        return

    print(f"Detailed Grid Forecast (Next {show_hours} Hours):")
    print("--------------------------------------------------------------------------------")
    print(f"{'Time':<20} {'POP (%)':<8} {'QPF (mm)':<10} {'SkyCover (%)':<13} {'RH (%)':<8}")
    print("--------------------------------------------------------------------------------")

    for i in range(show_hours):
        # validTime example: "2025-04-11T19:00:00+00:00/PT1H"
        vt = pop_vals[i].get("validTime", "").split("/")[0]
        try:
            dt = datetime.fromisoformat(vt.replace("Z", "+00:00"))
            time_str = dt.strftime("%Y-%m-%d %H:%M")
        except Exception:
            time_str = vt

        pop = pop_vals[i].get("value", "N/A")
        qpf = qpf_vals[i].get("value", "N/A")
        sky = sky_vals[i].get("value", "N/A")
        rh  = rh_vals[i].get("value", "N/A")

        print(f"{time_str:<20} {str(pop):<8} {str(qpf):<10} {str(sky):<13} {str(rh):<8}")

    print("--------------------------------------------------------------------------------\n")

# -------------------------------------------------------------------
# Main Function
# -------------------------------------------------------------------
def main():
    # 1. Fetch point metadata (gives us station list, forecast URLs)
    meta = get_point_metadata(LATITUDE, LONGITUDE)
    props = meta.get("properties", {})

    stations_url        = props.get("observationStations")
    forecast_hourly_url = props.get("forecastHourly")
    forecast_grid_url   = props.get("forecastGridData")

    # 2. Get nearest station and print its ID
    station_id, station_url = get_nearest_station(stations_url)
    print(f"Using observation station: {station_id}")

    # 3. Current observation
    obs_json = get_latest_observation(station_url)
    print_current_observation(obs_json)

    # 4. Hourly summary forecast
    hourly_json = get_hourly_forecast(forecast_hourly_url)
    print_hourly_forecast(hourly_json, hours=FORECAST_HOURS)

    # 5. Detailed grid forecast
    grid_json = get_grid_forecast(forecast_grid_url)
    print_grid_forecast(grid_json, hours=FORECAST_HOURS)

if __name__ == "__main__":
    main()
