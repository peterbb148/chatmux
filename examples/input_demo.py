"""Demo of the input handling system."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console

from chatmux.input_handler import InputHandler
from chatmux.ui.grid import GridLayout


async def mock_send_to_models(text: str, target_models: list[str]) -> None:
    """Mock function to simulate sending to models."""
    console = Console()
    if target_models:
        console.print(f"\n[yellow]Sending to {', '.join(target_models)}:[/yellow] {text}")
    else:
        console.print(f"\n[green]Sending to all models:[/green] {text}")

    # Simulate processing delay
    await asyncio.sleep(0.5)
    console.print("[dim]Message sent![/dim]\n")


def main() -> None:
    """Run the input handling demo."""
    console = Console()

    # Create grid layout
    grid = GridLayout(2, 3)

    # Add some model panes
    grid.add_pane("GPT-4", (0, 0))
    grid.add_pane("Claude", (0, 1))
    grid.add_pane("Gemini", (0, 2))
    grid.add_pane("Mistral", (1, 0))
    grid.add_pane("Ollama", (1, 1))
    # Position (1, 2) is reserved for input

    # Create input handler
    handler = InputHandler(grid, send_to_models=mock_send_to_models)

    # Set the input pane in the grid
    grid.input_pane = handler.get_input_pane()

    console.print("\n[bold cyan]Input Handling Demo[/bold cyan]")
    console.print("=" * 50)
    console.print("\n[yellow]Instructions:[/yellow]")
    console.print("• Type your message and press Enter to send")
    console.print("• Use @model to target specific models (e.g., @gpt4 @claude)")
    console.print("• Press Tab to switch focus between input and model panes")
    console.print("• Use arrow keys to navigate history or switch panes")
    console.print("• Press Ctrl+C to exit\n")

    # Start the grid display
    grid.start_live_display()

    try:
        # Simple input loop for demo
        while True:
            # Update display
            grid.update_display()

            # NOTE: This is a simplified demo implementation using input(),
            # which blocks the event loop. In real usage, you should use a proper
            # keyboard library (e.g., prompt_toolkit, curses) to handle
            # non-blocking, event-driven keyboard input.
            key = input("\nEnter key (or 'quit' to exit): ").strip().lower()

            if key == "quit":
                break

            # Handle the key
            handled = handler.handle_key(key)

            if not handled:
                console.print(f"[dim]Unknown key: {key}[/dim]")

    except KeyboardInterrupt:
        pass
    finally:
        grid.stop_live_display()
        console.print("\n[green]Demo ended![/green]")


if __name__ == "__main__":
    main()
