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

async def fetch_weather_data(lat: str = DEFAULT_LAT, lon: str = DEFAULT_LON) -> dict | None:
    """
    Fetches weather data from National Weather Service API.

    Args:
        lat: Latitude for the weather location.
        lon: Longitude for the weather location.

    Returns:
        A dictionary containing the weather data, or None if an error occurs.
    """
    base_url = 'https://api.weather.gov'
    headers = {
        'User-Agent': 'RaspberryPi-WeatherApp/1.0 (pyside-weather-app)',
        'Accept': 'application/json'
    }

    try:
        # First, get the grid point information
        points_url = f'{base_url}/points/{lat},{lon}'
        logger.info(f"Fetching gridpoints for lat={lat}, lon={lon} from {points_url}")
        
        async with httpx.AsyncClient() as client:
            # Get grid points
            points_response = await client.get(points_url, headers=headers)
            points_response.raise_for_status()
            points_data = points_response.json()
            
            # Extract forecast URL and other relevant information
            forecast_url = points_data.get('properties', {}).get('forecast')
            observation_stations_url = points_data.get('properties', {}).get('observationStations')
            
            if not forecast_url:
                logger.error("Forecast URL not found in points response")
                return None
                
            if not observation_stations_url:
                logger.error("Observation stations URL not found in points response")
                return None
                
            # Get forecast data
            logger.info(f"Fetching forecast from {forecast_url}")
            forecast_response = await client.get(forecast_url, headers=headers)
            forecast_response.raise_for_status()
            forecast_data = forecast_response.json()
            
            # Get observation stations
            logger.info(f"Fetching observation stations from {observation_stations_url}")
            stations_response = await client.get(observation_stations_url, headers=headers)
            stations_response.raise_for_status()
            stations_data = stations_response.json()
            
            if not stations_data.get('features') or len(stations_data['features']) == 0:
                logger.error("No observation stations found")
                return None
                
            # Get the first station's observations
            station_url = stations_data['features'][0]['properties'].get('@id')
            if not station_url:
                logger.error("Station URL not found")
                return None
                
            observations_url = f"{station_url}/observations/latest"
            logger.info(f"Fetching latest observations from {observations_url}")
            obs_response = await client.get(observations_url, headers=headers)
            obs_response.raise_for_status()
            obs_data = obs_response.json()
            
            # Format data to match our existing structure
            formatted_data = format_weather_data(forecast_data, obs_data)
            logger.info(f"Successfully fetched and formatted weather data for lat={lat}, lon={lon}")
            
            return formatted_data
            
    except httpx.RequestError as exc:
        logger.error(f"An error occurred while requesting {exc.request.url!r}: {exc}")
    except httpx.HTTPStatusError as exc:
        logger.error(f"Error response {exc.response.status_code} while requesting {exc.request.url!r}: {exc.response.text}")
    except Exception as exc:
        logger.error(f"An unexpected error occurred: {exc}")
    
    return None

