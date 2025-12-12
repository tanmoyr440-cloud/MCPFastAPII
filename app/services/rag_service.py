"""RAG (Retrieval-Augmented Generation) service for file-based AI responses using OpenAI."""
import os
import mimetypes
from pathlib import Path
from pypdf import PdfReader
from typing import Union, Dict, Any
from app.services.llm.llm_service import llm_service, ModelType

async def extract_text_from_file(file_path: str) -> str:
    """Extract text content from a file based on its mime type."""
    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        mime_type = "application/octet-stream"
        
    try:
        if mime_type == "application/pdf":
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        elif mime_type.startswith("text/") or mime_type == "application/json":
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        else:
            return f"[Unsupported file type: {mime_type}]"
    except Exception as e:
        return f"[Error extracting text: {str(e)}]"

async def get_rag_response(prompt: str, file_path: str) -> Union[str, Dict[str, Any]]:
    """
    Get AI response using RAG with file content and user prompt.
    """
    try:
        if not os.path.exists(file_path):
            return f"Error: File not found at {file_path}"

        # Extract text from file
        file_content = await extract_text_from_file(file_path)
        
        # Create RAG prompt
        rag_prompt = f"""You are an AI assistant analyzing the provided document.

Document Content:
{file_content[:20000]}  # Truncate to avoid token limits if necessary, though modern models handle large context.

User's Question/Request:
{prompt}

Please analyze the document content above and provide a comprehensive response."""

        # Generate response
        return await llm_service.get_response(
            prompt=rag_prompt,
            model_type=ModelType.BASIC,
            system_prompt="You are a helpful AI assistant."
        )
            
    except Exception as e:
        return f"Error: {str(e)}"




async def get_rag_response_with_conversation(
    prompt: str, 
    file_path: str, 
    conversation_history: list[dict] | None = None,
    evaluate: bool = False,
    retry_on_fail: bool = False
) -> Union[str, Dict[str, Any]]:
    """
    Get AI response using RAG with file content, user prompt, and conversation context.
    """
    try:
        if not os.path.exists(file_path):
            return f"Error: File not found at {file_path}"

        file_content = await extract_text_from_file(file_path)
        
        # Build conversation context
        context = ""
        if conversation_history:
            context = "Previous conversation:\n"
            for msg in conversation_history[-5:]:
                role = "You" if msg["role"] == "assistant" else "User"
                context += f"{role}: {msg['content']}\n"
            context += "\n"

        rag_prompt = f"""You are an AI assistant analyzing the provided document in the context of an ongoing conversation.

Document Content:
{file_content[:20000]}

{context}
User's Current Question:
{prompt}

Please analyze the document and provide a response considering the conversation history."""

        return await llm_service.get_response(
            prompt=rag_prompt,
            model_type=ModelType.BASIC,
            system_prompt="You are a helpful AI assistant.",
            evaluate=evaluate,
            retry_on_fail=retry_on_fail
        )
            
    except Exception as e:
        return f"Error: {str(e)}"
