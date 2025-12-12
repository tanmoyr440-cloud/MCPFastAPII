import logging
import json
from typing import Dict, Any, List, Optional
from app.mcp.tools import web_search

logger = logging.getLogger(__name__)

class GroundingService:
    """
    Service to verify LLM responses against external sources (Grounding).
    """

    async def verify_response(self, query: str, response: str, llm_service) -> Dict[str, Any]:
        """
        Verify the response by extracting claims and checking them against web search.
        
        Args:
            query: The original user query.
            response: The LLM's response.
            llm_service: The LLMService instance (passed to avoid circular imports).
            
        Returns:
            Dict containing verification results.
        """
        try:
            # 1. Extract claims
            claims = await self._extract_claims(response, llm_service)
            if not claims:
                return {"verified": False, "reason": "No verifiable claims found."}

            # 2. Search for evidence
            # We'll search for the original query + key terms from claims
            # For simplicity, just search the query for now, or construct a search query from claims.
            search_query = f"{query} {claims[0]}" if claims else query
            search_results = web_search(search_query, num_results=3)

            # 3. Verify claims against evidence
            verification = await self._verify_claims(claims, search_results, llm_service)
            
            return {
                "verified": True,
                "claims": claims,
                "evidence": search_results,
                "verification_analysis": verification
            }

        except Exception as e:
            logger.error(f"Grounding failed: {e}")
            return {"verified": False, "error": str(e)}

    async def _extract_claims(self, text: str, llm_service) -> List[str]:
        """Extract factual claims from text using LLM."""
        prompt = f"""
        Extract the key factual claims from the following text. 
        Return them as a JSON list of strings.
        Text: "{text}"
        """
        try:
            # Use JSON mode if available, or just parse text
            response = await llm_service.get_json_response(
                prompt=prompt,
                system_prompt="You are a fact-checker. Extract verifiable claims as a JSON list."
            )
            if isinstance(response, list):
                return response
            elif isinstance(response, dict) and "claims" in response:
                return response["claims"]
            return []
        except Exception as e:
            logger.warning(f"Failed to extract claims: {e}")
            return []

    async def _verify_claims(self, claims: List[str], evidence: str, llm_service) -> str:
        """Verify claims against evidence using LLM."""
        prompt = f"""
        Verify the following claims against the provided evidence.
        
        Claims:
        {json.dumps(claims, indent=2)}
        
        Evidence:
        {evidence}
        
        Provide a brief analysis of whether the claims are supported by the evidence.
        """
        return await llm_service.get_response(
            prompt=prompt,
            system_prompt="You are a fact-checker. Verify claims against evidence."
        )

# Global instance
grounding_service = GroundingService()
