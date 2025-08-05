"""Tests for input pane functionality."""

from unittest.mock import Mock

import pytest

from chatmux.ui.input_pane import InputPane, InputState


class TestInputState:
    """Test InputState data class."""

    def test_default_values(self):
        """Test default state values."""
        state = InputState()
        assert state.current_text == ""
        assert state.cursor_position == 0
        assert len(state.history) == 0
        assert state.history_index == -1
        assert state.temp_text == ""


class TestInputPane:
    """Test InputPane functionality."""

    def test_init(self):
        """Test input pane initialization."""
        callback = Mock()
        pane = InputPane(on_submit=callback, placeholder="Test placeholder")

        assert pane.on_submit == callback
        assert pane.placeholder == "Test placeholder"
        assert pane.is_focused is True
        assert isinstance(pane.state, InputState)

    def test_add_character(self):
        """Test adding characters."""
        pane = InputPane()

        # Add characters
        pane.add_character("H")
        pane.add_character("i")
        assert pane.state.current_text == "Hi"
        assert pane.state.cursor_position == 2

        # Add character in middle
        pane.state.cursor_position = 1
        pane.add_character("e")
        assert pane.state.current_text == "Hei"
        assert pane.state.cursor_position == 2

    def test_delete_character(self):
        """Test backspace functionality."""
        pane = InputPane()
        pane.state.current_text = "Hello"
        pane.state.cursor_position = 5

        # Delete from end
        pane.delete_character()
        assert pane.state.current_text == "Hell"
        assert pane.state.cursor_position == 4

        # Delete from middle
        pane.state.cursor_position = 2
        pane.delete_character()
        assert pane.state.current_text == "Hll"
        assert pane.state.cursor_position == 1

        # Try to delete at beginning (should do nothing)
        pane.state.cursor_position = 0
        pane.delete_character()
        assert pane.state.current_text == "Hll"
        assert pane.state.cursor_position == 0

    def test_delete_forward(self):
        """Test delete key functionality."""
        pane = InputPane()
        pane.state.current_text = "Hello"
        pane.state.cursor_position = 0

        # Delete from beginning
        pane.delete_forward()
        assert pane.state.current_text == "ello"
        assert pane.state.cursor_position == 0

        # Delete from middle
        pane.state.cursor_position = 2
        pane.delete_forward()
        assert pane.state.current_text == "elo"
        assert pane.state.cursor_position == 2

        # Try to delete at end (should do nothing)
        pane.state.cursor_position = 3
        pane.delete_forward()
        assert pane.state.current_text == "elo"
        assert pane.state.cursor_position == 3

    def test_cursor_movement(self):
        """Test cursor movement methods."""
        pane = InputPane()
        pane.state.current_text = "Hello World"
        pane.state.cursor_position = 5

        # Move left
        pane.move_cursor_left()
        assert pane.state.cursor_position == 4

        # Move right
        pane.move_cursor_right()
        pane.move_cursor_right()
        assert pane.state.cursor_position == 6

        # Move to home
        pane.move_cursor_home()
        assert pane.state.cursor_position == 0

        # Move to end
        pane.move_cursor_end()
        assert pane.state.cursor_position == 11

        # Try to move beyond boundaries
        pane.move_cursor_right()
        assert pane.state.cursor_position == 11

        pane.move_cursor_home()
        pane.move_cursor_left()
        assert pane.state.cursor_position == 0

    def test_history_navigation(self):
        """Test command history navigation."""
        pane = InputPane()

        # Add some history
        pane.state.history.extend(["first", "second", "third"])
        pane.state.current_text = "current"

        # Navigate to previous (most recent)
        pane.history_previous()
        assert pane.state.current_text == "third"
        assert pane.state.history_index == 0
        assert pane.state.temp_text == "current"

        # Continue navigating
        pane.history_previous()
        assert pane.state.current_text == "second"
        assert pane.state.history_index == 1

        pane.history_previous()
        assert pane.state.current_text == "first"
        assert pane.state.history_index == 2

        # Try to go beyond history
        pane.history_previous()
        assert pane.state.current_text == "first"
        assert pane.state.history_index == 2

        # Navigate forward
        pane.history_next()
        assert pane.state.current_text == "second"
        assert pane.state.history_index == 1

        # Return to current
        pane.history_next()
        pane.history_next()
        assert pane.state.current_text == "current"
        assert pane.state.history_index == -1

    def test_clear(self):
        """Test clearing input."""
        pane = InputPane()
        pane.state.current_text = "Hello"
        pane.state.cursor_position = 3
        pane.state.history_index = 1
        pane.state.temp_text = "temp"

        pane.clear()

        assert pane.state.current_text == ""
        assert pane.state.cursor_position == 0
        assert pane.state.history_index == -1
        assert pane.state.temp_text == ""

    def test_submit(self):
        """Test input submission."""
        callback = Mock()
        pane = InputPane(on_submit=callback)

        # Submit empty (should do nothing)
        pane.submit()
        callback.assert_not_called()

        # Submit with text
        pane.state.current_text = "Hello world"
        pane.submit()

        callback.assert_called_once_with("Hello world", [])
        assert pane.state.current_text == ""
        assert "Hello world" in pane.state.history

        # Submit with model targets
        callback.reset_mock()
        pane.state.current_text = "@gpt4 @claude Hello"
        pane.submit()

        callback.assert_called_once_with("@gpt4 @claude Hello", ["gpt4", "claude"])

    def test_parse_model_targets(self):
        """Test model target parsing."""
        pane = InputPane()

        # No targets
        assert pane._parse_model_targets("Hello world") == []

        # Single target
        assert pane._parse_model_targets("@gpt4 Hello") == ["gpt4"]

        # Multiple targets
        assert pane._parse_model_targets("@gpt4 @claude test") == ["gpt4", "claude"]

        # Target at end
        assert pane._parse_model_targets("Hello @claude") == ["claude"]

        # Invalid targets
        assert pane._parse_model_targets("@ test @") == []

        # Mixed valid and invalid
        assert pane._parse_model_targets("@valid @ @another") == ["valid", "another"]

    def test_focus(self):
        """Test focus state management."""
        pane = InputPane()

        assert pane.is_focused is True

        pane.set_focused(False)
        assert pane.is_focused is False

        pane.set_focused(True)
        assert pane.is_focused is True

    def test_render(self):
        """Test rendering."""
        pane = InputPane()

        # Test empty render
        panel = pane.render()
        assert panel.title == "[bold]Input[/bold] [yellow]●[/yellow]"
        assert panel.border_style == "bright_blue"

        # Test with text
        pane.state.current_text = "Hello"
        panel = pane.render()
        # Should have text content

        # Test unfocused
        pane.set_focused(False)
        panel = pane.render()
        assert panel.title == "[bold]Input[/bold]"
        assert panel.border_style == "dim white"

    def test_multiline_input(self):
        """Test multiline input handling."""
        pane = InputPane()

        pane.add_character("L")
        pane.add_character("i")
        pane.add_character("n")
        pane.add_character("e")
        pane.add_character("1")
        pane.add_character("\n")
        pane.add_character("L")
        pane.add_character("i")
        pane.add_character("n")
        pane.add_character("e")
        pane.add_character("2")

        assert pane.state.current_text == "Line1\nLine2"
        assert pane.state.cursor_position == 11