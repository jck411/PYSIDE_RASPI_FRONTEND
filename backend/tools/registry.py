"""
Tool Registry - Central location for registering and accessing all tool functions.
"""
import importlib
import inspect
import os
import asyncio
from typing import Dict, Callable, List, Any, Optional
import logging

# Import the orchestrator
from backend.tools.orchestrator import orchestrator, execute_parallel, execute_with_dependencies

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
            filename == 'orchestrator.py' or  # Skip orchestrator too
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
                
                # Register the tool with the orchestrator
                # Check if schema has dependency metadata
                function_data = schema.get('function', {})
                function_name = function_data.get('name')
                if function_name:
                    # Look for dependency metadata
                    dependencies = function_data.get('dependencies', [])
                    provides = function_data.get('provides', [])
                    
                    # Register with orchestrator if we have dependency info
                    if dependencies or provides:
                        orchestrator.add_tool(function_name, dependencies, provides)
                        logger.info(f"Registered dependencies for {function_name}: depends on {dependencies}, provides {provides}")
                
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

async def execute_tools_parallel(tool_calls: List[Dict[str, Any]], 
                               timeout: float = 30.0) -> Dict[str, Any]:
    """
    Execute multiple tool calls in parallel.
    
    Args:
        tool_calls: List of tool call dictionaries with 'name' and 'params'
        timeout: Maximum execution time in seconds
        
    Returns:
        Dictionary mapping tool names to their results
    """
    # Ensure tools are discovered
    functions = get_available_functions()
    
    # Use the orchestrator to execute in parallel
    return await execute_parallel(tool_calls, functions, timeout)

async def execute_tools_with_dependencies(tool_calls: List[Dict[str, Any]],
                                        timeout: float = 30.0) -> Dict[str, Any]:
    """
    Execute tool calls respecting dependencies between them.
    
    Args:
        tool_calls: List of tool call dictionaries with dependencies specified
        timeout: Maximum execution time in seconds per batch
        
    Returns:
        Dictionary mapping tool names to their results
    """
    # Ensure tools are discovered
    functions = get_available_functions()
    
    # Register orchestrator with all available functions
    orchestrator.set_functions(functions)
    
    # Use the orchestrator to execute with dependencies
    return await execute_with_dependencies(tool_calls, functions, timeout) 