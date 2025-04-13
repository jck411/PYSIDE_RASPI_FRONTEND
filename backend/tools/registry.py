"""
Tool Registry - Central location for registering and accessing all tool functions.
"""
import importlib
import inspect
import os
import asyncio
from typing import Dict, Callable, List, Any
import logging

logger = logging.getLogger(__name__)

# Dictionary to store all registered tool functions
_TOOL_FUNCTIONS: Dict[str, Callable] = {}

# List to store tool schemas
_TOOL_SCHEMAS: List[Dict[str, Any]] = []

def _discover_and_register_tools():
    """
    Auto-discover tool modules and register their functions.
    """
    # Get the directory of this file (tools directory)
    tools_dir = os.path.dirname(os.path.abspath(__file__))
    
    for filename in os.listdir(tools_dir):
        # Skip __init__.py, helpers.py, registry.py and non-python files
        if (filename.startswith('__') or 
            filename == 'helpers.py' or 
            filename == 'registry.py' or 
            not filename.endswith('.py')):
            continue
            
        module_name = filename[:-3]  # Remove .py extension
        
        try:
            # Import the module dynamically
            module = importlib.import_module(f"backend.tools.{module_name}")
            
            # Look for functions that are not internal (don't start with _)
            for name, obj in inspect.getmembers(module):
                if (inspect.isfunction(obj) or inspect.iscoroutinefunction(obj)) and not name.startswith('_'):
                    # Skip get_schema function as it's special
                    if name == 'get_schema':
                        continue
                        
                    # Register the function
                    _TOOL_FUNCTIONS[name] = obj
                    logger.info(f"Registered tool function: {name} from {module_name}")
            
            # Get schema if available
            if hasattr(module, 'get_schema'):
                schema = module.get_schema()
                _TOOL_SCHEMAS.append(schema)
                logger.info(f"Registered schema for: {schema['function']['name']}")
                
        except Exception as e:
            logger.error(f"Error registering tool module {module_name}: {e}")

def get_tools() -> List[Dict[str, Any]]:
    """
    Get all registered tool schemas.
    
    Returns:
        List of tool schema definitions
    """
    # Ensure tools are discovered
    if not _TOOL_SCHEMAS:
        _discover_and_register_tools()
    return _TOOL_SCHEMAS

def get_available_functions() -> Dict[str, Callable]:
    """
    Get all registered tool functions.
    
    Returns:
        Dictionary mapping function names to their implementations
    """
    # Ensure tools are discovered
    if not _TOOL_FUNCTIONS:
        _discover_and_register_tools()
    return _TOOL_FUNCTIONS 