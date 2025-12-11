import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from app.services.evaluation_service import EvaluationService
from app.services.llm_service import LLMService

@pytest.fixture
def evaluation_service():
    return EvaluationService()

def test_check_thresholds(evaluation_service):
    scores = {"faithfulness": 0.8, "answer_relevancy": 0.9}
    assert evaluation_service.check_thresholds(scores) is True
    
    scores = {"faithfulness": 0.5, "answer_relevancy": 0.9}
    assert evaluation_service.check_thresholds(scores) is False

@pytest.mark.asyncio
async def test_evaluate_response_mocked(evaluation_service):
    with patch("app.services.evaluation_service.evaluate") as mock_evaluate:
        mock_evaluate.return_value = {"faithfulness": 0.8, "answer_relevancy": 0.9}
        
        scores = await evaluation_service.evaluate_response("query", "response", ["context"])
        
        assert scores["faithfulness"] == 0.8
        assert scores["answer_relevancy"] == 0.9

@pytest.mark.asyncio
async def test_reflexion_loop():
    llm_service = LLMService()
    
    # Mock LLM response
    mock_response = MagicMock()
    mock_response.content = "Initial Answer"
    mock_response.response_metadata = {}
    
    # Mock LLM chain
    with patch.object(llm_service, "_get_llm") as mock_get_llm:
        mock_llm = MagicMock()
        
        # Scenario: First attempt fails, second succeeds
        async def side_effect(*args, **kwargs):
            messages = args[0]
            last_msg = messages[-1].content
            if "Critique" in last_msg:
                mock_response.content = "Improved Answer"
            else:
                mock_response.content = "Initial Answer"
            return mock_response
            
        mock_llm.ainvoke = AsyncMock(side_effect=side_effect)
        mock_get_llm.return_value = mock_llm
        
        # Mock EvaluationService
        with patch("app.services.llm_service.evaluation_service") as mock_eval_service:
            # First eval fails, second passes
            mock_eval_service.evaluate_response = AsyncMock(side_effect=[
                {"faithfulness": 0.5, "answer_relevancy": 0.5},
                {"faithfulness": 0.9, "answer_relevancy": 0.9}
            ])
            mock_eval_service.check_thresholds.side_effect = [False, True]
            
            # Mock other services
            with patch("app.services.llm_service.token_service"):
                with patch("app.services.llm_service.grounding_service"):
                     response = await llm_service.get_response(
                         prompt="Question",
                         evaluate=True,
                         retry_on_fail=True
                     )
                     
                     assert isinstance(response, dict)
                     assert response["content"] == "Improved Answer"
                     assert response["evaluation_scores"]["faithfulness"] == 0.9
                     assert not response.get("is_flagged", False)
                     
                     # Verify evaluate_response was called twice
                     assert mock_eval_service.evaluate_response.call_count == 2

@pytest.mark.asyncio
async def test_reflexion_loop_failure():
    llm_service = LLMService()
    
    # Mock LLM response
    mock_response = MagicMock()
    mock_response.content = "Bad Answer"
    mock_response.response_metadata = {}
    
    # Mock LLM chain
    with patch.object(llm_service, "_get_llm") as mock_get_llm:
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        mock_get_llm.return_value = mock_llm
        
        # Mock EvaluationService
        with patch("app.services.llm_service.evaluation_service") as mock_eval_service:
            # All attempts fail
            mock_eval_service.evaluate_response = AsyncMock(return_value={"faithfulness": 0.4, "answer_relevancy": 0.4})
            mock_eval_service.check_thresholds.return_value = False
            
            # Mock other services
            with patch("app.services.llm_service.token_service"):
                with patch("app.services.llm_service.grounding_service"):
                     response = await llm_service.get_response(
                         prompt="Question",
                         evaluate=True,
                         retry_on_fail=True
                     )
                     
                     assert isinstance(response, dict)
                     assert response["content"] == "Bad Answer"
                     assert response["is_flagged"] is True
