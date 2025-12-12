import asyncio
from app.services.llm.llm_service import LLMService, ModelType
from langchain_core.messages import AIMessage
import os

# Mock dependencies
@patch("app.services.llm.llm_service.ChatOpenAI")
def test_llm_service(mock_openai_class):
    print("\n--- Testing LLM Service (Mocked LangChain) ---")
    
    # Setup Mock
    mock_llm = MagicMock()
    mock_openai_class.return_value = mock_llm
    
    service = LLMService()
    
    # 1. Test Text Response
    print("\n1. Testing Text Response (Basic Model)")
    mock_response_text = MagicMock()
    mock_response_text.content = "Hello, I am an AI."
    mock_llm.ainvoke = AsyncMock(return_value=mock_response_text) # Use AsyncMock
    
    # Mock env var for deployment name
    with patch.dict("os.environ", {"MODEL_CHAT_BASIC": "gpt-35-turbo"}):
        response = asyncio.run(service.get_response("Hi", ModelType.BASIC))
        print(f"[PASS] Response: {response}")
        assert response == "Hello, I am an AI."

    # 2. Test JSON Response
    print("\n2. Testing JSON Response (Reasoning Model)")
    json_content = {"answer": 42, "explanation": "Life, universe, everything"}
    
    # Simpler approach: Mock the chain creation
    mock_chain = MagicMock()
    mock_chain.ainvoke = AsyncMock(return_value=json_content) # Use AsyncMock
    
    # We need to intercept the pipe operator or just mock the result if we can't easily mock the pipe.
    # But since we are mocking AzureChatOpenAI class, the instance 'llm' is a MagicMock.
    # llm | parser returns a new object (RunnableSequence).
    # We can configure the mock_llm.__or__ to return our mock_chain.
    mock_llm.__or__.return_value = mock_chain
    
    with patch.dict("os.environ", {"MODEL_REASONING": "deepseek-r1"}):
        response = asyncio.run(service.get_json_response("What is the answer?", ModelType.REASONING))
        print(f"[PASS] JSON Response: {response}")
        assert response["answer"] == 42
        assert response["explanation"] == "Life, universe, everything"

if __name__ == "__main__":
    # Mock env vars for init if needed
    import os
    if "API_KEY" not in os.environ:
        os.environ["API_KEY"] = "mock_key"
        os.environ["API_ENDPOINT"] = "https://mock.openai.azure.com"
        
    try:
        test_llm_service()
        print("\nAll Tests Passed!")
    except Exception as e:
        print(f"\n[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
