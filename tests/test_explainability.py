import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from app.services.llm_service import llm_service

@pytest.mark.asyncio
async def test_explainability():
    # Mock LLM response with reasoning tags
    mock_content = "<reasoning>Thinking step by step...</reasoning><answer>The answer is 42.</answer>"
    
    with patch.object(llm_service, "_get_llm") as mock_get_llm:
        mock_llm_instance = MagicMock()
        mock_llm_instance.ainvoke = AsyncMock(return_value=MagicMock(content=mock_content))
        mock_get_llm.return_value = mock_llm_instance
        
        # Mock token service to avoid errors
        with patch("app.services.llm_service.token_service") as mock_token:
            mock_token.count_tokens.return_value = 10
            
            # Mock observability to avoid errors
            with patch("app.services.llm_service.observability_service"):
                
                result = await llm_service.get_response(
                    prompt="What is the meaning of life?",
                    explain=True
                )
                
                assert isinstance(result, dict)
                assert result["content"] == "The answer is 42."
                assert result["reasoning"] == "Thinking step by step..."
