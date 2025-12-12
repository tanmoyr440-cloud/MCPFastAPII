import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from unittest.mock import MagicMock, AsyncMock
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from app.services.llm.token_optimizer import token_optimizer

@pytest.mark.asyncio
async def test_truncate_context():
    # Mock token service to return 10 tokens per message
    # (Assuming simple length for test)
    token_optimizer._count_tokens = MagicMock(return_value=10)
    
    messages = [
        SystemMessage(content="System"),
        HumanMessage(content="Msg 1"),
        AIMessage(content="Msg 2"),
        HumanMessage(content="Msg 3"),
        AIMessage(content="Msg 4")
    ]
    
    # Total tokens = 50
    # Max tokens = 30
    # Should keep System (10) + last 2 messages (20) = 30
    # But safety buffer is 500 in real code, so we need to mock that or adjust max_tokens
    
    # Let's bypass the safety buffer logic by mocking _count_tokens to return large values
    # or just trust the logic flow.
    
    # Real test with mocked token counts
    token_optimizer._count_tokens = MagicMock(side_effect=lambda msgs, m: len(msgs) * 100)
    token_optimizer.safety_buffer = 0
    
    # 5 messages * 100 = 500 tokens
    # Max = 300
    # Should keep System (100) + last 2 (200) = 300
    
    truncated = token_optimizer.truncate_context(messages, "model", max_context_tokens=300)
    
    assert len(truncated) == 3
    assert isinstance(truncated[0], SystemMessage)
    assert truncated[1].content == "Msg 3"
    assert truncated[2].content == "Msg 4"

@pytest.mark.asyncio
async def test_summarize_context():
    # Mock LLM service
    mock_llm_service = AsyncMock()
    mock_llm_service.get_response.return_value = "Summarized content"
    
    token_optimizer._count_tokens = MagicMock(return_value=1000) # Force optimization
    token_optimizer.safety_buffer = 0
    
    messages = [
        SystemMessage(content="System"),
        HumanMessage(content="Old 1"),
        AIMessage(content="Old 2"),
        HumanMessage(content="Old 3"),
        AIMessage(content="Old 4"),
        HumanMessage(content="New 1"),
        AIMessage(content="New 2")
    ]
    
    # Should summarize Old 1-4, keep New 1-2
    # Result: System(updated) + New 1 + New 2 = 3 messages
    
    # We need to ensure we have enough messages to trigger summarization logic (keep_count=4)
    # In the code: to_summarize = history[:-4]
    # So we need > 4 history messages.
    # Let's add more.
    messages = [SystemMessage(content="System")] + [HumanMessage(content=f"Msg {i}") for i in range(10)]
    
    # History = 10 messages. Keep last 4. Summarize first 6.
    
    optimized = await token_optimizer.summarize_context(messages, mock_llm_service, "model", max_context_tokens=500)
    
    assert len(optimized) == 5 # System + 4 kept messages
    assert "Summarized content" in optimized[0].content
    assert optimized[-1].content == "Msg 9"

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_truncate_context())
    asyncio.run(test_summarize_context())
    print("All tests passed!")
