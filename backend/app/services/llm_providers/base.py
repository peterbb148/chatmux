from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator


class BaseLLMProvider(ABC):
    """Base class for LLM providers"""

    @abstractmethod
    async def stream_completion(self, prompt: str) -> AsyncGenerator[str, None]:
        """Stream completion from the LLM"""
        pass

    @abstractmethod
    async def get_completion(self, prompt: str) -> str:
        """Get a non-streaming completion from the LLM"""
        pass
