import asyncio
import logging

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from backend.config.config import setup_chat_client
from backend.models.openaisdk import validate_messages_for_ws, stream_openai_completion
from backend.endpoints.api import router as api_router
from backend.endpoints.state import GEN_STOP_EVENT
from backend.tts.processor import process_streams

# Import weather components
from backend.weather.fetcher import fetch_weather_data
from backend.weather.openweather_fetcher import fetch_openweather_data
import backend.weather.state as weather_state  # Use alias to avoid name collision

from contextlib import asynccontextmanager

# Near the top of the file, import the navigation handler
from backend.websocket.navigation_handler import navigation_handler

# ------------------------------------------------------------------------------
# Logging Setup (Configure basic logging)
# ------------------------------------------------------------------------------
logging.basicConfig(
    level=logging.WARNING, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------
# Global Initialization
# ------------------------------------------------------------------------------
load_dotenv()
client, DEPLOYMENT_NAME = setup_chat_client()


# ------------------------------------------------------------------------------
# Background Tasks
# ------------------------------------------------------------------------------
async def periodic_weather_update(interval_seconds: int = 1800):
    """Periodically fetches weather data and updates the global state."""
    # Initial fetch immediately
    logger.info("Performing initial weather data fetch...")
    
    # Fetch NWS data (used for forecasts, but not for current weather)
    nws_data = await fetch_weather_data()
    
    # Fetch OpenWeatherMap data (for current weather)
    ow_data = await fetch_openweather_data()
    
    updated_weather_data = None
    if nws_data and not isinstance(nws_data, Exception):
        # Start with NWS data
        updated_weather_data = nws_data.copy() # Make a copy to avoid modifying original if needed elsewhere

        # Integrate OpenWeatherMap current weather data if available and valid
        if ow_data and not isinstance(ow_data, Exception):
            updated_weather_data["ow_current"] = ow_data.get("current", {})
            updated_weather_data["ow_minutely"] = ow_data.get("minutely", [])
            updated_weather_data["ow_weather_overview"] = ow_data.get("weather_overview", "")
            logger.info("OpenWeatherMap current data integrated successfully.")
        else:
            # Log warning if OW data failed but NWS succeeded
            logger.warning("OpenWeatherMap data fetch failed during initial fetch.")

        # Update theme manager if NWS data is valid
        try:
            from frontend.main import app
            if hasattr(app, "theme_manager") and app.theme_manager:
                sunrise_sunset = updated_weather_data.get("sunrise_sunset", {})
                if sunrise_sunset:
                    sunrise = sunrise_sunset.get("sunrise")
                    sunset = sunrise_sunset.get("sunset")
                    if sunrise and sunset:
                        app.theme_manager.update_sun_times(sunrise, sunset)
                        logger.info("Updated theme manager with sunrise/sunset times.")
        except ImportError:
             logger.warning("Could not import frontend app for theme manager update.")
        except Exception as e:
             logger.error(f"Error updating theme manager: {e}")

        # Assign the combined data to the state
        weather_state.latest_weather_data = updated_weather_data
        logger.info("Initial weather data processed successfully.")
    else:
        logger.warning("Initial NWS data fetch failed.")
        # No fallback data - we'll return 503 until real data is available
        
        # Retry sooner for the first attempt
        await asyncio.sleep(30)  # Wait 30 seconds before retrying
        
        # Retry both data sources
        nws_data = await fetch_weather_data()
        ow_data = await fetch_openweather_data()
        
        updated_weather_data_retry = None
        if nws_data and not isinstance(nws_data, Exception):
            # Start with NWS data
            updated_weather_data_retry = nws_data.copy()

            # Integrate OpenWeatherMap current weather data if available and valid
            if ow_data and not isinstance(ow_data, Exception):
                updated_weather_data_retry["ow_current"] = ow_data.get("current", {})
                updated_weather_data_retry["ow_minutely"] = ow_data.get("minutely", [])
                updated_weather_data_retry["ow_weather_overview"] = ow_data.get("weather_overview", "")
                logger.info("OpenWeatherMap current data integrated successfully on retry.")
            else:
                logger.warning("OpenWeatherMap data fetch failed on retry.")

            # Update theme manager if NWS data is valid
            try:
                from frontend.main import app
                if hasattr(app, "theme_manager") and app.theme_manager:
                    sunrise_sunset = updated_weather_data_retry.get("sunrise_sunset", {})
                    if sunrise_sunset:
                        sunrise = sunrise_sunset.get("sunrise")
                        sunset = sunrise_sunset.get("sunset")
                        if sunrise and sunset:
                            app.theme_manager.update_sun_times(sunrise, sunset)
                            logger.info("Updated theme manager with sunrise/sunset times on retry.")
            except ImportError:
                 logger.warning("Could not import frontend app for theme manager update on retry.")
            except Exception as e:
                 logger.error(f"Error updating theme manager on retry: {e}")

            # Assign the combined data to the state
            weather_state.latest_weather_data = updated_weather_data_retry
            logger.info("Second attempt weather data processed successfully.")
        else:
             # Log if NWS failed on retry as well
             logger.error("NWS data fetch failed on retry.")

    # Start periodic updates after the initial fetch
    while True:
        await asyncio.sleep(interval_seconds)  # Wait for specified interval
        logger.info("Attempting periodic weather update...")
        
        # Fetch both data sources concurrently
        nws_task = fetch_weather_data()
        ow_task = fetch_openweather_data()
        
        # Wait for both to complete
        nws_data, ow_data = await asyncio.gather(nws_task, ow_task, return_exceptions=True)
        
        # Handle NWS data
        if isinstance(nws_data, Exception):
            logger.error(f"NWS periodic update failed: {nws_data}")
            nws_data = None
        
        # Handle OpenWeatherMap data
        if isinstance(ow_data, Exception):
            logger.error(f"OpenWeatherMap periodic update failed: {ow_data}")
            ow_data = None
        
        # Update the weather state if NWS data is available
        updated_weather_data_periodic = None
        if nws_data: # Already checked for Exception above
             if isinstance(nws_data, dict): # Explicit check for Pylance
                 updated_weather_data_periodic = nws_data.copy()
             else:
                 # This case should logically not be reachable due to checks above
                 logger.error("Periodic: Reached unexpected state where nws_data is not None but not a dict.")
                 continue # Skip this update cycle

             if ow_data: # Already checked for Exception above
                 if isinstance(ow_data, dict): # Explicit check for Pylance
                     updated_weather_data_periodic["ow_current"] = ow_data.get("current", {})
                     updated_weather_data_periodic["ow_minutely"] = ow_data.get("minutely", [])
                     updated_weather_data_periodic["ow_weather_overview"] = ow_data.get("weather_overview", "")
                 # No else needed here, ow_data being None is handled by the outer 'if ow_data:'
                 logger.info("Periodic: Both NWS and OpenWeatherMap data updated successfully.")

                 # Update theme manager only if both are successful and NWS data is present
                 try:
                     from frontend.main import app
                     if hasattr(app, "theme_manager") and app.theme_manager:
                         sunrise_sunset = updated_weather_data_periodic.get("sunrise_sunset", {})
                         if sunrise_sunset:
                             sunrise = sunrise_sunset.get("sunrise")
                             sunset = sunrise_sunset.get("sunset")
                             if sunrise and sunset:
                                 app.theme_manager.update_sun_times(sunrise, sunset)
                                 logger.info("Periodic: Updated theme manager with sunrise/sunset times.")
                 except ImportError:
                      logger.warning("Periodic: Could not import frontend app for theme manager update.")
                 except Exception as e:
                      logger.error(f"Periodic: Error updating theme manager: {e}")

             else:
                 # NWS succeeded, OW failed
                 logger.warning("Periodic: Only NWS data updated successfully.")

             # Assign the potentially updated data (even if only NWS)
             weather_state.latest_weather_data = updated_weather_data_periodic

        elif ow_data:
             # NWS failed, OW succeeded - Currently we don't store OW data alone
             logger.warning("Periodic: NWS fetch failed, but OpenWeatherMap succeeded. Discarding OW data for now.")
             # Optionally, you could store OW data separately if needed
             # weather_state.latest_ow_data = ow_data # Example

        else:
             # Both failed
             logger.error("Periodic: Both NWS and OpenWeatherMap updates failed.")


# ------------------------------------------------------------------------------
# FastAPI Lifespan Management
# ------------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup...")
    # Start background tasks
    weather_update_task = asyncio.create_task(periodic_weather_update())
    logger.info("Periodic weather update task started.")

    yield  # Application is running

    # --- Shutdown sequence ---
    logger.info("Application shutting down...")
    # Cancel background tasks
    weather_update_task.cancel()
    try:
        await weather_update_task  # Wait for task to finish cancellation
    except asyncio.CancelledError:
        logger.info("Periodic weather update task cancelled.")

    # Add any other shutdown logic here (e.g., closing connections)
    shutdown()  # Call existing shutdown function if needed
    logger.info("Application shutdown complete.")


# --- Existing shutdown function ---
def shutdown():
    # Add any specific resource cleanup needed on shutdown
    logger.info("Executing shutdown procedures...")
    pass


# ------------------------------------------------------------------------------
# Global Variables
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# FastAPI App Setup
# ------------------------------------------------------------------------------
app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------------------------------------------
# WebSocket Endpoint
# ------------------------------------------------------------------------------
@app.websocket("/ws/chat")
async def unified_chat_websocket(websocket: WebSocket):
    await websocket.accept()
    logger.info("New WebSocket connection established")
    
    # Register websocket with navigation handler
    navigation_handler.register_connection(websocket)

    try:
        while True:
            data = await websocket.receive_json()
            logger.debug(f"Received JSON data: {data}")
            action = data.get("action")

            if action == "chat":
                logger.info("Processing new chat message...")
                # Clear event for the new chat.
                GEN_STOP_EVENT.clear()

                messages = data.get("messages", [])
                validated = await validate_messages_for_ws(messages)

                phrase_queue = asyncio.Queue()
                audio_queue = asyncio.Queue()

                process_streams_task = asyncio.create_task(
                    process_streams(phrase_queue, audio_queue, GEN_STOP_EVENT)
                )

                audio_forward_task = asyncio.create_task(
                    forward_audio_to_websocket(audio_queue, websocket, GEN_STOP_EVENT)
                )

                try:
                    async for content in stream_openai_completion(
                        client, DEPLOYMENT_NAME, validated, phrase_queue, GEN_STOP_EVENT
                    ):
                        if GEN_STOP_EVENT.is_set():
                            break
                        logger.debug(f"Sending content chunk: {content[:50]}...")
                        await websocket.send_json(
                            {"content": content, "is_chunk": True}
                        )
                finally:
                    logger.info("Chat stream finished, cleaning up...")
                    # Send a final signal to indicate streaming is complete
                    try:
                        if not GEN_STOP_EVENT.is_set():
                            # Get the accumulated content from the last message
                            # and mark it as complete
                            last_message = next(
                                (
                                    m
                                    for m in validated[::-1]
                                    if m.get("role") == "assistant"
                                ),
                                None,
                            )
                            if last_message:
                                final_content = last_message.get("content", "")
                                logger.debug(f"Sending final message: {final_content[:100]}...")
                                await websocket.send_json(
                                    {
                                        "content": final_content,
                                        "is_final": True,
                                    }
                                )
                    except Exception as e:
                        logger.error(f"Error sending final message: {e}")

                    await phrase_queue.put(None)
                    await process_streams_task
                    await audio_forward_task
                    logger.info("Cleanup completed")
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected.")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
    finally:
        # Unregister websocket from navigation handler
        navigation_handler.unregister_connection(websocket)
        await websocket.close()


# ------------------------------------------------------------------------------
# Audio Forwarding Function
# ------------------------------------------------------------------------------
async def forward_audio_to_websocket(
    audio_queue: asyncio.Queue, websocket: WebSocket, stop_event: asyncio.Event
):
    try:
        while True:
            if stop_event.is_set():
                logger.info("Audio forwarding stopped by stop event")
                await websocket.send_bytes(b"audio:")  # Send empty audio marker
                break

            try:
                audio_data = await audio_queue.get()
                if audio_data is None:
                    logger.info("Received None in audio queue, sending audio end marker")
                    await websocket.send_bytes(b"audio:")
                    break
                # Prepend "audio:" if not already present.
                message = (
                    b"audio:" + audio_data
                    if not audio_data.startswith(b"audio:")
                    else audio_data
                )
                logger.debug(f"Sending audio bytes, size: {len(message)}")
                await websocket.send_bytes(message)
            except Exception as e:
                logger.error(f"Error forwarding audio to websocket: {e}", exc_info=True)
                break
    except Exception as e:
        logger.error(f"Forward audio task error: {e}", exc_info=True)
    finally:
        try:
            await websocket.send_bytes(b"audio:")
        except Exception as e:
            logger.error(f"Error sending final empty message: {e}", exc_info=True)


# ------------------------------------------------------------------------------
# Include Additional API Routes & Run Uvicorn
# ------------------------------------------------------------------------------
app.include_router(api_router)

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
