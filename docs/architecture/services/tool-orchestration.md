# Tool Orchestration

The Tool Orchestration system manages the execution of backend tool functions, supporting both parallel and sequential execution based on dependencies between tools.

## Key Features

- **Parallel Execution**: Run independent tools concurrently using `asyncio.gather()`
- **Sequential Execution**: Execute tools in a specific order based on dependencies
- **Dependency Handling**: Automatically resolve tool dependencies and pass outputs between tools
- **Navigation Optimization**: Run navigation operations in parallel with other tools
- **Batch Processing**: Group independent tools into execution batches for efficiency
- **Timeout Management**: Apply timeouts to prevent hanging operations
- **Error Handling**: Gracefully handle exceptions during tool execution

## Architecture Components

### 1. ToolOrchestrator Class

The core orchestrator that manages tool execution based on dependencies:

```python
class ToolOrchestrator:
    def __init__(self):
        self.functions = {}  # Registry of available functions
        self.execution_plan = ToolExecutionPlan()  # Holds execution plan
        
    # Main method to execute tools with dependency resolution
    async def execute_tools(self, tool_calls, timeout=30.0):
        # Creates and executes a plan based on tool dependencies
```

### 2. ToolExecutionPlan Class

Responsible for dependency analysis and execution batch creation:

```python
class ToolExecutionPlan:
    def __init__(self):
        self.tool_dependencies = {}  # Maps tool names to their dependencies
        self.execution_batches = []  # Ordered list of batches for execution

    def build_execution_plan(self):
        # Analyzes dependencies and builds execution batches
        # Special handling for navigation tools
```

### 3. ToolDependency Class

Represents a dependency relationship between tools:

```python
class ToolDependency:
    def __init__(self, tool_name, provides=None):
        self.tool_name = tool_name  # Name of the tool
        self.provides = provides or []  # Data keys this tool provides
        self.depends_on = []  # Names of tools this tool depends on
        self.output = None  # Stores output for use by dependent tools
```

## Dependency Resolution Algorithm

The system uses a topological sorting approach to create execution batches:

1. Tools with no dependencies are placed in the first batch
2. Navigation tools are automatically placed in their own batch for parallel execution
3. For each subsequent batch, tools whose dependencies are satisfied by previous batches are included
4. The process continues until all tools are assigned to batches
5. If circular dependencies are detected, the system selects the tool with fewest unmet dependencies

## Schema Extensions

Tool schemas in the registry have been extended to include dependency metadata:

```python
{
    "type": "function",
    "function": {
        "name": "tool_name",
        "parameters": { /* ... */ },
        # Dependency metadata
        "dependencies": ["tool_name_1", "tool_name_2"],  # Tools this tool depends on
        "provides": ["data_key_1", "data_key_2"],  # Data provided by this tool
        "parallel_safe": true  # Whether this tool can run in parallel with others
    }
}
```

## Usage Examples

### Parallel Execution

```python
tool_calls = [
    {
        "name": "navigate_to_screen",
        "params": {"screen": "weather"}
    },
    {
        "name": "get_weather_current",
        "params": {
            "lat": "28.5988",
            "lon": "-81.3583",
            "units": "imperial",
            "lang": "en",
            "detail_level": "simple"
        }
    }
]

# Execute tools in parallel
results = await execute_tools_parallel(tool_calls)
```

### Sequential Execution with Dependencies

```python
tool_calls = [
    {
        "name": "get_weather_current",
        "params": {
            "lat": "28.5988",
            "lon": "-81.3583"
        },
        "provides": ["current_weather"]  # This tool provides weather data
    },
    {
        "name": "navigate_to_screen",
        "params": {"screen": "weather"},
        "depends_on": ["get_weather_current"]  # This tool depends on weather data
    }
]

# Execute tools with dependency handling
results = await execute_tools_with_dependencies(tool_calls)
```

## Implementation Details

- **Automatic Registration**: Tools register their dependencies through the schema system
- **Parameter Passing**: Outputs from dependent tools are automatically passed as inputs to dependent tools
- **Timeout Management**: Each batch has its own timeout to prevent hanging operations
- **Exception Handling**: Exceptions from one tool don't prevent other tools from executing
- **Special Navigation Handling**: Navigation tools run in parallel regardless of other dependencies

## Benefits

- **Improved Response Time**: Parallel execution reduces overall response time
- **Clean Dependencies**: Explicit dependency declarations make code more maintainable
- **Enhanced User Experience**: Navigation happens concurrently with data fetching
- **Error Resilience**: Failures in one tool don't prevent others from executing
- **Simplified Tool Development**: Developers can focus on single-purpose tools 