import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from app.agents.self_learning import SelfLearningAgent
from app.services.memory_service import memory_service

@pytest.mark.asyncio
async def test_self_learning_agent():
    # Mock LLM responses for the loop
    # 1. Draft
    # 2. Critique
    # 3. Refine
    # 4. Learn
    mock_responses = [
        "Draft Answer", 
        "Critique: Needs more detail.", 
        "Refined Answer", 
        "Lesson: Always be detailed."
    ]
    
    with patch("app.agents.self_learning.llm_service") as mock_llm_service:
        mock_llm_service.get_response = AsyncMock(side_effect=mock_responses)
        
        # Mock memory service to avoid file I/O
        with patch("app.agents.self_learning.memory_service") as mock_memory:
            mock_memory.get_relevant_learnings.return_value = []
            
            agent = SelfLearningAgent()
            response = await agent.process("How do I write a loop?")
            
            assert response == "Refined Answer"
            
            # Verify the loop calls
            assert mock_llm_service.get_response.call_count == 4
            
            # Verify learning was added
            mock_memory.add_learning.assert_called_once()
            args, _ = mock_memory.add_learning.call_args
            assert args[1] == "Lesson: Always be detailed."
