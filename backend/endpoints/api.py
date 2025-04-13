import logging
from fastapi import APIRouter, HTTPException, Response
from backend.config.config import CONFIG
from backend.endpoints.state import GEN_STOP_EVENT, TTS_STOP_EVENT

# Import weather state
import backend.weather.state as weather_state

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")


@router.options("/options")
async def openai_options():
    return Response(status_code=200)


@router.get("/tts-state")
async def get_tts_state():
    """Return the current TTS state from config"""
    try:
        return {"tts_enabled": CONFIG["GENERAL_AUDIO"]["TTS_ENABLED"]}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get TTS state: {str(e)}"
        )


@router.post("/toggle-tts")
async def toggle_tts():
    try:
        current_status = CONFIG["GENERAL_AUDIO"]["TTS_ENABLED"]
        CONFIG["GENERAL_AUDIO"]["TTS_ENABLED"] = not current_status
        return {"tts_enabled": CONFIG["GENERAL_AUDIO"]["TTS_ENABLED"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to toggle TTS: {str(e)}")


@router.post("/stop-audio")
async def stop_tts():
    logger.info("Stop TTS requested")
    TTS_STOP_EVENT.set()
    return {"status": "success", "message": "TTS stopped"}


@router.post("/stop-generation")
async def stop_generation():
    """
    Manually set the global GEN_STOP_EVENT.
    Any ongoing streaming text generation will stop soon after it checks the event.
    """
    GEN_STOP_EVENT.set()
    return {
        "detail": "Generation stop event triggered. Ongoing text generation will exit soon."
    }


# --- Weather Endpoint ---
@router.get("/weather")
async def get_weather_data():
    """Returns the latest cached weather data."""
    if weather_state.latest_weather_data:
        return weather_state.latest_weather_data
    else:
        # Return a 503 Service Unavailable if data hasn't been fetched yet
        raise HTTPException(
            status_code=503, detail="Weather data is not yet available."
        )

@router.post("/weather/refresh")
async def refresh_weather_data():
    """Forces a refresh of weather data by fetching new data from all sources."""
    from backend.weather.fetcher import fetch_weather_data
    from backend.weather.openweather_fetcher import fetch_openweather_data
    import asyncio
    
    try:
        # Fetch both NWS and OpenWeatherMap data concurrently
        nws_task = fetch_weather_data()
        ow_task = fetch_openweather_data()
        
        # Wait for both to complete
        nws_data, ow_data = await asyncio.gather(nws_task, ow_task, return_exceptions=True)
        
        # Handle any exceptions
        if isinstance(nws_data, Exception):
            logger.error(f"Error fetching NWS data: {nws_data}")
            return {"status": "error", "message": f"Failed to refresh NWS data: {str(nws_data)}"}
        
        if isinstance(ow_data, Exception):
            logger.error(f"Error fetching OpenWeatherMap data: {ow_data}")
            return {"status": "error", "message": f"Failed to refresh OpenWeatherMap data: {str(ow_data)}"}
            
        # Only update if NWS data was fetched successfully
        if nws_data:
            # Store basic NWS data
            weather_state.latest_weather_data = nws_data
            
            # Integrate OpenWeatherMap data if available
            if ow_data:
                weather_state.latest_weather_data["ow_current"] = ow_data.get("current", {})
                weather_state.latest_weather_data["ow_minutely"] = ow_data.get("minutely", [])
                weather_state.latest_weather_data["ow_weather_overview"] = ow_data.get("weather_overview", "")
                
            return {"status": "success", "message": "Weather data refreshed successfully"}
        else:
            return {"status": "error", "message": "Failed to refresh weather data"}
    except Exception as e:
        logger.error(f"Unexpected error refreshing weather data: {e}")
        return {"status": "error", "message": f"An error occurred: {str(e)}"}
