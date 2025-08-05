"""Input pane for handling user input and command parsing."""

from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field

from rich.panel import Panel
from rich.text import Text


@dataclass
class InputState:
    """State management for the input pane."""

    current_text: str = ""
    cursor_position: int = 0
    history: deque[str] = field(default_factory=lambda: deque(maxlen=100))
    history_index: int = -1
    temp_text: str = ""  # Store current text when navigating history


class InputPane:
    """Handles user input with history and model targeting."""

    def __init__(
        self,
        on_submit: Callable[[str, list[str]], None] | None = None,
        placeholder: str = "Type your message here...",
    ):
        """Initialize input pane.

        Args:
            on_submit: Callback when user submits input (text, target_models)
            placeholder: Placeholder text when input is empty
        """
        self.state = InputState()
        self.on_submit = on_submit
        self.placeholder = placeholder
        self.is_focused = True

    def add_character(self, char: str) -> None:
        """Add a character at cursor position."""
        text = self.state.current_text
        pos = self.state.cursor_position
        self.state.current_text = text[:pos] + char + text[pos:]
        self.state.cursor_position += 1

    def delete_character(self) -> None:
        """Delete character before cursor (backspace)."""
        if self.state.cursor_position > 0:
            text = self.state.current_text
            pos = self.state.cursor_position
            self.state.current_text = text[: pos - 1] + text[pos:]
            self.state.cursor_position -= 1

    def delete_forward(self) -> None:
        """Delete character after cursor (delete key)."""
        text = self.state.current_text
        pos = self.state.cursor_position
        if pos < len(text):
            self.state.current_text = text[:pos] + text[pos + 1 :]

    def move_cursor_left(self) -> None:
        """Move cursor one position left."""
        if self.state.cursor_position > 0:
            self.state.cursor_position -= 1

    def move_cursor_right(self) -> None:
        """Move cursor one position right."""
        if self.state.cursor_position < len(self.state.current_text):
            self.state.cursor_position += 1

    def move_cursor_home(self) -> None:
        """Move cursor to beginning of line."""
        self.state.cursor_position = 0

    def move_cursor_end(self) -> None:
        """Move cursor to end of line."""
        self.state.cursor_position = len(self.state.current_text)

    def history_previous(self) -> None:
        """Navigate to previous command in history."""
        if not self.state.history:
            return

        # Save current text on first history navigation
        if self.state.history_index == -1:
            self.state.temp_text = self.state.current_text

        # Move to previous item
        if self.state.history_index < len(self.state.history) - 1:
            self.state.history_index += 1
            self.state.current_text = self.state.history[
                -(self.state.history_index + 1)
            ]
            self.state.cursor_position = len(self.state.current_text)

    def history_next(self) -> None:
        """Navigate to next command in history."""
        if self.state.history_index > -1:
            self.state.history_index -= 1

            if self.state.history_index == -1:
                # Restore temp text
                self.state.current_text = self.state.temp_text
            else:
                self.state.current_text = self.state.history[
                    -(self.state.history_index + 1)
                ]

            self.state.cursor_position = len(self.state.current_text)

    def clear(self) -> None:
        """Clear current input."""
        self.state.current_text = ""
        self.state.cursor_position = 0
        self.state.history_index = -1
        self.state.temp_text = ""

    def submit(self) -> None:
        """Submit current input."""
        text = self.state.current_text.strip()
        if not text:
            return

        # Add to history
        self.state.history.append(text)

        # Parse for @model targets
        target_models = self._parse_model_targets(text)

        # Clear input
        self.clear()

        # Call submit callback
        if self.on_submit:
            self.on_submit(text, target_models)

    def _parse_model_targets(self, text: str) -> list[str]:
        """Parse @model targets from input text.

        Args:
            text: Input text to parse

        Returns:
            List of model names to target (empty list means all models)
        """
        targets = []
        words = text.split()

        for word in words:
            if word.startswith("@") and len(word) > 1:
                model_name = word[1:]
                targets.append(model_name)

        return targets

    def set_focused(self, focused: bool) -> None:
        """Set focus state."""
        self.is_focused = focused

    def render(self) -> Panel:
        """Render the input pane as a Rich panel."""
        # Create text with cursor
        text = Text()

        if self.state.current_text:
            # Add text before cursor
            if self.state.cursor_position > 0:
                text.append(self.state.current_text[: self.state.cursor_position])

            # Add cursor
            if self.is_focused:
                if self.state.cursor_position < len(self.state.current_text):
                    # Cursor on character
                    text.append(
                        self.state.current_text[self.state.cursor_position],
                        style="reverse",
                    )
                    # Add remaining text
                    if self.state.cursor_position + 1 < len(self.state.current_text):
                        text.append(
                            self.state.current_text[self.state.cursor_position + 1 :]
                        )
                else:
                    # Cursor at end
                    text.append("█", style="reverse")
            else:
                # Not focused, just show remaining text
                if self.state.cursor_position < len(self.state.current_text):
                    text.append(self.state.current_text[self.state.cursor_position :])
        else:
            # Empty input
            if self.is_focused:
                text.append("█", style="reverse")
            else:
                text.append(self.placeholder, style="dim italic")

        # Create hints text
        hints = (
            "[dim]Enter: Send | Shift+Enter: Newline | "
            "↑/↓: History | @model: Target specific model[/dim]"
        )

        # Create panel
        return Panel(
            text,
            title="[bold]Input[/bold]" + (" [yellow]●[/yellow]" if self.is_focused else ""),
            subtitle=hints,
            border_style="bright_blue" if self.is_focused else "dim white",
            expand=True,
        )
