"""Service for invoking LLM models using LangChain."""
import os
import time
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from dotenv import load_dotenv
import logging
import httpx

from app.services.llm.token_service import token_service
from app.services.llm.grounding_service import grounding_service
from app.services.llm.token_optimizer import token_optimizer
# cyclic import check: ensure evaluation_service is imported safely or moved if needed
# For now assuming structure allows it, otherwise use local import
from app.services.llm.evaluation_service import evaluation_service

load_dotenv(override=True)
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
            logger.warning("❌ Missing API Configuration. Check .env file.")

        # Configure Caching
        os.makedirs("data", exist_ok=True)
        set_llm_cache(SQLiteCache(database_path="data/.langchain.db"))

        # Initialize Middleware
        self.middlewares: List[BaseMiddleware] = [
            ObservabilityMiddleware(), 
            UncertaintyMiddleware(),   
            GuardrailsMiddleware(),    
        ]

    def _get_deployment_name(self, model_type: ModelType) -> str:
        """Get the deployment name from environment variable."""
        deployment_name = os.getenv(model_type.value)
        if not deployment_name:
            raise ValueError(f"Deployment name not found for {model_type.name} (Env: {model_type.value})")
        return deployment_name

    def _get_llm(self, model_type: ModelType, temperature: float = 0.7, max_tokens: Optional[int] = None) -> ChatOpenAI:
        """Get LangChain ChatOpenAI instance with FULL SSL bypass."""
        deployment_name = self._get_deployment_name(model_type)
        
        # --- CRITICAL FIX: Disable SSL for BOTH Sync and Async clients ---
        sync_client = httpx.Client(verify=False)
        async_client = httpx.AsyncClient(verify=False)
        
        return ChatOpenAI(
            api_key=self.api_key,
            base_url=self.api_endpoint,
            model=deployment_name,
            temperature=temperature,
            max_tokens=max_tokens,
            http_client=sync_client,       # Used for invoke()
            http_async_client=async_client # Used for ainvoke() - Critical for FastAPI/Ragas
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
        """
        deployment_name = self._get_deployment_name(model_type)
        current_prompt = prompt
        retries = 2 if retry_on_fail else 0
        
        for attempt in range(retries + 1):
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
                
                if context["model_kwargs"]:
                    llm = llm.bind(model_kwargs=context["model_kwargs"])
                
                current_system_prompt = system_prompt
                if explain:
                    current_system_prompt += " You must explain your reasoning step-by-step before providing the final answer. Format your response as:\n<reasoning>\n[Your reasoning here]\n</reasoning>\n<answer>\n[Your final answer here]\n</answer>"
    
                messages = [
                    SystemMessage(content=current_system_prompt),
                    HumanMessage(content=current_prompt)
                ]
                
                # --- Token Optimization ---
                # Check if we need to optimize context (e.g. for very long prompts or history)
                # Note: 'messages' here is just system+user. In a real chat app, you'd pass the full history.
                # For this implementation, we'll assume 'messages' might grow if we were passing history.
                # But since we construct it fresh here, let's pretend we might have history.
                # TODO: If get_response accepted a list of messages (history), we'd optimize that.
                # Currently it takes a single prompt string. 
                # However, if the prompt itself is huge, we might want to truncate? 
                # Or if we change get_response to support history later.
                
                # For now, let's just run the optimizer to show integration, 
                # even if it's just 2 messages.
                # We'll use a high limit so we don't accidentally truncate a normal prompt.
                messages = await token_optimizer.summarize_context(
                    messages, 
                    self, 
                    deployment_name, 
                    max_context_tokens=10000 # High limit for now
                )
                
                # This uses the async_client we configured above
                response = await llm.ainvoke(messages)
                
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
                
                if "usage_metrics" in context:
                    result["usage_metrics"] = context["usage_metrics"]
                
                # 5. Evaluation & Self-Correction
                if evaluate:
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
            
            if "json" not in system_prompt.lower():
                system_prompt += " Output must be a valid JSON object."
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=prompt)
            ]
            
            response = await llm.ainvoke(messages)
            content = response.content
            
            # Apply Guardrails
            from app.services.guardrails_service import validate_all_guardrails
            guardrail_result = validate_all_guardrails(content)
            
            if guardrail_result["overall_status"] == "blocked":
                logger.warning(f"Content blocked by guardrails: {guardrail_result}")
                raise ValueError("Response blocked by safety guardrails.")
            
            final_content = guardrail_result["final_content"]
            
            latency_ms = (time.time() - start_time) * 1000
            logger.info(f"JSON Response generated. Latency: {latency_ms}ms")

            return parser.parse(final_content)
            
        except Exception as e:
            logger.error(f"Error calling LLM for JSON: {str(e)}")
            raise

# Global instance
llm_service = LLMService()
