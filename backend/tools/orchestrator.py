"""
Tool Orchestrator - Manages execution of tools with dependency handling.

This module provides functionality to:
1. Execute tools in parallel when they're independent
2. Execute tools sequentially when there are dependencies
3. Automatically run navigation tools in parallel with other operations
4. Handle tool dependencies and execution planning

Tool call results are keyed by a unique 'id' field if present in the tool call dict, otherwise by tool name. This allows multiple calls to the same tool in a batch without overwriting results.
"""


import asyncio
import logging
from typing import Dict, List, Any, Callable, Optional, Set, Tuple, Union

# Setup logger for orchestrator
logger = logging.getLogger("orchestrator")
handler = logging.StreamHandler()
formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
handler.setFormatter(formatter)
if not logger.hasHandlers():
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

class ToolDependency:
    """
    Represents a dependency between tools.
    A tool can depend on another tool's output.
    """
    def __init__(self, tool_name: str, provides: Optional[List[str]] = None):
        self.tool_name = tool_name
        self.provides = provides or []  # Data/keys this tool provides
        self.depends_on: List[str] = []  # Names of tools this tool depends on
        self.output: Any = None  # Will store the tool's output once executed

    def add_dependency(self, dependency_tool_name: str):
        """Add a tool that this tool depends on"""
        if dependency_tool_name not in self.depends_on:
            self.depends_on.append(dependency_tool_name)

    def __repr__(self):
        return f"ToolDependency({self.tool_name}, depends_on={self.depends_on}, provides={self.provides})"


class ToolExecutionPlan:
    """
    Represents a plan for executing tools with dependencies.
    Sorts tools into execution batches where tools in the same batch
    can be executed in parallel.
    """
    def __init__(self):
        self.tool_dependencies: Dict[str, ToolDependency] = {}
        self.execution_batches: List[List[str]] = []
        logger.debug(f"ToolExecutionPlan initialized.")

    def add_tool(self, tool_name: str, 
                 depends_on: Optional[List[str]] = None, 
                 provides: Optional[List[str]] = None) -> None:
        logger.debug(f"Adding tool to plan: {tool_name}, depends_on={depends_on}, provides={provides}")
        """
        Add a tool to the execution plan with its dependencies
        and what data it provides.
        
        Args:
            tool_name: Name of the tool
            depends_on: List of tool names this tool depends on
            provides: List of data keys this tool provides
        """
        if tool_name not in self.tool_dependencies:
            self.tool_dependencies[tool_name] = ToolDependency(tool_name, provides)
        
        if depends_on:
            for dep in depends_on:
                self.tool_dependencies[tool_name].add_dependency(dep)
                
                # Ensure the dependency exists in our registry
                if dep not in self.tool_dependencies:
                    self.tool_dependencies[dep] = ToolDependency(dep)

    def build_execution_plan(self) -> None:
        logger.info(f"Building execution plan for tools: {list(self.tool_dependencies.keys())}")
        """
        Builds an execution plan by analyzing dependencies and 
        creating batches of tools that can be executed in parallel.
        """
        # Reset execution batches
        self.execution_batches = []
        
        # Create a copy of tool dependencies to work with
        remaining_tools = set(self.tool_dependencies.keys())
        executed_tools = set()
        
        # Special handling for navigation - always put it in its own batch
        # that can run in parallel with other operations
        navigation_tools = {t for t in remaining_tools 
                           if t == "navigate_to_screen" or "navigation" in t.lower()}
        logger.debug(f"Navigation tools detected: {navigation_tools}")

        # If we have navigation tools, put them in their own batch right away
        if navigation_tools:
            self.execution_batches.append(list(navigation_tools))
            logger.info(f"Navigation batch: {list(navigation_tools)}")
            executed_tools.update(navigation_tools)
            remaining_tools -= navigation_tools
        
        # Process remaining tools in dependency order
        logger.debug(f"Remaining tools after navigation: {remaining_tools}")
        while remaining_tools:
            # Find tools with no unmet dependencies
            ready_tools = {
                tool for tool in remaining_tools
                if all(dep in executed_tools for dep in self.tool_dependencies[tool].depends_on)
            }
            
            if not ready_tools:
                # If we have a circular dependency, break it by selecting the tool
                # with the fewest dependencies left to be satisfied
                min_unmet = float('inf')
                best_tool = None
                
                for tool in remaining_tools:
                    unmet = sum(1 for dep in self.tool_dependencies[tool].depends_on 
                               if dep not in executed_tools)
                    if unmet < min_unmet:
                        min_unmet = unmet
                        best_tool = tool
                
                if best_tool:
                    ready_tools = {best_tool}
                    logger.warning(f"Circular dependency detected. Selecting {best_tool} "
                                   f"with {min_unmet} unmet dependencies.")
                else:
                    # This should never happen if there's at least one remaining tool
                    logger.error("Unable to resolve circular dependencies.")
                    break
            
            # Add this batch of tools to the execution plan
            self.execution_batches.append(list(ready_tools))
            logger.info(f"Batch added: {list(ready_tools)}")
            executed_tools.update(ready_tools)
            remaining_tools -= ready_tools
    
    def get_tool_inputs(self, tool_name: str) -> Dict[str, Any]:
        """
        Gets inputs for a tool based on what its dependencies provide.
        
        Args:
            tool_name: Name of the tool to get inputs for
            
        Returns:
            Dictionary of inputs derived from dependencies
        """
        inputs = {}
        tool = self.tool_dependencies.get(tool_name)
        
        if not tool:
            return inputs
            
        for dep_name in tool.depends_on:
            dep = self.tool_dependencies.get(dep_name)
            if dep and dep.output is not None:
                # Merge the dependency's output into our inputs
                if isinstance(dep.output, dict):
                    inputs.update(dep.output)
        
        return inputs


