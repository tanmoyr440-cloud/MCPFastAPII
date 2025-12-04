"""Common MCP tools."""
from app.mcp.server import Tool
from datetime import datetime
from googlesearch import search

# Tool Definitions

CALCULATOR_TOOL = Tool(
    name="calculator",
    description="Perform basic arithmetic operations",
    parameters={
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "enum": ["add", "subtract", "multiply", "divide"],
                "description": "The operation to perform"
            },
            "a": {"type": "number", "description": "First number"},
            "b": {"type": "number", "description": "Second number"}
        },
        "required": ["operation", "a", "b"]
    }
)

WEB_SEARCH_TOOL = Tool(
    name="web_search",
    description="Search the web for information using Google",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "The search query"},
            "num_results": {"type": "integer", "description": "Number of results to return", "default": 3}
        },
        "required": ["query"]
    }
)

TIME_TOOL = Tool(
    name="get_current_time",
    description="Get the current date and time",
    parameters={
        "type": "object",
        "properties": {},
        "required": []
    }
)

# Tool Implementations

def calculator(operation: str, a: float, b: float) -> float:
    """Perform calculation."""
    if operation == "add":
        return a + b
    elif operation == "subtract":
        return a - b
    elif operation == "multiply":
        return a * b
    elif operation == "divide":
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b
    else:
        raise ValueError(f"Unknown operation: {operation}")

def web_search(query: str, num_results: int = 3) -> str:
    """Search the web using Google."""
    try:
        results = []
        for result in search(query, num_results=num_results, advanced=True):
            results.append(f"Title: {result.title}\nURL: {result.url}\nDescription: {result.description}\n")
        
        if not results:
            return f"No results found for '{query}'."
            
        return "\n---\n".join(results)
    except Exception as e:
        return f"Error performing search: {str(e)}"

def get_current_time() -> str:
    """Get current date and time."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
