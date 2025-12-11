"""Coding agent specialized in software development."""
from app.agents.base import BaseAgent
from app.services.llm_service import ModelType
from app.services.observability import trace_llm_operation

class CoderAgent(BaseAgent):
    """An AI agent specialized in writing and debugging code."""
    with trace_llm_operation(
        "agent.guardrail",
        attributes={
            "agent.name": "guardrail",
            "agent.type": "validation",
            "agent.chat_id": "unknown"
        }
    ):
        def __init__(self):
            # Use the high performance model (e.g., DeepSeek-V3)
            super().__init__(name="Coder", model_type=ModelType.HIGH_PERF)
            # Load system prompt from YAML
            self.set_system_prompt("agents.coder.system_prompt")

        async def process(self, user_input: str) -> str:
            """Process user input for coding tasks."""
            self.add_message("user", user_input)
            
            messages = [{"role": "system", "content": self.system_prompt}] + self.history
            
            response = await self._get_completion(messages, temperature=0.2) # Low temp for code precision
            self.add_message("assistant", response)
            return response
