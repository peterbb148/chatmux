import asyncio
import logging
import os
from collections.abc import AsyncGenerator
from pathlib import Path

try:
    import openai
    from dotenv import load_dotenv

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from typing import Any

from .base import BaseLLMProvider

# Load environment variables from parent .env file
env_path = Path(__file__).parent.parent.parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI provider with real API integration"""

    def __init__(self):
        if not OPENAI_AVAILABLE:
            logger.warning("OpenAI library not installed. Install with: pip install openai")
            return

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY not found in environment variables")
            return

        self.client = openai.AsyncClient(api_key=api_key)

    async def stream_completion(
        self, prompt: str, messages: list[dict[str, Any]] = None
    ) -> AsyncGenerator[str, None]:
        if not OPENAI_AVAILABLE or not hasattr(self, "client"):
            # Fallback to mock response
            response = f"[Mock] This is a simulated response from GPT-4 to: {prompt}"
            words = response.split()
            for word in words:
                yield word + " "
                await asyncio.sleep(0.1)
            return

        try:
            # Get the model name from environment
            model_name = os.getenv("OPENAI_MODEL_1", "gpt-4o")

            # Use provided messages or create new conversation
            if messages:
                # Append the current prompt as the latest user message
                conversation = messages + [{"role": "user", "content": prompt}]
            else:
                conversation = [{"role": "user", "content": prompt}]

            stream = await self.client.chat.completions.create(
                model=model_name,
                messages=conversation,
                temperature=0.7,
                max_tokens=2000,
                stream=True,
            )

            logger.info(f"Starting OpenAI stream for model: {model_name}")
            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    logger.debug(f"OpenAI chunk: {content}")
                    yield content
            logger.info("OpenAI stream completed")

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            yield f"Error: {str(e)}"

    async def get_completion(self, prompt: str, messages: list[dict[str, Any]] = None) -> str:
        if not OPENAI_AVAILABLE or not hasattr(self, "client"):
            return f"[Mock] This is a simulated response from GPT-4 to: {prompt}"

        try:
            model_name = os.getenv("OPENAI_MODEL_1", "gpt-4o")

            response = await self.client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=2000,
                stream=False,
            )

            return response.choices[0].message.content or ""

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return f"Error: {str(e)}"
