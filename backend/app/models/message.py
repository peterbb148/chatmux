from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageTarget(BaseModel):
    model_id: int
    model_name: str
    provider: str


class Message(BaseModel):
    content: str
    role: MessageRole = MessageRole.USER
    targets: list[int] = []  # Empty means all models
    timestamp: datetime | None = Field(default_factory=datetime.now)
    user_id: str = "default"


class StreamingResponse(BaseModel):
    model_id: int
    model_name: str
    provider: str
    content: str
    is_complete: bool = False
    timestamp: datetime | None = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
