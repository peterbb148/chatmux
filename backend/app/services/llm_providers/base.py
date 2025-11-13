from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import Any


class BaseLLMProvider(ABC):
    """Base class for LLM providers"""

    def __init__(self, model_name: str = None):
        """Initialize provider with optional model name"""
        self.model_name = model_name

    @abstractmethod
    async def stream_completion(
        self, prompt: str, messages: list[dict[str, Any]] = None
    ) -> AsyncGenerator[str, None]:
        """Stream completion from the LLM"""
        pass

    @abstractmethod
    async def get_completion(self, prompt: str, messages: list[dict[str, Any]] = None) -> str:
        """Get a non-streaming completion from the LLM"""
        pass
