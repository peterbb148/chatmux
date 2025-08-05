#!/usr/bin/env python3
"""
Textual proof-of-concept for Chatmux 2x3 grid layout.
This demonstrates a working TUI with proper input handling.
"""

from textual.app import App, ComposeResult
from textual.containers import Grid, Vertical
from textual.widgets import Input, Static, Header, Footer
from textual.binding import Binding


class ModelPane(Static):
    """A model pane showing model status and responses."""
    
    def __init__(self, model_name: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self.model_name = model_name
        self.border = True
        
    def compose(self) -> ComposeResult:
        yield Static(f"🤖 {self.model_name}", id="title")
        yield Static("Waiting for response...", id="content")
    
    def on_mount(self) -> None:
        self.border_title = f"{self.model_name} ✓"
        
    def update_content(self, content: str) -> None:
        """Update the model's response content."""
        content_widget = self.query_one("#content", Static)
        content_widget.update(content)


class ChatmuxApp(App):
    """Textual-based Chatmux application."""
    
    CSS = """
    Grid {
        grid-size: 3 3;
        grid-gutter: 1 1;
    }
    
    .model-pane {
        border: solid blue;
        height: 100%;
    }
    
    .input-section {
        height: 3;
        border: solid green;
    }
    
    Input {
        border: solid cyan;
    }
    
    #title {
        text-style: bold;
        background: blue 20%;
        height: 1;
    }
    
    #content {
        height: 1fr;
        padding: 1;
    }
    """
    
    BINDINGS = [
        Binding("escape", "quit", "Quit"),
        Binding("ctrl+c", "quit", "Quit"),
    ]
    
    def compose(self) -> ComposeResult:
        yield Header()
        
        with Grid():
            # Top row - 3 model panes
            yield ModelPane("GPT-4", classes="model-pane")
            yield ModelPane("GPT-3.5-Turbo", classes="model-pane") 
            yield ModelPane("Claude-3.5-Sonnet", classes="model-pane")
            
            # Second row - 2 model panes + input
            yield ModelPane("Gemini-Pro", classes="model-pane")
            yield ModelPane("Mistral-Large", classes="model-pane")
            
            # Input section
            with Vertical(classes="input-section"):
                yield Static("💬 Input", id="input-title")
                yield Input(placeholder="Type your message here... (Enter to send)")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Set up the application."""
        self.title = "Chatmux - Multi-LLM Chat"
        self.sub_title = "Textual Proof of Concept"
        
        # Focus the input
        input_widget = self.query_one(Input)
        input_widget.focus()
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission."""
        message = event.value.strip()
        if not message:
            return
            
        # Clear input
        event.input.value = ""
        
        # Simulate sending to all models
        self.simulate_responses(message)
    
    def simulate_responses(self, message: str) -> None:
        """Simulate model responses."""
        # Get all model panes
        model_panes = self.query(ModelPane)
        
        for i, pane in enumerate(model_panes):
            # Show "thinking" state
            pane.update_content(f"💭 Processing: {message[:30]}...")
            
            # Simulate response after delay (in real app, this would be async)
            self.call_later(
                1.0 + i * 0.5,  # Staggered responses
                lambda p=pane, m=message: p.update_content(
                    f"Response to '{m}' from {p.model_name}:\n\n"
                    f"This is a simulated response. The input was received "
                    f"and processed successfully. In the real implementation, "
                    f"this would be an actual AI model response."
                )
            )


def main():
    """Run the Textual proof-of-concept."""
    app = ChatmuxApp()
    app.run()


if __name__ == "__main__":
    main()