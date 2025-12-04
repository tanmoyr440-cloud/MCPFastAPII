import asyncio
from app.agents.general import GeneralAgent
from app.agents.researcher import ResearchAgent
from app.agents.coder import CoderAgent
from app.mcp.server import MCPServer
from app.mcp.tools import calculator, web_search, get_current_time, CALCULATOR_TOOL, WEB_SEARCH_TOOL, TIME_TOOL
from unittest.mock import MagicMock, patch, AsyncMock

@patch("app.mcp.tools.search")
def test_mcp_tools(mock_search):
    print("\n--- Testing MCP Tools ---")
    
    # Calculator
    res_add = calculator("add", 5, 3)
    print(f"[PASS] Calculator Add: 5 + 3 = {res_add}")
    assert res_add == 8
    
    res_div = calculator("divide", 10, 2)
    print(f"[PASS] Calculator Divide: 10 / 2 = {res_div}")
    assert res_div == 5
    
    # Web Search (Mocked Google Search)
    mock_result = MagicMock()
    mock_result.title = "Mock Title"
    mock_result.url = "http://mock.url"
    mock_result.description = "Mock Description"
    mock_search.return_value = [mock_result]
    
    res_search = web_search("python asyncio")
    print(f"[PASS] Web Search: {res_search}")
    assert "Mock Title" in res_search
    
    # Time Tool
    res_time = get_current_time()
    print(f"[PASS] Time Tool: {res_time}")
    assert len(res_time) > 0

def test_mcp_server():
    print("\n--- Testing MCP Server ---")
    server = MCPServer()
    server.register_tool(CALCULATOR_TOOL, calculator)
    server.register_tool(TIME_TOOL, get_current_time)
    
    # Call tool via server
    res = asyncio.run(server.call_tool("calculator", {"operation": "multiply", "a": 4, "b": 5}))
    print(f"[PASS] Server Call 'calculator': 4 * 5 = {res}")
    assert res == 20
    
    res_time = asyncio.run(server.call_tool("get_current_time", {}))
    print(f"[PASS] Server Call 'get_current_time': {res_time}")
    assert len(res_time) > 0

@patch("app.services.llm_service.ChatOpenAI")
def test_agents(mock_openai_class):
    print("\n--- Testing AI Agents (Mocked LangChain) ---")
    
    # Setup Mock
    mock_llm = MagicMock()
    mock_response = MagicMock()
    mock_response.content = "This is a mocked response."
    mock_llm.ainvoke = AsyncMock(return_value=mock_response) # Use AsyncMock
    mock_openai_class.return_value = mock_llm
    
    # General Agent
    agent = GeneralAgent()
    print(f"[PASS] Initialized {agent.name}")
    
    response = asyncio.run(agent.process("Hello"))
    print(f"[PASS] Agent Response: {response}")
    assert response == "This is a mocked response."
    assert len(agent.history) == 2 # User + Assistant
    
    # Research Agent
    researcher = ResearchAgent()
    print(f"[PASS] Initialized {researcher.name}")
    
    # Coder Agent
    coder = CoderAgent()
    print(f"[PASS] Initialized {coder.name}")

if __name__ == "__main__":
    # Mock env vars for testing if not present
    import os
    if "API_KEY" not in os.environ:
        os.environ["API_KEY"] = "mock_key"
        os.environ["API_ENDPOINT"] = "https://mock.openai.azure.com"
        os.environ["MODEL_CHAT_BASIC"] = "gpt-35-turbo"
        os.environ["MODEL_REASONING"] = "deepseek-r1"
        os.environ["MODEL_HIGH_PERF"] = "deepseek-v3"
        
    try:
        test_mcp_tools()
        test_mcp_server()
        test_agents()
        print("\nAll Tests Passed!")
    except Exception as e:
        print(f"\n[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
