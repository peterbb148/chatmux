"""Tests for UI pane component."""

from rich.panel import Panel

from chatmux.ui.pane import ModelPane
from chatmux.core.models import PaneStatus


class TestModelPane:
    """Test the ModelPane class."""

    def test_init(self):
        """Test pane initialization."""
        pane = ModelPane("GPT-4", (0, 0))
        assert pane.model_name == "GPT-4"
        assert pane.position == (0, 0)
        assert pane.status == PaneStatus.IDLE
        assert pane.content == ""
        assert not pane.is_focused
        assert pane.error_message is None

    def test_set_content(self):
        """Test setting content."""
        pane = ModelPane("GPT-4", (0, 0))
        pane.set_content("Hello world")
        assert pane.content == "Hello world"
        assert pane.status == PaneStatus.IDLE

    def test_append_content(self):
        """Test appending content for streaming."""
        pane = ModelPane("GPT-4", (0, 0))
        pane.append_content("Hello")
        assert pane.content == "Hello"
        assert pane.status == PaneStatus.STREAMING

        pane.append_content(" world")
        assert pane.content == "Hello world"
        assert pane.status == PaneStatus.STREAMING

    def test_set_error(self):
        """Test setting error state."""
        pane = ModelPane("GPT-4", (0, 0))
        pane.set_error("API error")
        assert pane.error_message == "API error"
        assert pane.status == PaneStatus.ERROR

    def test_clear(self):
        """Test clearing pane."""
        pane = ModelPane("GPT-4", (0, 0))
        pane.set_content("Some content")
        pane.set_error("Some error")

        pane.clear()
        assert pane.content == ""
        assert pane.error_message is None
        assert pane.status == PaneStatus.IDLE

    def test_focus(self):
        """Test focus state."""
        pane = ModelPane("GPT-4", (0, 0))
        assert not pane.is_focused

        pane.set_focused(True)
        assert pane.is_focused

        pane.set_focused(False)
        assert not pane.is_focused

    def test_render(self):
        """Test rendering as Rich Panel."""
        pane = ModelPane("GPT-4", (0, 0))
        panel = pane.render()
        assert isinstance(panel, Panel)
        assert "GPT-4" in panel.title

    def test_render_with_content(self):
        """Test rendering with content."""
        pane = ModelPane("GPT-4", (0, 0))
        pane.set_content("# Hello\nThis is **markdown**")
        panel = pane.render()
        assert isinstance(panel, Panel)

    def test_render_error_state(self):
        """Test rendering in error state."""
        pane = ModelPane("GPT-4", (0, 0))
        pane.set_error("Connection failed")
        panel = pane.render()
        assert isinstance(panel, Panel)
        assert "✗" in panel.title

    def test_render_streaming_state(self):
        """Test rendering in streaming state."""
        pane = ModelPane("GPT-4", (0, 0))
        pane.status = PaneStatus.STREAMING
        panel = pane.render()
        assert isinstance(panel, Panel)
        assert "◉" in panel.title

    def test_render_disabled_state(self):
        """Test rendering in disabled state."""
        pane = ModelPane("GPT-4", (0, 0))
        pane.status = PaneStatus.DISABLED
        panel = pane.render()
        assert isinstance(panel, Panel)
        assert "○" in panel.title

    def test_get_plain_content(self):
        """Test getting plain content."""
        pane = ModelPane("GPT-4", (0, 0))
        pane.set_content("# Hello\n**Bold** text")
        assert pane.get_plain_content() == "# Hello\n**Bold** text"

        pane.set_error("Test error")
        assert pane.get_plain_content() == "Error: Test error"

    def test_custom_dimensions(self):
        """Test pane with custom width/height."""
        pane = ModelPane("GPT-4", (0, 0), width=50, height=20)
        assert pane.width == 50
        assert pane.height == 20

        panel = pane.render()
        assert panel.width == 50
        assert panel.height == 20
