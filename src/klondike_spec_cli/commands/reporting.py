"""Report command handlers."""

from datetime import datetime
from pathlib import Path

from pith import Option, echo

from klondike_spec_cli.data import load_features, load_progress
from klondike_spec_cli.models import Feature, FeatureStatus, Session


def report_command(
    format_type: str = Option("markdown", "--format", "-f", pith="Output format: markdown, plain"),
    output: str | None = Option(None, "--output", "-o", pith="Output file path"),
    include_details: bool = Option(False, "--details", "-d", pith="Include feature details"),
) -> None:
    """Generate a stakeholder-friendly progress report.

    Creates a formatted report suitable for sharing with stakeholders,
    showing overall progress, completed features, and next steps.

    Examples:
        $ klondike report
        $ klondike report --format plain
        $ klondike report --output report.md --details

    Related:
        status - Quick status check
        progress - Regenerate agent-progress.md
    """
    registry = load_features()
    progress_log = load_progress()

    # Calculate metrics
    total = registry.metadata.total_features
    passing = registry.metadata.passing_features
    progress_pct = round(passing / total * 100, 1) if total > 0 else 0

    # Get current session
    current_session = progress_log.get_current_session()

    # Get features by status
    verified = registry.get_features_by_status(FeatureStatus.VERIFIED)
    in_progress = registry.get_features_by_status(FeatureStatus.IN_PROGRESS)
    blocked = registry.get_features_by_status(FeatureStatus.BLOCKED)
    not_started = registry.get_features_by_status(FeatureStatus.NOT_STARTED)

    # Get priority features for next steps
    priority = registry.get_priority_features(5)

    if format_type == "markdown":
        report_content = generate_markdown_report(
            registry.project_name,
            registry.version,
            total,
            passing,
            progress_pct,
            verified,
            in_progress,
            blocked,
            not_started,
            priority,
            current_session,
            include_details,
        )
    else:
        report_content = generate_plain_report(
            registry.project_name,
            registry.version,
            total,
            passing,
            progress_pct,
            verified,
            in_progress,
            blocked,
            not_started,
            priority,
            current_session,
            include_details,
        )

    if output:
        output_path = Path(output)
        output_path.write_text(report_content, encoding="utf-8")
        echo(f"✅ Report saved to {output_path}")
    else:
        echo(report_content)


def generate_markdown_report(
    project_name: str,
    version: str,
    total: int,
    passing: int,
    progress_pct: float,
    verified: list[Feature],
    in_progress: list[Feature],
    blocked: list[Feature],
    not_started: list[Feature],
    priority: list[Feature],
    current_session: Session | None,
    include_details: bool,
) -> str:
    """Generate a markdown-formatted stakeholder report."""
    lines = [
        f"# {project_name} - Progress Report",
        "",
        f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"**Version**: {version}",
        "",
        "---",
        "",
        "## Executive Summary",
        "",
        f"**Overall Progress**: {passing}/{total} features complete ({progress_pct}%)",
        "",
        "```",
        generate_progress_bar(progress_pct),
        "```",
        "",
        "### Status Breakdown",
        "",
        "| Status | Count |",
        "|--------|-------|",
        f"| ✅ Verified | {len(verified)} |",
        f"| 🔄 In Progress | {len(in_progress)} |",
        f"| 🚫 Blocked | {len(blocked)} |",
        f"| ⏳ Not Started | {len(not_started)} |",
        "",
    ]

    if current_session:
        lines.extend(
            [
                "---",
                "",
                "## Current Session",
                "",
                f"**Focus**: {current_session.focus}",
                f"**Date**: {current_session.date}",
                "",
            ]
        )
        if current_session.completed:
            lines.append("### Completed This Session")
            lines.append("")
            for item in current_session.completed:
                lines.append(f"- {item}")
            lines.append("")

    if verified:
        lines.extend(
            [
                "---",
                "",
                "## Completed Features",
                "",
            ]
        )
        if include_details:
            for f in verified:
                lines.append(f"### {f.id}: {f.description}")
                lines.append("")
                if f.acceptance_criteria:
                    for ac in f.acceptance_criteria:
                        lines.append(f"- [x] {ac}")
                lines.append("")
        else:
            for f in verified:
                lines.append(f"- **{f.id}**: {f.description}")
            lines.append("")

    if in_progress:
        lines.extend(
            [
                "---",
                "",
                "## In Progress",
                "",
            ]
        )
        for f in in_progress:
            lines.append(f"- **{f.id}**: {f.description}")
        lines.append("")

    if blocked:
        lines.extend(
            [
                "---",
                "",
                "## Blocked",
                "",
            ]
        )
        for f in blocked:
            reason = f.blocked_by if f.blocked_by else "No reason specified"
            lines.append(f"- **{f.id}**: {f.description}")
            lines.append(f"  - *Reason*: {reason}")
        lines.append("")

    if priority:
        lines.extend(
            [
                "---",
                "",
                "## Next Steps",
                "",
                "Priority features to be implemented:",
                "",
            ]
        )
        for i, f in enumerate(priority, 1):
            lines.append(f"{i}. **{f.id}**: {f.description}")
        lines.append("")

    lines.extend(
        [
            "---",
            "",
            "*Report generated by klondike-spec-cli*",
        ]
    )

    return "\n".join(lines)


