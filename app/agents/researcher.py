"""Research agent with reasoning capabilities."""
from app.agents.base import BaseAgent
from app.services.llm_service import ModelType
import asyncio

class ResearchAgent(BaseAgent):
    """An AI agent specialized in research and reasoning."""
    
    def __init__(self):
        # Use the reasoning model (e.g., DeepSeek-R1)
        super().__init__(name="Researcher", model_type=ModelType.REASONING)
        self.set_system_prompt("You are an expert researcher. You analyze complex topics, break them down, and provide detailed, well-reasoned answers.")

    async def process(self, user_input: str) -> str:
        """Process user input with simulated research steps."""
        self.add_message("user", user_input)
        
        # Simulate "thinking" or "researching"
        # In a real scenario, this would call search tools (MCP)
        # For now, we rely on the reasoning model's internal knowledge
        
        messages = [{"role": "system", "content": self.system_prompt}] + self.history
        
        response = await self._get_completion(messages, temperature=0.3) # Lower temp for reasoning
        self.add_message("assistant", response)
        return response
