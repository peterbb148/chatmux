"""Grid layout manager for the terminal UI."""

from rich.console import Console, RenderableType
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.style import Style

from .pane import ModelPane


class GridLayout:
    """Manages the 2x3 grid layout of model panes."""

    def __init__(self, rows: int = 2, cols: int = 3):
        """Initialize grid layout.

        Args:
            rows: Number of rows in grid
            cols: Number of columns in grid
        """
        self.rows = rows
        self.cols = cols
        self.panes: list[ModelPane] = []
        self.focused_index: int = 0
        self.console = Console()
        self._live: Live | None = None

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
        # Create a 2D grid of panes
        grid: list[list[Panel | None]] = [
            [None for _ in range(self.cols)] for _ in range(self.rows)
        ]

        # Place panes in grid
        for pane in self.panes:
            row, col = pane.position
            grid[row][col] = pane.render()

        # Create input panel for bottom-right position (1,2)
        input_panel = Panel(
            "[dim]Type your message here... (Press Tab to switch panes)[/dim]",
            title="[bold]Input[/bold]",
            border_style="bright_blue",
            expand=True,
        )

        # Place input panel at bottom-right if that position is empty
        if self.rows >= 2 and self.cols >= 3:
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

        # Create rows of columns
        rows: list[Layout] = []
        for i, grid_row in enumerate(grid):
            # Create a layout for this row
            row_layout = Layout(name=f"row{i}")

            # Split the row into columns
            col_layouts = []
            for j, panel in enumerate(grid_row):
                if panel is not None:
                    col_layout = Layout(panel, name=f"col{i}_{j}")
                    col_layouts.append(col_layout)

            if col_layouts:
                row_layout.split_row(*col_layouts)
            rows.append(row_layout)

        # Create the final layout
        layout = Layout()

        if len(rows) == 1:
            layout.update(rows[0])
        else:
            # Split into rows vertically with equal height
            layout.split_column(*rows)

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
        if self._live is not None:
            self._live.update(self.render())

    def handle_resize(self) -> None:
        """Handle terminal resize event."""
        # Rich handles most resize logic automatically
        # Just trigger a display update
        self.update_display()
