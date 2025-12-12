import time
from typing import Dict, Any
from app.services.middleware.base import BaseMiddleware
from app.services.observability import obs_manager, tracer
from opentelemetry.trace import Status, StatusCode

class ObservabilityMiddleware(BaseMiddleware):
    """
    Middleware for logging interactions and counting tokens using OpenTelemetry.
    """

    async def process_request(self, context: Dict[str, Any]) -> None:
        if not obs_manager.is_enabled():
            return

        # Start a span for the LLM call
        operation_name = f"llm.{context.get('model_type', 'unknown')}"
        span = tracer.start_span(operation_name)
        
        # Store span in context to close it later
        context["otel_span"] = span
        context["start_time"] = time.time()
        
        # Set initial attributes
        span.set_attribute("llm.system_prompt", context.get("system_prompt", ""))
        span.set_attribute("llm.prompt", context.get("prompt", ""))
        span.set_attribute("llm.model", context.get("deployment_name", "unknown"))
        span.set_attribute("llm.temperature", context.get("temperature", 0.0))

    async def process_response(self, context: Dict[str, Any]) -> None:
        if not obs_manager.is_enabled():
            return
            
        span = context.get("otel_span")
        if not span:
            return

        try:
            final_content = context.get("final_content", "")
            
            # Set response attributes
            span.set_attribute("llm.response", final_content)
            
            # Record Guardrails status
            guardrails_status = context.get("guardrails_status")
            if guardrails_status:
                span.set_attribute("llm.guardrails.status", guardrails_status)
            
            # Record Uncertainty metrics
            uncertainty = context.get("uncertainty_metrics")
            if uncertainty:
                span.set_attribute("llm.uncertainty.confidence", uncertainty.get("confidence_score", 0.0))
                span.set_attribute("llm.uncertainty.is_uncertain", uncertainty.get("is_uncertain", False))

            # Calculate and record tokens
            # Note: We rely on the LLM response metadata if available, or count manually if needed.
            # Here we can use the token_service if we want to be consistent, or use obs_manager's extraction if we had the raw response object.
            # Since we have the text, let's use token_service for consistency with previous logic, 
            # OR we can try to use the raw response metadata if we preserved it.
            # context["response_metadata"] might have it.
            
            # Let's try to extract from metadata first
            response_metadata = context.get("response_metadata", {})
            # We need a mock object to pass to extract_token_usage or just parse manually
            # obs_manager.extract_token_usage expects an object with response_metadata attribute
            
            # Simpler: just use token_service as before, but record to span
            from app.services.llm.token_service import token_service
            
            deployment_name = context.get("deployment_name")
            prompt = context.get("prompt", "")
            system_prompt = context.get("system_prompt", "")
            input_text = system_prompt + prompt
            
            prompt_tokens = token_service.count_tokens(input_text, deployment_name)
            completion_tokens = token_service.count_tokens(final_content, deployment_name)
            total_tokens = prompt_tokens + completion_tokens
            
            span.set_attribute("llm.input_tokens", prompt_tokens)
            span.set_attribute("llm.output_tokens", completion_tokens)
            span.set_attribute("llm.total_tokens", total_tokens)
            
            # Calculate cost
            cost = obs_manager.calculate_cost(prompt_tokens, completion_tokens, deployment_name)
            span.set_attribute("llm.estimated_cost_usd", cost)
            
            # Calculate carbon footprint
            carbon_footprint = obs_manager.calculate_carbon_footprint(total_tokens, deployment_name)
            span.set_attribute("llm.carbon_footprint_kg", carbon_footprint)
            
            # Store metrics in context for LLMService to return
            context["usage_metrics"] = {
                "input_tokens": prompt_tokens,
                "output_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "cost_usd": cost,
                "carbon_footprint_kg": carbon_footprint
            }
            
            span.set_status(Status(StatusCode.OK))
            
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
        finally:
            # End the span
            span.end()
