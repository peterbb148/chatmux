"""Grid layout manager for the terminal UI."""

from rich.console import Console, RenderableType
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.style import Style

from .input_pane import InputPane
from .pane import ModelPane


class GridLayout:
    """Manages the 2x3 grid layout of model panes."""

    def __init__(self, rows: int = 2, cols: int = 3, input_pane: InputPane | None = None):
        """Initialize grid layout.

        Args:
            rows: Number of rows in grid
            cols: Number of columns in grid
            input_pane: Optional input pane to display at position (1, 2)
        """
        self.rows = rows
        self.cols = cols
        self.panes: list[ModelPane] = []
        self.focused_index: int = 0
        self.console = Console()
        self._live: Live | None = None
        self.input_pane = input_pane

    def add_pane(self, model_name: str, position: tuple[int, int]) -> ModelPane:
        """Add a model pane to the grid.

        Args:
            model_name: Name of the model
            position: Grid position as (row, col)

        Returns:
            The created ModelPane

        Raises:
            ValueError: If position is invalid or already occupied
        """
        row, col = position
        if row >= self.rows or col >= self.cols:
            raise ValueError(f"Invalid position {position} for {self.rows}x{self.cols} grid")

        # Check if position is reserved for input pane
        if self.input_pane and position == (1, 2):
            raise ValueError("Position (1, 2) is reserved for input pane")

        # Check if position is already occupied
        for pane in self.panes:
            if pane.position == position:
                raise ValueError(f"Position {position} already occupied")

        pane = ModelPane(model_name, position)
        self.panes.append(pane)

        # Update focus if this is the first pane
        if len(self.panes) == 1:
            pane.set_focused(True)

        return pane

    def get_pane(self, position: tuple[int, int]) -> ModelPane | None:
        """Get pane at specific position."""
        for pane in self.panes:
            if pane.position == position:
                return pane
        return None

    def get_focused_pane(self) -> ModelPane | None:
        """Get the currently focused pane."""
        if 0 <= self.focused_index < len(self.panes):
            return self.panes[self.focused_index]
        return None

    def focus_next(self) -> None:
        """Move focus to next pane."""
        if self.panes:
            self.panes[self.focused_index].set_focused(False)
            self.focused_index = (self.focused_index + 1) % len(self.panes)
            self.panes[self.focused_index].set_focused(True)

    def focus_previous(self) -> None:
        """Move focus to previous pane."""
        if self.panes:
            self.panes[self.focused_index].set_focused(False)
            self.focused_index = (self.focused_index - 1) % len(self.panes)
            self.panes[self.focused_index].set_focused(True)

    def focus_pane(self, index: int) -> None:
        """Focus a specific pane by index."""
        if 0 <= index < len(self.panes):
            self.panes[self.focused_index].set_focused(False)
            self.focused_index = index
            self.panes[self.focused_index].set_focused(True)

    def render(self) -> RenderableType:
        """Render the grid layout.

        Returns:
            Renderable grid layout
        """
        # Always create a fresh layout structure to avoid update issues
        # This matches the working pattern from our debug test
        layout = Layout(name="main")

        # Create 2x3 grid structure with smaller minimum sizes
        top_row = Layout(name="top_row", ratio=1, minimum_size=8)
        bottom_row = Layout(name="bottom_row", ratio=1, minimum_size=8)

        # Create a 2D grid of panels
        grid: list[list[Panel | None]] = [
            [None for _ in range(self.cols)] for _ in range(self.rows)
        ]

        # Place panes in grid
        for pane in self.panes:
            row, col = pane.position
            grid[row][col] = pane.render()

        # Place input pane at bottom-right position (1,2) if provided
        if self.input_pane and self.rows >= 2 and self.cols >= 3:
            if grid[1][2] is None:
                grid[1][2] = self.input_pane.render()
        elif not self.input_pane and self.rows >= 2 and self.cols >= 3:
            # Create default input panel if no input pane provided
            input_panel = Panel(
                "[dim]Type your message here... (Press Tab to switch panes)[/dim]",
                title="[bold]Input[/bold]",
                border_style="bright_blue",
                expand=True,
            )
            if grid[1][2] is None:
                grid[1][2] = input_panel

        # Fill remaining empty positions with placeholder panels
        for row in range(self.rows):
            for col in range(self.cols):
                if grid[row][col] is None:
                    grid[row][col] = Panel(
                        "[dim italic]Empty slot[/dim italic]",
                        title="[dim]No Model[/dim]",
                        border_style=Style(color="white", dim=True),
                        expand=True,
                    )

        # Split top row into 3 columns with the actual panels
        top_row.split_row(
            Layout(grid[0][0], name="top_0_0"),
            Layout(grid[0][1], name="top_0_1"),
            Layout(grid[0][2], name="top_0_2"),
        )

        # Split bottom row into 3 columns with the actual panels
        bottom_row.split_row(
            Layout(grid[1][0], name="bottom_1_0"),
            Layout(grid[1][1], name="bottom_1_1"),
            Layout(grid[1][2], name="bottom_1_2"),
        )

        # Combine the rows
        layout.split_column(top_row, bottom_row)

        return layout

    def start_live_display(self) -> None:
        """Start live display for real-time updates."""
        if self._live is None:
            self._live = Live(
                self.render(),
                console=self.console,
                refresh_per_second=10,
                transient=False,
            )
            self._live.start()

    def stop_live_display(self) -> None:
        """Stop live display."""
        if self._live is not None:
            self._live.stop()
            self._live = None

    def update_display(self) -> None:
        """Update the live display."""
        # This method is called by input handler but we don't have our own Live display
        # The app manages the Live display, so this is a no-op
        pass

    def handle_resize(self) -> None:
        """Handle terminal resize event."""
        # Rich handles most resize logic automatically
        # Just trigger a display update
        self.update_display()
