"""
Examples for using the tool orchestrator with parallel and sequential execution.
"""
import asyncio
import logging
from typing import Dict, List, Any

from backend.tools.registry import execute_tools_parallel, execute_tools_with_dependencies

logger = logging.getLogger(__name__)

async def example_parallel_execution():
    """
    Example of executing multiple tools in parallel.
    """
    # Define tool calls to execute in parallel
    tool_calls = [
        {
            "name": "navigate_to_screen",
            "params": {
                "screen": "weather"
            }
        },
        {
            "name": "get_weather_current",
            "params": {
                "lat": "28.5988",
                "lon": "-81.3583",
                "units": "imperial",
                "lang": "en",
                "detail_level": "simple"
            }
        }
    ]
    
    # Execute tools in parallel
    results = await execute_tools_parallel(tool_calls)
    
    # Log results
    logger.info("Parallel execution results:")
    for tool_name, result in results.items():
        logger.info(f"{tool_name}: {result}")
    
    return results

async def example_sequential_execution():
    """
    Example of executing tools sequentially with dependencies.
    """
    # Define tool calls with dependencies
    tool_calls = [
        {
            "name": "get_weather_current",
            "params": {
                "lat": "28.5988",
                "lon": "-81.3583",
                "units": "imperial",
                "lang": "en",
                "detail_level": "simple"
            },
            "provides": ["current_weather"]  # This tool provides weather data
        },
        {
            "name": "navigate_to_screen",
            "params": {
                "screen": "weather"
            },
            "depends_on": ["get_weather_current"],  # This tool depends on weather data
            "provides": ["navigation_result"]
        }
    ]
    
    # Execute tools with dependency handling
    results = await execute_tools_with_dependencies(tool_calls)
    
    # Log results
    logger.info("Sequential execution results:")
    for tool_name, result in results.items():
        logger.info(f"{tool_name}: {result}")
    
    return results

async def example_combined_execution():
    """
    Example of a more complex execution with both parallel and sequential steps.
    Shows how navigation can run in parallel while other tools have dependencies.
    """
    # Define tool calls with mixed dependencies
    tool_calls = [
        # First batch (can run in parallel)
        {
            "name": "navigate_to_screen",
            "params": {
                "screen": "weather"
            },
            "provides": ["navigation_result"],
            "depends_on": []  # No dependencies
        },
        {
            "name": "get_weather_current",
            "params": {
                "lat": "28.5988",
                "lon": "-81.3583",
                "units": "imperial",
                "lang": "en",
                "detail_level": "simple"
            },
            "provides": ["current_weather"],
            "depends_on": []  # No dependencies
        },
        # Second batch (depends on first batch)
        {
            "name": "get_weather_forecast",  # Assuming this tool exists
            "params": {
                "lat": "28.5988",
                "lon": "-81.3583",
                "units": "imperial"
            },
            "provides": ["forecast_data"],
            "depends_on": ["get_weather_current"]  # Depends on current weather
        }
    ]
    
    # Execute tools with dependency handling
    results = await execute_tools_with_dependencies(tool_calls)
    
    # Log results
    logger.info("Combined execution results:")
    for tool_name, result in results.items():
        logger.info(f"{tool_name}: {result}")
    
    return results

# For testing and documentation
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Run examples
    asyncio.run(example_parallel_execution())
    asyncio.run(example_sequential_execution())
    asyncio.run(example_combined_execution()) 