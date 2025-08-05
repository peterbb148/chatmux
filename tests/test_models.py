"""Tests for core data models."""

import pytest
from datetime import datetime
from uuid import UUID

from chatmux.core.models import (
    PaneStatus,
    MessageRole,
    ModelProvider,
    TokenUsage,
    Message,
    ModelConfig,
    ModelPane,
    ChatSession,
)


class TestMessage:
    """Test Message model."""
    
    def test_message_creation(self):
        """Test creating a basic message."""
        msg = Message(role=MessageRole.USER, content="Hello, world!")
        assert msg.role == MessageRole.USER
        assert msg.content == "Hello, world!"
        assert isinstance(msg.id, UUID)
        assert isinstance(msg.timestamp, datetime)
        assert msg.model_id is None
        assert msg.metadata == {}
        assert msg.token_usage is None
    
    def test_message_with_all_fields(self):
        """Test message with all fields populated."""
        token_usage = TokenUsage(
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30,
            estimated_cost=0.001
        )
        msg = Message(
            role=MessageRole.ASSISTANT,
            content="Hello!",
            model_id="gpt-4",
            metadata={"source": "openai"},
            token_usage=token_usage
        )
        assert msg.model_id == "gpt-4"
        assert msg.metadata == {"source": "openai"}
        assert msg.token_usage.total_tokens == 30
    
    def test_message_empty_content_validation(self):
        """Test that empty content raises validation error."""
        with pytest.raises(ValueError, match="content cannot be empty"):
            Message(role=MessageRole.USER, content="")
        
        with pytest.raises(ValueError, match="content cannot be empty"):
            Message(role=MessageRole.USER, content="   ")


class TestModelConfig:
    """Test ModelConfig model."""
    
    def test_model_config_defaults(self):
        """Test ModelConfig with default values."""
        config = ModelConfig(
            provider=ModelProvider.OPENAI,
            model_name="gpt-4"
        )
        assert config.provider == ModelProvider.OPENAI
        assert config.model_name == "gpt-4"
        assert config.temperature == 0.7
        assert config.max_tokens == 2000
        assert config.timeout == 30
        assert config.retry_attempts == 3
        assert config.retry_delay == 1.0
        assert config.enabled is True
    
    def test_model_config_custom_values(self):
        """Test ModelConfig with custom values."""
        config = ModelConfig(
            provider=ModelProvider.ANTHROPIC,
            model_name="claude-3",
            api_key="test-key",
            temperature=0.5,
            max_tokens=1000,
            timeout=60
        )
        assert config.temperature == 0.5
        assert config.max_tokens == 1000
        assert config.timeout == 60
        assert config.api_key == "test-key"
    
    def test_model_config_api_key_excluded(self):
        """Test that API key is excluded from serialization."""
        config = ModelConfig(
            provider=ModelProvider.OPENAI,
            model_name="gpt-4",
            api_key="secret-key"
        )
        config_dict = config.model_dump()
        assert "api_key" not in config_dict
    
    def test_model_config_validation(self):
        """Test ModelConfig validation."""
        # Empty model name
        with pytest.raises(ValueError, match="Model name cannot be empty"):
            ModelConfig(provider=ModelProvider.OPENAI, model_name="")
        
        # Temperature out of range
        with pytest.raises(ValueError):
            ModelConfig(
                provider=ModelProvider.OPENAI,
                model_name="gpt-4",
                temperature=3.0
            )
        
        # Negative max_tokens
        with pytest.raises(ValueError):
            ModelConfig(
                provider=ModelProvider.OPENAI,
                model_name="gpt-4",
                max_tokens=-100
            )


class TestModelPane:
    """Test ModelPane model."""
    
    def test_model_pane_creation(self):
        """Test creating a model pane."""
        config = ModelConfig(
            provider=ModelProvider.OPENAI,
            model_name="gpt-4"
        )
        pane = ModelPane(position=0, config=config)
        assert pane.position == 0
        assert pane.config == config
        assert pane.status == PaneStatus.IDLE
        assert pane.current_response is None
        assert pane.last_error is None
        assert pane.is_focused is False
    
    def test_model_pane_reset(self):
        """Test resetting a model pane."""
        config = ModelConfig(
            provider=ModelProvider.OPENAI,
            model_name="gpt-4"
        )
        pane = ModelPane(position=0, config=config)
        
        # Set some state
        pane.status = PaneStatus.ERROR
        pane.current_response = "Some response"
        pane.last_error = "Some error"
        
        # Reset
        pane.reset()
        
        assert pane.status == PaneStatus.IDLE
        assert pane.current_response is None
        assert pane.last_error is None
    
    def test_model_pane_position_validation(self):
        """Test position validation."""
        config = ModelConfig(
            provider=ModelProvider.OPENAI,
            model_name="gpt-4"
        )
        
        # Valid positions
        for pos in range(5):
            pane = ModelPane(position=pos, config=config)
            assert pane.position == pos
        
        # Invalid positions
        with pytest.raises(ValueError):
            ModelPane(position=-1, config=config)
        
        with pytest.raises(ValueError):
            ModelPane(position=5, config=config)


class TestChatSession:
    """Test ChatSession model."""
    
    def test_chat_session_creation(self):
        """Test creating a chat session."""
        session = ChatSession()
        assert isinstance(session.id, UUID)
        assert session.title is None
        assert isinstance(session.created_at, datetime)
        assert isinstance(session.updated_at, datetime)
        assert session.messages == []
        assert session.model_panes == []
        assert session.active is True
        assert session.metadata == {}
    
    def test_add_message(self):
        """Test adding messages to session."""
        session = ChatSession()
        original_updated = session.updated_at
        
        msg1 = Message(role=MessageRole.USER, content="Hello")
        session.add_message(msg1)
        
        assert len(session.messages) == 1
        assert session.messages[0] == msg1
        assert session.updated_at > original_updated
    
    def test_get_messages_for_model(self):
        """Test filtering messages for a specific model."""
        session = ChatSession()
        
        # Add messages
        user_msg = Message(role=MessageRole.USER, content="Hello")
        system_msg = Message(role=MessageRole.SYSTEM, content="You are helpful")
        model1_msg = Message(
            role=MessageRole.ASSISTANT,
            content="Hi from model1",
            model_id="model1"
        )
        model2_msg = Message(
            role=MessageRole.ASSISTANT,
            content="Hi from model2",
            model_id="model2"
        )
        
        session.add_message(user_msg)
        session.add_message(system_msg)
        session.add_message(model1_msg)
        session.add_message(model2_msg)
        
        # Get messages for model1
        model1_messages = session.get_messages_for_model("model1")
        assert len(model1_messages) == 3  # user, system, model1
        assert user_msg in model1_messages
        assert system_msg in model1_messages
        assert model1_msg in model1_messages
        assert model2_msg not in model1_messages
    
    def test_clear_messages(self):
        """Test clearing messages."""
        session = ChatSession()
        
        # Add some messages
        session.add_message(Message(role=MessageRole.USER, content="Hello"))
        session.add_message(Message(role=MessageRole.ASSISTANT, content="Hi"))
        
        assert len(session.messages) == 2
        
        # Clear messages
        session.clear_messages()
        
        assert len(session.messages) == 0
        assert session.updated_at > session.created_at