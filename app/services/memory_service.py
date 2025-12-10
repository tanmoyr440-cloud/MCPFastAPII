import json
import logging
from typing import List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class MemoryService:
    """
    Service to store and retrieve learned patterns/strategies.
    Currently uses a simple JSON file storage.
    """
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.memory_file = self.data_dir / "memory.json"
        self._load_memory()

    def _load_memory(self):
        """Load memory from JSON file."""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, "r", encoding="utf-8") as f:
                    self.memory = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load memory: {e}")
                self.memory = []
        else:
            self.memory = []

    def _save_memory(self):
        """Save memory to JSON file."""
        try:
            with open(self.memory_file, "w", encoding="utf-8") as f:
                json.dump(self.memory, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save memory: {e}")

    def add_learning(self, topic: str, content: str, tags: List[str] = None):
        """
        Add a new learning entry.
        
        Args:
            topic: The general topic or problem area.
            content: The learned lesson or strategy.
            tags: Optional list of tags for filtering.
        """
        entry = {
            "topic": topic,
            "content": content,
            "tags": tags or []
        }
        self.memory.append(entry)
        self._save_memory()

    def get_relevant_learnings(self, query: str) -> List[Dict[str, Any]]:
        """
        Retrieve relevant learnings based on a query.
        For now, this does a simple keyword match on topic and tags.
        In a real system, this would use vector embeddings.
        """
        query_terms = query.lower().split()
        relevant = []
        
        for entry in self.memory:
            # Simple scoring: count matching terms in topic and tags
            score = 0
            text_to_search = (entry["topic"] + " " + " ".join(entry["tags"])).lower()
            
            for term in query_terms:
                if term in text_to_search:
                    score += 1
            
            if score > 0:
                relevant.append(entry)
        
        return relevant

# Global instance
memory_service = MemoryService()
