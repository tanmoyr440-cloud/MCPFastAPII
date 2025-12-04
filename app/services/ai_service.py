"""AI service for Gemini integration."""
import os
import google.generativeai as genai


async def get_ai_response(conversation_history: list[dict]) -> str:
    """
    Get response from Google Gemini Flash 2.5 using conversation history.
    
    Args:
        conversation_history: List of message dicts with 'role' and 'content'
        
    Returns:
        AI response text
    """
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return "Error: GEMINI_API_KEY environment variable not set. Create a .env file in the backend folder with GEMINI_API_KEY=<your-key>"

        # Configure Gemini API
        genai.configure(api_key=api_key)
        
        # Initialize model
        model = genai.GenerativeModel("gemini-2.0-flash")

        # Convert conversation history to Gemini format
        # Gemini uses different role names: 'user' and 'model'
        gemini_history = [
            {
                "role": "user" if msg["role"] == "user" else "model",
                "parts": [msg["content"]]
            }
            for msg in conversation_history
        ]

        # Create message with Gemini
        response = model.generate_content(
            contents=gemini_history[-1]["parts"][-1] if gemini_history else "",
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=1024,
            ),
        )

        # Extract response text
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"
