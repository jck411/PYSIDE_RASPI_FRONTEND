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
