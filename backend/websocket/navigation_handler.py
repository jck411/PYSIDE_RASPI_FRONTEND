import logging
import json
from typing import Dict, Any, Optional, Set, Callable
import asyncio

logger = logging.getLogger(__name__)

class NavigationHandler:
    """
    Handles navigation requests between the backend and frontend.
    
    This class manages the websocket-based communication for navigation requests
    that originate from LLM function calls.
    """
    
    def __init__(self):
        self._connections: Set = set()
        logger.info("[NavigationHandler] Initialized")
    
    def register_connection(self, websocket):
        """Register a new websocket connection."""
        self._connections.add(websocket)
        logger.info(f"[NavigationHandler] Connection registered. Total connections: {len(self._connections)}")
    
    def unregister_connection(self, websocket):
        """Unregister a websocket connection."""
        try:
            self._connections.remove(websocket)
            logger.info(f"[NavigationHandler] Connection unregistered. Remaining connections: {len(self._connections)}")
        except KeyError:
            logger.warning("[NavigationHandler] Attempted to unregister unknown connection")
    
    async def send_navigation_request(self, screen: str, params: Optional[Dict[str, Any]] = None, connection=None):
        """
        Send a navigation request to a specific connection or all connected frontends.
        
        Args:
            screen: The screen to navigate to
            params: Optional parameters for the screen
            connection: Optional specific websocket connection to send to. If None, send to all.
        """
        if connection:
            connections = [connection]
            logger.info(f"[NavigationHandler] Sending navigation request to specific connection")
        else:
            connections = self._connections
            if not connections:
                logger.warning("[NavigationHandler] No active connections to send navigation request")
                return
            logger.info(f"[NavigationHandler] Sending navigation request to all {len(connections)} connections")
        
        # Prepare the message
        message = {
            "action": "navigate",
            "screen": screen,
            "params": params or {}
        }
        
        message_json = json.dumps(message)
        logger.info(f"[NavigationHandler] Sending navigation request: {message_json}")
        
        # Send to target connections
        disconnected = set()
        for ws in connections:
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.error(f"[NavigationHandler] Error sending navigation request: {e}")
                disconnected.add(ws)
        
        # Clean up disconnected clients
        for ws in disconnected:
            self.unregister_connection(ws)

# Create a singleton instance
navigation_handler = NavigationHandler() 