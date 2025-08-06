import asyncio
import logging
from collections.abc import AsyncGenerator

from .base import BaseLLMProvider

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseLLMProvider):
    """Mock OpenAI provider for development"""

    async def stream_completion(self, prompt: str) -> AsyncGenerator[str, None]:
        # Mock streaming response
        response = f"This is a mock response from GPT-4 to: {prompt}"
        words = response.split()

        for word in words:
            yield word + " "
            await asyncio.sleep(0.1)  # Simulate streaming delay

    async def get_completion(self, prompt: str) -> str:
        # Mock non-streaming response
        return f"This is a mock response from GPT-4 to: {prompt}"
