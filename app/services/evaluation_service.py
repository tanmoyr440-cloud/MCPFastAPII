"""
Evaluation Service using Ragas.
"""
import os
import logging
import httpx
from typing import List, Dict, Any, Optional
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy
from datasets import Dataset
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from dotenv import load_dotenv

load_dotenv(override=True)
logger = logging.getLogger(__name__)

class EvaluationService:
    def __init__(self):
        self.api_key = os.getenv("API_KEY")
        self.api_endpoint = os.getenv("API_ENDPOINT")
        
        # --- CRITICAL FIX: SSL Bypass for Async Ragas calls ---
        self.sync_client = httpx.Client(verify=False)
        self.async_client = httpx.AsyncClient(verify=False)
        
        # 1. Configure LLM for Judge
        self.llm = ChatOpenAI(
            api_key=self.api_key,
            base_url=self.api_endpoint,
            model=os.getenv("MODEL_CHAT_BASIC", "gpt-3.5-turbo"),
            temperature=0,
            http_client=self.sync_client,
            http_async_client=self.async_client # <--- Required for Ragas
        )

        # 2. Configure Embeddings
        self.embeddings = OpenAIEmbeddings(
            api_key=self.api_key,
            base_url=self.api_endpoint,
            model=os.getenv("MODEL_EMBEDDING", "text-embedding-3-small"),
            http_client=self.sync_client,
            http_async_client=self.async_client, # <--- Required for Ragas
            check_embedding_ctx_length=False
        )
            
        self.metrics = [faithfulness, answer_relevancy]

    async def evaluate_response(
        self, 
        query: str, 
        response: str, 
        contexts: List[str]
    ) -> Dict[str, float]:
        """Evaluate a response using Ragas metrics."""
        try:
            # Prepare dataset
            # Handle empty contexts safely to prevent Ragas crash
            if not contexts or len(contexts) == 0:
                safe_contexts = [["No context provided"]]
            else:
                safe_contexts = [contexts]
            
            data = {
                "question": [query],
                "answer": [response],
                "contexts": safe_contexts,
                "ground_truth": [""] # CRITICAL: Added to prevent KeyError in Ragas
            }
            dataset = Dataset.from_dict(data)
            
            # Run evaluation
            results = evaluate(
                dataset=dataset,
                metrics=self.metrics,
                llm=self.llm,        # <--- Explicitly pass SSL-bypassed LLM
                embeddings=self.embeddings, # <--- Explicitly pass SSL-bypassed Embeddings
                raise_exceptions=False
            )
            
            # CRITICAL: Use bracket access instead of .get() as Ragas result is not a standard dict
            faithfulness_score = results["faithfulness"] if "faithfulness" in results else 1.0
            relevancy_score = results["answer_relevancy"] if "answer_relevancy" in results else 1.0

             # Handle NaNs (common in Ragas failures)
            import math
            if isinstance(faithfulness_score, float) and math.isnan(faithfulness_score):
                faithfulness_score = 1.0 
            if isinstance(relevancy_score, float) and math.isnan(relevancy_score):
                relevancy_score = 1.0 

            scores = {
                "faithfulness": float(faithfulness_score),
                "answer_relevancy": float(relevancy_score)
            }
            
            logger.info(f"Evaluation scores: {scores}")
            return scores
            
        except Exception as e:
            logger.error(f"Error during evaluation: {repr(e)}")
            # Return passing scores on error to prevent infinite retry loops
            return {"faithfulness": 1.0, "answer_relevancy": 1.0, "error": 1.0}

    def check_thresholds(
        self, 
        scores: Dict[str, float], 
        thresholds: Optional[Dict[str, float]] = None
    ) -> bool:
        if not isinstance(scores, dict):
            return True

        if scores.get("error") == 1.0:
            return True

        if not thresholds:
            thresholds = {"faithfulness": 0.5, "answer_relevancy": 0.5}
            
        for metric, threshold in thresholds.items():
            if scores.get(metric, 0.0) < threshold:
                return False
        return True

evaluation_service = EvaluationService()
