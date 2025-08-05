"""Tests for UI grid layout component."""

import pytest

from chatmux.ui.grid import GridLayout
from chatmux.ui.pane import ModelPane


class TestGridLayout:
    """Test the GridLayout class."""

    def test_init(self):
        """Test grid initialization."""
        grid = GridLayout()
        assert grid.rows == 2
        assert grid.cols == 3
        assert grid.panes == []
        assert grid.focused_index == 0

    def test_custom_dimensions(self):
        """Test grid with custom dimensions."""
        grid = GridLayout(rows=3, cols=4)
        assert grid.rows == 3
        assert grid.cols == 4

    def test_add_pane(self):
        """Test adding panes to grid."""
        grid = GridLayout()

        # Add first pane
        pane1 = grid.add_pane("GPT-4", (0, 0))
        assert isinstance(pane1, ModelPane)
        assert pane1.model_name == "GPT-4"
        assert pane1.position == (0, 0)
        assert pane1.is_focused  # First pane gets focus
        assert len(grid.panes) == 1

        # Add second pane
        pane2 = grid.add_pane("Claude", (0, 1))
        assert pane2.model_name == "Claude"
        assert not pane2.is_focused
        assert len(grid.panes) == 2

    def test_add_pane_invalid_position(self):
        """Test adding pane at invalid position."""
        grid = GridLayout(rows=2, cols=3)

        # Position out of bounds
        with pytest.raises(ValueError, match="Invalid position"):
            grid.add_pane("GPT-4", (2, 0))  # Row out of bounds

        with pytest.raises(ValueError, match="Invalid position"):
            grid.add_pane("GPT-4", (0, 3))  # Col out of bounds

    def test_add_pane_occupied_position(self):
        """Test adding pane at occupied position."""
        grid = GridLayout()
        grid.add_pane("GPT-4", (0, 0))

        with pytest.raises(ValueError, match="already occupied"):
            grid.add_pane("Claude", (0, 0))

    def test_get_pane(self):
        """Test getting pane by position."""
        grid = GridLayout()
        pane = grid.add_pane("GPT-4", (0, 0))

        assert grid.get_pane((0, 0)) == pane
        assert grid.get_pane((1, 1)) is None

    def test_get_focused_pane(self):
        """Test getting focused pane."""
        grid = GridLayout()

        # No panes
        assert grid.get_focused_pane() is None

        # Add panes
        pane1 = grid.add_pane("GPT-4", (0, 0))
        grid.add_pane("Claude", (0, 1))

        assert grid.get_focused_pane() == pane1

    def test_focus_navigation(self):
        """Test focus navigation between panes."""
        grid = GridLayout()
        pane1 = grid.add_pane("GPT-4", (0, 0))
        pane2 = grid.add_pane("Claude", (0, 1))
        pane3 = grid.add_pane("Gemini", (0, 2))

        # Initial focus
        assert pane1.is_focused
        assert grid.focused_index == 0

        # Focus next
        grid.focus_next()
        assert not pane1.is_focused
        assert pane2.is_focused
        assert grid.focused_index == 1

        # Focus next (wrap around)
        grid.focus_next()
        grid.focus_next()
        assert pane1.is_focused
        assert grid.focused_index == 0

        # Focus previous
        grid.focus_previous()
        assert pane3.is_focused
        assert grid.focused_index == 2

    def test_focus_specific_pane(self):
        """Test focusing specific pane by index."""
        grid = GridLayout()
        pane1 = grid.add_pane("GPT-4", (0, 0))
        grid.add_pane("Claude", (0, 1))
        pane3 = grid.add_pane("Gemini", (0, 2))

        grid.focus_pane(2)
        assert pane3.is_focused
        assert not pane1.is_focused

        # Invalid index
        grid.focus_pane(10)  # Should not change focus
        assert pane3.is_focused

    def test_render(self):
        """Test rendering grid layout."""
        grid = GridLayout()
        grid.add_pane("GPT-4", (0, 0))
        grid.add_pane("Claude", (0, 1))

        # Should render without error
        layout = grid.render()
        assert layout is not None

    def test_handle_resize(self):
        """Test handling terminal resize."""
        grid = GridLayout()
        grid.add_pane("GPT-4", (0, 0))

        # Should handle resize without error
        grid.handle_resize()

    def test_empty_grid_render(self):
        """Test rendering empty grid."""
        grid = GridLayout()

        # Should render empty slots with input in bottom-right
        layout = grid.render()
        assert layout is not None

    def test_grid_with_input_panel(self):
        """Test that input panel is placed at bottom-right."""
        grid = GridLayout()

        # Add panes but leave bottom-right empty
        grid.add_pane("GPT-4", (0, 0))
        grid.add_pane("Claude", (0, 1))
        grid.add_pane("Gemini", (0, 2))
        grid.add_pane("Mistral", (1, 0))
        grid.add_pane("Llama", (1, 1))
        # (1, 2) should have input panel

        layout = grid.render()
        assert layout is not None
