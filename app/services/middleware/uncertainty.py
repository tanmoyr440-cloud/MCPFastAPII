from typing import Dict, Any
import logging
from app.services.middleware.base import BaseMiddleware
from app.services.llm.uncertainty_service import uncertainty_service

logger = logging.getLogger(__name__)

class UncertaintyMiddleware(BaseMiddleware):
    """
    Middleware for calculating uncertainty metrics (hallucination detection).
    """

    async def process_request(self, context: Dict[str, Any]) -> None:
        if context.get("check_uncertainty"):
            # Ensure model_kwargs has logprobs
            model_kwargs = context.get("model_kwargs", {})
            model_kwargs["logprobs"] = True
            context["model_kwargs"] = model_kwargs

    async def process_response(self, context: Dict[str, Any]) -> None:
        if context.get("check_uncertainty"):
            response_metadata = context.get("response_metadata", {})
            
            try:
                logprobs = []
                if "logprobs" in response_metadata:
                    logprobs = response_metadata["logprobs"]["content"]
                
                metrics = uncertainty_service.calculate_metrics(logprobs)
                metrics["is_uncertain"] = uncertainty_service.is_hallucination(metrics["confidence_score"])
                
                context["uncertainty_metrics"] = metrics
            except Exception as e:
                logger.warning(f"Failed to calculate uncertainty: {e}")
