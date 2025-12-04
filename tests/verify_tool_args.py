import asyncio
from app.mcp.server import MCPServer, Tool

def mock_tool(a: int, b: int) -> int:
    return a + b

async def test_arg_filtering():
    print("\n--- Testing Tool Argument Filtering ---")
    
    server = MCPServer()
    tool_def = Tool(
        name="mock_tool",
        description="Mock tool",
        parameters={"type": "object", "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}}}
    )
    server.register_tool(tool_def, mock_tool)
    
    # Test with valid arguments
    print("1. Testing valid arguments...")
    result = await server.call_tool("mock_tool", {"a": 1, "b": 2})
    print(f"[PASS] Result: {result}")
    assert result == 3
    
    # Test with extra arguments (should be ignored)
    print("\n2. Testing extra arguments...")
    try:
        result = await server.call_tool("mock_tool", {"a": 5, "b": 5, "extra": "ignored", "additionalProp1": {}})
        print(f"[PASS] Result with extra args: {result}")
        assert result == 10
    except TypeError as e:
        print(f"[FAIL] TypeError raised: {e}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(test_arg_filtering())
        print("\nAll Tests Passed!")
    except Exception as e:
        print(f"\n[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
