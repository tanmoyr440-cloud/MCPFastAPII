"""Service for invoking LLM models using LangChain."""
import os
import json
import time
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from dotenv import load_dotenv
import logging
import httpx

from app.services.token_service import token_service
from app.services.token_service import token_service
from app.services.grounding_service import grounding_service
from app.services.evaluation_service import evaluation_service

load_dotenv()
logger = logging.getLogger(__name__)

class ModelType(str, Enum):
    """Enum for available model types mapped to env variables."""
    BASIC = "MODEL_CHAT_BASIC"
    MODERATE = "MODEL_CHAT_MOD"
    OPEN = "MODEL_CHAT_OPEN"
    REASONING = "MODEL_REASONING"
    HIGH_PERF = "MODEL_HIGH_PERF"
    EXPERIMENTAL = "MODEL_EXPERIMENTAL"
    VISION = "MODEL_VISION"

from langchain_core.globals import set_llm_cache
from langchain_community.cache import SQLiteCache

# Middleware imports
from app.services.middleware.base import BaseMiddleware
from app.services.middleware.observability import ObservabilityMiddleware
from app.services.middleware.guardrails import GuardrailsMiddleware
from app.services.middleware.uncertainty import UncertaintyMiddleware

class LLMService:
    """Service to interact with various LLM models using LangChain."""

    def __init__(self):
        self.api_key = os.getenv("API_KEY")
        self.api_endpoint = os.getenv("API_ENDPOINT")
        
        if not self.api_key or not self.api_endpoint:
            logger.warning("Missing Azure OpenAI configuration. Check .env for API_KEY and API_ENDPOINT")

        # Configure Caching
        os.makedirs("data", exist_ok=True)
        set_llm_cache(SQLiteCache(database_path="data/.langchain.db"))

        # Initialize Middleware
        self.middlewares: List[BaseMiddleware] = [
            ObservabilityMiddleware(), # Logs start time and input tokens
            UncertaintyMiddleware(),   # Configures logprobs
            GuardrailsMiddleware(),    # Validates output
        ]

    def _get_deployment_name(self, model_type: ModelType) -> str:
        """Get the deployment name from environment variable."""
        deployment_name = os.getenv(model_type.value)
        if not deployment_name:
            raise ValueError(f"Deployment name not found for {model_type.name} (Env: {model_type.value})")
        return deployment_name

    def _get_llm(self, model_type: ModelType, temperature: float = 0.7, max_tokens: Optional[int] = None) -> ChatOpenAI:
        """Get LangChain ChatOpenAI instance."""
        deployment_name = self._get_deployment_name(model_type)
        return ChatOpenAI(
            api_key=self.api_key,
            base_url=self.api_endpoint,
            model=deployment_name,
            temperature=temperature,
            max_tokens=max_tokens,
            http_client=httpx.Client(verify=False)
        )

    async def get_response(
        self, 
        prompt: str, 
        model_type: ModelType = ModelType.BASIC, 
        system_prompt: str = "You are a helpful AI assistant.",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        grounding: bool = False,
        explain: bool = False,
        check_uncertainty: bool = False,
        evaluate: bool = False,
        retry_on_fail: bool = False
    ) -> Union[str, Dict[str, Any]]:
        """
        Get a text response from the specified model.
        Uses middleware pipeline for logging, guardrails, and uncertainty.
        Supports evaluation and self-correction (Reflexion).
        """
        deployment_name = self._get_deployment_name(model_type)
        current_prompt = prompt
        retries = 2 if retry_on_fail else 0
        
        for attempt in range(retries + 1):
            # Context dictionary to pass through middleware
            context = {
                "prompt": current_prompt,
                "system_prompt": system_prompt,
                "model_type": model_type,
                "deployment_name": deployment_name,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "grounding": grounding,
                "explain": explain,
                "check_uncertainty": check_uncertainty,
                "model_kwargs": {}
            }
    
            try:
                # 1. Process Request Middleware
                for middleware in self.middlewares:
                    await middleware.process_request(context)
    
                # 2. Call LLM
                llm = self._get_llm(model_type, temperature, max_tokens)
                
                # Bind model_kwargs (e.g., logprobs)
                if context["model_kwargs"]:
                    llm = llm.bind(model_kwargs=context["model_kwargs"])
                
                # Modify system prompt for explainability
                current_system_prompt = system_prompt
                if explain:
                    current_system_prompt += " You must explain your reasoning step-by-step before providing the final answer. Format your response as:\n<reasoning>\n[Your reasoning here]\n</reasoning>\n<answer>\n[Your final answer here]\n</answer>"
    
                messages = [
                    SystemMessage(content=current_system_prompt),
                    HumanMessage(content=current_prompt)
                ]
                
                response = await llm.ainvoke(messages)
                
                # Update context with raw response
                context["raw_content"] = response.content
                context["response_metadata"] = response.response_metadata
                
                # 3. Process Response Middleware
                for middleware in reversed(self.middlewares):
                    await middleware.process_response(context)
    
                # 4. Construct Result
                final_content = context.get("final_content", context.get("raw_content"))
                result = {"content": final_content}
                
                if "uncertainty_metrics" in context:
                    result["uncertainty"] = context["uncertainty_metrics"]
    
                # Extract reasoning if requested
                if explain and "<reasoning>" in final_content:
                    try:
                        parts = final_content.split("</reasoning>")
                        reasoning_part = parts[0].split("<reasoning>")[1].strip()
                        answer_part = parts[1].split("<answer>")[1].split("</answer>")[0].strip() if "<answer>" in parts[1] else parts[1].strip()
                        
                        result["content"] = answer_part
                        result["reasoning"] = reasoning_part
                    except Exception as e:
                        logger.warning(f"Failed to parse reasoning: {e}")
                        result["reasoning"] = final_content
    
                if grounding and context.get("guardrails_status") != "blocked":
                    verification = await grounding_service.verify_response(prompt, result["content"], self)
                    result["grounding"] = verification
                
                # Add usage metrics if available
                if "usage_metrics" in context:
                    result["usage_metrics"] = context["usage_metrics"]
                
                # 5. Evaluation & Self-Correction
                if evaluate:
                    # Use original prompt for evaluation, not the retry prompt
                    scores = await evaluation_service.evaluate_response(prompt, result["content"], [])
                    result["evaluation_scores"] = scores
                    
                    if retry_on_fail and not evaluation_service.check_thresholds(scores):
                        if attempt < retries:
                            logger.info(f"Response failed evaluation (Attempt {attempt+1}/{retries+1}). Retrying...")
                            critique = f"Faithfulness: {scores.get('faithfulness')}, Relevancy: {scores.get('answer_relevancy')}."
                            current_prompt = f"{prompt}\n\nPrevious Answer: {result['content']}\nCritique: {critique}\nPlease improve the answer based on the critique."
                            continue
                        else:
                            result["is_flagged"] = True
                
                # If we have extra fields, return dict. Otherwise return str.
                if len(result) > 1:
                    return result
                
                return final_content
                
            except Exception as e:
                logger.error(f"Error calling LLM: {str(e)}")
                raise

    async def get_json_response(
        self, 
        prompt: str, 
        model_type: ModelType = ModelType.BASIC, 
        system_prompt: str = "You are a helpful AI assistant. You must output valid JSON.",
        temperature: float = 0.3
    ) -> Dict[str, Any]:
        """
        Get a JSON response from the specified model.
        """
        # Reuse get_response but force JSON parsing? 
        # Or keep separate? 
        # For now, let's keep separate but we should probably refactor this too later.
        # To avoid breaking changes, I will leave get_json_response mostly as is, 
        # but ideally it should also use middleware.
        # For this task, I focused on get_response.
        
        start_time = time.time()
        deployment_name = self._get_deployment_name(model_type)

        try:
            llm = self._get_llm(model_type, temperature)
            parser = JsonOutputParser()
            
            # Append JSON instruction to system prompt
            if "json" not in system_prompt.lower():
                system_prompt += " Output must be a valid JSON object."
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=prompt)
            ]
            
            # Count input tokens
            input_text = system_prompt + prompt
            prompt_tokens = token_service.count_tokens(input_text, deployment_name)
            
            # Get raw response first to apply guardrails
            response = await llm.ainvoke(messages)
            content = response.content
            
            # Count output tokens
            completion_tokens = token_service.count_tokens(content, deployment_name)

            # Apply Guardrails
            from app.services.guardrails_service import validate_all_guardrails
            guardrail_result = validate_all_guardrails(content)
            
            if guardrail_result["overall_status"] == "blocked":
                logger.warning(f"Content blocked by guardrails: {guardrail_result}")
                raise ValueError("Response blocked by safety guardrails.")
            
            final_content = guardrail_result["final_content"]
            
            # Log interaction
            latency_ms = (time.time() - start_time) * 1000
            observability_service.log_interaction(
                model=deployment_name,
                prompt=prompt,
                response=final_content,
                token_usage={
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": prompt_tokens + completion_tokens
                },
                latency_ms=latency_ms,
                metadata={"type": "json", "guardrails": guardrail_result["overall_status"]}
            )

            # Parse the (potentially redacted) content
            return parser.parse(final_content)
            
        except Exception as e:
            logger.error(f"Error calling LLM for JSON: {str(e)}")
            raise

# Global instance
llm_service = LLMService()
