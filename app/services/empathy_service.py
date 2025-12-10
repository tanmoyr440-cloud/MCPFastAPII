"""Empathy Service using LangGraph for human-like conversations."""
import os
import json
from typing import Annotated, List, Dict, Any
from enum import Enum
import google.generativeai as genai
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict


class EmotionalTone(str, Enum):
    """Emotional tone detected in user message"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    FRUSTRATED = "frustrated"
    ANXIOUS = "anxious"
    CONFUSED = "confused"
    EXCITED = "excited"


class ConversationState(TypedDict):
    """State for conversation flow with empathy"""
    user_message: str
    conversation_history: List[Dict[str, Any]]
    emotional_tone: EmotionalTone
    empathy_score: float  # 0-1, how much empathy to show
    context_awareness: str  # What the user is dealing with
    empathetic_response: str
    final_response: str


class EmpathyAnalyzer:
    """Analyzes emotional content and determines empathy level"""
    
    def __init__(self):
        """Initialize the empathy analyzer"""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-2.0-flash")
    
    async def analyze_emotional_tone(self, message: str) -> dict:
        """
        Analyze the emotional tone of a user message.
        
        Returns dict with:
        - emotional_tone: detected tone
        - empathy_score: how much empathy to show (0-1)
        - context_awareness: what the user is dealing with
        """
        prompt = f"""Analyze the emotional tone and context of this user message. 
Return a JSON object with these fields:
- "tone": one of (positive, negative, neutral, frustrated, anxious, confused, excited)
- "empathy_score": 0.0 to 1.0 (how much empathy this message needs)
- "context": brief description of what the user is dealing with
- "keywords": list of emotional keywords found

User message: "{message}"

Return ONLY valid JSON, no explanation."""

        response = self.model.generate_content(prompt)
        try:
            return json.loads(response.text)
        except json.JSONDecodeError:
            return {
                "tone": "neutral",
                "empathy_score": 0.5,
                "context": "conversation",
                "keywords": []
            }


class EmpathyResponseGenerator:
    """Generates empathetic responses using LangGraph workflow"""
    
    def __init__(self):
        """Initialize the empathy response generator"""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-2.0-flash")
        self.analyzer = EmpathyAnalyzer()
        self.graph = self._build_graph()
    
    def _build_graph(self):
        """Build the LangGraph workflow for empathetic responses"""
        graph = StateGraph(ConversationState)
        
        # Add nodes for each stage of empathetic conversation
        graph.add_node("analyze_emotion", self._analyze_emotion_node)
        graph.add_node("detect_context", self._detect_context_node)
        graph.add_node("generate_empathy", self._generate_empathy_node)
        graph.add_node("create_response", self._create_response_node)
        graph.add_node("enhance_with_empathy", self._enhance_with_empathy_node)
        
        # Define edges (workflow)
        graph.add_edge(START, "analyze_emotion")
        graph.add_edge("analyze_emotion", "detect_context")
        graph.add_edge("detect_context", "generate_empathy")
        graph.add_edge("generate_empathy", "create_response")
        graph.add_edge("create_response", "enhance_with_empathy")
        graph.add_edge("enhance_with_empathy", END)
        
        return graph.compile()
    
    async def _analyze_emotion_node(self, state: ConversationState) -> ConversationState:
        """Node: Analyze emotional tone of user message"""
        analysis = await self.analyzer.analyze_emotional_tone(state["user_message"])
        
        tone_map = {
            "positive": EmotionalTone.POSITIVE,
            "negative": EmotionalTone.NEGATIVE,
            "neutral": EmotionalTone.NEUTRAL,
            "frustrated": EmotionalTone.FRUSTRATED,
            "anxious": EmotionalTone.ANXIOUS,
            "confused": EmotionalTone.CONFUSED,
            "excited": EmotionalTone.EXCITED,
        }
        
        state["emotional_tone"] = tone_map.get(analysis.get("tone", "neutral"), EmotionalTone.NEUTRAL)
        state["empathy_score"] = float(analysis.get("empathy_score", 0.5))
        state["context_awareness"] = analysis.get("context", "conversation")
        
        return state
    
    async def _detect_context_node(self, state: ConversationState) -> ConversationState:
        """Node: Detect deeper context from conversation history"""
        # Analyze conversation history for patterns
        if len(state["conversation_history"]) > 0:
            recent_messages = state["conversation_history"][-4:]
            context_prompt = f"""Based on this conversation history, identify the user's current emotional state and needs:

{json.dumps(recent_messages, indent=2)}

Current message: "{state['user_message']}"

