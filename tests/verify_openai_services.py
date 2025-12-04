import asyncio
import os
from unittest.mock import MagicMock, patch, AsyncMock
from app.services.ai_service import get_ai_response
from app.services.rag_service import get_rag_response, get_rag_response_with_conversation

# Mock LLMService
@patch("app.services.ai_service.llm_service")
@patch("app.services.rag_service.llm_service")
def test_services(mock_llm_rag, mock_llm_ai):
    print("\n--- Testing OpenAI Services ---")
    
    # Setup Mocks
    mock_llm_ai.get_response = AsyncMock(return_value="AI Response")
    mock_llm_rag.get_response = AsyncMock(return_value="RAG Response")
    
    # 1. Test AI Service
    print("\n1. Testing AI Service")
    history = [{"role": "user", "content": "Hello"}]
    response = asyncio.run(get_ai_response(history))
    print(f"[PASS] AI Response: {response}")
    assert response == "AI Response"
    mock_llm_ai.get_response.assert_called_once()
    
    # 2. Test RAG Service (Text File)
    print("\n2. Testing RAG Service (Text File)")
    # Create dummy file
    with open("test_doc.txt", "w") as f:
        f.write("This is a test document content.")
        
    try:
        response = asyncio.run(get_rag_response("Analyze this", "test_doc.txt"))
        print(f"[PASS] RAG Response: {response}")
        assert response == "RAG Response"
        mock_llm_rag.get_response.assert_called()
        
        # Test with conversation
        response_conv = asyncio.run(get_rag_response_with_conversation("Follow up", "test_doc.txt", history))
        print(f"[PASS] RAG Context Response: {response_conv}")
        assert response_conv == "RAG Response"
        
    finally:
        if os.path.exists("test_doc.txt"):
            os.remove("test_doc.txt")

if __name__ == "__main__":
    try:
        test_services()
        print("\nAll Tests Passed!")
    except Exception as e:
        print(f"\n[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
