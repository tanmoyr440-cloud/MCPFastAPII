"""Tests for AI service integration."""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.services.ai_service import get_ai_response
import os

@pytest.mark.asyncio
async def test_get_ai_response_success():
    """Test successful AI response generation."""
    with patch("app.services.ai_service.llm_service.get_response") as mock_get_response:
        mock_get_response.return_value = "This is a test response"
        
        conversation = [{"role": "user", "content": "Hello"}]
        result = await get_ai_response(conversation)
        
        assert result == "This is a test response"

@pytest.mark.asyncio
async def test_get_ai_response_error():
    """Test AI response with error."""
    with patch("app.services.ai_service.llm_service.get_response") as mock_get_response:
        mock_get_response.side_effect = Exception("API Error")
        
        conversation = [{"role": "user", "content": "Hello"}]
        result = await get_ai_response(conversation)
        
        assert "Error" in result
        assert "API Error" in result

@pytest.mark.asyncio
async def test_get_ai_response_structured():
    """Test AI response with structured data."""
    with patch("app.services.ai_service.llm_service.get_response") as mock_get_response:
        mock_get_response.return_value = {
            "content": "Structured response",
            "usage_metrics": {"total_tokens": 10}
        }
        
        conversation = [{"role": "user", "content": "Hello"}]
        result = await get_ai_response(conversation)
        
        assert isinstance(result, dict)
        assert result["content"] == "Structured response"

