"""
Evaluation Service using Ragas.
"""
import os
import logging
from typing import List, Dict, Any, Optional
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy
from datasets import Dataset

logger = logging.getLogger(__name__)

class EvaluationService:
    def __init__(self):
        # Ragas uses OpenAI by default, ensure key is present
        if not os.getenv("OPENAI_API_KEY"):
            logger.warning("OPENAI_API_KEY not found. Ragas evaluation may fail.")
            
        self.metrics = [faithfulness, answer_relevancy]

    async def evaluate_response(
        self, 
        query: str, 
        response: str, 
        contexts: List[str]
    ) -> Dict[str, float]:
        """
        Evaluate a response using Ragas metrics.
        
        Args:
            query: The user's question.
            response: The generated answer.
            contexts: The retrieved contexts used to generate the answer.
            
        Returns:
            Dictionary of metric scores.
        """
        try:
            # Ragas expects a dataset
            data = {
                "question": [query],
                "answer": [response],
                "contexts": [contexts],
                # Ground truth is optional for these metrics but dataset structure might require it
                # "ground_truth": [""] 
            }
            dataset = Dataset.from_dict(data)
            
            # Run evaluation
            # Note: evaluate is synchronous but might make async calls internally. 
            # We wrap it or call it directly. Ragas 0.1+ supports async? 
            # For now, we'll run it directly. If it blocks, we might need run_in_executor.
            results = evaluate(
                dataset=dataset,
                metrics=self.metrics,
                raise_exceptions=False
            )
            
            # Extract scores
            scores = {
                "faithfulness": results.get("faithfulness", 0.0),
                "answer_relevancy": results.get("answer_relevancy", 0.0)
            }
            
            logger.info(f"Evaluation scores: {scores}")
            return scores
            
        except Exception as e:
            logger.error(f"Error during evaluation: {e}")
            return {"faithfulness": 0.0, "answer_relevancy": 0.0, "error": 1.0}

    def check_thresholds(
        self, 
        scores: Dict[str, float], 
        thresholds: Optional[Dict[str, float]] = None
    ) -> bool:
        """
        Check if scores meet the defined thresholds.
        """
        if not thresholds:
            thresholds = {
                "faithfulness": 0.7,
                "answer_relevancy": 0.7
            }
            
        for metric, threshold in thresholds.items():
            if scores.get(metric, 0.0) < threshold:
                return False
        return True

evaluation_service = EvaluationService()
