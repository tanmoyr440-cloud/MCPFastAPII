from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseMiddleware(ABC):
    """
    Base class for LLM Service Middleware.
    Allows intercepting requests and responses.
    """

    async def process_request(self, context: Dict[str, Any]) -> None:
        """
        Process the request before it is sent to the LLM.
        Modify context in-place.
        """
        pass

    async def process_response(self, context: Dict[str, Any]) -> None:
        """
        Process the response after it is received from the LLM.
        Modify context in-place.
        """
        pass
