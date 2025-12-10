import logging
from typing import Dict, List, Optional
import tiktoken

logger = logging.getLogger(__name__)

class TokenService:
    """
    Service to track and optimize token usage.
    """
    
    def __init__(self, default_model: str = "gpt-3.5-turbo"):
        self.default_model = default_model
        # Cache encoders to avoid re-initialization overhead
        self._encoders = {}

    def _get_encoder(self, model_name: str):
        """Get or create a tiktoken encoder for the specified model."""
        if model_name not in self._encoders:
            try:
                self._encoders[model_name] = tiktoken.encoding_for_model(model_name)
            except KeyError:
                logger.warning(f"Model {model_name} not found in tiktoken. Falling back to cl100k_base.")
                self._encoders[model_name] = tiktoken.get_encoding("cl100k_base")
        return self._encoders[model_name]

    def count_tokens(self, text: str, model: Optional[str] = None) -> int:
        """
        Count the number of tokens in a text string.
        """
        model = model or self.default_model
        encoder = self._get_encoder(model)
        return len(encoder.encode(text))

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int, model: str) -> float:
        """
        Estimate the cost of the interaction.
        Note: Prices are hardcoded here for simplicity, but should ideally be in a config.
        """
        # Simplified pricing map (per 1k tokens)
        pricing = {
            "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            # Add others as needed
        }
        
        # Default to gpt-3.5-turbo pricing if unknown
        model_pricing = pricing.get(model, pricing["gpt-3.5-turbo"])
        
        input_cost = (prompt_tokens / 1000) * model_pricing["input"]
        output_cost = (completion_tokens / 1000) * model_pricing["output"]
        
        return input_cost + output_cost

# Global instance
token_service = TokenService()
