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
        # Pricing map (per 1k tokens)
        # Includes standard OpenAI models and specific Azure/MaaS deployments from .env
        pricing = {
            # Standard OpenAI
            "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4o": {"input": 0.005, "output": 0.015},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            
            # Azure / Custom Deployments
            "azure/genailab-maas-gpt-35-turbo": {"input": 0.0005, "output": 0.0015},
            "azure/genailab-maas-gpt-4o": {"input": 0.005, "output": 0.015},
            
            # Llama 3 (Approximate Azure MaaS pricing)
            "azure_ai/genailab-maas-Llama-3.3-70B-Instruct": {"input": 0.0007, "output": 0.0009},
            
            # DeepSeek (Approximate pricing based on V2/V3 public rates)
            "azure_ai/genailab-maas-DeepSeek-R1": {"input": 0.00014, "output": 0.00028},
            "azure_ai/genailab-maas-DeepSeek-V3-0324": {"input": 0.00014, "output": 0.00028},
            
            # Experimental / Other
            "azure_ai/genailab-maas-Llama-4-Maverick-17B-128E-Instruct-FP8": {"input": 0.0005, "output": 0.001},
        }
        
        # Exact match
        if model in pricing:
            model_pricing = pricing[model]
        else:
            # Fallback heuristics
            if "gpt-4" in model:
                model_pricing = pricing["gpt-4o"] # Default to 4o for unknown GPT-4 variants
            elif "gpt-3.5" in model:
                model_pricing = pricing["gpt-3.5-turbo"]
            elif "Llama" in model:
                model_pricing = pricing["azure_ai/genailab-maas-Llama-3.3-70B-Instruct"]
            elif "DeepSeek" in model:
                model_pricing = pricing["azure_ai/genailab-maas-DeepSeek-V3-0324"]
            else:
                model_pricing = pricing["gpt-3.5-turbo"] # Ultimate fallback
        
        input_cost = (prompt_tokens / 1000) * model_pricing["input"]
        output_cost = (completion_tokens / 1000) * model_pricing["output"]
        
        return input_cost + output_cost

# Global instance
token_service = TokenService()
