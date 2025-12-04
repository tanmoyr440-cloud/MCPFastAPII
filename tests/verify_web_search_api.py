from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from app.app import create_app
import os

app = create_app()
client = TestClient(app)

@patch("app.mcp.tools.httpx.Client")
def test_web_search_api(mock_client_class):
    print("\n--- Testing Web Search API (Mocked Serper) ---")
    
    # Setup Mock
    mock_httpx_client = MagicMock()
    mock_httpx_client.__enter__.return_value = mock_httpx_client
    mock_client_class.return_value = mock_httpx_client
    
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "organic": [
            {
                "title": "API Result Title",
                "link": "http://api.result.url",
                "snippet": "API Result Description"
            }
        ]
    }
    mock_httpx_client.post.return_value = mock_response
    
    # Mock Env Var
    with patch.dict("os.environ", {"SERPER_API_KEY": "mock_key"}):
        payload = {
            "query": "fastapi testing",
            "num_results": 1
        }
        
        response = client.post("/api/agents/tools/web_search/call", json=payload)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response JSON: {response.json()}")
        
        assert response.status_code == 200
        result = response.json()["result"]
        assert "API Result Title" in result
        assert "http://api.result.url" in result

if __name__ == "__main__":
    try:
        test_web_search_api()
        print("\nAll Tests Passed!")
    except Exception as e:
        print(f"\n[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
