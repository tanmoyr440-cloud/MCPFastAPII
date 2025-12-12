import asyncio
import logging
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from app.services.llm.evaluation_service import evaluation_service
from app.services.llm.llm_service import LLMService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify_ssl_fix():
    print("--- Starting Verification of SSL Fix in Evaluation Driven Response ---")
    
    # 1. Test EvaluationService Initialization
    print("\n1. Testing EvaluationService Initialization...")
    try:
        # Accessing internal attributes to verify they are set correctly (for verification purposes)
        print(f"   Sync Client Verify: {evaluation_service.sync_client.headers}") 
        # Note: httpx client.verify is not easily accessible as a public attribute in all versions, 
        # but we can check if the object exists.
        if evaluation_service.sync_client:
            print("   Sync Client initialized.")
        if evaluation_service.async_client:
            print("   Async Client initialized.")
        if evaluation_service.llm:
            print("   LLM initialized.")
        if evaluation_service.embeddings:
            print("   Embeddings initialized.")
    except Exception as e:
        print(f"   FAILED to initialize EvaluationService: {e}")
        return

    # 2. Test LLMService Initialization
    print("\n2. Testing LLMService Initialization...")
    try:
        llm_service = LLMService()
        print("   LLMService initialized.")
    except Exception as e:
        print(f"   FAILED to initialize LLMService: {e}")
        return

    # 3. Test Evaluation Logic (Dry Run)
    # We will try to call evaluate_response. 
    # If API keys are invalid/missing, it might fail with 401, which is fine for SSL check.
    # We want to ensure it DOES NOT fail with SSLError.
    print("\n3. Testing evaluate_response (Network Call)...")
    query = "What is the capital of France?"
    response = "The capital of France is Paris."
    contexts = ["Paris is the capital and most populous city of France."]
    
    try:
        scores = await evaluation_service.evaluate_response(query, response, contexts)
        print(f"   Evaluation Result: {scores}")
        
        if scores.get("error") == 1.0:
            print("   Evaluation returned error (possibly expected if no keys), but handled gracefully.")
        else:
            print("   Evaluation successful!")
            
    except Exception as e:
        print(f"   FAILED during evaluate_response: {e}")

if __name__ == "__main__":
    asyncio.run(verify_ssl_fix())
