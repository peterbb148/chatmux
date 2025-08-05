"""Tests for model client base interface."""

import pytest

from chatmux.core.models import Message, MessageRole, ModelConfig, ModelProvider, TokenUsage
from chatmux.models import ModelClient


class MockModelClient(ModelClient):
    """Mock implementation for testing base client."""

    async def stream_response(self, messages):
        yield "test"

    async def send_message(self, messages):
        return "test response", TokenUsage(
            prompt_tokens=10, completion_tokens=5, total_tokens=15, estimated_cost=0.0015
        )


@pytest.fixture
def config():
    """Create test model config."""
    return ModelConfig(
        provider=ModelProvider.OPENAI,
        model_name="test-model",
        api_key="test-key",
        temperature=0.7,
        max_tokens=100,
    )


@pytest.fixture
def messages():
    """Create test message list."""
    return [
        Message(role=MessageRole.USER, content="Hello"),
        Message(role=MessageRole.ASSISTANT, content="Hi there"),
    ]


def test_init_validates_config(config):
    """Test client initialization validates config."""
    client = MockModelClient(config)
    assert client.config == config


@pytest.mark.asyncio
async def test_stream_response(config, messages):
    """Test streaming response generation."""
    client = MockModelClient(config)
    chunks = [chunk async for chunk in client.stream_response(messages)]
    assert chunks == ["test"]


@pytest.mark.asyncio
async def test_send_message(config, messages):
    """Test complete message response."""
    client = MockModelClient(config)
    response, usage = await client.send_message(messages)
    assert response == "test response"
    assert usage.prompt_tokens == 10
    assert usage.completion_tokens == 5
    assert usage.total_tokens == 15
    assert usage.estimated_cost == 0.0015
