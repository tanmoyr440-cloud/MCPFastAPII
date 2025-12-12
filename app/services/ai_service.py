"""AI service for OpenAI integration."""
from app.services.llm.llm_service import llm_service, ModelType

from typing import Union, Dict, Any

async def get_ai_response(
    conversation_history: list[dict],
    evaluate: bool = False,
    retry_on_fail: bool = False
) -> Union[str, Dict[str, Any]]:
    """
    Get response from OpenAI using conversation history.
    
    Args:
        conversation_history: List of message dicts with 'role' and 'content'
        
    Returns:
        AI response text
    """
    try:
        # Convert history to prompt context
        # LLMService currently takes a prompt string. 
        # We can construct the prompt from the history.
        
        # Extract the last user message as the main prompt
        last_message = conversation_history[-1]["content"] if conversation_history else ""
        
        # Build context from previous messages
        context = ""
        if len(conversation_history) > 1:
            context = "Previous conversation:\n"
            for msg in conversation_history[:-1]:
                role = msg["role"].capitalize()
                content = msg["content"]
                context += f"{role}: {content}\n"
            context += "\n"
            
        full_prompt = f"{context}User: {last_message}"
        
        # Use LLMService to get response
        response = await llm_service.get_response(
            prompt=full_prompt,
            model_type=ModelType.BASIC, # Default to basic model
            system_prompt="You are a helpful AI assistant.",
            evaluate=evaluate,
            retry_on_fail=retry_on_fail
        )

        if isinstance(response, dict):
            # Return the structured response directly
            # The caller (sessions.py) will handle extraction
            return response
            
        return response
    except Exception as e:
        return f"Error: {str(e)}"
