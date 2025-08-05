"""Main application class for Chatmux."""

import asyncio
import signal
import sys
from contextlib import suppress
from typing import Any

from rich.console import Console
from rich.live import Live

from .config import config
from .coordinator import ResponseCoordinator, StreamUpdate
from .core.models import Message, MessageRole, ModelProvider
from .input_handler import InputHandler
from .ui.grid import GridLayout
from .ui.pane import ModelPane


class ChatmuxApp:
    """Main application class that orchestrates all components."""

    def __init__(self) -> None:
        """Initialize the Chatmux application."""
        self.console = Console()
        self.grid = GridLayout(config.grid_rows, config.grid_cols)
        self.input_handler = InputHandler(self.grid)
        self.coordinator = ResponseCoordinator(on_stream_update=self._handle_stream_update)
        self.conversation_history: list[Message] = []
        self.running = False
        self._live: Live | None = None
        self._setup_signal_handlers()

    def _setup_signal_handlers(self) -> None:
        """Set up signal handlers for graceful shutdown."""
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, self._signal_handler)

    def _signal_handler(self, signum: int, frame: Any) -> None:
        """Handle shutdown signals."""
        self.running = False
        if self._live:
            self._live.stop()
        sys.exit(0)

    def _setup_model_panes(self) -> None:
        """Set up model panes based on configuration."""
        # OpenAI models
        if config.openai_api_key and config.openai_model_1:
            pane = ModelPane(
                config.openai_model_1,
                (0, 0),
                provider=ModelProvider.OPENAI,
            )
            self.grid.add_pane(config.openai_model_1, (0, 0))
            self.grid.panes[0] = pane

        if config.openai_api_key and config.openai_model_2:
            pane = ModelPane(
                config.openai_model_2,
                (0, 1),
                provider=ModelProvider.OPENAI,
            )
            self.grid.add_pane(config.openai_model_2, (0, 1))
            self.grid.panes[1] = pane

        # Anthropic models (placeholder for now)
        if config.anthropic_api_key and config.anthropic_model_1:
            pane = ModelPane(
                config.anthropic_model_1,
                (0, 2),
                provider=ModelProvider.ANTHROPIC,
            )
            pane.set_content("Anthropic client not yet implemented")
            self.grid.add_pane(config.anthropic_model_1, (0, 2))
            self.grid.panes[2] = pane

        # Other providers (placeholders)
        if config.gemini_api_key and config.gemini_model:
            pane = ModelPane(
                config.gemini_model,
                (1, 0),
                provider=ModelProvider.GEMINI,
            )
            pane.set_content("Gemini client not yet implemented")
            self.grid.add_pane(config.gemini_model, (1, 0))
            self.grid.panes[3] = pane

        if config.mistral_api_key and config.mistral_model:
            pane = ModelPane(
                config.mistral_model,
                (1, 1),
                provider=ModelProvider.MISTRAL,
            )
            pane.set_content("Mistral client not yet implemented")
            self.grid.add_pane(config.mistral_model, (1, 1))
            self.grid.panes[4] = pane

    def _handle_stream_update(self, update: StreamUpdate) -> None:
        """Handle streaming updates from the coordinator."""
        # The grid automatically updates when pane content changes
        # This callback is for future enhancements like logging
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
            self.console.print("[yellow]No models available or matched[/yellow]")
            return

        # Send to models
        await self.coordinator.send_to_models(message, target_panes, self.conversation_history)

        # Store assistant responses in history
        # TODO: This should be done per model when we support multiple conversations
        # For now, we'll just store the first response
        for pane in target_panes:
            if pane.content:
                assistant_msg = Message(
                    role=MessageRole.ASSISTANT,
                    content=pane.content,
                )
                self.conversation_history.append(assistant_msg)
                break

    async def _process_keyboard_events(self) -> None:
        """Process keyboard events in the background."""
        import sys
        import termios
        import tty

        # Save terminal settings
        old_settings = termios.tcgetattr(sys.stdin)

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
                            # Let input handler process the key
                            handled = self.input_handler.handle_key(char)

                            # If it was Enter, process the input
                            if char in ("\r", "\n") and handled:
                                input_pane = self.input_handler.get_input_pane()
                                content = input_pane.state.current_text
                                targets = input_pane._parse_model_targets(content)
                                if content.strip():
                                    # Schedule coroutine in the event loop
                                    asyncio.create_task(self._handle_input(content, targets))
                                    input_pane.clear()

                        # Update display
                        if self._live:
                            self._live.update(self.grid.render())

                except BlockingIOError:
                    # No input available, sleep briefly
                    await asyncio.sleep(0.01)
                except Exception:
                    # Log error but continue
                    pass

        finally:
            # Restore terminal settings
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

    async def run(self) -> None:
        """Run the main application loop."""
        self.running = True

        # Set up model panes
        self._setup_model_panes()

        # Display welcome message
        self.console.print("\n[bold cyan]Welcome to Chatmux![/bold cyan]")
        self.console.print("Press ESC or Ctrl+C to quit")
        self.console.print("Type your message and press Enter to send to all models")
        self.console.print("Use @model to target specific models (e.g., @gpt-4)\n")

        # Start live display
        with Live(
            self.grid.render(),
            console=self.console,
            refresh_per_second=10,
            transient=False,
        ) as live:
            self._live = live

            try:
                # Process keyboard events
                await self._process_keyboard_events()
            except KeyboardInterrupt:
                pass
            finally:
                # Cancel any active tasks
                await self.coordinator.cancel_all()
                self._live = None

        self.console.print("\n[yellow]Goodbye![/yellow]")


async def main() -> None:
    """Main entry point for the application."""
    app = ChatmuxApp()
    await app.run()


if __name__ == "__main__":
    with suppress(KeyboardInterrupt):
        asyncio.run(main())
