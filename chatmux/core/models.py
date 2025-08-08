"""Core data models for Chatmux."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_serializer, field_validator


class PaneStatus(str, Enum):
    """Status of a model pane."""

    IDLE = "idle"
    STREAMING = "streaming"
    ERROR = "error"
    DISABLED = "disabled"
    COMPLETE = "complete"
    RATE_LIMITED = "rate_limited"
    CANCELLED = "cancelled"


class MessageRole(str, Enum):
    """Role of a message in the conversation."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ModelProvider(str, Enum):
    """Supported model providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    MISTRAL = "mistral"
    OLLAMA = "ollama"


class TokenUsage(BaseModel):
    """Token usage statistics for a model response."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost: float | None = None


class Message(BaseModel):
    """A message in the conversation."""

    id: UUID = Field(default_factory=uuid4)
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    model_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    token_usage: TokenUsage | None = None

    @field_validator("content")
    @classmethod
    def content_not_empty(cls, v: str) -> str:
        """Ensure content is not empty."""
        if not v.strip():
            raise ValueError("Message content cannot be empty")
        return v

    @field_serializer("id", "timestamp")
    def serialize_datetime_and_uuid(self, value: datetime | UUID) -> str:
        """Serialize datetime and UUID fields."""
        if isinstance(value, datetime):
            return value.isoformat()
        elif isinstance(value, UUID):
            return str(value)
        return value


class ModelConfig(BaseModel):
    """Configuration for a specific model."""

    provider: ModelProvider
    model_name: str
    api_key: str | None = Field(default=None, exclude=True)  # Exclude from serialization
    endpoint: str | None = None
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=2000, gt=0)
    timeout: int = Field(default=30, gt=0)
    retry_attempts: int = Field(default=3, ge=0)
    retry_delay: float = Field(default=1.0, gt=0)
    enabled: bool = True
    pane_id: str | None = None  # Optional pane identifier for UI integration

    @field_validator("model_name")
    @classmethod
    def model_name_not_empty(cls, v: str) -> str:
        """Ensure model name is not empty."""
        if not v.strip():
            raise ValueError("Model name cannot be empty")
        return v


class ModelPane(BaseModel):
    """Represents a model pane in the grid layout."""

    id: UUID = Field(default_factory=uuid4)
    position: int = Field(ge=0, le=4)  # 0-4 for 5 model panes
    config: ModelConfig
    status: PaneStatus = PaneStatus.IDLE
    current_response: str | None = None
    last_error: str | None = None
    is_focused: bool = False

    def reset(self) -> None:
        """Reset the pane to idle state."""
        self.status = PaneStatus.IDLE
        self.current_response = None
        self.last_error = None

    @field_serializer("id")
    def serialize_uuid(self, value: UUID) -> str:
        """Serialize UUID field."""
        return str(value)


class ChatSession(BaseModel):
    """A chat session with conversation history."""

    id: UUID = Field(default_factory=uuid4)
    title: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    messages: list[Message] = Field(default_factory=list)
    model_panes: list[ModelPane] = Field(default_factory=list)
    active: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    def add_message(self, message: Message) -> None:
        """Add a message to the session."""
        self.messages.append(message)
        self.updated_at = datetime.utcnow()

    def get_messages_for_model(self, model_id: str) -> list[Message]:
        """Get all messages for a specific model."""
        return [
            msg
            for msg in self.messages
            if msg.model_id == model_id or msg.role in (MessageRole.USER, MessageRole.SYSTEM)
        ]

    def clear_messages(self) -> None:
        """Clear all messages from the session."""
        self.messages.clear()
        self.updated_at = datetime.utcnow()

    @field_serializer("id", "created_at", "updated_at")
    def serialize_datetime_and_uuid(self, value: datetime | UUID) -> str:
        """Serialize datetime and UUID fields."""
        if isinstance(value, datetime):
            return value.isoformat()
        elif isinstance(value, UUID):
            return str(value)
        return value
