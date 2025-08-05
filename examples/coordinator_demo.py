"""Demo of the response coordinator with multiple models."""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.live import Live

from chatmux.coordinator import ResponseCoordinator, StreamUpdate
from chatmux.core.models import ModelProvider
from chatmux.ui.grid import GridLayout
from chatmux.ui.pane import ModelPane


def create_demo_layout() -> tuple[GridLayout, list[ModelPane]]:
    """Create demo layout with model panes."""
    grid = GridLayout(2, 3)
    panes = []

    # Add OpenAI models
    if os.getenv("OPENAI_API_KEY"):
        pane1 = ModelPane("GPT-4", (0, 0), provider=ModelProvider.OPENAI)
        grid.add_pane("GPT-4", (0, 0))
        grid.panes[0] = pane1  # Replace with our pane that has provider
        panes.append(pane1)

        pane2 = ModelPane("GPT-3.5", (0, 1), provider=ModelProvider.OPENAI)
        grid.add_pane("GPT-3.5", (0, 1))
        grid.panes[1] = pane2
        panes.append(pane2)

    # Add placeholders for other providers
    pane3 = ModelPane("Claude (Coming Soon)", (0, 2))
    pane3.set_content("Anthropic integration coming soon...")
    grid.add_pane("Claude", (0, 2))
    grid.panes[-1] = pane3

    pane4 = ModelPane("Gemini (Coming Soon)", (1, 0))
    pane4.set_content("Google integration coming soon...")
    grid.add_pane("Gemini", (1, 0))
    grid.panes[-1] = pane4

    pane5 = ModelPane("Mistral (Coming Soon)", (1, 1))
    pane5.set_content("Mistral integration coming soon...")
    grid.add_pane("Mistral", (1, 1))
    grid.panes[-1] = pane5

    # Position (1, 2) is reserved for input

    return grid, panes


async def demo_coordinator() -> None:
    """Run the coordinator demo."""
    console = Console()

    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        console.print("[red]Error: OPENAI_API_KEY not set[/red]")
        console.print("Please set it with: export OPENAI_API_KEY='your-api-key'")
        return

    # Create layout
    grid, panes = create_demo_layout()

    # Create coordinator with update callback
    def on_update(update: StreamUpdate) -> None:
        """Handle stream updates."""
        # In real app, this would update the UI
        # For demo, we just update the grid
        grid.update_display()

    coordinator = ResponseCoordinator(on_stream_update=on_update)

    # Start live display
    console.print("\n[bold cyan]Response Coordinator Demo[/bold cyan]")
    console.print("=" * 50)
    console.print("\nSending prompt to multiple models simultaneously...\n")

    with Live(grid.render(), refresh_per_second=10, transient=False) as live:
        # Demo prompts
        prompts = [
            "Write a haiku about programming",
            "What is the meaning of life in exactly 3 sentences?",
            "Explain quantum computing to a 5-year-old",
        ]

        for i, prompt in enumerate(prompts):
            if i > 0:
                await asyncio.sleep(2)  # Pause between prompts
                console.print("\n" + "-" * 50 + "\n")

            console.print(f"[yellow]Prompt {i+1}:[/yellow] {prompt}")

            # Send to available models (only OpenAI for now)
            available_panes = [p for p in panes if p.provider == ModelProvider.OPENAI]

            # Clear previous responses
            for pane in available_panes:
                pane.clear_content()

            # Send prompt
            tasks = await coordinator.send_to_models(prompt, available_panes)

            # Update display while streaming
            while coordinator.get_active_count() > 0:
                live.update(grid.render())
                await asyncio.sleep(0.1)

            # Final update
            live.update(grid.render())

            # Show token usage summary (when implemented)
            usage = coordinator.get_token_usage_summary()
            if usage:
                console.print("\n[dim]Token usage:[/dim]")
                for pane_id, tokens in usage.items():
                    console.print(f"  {pane_id}: {tokens.total_tokens} tokens")

        # Keep display for a moment
        await asyncio.sleep(2)

    console.print("\n[green]Demo completed![/green]")

    # Cancel any remaining tasks
    await coordinator.cancel_all()


async def main() -> None:
    """Run the demo."""
    try:
        await demo_coordinator()
    except KeyboardInterrupt:
        console = Console()
        console.print("\n[yellow]Demo interrupted[/yellow]")


if __name__ == "__main__":
    asyncio.run(main())
