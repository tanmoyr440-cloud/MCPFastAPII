"""Base Agent class."""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from app.services.llm.llm_service import llm_service, ModelType
from app.core.prompt_manager import prompt_manager

class BaseAgent(ABC):
    """Abstract base class for AI Agents."""
    
    def __init__(self, name: str, model_type: ModelType = ModelType.BASIC):
        """
        Initialize the agent.
        
        Args:
            name: Name of the agent
            model_type: ModelType enum for the model to use
        """
        self.name = name
        self.model_type = model_type
        # Load default system prompt from PromptManager
        self.system_prompt = prompt_manager.get_prompt("common.default_system")
        self.history: List[Dict[str, str]] = []

    def set_system_prompt(self, prompt_key: str, **kwargs):
        """Set the system prompt using a key from PromptManager."""
        self.system_prompt = prompt_manager.get_prompt(prompt_key, **kwargs)

    def add_message(self, role: str, content: str):
        """Add a message to the history."""
        self.history.append({"role": role, "content": content})

    def clear_history(self):
        """Clear the message history."""
        self.history = []

    @abstractmethod
    async def process(self, user_input: str) -> str:
        """Process user input and return a response."""
        pass

    async def _get_completion(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> str:
        """Helper to get completion from LLMService."""
        # Convert history to prompt context if needed, or just pass last user message + history context
        # For simplicity, we'll construct a prompt from history
        
        # Note: LLMService takes a single prompt string and system prompt.
        # We need to serialize the history into the prompt or update LLMService to accept messages.
        # Given LLMService's current signature, we'll format the history into the prompt.
        
        conversation_text = ""
        for msg in messages:
            if msg["role"] != "system": # System prompt is passed separately
                conversation_text += f"{msg['role'].capitalize()}: {msg['content']}\n"
        
        return await llm_service.get_response(
            prompt=conversation_text,
            model_type=self.model_type,
            system_prompt=self.system_prompt,
            temperature=temperature
        )
