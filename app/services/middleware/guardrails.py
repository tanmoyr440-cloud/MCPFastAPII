from typing import Dict, Any
import logging
from app.services.middleware.base import BaseMiddleware
from app.services.guardrails_service import validate_all_guardrails

logger = logging.getLogger(__name__)

class GuardrailsMiddleware(BaseMiddleware):
    """
    Middleware for applying safety guardrails to LLM outputs.
    """

    async def process_response(self, context: Dict[str, Any]) -> None:
        raw_content = context.get("raw_content", "")
        
        guardrail_result = validate_all_guardrails(raw_content)
        
        final_content = guardrail_result["final_content"]
        if guardrail_result["overall_status"] == "blocked":
            logger.warning(f"Content blocked by guardrails: {guardrail_result}")
            final_content = "I cannot provide a response to this request due to safety guidelines."
            
        context["final_content"] = final_content
        context["guardrails_status"] = guardrail_result["overall_status"]
