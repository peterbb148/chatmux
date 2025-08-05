"""Tests for the main application."""

from unittest.mock import patch

import pytest

from chatmux.app import ChatmuxApp
from chatmux.core.models import ModelProvider
from chatmux.ui.pane import ModelPane


class TestChatmuxApp:
    """Test the main ChatmuxApp class."""

    def test_init(self):
        """Test app initialization."""
        app = ChatmuxApp()

        assert app.console is not None
        assert app.grid is not None
        assert app.input_handler is not None
        assert app.coordinator is not None
        assert len(app.conversation_history) == 0
        assert app.running is False

    def test_setup_model_panes(self):
        """Test model pane setup."""
        app = ChatmuxApp()
        app._setup_model_panes()

        # Check that at least OpenAI panes are set up (we have API key in .env)
        panes = [p for p in app.grid.panes if isinstance(p, ModelPane)]
        assert len(panes) > 0

        # Check first pane is OpenAI
        first_pane = panes[0]
        assert first_pane.provider == ModelProvider.OPENAI
        assert first_pane.model_name in ["gpt-4", "gpt-3.5-turbo"]

    @pytest.mark.asyncio
    async def test_handle_input(self):
        """Test input handling."""
        app = ChatmuxApp()
        app._setup_model_panes()

        # Mock coordinator
        with patch.object(app.coordinator, "send_to_models") as mock_send:
            await app._handle_input("Hello world", [])

            # Check that send_to_models was called
            mock_send.assert_called_once()
            args = mock_send.call_args[0]
            assert args[0] == "Hello world"  # message
            assert len(args[1]) > 0  # target panes

        # Check conversation history has at least the user message
        assert len(app.conversation_history) >= 1
        assert app.conversation_history[0].content == "Hello world"

    @pytest.mark.asyncio
    async def test_handle_input_with_targets(self):
        """Test input handling with model targets."""
        app = ChatmuxApp()
        app._setup_model_panes()

        # Mock coordinator
        with patch.object(app.coordinator, "send_to_models") as mock_send:
            await app._handle_input("Hello GPT-4", ["gpt-4"])

            # Check that only GPT-4 pane was targeted
            args = mock_send.call_args[0]
            target_panes = args[1]
            assert all("gpt-4" in p.model_name.lower() for p in target_panes)

    def test_signal_handler(self):
        """Test signal handler sets running to False."""
        app = ChatmuxApp()
        app.running = True

        # Mock sys.exit
        with patch("sys.exit") as mock_exit:
            app._signal_handler(None, None)

            assert app.running is False
            mock_exit.assert_called_once_with(0)
