"""Main application class for Chatmux."""

import asyncio
import signal
import sys
from contextlib import suppress
from typing import Any

from rich.console import Console

# Handle both direct execution and module import
try:
    from .config import config
    from .coordinator import ResponseCoordinator, StreamUpdate
    from .core.models import Message, MessageRole, ModelProvider
    from .input_handler import InputHandler
    from .ui.grid import GridLayout
    from .ui.pane import ModelPane
except ImportError:
    # Direct execution - add parent directory to path
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent.parent))

    from chatmux.config import config
    from chatmux.coordinator import ResponseCoordinator, StreamUpdate
    from chatmux.core.models import Message, MessageRole, ModelProvider
    from chatmux.input_handler import InputHandler
    from chatmux.ui.grid import GridLayout
    from chatmux.ui.pane import ModelPane


class ChatmuxApp:
    """Main application class that orchestrates all components."""

    def __init__(self) -> None:
        """Initialize the Chatmux application."""
        self.console = Console()

        # Create input handler first to get the input pane
        self.input_handler = InputHandler(None)  # We'll set grid later
        input_pane = self.input_handler.get_input_pane()

        # Create grid with input pane
        self.grid = GridLayout(config.grid_rows, config.grid_cols, input_pane)

        # Now set the grid reference in input handler
        self.input_handler.grid = self.grid

        self.coordinator = ResponseCoordinator(on_stream_update=self._handle_stream_update)
        self.conversation_history: list[Message] = []
        self.running = False
        self._setup_signal_handlers()

    def _setup_signal_handlers(self) -> None:
        """Set up signal handlers for graceful shutdown."""
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, self._signal_handler)

    def _signal_handler(self, signum: int, frame: Any) -> None:
        """Handle shutdown signals."""
        self.running = False
        sys.exit(0)

    def _setup_model_panes(self) -> None:
        """Set up model panes based on configuration."""
        # OpenAI models
        if config.openai_api_key and config.openai_model_1:
            pane = self.grid.add_pane(config.openai_model_1, (0, 0))
            pane.provider = ModelProvider.OPENAI

        if config.openai_api_key and config.openai_model_2:
            pane = self.grid.add_pane(config.openai_model_2, (0, 1))
            pane.provider = ModelProvider.OPENAI

        # Anthropic models (placeholder for now)
        if config.anthropic_api_key and config.anthropic_model_1:
            pane = self.grid.add_pane(config.anthropic_model_1, (0, 2))
            pane.provider = ModelProvider.ANTHROPIC
            pane.set_content("Anthropic client not yet implemented")

        # Other providers (placeholders)
        if config.gemini_api_key and config.gemini_model:
            pane = self.grid.add_pane(config.gemini_model, (1, 0))
            pane.provider = ModelProvider.GEMINI
            pane.set_content("Gemini client not yet implemented")

        if config.mistral_api_key and config.mistral_model:
            pane = self.grid.add_pane(config.mistral_model, (1, 1))
            pane.provider = ModelProvider.MISTRAL
            pane.set_content("Mistral client not yet implemented")

    def _handle_stream_update(self, update: StreamUpdate) -> None:
        """Handle streaming updates from the coordinator."""
        # The grid automatically updates when pane content changes
        # This callback is for future enhancements like logging
        pass

    def _translate_char_to_key(self, char: str) -> str:
        """Translate raw character to key name expected by input handler."""
        if char == "\r" or char == "\n":
            return "enter"
        elif char == "\x08" or char == "\x7f":  # Backspace or DEL
            return "backspace"
        elif char == "\t":
            return "tab"
        elif ord(char) == 21:  # Ctrl+U
            return "ctrl+u"
        elif len(char) == 1 and char.isprintable():
            return char
        else:
            # For other special characters, just return as-is
            return char

    def _update_display_if_needed(self) -> None:
        """Update display intelligently when input content changes."""
        # Disable real-time display updates to prevent scrolling and corruption
        # The input pane within the grid shows typing feedback automatically
        # Users can see what they're typing in the bottom-right input pane
        pass

    async def _handle_input(self, message: str, target_models: list[str]) -> None:
        """Handle user input and send to models."""
        # Add user message to history
        user_msg = Message(role=MessageRole.USER, content=message)
        self.conversation_history.append(user_msg)

        # Get target panes
        if target_models:
            # Filter panes by model names
            target_panes = [
                pane
                for pane in self.grid.panes
                if isinstance(pane, ModelPane)
                and pane.model_name
                and any(target.lower() in pane.model_name.lower() for target in target_models)
            ]
        else:
            # Send to all enabled panes
            target_panes = [
                pane for pane in self.grid.panes if isinstance(pane, ModelPane) and pane.model_name
            ]

        if not target_panes:
            # No models available - could show error in input pane if needed
            return

        # Update panes to show "thinking" state and refresh display
        for pane in target_panes:
            pane.set_content(f"💭 Thinking about: {message[:30]}...")

        # The "thinking" state will be visible in the panes automatically

        # Send to models (placeholder - actual model calls would happen here)
        await self._simulate_model_responses(message, target_panes)

        # Store assistant responses in history
        for pane in target_panes:
            if pane.content and not pane.content.startswith("💭"):
                assistant_msg = Message(
                    role=MessageRole.ASSISTANT,
                    content=pane.content,
                )
                self.conversation_history.append(assistant_msg)
                break  # Just store first response for now

    async def _simulate_model_responses(self, message: str, target_panes: list) -> None:
        """Simulate model responses (placeholder until real integration)."""
        import asyncio

        for i, pane in enumerate(target_panes):
            # Simulate different response times
            await asyncio.sleep(0.5 + i * 0.3)

            # Generate a placeholder response
            response = (
                f"[Response to: '{message[:20]}...']\n\n"
                f"This is a simulated response from {pane.model_name}. "
                "In the real implementation, this would be the actual AI model response."
            )

            pane.set_content(response)

            # Response will be visible in the pane automatically

    async def _process_keyboard_events(self) -> None:
        """Process keyboard events in the background."""
        import sys
        import termios
        import tty

        # Check if stdin is a terminal
        if not sys.stdin.isatty():
            self.console.print(
                "[yellow]Not running in a terminal, keyboard input disabled[/yellow]"
            )
            # Just wait until running is False
            while self.running:
                await asyncio.sleep(0.1)
            return

        # Save terminal settings
        try:
            old_settings = termios.tcgetattr(sys.stdin)
        except termios.error as e:
            self.console.print(f"[red]Terminal setup error: {e}[/red]")
            # Fall back to simple input mode
            while self.running:
                await asyncio.sleep(0.1)
            return

        try:
            # Set terminal to raw mode
            tty.setraw(sys.stdin.fileno())

            # Make stdin non-blocking
            import fcntl
            import os

            flags = fcntl.fcntl(sys.stdin.fileno(), fcntl.F_GETFL)
            fcntl.fcntl(sys.stdin.fileno(), fcntl.F_SETFL, flags | os.O_NONBLOCK)

            while self.running:
                try:
                    # Try to read a character
                    char = sys.stdin.read(1)
                    if char:
                        # Handle special characters
                        if char == "\x1b":  # ESC
                            self.running = False
                            break
                        elif char == "\x03":  # Ctrl+C
                            self.running = False
                            break
                        else:
                            # Translate raw characters to key names for input handler
                            key_name = self._translate_char_to_key(char)

                            # Special handling for Enter key
                            if char in ("\r", "\n"):
                                # Get content BEFORE processing Enter
                                input_pane = self.input_handler.get_input_pane()
                                content = input_pane.state.current_text.strip()

                                # Process the content
                                if content:
                                    targets = input_pane._parse_model_targets(content)
                                    # Schedule coroutine in the event loop
                                    asyncio.create_task(self._handle_input(content, targets))
                                    # Clear the input pane manually
                                    input_pane.clear()

                            else:
                                # For non-Enter keys, use normal input handler processing
                                self.input_handler.handle_key(key_name)

                                # Input pane within the grid shows typing automatically
                                # No additional display updates needed to avoid scrolling

                except BlockingIOError:
                    # No input available, sleep briefly
                    await asyncio.sleep(0.01)
                except Exception:
                    # Log error but continue silently to avoid display corruption
                    pass

        finally:
            # Restore terminal settings
            try:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
            except (termios.error, OSError):
                # Terminal may have been closed or changed
                pass

    async def run(self) -> None:
        """Run the main application loop."""
        self.running = True

        # Set up model panes
        self._setup_model_panes()

        # Display compact welcome message
        self.console.print(
            "[bold cyan]Chatmux[/bold cyan] | ESC/Ctrl+C: quit | Enter: send | @model: target"
        )

        # Use simple display update instead of Live for Warp compatibility
        try:
            # Initial render - print without extra newline
            self.console.print(self.grid.render(), end="")

            # Process keyboard events without Live display
            try:
                await self._process_keyboard_events()
            except KeyboardInterrupt:
                pass
            finally:
                # Cancel any active tasks
                await self.coordinator.cancel_all()
        except (BlockingIOError, BrokenPipeError):
            # Handle terminal output issues gracefully
            pass

        try:
            self.console.print("\n[yellow]Goodbye![/yellow]")
        except (BlockingIOError, BrokenPipeError):
            # Terminal may have been closed
            pass


async def main() -> None:
    """Main entry point for the application."""
    app = ChatmuxApp()
    await app.run()


if __name__ == "__main__":
    with suppress(KeyboardInterrupt):
        asyncio.run(main())
