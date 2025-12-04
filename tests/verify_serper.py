import os
import json
from unittest.mock import MagicMock, patch
from app.mcp.tools import web_search

@patch("app.mcp.tools.httpx.Client")
def test_serper_search(mock_client_class):
    print("\n--- Testing Serper Search (Mocked) ---")
    
    # Setup Mock
    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client_class.return_value = mock_client
    
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "organic": [
            {
                "title": "Serper API",
                "link": "https://serper.dev",
                "snippet": "Google Search API"
            },
            {
                "title": "Documentation",
                "link": "https://serper.dev/docs",
                "snippet": "API Documentation"
            }
        ]
    }
    mock_client.post.return_value = mock_response
    
    # Mock Env Var
    with patch.dict("os.environ", {"SERPER_API_KEY": "mock_key"}):
        results = web_search("serper api")
        print(f"[PASS] Search Results:\n{results}")
        
        assert "Serper API" in results
        assert "https://serper.dev" in results
        assert "Google Search API" in results

if __name__ == "__main__":
    try:
        test_serper_search()
        print("\nAll Tests Passed!")
    except Exception as e:
        print(f"\n[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
