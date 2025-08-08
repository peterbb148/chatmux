"""Tests for OpenAI client implementation."""

from unittest.mock import AsyncMock, Mock, patch

import openai
import pytest

from chatmux.core.models import Message, MessageRole, ModelConfig, ModelProvider, TokenUsage
from chatmux.models import AuthError, ConfigError, OpenAIClient, RateLimitError


@pytest.fixture
def config():
    """Create test OpenAI configuration."""
    return ModelConfig(
        provider=ModelProvider.OPENAI,
        model_name="gpt-3.5-turbo",
        api_key="test-api-key",
        temperature=0.7,
        max_tokens=100,
    )


@pytest.fixture
def messages():
    """Create test messages."""
    return [
        Message(
            role=MessageRole.SYSTEM,
            content="You are a helpful assistant.",
        ),
        Message(role=MessageRole.USER, content="Hello"),
        Message(role=MessageRole.ASSISTANT, content="Hi there!"),
        Message(role=MessageRole.USER, content="How are you?"),
    ]


class TestOpenAIClient:
    """Test OpenAI client functionality."""

    def test_init(self, config):
        """Test client initialization."""
        client = OpenAIClient(config)
        assert client.config == config
        assert isinstance(client.client, openai.AsyncClient)

    def test_init_no_api_key(self):
        """Test initialization without API key."""
        config = ModelConfig(
            provider=ModelProvider.OPENAI,
            model_name="gpt-3.5-turbo",
            api_key=None,
        )
        with pytest.raises(ConfigError, match="API key is required"):
            OpenAIClient(config)

    def test_convert_messages(self, config, messages):
        """Test message conversion to OpenAI format."""
        client = OpenAIClient(config)
        converted = client._convert_messages(messages)

        assert len(converted) == 4
        assert converted[0] == {
            "role": "system",
            "content": "You are a helpful assistant.",
        }
        assert converted[1] == {"role": "user", "content": "Hello"}
        assert converted[2] == {"role": "assistant", "content": "Hi there!"}
        assert converted[3] == {"role": "user", "content": "How are you?"}

    @pytest.mark.asyncio
    async def test_stream_response(self, config, messages):
        """Test streaming response."""
        client = OpenAIClient(config)

        # Mock the streaming response
        mock_chunk1 = Mock()
        mock_chunk1.choices = [Mock(delta=Mock(content="I'm "))]
        mock_chunk2 = Mock()
        mock_chunk2.choices = [Mock(delta=Mock(content="doing "))]
        mock_chunk3 = Mock()
        mock_chunk3.choices = [Mock(delta=Mock(content="well!"))]
        mock_chunk4 = Mock()
        mock_chunk4.choices = [Mock(delta=Mock(content=None))]

        async def mock_stream():
            for chunk in [mock_chunk1, mock_chunk2, mock_chunk3, mock_chunk4]:
                yield chunk

        with patch.object(
            client.client.chat.completions, "create", new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_stream()

            # Collect streamed response
            response = ""
            async for chunk in client.stream_response(messages):
                response += chunk

            assert response == "I'm doing well!"
            mock_create.assert_called_once_with(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant.",
                    },
                    {"role": "user", "content": "Hello"},
                    {"role": "assistant", "content": "Hi there!"},
                    {"role": "user", "content": "How are you?"},
                ],
                temperature=0.7,
                max_tokens=100,
                stream=True,
            )

    @pytest.mark.asyncio
    async def test_stream_response_auth_error(self, config, messages):
        """Test streaming with authentication error."""
        client = OpenAIClient(config)

        with patch.object(
            client.client.chat.completions, "create", new_callable=AsyncMock
        ) as mock_create:
            # Create a mock response for OpenAI error
            mock_response = Mock()
            mock_response.status_code = 401
            mock_response.json.return_value = {"error": {"message": "Invalid API key"}}
            mock_create.side_effect = openai.AuthenticationError(
                "Invalid API key", response=mock_response, body={}
            )

            with pytest.raises(AuthError, match="authentication failed"):
                async for _ in client.stream_response(messages):
                    pass

    @pytest.mark.asyncio
    async def test_stream_response_rate_limit(self, config, messages):
        """Test streaming with rate limit error."""
        client = OpenAIClient(config)

        with patch.object(
            client.client.chat.completions, "create", new_callable=AsyncMock
        ) as mock_create:
            # Create a mock response for OpenAI error
            mock_response = Mock()
            mock_response.status_code = 429
            mock_response.json.return_value = {"error": {"message": "Rate limit exceeded"}}
            mock_create.side_effect = openai.RateLimitError(
                "Rate limit exceeded", response=mock_response, body={}
            )

            with pytest.raises(RateLimitError, match="rate limit exceeded"):
                async for _ in client.stream_response(messages):
                    pass

    @pytest.mark.asyncio
    async def test_send_message(self, config, messages):
        """Test sending message and getting complete response."""
        client = OpenAIClient(config)

        # Mock response
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="I'm doing great!"))]
        mock_response.usage = Mock(
            prompt_tokens=20,
            completion_tokens=5,
            total_tokens=25,
        )

        with patch.object(
            client.client.chat.completions, "create", new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_response

            response_text, token_usage = await client.send_message(messages)

            assert response_text == "I'm doing great!"
            assert isinstance(token_usage, TokenUsage)
            assert token_usage.prompt_tokens == 20
            assert token_usage.completion_tokens == 5
            assert token_usage.total_tokens == 25
            assert token_usage.estimated_cost > 0

    @pytest.mark.asyncio
    async def test_send_message_no_usage(self, config, messages):
        """Test sending message without usage data."""
        client = OpenAIClient(config)

        # Mock response without usage
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Hello!"))]
        mock_response.usage = None

        with patch.object(
            client.client.chat.completions, "create", new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_response

            response_text, token_usage = await client.send_message(messages)

            assert response_text == "Hello!"
            assert token_usage is None

    def test_estimate_cost_gpt4(self, config):
        """Test cost estimation for GPT-4."""
        config.model_name = "gpt-4"
        client = OpenAIClient(config)

        # 1000 prompt tokens, 500 completion tokens
        cost = client._estimate_cost(1000, 500)

        # GPT-4: $30/1M prompt, $60/1M completion
        expected = (1000 / 1_000_000 * 30) + (500 / 1_000_000 * 60)
        assert cost == pytest.approx(expected)

    def test_estimate_cost_gpt35(self, config):
        """Test cost estimation for GPT-3.5."""
        config.model_name = "gpt-3.5-turbo"
        client = OpenAIClient(config)

        # 1000 prompt tokens, 500 completion tokens
        cost = client._estimate_cost(1000, 500)

        # GPT-3.5: $0.5/1M prompt, $1.5/1M completion
        expected = (1000 / 1_000_000 * 0.5) + (500 / 1_000_000 * 1.5)
        assert cost == pytest.approx(expected)

    def test_estimate_cost_unknown_model(self, config):
        """Test cost estimation for unknown model (defaults to GPT-3.5)."""
        config.model_name = "gpt-5-unknown"
        client = OpenAIClient(config)

        cost = client._estimate_cost(1000, 500)

        # Should default to GPT-3.5 pricing
        expected = (1000 / 1_000_000 * 0.5) + (500 / 1_000_000 * 1.5)
        assert cost == pytest.approx(expected)
