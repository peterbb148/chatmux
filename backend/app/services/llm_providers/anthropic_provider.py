import asyncio
import logging
from collections.abc import AsyncGenerator

from .base import BaseLLMProvider

logger = logging.getLogger(__name__)


class AnthropicProvider(BaseLLMProvider):
    """Mock Anthropic provider for development"""

    async def stream_completion(self, prompt: str) -> AsyncGenerator[str, None]:
        # Mock streaming response
        response = f"This is a mock response from Claude 3 to: {prompt}"
        words = response.split()

        for word in words:
            yield word + " "
            await asyncio.sleep(0.08)  # Slightly different timing for variety

    async def get_completion(self, prompt: str) -> str:
        # Mock non-streaming response
        return f"This is a mock response from Claude 3 to: {prompt}"
