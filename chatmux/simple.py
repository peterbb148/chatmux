"""
Simple, working version of chatmux with Ctrl+D to send messages.
This avoids the Cmd+Enter issues with TextArea.
"""

import asyncio
from typing import Any

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Grid, Vertical
from textual.widgets import Footer, Header, Static, TextArea

try:
    import pyperclip
except ImportError:
    pyperclip = None

try:
    from .config import config
    from .coordinator import ResponseCoordinator, StreamUpdate
    from .core.models import Message, MessageRole, ModelConfig, ModelProvider
except ImportError:
    # Handle direct execution
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent.parent))
    from chatmux.config import config
    from chatmux.coordinator import ResponseCoordinator, StreamUpdate
    from chatmux.core.models import Message, MessageRole, ModelConfig, ModelProvider


class ModelPane(Static):
    """A model pane showing model status and responses."""

    can_focus = True
    DEFAULT_CSS = """
    ModelPane {
        layout: vertical;
        overflow-x: hidden;
        overflow-y: hidden;
    }
    """

    def __init__(
        self, model_name: str, provider: ModelProvider, pane_id: str, **kwargs: Any
    ) -> None:
        super().__init__(**kwargs)
        self.model_name = model_name
        self.provider = provider
        self.pane_id = pane_id
        self.border = True
        self._accumulated_content = ""  # Store accumulated content for streaming

    def compose(self) -> ComposeResult:
        yield Static(f"🤖 {self.model_name}", id="title", classes="pane-title")
        yield TextArea(
            id="content", classes="pane-content", read_only=True, show_line_numbers=False
        )

    def on_mount(self) -> None:
        self.border_title = self.model_name
        self.border_subtitle = f"[{self.provider.value}]"
        # Set initial message
        content_widget = self.query_one("#content", TextArea)
        content_widget.load_text("Waiting for input...")

    def update_content(self, content: str) -> None:
        """Update the model's response content."""
        content_widget = self.query_one("#content", TextArea)
        content_widget.load_text(content)

    def set_thinking(self, message: str) -> None:
        """Show thinking state."""
        self._accumulated_content = ""  # Clear accumulated content for new message
        content_widget = self.query_one("#content", TextArea)
        content_widget.load_text(f"💭 Processing: {message[:50]}...")
        self.border_subtitle = "[Thinking...]"

    def set_error(self, error: str) -> None:
        """Show error state."""
        self._accumulated_content = f"❌ Error: {error}"
        self.update_content(self._accumulated_content)
        self.border_subtitle = "[Error]"


