import logging
import os
from collections.abc import AsyncGenerator
from typing import Any

from anthropic import AsyncAnthropic
from dotenv import load_dotenv

from .base import BaseLLMProvider

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../../../.env"))

logger = logging.getLogger(__name__)


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude provider with streaming support"""

    def __init__(self, model_name: str = "claude-3-5-sonnet-20241022"):
        super().__init__(model_name)
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.client = None

        if self.api_key:
            self.client = AsyncAnthropic(api_key=self.api_key)
            logger.info(f"Initialized Anthropic provider with model: {self.model_name}")
        else:
            logger.warning(
                "ANTHROPIC_API_KEY not found - Anthropic provider will return mock responses"
            )

    async def stream_completion(
        self, prompt: str, messages: list[dict[str, Any]] = None
    ) -> AsyncGenerator[str, None]:
        if not self.client:
            # Return mock response if no API key
            response = (
                f"[Mock Anthropic Response] This is a simulated response "
                f"from {self.model_name} to: {prompt}"
            )
            words = response.split()
            for word in words:
                yield word + " "
            return

        try:
            logger.info(f"Starting Anthropic stream for model: {self.model_name}")

            # Format messages for Anthropic API
            if messages:
                # Append the current prompt as the latest user message
                conversation = messages + [{"role": "user", "content": prompt}]
            else:
                conversation = [{"role": "user", "content": prompt}]

            async with self.client.messages.stream(
                model=self.model_name,
                messages=conversation,
                max_tokens=2000,
                temperature=0.7,
            ) as stream:
                async for text in stream.text_stream:
                    yield text

            logger.info("Anthropic stream completed")

        except Exception as e:
            logger.error(f"Error in Anthropic stream_completion: {e}")
            yield f"Error: {str(e)}"

    async def get_completion(self, prompt: str, messages: list[dict[str, Any]] = None) -> str:
        try:
            message = await self.client.messages.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.7,
            )

            return message.content[0].text

        except Exception as e:
            logger.error(f"Error in Anthropic get_completion: {e}")
            return f"Error: {str(e)}"
