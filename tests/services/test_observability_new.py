import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from app.services.middleware.observability import ObservabilityMiddleware
from app.services.observability import obs_manager

@pytest.mark.asyncio
async def test_observability_middleware():
    # Mock context
    context = {
        "model_type": "BASIC",
        "deployment_name": "gpt-3.5-turbo",
        "prompt": "Test prompt",
        "system_prompt": "System prompt",
        "temperature": 0.7,
        "final_content": "Test response",
        "guardrails_status": "allowed",
        "uncertainty_metrics": {"confidence_score": 0.9, "is_uncertain": False}
    }
    
    middleware = ObservabilityMiddleware()
    
    # Mock obs_manager.is_enabled to return True
    with patch.object(obs_manager, "is_enabled", return_value=True):
        # Mock tracer
        with patch("app.services.middleware.observability.tracer") as mock_tracer:
            mock_span = MagicMock()
            mock_tracer.start_span.return_value = mock_span
            
            # Mock token_service
            with patch("app.services.llm.token_service.token_service") as mock_token_service:
                mock_token_service.count_tokens.return_value = 10
                
                # Test process_request
                await middleware.process_request(context)
                
                mock_tracer.start_span.assert_called_once()
                assert context["otel_span"] == mock_span
                assert "start_time" in context
                
                # Test process_response
                await middleware.process_response(context)
                
                # Verify attributes were set
                mock_span.set_attribute.assert_any_call("llm.response", "Test response")
                mock_span.set_attribute.assert_any_call("llm.guardrails.status", "allowed")
                mock_span.set_attribute.assert_any_call("llm.uncertainty.confidence", 0.9)
                mock_span.set_attribute.assert_any_call("llm.input_tokens", 10)
                mock_span.set_attribute.assert_any_call("llm.output_tokens", 10)
                mock_span.set_attribute.assert_any_call("llm.total_tokens", 20)
                
                # Verify span ended
                mock_span.end.assert_called_once()
