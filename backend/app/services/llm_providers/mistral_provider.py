import logging
import os
from collections.abc import AsyncGenerator

from dotenv import load_dotenv
from mistralai import Mistral

from .base import BaseLLMProvider

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../../../.env"))

logger = logging.getLogger(__name__)


class MistralProvider(BaseLLMProvider):
    """Mistral AI provider with streaming support"""

    def __init__(self):
        self.api_key = os.getenv("MISTRAL_API_KEY")
        self.model_name = os.getenv("MISTRAL_MODEL_4", "mistral-large-latest")
        self.client = None

        if self.api_key:
            self.client = Mistral(api_key=self.api_key)
            logger.info(f"Initialized Mistral provider with model: {self.model_name}")
        else:
            logger.warning(
                "MISTRAL_API_KEY not found - Mistral provider will return mock responses"
            )

    async def stream_completion(self, prompt: str) -> AsyncGenerator[str, None]:
        if not self.client:
            # Return mock response if no API key
            response = (
                f"[Mock Mistral Response] This is a simulated response "
                f"from {self.model_name} to: {prompt}"
            )
            words = response.split()
            for word in words:
                yield word + " "
            return

        try:
            logger.info(f"Starting Mistral stream for model: {self.model_name}")

            # Mistral SDK uses sync streaming
            response = self.client.chat.stream(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.7,
            )

            for chunk in response:
                if chunk.data.choices[0].delta.content:
                    yield chunk.data.choices[0].delta.content

            logger.info("Mistral stream completed")

        except Exception as e:
            logger.error(f"Error in Mistral stream_completion: {e}")
            yield f"Error: {str(e)}"

    async def get_completion(self, prompt: str) -> str:
        if not self.client:
            return (
                f"[Mock Mistral Response] This is a simulated response "
                f"from {self.model_name} to: {prompt}"
            )

        try:
            response = self.client.chat.complete(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.7,
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Error in Mistral get_completion: {e}")
            return f"Error: {str(e)}"
