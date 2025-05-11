#!/usr/bin/env python3
import sys
import asyncio
import signal
import os
import logging
from pathlib import Path
from PySide6.QtQml import QQmlApplicationEngine, qmlRegisterSingletonInstance, QQmlComponent
from PySide6.QtCore import QTimer, Qt, QObject, Slot, Property
from PySide6.QtGui import QGuiApplication
from PySide6.QtWebEngineQuick import QtWebEngineQuick
import PySide6
from frontend.config_manager import ConfigManager
from frontend.logic.chat_controller import ChatController
from frontend.theme_manager import ThemeManager
from frontend.settings_service import SettingsService
from frontend.error_handler import error_handler_instance, ErrorHandler
from frontend.photo_controller import PhotoController
from frontend.logic.calendar_controller import CalendarController
from frontend.utils.markdown_utils import markdown_utils
# Import the new AlarmController v2 instead of the old one
from frontend.logic.alarm_controller_v2 import AlarmController
from frontend.logic.time_context_provider import TimeContextProvider
from frontend.logic.audio_manager import AudioManager
# Import the new TimerController
from frontend.logic.timer_controller import TimerController
# Import the TimerCommandProcessor
from frontend.logic.timer_command_processor import TimerCommandProcessor
# Import the new AlarmCommandProcessor
from frontend.logic.alarm_command_processor import AlarmCommandProcessor
# Import the new NavigationController
from frontend.logic.navigation_controller import NavigationController
# Import config functions
from frontend.config import set_app_instance

# Display PySide6 version for debugging
print(f"Using PySide6 version: {PySide6.__version__}")

# Define app as a module-level variable so it's accessible outside of main()
app = None


# Add a new path provider class
class PathProvider(QObject):
    def __init__(self):
        super().__init__()
        self._base_path = str(Path(__file__).resolve().parent.parent)
        logger.info(f"Base application path: {self._base_path}")

    @Property(str, constant=True) # type: ignore
    def basePath(self):
        return self._base_path

    @Slot(str, result=str)
    def getAbsolutePath(self, relativePath):
        """Convert a relative path to an absolute path"""
        if relativePath.startswith("/"):
            return relativePath  # Already absolute
        return str(Path(self._base_path) / relativePath)


# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("frontend.config")
logger.setLevel(logging.DEBUG)  # Set to DEBUG for more information

# Add a console handler to ensure logs are visible
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
console_handler.setLevel(logging.DEBUG)
root_logger = logging.getLogger()
root_logger.addHandler(console_handler)

# Set up specific loggers for our key components
alarm_logger = logging.getLogger("frontend.logic.alarm_command_processor")
alarm_logger.setLevel(logging.DEBUG)
controller_logger = logging.getLogger("frontend.logic.alarm_controller_v2")
controller_logger.setLevel(logging.DEBUG)
manager_logger = logging.getLogger("utils.alarm_manager_v2")
manager_logger.setLevel(logging.DEBUG)
navigation_logger = logging.getLogger("frontend.logic.navigation_controller")
navigation_logger.setLevel(logging.DEBUG)


