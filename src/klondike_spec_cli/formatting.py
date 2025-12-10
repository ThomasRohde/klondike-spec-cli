"""Rich terminal formatting for klondike CLI.

Provides color-coded output, progress bars, and tables with
a --no-color fallback.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

from rich.console import Console
from rich.progress import BarColumn, Progress, TextColumn
from rich.table import Table
from rich.text import Text

if TYPE_CHECKING:
    from .models import Feature, FeatureRegistry, FeatureStatus

# Global color state
_no_color: bool = False


def set_no_color(value: bool) -> None:
    """Set global no-color mode."""
    global _no_color
    _no_color = value


def is_no_color() -> bool:
    """Check if color is disabled."""
    return _no_color or os.environ.get("NO_COLOR", "") != ""


def get_console() -> Console:
    """Get a Rich console with appropriate color settings."""
    return Console(no_color=is_no_color(), force_terminal=not is_no_color())


@dataclass
class StatusColors:
    """Color mapping for feature statuses."""

    NOT_STARTED = "dim"
    IN_PROGRESS = "yellow"
    BLOCKED = "red"
    VERIFIED = "green"


def status_icon(status: FeatureStatus, plain: bool = False) -> str:
    """Get status icon with optional color styling."""
    from .models import FeatureStatus

    icons = {
        FeatureStatus.NOT_STARTED: ("⏳", StatusColors.NOT_STARTED),
        FeatureStatus.IN_PROGRESS: ("🔄", StatusColors.IN_PROGRESS),
        FeatureStatus.BLOCKED: ("🚫", StatusColors.BLOCKED),
        FeatureStatus.VERIFIED: ("✅", StatusColors.VERIFIED),
    }

    icon, _ = icons.get(status, ("•", "white"))
    return icon


def colored_status(status: FeatureStatus) -> Text:
    """Get colored status text for Rich output."""
    from .models import FeatureStatus

    colors = {
        FeatureStatus.NOT_STARTED: ("Not started", StatusColors.NOT_STARTED),
        FeatureStatus.IN_PROGRESS: ("In progress", StatusColors.IN_PROGRESS),
        FeatureStatus.BLOCKED: ("Blocked", StatusColors.BLOCKED),
        FeatureStatus.VERIFIED: ("Verified", StatusColors.VERIFIED),
    }

    text, color = colors.get(status, (str(status), "white"))
    return Text(f"{status_icon(status)} {text}", style=color)


def colored_percentage(value: float) -> Text:
    """Get colored percentage text based on completion."""
    if value >= 80:
        color = "green"
    elif value >= 50:
        color = "yellow"
    else:
        color = "red"

    return Text(f"{value:.1f}%", style=color)


def progress_bar_text(completed: int, total: int, width: int = 20) -> str:
    """Generate a text-based progress bar.

    Args:
        completed: Number of completed items
        total: Total number of items
        width: Width of the bar in characters

    Returns:
        A progress bar string like [████████░░░░░░░░░░░░] 40%
    """
    if total == 0:
        percentage = 0.0
    else:
        percentage = (completed / total) * 100

    filled = int((percentage / 100) * width)
    empty = width - filled

    bar = "█" * filled + "░" * empty
    return f"[{bar}] {percentage:.1f}%"


def progress_bar_rich(completed: int, total: int, description: str = "Progress") -> None:
    """Display an animated Rich progress bar."""
    console = get_console()

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task(description, total=total, completed=completed)
        progress.update(task, completed=completed)


def print_feature_table(
    features: list[Feature],
    title: str = "Features",
    show_criteria: bool = False,
) -> None:
    """Print a formatted table of features.

    Args:
        features: List of features to display
        title: Table title
        show_criteria: Whether to show acceptance criteria column
    """
    console = get_console()

    table = Table(title=title, show_header=True, header_style="bold")
    table.add_column("ID", style="cyan", width=6)
    table.add_column("Description", style="white")
    table.add_column("Category", style="magenta", width=12)
    table.add_column("Priority", justify="center", width=8)
    table.add_column("Status", width=16)

    if show_criteria:
        table.add_column("Criteria", style="dim")

    for f in sorted(features, key=lambda x: (x.priority, x.id)):
        row = [
            f.id,
            f.description[:50] + ("..." if len(f.description) > 50 else ""),
            f.category,
            f"P{f.priority}",
            colored_status(f.status),
        ]

        if show_criteria:
            criteria_text = ", ".join(f.acceptance_criteria[:2])
            if len(f.acceptance_criteria) > 2:
                criteria_text += f" (+{len(f.acceptance_criteria) - 2})"
            row.append(criteria_text)

        table.add_row(*row)

    console.print(table)


def print_status_summary(registry: FeatureRegistry, project_name: str) -> None:
    """Print a rich status summary with colors and progress bar.

    Args:
        registry: The feature registry
        project_name: Name of the project
    """
    from .models import FeatureStatus

    console = get_console()

    total = len(registry.features)
    verified = len(registry.get_features_by_status(FeatureStatus.VERIFIED))
    in_progress = len(registry.get_features_by_status(FeatureStatus.IN_PROGRESS))
    blocked = len(registry.get_features_by_status(FeatureStatus.BLOCKED))
    not_started = len(registry.get_features_by_status(FeatureStatus.NOT_STARTED))

    percentage = (verified / total * 100) if total > 0 else 0.0

    # Header
    console.print()
    console.print(f"[bold blue]📊 Project:[/bold blue] [white]{project_name}[/white]")
    console.print(f"   [dim]Completion: {percentage:.1f}%[/dim]")
    console.print()

    # Progress bar
    console.print(f"[bold]Progress:[/bold] {progress_bar_text(verified, total)}")
    console.print()

    # Status breakdown with colors
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Icon", width=3)
    table.add_column("Status", width=12)
    table.add_column("Count", justify="right", width=5)

    if verified > 0:
        table.add_row("✅", Text("Verified", style="green"), str(verified))
    if in_progress > 0:
        table.add_row("🔄", Text("In Progress", style="yellow"), str(in_progress))
    if blocked > 0:
        table.add_row("🚫", Text("Blocked", style="red"), str(blocked))
    if not_started > 0:
        table.add_row("⏳", Text("Not Started", style="dim"), str(not_started))

    console.print(table)
    console.print()


def success(message: str) -> None:
    """Print a success message in green."""
    console = get_console()
    console.print(f"[green]✅ {message}[/green]")


def warning(message: str) -> None:
    """Print a warning message in yellow."""
    console = get_console()
    console.print(f"[yellow]⚠️  {message}[/yellow]")


def error(message: str) -> None:
    """Print an error message in red."""
    console = get_console()
    console.print(f"[red]❌ {message}[/red]")


def info(message: str) -> None:
    """Print an info message in blue."""
    console = get_console()
    console.print(f"[blue]ℹ️  {message}[/blue]")
