# Time Context Management

The application provides time awareness for LLM interactions, ensuring that the AI assistant has access to accurate current time information without explicitly asking:

## TimeContextManager
A backend component in `backend/tools/time.py` that manages time context updates:
- Regularly updates current time information based on location coordinates
- Uses an event-driven architecture with callbacks for time updates
- Automatically refreshes time information at configurable intervals (default: every 60 seconds)
- Provides timezone-aware time based on geolocation coordinates
- Implemented as an asyncio-based service that runs in the background

## Comprehensive Time Tool
Instead of injecting time context into messages, the system uses a tool-based approach:
- The `get_time()` function provides comprehensive time information for any query
- Returns detailed information including current time, date, day of week, month, year
- Provides calendar-related calculations like days until end of month/year
- Determines time of day (morning, afternoon, evening, night)
- Includes information about yesterday, today, and tomorrow
- Formats nicely summarized time information for easy reference

## System Prompt Time Instructions
The system uses explicit instructions in the system prompt:
- Instructs the LLM to always check the current time for any time-related queries
- Lists specific scenarios when the time function should be used
- Prevents the LLM from guessing or assuming time information without checking
- Makes time awareness automatic for the AI assistant

This implementation ensures the AI assistant always provides accurate time information for any time-related query (not just predefined questions). The approach is robust to format constraints and allows the LLM to access time information on demand while following the expected messaging format. 