Provide a brief emotional context (1 sentence). Be empathetic in your understanding."""
            
            response = self.model.generate_content(context_prompt)
            state["context_awareness"] = response.text.strip()
        
        return state
    
    async def _generate_empathy_node(self, state: ConversationState) -> ConversationState:
        """Node: Generate empathetic opening based on detected emotion"""
        empathy_templates = {
            EmotionalTone.FRUSTRATED: [
                "I can see this is frustrating for you, and I appreciate you sharing.",
                "That sounds really frustrating. Let me help.",
                "I understand your frustration. Let's work through this together.",
            ],
            EmotionalTone.ANXIOUS: [
                "It sounds like you're dealing with some concerns. I'm here to help.",
                "I can sense some anxiety. Let's take this step by step.",
                "Your feelings are valid. Let me support you.",
            ],
            EmotionalTone.CONFUSED: [
                "I can see this is confusing. Let me clarify things for you.",
                "That's a great question. Let me break this down.",
                "Confusion is normal. Let's work through this together.",
            ],
            EmotionalTone.EXCITED: [
                "Your enthusiasm is wonderful! Let's explore this together.",
                "I love your energy! Let's dive into this.",
                "That sounds exciting! Tell me more.",
            ],
            EmotionalTone.NEGATIVE: [
                "I hear you, and your concerns are important.",
                "That sounds challenging. I'm here to support.",
                "I understand this is difficult. Let's address it.",
            ],
            EmotionalTone.POSITIVE: [
                "That's great! I'm glad to hear that.",
                "Wonderful! Let's build on that.",
                "I appreciate your positivity! Let's continue.",
            ],
            EmotionalTone.NEUTRAL: [
                "I understand what you're asking.",
                "Let me help with that.",
                "I'm here to assist.",
            ],
        }
        
        templates = empathy_templates.get(state["emotional_tone"], empathy_templates[EmotionalTone.NEUTRAL])
        # Use empathy score to pick most empathetic template
        idx = min(int(state["empathy_score"] * len(templates)), len(templates) - 1)
        state["empathetic_response"] = templates[idx]
        
        return state
    
    async def _create_response_node(self, state: ConversationState) -> ConversationState:
        """Node: Create the actual AI response to the user's query"""
        # Build context for response generation
        context_messages = "\n".join([
            f"{msg['role'].upper()}: {msg['content']}"
            for msg in state["conversation_history"][-3:]  # Last 3 messages for context
        ]) if state["conversation_history"] else ""
        
        prompt = f"""You are a helpful, empathetic AI assistant.

Conversation context:
{context_messages}

User's current message: {state['user_message']}

Emotional context: {state['context_awareness']}

Provide a helpful, accurate response that:
1. Acknowledges their feelings
2. Addresses their specific question or concern
3. Offers practical help or insight
4. Maintains a warm, human tone

Keep the response concise but meaningful."""

        response = self.model.generate_content(prompt)
        state["final_response"] = response.text
        
        return state
    
    async def _enhance_with_empathy_node(self, state: ConversationState) -> ConversationState:
        """Node: Enhance response with empathetic elements"""
        # If empathy score is high, add empathetic touches
        if state["empathy_score"] > 0.6:
            enhance_prompt = f"""Enhance this response with empathy while maintaining accuracy:

Original response: {state['final_response']}

Add empathetic elements such as:
- Acknowledging feelings
- Validating concerns
- Showing understanding
- Offering support

Return the enhanced response. Keep it natural and genuine."""
            
            response = self.model.generate_content(enhance_prompt)
            state["final_response"] = response.text
        
        # Add empathetic opening if needed
        if state["empathy_score"] > 0.3:
            state["final_response"] = f"{state['empathetic_response']}\n\n{state['final_response']}"
        
        return state
    
    async def generate_empathetic_response(
        self,
        user_message: str,
        conversation_history: List[Dict[str, Any]] | None = None
    ) -> str:
        """
        Generate an empathetic AI response to user message.
        
        Args:
            user_message: The user's current message
            conversation_history: Previous messages in conversation
            
        Returns:
            Empathetic AI response
        """
        initial_state = ConversationState(
            user_message=user_message,
            conversation_history=conversation_history or [],
            emotional_tone=EmotionalTone.NEUTRAL,
            empathy_score=0.5,
            context_awareness="general conversation",
            empathetic_response="",
            final_response=""
        )
        
        # Run the empathy graph
        final_state = await self.graph.ainvoke(initial_state)
        
        return final_state["final_response"]
    
    async def get_emotional_summary(
        self,
        conversation_history: List[Dict[str, Any]]
    ) -> dict:
        """
        Get emotional summary of entire conversation.
        
        Returns:
            Summary with emotional journey, key concerns, and sentiment
        """
        if not conversation_history:
            return {"summary": "No conversation history", "sentiment": "neutral", "concerns": []}
        
        prompt = f"""Analyze this conversation history for emotional patterns:

{json.dumps(conversation_history, indent=2)}

Provide a JSON object with:
- "sentiment": overall (positive, negative, mixed)
- "emotional_journey": brief description of how user's mood evolved
- "key_concerns": list of main issues raised
- "empathy_level_needed": 0-1 (how much empathy user needs going forward)
- "recommendation": brief note on how to continue supporting them

Return ONLY valid JSON."""

        response = self.model.generate_content(prompt)
        try:
            return json.loads(response.text)
        except json.JSONDecodeError:
            return {
                "sentiment": "neutral",
                "emotional_journey": "conversation in progress",
                "key_concerns": [],
                "empathy_level_needed": 0.5,
                "recommendation": "continue with supportive tone"
            }
