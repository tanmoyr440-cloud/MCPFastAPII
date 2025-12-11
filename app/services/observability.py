"""
Observability utilities for LLM tracing and monitoring.

This module provides a structural approach to instrument LLM calls across the application.
Uses OpenTelemetry and Phoenix for local, privacy-preserving observability.
"""

from functools import wraps
from typing import Optional, Dict, Any, Callable
from contextlib import contextmanager
import re
import time
import os
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
# from app.core.config import settings
from app.core.logger import get_logger
from dotenv import load_dotenv
load_dotenv()


logger = get_logger(__name__)

# Get tracer instance
tracer = trace.get_tracer(__name__)


class ObservabilityManager:
    """
    Centralized manager for observability features.
    Provides a structural way to add tracing to any LLM-related function.
    """
    
    def __init__(self):
        self.enabled = os.getenv("ENABLE_OBSERVABILITY")
        self.pii_redaction_enabled = os.getenv("ENABLE_PII_REDACTION")
        
    def is_enabled(self) -> bool:
        """Check if observability is enabled."""
        return self.enabled
    
    @staticmethod
    def redact_pii(text: str) -> str:
        """
        Redact PII from text (emails, phone numbers, etc.).
        
        Args:
            text: Text that may contain PII
            
        Returns:
            Text with PII redacted
        """
        if not os.getenv("ENABLE_PII_REDACTION"):
            return text
            
        # Redact email addresses
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL_REDACTED]', text)
        
        # Redact phone numbers (various formats)
        text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE_REDACTED]', text)
        text = re.sub(r'\b\+\d{1,3}[-.]?\d{3,4}[-.]?\d{3,4}[-.]?\d{3,4}\b', '[PHONE_REDACTED]', text)
        
        # Redact credit card numbers
        text = re.sub(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '[CARD_REDACTED]', text)
        
        # Redact SSN
        text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN_REDACTED]', text)
        
        return text
    
    @staticmethod
    def calculate_cost(input_tokens: int, output_tokens: int, model: str) -> float:
        """
        Calculate estimated cost for LLM call.
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model: Model name
            
        Returns:
            Estimated cost in USD
        """
        # Pricing per 1M tokens (approximate, update as needed)
        pricing = {
            "gemini-2.5-flash": {"input": 0.075, "output": 0.30},  # per 1M tokens
            "gpt-4": {"input": 30.0, "output": 60.0},
            "gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
            "deepseek-r1": {"input": 0.55, "output": 2.19},
        }
        
        # Default pricing if model not found
        default_pricing = {"input": 1.0, "output": 2.0}
        
        model_pricing = pricing.get(model, default_pricing)
        
        input_cost = (input_tokens / 1_000_000) * model_pricing["input"]
        output_cost = (output_tokens / 1_000_000) * model_pricing["output"]
        
        return input_cost + output_cost
    
    @staticmethod
    def calculate_carbon_footprint(total_tokens: int, model: str) -> float:
        """
        Calculate estimated carbon footprint in kg CO2e.
        
        Based on:
        - Energy per token (approx 0.0003 kWh for large models)
        - Carbon intensity of grid (approx 0.475 kg CO2e/kWh global avg)
        
        Args:
            total_tokens: Total tokens (input + output)
            model: Model name
            
        Returns:
            Estimated carbon footprint in kg CO2e
        """
        # Energy consumption per 1000 tokens (kWh) - rough estimates
        # GPT-4 class: 0.0003 kWh
        # GPT-3.5 class: 0.00005 kWh
        energy_factors = {
            "gpt-4": 0.0003,
            "gemini-1.5-pro": 0.0003,
            "gpt-3.5-turbo": 0.00005,
            "gemini-2.5-flash": 0.00005,
        }
        
        # Default to lower bound
        kwh_per_1k_tokens = energy_factors.get(model, 0.00005)
        
        total_kwh = (total_tokens / 1000) * kwh_per_1k_tokens
        
        # Global average carbon intensity (kg CO2e / kWh)
        # Source: Ember (2022)
        carbon_intensity = 0.475 
        
        return total_kwh * carbon_intensity
    
    @staticmethod
    def extract_token_usage(response: Any) -> Dict[str, int]:
        """
        Extract token usage from LLM response.
        
        Args:
            response: LLM response object
            
        Returns:
            Dictionary with input_tokens, output_tokens, total_tokens
        """
        tokens = {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0
        }
        
        try:
            # For LangChain responses
            if hasattr(response, 'response_metadata'):
                metadata = response.response_metadata
                if 'token_usage' in metadata:
                    usage = metadata['token_usage']
                    tokens["input_tokens"] = usage.get('prompt_tokens', 0)
                    tokens["output_tokens"] = usage.get('completion_tokens', 0)
                    tokens["total_tokens"] = usage.get('total_tokens', 0)
                elif 'usage_metadata' in metadata:
                    # Gemini format
                    usage = metadata['usage_metadata']
                    tokens["input_tokens"] = usage.get('prompt_token_count', 0)
                    tokens["output_tokens"] = usage.get('candidates_token_count', 0)
                    tokens["total_tokens"] = tokens["input_tokens"] + tokens["output_tokens"]
            
            # For OpenAI responses
            elif hasattr(response, 'usage'):
                tokens["input_tokens"] = response.usage.prompt_tokens
                tokens["output_tokens"] = response.usage.completion_tokens
                tokens["total_tokens"] = response.usage.total_tokens
                
        except Exception as e:
            logger.warning(f"Could not extract token usage: {str(e)}")
        
        return tokens


