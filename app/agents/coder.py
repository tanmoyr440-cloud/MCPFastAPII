"""Coding agent specialized in software development."""
from app.agents.base import BaseAgent
from app.services.llm_service import ModelType

class CoderAgent(BaseAgent):
    """An AI agent specialized in writing and debugging code."""
    
    def __init__(self):
        # Use the high performance model (e.g., DeepSeek-V3)
        super().__init__(name="Coder", model_type=ModelType.HIGH_PERF)
        self.set_system_prompt("You are an expert software engineer. You write clean, efficient, and well-documented code. You can debug complex issues and suggest architectural improvements.")

    async def process(self, user_input: str) -> str:
        """Process user input for coding tasks."""
        self.add_message("user", user_input)
        
        messages = [{"role": "system", "content": self.system_prompt}] + self.history
        
        response = await self._get_completion(messages, temperature=0.2) # Low temp for code precision
        self.add_message("assistant", response)
        return response
