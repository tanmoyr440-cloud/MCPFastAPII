from app.agents.base import BaseAgent
from app.services.llm.llm_service import ModelType

class GeneralAgent(BaseAgent):
    """A general purpose AI assistant."""
    
    def __init__(self):
        super().__init__(name="General Assistant", model_type=ModelType.BASIC)
        self.set_system_prompt("You are a helpful and friendly AI assistant capable of answering general questions.")

    async def process(self, user_input: str) -> str:
        """Process user input."""
        self.add_message("user", user_input)
        
        messages = [{"role": "system", "content": self.system_prompt}] + self.history
        
        response = await self._get_completion(messages)
        self.add_message("assistant", response)
        return response
