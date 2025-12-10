from typing import List, Dict, Any
from app.agents.base import BaseAgent
from app.services.llm_service import llm_service, ModelType
from app.services.memory_service import memory_service
from app.core.prompt_manager import prompt_manager

class SelfLearningAgent(BaseAgent):
    """
    An agent that improves its answers through iterative refinement and memory.
    """
    
    def __init__(self):
        super().__init__(name="SelfLearning", model_type=ModelType.REASONING)
        # System prompt is dynamic, so we don't set a static one here via super
        self.base_system_prompt = prompt_manager.get_prompt("agents.self_learning.system_prompt")

    async def process(self, user_input: str) -> str:
        """
        Process user input with the Generate-Critique-Refine-Learn loop.
        """
        self.add_message("user", user_input)
        
        # 1. Retrieve Context (Memory)
        relevant_memories = memory_service.get_relevant_learnings(user_input)
        memory_context = ""
        if relevant_memories:
            memory_context = "\nRelevant Lessons from Memory:\n"
            for mem in relevant_memories:
                memory_context += f"- {mem['content']}\n"
        
        # 2. Draft Solution
        # Inject memory into system prompt for the draft
        current_system_prompt = self.base_system_prompt + memory_context
        
        draft_response = await llm_service.get_response(
            prompt=user_input,
            model_type=self.model_type,
            system_prompt=current_system_prompt
        )
        
        # 3. Critique
        critique_prompt = prompt_manager.get_prompt(
            "agents.self_learning.critique_prompt",
            user_input=user_input,
            draft_response=draft_response
        )
        
        critique = await llm_service.get_response(
            prompt=critique_prompt,
            model_type=ModelType.HIGH_PERF, # Use a strong model for critique
            system_prompt="You are a critical code reviewer and logic expert."
        )
        
        # If critique says "No major issues", skip refinement? 
        # For now, let's always refine to be safe, or check for keywords.
        if "no major issues" in critique.lower() and len(critique) < 100:
            final_response = draft_response
        else:
            # 4. Refine
            refine_prompt = prompt_manager.get_prompt(
                "agents.self_learning.refine_prompt",
                critique=critique,
                draft_response=draft_response
            )
            
            final_response = await llm_service.get_response(
                prompt=refine_prompt,
                model_type=self.model_type,
                system_prompt="You are an expert editor and problem solver."
            )

        self.add_message("assistant", final_response)
        
        # 5. Learn (Async or blocking? Blocking for now to ensure it's saved)
        await self._learn_from_interaction(user_input, final_response)
        
        return final_response

    async def _learn_from_interaction(self, user_input: str, final_response: str):
        """Extract a lesson and save to memory."""
        learning_prompt = prompt_manager.get_prompt(
            "agents.self_learning.learning_prompt",
            user_input=user_input,
            final_response=final_response
        )
        
        lesson = await llm_service.get_response(
            prompt=learning_prompt,
            model_type=ModelType.BASIC, # Basic model is enough for summarization
            system_prompt="You are a reflective AI."
        )
        
        # Extract topic (simple heuristic or another LLM call)
        # For simplicity, use the first few words of user input as topic
        topic = " ".join(user_input.split()[:5])
        
        memory_service.add_learning(topic, lesson, tags=["auto-learned"])
