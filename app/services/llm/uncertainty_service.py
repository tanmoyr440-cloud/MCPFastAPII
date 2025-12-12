import math
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class UncertaintyService:
    """
    Service to quantify uncertainty in LLM responses using log probabilities.
    Helps in detecting potential hallucinations.
    """

    def calculate_metrics(self, logprobs: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate uncertainty metrics from a list of token logprobs.
        
        Args:
            logprobs: List of dicts, where each dict represents a token and contains 'logprob'.
                      Structure depends on the provider, but usually has 'logprob' or 'log_prob'.
        
        Returns:
            Dict containing 'confidence_score' (0-1) and 'entropy'.
        """
        if not logprobs:
            return {"confidence_score": 0.0, "entropy": 0.0}

        total_prob = 0.0
        total_entropy = 0.0
        count = 0

        for token_data in logprobs:
            # Handle different structures (LangChain/OpenAI)
            # Sometimes it's an object, sometimes a dict
            if hasattr(token_data, "logprob"):
                log_prob = token_data.logprob
            elif isinstance(token_data, dict):
                log_prob = token_data.get("logprob") or token_data.get("log_prob")
            else:
                continue
                
            if log_prob is None:
                continue

            prob = math.exp(log_prob)
            total_prob += prob
            
            # Entropy = -sum(p * log(p))
            # Here we are summing entropy per token? 
            # Actually, entropy of the sequence is usually average entropy per token.
            # But we only have the logprob of the *chosen* token, not the full distribution.
            # So we can only approximate or use the negative log likelihood (NLL) as a proxy for uncertainty.
            # NLL = -log_prob
            total_entropy += -log_prob
            
            count += 1

        if count == 0:
            return {"confidence_score": 0.0, "entropy": 0.0}

        avg_prob = total_prob / count
        avg_entropy = total_entropy / count # This is essentially Average NLL

        return {
            "confidence_score": avg_prob,
            "entropy": avg_entropy
        }

    def is_hallucination(self, confidence: float, threshold: float = 0.7) -> bool:
        """
        Determine if a response is a potential hallucination based on confidence score.
        """
        return confidence < threshold

# Global instance
uncertainty_service = UncertaintyService()
