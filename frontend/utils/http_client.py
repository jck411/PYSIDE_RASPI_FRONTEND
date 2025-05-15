import asyncio
import aiohttp
from typing import Optional, Dict, Any, Tuple
import logging
import time

logger = logging.getLogger(__name__)

class SharedHTTPClient:
    """
    Singleton class that manages a shared aiohttp ClientSession for the entire application.
    This reduces connection overhead by reusing connections across multiple requests.
    """
    _instance: Optional["SharedHTTPClient"] = None
    _session: Optional[aiohttp.ClientSession] = None
    _lock = asyncio.Lock()

    @classmethod
    async def get_instance(cls) -> "SharedHTTPClient":
        """Get the singleton instance, creating it if necessary"""
        async with cls._lock:
            if cls._instance is None:
                cls._instance = SharedHTTPClient()
            return cls._instance

    @classmethod
    async def get_session(cls) -> aiohttp.ClientSession:
        """Get the shared aiohttp session, creating it if necessary"""
        instance = await cls.get_instance()
        if instance._session is None or instance._session.closed:
            logger.info("Creating new shared HTTP session")
            instance._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))
        return instance._session

    @classmethod
    async def close(cls):
        """Close the shared session if it exists"""
        if cls._instance and cls._instance._session and not cls._instance._session.closed:
            logger.info("Closing shared HTTP session")
            await cls._instance._session.close()
            cls._instance._session = None

    @classmethod
    def is_initialized(cls) -> bool:
        """Check if the session is initialized"""
        return cls._instance is not None and cls._instance._session is not None

class TTSResponseCache:
    """
    Simple cache for TTS responses to avoid redundant API calls.
    Caches responses for common phrases to improve responsiveness.
    """
    _instance: Optional["TTSResponseCache"] = None
    _lock = asyncio.Lock()
    
    def __init__(self):
        self._cache: Dict[str, Tuple[bytes, float]] = {}
        self._max_size = 50  # Maximum number of cached items
        self._ttl = 3600     # Time to live in seconds (1 hour)
        logger.info("Initialized TTS response cache")
    
    @classmethod
    async def get_instance(cls) -> "TTSResponseCache":
        """Get the singleton instance, creating it if necessary"""
        async with cls._lock:
            if cls._instance is None:
                cls._instance = TTSResponseCache()
            return cls._instance
    
    async def get(self, text: str) -> Optional[bytes]:
        """Get cached audio data for the given text if available"""
        if text in self._cache:
            data, timestamp = self._cache[text]
            # Check if entry is still valid
            if time.time() - timestamp < self._ttl:
                logger.debug(f"TTS cache hit for '{text[:20]}...'")
                return data
            else:
                # Remove expired entry
                del self._cache[text]
        return None
    
    async def set(self, text: str, data: bytes) -> None:
        """Store audio data for the given text"""
        # Implement cache size management
        if len(self._cache) >= self._max_size:
            # Remove oldest entry
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
            del self._cache[oldest_key]
        
        # Store new entry
        self._cache[text] = (data, time.time())
        logger.debug(f"Cached TTS response for '{text[:20]}...'")
    
    async def clear(self) -> None:
        """Clear the cache"""
        self._cache.clear()
        logger.info("Cleared TTS response cache")

# Function to register cleanup on application exit
def register_http_client_cleanup():
    """
    Register the HTTP client cleanup with the application shutdown handlers.
    This ensures connections are properly closed when the app exits.
    """
    from PySide6.QtCore import QCoreApplication
    
    async def cleanup():
        await SharedHTTPClient.close()
    
    # Connect to aboutToQuit signal
    app = QCoreApplication.instance()
    if app:
        app.aboutToQuit.connect(lambda: asyncio.create_task(cleanup()))
        logger.info("Registered HTTP client cleanup with application") 