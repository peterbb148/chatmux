"""Simple test to verify grid layout."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.columns import Columns
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel


def test_grid():
    """Test basic grid layout."""
    console = Console()

    # Create a 2x3 grid of panels
    row1 = Columns(
        [
            Panel("GPT-4", expand=True),
            Panel("Claude 3", expand=True),
            Panel("Gemini", expand=True),
        ],
        equal=True,
        expand=True,
    )

    row2 = Columns(
        [
            Panel("Mistral", expand=True),
            Panel("Llama 3", expand=True),
            Panel("GPT-3.5", expand=True),
        ],
        equal=True,
        expand=True,
    )

    # Create layout
    layout = Layout()
    layout.split_column(
        Layout(row1, name="row1"),
        Layout(row2, name="row2"),
        Layout(Panel("Input area"), name="input", size=3),
    )

    console.print(layout, height=20)


if __name__ == "__main__":
    test_grid()