class ToolOrchestrator:
    """
    Orchestrates the execution of tools based on dependencies.
    """
    def __init__(self):
        self.functions: Dict[str, Callable] = {}
        self.execution_plan = ToolExecutionPlan()
        logger.debug("ToolOrchestrator initialized.")
        
    def register_function(self, name: str, func: Callable) -> None:
        """Register a tool function with the orchestrator"""
        logger.info(f"Registering tool function: {name}")
        self.functions[name] = func
        
    def set_functions(self, functions: Dict[str, Callable]) -> None:
        """Set all available functions at once"""
        logger.info(f"Setting all tool functions: {list(functions.keys())}")
        self.functions = functions
        
    def add_tool(self, name: str, depends_on: Optional[List[str]] = None,
                provides: Optional[List[str]] = None) -> None:
        """Add a tool to the execution plan"""
        logger.info(f"Adding tool to orchestrator: {name}, depends_on={depends_on}, provides={provides}")
        self.execution_plan.add_tool(name, depends_on, provides)
    
    def create_tool_dependency_map(self, tool_calls: List[Dict[str, Any]]) -> None:
        logger.info(f"Creating tool dependency map for tool_calls: {tool_calls}")
        """
        Analyzes a list of tool calls and creates a dependency map.
        
        Args:
            tool_calls: List of tool call dictionaries, each containing at least
                       'name' and optionally 'depends_on' and 'provides' keys
        """
        self.execution_plan = ToolExecutionPlan()
        
        # First pass: register all tools
        for tool_call in tool_calls:
            name = tool_call.get('name')
            depends_on = tool_call.get('depends_on', [])
            provides = tool_call.get('provides', [])
            
            if name:
                self.execution_plan.add_tool(name, depends_on, provides)
        
        # Build the execution plan
        self.execution_plan.build_execution_plan()
        
    async def execute_tools(self, tool_calls: List[Dict[str, Any]], 
                           timeout: float = 30.0) -> Dict[str, Any]:
        logger.info(f"Executing tool calls: {[call.get('name') for call in tool_calls]}")
        """
        Execute tool calls based on the dependency plan.
        
        Args:
            tool_calls: List of tool call dictionaries containing 'name' and 'params'
            timeout: Maximum time to wait for execution in seconds
            
        Returns:
            Dictionary mapping tool names to their results
        """
        # Create dependency map if not already done
        self.create_tool_dependency_map(tool_calls)
        
        # Create lookup for tool parameters and ids
        tool_params = {}
        tool_ids = {}
        for tc in tool_calls:
            if 'name' in tc:
                tool_params[tc['name']] = tc.get('params', {})
                # Use id if present, else fallback to name
                key = tc.get('id', tc['name'])
                tool_ids[tc['name']] = key
        
        # Prepare results dictionary
        results = {}
        
        # Execute batches in sequence
        for batch_idx, batch in enumerate(self.execution_plan.execution_batches):
            logger.info(f"Executing batch {batch_idx+1}/{len(self.execution_plan.execution_batches)}: {batch}")
            for tool_name in batch:
                logger.info(f"Batch {batch_idx+1}: tool {tool_name}")
            
            # Prepare coroutines for this batch
            batch_coros = []
            for tool_name in batch:
                # Get function to execute
                func = self.functions.get(tool_name)
                if not func:
                    logger.error(f"Tool function '{tool_name}' not found")
                    key = tool_ids.get(tool_name, tool_name)
                    results[key] = {"error": f"Tool function '{tool_name}' not found"}
                    continue
                # Get parameters for this tool
                params = tool_params.get(tool_name, {})
                # Get inputs from dependencies
                dep_inputs = self.execution_plan.get_tool_inputs(tool_name)
                # Merge dependency inputs with explicit parameters
                merged_params = {**dep_inputs, **params}
                # Create coroutine
                if asyncio.iscoroutinefunction(func):
                    coro = func(**merged_params)
                else:
                    coro = asyncio.to_thread(func, **merged_params)
                batch_coros.append((tool_name, coro))
            
            # Execute batch with timeout
            try:
                # Wait for all coroutines in the batch with a timeout
                batch_results = await asyncio.wait_for(
                    asyncio.gather(
                        *[coro for _, coro in batch_coros],
                        return_exceptions=True
                    ),
                    timeout=timeout
                )
                
                # Process results
                for (tool_name, _), result in zip(batch_coros, batch_results):
                    key = tool_ids.get(tool_name, tool_name)
                    if isinstance(result, Exception):
                        logger.error(f"Error executing tool '{tool_name}': {result}")
                        results[key] = {"error": str(result)}
                    else:
                        # Store the result
                        results[key] = result
                        # Also store in the dependency for use by subsequent tools
                        if tool_name in self.execution_plan.tool_dependencies:
                            self.execution_plan.tool_dependencies[tool_name].output = result
                            
            except asyncio.TimeoutError:
                logger.error(f"Timeout executing batch {batch_idx+1}")
                for tool_name, _ in batch_coros:
                    key = tool_ids.get(tool_name, tool_name)
                    if key not in results:
                        results[key] = {"error": "Execution timed out"}
        
        return results


