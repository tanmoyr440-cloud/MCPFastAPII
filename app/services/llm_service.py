"""Service for invoking LLM models using LangChain."""
import os
import json
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from dotenv import load_dotenv
import logging

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
            http_client=None # Explicitly disabled as per previous request context
        )

    async def get_response(
        self, 
        prompt: str, 
        model_type: ModelType = ModelType.BASIC, 
        system_prompt: str = "You are a helpful AI assistant.",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Get a text response from the specified model.
        """
        try:
            llm = self._get_llm(model_type, temperature, max_tokens)
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=prompt)
            ]
            response = await llm.ainvoke(messages)
            return response.content
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
            
            # Chain: LLM -> Parser
            chain = llm | parser
            return await chain.ainvoke(messages)
        except Exception as e:
            logger.error(f"Error calling LLM for JSON: {str(e)}")
            raise

# Global instance
llm_service = LLMService()
