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
from frontend.logic.calendar_controller import CalendarController # Add import
from frontend.utils.markdown_utils import markdown_utils  # Add markdown utils import
from frontend.logic.alarm_controller import AlarmController  # Add alarm controller import

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
logger.setLevel(logging.WARNING)  # Reduce log verbosity for this specific logger


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

    # Handle graceful shutdown
    def signal_handler(sig, frame):
        logger.info("Signal received => shutting down.")
        app.quit() # type: ignore

    signal.signal(signal.SIGINT, signal_handler)

    # Start the Qt event loop
    exit_code = app.exec()

    # Cleanup
    # chat_controller = None # REMOVE: We have the instance directly
    # for obj in engine.rootObjects():
    #     chat_controller = obj.findChild(ChatController)
    #     if chat_controller:
    #         chat_controller.cleanup()
    #         break
    # Directly cleanup the singleton instance
    if chat_controller_instance:
        logger.info("Cleaning up ChatController singleton...")
        chat_controller_instance.cleanup()

    loop.close()
    logger.info("Application closed.")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
