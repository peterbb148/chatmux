"""Common error types for model clients."""


class ModelError(Exception):
    """Base class for model client errors."""
    pass


class ConfigError(ModelError):
    """Error due to invalid configuration."""
    pass


class RateLimitError(ModelError):
    """Error due to API rate limits being exceeded."""
    pass


class AuthError(ModelError):
    """Error due to authentication/API key issues."""
    pass
