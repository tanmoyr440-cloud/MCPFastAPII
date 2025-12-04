"""RAG (Retrieval-Augmented Generation) service for file-based AI responses."""
import os
import google.generativeai as genai
from pathlib import Path
import mimetypes


async def get_rag_response(prompt: str, file_path: str) -> str:
    """
    Get AI response using RAG with file content and user prompt.
    
    Args:
        prompt: User's question or request
        file_path: Path to the uploaded file to analyze
        
    Returns:
        AI response based on file content and prompt
    """
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return "Error: GEMINI_API_KEY environment variable not set. Create a .env file in the backend folder with GEMINI_API_KEY=<your-key>"

        # Verify file exists
        if not os.path.exists(file_path):
            return f"Error: File not found at {file_path}"

        # Configure Gemini API
        genai.configure(api_key=api_key)
        
        # Initialize model
        model = genai.GenerativeModel("gemini-2.0-flash")

        # Get file mime type
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = "application/octet-stream"

        # Upload file to Gemini
        file_obj = genai.upload_file(file_path, mime_type=mime_type)
        
        try:
            # Create RAG prompt that includes file context
            rag_prompt = f"""You are an AI assistant analyzing the provided document.

User's Question/Request:
{prompt}

Please analyze the attached file and provide a comprehensive response to the user's question based on the file content."""

            # Generate response with file context
            response = model.generate_content(
                [rag_prompt, file_obj],
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=2048,
                    temperature=0.7,
                ),
            )

            return response.text
        finally:
            # Clean up uploaded file
            genai.delete_file(file_obj.name)
            
    except Exception as e:
        return f"Error: {str(e)}"


async def get_rag_response_with_conversation(
    prompt: str, 
    file_path: str, 
    conversation_history: list[dict] | None = None
) -> str:
    """
    Get AI response using RAG with file content, user prompt, and conversation context.
    
    Args:
        prompt: User's current question or request
        file_path: Path to the uploaded file to analyze
        conversation_history: List of previous messages in the conversation
        
    Returns:
        AI response based on file content, prompt, and conversation context
    """
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return "Error: GEMINI_API_KEY environment variable not set."

        if not os.path.exists(file_path):
            return f"Error: File not found at {file_path}"

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")

        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = "application/octet-stream"

        file_obj = genai.upload_file(file_path, mime_type=mime_type)
        
        try:
            # Build conversation context
            context = ""
            if conversation_history:
                context = "Previous conversation:\n"
                for msg in conversation_history[-5:]:  # Last 5 messages for context
                    role = "You" if msg["role"] == "assistant" else "User"
                    context += f"{role}: {msg['content']}\n"
                context += "\n"

            rag_prompt = f"""You are an AI assistant analyzing the provided document in the context of an ongoing conversation.

{context}
User's Current Question:
{prompt}

Please analyze the attached file and provide a response to the user's question based on the file content, considering the conversation history."""

            response = model.generate_content(
                [rag_prompt, file_obj],
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=2048,
                    temperature=0.7,
                ),
            )

            return response.text
        finally:
            genai.delete_file(file_obj.name)
            
    except Exception as e:
        return f"Error: {str(e)}"
