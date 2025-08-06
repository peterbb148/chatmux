import asyncio
import logging
from collections.abc import AsyncGenerator

from .base import BaseLLMProvider

logger = logging.getLogger(__name__)


class GoogleProvider(BaseLLMProvider):
    """Mock Google provider for development"""

    async def stream_completion(self, prompt: str) -> AsyncGenerator[str, None]:
        # Mock streaming response
        response = f"This is a mock response from Gemini Pro to: {prompt}"
        words = response.split()

        for word in words:
            yield word + " "
            await asyncio.sleep(0.12)  # Different timing pattern

    async def get_completion(self, prompt: str) -> str:
        # Mock non-streaming response
        return f"This is a mock response from Gemini Pro to: {prompt}"
