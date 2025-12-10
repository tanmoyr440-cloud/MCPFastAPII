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

from app.services.observability_service import observability_service
from app.services.token_service import token_service
from app.services.grounding_service import grounding_service

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

class LLMService:
    """Service to interact with various LLM models using LangChain."""

    def __init__(self):
        self.api_key = os.getenv("API_KEY")
        self.api_endpoint = os.getenv("API_ENDPOINT")
        
        if not self.api_key or not self.api_endpoint:
            logger.warning("Missing Azure OpenAI configuration. Check .env for API_KEY and API_ENDPOINT")

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
        check_uncertainty: bool = False
    ) -> Union[str, Dict[str, Any]]:
        """
        Get a text response from the specified model.
        If grounding is True, returns a Dict with response and verification details.
        If explain is True, asks the model to explain its reasoning.
        If check_uncertainty is True, calculates confidence score (requires logprobs support).
        """
        start_time = time.time()
        deployment_name = self._get_deployment_name(model_type)
        
        try:
            # Configure LLM with logprobs if needed
            model_kwargs = {}
            if check_uncertainty:
                model_kwargs["logprobs"] = True
                # model_kwargs["top_logprobs"] = 5 # Optional, for more detailed entropy
            
            llm = self._get_llm(model_type, temperature, max_tokens)
            
            if model_kwargs:
                llm = llm.bind(model_kwargs=model_kwargs)
            
            # Modify system prompt for explainability
            if explain:
                system_prompt += " You must explain your reasoning step-by-step before providing the final answer. Format your response as:\n<reasoning>\n[Your reasoning here]\n</reasoning>\n<answer>\n[Your final answer here]\n</answer>"

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=prompt)
            ]
            
            # Count input tokens
            input_text = system_prompt + prompt
            prompt_tokens = token_service.count_tokens(input_text, deployment_name)
            
            response = await llm.ainvoke(messages)
            content = response.content
            
            # Count output tokens
            completion_tokens = token_service.count_tokens(content, deployment_name)
            
            # Apply Guardrails
            from app.services.guardrails_service import validate_all_guardrails
            guardrail_result = validate_all_guardrails(content)
            
            final_content = guardrail_result["final_content"]
            if guardrail_result["overall_status"] == "blocked":
                logger.warning(f"Content blocked by guardrails: {guardrail_result}")
                final_content = "I cannot provide a response to this request due to safety guidelines."
            
            # Calculate Uncertainty
            uncertainty_metrics = {}
            if check_uncertainty:
                from app.services.uncertainty_service import uncertainty_service
                # Extract logprobs from response metadata
                # LangChain structure: response.response_metadata['logprobs']['content'] -> list of dicts
                try:
                    logprobs = []
                    if "logprobs" in response.response_metadata:
                        logprobs = response.response_metadata["logprobs"]["content"]
                    
                    uncertainty_metrics = uncertainty_service.calculate_metrics(logprobs)
                    uncertainty_metrics["is_uncertain"] = uncertainty_service.is_hallucination(uncertainty_metrics["confidence_score"])
                except Exception as e:
                    logger.warning(f"Failed to calculate uncertainty: {e}")

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
                metadata={
                    "grounding": grounding, 
                    "explain": explain,
                    "check_uncertainty": check_uncertainty,
                    "uncertainty": uncertainty_metrics,
                    "guardrails": guardrail_result["overall_status"]
                }
            )

            result = {"content": final_content}
            
            if uncertainty_metrics:
                result["uncertainty"] = uncertainty_metrics

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
                    # Fallback: return full content as reasoning if parsing fails
                    result["reasoning"] = final_content

            if grounding and guardrail_result["overall_status"] != "blocked":
                verification = await grounding_service.verify_response(prompt, result["content"], self)
                result["grounding"] = verification
            
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
