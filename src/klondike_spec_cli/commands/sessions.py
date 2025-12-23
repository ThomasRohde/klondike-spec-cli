"""Session command handlers for Klondike Spec CLI."""

from __future__ import annotations

from datetime import datetime

from pith import PithException, echo

from ..data import (
    load_config,
    load_features,
    load_progress,
    regenerate_progress_md,
    save_features,
    save_progress,
    update_quick_reference,
)
from ..models import Session
from ..ntfy import get_ntfy_client


def session_start(focus: str | None) -> None:
    """Start a new session."""
    from klondike_spec_cli.git import format_git_status, get_git_status

    registry = load_features()
    progress = load_progress()

    # Check git status first
    echo("🔍 Checking git status...")
    git_status = get_git_status()
    if git_status.is_git_repo:
        echo(f"   {format_git_status(git_status)}")
        if git_status.has_uncommitted_changes:
            echo("   ⚠️  Consider committing or stashing changes before starting.")
    else:
        echo("   ℹ️  Not a git repository")
    echo("")

    # Validate artifact integrity
    echo("🔍 Validating artifacts...")

    # Check metadata consistency
    actual_total = len(registry.features)
    actual_passing = sum(1 for f in registry.features if f.passes)

    if registry.metadata.total_features != actual_total:
        echo(
            f"⚠️  Warning: metadata.totalFeatures ({registry.metadata.total_features}) != actual ({actual_total})"
        )
        registry.metadata.total_features = actual_total

    if registry.metadata.passing_features != actual_passing:
        echo(
            f"⚠️  Warning: metadata.passingFeatures ({registry.metadata.passing_features}) != actual ({actual_passing})"
        )
        registry.metadata.passing_features = actual_passing

    echo("✅ Artifacts validated")
    echo("")

    # Create new session
    session_num = progress.next_session_number()
    new_session = Session(
        session_number=session_num,
        date=datetime.now().strftime("%Y-%m-%d"),
        agent="Coding Agent",
        duration="(in progress)",
        focus=focus or "General development",
        completed=[],
        in_progress=["Session started"],
        blockers=[],
        next_steps=[],
        technical_notes=[],
    )

    progress.add_session(new_session)
    progress.current_status = "In Progress"

    update_quick_reference(progress, registry)
    save_features(registry)
    save_progress(progress)
    regenerate_progress_md()

    # Show status
    total = registry.metadata.total_features
    passing = registry.metadata.passing_features
    progress_pct = round(passing / total * 100, 1) if total > 0 else 0

    echo(f"🚀 Session {session_num} Started")
    echo(f"   Focus: {new_session.focus}")
    echo("")
    echo(f"📊 Project Status: {passing}/{total} features ({progress_pct}%)")

    # Show priority features
    priority = registry.get_priority_features(3)
    if priority:
        echo("")
        echo("♠️  Priority Features:")
        for f in priority:
            echo(f"   • {f.id}: {f.description}")

    echo("")
    echo("💡 Tip: Use 'klondike feature start <ID>' to mark a feature as in-progress")

    # Send notification
    config = load_config()
    ntfy_client = get_ntfy_client(config.ntfy)
    if ntfy_client:
        ntfy_client.session_started(session_num, new_session.focus)


def session_end(
    summary: str | None,
    completed: str | None,
    blockers: str | None,
    next_steps: str | None,
    auto_commit: bool = False,
) -> None:
    """End current session."""
    from klondike_spec_cli.git import (
        format_git_status,
        get_git_status,
        git_add_all,
        git_commit,
    )

    registry = load_features()
    progress = load_progress()

    current = progress.get_current_session()
    if not current:
        raise PithException("No active session found. Use 'klondike session start' first.")

    # Update session
    current.duration = "~session"  # TODO: Calculate actual duration
    current.in_progress = []

    if summary:
        current.focus = summary

    if completed:
        current.completed = [c.strip() for c in completed.split(",")]

    if blockers:
        current.blockers = [b.strip() for b in blockers.split(",")]

    if next_steps:
        current.next_steps = [n.strip() for n in next_steps.split(",")]
    else:
        # Auto-generate next steps from priority features
        priority = registry.get_priority_features(3)
        current.next_steps = [f"Continue {f.id}: {f.description}" for f in priority]

    progress.current_status = "Session Ended"
    update_quick_reference(progress, registry)
    save_progress(progress)
    regenerate_progress_md()

    echo(f"✅ Session {current.session_number} Ended")
    echo(f"   Focus: {current.focus}")

    if current.completed:
        echo("   Completed:")
        for item in current.completed:
            echo(f"     • {item}")

    # Check git status and optionally auto-commit
    git_status = get_git_status()
    if git_status.is_git_repo:
        echo("")
        echo(f"📂 Git: {format_git_status(git_status)}")

        if git_status.has_uncommitted_changes:
            if auto_commit:
                # Auto-commit with session summary
                commit_msg = f"chore(session): end session {current.session_number}"
                if summary:
                    commit_msg += f"\n\n{summary}"
                git_add_all()
                success, result = git_commit(commit_msg)
                if success:
                    echo("   ✅ Auto-committed changes")
                else:
                    echo(f"   ⚠️  Auto-commit failed: {result}")
            else:
                echo("   💡 Use --auto-commit to commit changes automatically")
    echo("")

    # Send notification
    config = load_config()
    ntfy_client = get_ntfy_client(config.ntfy)
    if ntfy_client:
        features_completed = len(current.completed) if current.completed else 0
        ntfy_client.session_ended(current.session_number, current.focus, features_completed)
