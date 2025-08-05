"""Abstract base class for model clients and common functionality."""

import abc
from typing import AsyncGenerator, List, Optional

from ..core.models import Message, ModelConfig, TokenUsage


class ModelClient(abc.ABC):
    """Abstract base class for model clients.
    
    Provides common interface and functionality for interacting with different 
    model providers (OpenAI, Anthropic, etc).
    """

    def __init__(self, config: ModelConfig):
        """Initialize model client with configuration.
        
        Args:
            config: Model-specific configuration and API settings
        """
        self.config = config
        self._validate_config()

    @abc.abstractmethod
    async def stream_response(
        self, messages: List[Message]
    ) -> AsyncGenerator[str, None]:
        """Stream model response tokens for the given messages.
        
        Args:
            messages: List of conversation messages to generate from
            
        Yields:
            Response text tokens as they become available
            
        Raises:
            ModelError: For API/generation errors
            ConfigError: For invalid configuration
            RateLimitError: When API rate limits are hit
            AuthError: For authentication/key issues
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def send_message(
        self, messages: List[Message]
    ) -> tuple[str, Optional[TokenUsage]]:
        """Send messages and get complete response.
        
        Args:
            messages: List of conversation messages to generate from
            
        Returns:
            Tuple of (response text, token usage data if available)
            
        Raises:
            ModelError: For API/generation errors
            ConfigError: For invalid configuration  
            RateLimitError: When API rate limits are hit
            AuthError: For authentication/key issues
        """
        raise NotImplementedError

    def _validate_config(self) -> None:
        """Validate model configuration.
        
        The base implementation uses Pydantic validation.
        Override to add provider-specific validation.
        
        Raises:
            ConfigError: If configuration is invalid
        """
        # Config already validated by Pydantic
        pass