class ChatmuxTextualApp(App):
    """Textual-based Chatmux application."""

    CSS = """
    Vertical {
        height: 100%;
    }

    #model-grid {
        grid-size: 2 3;
        grid-gutter: 1 1;
        height: 1fr;
        padding: 1;
    }

    .model-pane {
        border: solid $primary;
        height: 100%;
        layout: vertical;
    }

    .model-pane:focus {
        border: thick $accent;
    }

    #main-input {
        dock: bottom;
        height: 5;
        margin: 0 1 1 1;
    }

    .pane-title {
        text-style: bold;
        background: $primary 20%;
        height: 3;
        padding: 0 1;
        dock: top;
    }

    .pane-content {
        padding: 1;
        height: 1fr;
    }
    """

    BINDINGS = [
        Binding("escape", "quit", "Quit"),
        Binding("ctrl+c", "quit", "Quit"),
        Binding("tab", "focus_next", "Next pane", show=False),
        Binding("shift+tab", "focus_previous", "Previous pane", show=False),
        Binding("ctrl+y", "copy_focused", "Copy focused pane"),
        Binding("ctrl+d", "send_message", "Send message"),  # Like terminal EOF
    ]

    def __init__(self) -> None:
        super().__init__()
        self.coordinator = ResponseCoordinator(on_stream_update=self._handle_stream_update)
        self.conversation_history: list[Message] = []
        self.model_panes: dict[str, ModelPane] = {}

    def compose(self) -> ComposeResult:
        yield Header()

        # Main container with vertical layout
        with Vertical():
            # Grid for model panes (takes up most space)
            with Grid(id="model-grid"):
                # Create model panes based on configuration
                # Top row
                if config.openai_api_key and config.openai_model_1:
                    pane = ModelPane(
                        config.openai_model_1,
                        ModelProvider.OPENAI,
                        "openai_1",
                        classes="model-pane",
                    )
                    self.model_panes["openai_1"] = pane
                    yield pane
                else:
                    yield Static("No OpenAI Model 1", classes="model-pane")

                if config.openai_api_key and config.openai_model_2:
                    pane = ModelPane(
                        config.openai_model_2,
                        ModelProvider.OPENAI,
                        "openai_2",
                        classes="model-pane",
                    )
                    self.model_panes["openai_2"] = pane
                    yield pane
                else:
                    yield Static("No OpenAI Model 2", classes="model-pane")

                if config.anthropic_api_key and config.anthropic_model_1:
                    pane = ModelPane(
                        config.anthropic_model_1,
                        ModelProvider.ANTHROPIC,
                        "anthropic_1",
                        classes="model-pane",
                    )
                    self.model_panes["anthropic_1"] = pane
                    yield pane
                else:
                    yield Static("No Anthropic Model", classes="model-pane")

                # Bottom row
                if config.gemini_api_key and config.gemini_model:
                    pane = ModelPane(
                        config.gemini_model, ModelProvider.GEMINI, "gemini", classes="model-pane"
                    )
                    self.model_panes["gemini"] = pane
                    yield pane
                else:
                    yield Static("No Gemini Model", classes="model-pane")

                if config.mistral_api_key and config.mistral_model:
                    pane = ModelPane(
                        config.mistral_model, ModelProvider.MISTRAL, "mistral", classes="model-pane"
                    )
                    self.model_panes["mistral"] = pane
                    yield pane
                else:
                    yield Static("No Mistral Model", classes="model-pane")

            # Input at the bottom (outside the grid)
            yield TextArea("", id="main-input", classes="input-section", show_line_numbers=False)

        yield Footer()

    def on_mount(self) -> None:
        """Set up the application on mount."""
        self.title = "Chatmux"
        self.sub_title = "Multi-LLM Chat Interface"

        # Set initial messages for non-implemented providers
        for _pane_id, pane in self.model_panes.items():
            content_widget = pane.query_one("#content", TextArea)
            if pane.provider == ModelProvider.ANTHROPIC:
                content_widget.load_text("Anthropic client not yet implemented")
            elif pane.provider == ModelProvider.GEMINI:
                content_widget.load_text("Gemini client not yet implemented")
            elif pane.provider == ModelProvider.MISTRAL:
                content_widget.load_text("Mistral client not yet implemented")

        # Focus the input
        input_area = self.query_one("#main-input", TextArea)
        input_area.border_title = "💬 Input"
        input_area.border_subtitle = "Ctrl+D to send | Enter for new line | @model to target"
        self.set_focus(input_area)

    async def action_send_message(self) -> None:
        """Send message when triggered."""
        input_area = self.query_one("#main-input", TextArea)
        message = input_area.text.strip()
        if not message:
            return

        # Clear input
        input_area.clear()

        # Parse target models
        target_models = self._parse_model_targets(message)

        # Add to history
        user_msg = Message(role=MessageRole.USER, content=message)
        self.conversation_history.append(user_msg)

        # Send to models
        asyncio.create_task(self._send_to_models(message, target_models))

    def _parse_model_targets(self, text: str) -> list[str]:
        """Parse @model targets from input text."""
        targets = []
        words = text.split()

        for word in words:
            if word.startswith("@") and len(word) > 1:
                model_name = word[1:]
                targets.append(model_name)

        return targets

    async def _send_to_models(self, message: str, target_models: list[str]) -> None:
        """Send message to models."""
        # Determine target panes
        if target_models:
            # Filter panes by model names
            target_panes = []
            for _pane_id, pane in self.model_panes.items():
                if any(target.lower() in pane.model_name.lower() for target in target_models):
                    target_panes.append(pane)
        else:
            # Send to all active panes
            target_panes = list(self.model_panes.values())

        if not target_panes:
            return

        # Show thinking state
        for pane in target_panes:
            pane.set_thinking(message)

        # Create model configs for coordinator
        model_configs = []
        for pane in target_panes:
            if pane.provider == ModelProvider.OPENAI:
                # Get full config from config object
                pane_num = "1" if pane.model_name == config.openai_model_1 else "2"
                config_dict = config.get_model_config("openai", pane_num)
                # Add provider as enum and pane_id
                config_dict["provider"] = pane.provider
                config_dict["pane_id"] = pane.pane_id
                model_configs.append(ModelConfig(**config_dict))
            # Add other providers as they're implemented

        if model_configs:
            # Send to coordinator with conversation history
            await self.coordinator.send_to_models(
                message,
                model_configs,
                self.conversation_history[:-1],  # Exclude the last message we just added
            )

    def _handle_stream_update(self, update: StreamUpdate) -> None:
        """Handle streaming updates from the coordinator."""
        # Find the pane by ID
        pane = self.model_panes.get(update.pane_id)
        if not pane:
            return

        if update.error:
            pane.set_error(update.error)
        elif update.is_complete:
            # Final update - mark as complete
            pane.border_subtitle = "[✓ Complete]"
        else:
            # Streaming update - accumulate content
            pane._accumulated_content += update.content
            pane.update_content(pane._accumulated_content)

    async def action_quit(self) -> None:
        """Quit the application."""
        await self.coordinator.cancel_all()
        self.exit()

    async def action_copy_focused(self) -> None:
        """Copy the content of the focused pane to clipboard."""
        if pyperclip is None:
            self.notify("pyperclip is not installed", severity="error")
            return

        # Find which model pane has focus
        focused = self.focused

        # Check if it's a ModelPane by looking for the pane_id attribute
        if focused and hasattr(focused, "pane_id"):
            # This is a ModelPane, copy its content
            try:
                content = (
                    focused._accumulated_content if hasattr(focused, "_accumulated_content") else ""
                )
                if content:
                    pyperclip.copy(content)
                    self.notify(
                        f"Copied {len(content)} characters to clipboard!", severity="information"
                    )
                else:
                    self.notify("No content to copy", severity="warning")
            except Exception as e:
                self.notify(f"Failed to copy: {e}", severity="error")
        else:
            # Try to find any focused model pane
            for _pane_id, pane in self.model_panes.items():
                if pane.has_focus or any(child.has_focus for child in pane.walk_children()):
                    try:
                        content = (
                            pane._accumulated_content
                            if hasattr(pane, "_accumulated_content")
                            else ""
                        )
                        if content:
                            pyperclip.copy(content)
                            self.notify(
                                f"Copied {len(content)} characters to clipboard!",
                                severity="information",
                            )
                        else:
                            self.notify("No content to copy", severity="warning")
                        return
                    except Exception as e:
                        self.notify(f"Failed to copy: {e}", severity="error")
                        return
            self.notify("Focus a model pane first (Tab to switch)", severity="warning")


def main() -> None:
    """Run the Textual-based Chatmux application."""
    app = ChatmuxTextualApp()
    app.run()


if __name__ == "__main__":
    main()