# Global observability manager instance
obs_manager = ObservabilityManager()


@contextmanager
def trace_llm_operation(
    operation_name: str,
    attributes: Optional[Dict[str, Any]] = None,
    capture_input: bool = True,
    capture_output: bool = True
):
    """
    Context manager for tracing LLM operations.
    
    Structural approach: Use this to wrap any LLM-related operation.
    
    Args:
        operation_name: Name of the operation (e.g., "llm.chat.invoke")
        attributes: Additional attributes to add to the span
        capture_input: Whether to capture input in span
        capture_output: Whether to capture output in span
        
    Usage:
        with trace_llm_operation("llm.chat.invoke", {"model": "gpt-4"}):
            response = llm.invoke(query)
    """
    if not obs_manager.is_enabled():
        yield None
        return
    
    with tracer.start_as_current_span(operation_name) as span:
        start_time = time.time()
        
        # Set initial attributes
        if attributes:
            for key, value in attributes.items():
                # Redact PII if enabled
                if isinstance(value, str) and obs_manager.pii_redaction_enabled:
                    value = obs_manager.redact_pii(value)
                span.set_attribute(key, value)
        
        try:
            yield span
            span.set_status(Status(StatusCode.OK))
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            raise
        finally:
            # Record duration
            duration_ms = (time.time() - start_time) * 1000
            span.set_attribute("duration_ms", duration_ms)


