#!/usr/bin/env python3
"""
Test script to benchmark the optimized async weather fetcher.
This script compares the performance of sequential vs. concurrent API requests.
"""

import asyncio
import time
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

async def run_benchmark():
    """
    Run benchmarks to compare optimized vs. non-optimized approaches.
    """
    from backend.weather.fetcher import fetch_weather_data, close_http_client
    from backend.weather.openweather_fetcher import fetch_openweather_data
    
    # Define test locations (lat/lon pairs)
    test_locations = [
        ("28.5988", "-81.3583"),  # Winter Park, FL
        ("40.7128", "-74.0060"),  # New York City
        ("34.0522", "-118.2437"), # Los Angeles
        ("41.8781", "-87.6298"),  # Chicago
        ("29.7604", "-95.3698"),  # Houston
    ]
    
    # Test 1: Sequential requests (simulating non-optimized approach)
    logger.info("Starting sequential requests benchmark...")
    start_time = time.time()
    
    for lat, lon in test_locations:
        logger.info(f"Fetching data for location: {lat}, {lon}")
        weather_data = await fetch_weather_data(lat, lon)
        logger.info(f"NWS data fetched: {'Success' if weather_data else 'Failed'}")
        
        ow_data = await fetch_openweather_data(lat, lon)
        logger.info(f"OpenWeatherMap data fetched: {'Success' if ow_data else 'Failed'}")
    
    sequential_time = time.time() - start_time
    logger.info(f"Sequential requests completed in {sequential_time:.2f} seconds")
    
    # Test 2: Concurrent requests (using our optimized approach)
    logger.info("Starting concurrent requests benchmark...")
    start_time = time.time()
    
    # Create tasks for all locations
    nws_tasks = [fetch_weather_data(lat, lon) for lat, lon in test_locations]
    ow_tasks = [fetch_openweather_data(lat, lon) for lat, lon in test_locations]
    
    # Run all tasks concurrently
    all_results = await asyncio.gather(*nws_tasks, *ow_tasks, return_exceptions=True)
    
    # Count successful results
    nws_results = all_results[:len(test_locations)]
    ow_results = all_results[len(test_locations):]
    
    nws_success = sum(1 for r in nws_results if r and not isinstance(r, Exception))
    ow_success = sum(1 for r in ow_results if r and not isinstance(r, Exception))
    
    logger.info(f"NWS successful fetches: {nws_success}/{len(test_locations)}")
    logger.info(f"OpenWeatherMap successful fetches: {ow_success}/{len(test_locations)}")
    
    concurrent_time = time.time() - start_time
    logger.info(f"Concurrent requests completed in {concurrent_time:.2f} seconds")
    
    # Calculate speedup
    speedup = sequential_time / concurrent_time if concurrent_time > 0 else float('inf')
    logger.info(f"Speedup from concurrent execution: {speedup:.2f}x")
    
    # Ensure we close the HTTP client
    await close_http_client()

if __name__ == "__main__":
    # Run the benchmark
    asyncio.run(run_benchmark()) 