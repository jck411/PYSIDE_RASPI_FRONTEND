import inspect
import asyncio
from typing import Callable, Tuple, Dict, Any, Union, Awaitable, Optional
import json
import logging
import traceback

logger = logging.getLogger(__name__)

def check_args(function: Callable, args: dict) -> bool:
    """
    Check if the arguments match the function signature.
    
    Args:
        function: The function to check
        args: The arguments to check
        
    Returns:
        True if the arguments match the function signature
    """
    sig = inspect.signature(function)
    params = sig.parameters
    for name in args:
        if name not in params:
            return False
    for name, param in params.items():
        if param.default is param.empty and name not in args:
            return False
    return True


def get_function_and_args(
    tool_call: dict, available_functions: dict
) -> Tuple[Callable, dict]:
    """
    Get the function and arguments from a tool call.
    
    Args:
        tool_call: The tool call from OpenAI
        available_functions: Dictionary of available functions
        
    Returns:
        Tuple of (function, arguments)
    """
    function_name = tool_call["function"]["name"]
    function_args = json.loads(tool_call["function"]["arguments"])
    
    if function_name not in available_functions:
        raise ValueError(f"Function '{function_name}' not found")
        
    function_to_call = available_functions[function_name]
    
    if not check_args(function_to_call, function_args):
        raise ValueError(f"Invalid arguments for function '{function_name}'")
        
    return function_to_call, function_args


async def execute_function(function: Callable, args: Dict[str, Any], timeout: Optional[float] = None) -> Any:
    """
    Execute a function with the given arguments, handling both sync and async functions.
    
    Args:
        function: The function to execute
        args: The arguments to pass to the function
        timeout: Optional timeout in seconds for the function execution
        
    Returns:
        The result of the function call
        
    Raises:
        asyncio.TimeoutError: If the function execution times out
        Exception: Any exception raised by the function
    """
    logger.info(f"Executing function: {function.__name__} with args: {args}")
    
    # Extract connection parameter if it exists (it might not be in the function signature)
    connection = args.pop('connection', None) if 'connection' in args else None
    
    # Make a copy of args to filter out params not in the function signature
    sig = inspect.signature(function)
    valid_args = {k: v for k, v in args.items() if k in sig.parameters}
    
    # Add connection back if it's a valid parameter
    if connection is not None and 'connection' in sig.parameters:
        valid_args['connection'] = connection
    
    try:
        if inspect.iscoroutinefunction(function):
            # Function is async, await it with optional timeout
            logger.info(f"Function {function.__name__} is async")
            if timeout:
                try:
                    return await asyncio.wait_for(function(**valid_args), timeout=timeout)
                except asyncio.TimeoutError:
                    logger.error(f"Function {function.__name__} timed out after {timeout} seconds")
                    return {
                        "error": f"The operation timed out after {timeout} seconds",
                        "status": "timeout"
                    }
            else:
                # No timeout specified
                return await function(**valid_args)
        else:
            # Function is sync, run it directly
            logger.info(f"Function {function.__name__} is sync")
            return function(**valid_args)
    except Exception as e:
        logger.error(f"Error executing function {function.__name__}: {e}")
        logger.debug(f"Exception traceback: {traceback.format_exc()}")
        return {
            "error": f"An error occurred: {str(e)}",
            "status": "error"
        }
