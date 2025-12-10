import logging
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class ObservabilityService:
    """
    Service to log and trace LLM interactions.
    Currently logs to a JSONL file, but can be extended to support DB or external tools.
    """
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.log_file = self.log_dir / "llm_trace.jsonl"

    def log_interaction(
        self,
        model: str,
        prompt: str,
        response: str,
        token_usage: Dict[str, int],
        latency_ms: float,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log an LLM interaction.
        
        Args:
            model: The model name used.
            prompt: The input prompt.
            response: The generated response.
            token_usage: Dictionary containing token counts (prompt, completion, total).
            latency_ms: Latency in milliseconds.
            metadata: Additional metadata (e.g., user_id, session_id).
        """
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "model": model,
            "prompt": prompt,
            "response": response,
            "token_usage": token_usage,
            "latency_ms": latency_ms,
            "metadata": metadata or {}
        }
        
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            logger.error(f"Failed to log LLM interaction: {e}")

# Global instance
observability_service = ObservabilityService()
