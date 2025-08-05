"""
Textual-based Chatmux application.
This replaces the broken Rich-based implementation with a proper TUI framework.
"""

import asyncio
from typing import Any

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Grid, Vertical
from textual.widgets import Footer, Header, Input, Static

from .config import config
from .coordinator import ResponseCoordinator, StreamUpdate
from .core.models import Message, MessageRole, ModelConfig, ModelProvider


class ModelPane(Static):
    """A model pane showing model status and responses."""
    
    def __init__(
        self,
        model_name: str,
        provider: ModelProvider,
        pane_id: str,
        **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self.model_name = model_name
        self.provider = provider
        self.pane_id = pane_id
        self.border = True
        
    def compose(self) -> ComposeResult:
        yield Static(f"🤖 {self.model_name}", id="title", classes="pane-title")
        yield Static("Waiting for response...", id="content", classes="pane-content")
    
    def on_mount(self) -> None:
        self.border_title = f"{self.model_name} ✓"
        self.border_subtitle = f"[{self.provider.value}]"
        
    def update_content(self, content: str) -> None:
        """Update the model's response content."""
        content_widget = self.query_one("#content", Static)
        content_widget.update(content)
        
    def set_thinking(self, message: str) -> None:
        """Show thinking state."""
        self.update_content(f"💭 Processing: {message[:50]}...")
        
    def set_error(self, error: str) -> None:
        """Show error state."""
        self.update_content(f"❌ Error: {error}")


class ChatmuxTextualApp(App):
    """Textual-based Chatmux application."""
    
    CSS = """
    Grid {
        grid-size: 3 2;
        grid-gutter: 1 1;
        height: 100%;
    }
    
    .model-pane {
        border: solid $primary;
        height: 100%;
    }
    
    .input-section {
        height: 5;
        border: solid $success;
    }
    
    Input {
        border: solid $accent;
        margin: 0 1;
    }
    
    .pane-title {
        text-style: bold;
        background: $primary 20%;
        height: 1;
        padding: 0 1;
    }
    
    .pane-content {
        height: 1fr;
        padding: 1;
        overflow-y: auto;
    }
    
    #input-title {
        text-style: bold;
        height: 1;
        padding: 0 1;
    }
    """
    
    BINDINGS = [
        Binding("escape", "quit", "Quit"),
        Binding("ctrl+c", "quit", "Quit"),
        Binding("tab", "focus_next", "Next pane"),
        Binding("shift+tab", "focus_previous", "Previous pane"),
    ]
    
    def __init__(self):
        super().__init__()
        self.coordinator = ResponseCoordinator(on_stream_update=self._handle_stream_update)
        self.conversation_history: list[Message] = []
        self.model_panes: dict[str, ModelPane] = {}
        
    def compose(self) -> ComposeResult:
        yield Header()
        
        with Grid():
            # Create model panes based on configuration
            # Top row
            if config.openai_api_key and config.openai_model_1:
                pane = ModelPane(
                    config.openai_model_1,
                    ModelProvider.OPENAI,
                    "openai_1",
                    classes="model-pane"
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
                    classes="model-pane"
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
                    classes="model-pane"
                )
                self.model_panes["anthropic_1"] = pane
                yield pane
            else:
                yield Static("No Anthropic Model", classes="model-pane")
                
            # Bottom row
            if config.gemini_api_key and config.gemini_model:
                pane = ModelPane(
                    config.gemini_model,
                    ModelProvider.GEMINI,
                    "gemini",
                    classes="model-pane"
                )
                self.model_panes["gemini"] = pane
                yield pane
            else:
                yield Static("No Gemini Model", classes="model-pane")
                
            if config.mistral_api_key and config.mistral_model:
                pane = ModelPane(
                    config.mistral_model,
                    ModelProvider.MISTRAL,
                    "mistral",
                    classes="model-pane"
                )
                self.model_panes["mistral"] = pane
                yield pane
            else:
                yield Static("No Mistral Model", classes="model-pane")
                
            # Input section
            with Vertical(classes="input-section"):
                yield Static("💬 Input (@model to target specific models)", id="input-title")
                yield Input(
                    placeholder="Type your message here... (Enter to send, Tab to switch panes)",
                    id="main-input"
                )
        
        yield Footer()
        
    def on_mount(self) -> None:
        """Set up the application on mount."""
        self.title = "Chatmux"
        self.sub_title = "Multi-LLM Chat Interface"
        
        # Set initial messages for non-implemented providers
        for pane_id, pane in self.model_panes.items():
            if pane.provider == ModelProvider.ANTHROPIC:
                pane.update_content("Anthropic client not yet implemented")
            elif pane.provider == ModelProvider.GEMINI:
                pane.update_content("Gemini client not yet implemented")
            elif pane.provider == ModelProvider.MISTRAL:
                pane.update_content("Mistral client not yet implemented")
        
        # Focus the input
        self.set_focus(self.query_one("#main-input", Input))
        
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission."""
        message = event.value.strip()
        if not message:
            return
            
        # Clear input
        event.input.value = ""
        
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
            for pane_id, pane in self.model_panes.items():
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
                config_dict = {
                    "provider": pane.provider,
                    "model": pane.model_name,
                    "pane_id": pane.pane_id,
                }
                model_configs.append(ModelConfig(**config_dict))
            # Add other providers as they're implemented
            
        if model_configs:
            # Send to coordinator
            await self.coordinator.send_to_models(message, model_configs)
            
    def _handle_stream_update(self, update: StreamUpdate) -> None:
        """Handle streaming updates from the coordinator."""
        # Find the pane by ID
        pane = self.model_panes.get(update.pane_id)
        if not pane:
            return
            
        if update.error:
            pane.set_error(update.error)
        elif update.done:
            # Final update - content should be complete
            if update.content:
                pane.update_content(update.content)
        else:
            # Streaming update
            pane.update_content(update.content)
            
    async def action_quit(self) -> None:
        """Quit the application."""
        await self.coordinator.cancel_all()
        self.exit()


def main() -> None:
    """Run the Textual-based Chatmux application."""
    app = ChatmuxTextualApp()
    app.run()


if __name__ == "__main__":
    main()