def format_weather_data(forecast_data, observation_data):
    """
    Formats NWS API data to match the structure expected by our frontend.
    """
    try:
        # Extract current observation data
        current_props = observation_data.get('properties', {})
        temperature_c = current_props.get('temperature', {}).get('value')
        temperature_f = celsius_to_fahrenheit(temperature_c) if temperature_c is not None else None
        
        current = {
            "temp": temperature_f,
            "feels_like": temperature_f,  # NWS doesn't provide feels_like directly
            "weather": [
                {
                    "description": current_props.get('textDescription', 'Unknown'),
                    "icon": map_nws_icon_to_owm(current_props.get('icon'))
                }
            ]
        }
        
        # Process forecast periods (format them as daily data)
        daily = []
        periods = forecast_data.get('properties', {}).get('periods', [])
        
        # NWS provides forecasts for day/night separately, combine them
        day_index = 0
        while day_index < len(periods):
            if day_index + 1 < len(periods):
                day_period = periods[day_index]
                night_period = periods[day_index + 1]
                
                # Skip if the periods don't match a day/night pair
                if "night" not in night_period.get('name', '').lower():
                    day_index += 1
                    continue
                
                # Calculate average temperature
                day_temp = day_period.get('temperature')
                night_temp = night_period.get('temperature')
                
                pop = estimate_precipitation_probability(
                    day_period.get('shortForecast', ''),
                    day_period.get('detailedForecast', '')
                )
                
                daily_entry = {
                    "dt": convert_nws_date_to_unix(day_period.get('startTime')),
                    "temp": {
                        "day": day_temp,
                        "min": night_temp,
                        "max": day_temp
                    },
                    "weather": [
                        {
                            "description": day_period.get('shortForecast', 'Unknown'),
                            "icon": map_nws_icon_to_owm(day_period.get('icon'))
                        }
                    ],
                    "pop": pop
                }
                
                daily.append(daily_entry)
                day_index += 2  # Move to the next day (skip night)
            else:
                # Handle the case with an odd number of periods
                day_index += 1
                
        # Return data in format similar to OpenWeatherMap for compatibility
        return {
            "current": current,
            "daily": daily
        }
        
    except Exception as e:
        logger.error(f"Error formatting weather data: {e}")
        return None
        
def celsius_to_fahrenheit(celsius):
    """Convert Celsius to Fahrenheit"""
    if celsius is None:
        return None
    return (celsius * 9/5) + 32

def convert_nws_date_to_unix(date_string):
    """Convert NWS ISO date string to Unix timestamp"""
    if not date_string:
        return None
    try:
        from datetime import datetime
        import time
        dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
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
    percentage_matches = re.findall(r'(\d+)\s*percent(?:\s*chance)?', detailed_forecast.lower())
    if percentage_matches:
        # Use the highest percentage found
        probability = max([float(p)/100 for p in percentage_matches])
    else:
        # Estimate based on wording
        if "slight chance" in detailed_forecast.lower():
            probability = 0.2
        elif "chance" in detailed_forecast.lower():
            probability = 0.4
        elif "likely" in detailed_forecast.lower():
            probability = 0.7
        elif any(term in detailed_forecast.lower() for term in ["rain", "showers", "thunderstorms", "snow"]):
            probability = 0.9
    
    return probability

def map_nws_icon_to_owm(nws_icon_url):
    """
    Map NWS icon URLs to OpenWeatherMap icon codes for compatibility with existing frontend
    """
    if not nws_icon_url:
        return "01d"  # Default to clear day
        
    # Extract the icon name from URL
    # Example URL: https://api.weather.gov/icons/land/day/skc?size=medium
    icon_name = nws_icon_url.split('/')[-1].split('?')[0]
    is_day = '/day/' in nws_icon_url
    suffix = "d" if is_day else "n"
    
    # Map NWS icons to OpenWeatherMap codes
    icon_map = {
        "skc": f"01{suffix}",  # clear sky
        "few": f"02{suffix}",  # few clouds
        "sct": f"03{suffix}",  # scattered clouds
        "bkn": f"04{suffix}",  # broken clouds
        "ovc": f"04{suffix}",  # overcast clouds
        "rain": f"10{suffix}",  # rain
        "rain_showers": f"09{suffix}",  # showers
        "rain_showers_hi": f"09{suffix}",  # showers high intensity
        "tsra": f"11{suffix}",  # thunderstorm
        "tsra_sct": f"11{suffix}",  # scattered thunderstorms
        "tsra_hi": f"11{suffix}",  # heavy thunderstorms
        "snow": f"13{suffix}",  # snow
        "rain_snow": f"13{suffix}",  # rain and snow
        "fzra": f"13{suffix}",  # freezing rain
        "snow_fzra": f"13{suffix}",  # snow and freezing rain
        "sleet": f"13{suffix}",  # sleet
        "fog": f"50{suffix}",  # fog
    }
    
    for key, value in icon_map.items():
        if key in icon_name:
            return value
            
    return f"01{suffix}"  # Default to clear sky

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