def generate_plain_report(
    project_name: str,
    version: str,
    total: int,
    passing: int,
    progress_pct: float,
    verified: list[Feature],
    in_progress: list[Feature],
    blocked: list[Feature],
    not_started: list[Feature],
    priority: list[Feature],
    current_session: Session | None,
    include_details: bool,
) -> str:
    """Generate a plain text stakeholder report."""
    lines = [
        f"{project_name} - Progress Report",
        "=" * 50,
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"Version: {version}",
        "",
        "EXECUTIVE SUMMARY",
        "-" * 30,
        "",
        f"Overall Progress: {passing}/{total} features ({progress_pct}%)",
        "",
        generate_progress_bar(progress_pct),
        "",
        "Status Breakdown:",
        f"  Verified:     {len(verified)}",
        f"  In Progress:  {len(in_progress)}",
        f"  Blocked:      {len(blocked)}",
        f"  Not Started:  {len(not_started)}",
        "",
    ]

    if current_session:
        lines.extend(
            [
                "CURRENT SESSION",
                "-" * 30,
                "",
                f"Focus: {current_session.focus}",
                f"Date: {current_session.date}",
                "",
            ]
        )
        if current_session.completed:
            lines.append("Completed This Session:")
            for item in current_session.completed:
                lines.append(f"  - {item}")
            lines.append("")

    if verified:
        lines.extend(
            [
                "COMPLETED FEATURES",
                "-" * 30,
                "",
            ]
        )
        for f in verified:
            lines.append(f"  [{f.id}] {f.description}")
        lines.append("")

    if in_progress:
        lines.extend(
            [
                "IN PROGRESS",
                "-" * 30,
                "",
            ]
        )
        for f in in_progress:
            lines.append(f"  [{f.id}] {f.description}")
        lines.append("")

    if blocked:
        lines.extend(
            [
                "BLOCKED",
                "-" * 30,
                "",
            ]
        )
        for f in blocked:
            reason = f.blocked_by if f.blocked_by else "No reason specified"
            lines.append(f"  [{f.id}] {f.description}")
            lines.append(f"         Reason: {reason}")
        lines.append("")

    if priority:
        lines.extend(
            [
                "NEXT STEPS",
                "-" * 30,
                "",
            ]
        )
        for i, f in enumerate(priority, 1):
            lines.append(f"  {i}. [{f.id}] {f.description}")
        lines.append("")

    return "\n".join(lines)


def generate_progress_bar(percentage: float, width: int = 40) -> str:
    """Generate an ASCII progress bar."""
    filled = int(width * percentage / 100)
    empty = width - filled
    bar = "█" * filled + "░" * empty
    return f"[{bar}] {percentage}%"
