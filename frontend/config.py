#!/usr/bin/env python3
"""
Configuration settings for the PySide Raspberry Pi Frontend

This module provides centralized configuration for all aspects of the application,
including server settings, logging, and speech-to-text functionality.
"""
import logging
from typing import Dict, Any

# ========================
# SERVER CONFIGURATION
# ========================
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8000
WEBSOCKET_PATH = "/ws/chat"
HTTP_BASE_URL = f"http://{SERVER_HOST}:{SERVER_PORT}"

# ========================
# SPEECH-TO-TEXT CONFIGURATION
# ========================
STT_CONFIG: Dict[str, Any] = {
    'enabled': False,      # Global switch to enable/disable STT
    'auto_start': False,   # Whether to start STT automatically on initialization
    'use_keepalive': True, # Whether to use KeepAlive for pausing/resuming during TTS
    'auto_submit_utterances': True, # Whether to automatically submit complete utterances directly to chat
    'inactivity_timeout_ms': 10000, # Milliseconds of silence before automatically stopping STT (0 to disable)
}

# Audio capture configuration
AUDIO_CONFIG = {
    'channels': 1,
    'sample_rate': 16000,
    'block_size': 4000,
    'dtype': 'float32',    # Used by sounddevice
}

# Deepgram configuration
DEEPGRAM_CONFIG = {
    # Core settings
    'language': 'en-US',
    'model': 'nova-3',
    
    # Audio settings
    'encoding': 'linear16',
    'channels': 1,
    'sample_rate': 16000,
    
    # Transcription settings
    'smart_format': True,
    'interim_results': True,
    'endpointing': 500,
    'punctuate': True,
    'filler_words': True,
    'vad_events': True,
    
    # Connection settings
    'keepalive': True,            # Enable KeepAlive in the Deepgram connection
    'keepalive_timeout': 30       # Seconds before the connection times out when in KeepAlive mode
}

# ========================
# LOGGING CONFIGURATION
# ========================
def setup_logger(name=__name__, level=logging.INFO):
    """
    Set up a logger with consistent formatting
    
    Args:
        name: Logger name, defaults to the current module name
        level: Logging level, defaults to INFO
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    # Clear any existing handlers to prevent duplicate logs
    logger.handlers = []
    # Only add a handler if none exists
    if not logger.handlers:
        ch = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    # Prevent propagation to root logger to avoid duplicate logs
    logger.propagate = False
    return logger

# Create default logger
logger = setup_logger(level=logging.INFO)

# ========================
# CHAT CONFIGURATION
# ========================
CHAT_CONFIG: Dict[str, Any] = {
    'show_input_box': True,      # Whether to show the text input field on the chat screen
}
