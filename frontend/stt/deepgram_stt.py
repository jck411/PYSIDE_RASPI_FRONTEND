#!/usr/bin/env python3
import os
import asyncio
import json
import logging
import threading
import concurrent.futures

from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    LiveTranscriptionEvents,
    LiveOptions,
    Microphone,
)
from PySide6.QtCore import QObject, Signal
from dotenv import load_dotenv
from frontend.config import DEEPGRAM_CONFIG, STT_CONFIG

# Use the logger from config
from frontend.config import logger

logging.basicConfig(level=logging.INFO)

load_dotenv()


class DeepgramSTT(QObject):
    transcription_received = Signal(str)
    complete_utterance_received = Signal(str)
    state_changed = Signal(bool)
    enabled_changed = Signal(bool)
    # Signals for inactivity timer UI
    inactivityTimerStarted = Signal(int)  # Emits timeout duration in ms
    inactivityTimerStopped = Signal()

    def __init__(self):
        super().__init__()
        self.is_enabled = STT_CONFIG["enabled"]
        self.is_paused = False
        self.is_finals = []
        self.keepalive_active = False
        self.use_keepalive = STT_CONFIG.get("use_keepalive", True)
        # Get inactivity timeout config
        self._inactivity_timeout_ms = STT_CONFIG.get("inactivity_timeout_ms", 0)
        self._inactivity_timeout_sec = (
            self._inactivity_timeout_ms / 1000.0
            if self._inactivity_timeout_ms > 0
            else 0
        )
        # Create a dedicated event loop for Deepgram tasks and run it in a separate thread.
        self.dg_loop = asyncio.new_event_loop()
        self.dg_thread = threading.Thread(target=self._run_dg_loop, daemon=True)
        self.dg_thread.start()
        # Task references
        self._start_task = None
        self._stop_task = None
        self._is_toggling = False
        self._keepalive_task = None
        self._inactivity_timer_task = None  # Task for inactivity timer
        self._timer_start_time = None  # Store timer start time (monotonic clock)
        # Initialize Deepgram client
        api_key = os.getenv("DEEPGRAM_API_KEY")
        if not api_key:
            raise ValueError("Missing DEEPGRAM_API_KEY in environment variables")
        keepalive_config = {"keepalive": "true"}
        if DEEPGRAM_CONFIG.get("keepalive_timeout"):
            keepalive_config["keepalive_timeout"] = str(
                DEEPGRAM_CONFIG.get("keepalive_timeout")
            )
        config = DeepgramClientOptions(options=keepalive_config)
        self.deepgram = DeepgramClient(api_key, config)
        self.dg_connection = None
        self.microphone = None
        logger.debug("DeepgramSTT initialized with config: %s", DEEPGRAM_CONFIG)
        logger.debug(
            "KeepAlive enabled: %s, timeout: %s seconds",
            DEEPGRAM_CONFIG.get("keepalive", True),
            DEEPGRAM_CONFIG.get("keepalive_timeout", 30),
        )
        logger.info(
            f"STT Inactivity Timeout set to: {self._inactivity_timeout_sec} seconds (0 means disabled)"
        )
        if STT_CONFIG["auto_start"] and self.is_enabled:
            self.set_enabled(True)

    def _run_dg_loop(self):
        asyncio.set_event_loop(self.dg_loop)
        self.dg_loop.run_forever()

    def setup_connection(self):
        self.dg_connection = self.deepgram.listen.asyncwebsocket.v("1")

        async def on_open(client, *args, **kwargs):
            logging.debug("Deepgram connection established")

        self.dg_connection.on(LiveTranscriptionEvents.Open, on_open)

        async def on_close(client, *args, **kwargs):
            self._handle_close()

        self.dg_connection.on(LiveTranscriptionEvents.Close, on_close)

        async def on_warning(client, warning, **kwargs):
            logging.warning("Deepgram warning: %s", warning)

        self.dg_connection.on(LiveTranscriptionEvents.Warning, on_warning)

        async def on_error(client, error, **kwargs):
            self._handle_error(error)

        self.dg_connection.on(LiveTranscriptionEvents.Error, on_error)

        async def on_transcript(client, result, **kwargs):
            try:
                transcript = result.channel.alternatives[0].transcript
                if transcript.strip():
                    # Cancel timer whenever actual text arrives (interim or final)
                    self._cancel_inactivity_timer()

                    if result.is_final:
                        confidence = getattr(
                            result.channel.alternatives[0], "confidence", "N/A"
                        )
                        logging.info(
                            "[FINAL TRANSCRIPT] %s (Confidence: %s)",
                            transcript,
                            confidence,
                        )
                        # Start timer after a final transcript segment is received
                        self._start_inactivity_timer()
                    else:
                        logging.info("[INTERIM TRANSCRIPT] %s", transcript)
                    self.transcription_received.emit(transcript)
                    if result.is_final and transcript:
                        self.is_finals.append(transcript)

                    # Reset inactivity timer ONLY when actual transcript text is received
                    # self._reset_inactivity_timer() # <--- REMOVED: Now handled by VAD events

                # if hasattr(result, 'speech_final') and result.speech_final:
                #     logging.info("[SPEECH EVENT] Speech segment ended")
                #     # Start timer only when Deepgram indicates speech segment ended
                #     self._start_inactivity_timer()

            except Exception as e:
                logging.error("Error processing transcript: %s", str(e))

        self.dg_connection.on(LiveTranscriptionEvents.Transcript, on_transcript)

        async def on_utterance_end(client, *args, **kwargs):
            if self.is_finals:
                utterance = " ".join(self.is_finals)
                logging.info("[COMPLETE UTTERANCE] %s", utterance)
                logging.info(
                    "[UTTERANCE INFO] Segments combined: %d", len(self.is_finals)
                )
                self.complete_utterance_received.emit(utterance)
                self.is_finals = []
            else:
                logging.info("[UTTERANCE END] No final segments to combine")

        self.dg_connection.on(LiveTranscriptionEvents.UtteranceEnd, on_utterance_end)

        # --- Add VAD Event Handlers ---
        # async def on_speech_started(client, *args, **kwargs):
        #     logger.info("[VAD EVENT] Speech started")
        #     # Cancel timer when speech starts
        #     self._cancel_inactivity_timer()
        # self.dg_connection.on(LiveTranscriptionEvents.SpeechStarted, on_speech_started) # <--- REMOVING

        # async def on_speech_ended(client, *args, **kwargs):
        #     logger.info("[VAD EVENT] Speech ended")
        #     # Start timer when speech ends
        #     self._start_inactivity_timer()
        # self.dg_connection.on(LiveTranscriptionEvents.SpeechEnded, on_speech_ended) # <--- REMOVING
        # --- End VAD Event Handlers ---

    async def _async_start(self):
        try:
            self.setup_connection()
            options = LiveOptions(
                model=DEEPGRAM_CONFIG.get("model", "nova-3"),
                language=DEEPGRAM_CONFIG.get("language", "en-US"),
                smart_format=DEEPGRAM_CONFIG.get("smart_format", True),
                encoding=DEEPGRAM_CONFIG.get("encoding", "linear16"),
                channels=DEEPGRAM_CONFIG.get("channels", 1),
                sample_rate=DEEPGRAM_CONFIG.get("sample_rate", 16000),
                interim_results=DEEPGRAM_CONFIG.get("interim_results", True),
                utterance_end_ms="1000",
                vad_events=DEEPGRAM_CONFIG.get("vad_events", True),
                endpointing=DEEPGRAM_CONFIG.get("endpointing", 300),
            )
            started = await self.dg_connection.start(options)
            if not started:
                raise Exception("Failed to start Deepgram connection")
            self.microphone = Microphone(self.dg_connection.send)
            self.microphone.start()
            self.state_changed.emit(self.is_enabled)
            logger.debug("STT started")
            # Start inactivity timer when STT starts
            self._start_inactivity_timer()
        except Exception as e:
            logger.error("Error starting STT: %s", str(e))
            self.set_enabled(False)  # Ensure state is consistent on failure
            self._cancel_inactivity_timer()  # Cancel timer on start failure

    async def _async_stop(self):
        try:
            # Cancel inactivity timer first
            self._cancel_inactivity_timer()

            self.keepalive_active = False
            if self._keepalive_task and not self._keepalive_task.done():
                self._keepalive_task.cancel()
                try:
                    await asyncio.wrap_future(
                        asyncio.run_coroutine_threadsafe(
                            self._keepalive_task, self.dg_loop
                        )
                    )
                except (asyncio.CancelledError, concurrent.futures.CancelledError):
                    pass
                self._keepalive_task = None
            if self.microphone:
                self.microphone.finish()
                self.microphone = None
            if self.dg_connection:
                try:
                    await asyncio.sleep(0.1)
                    await self.dg_connection.finish()
                except asyncio.CancelledError:
                    logger.debug("Deepgram connection finish cancelled as expected.")
                except Exception as e:
                    logger.warning(f"Error during Deepgram connection finish: {e}")
                finally:
                    self.dg_connection = None
            self.state_changed.emit(self.is_enabled)
            logger.debug("STT stopped")
        except asyncio.CancelledError:
            logger.debug("STT stop operation was cancelled")
            # Ensure timer is cancelled if stop is cancelled mid-operation
            self._cancel_inactivity_timer()
            if self.microphone:
                self.microphone.finish()
            if self.dg_connection:
                self.dg_connection = None
        except Exception as e:
            logger.error(f"Error stopping STT: {e}")
            # Ensure timer is cancelled on stop error
            self._cancel_inactivity_timer()
        finally:
            self._stop_task = None

    def set_enabled(self, enabled: bool):
        if self.is_enabled == enabled or self._is_toggling:
            return
        self._is_toggling = True
        try:
            logger.info(f"Setting STT enabled state to: {enabled}")
            self.is_enabled = enabled
            self.enabled_changed.emit(enabled)
            self.state_changed.emit(
                enabled
            )  # Ensure state_changed is emitted consistently

            # Cancel any existing start/stop tasks first
            if self._start_task and not self._start_task.done():
                logger.debug("Cancelling previous start task.")
                self._start_task.cancel()
                self._start_task = None
            if self._stop_task and not self._stop_task.done():
                logger.debug("Cancelling previous stop task.")
                self._stop_task.cancel()
                self._stop_task = None

            # Cancel inactivity timer if disabling
            if not enabled:
                self._cancel_inactivity_timer()

            # Schedule the appropriate async action
            if enabled:
                logger.debug("Scheduling async start...")
                self._start_task = asyncio.run_coroutine_threadsafe(
                    self._async_start(), self.dg_loop
                )
            else:
                logger.debug("Scheduling async stop...")
                self._stop_task = asyncio.run_coroutine_threadsafe(
                    self._async_stop(), self.dg_loop
                )
        finally:
            # Ensure toggling flag is reset even if errors occur
            self._is_toggling = False

    def set_paused(self, paused: bool):
        if self.is_paused == paused:
            return
        self.is_paused = paused
        logger.info(f"Setting STT paused state to: {paused}")
        if not self.is_enabled:
            logger.warning("Cannot pause/resume STT when it's not enabled.")
            return

        if self.dg_connection:
            if paused:
                # Stop timer when pausing
                self._cancel_inactivity_timer()
                if self.use_keepalive:
                    self._activate_keepalive()
                else:
                    # Stop mic directly if not using keepalive
                    if self.microphone:
                        logger.debug("Pausing: Finishing microphone (no keepalive).")
                        self.microphone.finish()
                        self.microphone = None
            else:  # Resuming
                # Regardless of keepalive, if the microphone is not running, restart it.
                if not self.microphone and self.dg_connection:
                    logger.info("Resuming STT: Restarting microphone.")
                    # Ensure keepalive pings are stopped if they were active
                    if self.use_keepalive and self.keepalive_active:
                        self._deactivate_keepalive()
                    # Start the microphone to send audio data
                    self.microphone = Microphone(self.dg_connection.send)
                    self.microphone.start()
                elif self.microphone:
                    # If mic exists but maybe keepalive was used, ensure keepalive is deactivated
                    if self.use_keepalive and self.keepalive_active:
                        logger.debug(
                            "Resuming STT: Microphone exists, ensuring keepalive is deactivated."
                        )
                        self._deactivate_keepalive()
                    else:
                        logger.debug(
                            "Resuming STT: Microphone already running (or keepalive not used)."
                        )
                else:  # No connection?
                    logger.warning(
                        "Resuming STT: Cannot restart microphone - Deepgram connection not active?"
                    )

                # Always attempt to start the inactivity timer when resuming.
                self._start_inactivity_timer()
        else:
            logger.warning("Cannot pause/resume: Deepgram connection is not active.")

    def _activate_keepalive(self):
        if self.keepalive_active:
            return
        logger.debug("Activating Deepgram KeepAlive mode")
        # No need to cancel timer here, pause handles it
        if self.microphone:
            self.microphone.finish()
            self.microphone = None
        self.keepalive_active = True
        if self._keepalive_task and not self._keepalive_task.done():
            self._keepalive_task.cancel()
        self._keepalive_task = asyncio.run_coroutine_threadsafe(
            self._send_keepalive_messages(), self.dg_loop
        )

    async def _send_keepalive_messages(self):
        try:
            interval = 5
            logger.debug(f"Starting KeepAlive message loop with {interval}s interval")
            while self.keepalive_active and self.dg_connection:
                try:
                    keepalive_msg = {"type": "KeepAlive"}
                    await self.dg_connection.send(json.dumps(keepalive_msg))
                    logger.debug("Sent KeepAlive message")
                except Exception as e:
                    logger.error(f"Error sending KeepAlive message: {e}")
                    # Potentially stop keepalive if sending fails repeatedly?
                    break  # Exit loop on send error
                await asyncio.sleep(interval)
            logger.debug("KeepAlive message loop finished.")
        except asyncio.CancelledError:
            logger.debug("KeepAlive message loop cancelled.")
            raise
        except Exception as e:
            logger.error(f"Error in KeepAlive message loop: {e}")
        finally:
            self.keepalive_active = False  # Ensure flag is reset

    def _deactivate_keepalive(self):
        """Deactivate the keepalive mechanism."""
        if self.keepalive_active and self._keepalive_task:
            logger.debug("Deactivating keepalive task")
            # Cancel the task directly instead of using the old helper
            if not self._keepalive_task.done():
                try:
                    self._keepalive_task.cancel()
                    # Optional: Wait briefly for cancellation if needed, but often not necessary
                    # asyncio.run_coroutine_threadsafe(asyncio.sleep(0.01), self.dg_loop).result(timeout=0.1)
                except Exception as e:
                    logger.error(f"Error cancelling keepalive task: {e}")
            self._keepalive_task = None  # Clear the reference
            self.keepalive_active = False
        else:
            logger.debug("Keepalive already inactive or task not found.")
            # Ensure state is consistent
            self.keepalive_active = False
            self._keepalive_task = None

    # --- Inactivity Timer Logic ---

    async def _inactivity_timeout_handler(self):
        """Coroutine that waits for the timeout and then disables STT."""
        timer_duration = self._inactivity_timeout_sec  # Store initial duration
        if timer_duration <= 0:
            logger.debug("Inactivity timer disabled.")
            return  # Do nothing if timeout is zero or negative

        try:
            remaining_time = timer_duration
            logger.info(
                f"Inactivity timer started, timeout in {remaining_time:.1f} seconds."
            )

            while remaining_time > 0:
                await asyncio.sleep(1.0)  # Wait 1 second
                remaining_time -= 1.0
                # Log countdown every few seconds or when close to timeout
                if int(remaining_time) % 5 == 0 or remaining_time < 5:
                    # logger.debug(f"Inactivity timer: {remaining_time:.1f}s remaining...") # Commented out countdown log
                    pass  # Keep the structure

                # Check if cancelled during sleep
                if (
                    not self._inactivity_timer_task
                    or self._inactivity_timer_task.cancelled()
                ):
                    logger.debug("Inactivity timer cancelled during countdown.")
                    return

            # --- Timeout Reached ---
            logger.info(
                f"STT Inactivity timeout reached after {timer_duration:.1f} seconds."
            )

            # Check again if state changed just before disabling
            if (
                not self._inactivity_timer_task
                or self._inactivity_timer_task.cancelled()
            ):
                logger.debug("Inactivity timer cancelled just before disabling STT.")
                return

            if self.is_enabled and not self.is_paused:
                logger.info(
                    f"STT Inactivity timeout reached after {timer_duration:.1f} seconds. Disabling STT."
                )
                # Emit stopped signal before disabling STT
                self.inactivityTimerStopped.emit()
                # Important: Use set_enabled(False) which handles state changes and signals correctly
                # Schedule this call back in the main thread or ensure thread safety if needed,
                # but set_enabled already uses run_coroutine_threadsafe for its core logic.
                # We are already in the dg_loop, so calling set_enabled should be okay as it schedules work.
                self.set_enabled(False)
            else:
                logger.debug(
                    "Inactivity timeout reached, but STT is already disabled or paused."
                )

        except asyncio.CancelledError:
            logger.debug("Inactivity timer task cancelled.")
            # Don't re-raise cancellation error here, it's expected
        except Exception as e:
            logger.error(f"Error in inactivity timeout handler: {e}")
        finally:
            # Ensure task reference is cleared after execution or cancellation
            self._inactivity_timer_task = None

    def _start_inactivity_timer(self):
        """Start or reset the inactivity timer if configured."""
        if self._inactivity_timeout_sec <= 0 or not self.is_enabled:
            return  # Timer disabled or STT not enabled

        # Cancel any existing timer first to reset it
        self._cancel_inactivity_timer(
            emit_signal=False
        )  # Don't emit stop signal on reset

        logger.debug(
            f"Starting inactivity timer for {self._inactivity_timeout_sec} seconds."
        )
        self._timer_start_time = self.dg_loop.time()  # Record start time
        self._inactivity_timer_task = asyncio.run_coroutine_threadsafe(
            self._inactivity_timeout_handler(), self.dg_loop
        )
        # Emit signal with total duration
        self.inactivityTimerStarted.emit(self._inactivity_timeout_ms)

    def _cancel_inactivity_timer(self, emit_signal=True):
        """Cancel the inactivity timer task."""
        cancelled = False
        if self._inactivity_timer_task:
            logger.debug("Cancelling inactivity timer.")
            try:
                self._inactivity_timer_task.cancel()
                # We might want to await briefly if cancellation needs to propagate
                # but run_coroutine_threadsafe makes awaiting tricky here.
                # Let's rely on the cancellation being effective immediately.
                cancelled = True
            except Exception as e:
                logger.error(f"Error cancelling inactivity timer task: {e}")
            finally:
                self._inactivity_timer_task = None
                self._timer_start_time = None  # Reset start time

        if cancelled and emit_signal:
            self.inactivityTimerStopped.emit()

    # --- Add Timer State Getters ---
    def is_timer_running(self):
        """Check if the inactivity timer task exists and is running."""
        return (
            self._inactivity_timer_task is not None
            and not self._inactivity_timer_task.done()
        )

    def get_timer_remaining_ms(self):
        """Calculate the remaining time for the inactivity timer in milliseconds."""
        if not self.is_timer_running() or self._timer_start_time is None:
            return 0

        try:
            now = self.dg_loop.time()
            elapsed_sec = now - self._timer_start_time
            remaining_sec = self._inactivity_timeout_sec - elapsed_sec
            return max(0, int(remaining_sec * 1000))
        except Exception as e:
            logger.error(f"Error calculating remaining timer time: {e}")
            return 0

    # --- End Timer State Getters ---

    def _handle_close(self):
        """Handle connection closure."""
        logger.warning("Deepgram connection closed.")
        self._cancel_inactivity_timer()  # Stop timer on close
        self.keepalive_active = False  # Ensure keepalive is off
        if self._keepalive_task and not self._keepalive_task.done():
            self._keepalive_task.cancel()
        self._keepalive_task = None
        if self.is_enabled:
            # Maybe attempt reconnect or just signal that it's off?
            # For now, just update the state to off if it was supposed to be on.
            logger.info(
                "STT was enabled but connection closed. Setting state to disabled."
            )
            # Use set_enabled(False) to ensure cleanup and signal emission
            # Schedule this call as we are likely in the dg_loop already
            asyncio.run_coroutine_threadsafe(
                self._schedule_set_enabled(False), self.dg_loop
            )
            # self.is_enabled = False
            # self.state_changed.emit(False) # Direct state change can lead to inconsistency

    def _handle_error(self, error):
        """Handle connection errors."""
        logger.error(f"Deepgram connection error: {error}")
        self._cancel_inactivity_timer()  # Stop timer on error
        self.keepalive_active = False  # Ensure keepalive is off
        if self._keepalive_task and not self._keepalive_task.done():
            self._keepalive_task.cancel()
        self._keepalive_task = None
        if self.is_enabled:
            logger.info(
                "STT was enabled but encountered an error. Setting state to disabled."
            )
            # Use set_enabled(False) for consistent state management
            asyncio.run_coroutine_threadsafe(
                self._schedule_set_enabled(False), self.dg_loop
            )
            # self.is_enabled = False
            # self.state_changed.emit(False)

    async def _schedule_set_enabled(self, enabled: bool):
        """Helper to schedule set_enabled from within the dg_loop."""
        # This avoids potential deadlocks if set_enabled tries to wait on a future
        # that needs the dg_loop, which might be blocked waiting for this handler.
        # However, set_enabled itself uses run_coroutine_threadsafe, so direct call might be okay.
        # Keeping this separation for potential future complexity.
        logger.debug(f"Scheduling set_enabled({enabled}) from dg_loop handler.")
        self.set_enabled(enabled)

    def cleanup(self):
        """Clean up resources."""
        logger.info("Cleaning up DeepgramSTT resources...")
        # Cancel timer first
        self._cancel_inactivity_timer()

        # Ensure STT is stopped cleanly using the existing mechanism
        if self.is_enabled:
            logger.debug("Cleanup: Setting enabled to False to trigger stop.")
            # Use set_enabled which handles async stop and cleanup
            # Need to wait for the stop task to complete? This can be tricky on shutdown.
            # Run the stop synchronously if possible, or manage future.
            if self._stop_task and not self._stop_task.done():
                logger.warning("Cleanup: Previous stop task still running?")
                # Maybe wait for it? self._stop_task.result(timeout=2) ?

            # Initiate stop using set_enabled
            self.set_enabled(False)
            # Give it a moment to process in the dg_loop
            if self._stop_task:
                try:
                    logger.debug("Cleanup: Waiting for stop task...")
                    # Wait for the future scheduled by set_enabled(False)
                    self._stop_task.result(timeout=2.0)
                    logger.debug("Cleanup: Stop task completed.")
                except (asyncio.TimeoutError, concurrent.futures.TimeoutError):
                    logger.warning(
                        "Cleanup: Timeout waiting for STT stop task to complete."
                    )
                except Exception as e:
                    logger.error(f"Cleanup: Error waiting for STT stop task: {e}")

        # Stop the dedicated event loop thread
        if self.dg_loop.is_running():
            logger.debug("Cleanup: Stopping Deepgram event loop...")
            # Schedule loop stop from another thread (or here?)
            self.dg_loop.call_soon_threadsafe(self.dg_loop.stop)
            # Wait for the thread to finish
            logger.debug("Cleanup: Waiting for Deepgram thread to join...")
            self.dg_thread.join(timeout=2.0)
            if self.dg_thread.is_alive():
                logger.warning("Cleanup: Deepgram thread did not stop gracefully.")
            else:
                logger.debug("Cleanup: Deepgram thread stopped.")
        logger.info("DeepgramSTT cleanup finished.")

    def toggle(self):
        try:
            self.set_enabled(not self.is_enabled)
        except Exception as e:
            logger.error(f"Error toggling STT: {e}")
            self.state_changed.emit(self.is_enabled)

    def stop(self):
        if self._start_task and not self._start_task.done():
            self._start_task.cancel()
            self._start_task = None
        if self._stop_task and not self._stop_task.done():
            self._stop_task.cancel()
            self._stop_task = None
        self._stop_task = asyncio.run_coroutine_threadsafe(
            self._async_stop(), self.dg_loop
        )
        self.is_enabled = False
        self.is_paused = False
        self.state_changed.emit(False)
        self.enabled_changed.emit(False)
        logger.debug("STT stop initiated")

    async def stop_async(self):
        if self._start_task and not self._start_task.done():
            self._start_task.cancel()
            self._start_task = None
        if self._stop_task and not self._stop_task.done():
            self._stop_task.cancel()
            self._stop_task = None
        self._stop_task = asyncio.run_coroutine_threadsafe(
            self._async_stop(), self.dg_loop
        )
        self._stop_task.result()
        self.is_enabled = False
        self.is_paused = False
        self.enabled_changed.emit(False)
        logger.debug("STT fully stopped and cleaned up")

    def __enter__(self):
        self.set_enabled(True)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.set_enabled(False)
        return False

    def __del__(self):
        self.keepalive_active = False
        if self._keepalive_task and not self._keepalive_task.done():
            self._keepalive_task.cancel()
        self.set_enabled(False)

    async def shutdown(self, signal, loop):
        logger.debug(f"Received exit signal {signal}...")
        if self.microphone:
            self.microphone.finish()
        if self.dg_connection:
            await self.dg_connection.finish()
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        [task.cancel() for task in tasks]
        await asyncio.gather(*tasks, return_exceptions=True)
        loop.stop()
