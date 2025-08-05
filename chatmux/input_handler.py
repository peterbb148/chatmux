"""Input handler for keyboard events and model coordination."""

import asyncio
from collections.abc import Awaitable, Callable

from rich.console import Console

from .ui.grid import GridLayout
from .ui.input_pane import InputPane


class InputHandler:
    """Handles keyboard input and coordinates between input pane and model panes."""

    def __init__(
        self,
        grid: GridLayout | None,
        send_to_models: Callable[[str, list[str]], Awaitable[None]] | None = None,
    ):
        """Initialize input handler.

        Args:
            grid: The grid layout containing model panes
            send_to_models: Callback to send messages to models
        """
        self.grid = grid
        self.send_to_models = send_to_models
        self.console = Console()

        # Create input pane with submit callback
        self.input_pane = InputPane(on_submit=self._handle_submit)

        # Track focus state
        self.input_has_focus = True

    def _handle_submit(self, text: str, target_models: list[str]) -> None:
        """Handle input submission.

        Args:
            text: The submitted text
            target_models: List of model names to target (empty = all)
        """
        if self.send_to_models:
            # Create async task for sending to models
            asyncio.create_task(self._send_to_models_async(text, target_models))

    async def _send_to_models_async(self, text: str, target_models: list[str]) -> None:
        """Send message to models asynchronously.

        Args:
            text: Message text
            target_models: Target model names (empty = all)
        """
        if self.send_to_models:
            await self.send_to_models(text, target_models)

    def handle_key(self, key: str) -> bool:
        """Handle keyboard input.

        Args:
            key: The key pressed

        Returns:
            True if key was handled, False otherwise
        """
        # Tab switches between input and model panes
        if key == "tab":
            self._toggle_focus()
            return True

        # If input has focus, handle input-specific keys
        if self.input_has_focus:
            return self._handle_input_key(key)

        # Otherwise, handle grid navigation
        return self._handle_grid_key(key)

    def _toggle_focus(self) -> None:
        """Toggle focus between input and grid."""
        self.input_has_focus = not self.input_has_focus
        self.input_pane.set_focused(self.input_has_focus)
        if self.grid:
            self.grid.update_display()

    def _handle_input_key(self, key: str) -> bool:
        """Handle key when input pane has focus.

        Args:
            key: The key pressed

        Returns:
            True if handled
        """
        # Special keys
        if key == "enter":
            self.input_pane.submit()
            return True
        elif key == "shift+enter":
            self.input_pane.add_character("\n")
            return True
        elif key == "up":
            self.input_pane.history_previous()
            return True
        elif key == "down":
            self.input_pane.history_next()
            return True
        elif key == "left":
            self.input_pane.move_cursor_left()
            return True
        elif key == "right":
            self.input_pane.move_cursor_right()
            return True
        elif key == "home":
            self.input_pane.move_cursor_home()
            return True
        elif key == "end":
            self.input_pane.move_cursor_end()
            return True
        elif key == "backspace":
            self.input_pane.delete_character()
            return True
        elif key == "delete":
            self.input_pane.delete_forward()
            return True
        elif key == "ctrl+u":
            self.input_pane.clear()
            return True
        elif len(key) == 1:
            # Regular character
            self.input_pane.add_character(key)
            return True

        return False

    def _handle_grid_key(self, key: str) -> bool:
        """Handle key when grid has focus.

        Args:
            key: The key pressed

        Returns:
            True if handled
        """
        if not self.grid:
            return False

        if key in ["left", "h"]:
            self.grid.focus_previous()
            return True
        elif key in ["right", "l"]:
            self.grid.focus_next()
            return True
        elif key.isdigit() and 1 <= int(key) <= 6:
            # Direct pane selection
            self.grid.focus_pane(int(key) - 1)
            return True

        return False

    def get_input_pane(self) -> InputPane:
        """Get the input pane for rendering."""
        return self.input_pane