# Create a singleton instance
orchestrator = ToolOrchestrator()

# Utility functions

async def execute_parallel(tool_calls: List[Dict[str, Any]], 
                         functions: Dict[str, Callable],
                         timeout: float = 30.0) -> Dict[str, Any]:
    """
    Execute multiple tool calls in parallel.
    
    Args:
        tool_calls: List of tool call dictionaries with 'name' and 'params'
        functions: Dictionary mapping function names to their implementations
        timeout: Maximum execution time in seconds
        
    Returns:
        Dictionary mapping tool names to their results
    """
    # Set up the orchestrator
    orchestrator.set_functions(functions)
    
    # Execute all tools
    return await orchestrator.execute_tools(tool_calls, timeout)


async def execute_with_dependencies(tool_calls: List[Dict[str, Any]],
                                  functions: Dict[str, Callable],
                                  timeout: float = 30.0) -> Dict[str, Any]:
    """
    Execute tool calls respecting dependencies between them.
    
    Args:
        tool_calls: List of tool call dictionaries with:
                   - 'name': Tool name
                   - 'params': Parameters for the tool
                   - 'depends_on': List of tool names this tool depends on
                   - 'provides': List of data keys this tool provides
        functions: Dictionary mapping function names to their implementations
        timeout: Maximum execution time in seconds per batch
        
    Returns:
        Dictionary mapping tool names to their results
    """
    # Set up the orchestrator
    orchestrator.set_functions(functions)
    
    # Execute all tools with dependency handling
    return await orchestrator.execute_tools(tool_calls, timeout) 