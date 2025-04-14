#!/usr/bin/env python3
import os
import openai
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()


CONFIG: Dict[str, Any] = {
    "API_SETTINGS": {"API_HOST": "openai"},
    "API_SERVICES": {
        "openai": {"BASE_URL": "https://api.openai.com/v1", "MODEL": "gpt-4o-mini"},
        "openrouter": {
            "BASE_URL": "https://openrouter.ai/api/v1",
            "MODEL": "meta-llama/llama-3.1-70b-instruct",
        },
    },
    "SYSTEM_PROMPT": {
        "CONTENT": """You are a sarcastic but helpful assistant that uses short replies. Users live in Orlando, FL.

IMPORTANT TIME HANDLING INSTRUCTIONS:
1. ALWAYS use the get_time() function to check the current date and time when questions involve:
   - Current time, date, day of week, or month
   - Days remaining in current month or year
   - Schedules, deadlines, or time-sensitive information
   - Anything related to "today", "yesterday", "tomorrow", or calendar events
2. Never assume you know the current time without checking
3. Even for simple questions like "what time is it" or "how many days until the end of the month", always use get_time()
4. When users ask about "days left", "time remaining", or similar time calculations, use get_time() first

Remember that you have no knowledge of the current time unless you check it using the tools provided."""
    },
    "GENERAL_AUDIO": {
        "TTS_ENABLED": True,  # Set to False by default
    },
    "PROCESSING_PIPELINE": {
        "USE_SEGMENTATION": True,
        "DELIMITERS": ["\n", ". ", "? ", "! ", "* "],
        "CHARACTER_MAXIMUM": 50,  # will only segment for the initial characters listed here, the rest will just stream
    },
    "TTS_MODELS": {
        "PROVIDER": "azure",  # "azure" or "openai"
        "OPENAI_TTS": {
            "TTS_CHUNK_SIZE": 8192,
            "TTS_SPEED": 1.0,
            "TTS_VOICE": "alloy",
            "TTS_MODEL": "tts-1",
            "AUDIO_RESPONSE_FORMAT": "pcm",
            "AUDIO_FORMAT_RATES": {"pcm": 24000, "mp3": 44100, "wav": 48000},
            "PLAYBACK_RATE": 24000,
            "BUFFER_SIZE": 16384,
        },
        "AZURE_TTS": {
            "TTS_SPEED": "0%",
            "TTS_VOICE": "en-US-AlloyTurboMultilingualNeural",  # en-US-AlloyTurboMultilingualNeural #en-US-Alloy:DragonHDLatestNeural
            "SPEECH_SYNTHESIS_RATE": "0%",
            "AUDIO_FORMAT": "Raw24Khz16BitMonoPcm",
            "AUDIO_FORMAT_RATES": {
                "Raw8Khz16BitMonoPcm": 8000,
                "Raw16Khz16BitMonoPcm": 16000,
                "Raw24Khz16BitMonoPcm": 24000,
                "Raw44100Hz16BitMonoPcm": 44100,
                "Raw48Khz16BitMonoPcm": 48000,
            },
            "PLAYBACK_RATE": 24000,
            "ENABLE_PROFANITY_FILTER": False,
            "STABILITY": 0,
            "PROSODY": {"rate": "1.0", "pitch": "0%", "volume": "default"},
        },
    },
    "AUDIO_SETTINGS": {
        "FORMAT": 16,
        "CHANNELS": 1,
        "RATE": 24000,
    },
    "LOGGING": {
        "PRINT_SEGMENTS": True,
        "PRINT_TOOL_CALLS": True,
        "PRINT_FUNCTION_CALLS": True,
    },
}


def setup_chat_client():
    api_host = CONFIG["API_SETTINGS"]["API_HOST"].lower()
    if api_host == "openai":
        client = openai.AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=CONFIG["API_SERVICES"]["openai"]["BASE_URL"],
        )
        deployment_name = CONFIG["API_SERVICES"]["openai"]["MODEL"]
    elif api_host == "openrouter":
        client = openai.AsyncOpenAI(
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url=CONFIG["API_SERVICES"]["openrouter"]["BASE_URL"],
        )
        deployment_name = CONFIG["API_SERVICES"]["openrouter"]["MODEL"]
    else:
        raise ValueError(f"Unsupported API_HOST: {api_host}")
    return client, deployment_name