def trace_llm_call(
    operation_name: Optional[str] = None,
    attributes: Optional[Dict[str, Any]] = None,
    capture_args: bool = False,
    capture_result: bool = True
):
    """
    Decorator for tracing LLM function calls.
    
    Structural approach: Apply this decorator to any function that calls an LLM.
    
    Args:
        operation_name: Custom operation name (defaults to function name)
        attributes: Static attributes to add to the span
        capture_args: Whether to capture function arguments
        capture_result: Whether to capture function result
        
    Usage:
        @trace_llm_call(operation_name="custom.llm.call", attributes={"type": "chat"})
        def my_llm_function(query: str):
            return llm.invoke(query)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            if not obs_manager.is_enabled():
                return func(*args, **kwargs)
            
            op_name = operation_name or f"llm.{func.__name__}"
            
            with tracer.start_as_current_span(op_name) as span:
                start_time = time.time()
                
                # Capture function metadata
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)
                
                # Add static attributes
                if attributes:
                    for key, value in attributes.items():
                        if isinstance(value, str) and obs_manager.pii_redaction_enabled:
                            value = obs_manager.redact_pii(value)
                        span.set_attribute(key, value)
                
                # Capture arguments if requested
                if capture_args and kwargs:
                    for key, value in kwargs.items():
                        if isinstance(value, (str, int, float, bool)):
                            attr_value = value
                            if isinstance(value, str) and obs_manager.pii_redaction_enabled:
                                attr_value = obs_manager.redact_pii(value)
                            span.set_attribute(f"arg.{key}", attr_value)
                
                try:
                    result = func(*args, **kwargs)
                    
                    # Extract and record token usage
                    tokens = obs_manager.extract_token_usage(result)
                    if tokens["total_tokens"] > 0:
                        span.set_attribute("llm.input_tokens", tokens["input_tokens"])
                        span.set_attribute("llm.output_tokens", tokens["output_tokens"])
                        span.set_attribute("llm.total_tokens", tokens["total_tokens"])
                        
                        # Calculate cost if model info available
                        if "model" in kwargs:
                            cost = obs_manager.calculate_cost(
                                tokens["input_tokens"],
                                tokens["output_tokens"],
                                kwargs["model"]
                            )
                            span.set_attribute("llm.estimated_cost_usd", cost)
                    
                    span.set_status(Status(StatusCode.OK))
                    return result
                    
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise
                finally:
                    duration_ms = (time.time() - start_time) * 1000
                    span.set_attribute("duration_ms", duration_ms)
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if not obs_manager.is_enabled():
                return await func(*args, **kwargs)
            
            op_name = operation_name or f"llm.{func.__name__}"
            
            with tracer.start_as_current_span(op_name) as span:
                start_time = time.time()
                
                # Capture function metadata
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)
                
                # Add static attributes
                if attributes:
                    for key, value in attributes.items():
                        if isinstance(value, str) and obs_manager.pii_redaction_enabled:
                            value = obs_manager.redact_pii(value)
                        span.set_attribute(key, value)
                
                # Capture arguments if requested
                if capture_args and kwargs:
                    for key, value in kwargs.items():
                        if isinstance(value, (str, int, float, bool)):
                            attr_value = value
                            if isinstance(value, str) and obs_manager.pii_redaction_enabled:
                                attr_value = obs_manager.redact_pii(value)
                            span.set_attribute(f"arg.{key}", attr_value)
                
                try:
                    result = await func(*args, **kwargs)
                    
                    # Extract and record token usage
                    tokens = obs_manager.extract_token_usage(result)
                    if tokens["total_tokens"] > 0:
                        span.set_attribute("llm.input_tokens", tokens["input_tokens"])
                        span.set_attribute("llm.output_tokens", tokens["output_tokens"])
                        span.set_attribute("llm.total_tokens", tokens["total_tokens"])
                    
                    span.set_status(Status(StatusCode.OK))
                    return result
                    
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise
                finally:
                    duration_ms = (time.time() - start_time) * 1000
                    span.set_attribute("duration_ms", duration_ms)
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def add_span_attributes(attributes: Dict[str, Any]):
    """
    Add attributes to the current active span.
    
    Args:
        attributes: Dictionary of attributes to add
    """
    if not obs_manager.is_enabled():
        return
    
    span = trace.get_current_span()
    if span and span.is_recording():
        for key, value in attributes.items():
            if isinstance(value, str) and obs_manager.pii_redaction_enabled:
                value = obs_manager.redact_pii(value)
            span.set_attribute(key, value)


def record_llm_metrics(
    model: str,
    input_tokens: int,
    output_tokens: int,
    duration_ms: float,
    status: str = "success"
):
    """
    Record LLM metrics for the current span.
    
    Args:
        model: Model name
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        duration_ms: Duration in milliseconds
        status: Status of the call (success/error)
    """
    if not obs_manager.is_enabled():
        return
    
    attributes = {
        "llm.model": model,
        "llm.input_tokens": input_tokens,
        "llm.output_tokens": output_tokens,
        "llm.total_tokens": input_tokens + output_tokens,
        "llm.duration_ms": duration_ms,
        "llm.status": status,
    }
    
    # Calculate cost
    cost = obs_manager.calculate_cost(input_tokens, output_tokens, model)
    attributes["llm.estimated_cost_usd"] = cost
    
    add_span_attributes(attributes)
