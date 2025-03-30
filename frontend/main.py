#!/usr/bin/env python3
import sys
import asyncio
import signal
from PySide6.QtWidgets import QApplication
from PySide6.QtQml import QQmlApplicationEngine, qmlRegisterType, qmlRegisterSingletonInstance
from PySide6.QtCore import QTimer, Qt
from frontend.config import logger
from frontend.config_manager import ConfigManager
from frontend.logic.chat_controller import ChatController
from frontend.theme_manager import ThemeManager
from frontend.settings_service import SettingsService
from frontend.error_handler import error_handler_instance, ErrorHandler

def main():
    # Enable touch input
    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    
    # Create an asyncio loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # --- Configuration Loading --- 
    config_manager = ConfigManager()
    # Load STT related configurations
    config_manager.load_module_config(
        module_path='frontend.config', 
        module_key='stt',
        config_vars=['STT_CONFIG', 'AUDIO_CONFIG', 'DEEPGRAM_CONFIG']
    )
    # Load Server related configurations
    config_manager.load_module_config(
        module_path='frontend.config', 
        module_key='server',
        config_vars=['SERVER_HOST', 'SERVER_PORT', 'WEBSOCKET_PATH', 'HTTP_BASE_URL']
    )
    # ----------------------------

    # Create theme manager instance
    theme_manager = ThemeManager()
    
    # Create settings service instance
    settings_service = SettingsService()
    
    # Register ChatController as ChatLogic for QML compatibility
    qmlRegisterType(ChatController, "MyScreens", 1, 0, "ChatLogic")
    
    # Register ThemeManager as a singleton
    qmlRegisterSingletonInstance(ThemeManager, "MyTheme", 1, 0, "ThemeManager", theme_manager)
    
    # Register SettingsService as a singleton
    qmlRegisterSingletonInstance(SettingsService, "MyServices", 1, 0, "SettingsService", settings_service)
    
    # Register ErrorHandler as a singleton
    qmlRegisterSingletonInstance(ErrorHandler, "MyServices", 1, 0, "ErrorHandler", error_handler_instance)
    
    # Create QML engine
    engine = QQmlApplicationEngine()
    
    # Add import paths for base components
    engine.addImportPath("frontend/qml")
    
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
        main_window.setVisible(True)
        logger.info(f"Main window size: {main_window.width()}x{main_window.height()}")
    
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
        app.quit()
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Start the Qt event loop
    exit_code = app.exec()
    
    # Cleanup
    chat_controller = None
    for obj in engine.rootObjects():
        chat_controller = obj.findChild(ChatController)
        if chat_controller:
            chat_controller.cleanup()
            break
    
    loop.close()
    logger.info("Application closed.")
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
