"""MCP Server implementation."""
from typing import Dict, Callable, Any, List
from pydantic import BaseModel

class Tool(BaseModel):
    """Tool definition."""
    name: str
    description: str
    parameters: Dict[str, Any]

class MCPServer:
    """Model Context Protocol (MCP) Server."""
    
    def __init__(self):
        self.tools: Dict[str, Callable] = {}
        self.tool_definitions: List[Tool] = []

    def register_tool(self, tool_def: Tool, func: Callable):
        """Register a tool."""
        self.tools[tool_def.name] = func
        self.tool_definitions.append(tool_def)

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Call a registered tool."""
        if name not in self.tools:
            raise ValueError(f"Tool '{name}' not found")
        
        func = self.tools[name]
        
        # Filter arguments to match function signature
        import inspect
        sig = inspect.signature(func)
        valid_args = {
            k: v for k, v in arguments.items() 
            if k in sig.parameters
        }
        
        # Check if function is async
        if asyncio.iscoroutinefunction(func):
            return await func(**valid_args)
        return func(**valid_args)

    def get_tools(self) -> List[Dict[str, Any]]:
        """Get list of registered tools."""
        return [tool.dict() for tool in self.tool_definitions]

import asyncio
