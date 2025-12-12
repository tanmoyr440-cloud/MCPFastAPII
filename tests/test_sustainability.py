import pytest
from unittest.mock import MagicMock, patch
from app.services.observability import obs_manager
from app.services.llm.llm_service import LLMService, ModelType
from app.services.ai_service import get_ai_response

def test_calculate_carbon_footprint():
    # Test GPT-4 calculation
    # 1000 tokens * 0.0003 kWh/1k * 0.475 kg/kWh = 0.0001425 kg
    footprint = obs_manager.calculate_carbon_footprint(1000, "gpt-4")
    assert footprint == pytest.approx(0.0001425)
    
    # Test GPT-3.5 calculation
    # 1000 tokens * 0.00005 kWh/1k * 0.475 kg/kWh = 0.00002375 kg
    footprint = obs_manager.calculate_carbon_footprint(1000, "gpt-3.5-turbo")
    assert footprint == pytest.approx(0.00002375)

@pytest.mark.asyncio
async def test_llm_service_returns_metrics():
    # Mock LLMService and its dependencies
    llm_service = LLMService()
    
    # Mock the LLM response
    mock_response = MagicMock()
    mock_response.content = "Test response"
    mock_response.response_metadata = {
        "token_usage": {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30
        }
    }
    
    # Mock the LLM chain
    with patch.object(llm_service, "_get_llm") as mock_get_llm:
        mock_llm = MagicMock()
        # Make ainvoke an async method
        async def async_return(*args, **kwargs):
            return mock_response
        mock_llm.ainvoke.side_effect = async_return
        
        mock_get_llm.return_value = mock_llm
        
        # We also need to mock token_service because middleware uses it
        with patch("app.services.llm.token_service.token_service") as mock_token_service:
            mock_token_service.count_tokens.side_effect = [10, 20] # input, output
            
            # Ensure observability is enabled
            with patch.object(obs_manager, "is_enabled", return_value=True):
                response = await llm_service.get_response("Test prompt")
                
                assert isinstance(response, dict)
                assert response["content"] == "Test response"
                assert "usage_metrics" in response
                metrics = response["usage_metrics"]
                assert metrics["input_tokens"] == 10
                assert metrics["output_tokens"] == 20
                assert metrics["total_tokens"] == 30
                assert "cost_usd" in metrics
                assert "carbon_footprint_kg" in metrics

@pytest.mark.asyncio
async def test_ai_service_returns_structured_data():
    # Mock llm_service.get_response to return dict with metrics
    with patch("app.services.ai_service.llm_service.get_response") as mock_get_response:
        mock_get_response.return_value = {
            "content": "Test Answer",
            "usage_metrics": {
                "input_tokens": 10,
                "output_tokens": 20,
                "total_tokens": 30,
                "cost_usd": 0.001,
                "carbon_footprint_kg": 0.0005
            }
        }


        response = await get_ai_response([{"role": "user", "content": "Hi"}])
        
        assert isinstance(response, dict)
        assert response["content"] == "Test Answer"
        assert "usage_metrics" in response
        assert response["usage_metrics"]["total_tokens"] == 30

@pytest.mark.asyncio
async def test_rag_service_returns_structured_data():
    from app.services.rag_service import get_rag_response_with_conversation
    
    # Mock llm_service.get_response to return dict with metrics
    with patch("app.services.rag_service.llm_service.get_response") as mock_get_response:
        mock_get_response.return_value = {
            "content": "RAG Answer",
            "usage_metrics": {
                "input_tokens": 15,
                "output_tokens": 25,
                "total_tokens": 40,
                "cost_usd": 0.002,
                "carbon_footprint_kg": 0.0008
            }
        }
        
        # Mock file existence and content extraction
        with patch("os.path.exists", return_value=True):
            with patch("app.services.rag_service.extract_text_from_file", return_value="Document content"):
                response = await get_rag_response_with_conversation(
                    "Question", 
                    "path/to/file", 
                    [{"role": "user", "content": "Hi"}]
                )
                
                assert isinstance(response, dict)
                assert response["content"] == "RAG Answer"
                assert "usage_metrics" in response
                assert response["usage_metrics"]["total_tokens"] == 40

