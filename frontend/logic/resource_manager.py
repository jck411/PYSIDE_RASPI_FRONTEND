#!/usr/bin/env python3
import asyncio
import aiohttp

from frontend.config import HTTP_BASE_URL, logger


class ResourceManager:
    """
    Unified manager that handles both asynchronous tasks and service-level operations.
    Combines the functionality previously split between TaskManager and ServiceManager.
    """

    def __init__(self, loop=None):
        self.tasks = {}
        self._loop = loop or asyncio.get_event_loop()
        logger.info("[ResourceManager] Initialized")

    #
    # Task Management Functions (previously in TaskManager)
    #

    def create_task(self, name, coro):
        """
        Create and track a named task

        Args:
            name: String identifier for the task
            coro: Coroutine to execute

        Returns:
            Task object
        """
        task = self._loop.create_task(coro)
        self.tasks[name] = task
        logger.debug(f"[ResourceManager] Created task: {name}")
        return task

    def cancel_task(self, name):
        """
        Cancel a specific task by name

        Args:
            name: String identifier for the task

        Returns:
            Boolean indicating if task was found and cancelled
        """
        if name in self.tasks and not self.tasks[name].done():
            self.tasks[name].cancel()
            logger.info(f"[ResourceManager] Cancelled task: {name}")
            return True
        return False

    def cancel_all_tasks(self):
        """
        Cancel all tracked tasks

        Returns:
            Number of tasks cancelled
        """
        count = 0
        for name, task in list(self.tasks.items()):
            if not task.done():
                task.cancel()
                count += 1

        if count > 0:
            logger.info(f"[ResourceManager] Cancelled {count} tasks")
        return count

    def schedule_coroutine(self, coro):
        """
        Schedule a coroutine without tracking it

        Args:
            coro: Coroutine to execute

        Returns:
            Task object
        """
        return self._loop.create_task(coro)

    #
    # Service Management Functions (previously in ServiceManager)
    #

    async def stop_generation(self):
        """Stop ongoing message generation on the server"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{HTTP_BASE_URL}/api/stop-generation") as resp:
                    resp_data = await resp.json()
                    logger.info(
                        f"[ResourceManager] Stop generation response: {resp_data}"
                    )
            return True
        except Exception as e:
            logger.error(f"[ResourceManager] Error stopping generation: {e}")
            return False

    async def stop_all_services(self):
        """Stop all ongoing services on the server side"""
        results = {"generation_stopped": False, "audio_stopped": False}

        try:
            # Create a client session for both requests
            async with aiohttp.ClientSession() as session:
                # Stop audio first
                async with session.post(f"{HTTP_BASE_URL}/api/stop-audio") as resp1:
                    resp1_data = await resp1.json()
                    results["audio_stopped"] = resp1_data.get("success", False)
                    logger.info(f"[ResourceManager] Stop audio response: {resp1_data}")

                # Then stop generation
                async with session.post(
                    f"{HTTP_BASE_URL}/api/stop-generation"
                ) as resp2:
                    resp2_data = await resp2.json()
                    results["generation_stopped"] = resp2_data.get("success", False)
                    logger.info(
                        f"[ResourceManager] Stop generation response: {resp2_data}"
                    )

            return results
        except Exception as e:
            logger.error(f"[ResourceManager] Error stopping services: {e}")
            return results

    def cleanup(self):
        """
        Cancel all tasks and perform cleanup
        """
        cancelled = self.cancel_all_tasks()
        logger.info(f"[ResourceManager] Cleanup complete, cancelled {cancelled} tasks")
