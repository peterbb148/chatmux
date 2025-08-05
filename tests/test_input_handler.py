"""Tests for input handler functionality."""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from chatmux.input_handler import InputHandler
from chatmux.ui.grid import GridLayout


@pytest.fixture
def grid():
    """Create a mock grid layout."""
    grid = Mock(spec=GridLayout)
    grid.update_display = Mock()
    grid.focus_next = Mock()
    grid.focus_previous = Mock()
    grid.focus_pane = Mock()
    return grid


@pytest.fixture
def handler(grid):
    """Create an input handler with mock grid."""
    return InputHandler(grid)


class TestInputHandler:
    """Test InputHandler functionality."""

    def test_init(self, grid):
        """Test input handler initialization."""
        send_callback = Mock()
        handler = InputHandler(grid, send_to_models=send_callback)

        assert handler.grid == grid
        assert handler.send_to_models == send_callback
        assert handler.input_has_focus is True
        assert handler.input_pane is not None

    def test_toggle_focus(self, handler, grid):
        """Test focus toggling."""
        assert handler.input_has_focus is True

        # Toggle to grid
        handler._toggle_focus()
        assert handler.input_has_focus is False
        assert handler.input_pane.is_focused is False
        grid.update_display.assert_called_once()

        # Toggle back to input
        grid.update_display.reset_mock()
        handler._toggle_focus()
        assert handler.input_has_focus is True
        assert handler.input_pane.is_focused is True
        grid.update_display.assert_called_once()

    def test_handle_key_tab(self, handler):
        """Test tab key handling."""
        assert handler.input_has_focus is True

        # Tab switches focus
        result = handler.handle_key("tab")
        assert result is True
        assert handler.input_has_focus is False

    def test_handle_input_keys(self, handler):
        """Test key handling when input has focus."""
        # Regular character
        result = handler.handle_key("a")
        assert result is True
        assert handler.input_pane.state.current_text == "a"

        # Enter key
        handler.input_pane.state.current_text = "test"
        with patch.object(handler.input_pane, "submit") as mock_submit:
            result = handler.handle_key("enter")
            assert result is True
            mock_submit.assert_called_once()

        # Navigation keys
        handler.input_pane.state.current_text = "hello"
        handler.input_pane.state.cursor_position = 5

        result = handler.handle_key("left")
        assert result is True
        assert handler.input_pane.state.cursor_position == 4

        result = handler.handle_key("right")
        assert result is True
        assert handler.input_pane.state.cursor_position == 5

        result = handler.handle_key("home")
        assert result is True
        assert handler.input_pane.state.cursor_position == 0

        result = handler.handle_key("end")
        assert result is True
        assert handler.input_pane.state.cursor_position == 5

        # History navigation
        handler.input_pane.state.history.append("previous")
        result = handler.handle_key("up")
        assert result is True
        assert handler.input_pane.state.current_text == "previous"

        result = handler.handle_key("down")
        assert result is True
        assert handler.input_pane.state.current_text == "hello"

        # Delete keys
        handler.input_pane.state.current_text = "test"
        handler.input_pane.state.cursor_position = 4
        result = handler.handle_key("backspace")
        assert result is True
        assert handler.input_pane.state.current_text == "tes"

        handler.input_pane.state.cursor_position = 0
        result = handler.handle_key("delete")
        assert result is True
        assert handler.input_pane.state.current_text == "es"

        # Clear
        result = handler.handle_key("ctrl+u")
        assert result is True
        assert handler.input_pane.state.current_text == ""

        # Shift+Enter for newline
        result = handler.handle_key("shift+enter")
        assert result is True
        assert handler.input_pane.state.current_text == "\n"

    def test_handle_grid_keys(self, handler, grid):
        """Test key handling when grid has focus."""
        # Switch focus to grid
        handler.input_has_focus = False

        # Navigation keys
        result = handler.handle_key("left")
        assert result is True
        grid.focus_previous.assert_called_once()

        grid.focus_next.reset_mock()
        result = handler.handle_key("right")
        assert result is True
        grid.focus_next.assert_called_once()

        # Vim-style navigation
        grid.focus_previous.reset_mock()
        result = handler.handle_key("h")
        assert result is True
        grid.focus_previous.assert_called_once()

        grid.focus_next.reset_mock()
        result = handler.handle_key("l")
        assert result is True
        grid.focus_next.assert_called_once()

        # Direct pane selection
        result = handler.handle_key("3")
        assert result is True
        grid.focus_pane.assert_called_with(2)  # 0-indexed

        # Invalid number
        result = handler.handle_key("9")
        assert result is False

        # Non-number
        result = handler.handle_key("x")
        assert result is False

    @pytest.mark.asyncio
    async def test_handle_submit(self, grid):
        """Test submit handling with async callback."""
        # Create mock async callback
        send_callback = AsyncMock()
        handler = InputHandler(grid, send_to_models=send_callback)

        # Submit some text
        handler._handle_submit("Hello world", ["gpt4"])

        # Give async task time to run
        await asyncio.sleep(0.1)

        # Check callback was called
        send_callback.assert_called_once_with("Hello world", ["gpt4"])

    def test_get_input_pane(self, handler):
        """Test getting input pane."""
        pane = handler.get_input_pane()
        assert pane == handler.input_pane
