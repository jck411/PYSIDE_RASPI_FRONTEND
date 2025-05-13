#!/usr/bin/env python3
import json
import asyncio
import os
from datetime import datetime

from PySide6.QtCore import QObject, Signal, Slot, Property, QTimer

from frontend.config import logger
from frontend.logic.audio_manager import AudioManager
from frontend.logic.websocket_client import WebSocketClient
from frontend.logic.speech_manager import SpeechManager
from frontend.logic.message_handler import MessageHandler
from frontend.logic.wake_word_handler import WakeWordHandler
from frontend.logic.tts_controller import TTSController
from frontend.logic.resource_manager import ResourceManager
from frontend.logic.time_context_provider import TimeContextProvider
from frontend.logic.alarm_command_processor import AlarmCommandProcessor
# Assuming NavigationController is available for import if type hinting is needed
# from frontend.logic.navigation_controller import NavigationController


class ChatController(QObject):
    """
    Main controller that coordinates all chat components.
    Uses modular components to manage different aspects of the chat functionality.
    """

    # Signals for QML - these forward signals from the components
    messageReceived = Signal(str)  # From MessageHandler
    sttTextReceived = Signal(str)  # From SpeechManager
    sttStateChanged = Signal(bool)  # From SpeechManager
    audioReceived = Signal(bytes)  # From WebSocketClient
    connectionStatusChanged = Signal(bool)  # From WebSocketClient
    ttsStateChanged = Signal(bool)  # From TTSController
    messageChunkReceived = Signal(str, bool)  # From MessageHandler
    sttInputTextReceived = Signal(str)  # From SpeechManager
    userMessageAutoSubmitted = Signal(str)  # Emitted when a message is auto-submitted
    # Relayed inactivity timer signals for UI
    inactivityTimerStarted = Signal(int)  # Relays timeout duration in ms
    inactivityTimerStopped = Signal()  # Relays timer stop event
    # Signal to notify UI when history is cleared
    historyCleared = Signal()
    # Signal for time context updates
    timeContextUpdated = Signal(dict)  # Relays time context updates

    def __init__(self, parent=None):
        """
        Initialize the chat controller.
        """
        super().__init__(parent)
        self._running = True
        self._connected = False
        self._chat_history = []  # <-- Add history list here

        # Get the event loop but don't start tasks immediately
        self._loop = asyncio.get_event_loop()

        # Initialize resource manager for async operations and services
        self.resource_manager = ResourceManager(self._loop)

        # Initialize component managers
        self.audio_manager = AudioManager()
        self.speech_manager = SpeechManager()
        self.message_handler = MessageHandler()
        self.websocket_client = WebSocketClient()
        self.tts_controller = TTSController(parent)
        
        # Initialize time context provider
        self.time_context_provider = TimeContextProvider()
        
        # Connect the time context provider to the message handler
        self.message_handler.set_time_context_provider(self.time_context_provider)

        # Initialize wake word handler
        self.wake_word_handler = WakeWordHandler()
        # MODIFIED: Set the new callback for "hey computer"
        self.wake_word_handler.set_tts_callback(self.handle_hey_computer_wakeword)

        # Don't initialize alarm command processor here - it will be set from main.py
        # with proper alarm_controller
        self._alarm_command_processor = None

        # Navigation controller reference - will be set in main.py
        self.navigation_controller = None # type: Optional[NavigationController]
        
        # Timer command processor reference - will be set in main.py
        self._timer_command_processor = None

        # Connect signals
        self._connect_signals()

        # Start tasks with a small delay to ensure QML is set up
        timer = QTimer(self)
        timer.setSingleShot(True)
        timer.setInterval(100)  # 100ms delay
        timer.timeout.connect(self._startTasks)
        timer.start()

        logger.info("[ChatController] Initialized")

    def _connect_signals(self):
        """Connect signals between components"""
        # WebSocket client signals
        self.websocket_client.connectionStatusChanged.connect(
            self._handle_connection_change
        )
        self.websocket_client.messageReceived.connect(self._handle_websocket_message)
        self.websocket_client.audioReceived.connect(self._handle_audio_data_signal)

        # Speech manager signals
        self.speech_manager.sttTextReceived.connect(self.sttTextReceived)
        self.speech_manager.sttStateChanged.connect(self.sttStateChanged)
        self.speech_manager.sttInputTextReceived.connect(self.sttInputTextReceived)
        self.speech_manager.autoSubmitUtterance.connect(
            self._handle_auto_submit_utterance
        )
        # Relay inactivity timer signals from SpeechManager
        self.speech_manager.inactivityTimerStarted.connect(self.inactivityTimerStarted)
        self.speech_manager.inactivityTimerStopped.connect(self.inactivityTimerStopped)

        # MessageHandler signals
        self.message_handler.messageReceived.connect(self.messageReceived)
        self.message_handler.messageChunkReceived.connect(self.messageChunkReceived)
        # Connect internal handler for adding assistant messages to history
        self.message_handler.messageReceived.connect(
            self._add_assistant_message_to_history
        )
        self.message_handler.messageChunkReceived.connect(
            self._handle_assistant_message_chunk
        )

        # TTS controller signals
        self.tts_controller.ttsStateChanged.connect(self.ttsStateChanged)

        # AudioManager sink state changes
        self.audio_manager.audioSink.stateChanged.connect(
            self.audio_manager.handle_audio_state_changed
        )
        
        # Time context provider signals
        self.time_context_provider.timeContextUpdated.connect(self.timeContextUpdated)
        
        # Add method to connect timer command processor when it's set
        self._connect_timer_command_processor()
        
        # Add method to connect alarm command processor when it's set
        self._connect_alarm_command_processor()

    def _connect_timer_command_processor(self):
        """Connect timer command processor signals if available"""
        if hasattr(self, '_timer_command_processor') and self._timer_command_processor:
            # Connect the timerStateQueried signal to handle timer responses
            self._timer_command_processor.timerStateQueried.connect(self._handle_timer_response)
            logger.info("[ChatController] Connected TimerCommandProcessor signals")
    
    def _connect_alarm_command_processor(self):
        """Connect alarm command processor signals if available"""
        if hasattr(self, '_alarm_command_processor') and self._alarm_command_processor:
            # Connect the alarmStateQueried signal to handle alarm responses
            self._alarm_command_processor.alarmStateQueried.connect(self._handle_alarm_response)
            logger.info("[ChatController] Connected AlarmCommandProcessor signals")
    
    def _handle_timer_response(self, response_text):
        """Handle timer command responses"""
        if response_text:
            # Create a unique ID for this timer response
            timestamp = int(datetime.now().timestamp())
            msg_id = f"timer_command_response_{timestamp}"
            
            # Use the message handler to process the response
            self.message_handler.process_message({
                "action": "timer_response",
                "id": msg_id,
                "content": response_text,
                "is_final": True
            })
            logger.info(f"[ChatController] Added timer response: {response_text}")
    
    def _handle_alarm_response(self, response_text):
        """Handle alarm command responses"""
        if response_text:
            # Create a unique ID for this alarm response
            timestamp = int(datetime.now().timestamp())
            msg_id = f"alarm_command_response_{timestamp}"
            
            # Use the message handler to process the response
            self.message_handler.process_message({
                "action": "alarm_response",
                "id": msg_id,
                "content": response_text,
                "is_final": True
            })
            logger.info(f"[ChatController] Added alarm response: {response_text}")

    def _startTasks(self):
        """Start the background tasks"""
        logger.info("[ChatController] Starting background tasks")
        
        # Initialize time context provider
        self.resource_manager.create_task(
            "time_context", self._initialize_time_context()
        )
        
        # Start other background tasks
        self.resource_manager.create_task(
            "websocket", self.websocket_client.start_connection_loop()
        )
        self.resource_manager.create_task(
            "audio", self.audio_manager.start_audio_consumer()
        )

        # Start wake word detection
        self.wake_word_handler.start_listening()
        logger.info("[ChatController] Wake word detection started")
    
    async def _initialize_time_context(self):
        """Initialize the time context provider"""
        success = await self.time_context_provider.initialize()
        if success:
            logger.info("[ChatController] Time context provider initialized successfully")
        else:
            logger.error("[ChatController] Failed to initialize time context provider")

    def _handle_connection_change(self, connected):
        """Handle WebSocket connection status changes"""
        self._connected = connected
        self.connectionStatusChanged.emit(connected)

    def _handle_websocket_message(self, data):
        """Process incoming WebSocket messages"""
        msg_type = data.get("type")
        action = data.get("action")

        if msg_type == "stt":
            stt_text = data.get("stt_text", "")
            logger.debug(
                f"[ChatController] Processing STT text immediately: {stt_text}"
            )
            self.sttTextReceived.emit(stt_text)
        elif msg_type == "stt_state":
            is_listening = data.get("is_listening", False)
            logger.debug(
                f"[ChatController] Updating STT state: listening = {is_listening}"
            )
            self.sttStateChanged.emit(is_listening)
        elif action == "navigate":
            # Handle navigation request from backend
            screen = data.get("screen", "")
            params = data.get("params", {})
            
            # Handle navigation if possible
            if screen and hasattr(self, 'navigation_controller') and self.navigation_controller:
                logger.info(f"[ChatController] Received navigation request to: {screen}")
                if params:
                    # Convert params to JSON string for the QML-friendly slot
                    params_json = json.dumps(params)
                    self.navigation_controller.handleBackendNavigationRequest(screen, params_json)
                else:
                    self.navigation_controller.handleBackendNavigationRequest(screen)
            else:
                logger.warning(f"[ChatController] Cannot process navigation request: {data}")
                
            # Important: Even for navigation requests, still process the message content if available
            # This allows the LLM's response to be displayed even while navigating
            if "content" in data:
                # Process the message content normally
                # Ensure the message has an ID to prevent duplication
                if "id" not in data:
                    data["id"] = f"nav_{screen}_{hash(data.get('content', '')[:50])}"
                self.message_handler.process_message(data)
        elif action == "set_timer":
            # Handle timer setting request
            timer_params = data.get("params", {})
            result = self.message_handler.process_timer_command(timer_params)
            
            # Process the content message if available
            if "content" in data:
                # Process the message content normally to show LLM's natural response
                # Ensure the message has an ID to prevent duplication
                if "id" not in data:
                    timer_name = timer_params.get("name", "Timer")
                    data["id"] = f"timer_{timer_name}_{hash(data.get('content', '')[:50])}"
                self.message_handler.process_message(data)
            else:
                # Only if no content is provided, use the default response
                if result["success"]:
                    # Create a unique ID for this message
                    msg_id = f"timer_default_{timer_params.get('name', 'Timer')}"
                    self.message_handler.process_message({
                        "action": "set_timer",
                        "id": msg_id,
                        "content": result["message"],
                        "is_final": True
                    })
                else:
                    error_msg = f"Could not set timer: {result['message']}"
                    # Create a unique ID for this message
                    msg_id = f"timer_error_{timer_params.get('name', 'Timer')}"
                    self.message_handler.process_message({
                        "action": "set_timer",
                        "id": msg_id,
                        "content": error_msg,
                        "is_final": True
                    })
        elif action == "set_alarm":
            # Handle alarm setting request
            alarm_params = data.get("params", {})
            result = self.message_handler.process_alarm_command(alarm_params)
            
            # Process the content message if available
            if "content" in data:
                # Process the message content normally to show LLM's natural response
                # Ensure the message has an ID to prevent duplication
                if "id" not in data:
                    alarm_name = alarm_params.get("name", "Alarm")
                    data["id"] = f"alarm_{alarm_name}_{hash(data.get('content', '')[:50])}"
                self.message_handler.process_message(data)
            else:
                # Only if no content is provided, use the default response
                if result["success"]:
                    # Create a unique ID for this message
                    msg_id = f"alarm_default_{alarm_params.get('name', 'Alarm')}"
                    self.message_handler.process_message({
                        "action": "set_alarm",
                        "id": msg_id,
                        "content": result["message"],
                        "is_final": True
                    })
                else:
                    error_msg = f"Could not set alarm: {result['message']}"
                    # Create a unique ID for this message
                    msg_id = f"alarm_error_{alarm_params.get('name', 'Alarm')}"
                    self.message_handler.process_message({
                        "action": "set_alarm",
                        "id": msg_id,
                        "content": error_msg,
                        "is_final": True
                    })
        else:
            # Try to process as a message - MessageHandler will emit signals handled elsewhere
            self.message_handler.process_message(data)

    def _handle_audio_data_signal(self, audio_data):
        """
        Non-coroutine method that schedules the async processing of audio data.
        This is what gets connected to the audioReceived signal.
        """
        self.resource_manager.schedule_coroutine(self._handle_audio_data(audio_data))
        logger.debug(
            f"[ChatController] Scheduled audio processing task for {len(audio_data)} bytes"
        )

    async def _handle_audio_data(self, audio_data):
        """Process incoming audio data"""
        # Process the audio in the AudioManager
        is_active = await self.audio_manager.process_audio_data(audio_data)

        # Manage STT pausing/resuming during TTS
        if is_active:  # Audio started or continuing
            if self.speech_manager.is_stt_enabled():
                logger.info("[ChatController] Pausing STT during TTS audio playback")
                self.speech_manager.set_paused(True)
        else:  # Audio ended
            if self.speech_manager.is_stt_enabled():
                # Wait for audio to finish playing before resuming STT
                await self.audio_manager.resume_after_audio()
                logger.info("[ChatController] Resuming STT after TTS audio finished")
                self.speech_manager.set_paused(False)

            # Notify server that playback is complete
            await self.websocket_client.send_playback_complete()

    @property
    def timer_command_processor(self):
        """Get the timer command processor"""
        return self._timer_command_processor
    
    @timer_command_processor.setter
    def timer_command_processor(self, processor):
        """Set the timer command processor and connect signals"""
        self._timer_command_processor = processor
        if processor:
            self._connect_timer_command_processor()
            logger.info("[ChatController] Timer command processor set")

    @property
    def alarm_command_processor(self):
        """Get the alarm command processor"""
        return self._alarm_command_processor
    
    @alarm_command_processor.setter
    def alarm_command_processor(self, processor):
        """Set the alarm command processor and connect signals"""
        self._alarm_command_processor = processor
        if processor:
            self._connect_alarm_command_processor()
            logger.info("[ChatController] Alarm command processor set")

    @Slot(str)
    def sendMessage(self, text):
        """
        Send a user message.
        """
        text = text.strip()
        if not text or not self.websocket_client.is_connected():
            return

        # First, check if this is a timer command
        # If we have a timer command processor registered, try to process as timer command
        timer_command = False
        if hasattr(self, '_timer_command_processor') and self._timer_command_processor:
            # Try to process as a timer command
            if self._timer_command_processor.processCommand(text):
                timer_command = True
                logger.info(f"[ChatController] Timer command detected: {text}")
                # We'll still process this as a normal message, but remember it's a timer command
        
        # Next, check if this is an alarm command
        # If we have an alarm command processor registered, try to process as alarm command
        alarm_command = False
        if self._alarm_command_processor is not None:
            # Try to process as an alarm command
            if self._alarm_command_processor.processCommand(text):
                alarm_command = True
                logger.info(f"[ChatController] Alarm command detected: {text}")
                # We'll still process this as a normal message, but remember it's an alarm command
        
        # Then, check if this is a navigation command
        # If we have a navigation controller registered, try to process as navigation
        navigation_command = False
        if hasattr(self, 'navigation_controller') and self.navigation_controller:
            if self.navigation_controller.processNavigationCommand(text):
                navigation_command = True
                logger.info(f"[ChatController] Navigation command detected: {text}")
                # We'll still process this as a normal message below, but remember it's a navigation command
        
        # Check if we have an interrupted response that needs to be continued
        has_interrupted = self.message_handler.has_interrupted_response()

        # Add message to history
        self.message_handler.add_message("user", text)

        # Add message to persistent display history
        self._add_user_message_to_history(text)

        # If there's interrupted content, we want to continue from where we left off
        # instead of resetting the current response
        if not has_interrupted:
            self.message_handler.reset_current_response()
        else:
            # Initialize the current response with the interrupted content
            interrupted_text = self.message_handler.get_interrupted_response()
            logger.info(
                f"[ChatController] Continuing from interrupted response of length: {len(interrupted_text)}"
            )

            # Emit the interrupted text as the starting point for the current response
            self.message_handler.messageChunkReceived.emit(interrupted_text, False)

            # Clear the interrupted state now that we're continuing
            self.message_handler.clear_interrupted_response()

        # Prepare payload
        payload = {"action": "chat", "messages": self.message_handler.get_messages()}

        # If we're continuing from an interrupted response, tell the server
        if has_interrupted:
            payload["continue_response"] = True
        
        # Add context to the payload for special commands
        context = {}
        if navigation_command:
            context["navigation_command"] = True
        if timer_command:
            context["timer_command"] = True
        if alarm_command:
            context["alarm_command"] = True
            
        if context:
            payload["context"] = context

        # Send asynchronously
        self.resource_manager.schedule_coroutine(
            self.websocket_client.send_message(payload)
        )
        
        command_types = []
        if navigation_command:
            command_types.append("navigation")
        if timer_command:
            command_types.append("timer")
        if alarm_command:
            command_types.append("alarm")
            
        command_type_str = f" ({', '.join(command_types)} command)" if command_types else ""
        
        logger.info(
            f"[ChatController] Sending message: {text}{' (continuing interrupted response)' if has_interrupted else ''}{command_type_str}"
        )

    @Slot()
    def toggleSTT(self):
        """Toggle speech-to-text functionality"""
        self.speech_manager.toggle_stt()

    @Slot()
    def toggleTTS(self):
        """Toggle text-to-speech functionality"""
        self.resource_manager.schedule_coroutine(self.tts_controller.toggleTTS())

    @Slot()
    def stopAll(self):
        """Stop all ongoing operations"""
        logger.info("[ChatController] Stop all triggered.")
        # Mark the current response as interrupted before stopping
        self.message_handler.mark_response_as_interrupted()
        self.resource_manager.schedule_coroutine(self._stopAllAsync())

    async def _stopAllAsync(self):
        """
        Stop TTS/generation and clean up resources.
        """
        # Save current TTS state before stopping
        current_tts_state = self.tts_controller.get_tts_enabled()
        logger.info(
            f"[ChatController] Current TTS state before stopping: {current_tts_state}"
        )

        # Stop server-side operations
        await self.resource_manager.stop_all_services()

        # Restore TTS state if needed
        if current_tts_state:
            logger.info("[ChatController] Restoring TTS state to enabled")
            await self.tts_controller.restore_tts_state(current_tts_state)

        # Stop client-side audio playback
        await self.audio_manager.stop_playback()
        logger.info("[ChatController] Audio resources cleaned up")

    @Slot()
    def clearChat(self):
        """Clear the chat history, saving the current one first."""
        logger.info("[ChatController] Clear chat triggered. Scheduling save and clear.")
        # Schedule the async task to save and clear
        self.resource_manager.schedule_coroutine(self._save_and_clear_history_async())

    def _save_history_to_file(self, history_to_save):
        """Synchronously saves the given history list to a timestamped JSON file."""
        save_path = (
            "/home/jack/PYSIDE_RASPI_FRONTEND/chat_history"  # User specified path
        )
        full_path = ""

        if not history_to_save:
            logger.info(
                "[ChatController:_save_history_to_file] History is empty, skipping save."
            )
            return True  # Indicate success (nothing needed to be done)

        try:
            # Ensure the directory exists
            os.makedirs(save_path, exist_ok=True)

            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"conversation_{timestamp}.json"
            full_path = os.path.join(save_path, filename)

            # Save the file
            with open(full_path, "w", encoding="utf-8") as f:
                json.dump(history_to_save, f, indent=4, ensure_ascii=False)

            logger.info(
                f"[ChatController:_save_history_to_file] Successfully saved conversation to {full_path}"
            )
            return True

        except OSError as e:
            logger.error(
                f"[ChatController:_save_history_to_file] Error creating directory {save_path}: {e}"
            )
            return False
        except IOError as e:
            logger.error(
                f"[ChatController:_save_history_to_file] Error saving conversation to {full_path}: {e}"
            )
            return False
        except Exception as e:
            logger.error(
                f"[ChatController:_save_history_to_file] Unexpected error saving conversation: {e}"
            )
            return False

    async def _save_and_clear_history_async(self):
        """Asynchronously saves the current history using a sync helper and then clears it."""
        history_copy = list(self._chat_history)  # Make a copy

        # Run the synchronous save function in a thread
        save_success = await asyncio.to_thread(self._save_history_to_file, history_copy)

        if not save_success:
            logger.warning(
                "[ChatController:_save_and_clear_history_async] Saving history failed, but proceeding to clear."
            )

        # --- Clear internal state AFTER saving attempt ---
        self.message_handler.clear_history()  # Clear backend context history
        self._chat_history.clear()  # Clear display history
        logger.info("[ChatController] Internal chat history cleared.")
        self.historyCleared.emit()  # Notify UI

    def getConnected(self):
        """Get the connection status for Property binding"""
        return self._connected

    connected = Property(bool, fget=getConnected, notify=connectionStatusChanged)

    # --- Add TTS state getter ---
    @Slot(result=bool)
    def isTtsEnabled(self):
        """Returns the current enabled state of the TTS controller."""
        return self.tts_controller.get_tts_enabled()

    # --- End TTS state getter ---

    # --- Add STT state getters ---
    @Slot(result=bool)
    def isSttEnabled(self):
        """Returns the current enabled state of the STT manager."""
        return self.speech_manager.is_stt_enabled()

    @Slot(result=bool)
    def isSttInactivityTimerRunning(self):
        """Returns true if the STT inactivity timer is currently running."""
        return self.speech_manager.is_inactivity_timer_running()

    @Slot(result=int)
    def getSttInactivityTimeRemaining(self):
        """Returns the remaining time in milliseconds for the STT inactivity timer."""
        return self.speech_manager.get_inactivity_time_remaining()

    # --- End STT state getters ---

    async def cleanup(self):
        """Clean up all resources."""
        logger.info("[ChatController] Cleaning up resources...")
        
        # Add cleanup for time context provider
        await self.time_context_provider.cleanup()
        
        # Perform all existing cleanup
        self._running = False
        
        # Stop wake word detection
        self.wake_word_handler.stop_listening()
        logger.info("[ChatController] Wake word detection stopped")
        
        # Stop audio playback
        await self.audio_manager.stop_playback()
        
        # Stop WebSocket connection
        await self.websocket_client.disconnect()
        
        # Cancel all scheduled tasks
        tasks_cancelled = self.resource_manager.cancel_all_tasks()
        logger.info(f"[ChatController] Cancelled {tasks_cancelled} scheduled tasks")
        
        # Stop audio sink
        await self.audio_manager.cleanup()
        
        # Wait for all tasks to actually complete
        await self.resource_manager.wait_for_all_tasks()
        
        logger.info("[ChatController] All resources cleaned up")

    # --- History Management Methods ---
    @Slot(result=list)
    def getChatHistory(self):
        """Return the current chat history for QML."""
        logger.debug(
            f"[ChatController] getChatHistory called, returning {len(self._chat_history)} messages."
        )
        return list(self._chat_history)  # Return a copy

    def _add_user_message_to_history(self, text):
        """Adds a user message to the internal history list."""
        self._chat_history.append({"text": text, "isUser": True})
        logger.debug(
            f"[ChatController] Added user message to history. New length: {len(self._chat_history)}"
        )

    def _add_assistant_message_to_history(self, text):
        """Adds an assistant message to the internal history list."""
        self._chat_history.append({"text": text, "isUser": False})
        logger.debug(
            f"[ChatController] Added assistant message to history. New length: {len(self._chat_history)}"
        )

    def _handle_assistant_message_chunk(self, text, is_final):
        """Handles chunks of an assistant message, appending to the last message if not final."""
        # The problem is in this method - it's concatenating chunks in a bad way
        # Each received chunk already has the full text via the MessageHandler

        # Don't append repeatedly - just set the text directly
        if not self._chat_history or self._chat_history[-1]["isUser"]:
            # If history is empty or last message was user, add new assistant message
            self._chat_history.append({"text": text, "isUser": False})
        else:
            # Replace existing assistant message instead of appending
            self._chat_history[-1]["text"] = text
        
        logger.debug(
            f"[ChatController] Handled assistant message chunk. Current message: '{text[:50]}...'"
        )

    async def handle_hey_computer_wakeword(self):
        """
        Handles the 'hey computer' wake word.
        If not on the chat screen, navigates there first, then activates voice interaction.
        Uses an event-driven approach to wait for navigation completion.
        """
        logger.info("[ChatController] 'Hey computer' wakeword detected.")

        if not self.navigation_controller:
            logger.warning("[ChatController] NavigationController not available. Activating voice interaction directly.")
            await self._activate_voice_interaction_core()
            return

        current_screen = self.navigation_controller.getCurrentScreenName()
        logger.info(f"[ChatController] Current screen: {current_screen}")

        if current_screen == "ChatScreen.qml":
            await self._activate_voice_interaction_core()
        else:
            logger.info(f"[ChatController] Navigating from {current_screen} to ChatScreen.qml. Waiting for confirmation...")
            navigation_complete_event = asyncio.Event()

            # Temporary slot to listen for the specific screen change
            # Needs to be a method or a callable that can be disconnected.
            # Using a nested function that captures navigation_complete_event and self

            def _on_screen_changed_for_wakeword(screen_name: str):
                # This function will be called by the Qt signal
                if screen_name == "ChatScreen.qml":
                    logger.info(f"[ChatController] Navigation to {screen_name} confirmed via signal for wakeword activation.")
                    if not navigation_complete_event.is_set():
                        self._loop.call_soon_threadsafe(navigation_complete_event.set)
                    # Attempt to disconnect immediately after the event is set
                    try:
                        self.navigation_controller.currentScreenNameChanged.disconnect(_on_screen_changed_for_wakeword)
                        logger.debug("[ChatController] Disconnected temporary screen change listener for wakeword.")
                    except (TypeError, RuntimeError) as e:
                        logger.warning(f"[ChatController] Error disconnecting listener (may have already been disconnected): {e}")
            
            try:
                self.navigation_controller.currentScreenNameChanged.connect(_on_screen_changed_for_wakeword)
                logger.debug("[ChatController] Connected temporary screen change listener for wakeword.")
                
                self.navigation_controller.navigationRequested.emit("ChatScreen.qml")

                try:
                    await asyncio.wait_for(navigation_complete_event.wait(), timeout=5.0) # 5-second timeout
                    logger.info("[ChatController] Navigation to ChatScreen.qml confirmed by event.")
                except asyncio.TimeoutError:
                    logger.warning("[ChatController] Timeout waiting for navigation to ChatScreen.qml. Activating voice interaction anyway.")
                finally:
                    # Ensure disconnection if not already done (e.g. timeout)
                    try:
                        self.navigation_controller.currentScreenNameChanged.disconnect(_on_screen_changed_for_wakeword)
                        logger.debug("[ChatController] Ensured disconnection of listener in finally block after wait.")
                    except (TypeError, RuntimeError):
                        pass # Listener might have already been disconnected or failed to connect

            except Exception as e:
                logger.error(f"[ChatController] Error during navigation setup or wait: {e}. Activating voice interaction as fallback.")
            
            await self._activate_voice_interaction_core()

    async def _activate_voice_interaction_core(self):
        """
        Core logic to activate voice interaction: plays wake sound, enables STT and TTS.
        This was previously the content of _enable_tts_on_wake_word.
        """
        logger.info("[ChatController] Activating voice interaction (sound, STT, TTS)")

        # Play the wake sound
        try:
            # Construct the path to the wakesound PCM file
            wakesound_path = os.path.join(
                os.path.dirname(__file__), "..", "wakeword", "sounds", "Wakesound.pcm"
            )

            # Check if the file exists
            if os.path.exists(wakesound_path):
                logger.info(
                    f"[ChatController] Playing wake sound from {wakesound_path}"
                )
                # Read the PCM data
                with open(wakesound_path, "rb") as f:
                    pcm_data = f.read()

                # Process the PCM audio data
                await self.audio_manager.process_audio_data(pcm_data)
                logger.info("[ChatController] Wake sound playback initiated")

                # Send end-of-stream marker to ensure playback completes properly
                await self.audio_manager.process_audio_data(b"")
                logger.info("[ChatController] Wake sound playback completed")
            else:
                logger.error(
                    f"[ChatController] Wake sound file not found at {wakesound_path}"
                )
        except Exception as e:
            logger.error(f"[ChatController] Error playing wake sound: {e}")

        # Enable STT if it's not already enabled
        if not self.speech_manager.is_stt_enabled():
            # Call toggleSTT which handles state and UI updates
            self.toggleSTT()  
            logger.info("[ChatController] STT enabled after wake word processing.")
        else:
            logger.info("[ChatController] STT was already enabled.")


        # Also enable TTS as per the latest implementation
        # Ensure TTS is enabled for voice responses
        await self.tts_controller.set_tts_enabled(True)
        logger.info("[ChatController] TTS explicitly enabled after wake word processing.")

    def _handle_auto_submit_utterance(self, text: str):
        """
        Handle auto-submission of complete utterances directly to chat.
        This bypasses the input field and sends the message immediately.
        """
        logger.info(f"[ChatController] Auto-submitting utterance to chat: {text}")
        # Emit a signal so the UI can display the message
        self.userMessageAutoSubmitted.emit(text)
        # Call sendMessage, which now handles adding to history
        self.sendMessage(text)
