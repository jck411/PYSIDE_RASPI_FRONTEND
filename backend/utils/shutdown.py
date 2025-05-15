"""
Utility functions for handling application shutdown and cleanup tasks.
"""

import logging
import asyncio
from typing import List, Callable, Awaitable, Any

logger = logging.getLogger(__name__)

# List of cleanup functions to run on shutdown
_cleanup_tasks: List[Callable[[], Awaitable[Any]]] = []

def register_cleanup_task(func: Callable[[], Awaitable[Any]]) -> None:
    """
    Register an async function to be called during application shutdown.
    
    Args:
        func: Async function to call during shutdown
    """
    if func not in _cleanup_tasks:
        _cleanup_tasks.append(func)
        logger.info(f"Registered cleanup task: {func.__name__}")

async def run_cleanup_tasks() -> None:
    """
    Run all registered cleanup tasks.
    Should be called during application shutdown.
    """
    if not _cleanup_tasks:
        logger.info("No cleanup tasks registered")
        return
        
    logger.info(f"Running {len(_cleanup_tasks)} cleanup tasks")
    
    for task in _cleanup_tasks:
        try:
            logger.info(f"Running cleanup task: {task.__name__}")
            await task()
        except Exception as e:
            logger.error(f"Error in cleanup task {task.__name__}: {e}")
    
    logger.info("All cleanup tasks completed") 