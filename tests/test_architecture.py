import pytest
import os
from app.core.prompt_manager import prompt_manager
from app.services.llm.token_service import token_service
from app.services.observability import obs_manager as observability_service
from app.services.llm.grounding_service import grounding_service
from unittest.mock import MagicMock, patch, AsyncMock

@pytest.mark.asyncio
async def test_prompt_manager():
    # Test loading common prompts
    assert "default_system" in prompt_manager.prompts.get("common", {})
    prompt = prompt_manager.get_prompt("common.default_system")
    assert prompt == "You are a helpful AI assistant."

@pytest.mark.asyncio
async def test_token_service():
    # Test token counting
    text = "Hello world"
    count = token_service.count_tokens(text)
    assert count > 0

@pytest.mark.asyncio
async def test_observability_service(tmp_path):
    pytest.skip("Observability service has changed to OpenTelemetry/Phoenix and does not use a simple log file.")
    # Test logging
    # Temporarily point to a temp file
    # original_log_file = observability_service.log_file
    # observability_service.log_file = tmp_path / "test_log.jsonl"
    
    # observability_service.log_interaction(
    #     model="test-model",
    #     prompt="test prompt",
    #     response="test response",
    #     token_usage={"total": 10},
    #     latency_ms=100
    # )
    
    # assert observability_service.log_file.exists()
    # content = observability_service.log_file.read_text()
    # assert "test-model" in content
    
    # Restore
    # observability_service.log_file = original_log_file

@pytest.mark.asyncio
async def test_grounding_service():
    # Mock web_search and LLM
    with patch("app.services.llm.grounding_service.web_search") as mock_search:
        mock_search.return_value = "Evidence: The sky is blue."
        
        mock_llm = MagicMock()
        mock_llm.get_json_response = AsyncMock(return_value=["The sky is blue"])
        mock_llm.get_response = AsyncMock(return_value="Supported")
        
        result = await grounding_service.verify_response(
            query="Is the sky blue?",
            response="The sky is blue.",
            llm_service=mock_llm
        )
        
        assert result["verified"] is True
        assert "claims" in result
        assert result["claims"] == ["The sky is blue"]
