import logging
from typing import List, Dict, Any, Optional
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from app.services.llm.token_service import token_service

logger = logging.getLogger(__name__)

class TokenOptimizerService:
    """
    Service to optimize conversation context by truncating or summarizing 
    messages to fit within token limits.
    """
    
    def __init__(self):
        # Default safety buffer
        self.safety_buffer = 500
        
    def _count_tokens(self, messages: List[BaseMessage], model: str) -> int:
        """Count total tokens in a list of messages."""
        text = ""
        for msg in messages:
            text += msg.content + "\n"
        return token_service.count_tokens(text, model)

    def should_optimize(self, messages: List[BaseMessage], model: str, max_context_tokens: int = 4000) -> bool:
        """Check if optimization is needed."""
        total_tokens = self._count_tokens(messages, model)
        return total_tokens > max_context_tokens

    def truncate_context(self, messages: List[BaseMessage], model: str, max_context_tokens: int = 4000) -> List[BaseMessage]:
        """
        Truncate context by removing oldest messages (excluding System prompt).
        Keeps the System prompt and the most recent messages that fit.
        """
        if not self.should_optimize(messages, model, max_context_tokens):
            return messages
            
        logger.info("Truncating context to fit token limit...")
        
        # Separate System message (always keep)
        system_message = None
        other_messages = []
        
        for msg in messages:
            if isinstance(msg, SystemMessage):
                system_message = msg
            else:
                other_messages.append(msg)
                
        # Calculate available tokens for history
        sys_tokens = self._count_tokens([system_message], model) if system_message else 0
        available_tokens = max_context_tokens - sys_tokens - self.safety_buffer
        
        if available_tokens <= 0:
            logger.warning("System prompt is too large! Returning only last message.")
            return [system_message, other_messages[-1]] if system_message and other_messages else messages[-2:]

        # Reconstruct history from end (most recent) to start
        optimized_history = []
        current_tokens = 0
        
        for msg in reversed(other_messages):
            msg_tokens = self._count_tokens([msg], model)
            if current_tokens + msg_tokens <= available_tokens:
                optimized_history.insert(0, msg)
                current_tokens += msg_tokens
            else:
                break
                
        result = [system_message] + optimized_history if system_message else optimized_history
        logger.info(f"Context truncated. Kept {len(result)}/{len(messages)} messages.")
        return result

    async def summarize_context(self, messages: List[BaseMessage], llm_service, model: str, max_context_tokens: int = 4000) -> List[BaseMessage]:
        """
        Summarize older context into a single System message update.
        """
        if not self.should_optimize(messages, model, max_context_tokens):
            return messages

        logger.info("Summarizing context to fit token limit...")
        
        # 1. Identify messages to summarize vs keep
        # We want to keep the last N messages intact for immediate context
        # and summarize the rest.
        
        system_message = None
        history_messages = []
        
        for msg in messages:
            if isinstance(msg, SystemMessage):
                system_message = msg
            else:
                history_messages.append(msg)
        
        # Keep last 4 messages (approx) or based on token count
        keep_count = 4
        if len(history_messages) <= keep_count:
            return self.truncate_context(messages, model, max_context_tokens)
            
        to_summarize = history_messages[:-keep_count]
        to_keep = history_messages[-keep_count:]
        
        # 2. Generate Summary
        # Convert messages to text format for summarization
        conversation_text = ""
        for msg in to_summarize:
            role = "User" if isinstance(msg, HumanMessage) else "Assistant"
            conversation_text += f"{role}: {msg.content}\n"
            
        summary_prompt = (
            "Summarize the following conversation history into a concise paragraph. "
            "Retain key facts, user preferences, and important decisions. "
            "Ignore trivial pleasantries.\n\n"
            f"History:\n{conversation_text}"
        )
        
        try:
            # Use a cheap model for summarization
            summary = await llm_service.get_response(
                prompt=summary_prompt,
                model_type="MODEL_CHAT_BASIC", # Use basic model
                system_prompt="You are a helpful summarizer.",
                temperature=0.3,
                max_tokens=500
            )
            
            logger.info(f"Generated summary: {summary[:50]}...")
            
            # 3. Create new System Message with Summary
            original_sys_content = system_message.content if system_message else "You are a helpful AI assistant."
            new_sys_content = f"{original_sys_content}\n\n[Previous Conversation Summary]: {summary}"
            
            new_system_message = SystemMessage(content=new_sys_content)
            
            result = [new_system_message] + to_keep
            return result
            
        except Exception as e:
            logger.error(f"Summarization failed: {e}. Falling back to truncation.")
            return self.truncate_context(messages, model, max_context_tokens)

token_optimizer = TokenOptimizerService()
