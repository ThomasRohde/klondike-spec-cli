"""Git integration for klondike session management.

Provides git-related utilities for session start/end and status.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class GitStatus:
    """Status of a git repository."""

    is_git_repo: bool = False
    has_uncommitted_changes: bool = False
    staged_count: int = 0
    unstaged_count: int = 0
    untracked_count: int = 0
    current_branch: str | None = None
    error: str | None = None

    @property
    def clean(self) -> bool:
        """Check if the repository is clean (no uncommitted changes)."""
        return not self.has_uncommitted_changes


@dataclass
class GitCommit:
    """Represents a git commit."""

    hash: str
    short_hash: str
    message: str
    author: str
    date: str


def is_git_installed() -> bool:
    """Check if git is installed and available."""
    try:
        result = subprocess.run(
            ["git", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def is_git_repo(path: Path | None = None) -> bool:
    """Check if the path is inside a git repository.

    Args:
        path: Path to check, defaults to current directory

    Returns:
        True if inside a git repo
    """
    cwd = path or Path.cwd()
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=5,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def get_git_status(path: Path | None = None) -> GitStatus:
    """Get the current git status.

    Args:
        path: Path to check, defaults to current directory

    Returns:
        GitStatus with repository state information
    """
    cwd = path or Path.cwd()

    if not is_git_installed():
        return GitStatus(error="Git is not installed")

    if not is_git_repo(cwd):
        return GitStatus(error="Not a git repository")

    status = GitStatus(is_git_repo=True)

    # Get current branch
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=5,
        )
        if result.returncode == 0:
            status.current_branch = result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Get porcelain status for counting
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=10,
        )
        if result.returncode == 0:
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                status.has_uncommitted_changes = True
                index_status = line[0]
                worktree_status = line[1]

                if index_status != " " and index_status != "?":
                    status.staged_count += 1
                if worktree_status != " " and worktree_status != "?":
                    status.unstaged_count += 1
                if index_status == "?" and worktree_status == "?":
                    status.untracked_count += 1
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    return status


def get_recent_commits(count: int = 5, path: Path | None = None) -> list[GitCommit]:
    """Get recent git commits.

    Args:
        count: Number of commits to retrieve
        path: Path to check, defaults to current directory

    Returns:
        List of recent commits
    """
    cwd = path or Path.cwd()
    commits: list[GitCommit] = []

    if not is_git_repo(cwd):
        return commits

    try:
        # Format: hash|short_hash|message|author|date
        result = subprocess.run(
            [
                "git",
                "log",
                f"-{count}",
                "--format=%H|%h|%s|%an|%ad",
                "--date=short",
            ],
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=10,
        )
        if result.returncode == 0:
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                parts = line.split("|", 4)
                if len(parts) >= 5:
                    commits.append(
                        GitCommit(
                            hash=parts[0],
                            short_hash=parts[1],
                            message=parts[2],
                            author=parts[3],
                            date=parts[4],
                        )
                    )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    return commits


def git_add_all(path: Path | None = None) -> bool:
    """Add all changes to git staging.

    Args:
        path: Path to repository, defaults to current directory

    Returns:
        True if successful
    """
    cwd = path or Path.cwd()
    try:
        result = subprocess.run(
            ["git", "add", "-A"],
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=10,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def git_commit(message: str, path: Path | None = None) -> tuple[bool, str]:
    """Create a git commit.

    Args:
        message: Commit message
        path: Path to repository, defaults to current directory

    Returns:
        Tuple of (success, output/error message)
    """
    cwd = path or Path.cwd()
    try:
        result = subprocess.run(
            ["git", "commit", "-m", message],
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=30,
        )
        if result.returncode == 0:
            return True, result.stdout.strip()
        else:
            return False, result.stderr.strip() or result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        return False, str(e)


def format_git_status(status: GitStatus) -> str:
    """Format git status for display.

    Args:
        status: The git status to format

    Returns:
        Formatted string for display
    """
    if not status.is_git_repo:
        return status.error or "Not a git repository"

    if status.clean:
        return f"✅ Clean (branch: {status.current_branch})"

    parts = []
    if status.staged_count:
        parts.append(f"{status.staged_count} staged")
    if status.unstaged_count:
        parts.append(f"{status.unstaged_count} modified")
    if status.untracked_count:
        parts.append(f"{status.untracked_count} untracked")

    changes = ", ".join(parts)
    return f"⚠️  Uncommitted changes: {changes} (branch: {status.current_branch})"


def format_git_log(commits: list[GitCommit], max_msg_len: int = 50) -> str:
    """Format git log for display.

    Args:
        commits: List of commits to format
        max_msg_len: Maximum message length before truncation

    Returns:
        Formatted string for display
    """
    if not commits:
        return "No commits found"

    lines = []
    for commit in commits:
        msg = commit.message
        if len(msg) > max_msg_len:
            msg = msg[: max_msg_len - 3] + "..."
        lines.append(f"  {commit.short_hash} {commit.date} {msg}")

    return "\n".join(lines)


def git_push(path: Path | None = None) -> tuple[bool, str]:
    """Push commits to remote.

    Args:
        path: Path to repository, defaults to current directory

    Returns:
        Tuple of (success, output/error message)
    """
    cwd = path or Path.cwd()
    try:
        result = subprocess.run(
            ["git", "push"],
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=60,
        )
        if result.returncode == 0:
            return True, result.stdout.strip() or result.stderr.strip()
        else:
            return False, result.stderr.strip() or result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        return False, str(e)


def git_tag(tag: str, message: str | None = None, path: Path | None = None) -> tuple[bool, str]:
    """Create a git tag.

    Args:
        tag: Tag name (e.g., "v0.2.0")
        message: Optional tag message (creates annotated tag if provided)
        path: Path to repository, defaults to current directory

    Returns:
        Tuple of (success, output/error message)
    """
    cwd = path or Path.cwd()
    try:
        if message:
            cmd = ["git", "tag", "-a", tag, "-m", message]
        else:
            cmd = ["git", "tag", tag]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=10,
        )
        if result.returncode == 0:
            return True, f"Created tag {tag}"
        else:
            return False, result.stderr.strip() or result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        return False, str(e)


def git_push_tag(tag: str, path: Path | None = None) -> tuple[bool, str]:
    """Push a specific tag to remote.

    Args:
        tag: Tag name to push
        path: Path to repository, defaults to current directory

    Returns:
        Tuple of (success, output/error message)
    """
    cwd = path or Path.cwd()
    try:
        result = subprocess.run(
            ["git", "push", "origin", tag],
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=60,
        )
        if result.returncode == 0:
            return True, result.stdout.strip() or result.stderr.strip()
        else:
            return False, result.stderr.strip() or result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        return False, str(e)


def get_tags(path: Path | None = None) -> list[str]:
    """Get list of git tags.

    Args:
        path: Path to repository, defaults to current directory

    Returns:
        List of tag names, sorted by version
    """
    cwd = path or Path.cwd()
    try:
        result = subprocess.run(
            ["git", "tag", "--sort=-v:refname"],
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=10,
        )
        if result.returncode == 0:
            return [t for t in result.stdout.strip().split("\n") if t]
        return []
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []
