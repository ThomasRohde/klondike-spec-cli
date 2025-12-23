"""Agents command - generate AGENTS.md from configuration."""

from datetime import datetime
from pathlib import Path

from pith import PithException, echo

from ..data import get_klondike_dir, load_config, load_features, load_progress


def agents_generate_command() -> None:
    """Generate AGENTS.md based on klondike configuration and project state.

    Creates AGENTS.md in the repository root with basic agent workflow and context.
    """
    root = Path.cwd()
    klondike_dir = get_klondike_dir(root)
    if not klondike_dir:
        raise PithException("Not in a Klondike project. Run 'klondike init' first.")

    registry = load_features(root)
    progress = load_progress(root)
    config = load_config(root)

    lines: list[str] = []
    lines.append(f"# {registry.project_name} — Agents Guide")
    lines.append("")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")
    lines.append("## Workflow Overview")
    lines.append("- Use klondike CLI to manage features and sessions")
    lines.append("- Do not edit .klondike JSON files directly; use CLI commands")
    lines.append("- Keep one feature in progress at a time")
    lines.append("")
    lines.append("## Key Commands")
    lines.append("```bash")
    lines.append("klondike status")
    lines.append("klondike feature list")
    lines.append('klondike session start --focus "F00X - description"')
    lines.append("klondike feature start F00X")
    lines.append("```")
    lines.append("")
    lines.append("## Configuration")
    lines.append(f"- default_category: {config.default_category}")
    lines.append(f"- default_priority: {config.default_priority}")
    lines.append(f"- verified_by: {config.verified_by}")
    lines.append(f"- progress_output_path: {config.progress_output_path}")
    lines.append("")
    lines.append("## Current Priority Features")
    for pf in progress.quick_reference.priority_features:
        lines.append(f"- {pf.id}: {pf.description} ({pf.status})")

    output_path = root / "AGENTS.md"
    output_path.write_text("\n".join(lines), encoding="utf-8")
    echo(f"✅ Generated {output_path}")
