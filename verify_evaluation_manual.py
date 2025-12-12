import asyncio
import logging
from unittest.mock import MagicMock, AsyncMock, patch
from app.services.llm_service import LLMService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify_evaluation_flow():
    print("--- Starting Manual Verification of Evaluation Driven Response ---")
    
    llm_service = LLMService()
    
    # Mocking external dependencies to avoid needing real API keys for this check
    print("1. Mocking LLM and Evaluation Service...")
    
    # Mock LLM Response
    mock_response = MagicMock()
    mock_response.content = "This is a verified response."
    mock_response.response_metadata = {}
    
    # Mock Evaluation Service
    mock_scores = {"faithfulness": 0.95, "answer_relevancy": 0.98}
    
    with patch.object(llm_service, "_get_llm") as mock_get_llm, \
         patch("app.services.llm_service.evaluation_service") as mock_eval_service, \
         patch("app.services.llm_service.token_service"), \
         patch("app.services.llm_service.grounding_service"):
        
        # Setup Mocks
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        mock_get_llm.return_value = mock_llm
        
        mock_eval_service.evaluate_response = AsyncMock(return_value=mock_scores)
        mock_eval_service.check_thresholds.return_value = True
        
        print("2. Calling LLMService.get_response with evaluate=True...")
        
        # Call the service
        result = await llm_service.get_response(
            prompt="Test Prompt",
            evaluate=True,
            retry_on_fail=True
        )
        
        print("\n--- Result ---")
        if isinstance(result, dict):
            print(f"Content: {result.get('content')}")
            print(f"Evaluation Scores: {result.get('evaluation_scores')}")
            print(f"Is Flagged: {result.get('is_flagged')}")
            
            if result.get("evaluation_scores") == mock_scores:
                print("\nSUCCESS: Evaluation scores were correctly returned!")
            else:
                print("\nFAILURE: Evaluation scores missing or incorrect.")
        else:
            print(f"Result: {result}")
            print("\nFAILURE: Expected a dictionary response with evaluation scores.")

if __name__ == "__main__":
    asyncio.run(verify_evaluation_flow())
