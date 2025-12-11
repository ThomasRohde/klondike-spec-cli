"""Copilot command handlers for Klondike Spec CLI."""

from __future__ import annotations

from pith import echo

from ..copilot import (
    CopilotConfig,
    cleanup_copilot_worktrees,
    launch_copilot,
    list_copilot_worktrees,
)
from ..data import load_features


def copilot_start(
    model: str | None,
    resume: bool,
    feature_id: str | None,
    instructions: str | None,
    allow_tools: str | None,
    dry_run: bool,
    use_worktree: bool = False,
    parent_branch: str | None = None,
    session_name: str | None = None,
    cleanup_after: bool = False,
    apply_changes: bool = False,
) -> None:
    """Launch GitHub Copilot CLI with project context.

    Args:
        model: Model to use (e.g., claude-sonnet, gpt-4)
        resume: Resume previous session
        feature_id: Focus on specific feature
        instructions: Additional instructions
        allow_tools: Comma-separated list of allowed tools
        dry_run: Show command without executing
        use_worktree: Run in isolated git worktree
        parent_branch: Parent branch for worktree (default: current)
        session_name: Custom session/branch name for worktree
        cleanup_after: Remove worktree after session ends
        apply_changes: Apply worktree changes to main project after session
    """
    registry = load_features()

    config = CopilotConfig(
        model=model,
        resume=resume,
        feature_id=feature_id,
        instructions=instructions,
        allow_tools=allow_tools,
        dry_run=dry_run,
        use_worktree=use_worktree,
        parent_branch=parent_branch,
        session_name=session_name,
        cleanup_after=cleanup_after,
        apply_changes=apply_changes,
    )

    launch_copilot(config, registry)


def copilot_list_worktrees() -> None:
    """List all copilot worktree sessions."""
    worktrees = list_copilot_worktrees()

    if not worktrees:
        echo("No active worktree sessions found.")
        echo("")
        echo("💡 Start a worktree session with: klondike copilot start --worktree")
        return

    echo(f"🌳 Active Worktree Sessions ({len(worktrees)} total)")
    echo("")

    for wt in worktrees:
        echo(f"   📂 {wt.worktree_path}")
        echo(f"      Branch: {wt.branch_name}")
        if wt.feature_id:
            echo(f"      Feature: {wt.feature_id}")
        echo("")


def copilot_cleanup_worktrees(force: bool = False) -> None:
    """Cleanup all copilot worktree sessions."""
    worktrees = list_copilot_worktrees()

    if not worktrees:
        echo("No active worktree sessions to clean up.")
        return

    echo(f"🧹 Cleaning up {len(worktrees)} worktree session(s)...")
    echo("")

    cleaned = cleanup_copilot_worktrees(force=force)

    echo("")
    echo(f"✅ Cleaned up {cleaned} worktree session(s)")
