import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from app.services.llm.llm_service import LLMService, ModelType
from app.services.guardrails_service import guardrails_service
@patch("app.services.llm.llm_service.ChatOpenAI")
def test_guardrails_integration(mock_openai_class):
    print("\n--- Testing Guardrails Integration in LLMService ---")
    
    # Setup Mock
    mock_llm = MagicMock()
    mock_openai_class.return_value = mock_llm
    
    service = LLMService()
    
    # 1. Test Clean Content (Should Pass)
    print("\n1. Testing Clean Content")
    mock_response_clean = MagicMock()
    mock_response_clean.content = "This is safe content."
    mock_llm.ainvoke = AsyncMock(return_value=mock_response_clean)
    
    response = asyncio.run(service.get_response("Hello"))
    print(f"[PASS] Response: {response}")
    assert response == "This is safe content."
    
    # 2. Test Toxic Content (Should Block)
    print("\n2. Testing Toxic Content")
    mock_response_toxic = MagicMock()
    # Using a phrase that triggers the toxicity regex in guardrails_service.py
    # Pattern: r"\b(will|gonna|...)\s+(kill|murder...)\b"
    mock_response_toxic.content = "I will kill everyone." 
    mock_llm.ainvoke = AsyncMock(return_value=mock_response_toxic)
    
    response = asyncio.run(service.get_response("Generate toxicity"))
    print(f"[PASS] Blocked Response: {response}")
    assert "I cannot provide a response" in response
    
    # 3. Test PII Redaction (Should Redact)
    print("\n3. Testing PII Redaction")
    mock_response_pii = MagicMock()
    mock_response_pii.content = "My email is test@example.com."
    mock_llm.ainvoke = AsyncMock(return_value=mock_response_pii)
    
    response = asyncio.run(service.get_response("What is your email?"))
    print(f"[PASS] Redacted Response: {response}")
    assert "[EMAIL_REDACTED]" in response
    assert "test@example.com" not in response

    # 4. Test JSON Redaction (Should Redact and Parse)
    print("\n4. Testing JSON Redaction")
    mock_response_json = MagicMock()
    mock_response_json.content = '{"email": "user@example.com", "name": "John"}'
    mock_llm.ainvoke = AsyncMock(return_value=mock_response_json)
    
    response = asyncio.run(service.get_json_response("Get user info"))
    print(f"[PASS] JSON Response: {response}")
    assert response["email"] == "[EMAIL_REDACTED]"
    assert response["name"] == "John"

if __name__ == "__main__":
    # Mock env vars
    import os
    if "API_KEY" not in os.environ:
        os.environ["API_KEY"] = "mock_key"
        os.environ["API_ENDPOINT"] = "https://mock.openai.azure.com"
        os.environ["MODEL_CHAT_BASIC"] = "gpt-35-turbo"
        
    try:
        test_guardrails_integration()
        print("\nAll Tests Passed!")
    except Exception as e:
        print(f"\n[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
