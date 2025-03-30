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
    
    def load_module_config(self, module_path: str, module_key: str, config_vars: List[str]) -> Dict[str, Any]:
        """
        Load configuration from a Python module.
        
        Args:
            module_path: Import path to the module (e.g., 'frontend.stt.config')
            module_key: The key to use for this configuration source (e.g., 'stt')
            config_vars: List of variable names to extract from the module
            
        Returns:
            Dictionary containing the extracted configuration variables
        """
        # Check if already loaded with the same key to prevent redundant loads
        # and potential key conflicts if different modules were assigned the same key.
        if module_key in self._module_configs:
            # Optionally, log a warning or raise an error if config_vars differ?
            # For now, just return the existing config.
            logger.debug(f"Module config for key '{module_key}' already loaded. Skipping load from {module_path}.")
            return self._module_configs[module_key]

        try:
            module = importlib.import_module(module_path)
            config_dict = {}
            
            for var_name in config_vars:
                if hasattr(module, var_name):
                    config_dict[var_name] = getattr(module, var_name)
            
            # Store in module configs using the provided key
            self._module_configs[module_key] = config_dict
            logger.info(f"Loaded module config '{module_key}' from {module_path}: {', '.join(config_vars)}")
            return config_dict
        except ModuleNotFoundError:
            logger.error(f"Module not found when loading config: {module_path}")
            # Store an empty dict to prevent repeated load attempts for this key
            self._module_configs[module_key] = {} 
            return {}
        except Exception as e:
            logger.error(f"Error loading module config '{module_key}' from {module_path}: {e}")
             # Store an empty dict to prevent repeated load attempts for this key
            self._module_configs[module_key] = {}
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
        override_found = False
        override_value = None
        if 'module_overrides' in self._file_configs.get('user', {}) and \
           source in self._file_configs['user']['module_overrides'] and \
           var in self._file_configs['user']['module_overrides'][source]:
            
            override = self._file_configs['user']['module_overrides'][source][var]
            logger.debug(f"[get_config] Found base override for {path}: {override}")

            # Handle nested access for overrides
            if len(parts) > 2:
                current_override_level = override
                keys_to_traverse = parts[2:]
                all_keys_found = True
                for i, key in enumerate(keys_to_traverse):
                    if isinstance(current_override_level, dict) and key in current_override_level:
                        current_override_level = current_override_level[key]
                        logger.debug(f"[get_config] Traversing override key '{key}' for {path}, current value: {current_override_level}")
                    else:
                        logger.debug(f"[get_config] Nested key '{key}' not found in override for {path}. Fallback likely.")
                        all_keys_found = False
                        break 
                
                if all_keys_found:
                    # If we've traversed all keys successfully, return the override
                    override_found = True
                    override_value = current_override_level
                    logger.debug(f"[get_config] Found nested override for {path}: {override_value}")
            else:
                # Direct access without nested keys
                override_found = True
                override_value = override
                logger.debug(f"[get_config] Found direct override for {path}: {override_value}")

        if override_found:
            self._config_cache[path] = override_value # Cache the found override
            return override_value
        else:
             logger.debug(f"[get_config] No override found for path '{path}'. Checking module config.")

        # Handle module config - *DO NOT LOAD HERE*
        # Configuration should be loaded explicitly elsewhere.
        # if source not in self._module_configs:
        #     # This logic was problematic, loading specific modules based on key,
        #     # and always from frontend.config. Removing it.
        #     # if source == 'stt':
        #     #     self.load_module_config('frontend.config', 'stt', ['STT_CONFIG', 'AUDIO_CONFIG', 'DEEPGRAM_CONFIG'])
        #     # elif source == 'server':
        #     #     self.load_module_config('frontend.config', 'server', ['SERVER_HOST', 'SERVER_PORT', 'WEBSOCKET_PATH', 'HTTP_BASE_URL'])
        #     pass # Let it fall through to check self._module_configs below

        # Get from module config
        if source in self._module_configs and var in self._module_configs[source]:
            config = self._module_configs[source][var]
            
            # Handle nested access
            if len(parts) > 2:
                current_module_level = config
                keys_to_traverse = parts[2:]
                all_keys_found = True
                for key in keys_to_traverse:
                    if isinstance(current_module_level, dict) and key in current_module_level:
                        current_module_level = current_module_level[key]
                        logger.debug(f"[get_config] Traversing module key '{key}' for {path}, current value: {current_module_level}")
                    else:
                        logger.debug(f"[get_config] Nested key '{key}' not found in module config for {path}. Using default.")
                        all_keys_found = False
                        return default # Return default if nested key not found in module config
                
                if all_keys_found:
                    config = current_module_level # Use the final nested value
                else: # Should not happen due to return above, but for safety
                    return default 
            
            self._config_cache[path] = config
            logger.debug(f"[get_config] Found value in module config for {path}: {config}")
            return config
        
        logger.debug(f"[get_config] Path '{path}' not found in overrides or module config. Returning default: {default}")
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
        
        # Load module config if needed - *DO NOT LOAD HERE*
        # Configuration should be loaded explicitly elsewhere.
        # if source not in self._module_configs:
        #     # Problematic logic removed, see get_config
        #     # if source == 'stt':
        #     #     self.load_module_config('frontend.config', 'stt', ['STT_CONFIG', 'AUDIO_CONFIG', 'DEEPGRAM_CONFIG'])
        #     # elif source == 'server':
        #     #     self.load_module_config('frontend.config', 'server', ['SERVER_HOST', 'SERVER_PORT', 'WEBSOCKET_PATH', 'HTTP_BASE_URL'])
        #     pass # Cannot set config for a source that hasn't been loaded

        # Ensure module overrides path exists in user config
        if 'module_overrides' not in self._file_configs['user']:
            self._file_configs['user']['module_overrides'] = {}
        if source not in self._file_configs['user']['module_overrides']:
            self._file_configs['user']['module_overrides'][source] = {}
        
        override_target = self._file_configs['user']['module_overrides'][source]
        
        # Handle nested keys for overrides
        if len(parts) > 2:
             # Navigate to the parent dictionary
            for key in parts[1:-1]: # Iterate up to the second-to-last part
                 # If a key represents a variable name (like STT_CONFIG) and is the target, update it directly
                if key == var and len(parts) == 3: # e.g., stt.STT_CONFIG.enabled
                    if var not in override_target:
                         override_target[var] = {} # Initialize if it doesn't exist
                    if isinstance(override_target[var], dict):
                         override_target[var][parts[-1]] = value
                    else:
                         # This case might indicate an issue - trying to set a sub-key on a non-dict override?
                         # For now, let's overwrite the existing non-dict value. Consider logging a warning.
                         logger.warning(f"Overwriting non-dictionary value at '{'.'.join(parts[:-1])}' with dictionary for key '{parts[-1]}'")
                         override_target[var] = {parts[-1]: value}
                    break # Value set, exit loop

                # Otherwise, traverse deeper
                if key not in override_target or not isinstance(override_target.get(key), dict):
                     logger.debug(f"[set_config] Creating/overwriting dict for key '{key}' in override target")
                     override_target[key] = {} # Create nested dict if needed
                override_target = override_target[key]
            else: # This 'else' belongs to the 'for' loop, executes if loop completes without 'break'
                 # This means we are setting a nested value like stt.VAR.key1.key2
                 # Ensure the direct parent exists
                 if parts[-2] not in override_target:
                     override_target[parts[-2]] = {}
                 if isinstance(override_target[parts[-2]], dict):
                    override_target[parts[-2]][parts[-1]] = value
                 else:
                    # Similar issue as above - parent is not a dict. Overwrite it.
                    logger.warning(f"Overwriting non-dictionary value at '{'.'.join(parts[:-1])}' with dictionary for key '{parts[-1]}'")
                    override_target[parts[-2]] = {parts[-1]: value}

        else: # Direct setting (e.g., 'stt.STT_CONFIG')
            override_target[var] = value

        # Log the state just before saving
        logger.debug(f"[set_config] User config state before saving for path '{path}': {self._file_configs.get('user', {})}")

        # Save updated user config
        return self._save_user_config()
    
    def reset_config(self, path: str) -> bool:
        """
        Reset configuration to default (remove override).
        
        Args:
            path: Configuration path
            
        Returns:
            True if successful, False otherwise
        """
        parts = path.split('.')
        if len(parts) < 2:
            logger.error(f"Invalid config path: {path}")
            return False
        
        source = parts[0]
        var = parts[1]
        
        # Clear cache
        if path in self._config_cache:
            del self._config_cache[path]
        
        # Can only reset module overrides
        if source == 'user':
            logger.error(f"Cannot reset user config: {path}")
            return False
        
        # Check if override exists
        if 'module_overrides' not in self._file_configs['user'] or \
           source not in self._file_configs['user']['module_overrides'] or \
           var not in self._file_configs['user']['module_overrides'][source]:
            # Nothing to reset
            return True
        
        # Handle nested keys
        if len(parts) > 2:
            config = self._file_configs['user']['module_overrides'][source][var]
            parent = None
            leaf = None
            
            # Navigate to the parent of the leaf node
            for i, key in enumerate(parts[2:], 2):
                if i == len(parts) - 1:  # Last key
                    parent = config
                    leaf = key
                elif key in config:
                    config = config[key]
                else:
                    # Key doesn't exist, nothing to reset
                    return True
            
            # Remove leaf node
            if parent is not None and leaf in parent:
                del parent[leaf]
        else:
            # Remove the entire var
            del self._file_configs['user']['module_overrides'][source][var]
        
        # Cleanup empty dictionaries
        if source in self._file_configs['user']['module_overrides'] and \
           not self._file_configs['user']['module_overrides'][source]:
            del self._file_configs['user']['module_overrides'][source]
        
        if 'module_overrides' in self._file_configs['user'] and \
           not self._file_configs['user']['module_overrides']:
            del self._file_configs['user']['module_overrides']
        
        # Save to file
        return self._save_user_config()
