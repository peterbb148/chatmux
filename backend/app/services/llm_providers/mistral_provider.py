import asyncio
import logging
from collections.abc import AsyncGenerator

from .base import BaseLLMProvider

logger = logging.getLogger(__name__)


class MistralProvider(BaseLLMProvider):
    """Mock Mistral provider for development"""

    async def stream_completion(self, prompt: str) -> AsyncGenerator[str, None]:
        # Mock streaming response
        response = f"This is a mock response from Mistral Large to: {prompt}"
        words = response.split()

        for word in words:
            yield word + " "
            await asyncio.sleep(0.09)  # Different timing

    async def get_completion(self, prompt: str) -> str:
        # Mock non-streaming response
        return f"This is a mock response from Mistral Large to: {prompt}"
