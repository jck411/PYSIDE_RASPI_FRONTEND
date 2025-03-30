#!/usr/bin/env python3
import asyncio
import logging

from PySide6.QtCore import QObject, Signal, Slot

from frontend.config import logger, STT_CONFIG
from frontend.stt.deepgram_stt import DeepgramSTT
from frontend.config_manager import ConfigManager

class SpeechManager(QObject):
    """
    Manages speech recognition and synthesis states.
    """
    # Signals
    sttTextReceived = Signal(str)           # Emitted when partial or final STT text arrives
    sttStateChanged = Signal(bool)          # Emitted when STT state toggles
    sttInputTextReceived = Signal(str)      # Emitted when complete STT utterance should be set as input text
    autoSubmitUtterance = Signal(str)       # Emitted when a complete utterance should be auto-submitted to chat

    def __init__(self, parent=None):
        super().__init__(parent)
        self.stt_listening = False
        self.is_toggling_stt = False
        self.tts_audio_playing = False
        
        # Initialize configuration manager
        self.config_manager = ConfigManager()
        
        # Initialize Deepgram STT
        self.frontend_stt = DeepgramSTT()

        # Connect to STT signals
        self.frontend_stt.transcription_received.connect(self.handle_interim_stt_text)
        self.frontend_stt.complete_utterance_received.connect(self.handle_frontend_stt_text)
        self.frontend_stt.state_changed.connect(self.handle_frontend_stt_state)
        
        logger.info("[SpeechManager] Initialized with Deepgram STT")

    def handle_interim_stt_text(self, text):
        """Handle partial transcription updates"""
        if text.strip():
            logger.debug(f"[SpeechManager] Interim STT text: {text}")
            self.sttTextReceived.emit(text)

    def handle_frontend_stt_text(self, text):
        """Handle final transcription results"""
        if text.strip():
            logger.info(f"[SpeechManager] Complete utterance: {text}")
            self.sttTextReceived.emit(text)
            
            # Check if we should auto-submit complete utterances
            # Use ConfigManager to get the most up-to-date setting value
            auto_submit = self.config_manager.get_config("stt.STT_CONFIG.auto_submit_utterances", False)
            logger.info(f"[SpeechManager] Auto-submit setting value: {auto_submit}")
            
            if auto_submit:
                logger.info(f"[SpeechManager] Auto-submitting utterance to chat: {text}")
                self.autoSubmitUtterance.emit(text)
            else:
                # Default behavior: just populate the input field
                logger.info(f"[SpeechManager] Sending utterance to input field: {text}")
                self.sttInputTextReceived.emit(text)

    def handle_frontend_stt_state(self, is_listening):
        """Handle STT state changes"""
        try:
            self.stt_listening = is_listening
            self.sttStateChanged.emit(is_listening)
            logger.info(f"[SpeechManager] STT state changed: {is_listening}")
        except asyncio.exceptions.CancelledError:
            logger.warning("[SpeechManager] STT state update task was cancelled - expected during shutdown")
        except Exception as e:
            logger.error(f"[SpeechManager] Error updating STT state: {e}")

    @Slot()
    def toggle_stt(self):
        """
        Toggles STT capture using the Deepgram STT implementation.
        """
        if self.is_toggling_stt:
            return
        self.is_toggling_stt = True
        try:
            if hasattr(self.frontend_stt, 'toggle'):
                self.frontend_stt.toggle()
            else:
                logger.error("[SpeechManager] Frontend STT implementation missing toggle method")
                self.handle_frontend_stt_state(not self.stt_listening)
        except asyncio.exceptions.CancelledError:
            logger.warning("[SpeechManager] STT toggle task was cancelled - expected during shutdown")
        except Exception as e:
            logger.error(f"[SpeechManager] Error toggling STT: {e}")
            self.handle_frontend_stt_state(not self.stt_listening)
        finally:
            self.is_toggling_stt = False
    
    def is_stt_enabled(self):
        """Returns whether STT is currently enabled"""
        return self.frontend_stt.is_enabled

    def set_paused(self, paused):
        """Pause or resume STT without changing the enabled state"""
        self.frontend_stt.set_paused(paused)
        logger.info(f"[SpeechManager] STT paused: {paused}")

    def cleanup(self):
        """Clean up resources"""
        if hasattr(self.frontend_stt, 'stop'):
            self.frontend_stt.stop()
            logger.info("[SpeechManager] Stopped Deepgram STT")