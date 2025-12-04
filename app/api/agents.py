"""API routes for AI Agents."""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.agents.general import GeneralAgent
from app.agents.researcher import ResearchAgent
from app.agents.coder import CoderAgent
from app.mcp.server import MCPServer
from app.mcp.tools import CALCULATOR_TOOL, WEB_SEARCH_TOOL, TIME_TOOL, calculator, web_search, get_current_time

router = APIRouter(prefix="/api/agents", tags=["agents"])

# Initialize Agents
agents = {
    "general": GeneralAgent(),
    "researcher": ResearchAgent(),
    "coder": CoderAgent()
}

# Initialize MCP Server
mcp_server = MCPServer()
mcp_server.register_tool(CALCULATOR_TOOL, calculator)
mcp_server.register_tool(WEB_SEARCH_TOOL, web_search)
mcp_server.register_tool(TIME_TOOL, get_current_time)

class AgentMessageRequest(BaseModel):
    """Request model for sending a message to an agent."""
    message: str

class AgentResponse(BaseModel):
    """Response model from an agent."""
    response: str
    agent: str

@router.get("/", response_model=List[str])
async def list_agents():
    """List available agents."""
    return list(agents.keys())

@router.post("/{agent_name}/chat", response_model=AgentResponse)
async def chat_with_agent(agent_name: str, request: AgentMessageRequest):
    """Chat with a specific agent."""
    if agent_name not in agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent = agents[agent_name]
    
    # Process message
    try:
        response = await agent.process(request.message)
        return AgentResponse(response=response, agent=agent_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tools", response_model=List[Dict[str, Any]])
async def list_tools():
    """List available MCP tools."""
    return mcp_server.get_tools()

@router.post("/tools/{tool_name}/call")
async def call_tool(tool_name: str, arguments: Dict[str, Any]):
    """Call an MCP tool directly (for testing/demo)."""
    try:
        result = await mcp_server.call_tool(tool_name, arguments)
        return {"result": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