def main():
    global app  # Use the global app variable
    
    # Set environment variable to allow loading local files via XMLHttpRequest
    os.environ["QML_XHR_ALLOW_FILE_READ"] = "1"
    logger.info("Enabled QML_XHR_ALLOW_FILE_READ for local file access")

    # Enable touch input
    app = QGuiApplication(sys.argv)
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True) # type: ignore
    app.setOrganizationName("SmartScreen")
    app.setOrganizationDomain("smartscreen.local")

    # Create an asyncio loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Initialize QtWebEngine before creating QML engine
    QtWebEngineQuick.initialize()

    # --- Configuration Loading ---
    config_manager = ConfigManager()
    # Load STT related configurations
    config_manager.load_module_config(
        module_path="frontend.config",
        module_key="stt",
        config_vars=["STT_CONFIG", "AUDIO_CONFIG", "DEEPGRAM_CONFIG"],
    )
    # Load Server related configurations
    config_manager.load_module_config(
        module_path="frontend.config",
        module_key="server",
        config_vars=["SERVER_HOST", "SERVER_PORT", "WEBSOCKET_PATH", "HTTP_BASE_URL"],
    )
    # Load Chat related configurations
    config_manager.load_module_config(
        module_path="frontend.config", module_key="chat", config_vars=["CHAT_CONFIG"]
    )
    # Load UI related configurations (NEW)
    config_manager.load_module_config(
        module_path="frontend.ui.config",  # Use the new path
        module_key="ui",  # Key for accessing settings
        config_vars=["WINDOW_CONFIG"],  # The variable holding the config dict
    )
    # ----------------------------

    # Create theme manager instance
    theme_manager = ThemeManager()
    # Make theme_manager globally accessible
    app.theme_manager = theme_manager # type: ignore

    # Create settings service instance
    settings_service = SettingsService()

    # --- Create Singleton Instances ---
    # Create the single ChatController instance
    chat_controller_instance = ChatController()

    # Create the single PhotoController instance
    photo_controller_instance = PhotoController()

    # Create the single CalendarController instance
    calendar_controller_instance = CalendarController()
    
    # Create the single AlarmController instance
    alarm_controller_instance = AlarmController()
    
    # Create the single TimeContextProvider instance via ChatController
    time_context_provider_instance = chat_controller_instance.time_context_provider
    
    # Create the single AudioManager instance
    audio_manager_instance = AudioManager()
    
    # Create the single NavigationController instance
    navigation_controller_instance = NavigationController()
    
    # Create the single TimerController instance
    timer_controller_instance = TimerController(navigation_controller_instance)
    
    # Create the TimerCommandProcessor and connect it to the TimerController
    timer_command_processor_instance = TimerCommandProcessor(timer_controller_instance)
    
    # Create the AlarmCommandProcessor and connect it to the AlarmController
    alarm_command_processor_instance = AlarmCommandProcessor(alarm_controller_instance)
    
    # Set the navigation controller for AlarmCommandProcessor
    alarm_command_processor_instance.set_navigation_controller(navigation_controller_instance)
    
    # Connect NavigationController to ChatController for processing navigation commands
    chat_controller_instance.navigation_controller = navigation_controller_instance
    
    # Connect TimerCommandProcessor to ChatController for processing timer commands
    chat_controller_instance.timer_command_processor = timer_command_processor_instance
    
    # Connect AlarmCommandProcessor to ChatController for processing alarm commands
    chat_controller_instance.alarm_command_processor = alarm_command_processor_instance
    
    # Store instance references on the app object for direct access
    app.timer_controller_instance = timer_controller_instance
    app.chat_controller_instance = chat_controller_instance
    app.navigation_controller_instance = navigation_controller_instance
    app.timer_command_processor_instance = timer_command_processor_instance
    app.alarm_command_processor_instance = alarm_command_processor_instance
    
    # Register app instance in config for global access
    set_app_instance(app)
    
    # ----------------------------------

    # --- Register QML Types and Singletons ---
    # Register ThemeManager as a singleton
    qmlRegisterSingletonInstance(
        ThemeManager, "MyTheme", 1, 0, "ThemeManager", theme_manager # type: ignore
    )

    # Register SettingsService as a singleton
    qmlRegisterSingletonInstance(
        SettingsService, "MyServices", 1, 0, "SettingsService", settings_service # type: ignore
    )

    # Register ErrorHandler as a singleton
    qmlRegisterSingletonInstance(
        ErrorHandler, "MyServices", 1, 0, "ErrorHandler", error_handler_instance # type: ignore
    )

    # Register ChatController instance as a singleton
    qmlRegisterSingletonInstance(
        ChatController, "MyServices", 1, 0, "ChatService", chat_controller_instance # type: ignore
    )

    # Register PhotoController instance as a singleton
    qmlRegisterSingletonInstance(
        PhotoController,
        "MyServices",
        1,
        0,
        "PhotoController", # type: ignore
        photo_controller_instance,
    )

    # Create PathProvider instance
    path_provider = PathProvider()

    # Register PathProvider as a singleton
    qmlRegisterSingletonInstance(
        PathProvider, "MyServices", 1, 0, "PathProvider", path_provider # type: ignore
    )

    # Register CalendarController instance as a singleton
    qmlRegisterSingletonInstance(
        CalendarController,
        "MyServices",
        1,
        0,
        "CalendarController", # Name exposed to QML # type: ignore
        calendar_controller_instance,
    )

    # Register MarkdownUtils instance as a singleton
    qmlRegisterSingletonInstance(
        QObject,  # Base type
        "MyUtils",
        1,
        0,
        "MarkdownUtils",  # Name exposed to QML # type: ignore
        markdown_utils,
    )
    
    # Register AlarmController instance as a singleton
    qmlRegisterSingletonInstance(
        AlarmController,
        "MyServices",
        1,
        0,
        "AlarmController",  # Name exposed to QML # type: ignore
        alarm_controller_instance,
    )
    
    # Register TimeContextProvider as a singleton
    qmlRegisterSingletonInstance(
        TimeContextProvider,
        "MyServices",
        1,
        0,
        "TimeContextProvider",  # Name exposed to QML # type: ignore
        time_context_provider_instance,
    )

    # Register AudioManager as a singleton
    qmlRegisterSingletonInstance(
        AudioManager,
        "MyServices",
        1,
        0,
        "AudioManager",
        audio_manager_instance,
    )

    # Register TimerController instance as a singleton
    qmlRegisterSingletonInstance(
        TimerController,
        "MyServices",
        1,
        0,
        "TimerController",  # Name exposed to QML
        timer_controller_instance,
    )

    # Register NavigationController instance as a singleton
    qmlRegisterSingletonInstance(
        NavigationController,
        "MyServices",
        1,
        0,
        "NavigationController",  # Name exposed to QML
        navigation_controller_instance,
    )
    # -----------------------------------------

    # Create QML engine
    engine = QQmlApplicationEngine()

    # Add import paths for base components
    engine.addImportPath("frontend/qml")
    engine.addImportPath("frontend/qml/components")
    engine.addImportPath("frontend/qml/utils")
    
    # Add the path of our custom QML components - this is the most critical part
    qml_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "qml")
    engine.addImportPath(qml_path)
    logger.info(f"Added QML import path: {qml_path}")

    # Check PySide6 version and add QtQuick.Effects module if available
    try:
        pyside_version = tuple(map(int, PySide6.__version__.split(".")))
        major, minor, patch = pyside_version[:3]

        # Enable QtQuick.Effects for PySide6 6.5+
        if major > 6 or (major == 6 and minor >= 5):
            logger.info("PySide6 6.5+ detected, enabling QtQuick.Effects")
            # Add any special configuration for QtQuick.Effects if needed
        else:
            logger.warning(
                f"PySide6 version {PySide6.__version__} detected. "
                f"QtQuick.Effects requires PySide6 6.5+. Some visual effects may not work."
            )
    except Exception as e:
        logger.error(f"Error checking PySide6 version: {e}")

    # Load QML from the correct relative path (from project root)
    engine.load("frontend/qml/MainWindow.qml")

    if not engine.rootObjects():
        logger.error("Failed to load QML. Exiting.")
        sys.exit(-1)

    # Make sure the root window is visible
    root_objects = engine.rootObjects()
    if root_objects:
        logger.info(f"Number of root objects loaded: {len(root_objects)}")
        main_window = root_objects[0]
        main_window.setVisible(True) # type: ignore
        logger.info(f"Main window size: {main_window.width()}x{main_window.height()}") # type: ignore

    # Set up a timer to process asyncio events
    timer = QTimer()
    timer.setInterval(10)  # 10ms

    # Process asyncio events on timer tick
    def process_asyncio_events():
        loop.call_soon(loop.stop)
        loop.run_forever()

    timer.timeout.connect(process_asyncio_events)
    timer.start()

    # Define signal handler for graceful shutdown
    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}, initiating graceful shutdown...")
        app.quit()

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start the application event loop
    exit_code = app.exec()
    
    # Clean up after the application exits
    logger.info("Application event loop exited. Cleaning up...")
    
    # Scheduled cleanup tasks using asyncio
    try:
        # Handle chat controller cleanup
        loop.run_until_complete(chat_controller_instance.cleanup())
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
    
    # Exit the application with the exit code
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
