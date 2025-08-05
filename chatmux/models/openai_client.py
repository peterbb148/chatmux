"""OpenAI model client implementation."""

from collections.abc import AsyncGenerator

import openai
from openai.types.chat import ChatCompletionMessageParam

from ..core.models import Message, MessageRole, ModelConfig, TokenUsage
from .base import ModelClient
from .errors import AuthError, ConfigError, ModelError, RateLimitError


class OpenAIClient(ModelClient):
    """Client for interacting with OpenAI models."""

    def __init__(self, config: ModelConfig):
        """Initialize OpenAI client.

        Args:
            config: Model configuration including API key
        """
        super().__init__(config)
        self.client = openai.AsyncClient(api_key=self.config.api_key)

    def _validate_config(self) -> None:
        """Validate OpenAI-specific configuration."""
        super()._validate_config()
        if not self.config.api_key:
            raise ConfigError("OpenAI API key is required")

    def _convert_messages(self, messages: list[Message]) -> list[ChatCompletionMessageParam]:
        """Convert our Message objects to OpenAI format.

        Args:
            messages: List of Message objects

        Returns:
            List of messages in OpenAI format
        """
        openai_messages: list[ChatCompletionMessageParam] = []
        for msg in messages:
            if msg.role == MessageRole.USER:
                openai_messages.append({"role": "user", "content": msg.content})
            else:
                openai_messages.append({"role": "assistant", "content": msg.content})
        return openai_messages

    async def stream_response(  # type: ignore[override]
        self, messages: list[Message]
    ) -> AsyncGenerator[str, None]:
        """Stream response from OpenAI.

        Args:
            messages: Conversation history

        Yields:
            Response text chunks
        """
        try:
            stream = await self.client.chat.completions.create(
                model=self.config.model_name,
                messages=self._convert_messages(messages),
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                stream=True,
            )

            async for chunk in stream:  # type: ignore[union-attr]
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content

        except openai.AuthenticationError as e:
            raise AuthError(f"OpenAI authentication failed: {str(e)}") from e
        except openai.RateLimitError as e:
            raise RateLimitError(f"OpenAI rate limit exceeded: {str(e)}") from e
        except openai.APIError as e:
            raise ModelError(f"OpenAI API error: {str(e)}") from e
        except Exception as e:
            raise ModelError(f"Unexpected error: {str(e)}") from e

    async def send_message(self, messages: list[Message]) -> tuple[str, TokenUsage | None]:
        """Send messages and get complete response.

        Args:
            messages: Conversation history

        Returns:
            Tuple of (response text, token usage)
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.config.model_name,
                messages=self._convert_messages(messages),
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                stream=False,
            )

            # Extract response text
            response_text = response.choices[0].message.content or ""  # type: ignore[union-attr]

            # Extract token usage if available
            token_usage = None
            if hasattr(response, "usage") and response.usage:  # type: ignore[union-attr]
                token_usage = TokenUsage(
                    prompt_tokens=response.usage.prompt_tokens,  # type: ignore[union-attr]
                    completion_tokens=response.usage.completion_tokens,  # type: ignore[union-attr]
                    total_tokens=response.usage.total_tokens,  # type: ignore[union-attr]
                    # Estimate cost based on model
                    estimated_cost=self._estimate_cost(
                        response.usage.prompt_tokens,  # type: ignore[union-attr]
                        response.usage.completion_tokens,  # type: ignore[union-attr]
                    ),
                )

            return response_text, token_usage

        except openai.AuthenticationError as e:
            raise AuthError(f"OpenAI authentication failed: {str(e)}") from e
        except openai.RateLimitError as e:
            raise RateLimitError(f"OpenAI rate limit exceeded: {str(e)}") from e
        except openai.APIError as e:
            raise ModelError(f"OpenAI API error: {str(e)}") from e
        except Exception as e:
            raise ModelError(f"Unexpected error: {str(e)}") from e

    def _estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Estimate cost based on token usage.

        Args:
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens

        Returns:
            Estimated cost in USD
        """
        # Pricing as of 2024 (per 1M tokens)
        pricing = {
            "gpt-4": {"prompt": 30.0, "completion": 60.0},
            "gpt-4-32k": {"prompt": 60.0, "completion": 120.0},
            "gpt-3.5-turbo": {"prompt": 0.5, "completion": 1.5},
            "gpt-3.5-turbo-16k": {"prompt": 3.0, "completion": 4.0},
        }

        # Default to GPT-3.5 pricing if model not found
        model_pricing = pricing.get(self.config.model_name, pricing["gpt-3.5-turbo"])

        prompt_cost = (prompt_tokens / 1_000_000) * model_pricing["prompt"]
        completion_cost = (completion_tokens / 1_000_000) * model_pricing["completion"]

        return prompt_cost + completion_cost
