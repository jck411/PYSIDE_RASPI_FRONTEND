#!/usr/bin/env python3
import json
import asyncio
import websockets
import logging

from PySide6.QtCore import QObject, Signal

from frontend.config import SERVER_HOST, SERVER_PORT, WEBSOCKET_PATH, logger
from frontend.error_handler import handle_error


class WebSocketClient(QObject):
    """
    Manages WebSocket connection and message handling.
    """

    # Signals
    connectionStatusChanged = Signal(
        bool
    )  # Emitted when WebSocket connects/disconnects
    messageReceived = Signal(dict)  # Emitted when a JSON message is received
    audioReceived = Signal(bytes)  # Emitted when audio data is received

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = True
        self._connected = False
        self._ws = None
        self._ws_url = f"ws://{SERVER_HOST}:{SERVER_PORT}{WEBSOCKET_PATH}"
        logger.info(f"[WebSocketClient] Initialized with URL: {self._ws_url}")

    async def start_connection_loop(self):
        """
        Persistent WebSocket loop for sending and receiving data.
        """
        while self._running:
            logger.info(f"[WebSocketClient] Attempting connection to {self._ws_url}...")
            try:
                async with websockets.connect(self._ws_url) as ws:
                    self._connected = True
                    self._ws = ws
                    self.connectionStatusChanged.emit(True)
                    logger.info("[WebSocketClient] Connected.")

                    while self._running:
                        try:
                            raw_msg = await ws.recv()
                            logger.debug(f"[WebSocketClient] Raw message received type: {type(raw_msg)}, content preview: {str(raw_msg)[:100]}...")
                            await self._process_message(raw_msg)
                        except Exception as e:
                            # Pass user message for significant processing errors
                            handle_error(
                                e,
                                context="WebSocket message processing",
                                user_message="Error processing server message.",
                                error_type="Data",
                            )
                            await asyncio.sleep(0.1)
                            continue
            except (ConnectionRefusedError, websockets.exceptions.InvalidURI) as e:
                # Provide user message for connection failures
                handle_error(
                    e,
                    context="WebSocket connection failed",
                    level=logging.ERROR,
                    user_message="Cannot connect to the server.",
                    error_type="Connection",
                )
                self._connected = False
                self._ws = None
                self.connectionStatusChanged.emit(False)
                await asyncio.sleep(2)
            except websockets.exceptions.ConnectionClosedError as e:
                # Provide user message for unexpected disconnects (but keep as warning)
                handle_error(
                    e,
                    context="WebSocket connection closed",
                    level=logging.WARNING,
                    user_message="Connection to server lost.",
                    error_type="Connection",
                )
                self._connected = False
                self._ws = None
                self.connectionStatusChanged.emit(False)
                await asyncio.sleep(2)
            except Exception as e:
                # General connection loop errors
                handle_error(
                    e,
                    context="WebSocket connection loop",
                    user_message="A WebSocket error occurred.",
                    error_type="Connection",
                )
                self._connected = False
                self._ws = None
                self.connectionStatusChanged.emit(False)
                await asyncio.sleep(2)

        logger.info("[WebSocketClient] Connection loop exited.")
        self._connected = False
        self._ws = None
        self.connectionStatusChanged.emit(False)

    async def _process_message(self, raw_msg):
        """Process incoming messages from WebSocket"""
        if isinstance(raw_msg, bytes):
            if raw_msg.startswith(b"audio:"):
                audio_data = raw_msg[len(b"audio:") :]
                logger.debug(
                    f"[WebSocketClient] Received audio chunk of size: {len(audio_data)} bytes"
                )
                # FIXED: Using synchronous emit for the signal
                # The ChatController will handle scheduling the actual async work
                logger.debug(f"[WebSocketClient] Emitting audioReceived signal for chunk size: {len(audio_data)}")
                self.audioReceived.emit(audio_data)
            else:
                logger.warning("[WebSocketClient] Unknown binary message format")
                # Emit as audio anyway with proper prefix
                audio_data = raw_msg
                self.audioReceived.emit(audio_data)
        else:
            try:
                data = json.loads(raw_msg)
                logger.debug(f"[WebSocketClient] Received message: {data}")
                logger.debug(f"[WebSocketClient] Emitting messageReceived signal with data: {data}")
                self.messageReceived.emit(data)
            except json.JSONDecodeError as e:
                # User message for bad JSON data
                handle_error(
                    e,
                    context="Parsing JSON message",
                    user_message="Received invalid data from server.",
                    error_type="Data",
                )
                logger.error(f"[WebSocketClient] Raw message: {raw_msg}")

    async def send_message(self, data):
        """
        Send a message over the WebSocket connection.

        Args:
            data: Dictionary to be sent as JSON
        """
        if not self._connected or not self._ws:
            logger.warning("[WebSocketClient] Cannot send message: Not connected")
            return False

        try:
            logger.debug(f"[WebSocketClient] Attempting to send message: {data}")
            await self._ws.send(json.dumps(data))
            return True
        except Exception as e:
            # User message for send failures
            handle_error(
                e,
                context="Sending WebSocket message",
                user_message="Failed to send message to server.",
                error_type="Connection",
            )
            return False

    async def send_playback_complete(self):
        """Notify the server that playback is complete"""
        if self._connected and self._ws:
            await self._ws.send(json.dumps({"action": "playback-complete"}))
            logger.info("[WebSocketClient] Sent playback-complete to server")
            return True
        return False

    def is_connected(self):
        """Return the current connection status"""
        return self._connected

    def cleanup(self):
        """Clean up resources"""
        logger.info("[WebSocketClient] Cleaning up resources")
        self._running = False
