import logging
import os
from collections.abc import AsyncGenerator
from typing import Any

import google.generativeai as genai
from dotenv import load_dotenv

from .base import BaseLLMProvider

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../../../.env"))

logger = logging.getLogger(__name__)


class GoogleProvider(BaseLLMProvider):
    """Google Gemini provider with streaming support"""

    def __init__(self, model_name: str = "gemini-1.5-pro"):
        super().__init__(model_name)
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.model = None

        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
            logger.info(f"Initialized Google provider with model: {self.model_name}")
        else:
            logger.warning("GOOGLE_API_KEY not found - Google provider will return mock responses")

    async def stream_completion(
        self, prompt: str, messages: list[dict[str, Any]] = None
    ) -> AsyncGenerator[str, None]:
        if not self.model:
            # Return mock response if no API key
            response = (
                f"[Mock Google Response] This is a simulated response "
                f"from {self.model_name} to: {prompt}"
            )
            words = response.split()
            for word in words:
                yield word + " "
            return

        try:
            logger.info(f"Starting Google stream for model: {self.model_name}")

            # Format conversation for Google (they use a different format)
            if messages:
                # Convert messages to Google's format
                formatted_prompt = ""
                for msg in messages:
                    role = "User" if msg["role"] == "user" else "Assistant"
                    formatted_prompt += f"{role}: {msg['content']}\n\n"
                formatted_prompt += f"User: {prompt}\nAssistant:"
            else:
                formatted_prompt = prompt

            # Google's SDK doesn't have native async streaming, so we use sync streaming
            response = self.model.generate_content(
                formatted_prompt,
                generation_config=genai.GenerationConfig(
                    max_output_tokens=2000,
                    temperature=0.7,
                ),
                stream=True,
            )

            for chunk in response:
                if chunk.text:
                    yield chunk.text

            logger.info("Google stream completed")

        except Exception as e:
            logger.error(f"Error in Google stream_completion: {e}")
            yield f"Error: {str(e)}"

    async def get_completion(self, prompt: str, messages: list[dict[str, Any]] = None) -> str:
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    max_output_tokens=2000,
                    temperature=0.7,
                ),
            )

            return response.text

        except Exception as e:
            logger.error(f"Error in Google get_completion: {e}")
            return f"Error: {str(e)}"
