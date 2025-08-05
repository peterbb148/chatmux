"""Model pane component for displaying AI model responses."""

from enum import Enum
from uuid import uuid4

from rich.console import RenderableType
from rich.markdown import Markdown
from rich.panel import Panel
from rich.style import Style

from ..core.models import ModelProvider


class PaneStatus(Enum):
    """Status of a model pane."""

    IDLE = "idle"
    STREAMING = "streaming"
    ERROR = "error"
    DISABLED = "disabled"
    COMPLETE = "complete"
    RATE_LIMITED = "rate_limited"
    CANCELLED = "cancelled"


class ModelPane:
    """A pane that displays responses from a single AI model."""

    def __init__(
        self,
        model_name: str,
        position: tuple[int, int],
        provider: ModelProvider | None = None,
        width: int | None = None,
        height: int | None = None,
    ):
        """Initialize a model pane.

        Args:
            model_name: Name of the model (e.g., "GPT-4", "Claude 3")
            position: Grid position as (row, col)
            provider: Model provider (optional, will be inferred from model_name)
            width: Optional fixed width
            height: Optional fixed height
        """
        self.pane_id = str(uuid4())
        self.model_name = model_name
        self.position = position
        self.width = width
        self.height = height
        self.status = PaneStatus.IDLE
        self.content: str = ""
        self.is_focused = False
        self.error_message: str | None = None

        # Infer provider from model name if not provided
        if provider:
            self.provider = provider
        else:
            self.provider = self._infer_provider(model_name)

    def set_content(self, content: str) -> None:
        """Set the pane's content."""
        self.content = content
        self.status = PaneStatus.IDLE

    def append_content(self, chunk: str) -> None:
        """Append content chunk (for streaming)."""
        self.content += chunk
        self.status = PaneStatus.STREAMING

    def set_error(self, error: str) -> None:
        """Set error state with message."""
        self.error_message = error
        self.status = PaneStatus.ERROR

    def clear(self) -> None:
        """Clear the pane content."""
        self.content = ""
        self.error_message = None
        self.status = PaneStatus.IDLE

    def set_focused(self, focused: bool) -> None:
        """Set focus state."""
        self.is_focused = focused

    def render(self) -> Panel:
        """Render the pane as a Rich Panel.

        Returns:
            Rich Panel with formatted content
        """
        # Determine border style based on status and focus
        border_style = self._get_border_style()

        # Render content based on status
        content = self._render_content()

        # Create panel with title showing model name and status
        title = self._get_title()

        return Panel(
            content,
            title=title,
            border_style=border_style,
            width=self.width,
            height=self.height,
            expand=True,
        )

    def _get_border_style(self) -> Style:
        """Get border style based on pane state."""
        if self.is_focused:
            return Style(color="bright_cyan", bold=True)

        style_map = {
            PaneStatus.IDLE: Style(color="green"),
            PaneStatus.STREAMING: Style(color="yellow"),
            PaneStatus.ERROR: Style(color="red"),
            PaneStatus.DISABLED: Style(color="white", dim=True),
            PaneStatus.COMPLETE: Style(color="bright_green"),
            PaneStatus.RATE_LIMITED: Style(color="orange3"),
            PaneStatus.CANCELLED: Style(color="magenta"),
        }
        return style_map.get(self.status, Style())

    def _get_title(self) -> str:
        """Get panel title with model name and status indicator."""
        status_symbols = {
            PaneStatus.IDLE: "✓",
            PaneStatus.STREAMING: "◉",
            PaneStatus.ERROR: "✗",
            PaneStatus.DISABLED: "○",
            PaneStatus.COMPLETE: "✓",
            PaneStatus.RATE_LIMITED: "⏳",
            PaneStatus.CANCELLED: "⊗",
        }
        symbol = status_symbols.get(self.status, "")
        return f"[bold]{self.model_name}[/bold] {symbol}"

    def _render_content(self) -> RenderableType:
        """Render the pane content based on status."""
        if self.status == PaneStatus.ERROR and self.error_message:
            return f"[red]Error: {self.error_message}[/red]"

        if self.status == PaneStatus.DISABLED:
            return "[dim]Model disabled[/dim]"

        if not self.content:
            return "[dim italic]Waiting for response...[/dim italic]"

        # Render markdown content
        return Markdown(self.content)

    def get_plain_content(self) -> str:
        """Get plain text content without formatting.

        Returns:
            Plain text content for copying to clipboard
        """
        if self.status == PaneStatus.ERROR and self.error_message:
            return f"Error: {self.error_message}"
        return self.content

    def set_status(self, status: PaneStatus) -> None:
        """Set the pane status."""
        self.status = status

    def clear_content(self) -> None:
        """Clear the pane content (alias for clear)."""
        self.clear()

    def _infer_provider(self, model_name: str) -> ModelProvider:
        """Infer provider from model name.

        Args:
            model_name: The model name

        Returns:
            Inferred provider
        """
        model_lower = model_name.lower()
        if "gpt" in model_lower or "openai" in model_lower:
            return ModelProvider.OPENAI
        elif "claude" in model_lower or "anthropic" in model_lower:
            return ModelProvider.ANTHROPIC
        elif "gemini" in model_lower or "google" in model_lower:
            return ModelProvider.GEMINI
        elif "mistral" in model_lower:
            return ModelProvider.MISTRAL
        elif "llama" in model_lower or "ollama" in model_lower:
            return ModelProvider.OLLAMA
        else:
            # Default to OpenAI if can't infer
            return ModelProvider.OPENAI
