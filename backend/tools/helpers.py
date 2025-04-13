import inspect
import asyncio
from typing import Callable, Tuple, Dict, Any, Union, Awaitable
import json
import logging

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


async def execute_function(function: Callable, args: Dict[str, Any]) -> Any:
    """
    Execute a function with the given arguments, handling both sync and async functions.
    
    Args:
        function: The function to execute
        args: The arguments to pass to the function
        
    Returns:
        The result of the function call
    """
    logger.info(f"Executing function: {function.__name__} with args: {args}")
    
    if inspect.iscoroutinefunction(function):
        # Function is async, await it
        logger.info(f"Function {function.__name__} is async")
        return await function(**args)
    else:
        # Function is sync, run it directly
        logger.info(f"Function {function.__name__} is sync")
        return function(**args)
