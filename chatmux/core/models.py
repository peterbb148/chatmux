"""Core data models for Chatmux."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class PaneStatus(str, Enum):
    """Status of a model pane."""
    
    IDLE = "idle"
    STREAMING = "streaming"
    ERROR = "error"
    DISABLED = "disabled"


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
    estimated_cost: Optional[float] = None


class Message(BaseModel):
    """A message in the conversation."""
    
    id: UUID = Field(default_factory=uuid4)
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    model_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    token_usage: Optional[TokenUsage] = None
    
    @field_validator('content')
    @classmethod
    def content_not_empty(cls, v: str) -> str:
        """Ensure content is not empty."""
        if not v.strip():
            raise ValueError("Message content cannot be empty")
        return v


class ModelConfig(BaseModel):
    """Configuration for a specific model."""
    
    provider: ModelProvider
    model_name: str
    api_key: Optional[str] = Field(default=None, exclude=True)  # Exclude from serialization
    endpoint: Optional[str] = None
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=2000, gt=0)
    timeout: int = Field(default=30, gt=0)
    retry_attempts: int = Field(default=3, ge=0)
    retry_delay: float = Field(default=1.0, gt=0)
    enabled: bool = True
    
    @field_validator('model_name')
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
    current_response: Optional[str] = None
    last_error: Optional[str] = None
    is_focused: bool = False
    
    def reset(self) -> None:
        """Reset the pane to idle state."""
        self.status = PaneStatus.IDLE
        self.current_response = None
        self.last_error = None


class ChatSession(BaseModel):
    """A chat session with conversation history."""
    
    id: UUID = Field(default_factory=uuid4)
    title: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    messages: List[Message] = Field(default_factory=list)
    model_panes: List[ModelPane] = Field(default_factory=list)
    active: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def add_message(self, message: Message) -> None:
        """Add a message to the session."""
        self.messages.append(message)
        self.updated_at = datetime.utcnow()
    
    def get_messages_for_model(self, model_id: str) -> List[Message]:
        """Get all messages for a specific model."""
        return [
            msg for msg in self.messages 
            if msg.model_id == model_id or msg.role in (MessageRole.USER, MessageRole.SYSTEM)
        ]
    
    def clear_messages(self) -> None:
        """Clear all messages from the session."""
        self.messages.clear()
        self.updated_at = datetime.utcnow()
    
    class Config:
        """Pydantic config."""
        
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }