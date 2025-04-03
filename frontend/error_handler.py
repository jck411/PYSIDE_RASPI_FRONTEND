#!/usr/bin/env python3
"""
Centralized error handling for the application.
"""

import logging
import traceback

from PySide6.QtCore import QObject, Signal
from frontend.config import logger  # Use the configured logger


class ErrorHandler(QObject):
    """
    A QObject based singleton class to handle and emit error signals.
    """

    # Signal arguments: error_type (str), user_message (str)
    errorOccurred = Signal(str, str)

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ErrorHandler, cls).__new__(cls)
            # Initialize QObject part only once
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        super().__init__()
        self._initialized = True
        logger.info("[ErrorHandler] Initialized.")

    def handle_error(
        self,
        exception: Exception,
        context: str | None = None,
        level: int = logging.ERROR,
        user_message: str | None = None,
        error_type: str = "General",
    ):
        """
        Logs an exception and potentially emits a signal for the UI.

        Args:
            exception: The exception object caught.
            context: Optional string describing the context where the error occurred.
            level: The logging level to use (e.g., logging.ERROR, logging.WARNING).
            user_message: Optional user-friendly message to show in the UI. If None, signal might not be emitted.
            error_type: A category for the error (e.g., "Connection", "Audio", "Configuration").
        """
        error_log_message = f"Error occurred: {type(exception).__name__}: {exception}"
        if context:
            error_log_message = (
                f"Error occurred in {context}: {type(exception).__name__}: {exception}"
            )

        # Log the main error message
        logger.log(level, error_log_message)

        # Log the full traceback for debugging
        tb_level = logging.DEBUG if level < logging.ERROR else level
        logger.log(tb_level, f"Traceback:\n{traceback.format_exc()}")

        # Emit signal if a user message is provided and the error is significant enough (e.g., ERROR level)
        if user_message and level >= logging.ERROR:
            logger.info(
                f"[ErrorHandler] Emitting error signal: type='{error_type}', message='{user_message}'"
            )
            self.errorOccurred.emit(error_type, user_message)


# Create the singleton instance
error_handler_instance = ErrorHandler()


# Global function remains for convenience, calls the singleton's method
def handle_error(
    exception: Exception,
    context: str | None = None,
    level: int = logging.ERROR,
    user_message: str | None = None,
    error_type: str = "General",
):
    error_handler_instance.handle_error(
        exception, context, level, user_message, error_type
    )


# Example Usage (within an except block):
# try:
#     # some code that might raise an error
#     risky_operation()
# except Exception as e:
#     handle_error(e, context="risky_operation", user_message="Failed to perform the risky operation.", error_type="Operation")
