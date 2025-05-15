# Connection-Aware Tools

The application now implements connection-aware tools that maintain context about which WebSocket connection initiated a request. This approach ensures responses and actions are directed only to the originating client rather than broadcasting to all connected clients.

## Key Features

- **Request-Response Pairing**: Each tool request can be associated with the specific WebSocket connection that initiated it
- **Targeted Navigation**: Navigation requests can be sent to specific clients rather than broadcasted to all
- **Context Preservation**: Connection context is maintained throughout the tool execution pipeline
- **Improved Multi-User Support**: Different clients can receive client-specific responses

## Implementation Details

### WebSocket Handler

The WebSocket handler in `backend/main.py` now passes the connection context when processing chat messages:

```python
async for content in stream_openai_completion(
    client, DEPLOYMENT_NAME, validated, phrase_queue, GEN_STOP_EVENT, connection=websocket
):
    # Handle response to specific connection
```

### Navigation Handler

The `NavigationHandler` class has been updated to support sending navigation requests to specific connections:

```python
async def send_navigation_request(self, screen: str, params: Optional[Dict[str, Any]] = None, connection=None):
    """
    Send a navigation request to a specific connection or all connected frontends.
    
    Args:
        screen: The screen to navigate to
        params: Optional parameters for the screen
        connection: Optional specific websocket connection to send to. If None, send to all.
    """
    if connection:
        connections = [connection]
    else:
        connections = self._connections
    
    # Send to specific connection(s)
    for ws in connections:
        await ws.send_json(message)
```

### Tool Function Updates

The navigation tool and other tools now accept a `connection` parameter that identifies the originating connection:

```python
async def navigate_to_screen(screen: str, extra_params: Optional[Dict[str, Any]] = None, connection=None):
    # Use connection context to target navigation request
    await navigation_handler.send_navigation_request(target_screen, extra_params, connection)
```

### OpenAI SDK Integration

The OpenAI SDK integration has been updated to pass the connection context when executing tool calls:

```python
# If this is a navigation function and we have a connection, add it to the args
if fn.__name__ == 'navigate_to_screen' and connection:
    fn_args['connection'] = connection
```

### Tool Execution

The tool execution pipeline has been enhanced to handle connection parameters:

```python
# Extract connection parameter if it exists
connection = args.pop('connection', None) if 'connection' in args else None

# Make a copy of args to filter out params not in the function signature
sig = inspect.signature(function)
valid_args = {k: v for k, v in args.items() if k in sig.parameters}

# Add connection back if it's a valid parameter
if connection is not None and 'connection' in sig.parameters:
    valid_args['connection'] = connection
```

## Benefits

1. **Improved Multi-User Experience**: When multiple users are connected to the application, each user's interactions and responses remain isolated.

2. **Reduced Unnecessary Traffic**: Navigation commands and other actions are only sent to the relevant client, reducing network traffic.

3. **Context Preservation**: Tool executions maintain awareness of which client initiated the request, allowing for stateful interactions.

4. **Enhanced Privacy**: User-specific responses are only sent to the originating user, enhancing privacy in multi-user scenarios.

## Future Enhancements

- Extend connection-aware functionality to other tools beyond navigation
- Add user identification to connections for personalized experiences
- Implement connection pools for handling different types of client connections
- Create a unified connection context object to simplify parameter passing 