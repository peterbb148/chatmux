"""Demo of the Chatmux UI grid layout."""

import sys
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from chatmux.ui import GridLayout, PaneStatus


def main():
    """Run UI demo."""
    # Create grid layout
    grid = GridLayout(rows=2, cols=3)

    # Add model panes (5 models, leaving bottom-right for input)
    models = [
        ("GPT-4", (0, 0)),
        ("Claude 3", (0, 1)),
        ("Gemini Pro", (0, 2)),
        ("Mistral", (1, 0)),
        ("Llama 3", (1, 1)),
        # Position (1, 2) is reserved for input pane
    ]

    panes = []
    for model_name, position in models:
        pane = grid.add_pane(model_name, position)
        panes.append(pane)

    # Start live display
    grid.start_live_display()

    try:
        # Simulate some activity
        time.sleep(1)

        # Set some content
        panes[0].set_content("# Hello from GPT-4!\n\nThis is a **markdown** response.")
        grid.update_display()
        time.sleep(1)

        # Simulate streaming
        panes[1].status = PaneStatus.STREAMING
        panes[1].set_content("Thinking")
        grid.update_display()

        for _ in range(3):
            time.sleep(0.5)
            panes[1].append_content(".")
            grid.update_display()

        code = (
            "\n\nHere's some code:\n\n```python\ndef hello():\n    print('Hello from Claude!')\n```"
        )
        panes[1].append_content(code)
        panes[1].status = PaneStatus.IDLE
        grid.update_display()

        # Show error
        time.sleep(1)
        panes[2].set_error("API rate limit exceeded")
        grid.update_display()

        # Test focus switching
        time.sleep(1)
        for _ in range(6):
            grid.focus_next()
            grid.update_display()
            time.sleep(0.5)

        # Keep running for a bit
        time.sleep(3)

    finally:
        grid.stop_live_display()


if __name__ == "__main__":
    main()
