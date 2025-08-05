#!/usr/bin/env python3
"""
Simple Textual test to verify input handling works.
"""

from textual.app import App, ComposeResult
from textual.widgets import Input, Static, Header, Footer
from textual.binding import Binding


class SimpleTest(App):
    """Simple test app to verify input works."""
    
    BINDINGS = [
        Binding("escape", "quit", "Quit"),
        Binding("ctrl+c", "quit", "Quit"),
    ]
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Type something and press Enter:", id="instructions")
        yield Input(placeholder="Type here...")
        yield Static("", id="output")
        yield Footer()
    
    def on_mount(self) -> None:
        self.title = "Textual Input Test"
        input_widget = self.query_one(Input)
        input_widget.focus()
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission."""
        message = event.value.strip()
        
        # Update output
        output = self.query_one("#output", Static)
        output.update(f"✅ Received: '{message}'")
        
        # Clear input
        event.input.value = ""


if __name__ == "__main__":
    app = SimpleTest()
    app.run()