#!/usr/bin/env python3
"""
Configuration Manager for the PySide Raspberry Pi Frontend

This module provides centralized configuration management, allowing the application
to load, access, and save configuration from various sources including Python modules
and JSON files.
"""

import json
import os
import importlib
from typing import Dict, Any, List, Optional, Union

from frontend.config import logger

class ConfigManager:
    """
    Manages application configuration from various sources.
    
    This class provides a unified interface for accessing configuration values
    from different sources, including Python modules and JSON files. It also
    handles saving configuration changes back to the appropriate location.
    """
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern to ensure only one config manager exists."""
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the configuration manager."""
        if self._initialized:
            return
            
        self._config_cache = {}
        self._file_configs = {}
        self._module_configs = {}
        self._user_config_path = os.path.expanduser("~/.smartscreen_config.json")
        self._load_user_config()
        self._initialized = True
    
    def _load_user_config(self) -> None:
        """Load user configuration from JSON file if it exists."""
        try:
            if os.path.exists(self._user_config_path):
                with open(self._user_config_path, 'r') as f:
                    self._file_configs['user'] = json.load(f)
                    logger.info(f"Loaded user configuration from {self._user_config_path}")
            else:
                self._file_configs['user'] = {}
                logger.info("No user configuration file found, using defaults")
        except Exception as e:
            logger.error(f"Error loading user configuration: {e}")
            self._file_configs['user'] = {}
    
    def _save_user_config(self) -> bool:
        """Save user configuration to JSON file."""
        try:
            with open(self._user_config_path, 'w') as f:
                json.dump(self._file_configs['user'], f, indent=2)
            logger.info(f"Saved user configuration to {self._user_config_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving user configuration: {e}")
            return False
    
    def load_module_config(self, module_path: str, config_vars: List[str]) -> Dict[str, Any]:
        """
        Load configuration from a Python module.
        
        Args:
            module_path: Import path to the module (e.g., 'frontend.stt.config')
            config_vars: List of variable names to extract from the module
            
        Returns:
            Dictionary containing the extracted configuration variables
        """
        try:
            module = importlib.import_module(module_path)
            config_dict = {}
            
            for var_name in config_vars:
                if hasattr(module, var_name):
                    config_dict[var_name] = getattr(module, var_name)
            
            # Store in module configs
            module_key = module_path.split('.')[-1]  # Use last part of path as key
            self._module_configs[module_key] = config_dict
            logger.info(f"Loaded module config from {module_path}: {', '.join(config_vars)}")
            return config_dict
        except Exception as e:
            logger.error(f"Error loading module config {module_path}: {e}")
            return {}
    
    def get_config(self, path: str, default: Any = None) -> Any:
        """
        Get configuration value by path.
        
        The path format is 'source.variable.key', for example:
        - 'stt.STT_CONFIG.enabled' for a module config
        - 'user.theme.is_dark_mode' for a user config
        
        Args:
            path: Configuration path
            default: Default value if path not found
            
        Returns:
            Configuration value or default if not found
        """
        # Check cache first
        if path in self._config_cache:
            return self._config_cache[path]
        
        parts = path.split('.')
        if len(parts) < 2:
            return default
        
        source = parts[0]
        var = parts[1]
        
        # Handle user config
        if source == 'user':
            if var in self._file_configs.get('user', {}):
                config = self._file_configs['user'][var]
                
                # Handle nested access
                if len(parts) > 2:
                    for key in parts[2:]:
                        if isinstance(config, dict) and key in config:
                            config = config[key]
                        else:
                            return default
                
                self._config_cache[path] = config
                return config
            return default
        
        # Check for module overrides first
        if 'module_overrides' in self._file_configs.get('user', {}) and \
           source in self._file_configs['user']['module_overrides'] and \
           var in self._file_configs['user']['module_overrides'][source]:
            
            override = self._file_configs['user']['module_overrides'][source][var]
            
            # Handle nested access for overrides
            if len(parts) > 2:
                for key in parts[2:]:
                    if isinstance(override, dict) and key in override:
                        override = override[key]
                    else:
                        # If we can't find the nested key in the override, 
                        # we'll fall back to the module config
                        break
                else:
                    # If we've traversed all keys successfully, return the override
                    self._config_cache[path] = override
                    return override
            else:
                # Direct access without nested keys
                self._config_cache[path] = override
                return override
        
        # Handle module config - load if needed
        if source not in self._module_configs:
            if source == 'stt':
                self.load_module_config('frontend.config', ['STT_CONFIG', 'AUDIO_CONFIG', 'DEEPGRAM_CONFIG'])
            elif source == 'server':
                self.load_module_config('frontend.config', ['SERVER_HOST', 'SERVER_PORT', 'WEBSOCKET_PATH', 'HTTP_BASE_URL'])
        
        # Get from module config
        if source in self._module_configs and var in self._module_configs[source]:
            config = self._module_configs[source][var]
            
            # Handle nested access
            if len(parts) > 2:
                for key in parts[2:]:
                    if isinstance(config, dict) and key in config:
                        config = config[key]
                    else:
                        return default
            
            self._config_cache[path] = config
            return config
        
        return default
    
    def set_config(self, path: str, value: Any) -> bool:
        """
        Set configuration value by path.
        
        For module configs, this will update the user override in the user config file.
        The original module will not be modified.
        
        Args:
            path: Configuration path
            value: New value to set
            
        Returns:
            True if successful, False otherwise
        """
        parts = path.split('.')
        if len(parts) < 2:
            logger.error(f"Invalid config path: {path}")
            return False
        
        source = parts[0]
        var = parts[1]
        
        # Update cache
        self._config_cache[path] = value
        
        # Handle user config
        if source == 'user':
            if var not in self._file_configs['user']:
                self._file_configs['user'][var] = {}
            
            config = self._file_configs['user'][var]
            
            # Handle nested keys
            if len(parts) > 2:
                for i, key in enumerate(parts[2:-1], 2):
                    if key not in config:
                        config[key] = {}
                    config = config[key]
                
                # Set the final value
                config[parts[-1]] = value
            else:
                # Direct setting
                self._file_configs['user'][var] = value
            
            # Save to file
            return self._save_user_config()
        
        # Handle module config overrides
        if source in self._module_configs:
            # Create override structure in user config
            if 'module_overrides' not in self._file_configs['user']:
                self._file_configs['user']['module_overrides'] = {}
            
            if source not in self._file_configs['user']['module_overrides']:
                self._file_configs['user']['module_overrides'][source] = {}
            
            if var not in self._file_configs['user']['module_overrides'][source]:
                self._file_configs['user']['module_overrides'][source][var] = {}
            
            override = self._file_configs['user']['module_overrides'][source][var]
            
            # Handle nested keys
            if len(parts) > 2:
                for i, key in enumerate(parts[2:-1], 2):
                    if key not in override:
                        override[key] = {}
                    override = override[key]
                
                # Set the final value
                override[parts[-1]] = value
            else:
                # Direct setting
                self._file_configs['user']['module_overrides'][source][var] = value
            
            # Save to file
            return self._save_user_config()
        
        logger.error(f"Unknown config source: {source}")
        return False
    
    def clear_cache(self) -> None:
        """Clear the configuration cache."""
        self._config_cache = {}
        logger.debug("Config cache cleared")
