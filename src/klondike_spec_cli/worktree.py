"""Git worktree management for isolated agent sessions.

Provides git worktree operations for running AI agents in isolated branches,
following patterns from FleetCode (https://github.com/built-by-as/FleetCode).

Directory structure:
    ~/klondike-worktrees/
    └── <project-name>/
        ├── .klondike-project          # Marker file with original project path
        └── <session-name>-<uuid>/     # Worktree for session
            └── <full project copy>
"""

from __future__ import annotations

import hashlib
import subprocess
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

# Default worktree base directory
DEFAULT_WORKTREE_BASE = Path.home() / "klondike-worktrees"

# Marker file to track which project owns a worktree directory
PROJECT_MARKER_FILE = ".klondike-project"

# Prefix for klondike-managed branches
BRANCH_PREFIX = "klondike"


@dataclass
class WorktreeConfig:
    """Configuration for creating a worktree."""

    project_dir: Path
    parent_branch: str | None = None  # None = use current branch
    session_name: str | None = None  # None = auto-generate
    feature_id: str | None = None  # If working on a specific feature
    worktree_base: Path | None = None  # None = use ~/klondike-worktrees

    def get_worktree_base(self) -> Path:
        """Get the worktree base directory."""
        return self.worktree_base or DEFAULT_WORKTREE_BASE


@dataclass
class WorktreeInfo:
    """Information about a created or existing worktree."""

    worktree_path: Path
    branch_name: str
    parent_branch: str
    session_id: str
    created_at: str
    project_dir: Path
    feature_id: str | None = None
    is_active: bool = True

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "worktree_path": str(self.worktree_path),
            "branch_name": self.branch_name,
            "parent_branch": self.parent_branch,
            "session_id": self.session_id,
            "created_at": self.created_at,
            "project_dir": str(self.project_dir),
            "feature_id": self.feature_id,
            "is_active": self.is_active,
        }

    @classmethod
    def from_dict(cls, data: dict) -> WorktreeInfo:
        """Create from dictionary."""
        return cls(
            worktree_path=Path(data["worktree_path"]),
            branch_name=data["branch_name"],
            parent_branch=data["parent_branch"],
            session_id=data["session_id"],
            created_at=data["created_at"],
            project_dir=Path(data["project_dir"]),
            feature_id=data.get("feature_id"),
            is_active=data.get("is_active", True),
        )


@dataclass
class WorktreeError(Exception):
    """Error during worktree operations."""

    message: str
    details: str | None = None

    def __str__(self) -> str:
        if self.details:
            return f"{self.message}: {self.details}"
        return self.message


def get_worktree_base() -> Path:
    """Get the default base directory for all worktrees."""
    return DEFAULT_WORKTREE_BASE


def get_project_name(project_dir: Path) -> str:
    """Get the project name from directory, handling collisions.

    If the project name already exists for a different project,
    appends a hash suffix to avoid conflicts.
    """
    base_name = project_dir.name
    worktree_base = get_worktree_base()
    project_worktree_dir = worktree_base / base_name

    # If directory doesn't exist yet, use base name
    if not project_worktree_dir.exists():
        return base_name

    # Check if it's the same project
    marker_path = project_worktree_dir / PROJECT_MARKER_FILE
    if marker_path.exists():
        existing_project = marker_path.read_text(encoding="utf-8").strip()
        if existing_project == str(project_dir.resolve()):
            return base_name

    # Different project with same name - add hash suffix
    project_hash = hashlib.md5(str(project_dir.resolve()).encode()).hexdigest()[:6]
    return f"{base_name}-{project_hash}"


def get_project_worktrees_dir(project_dir: Path) -> Path:
    """Get the worktrees directory for a specific project."""
    project_name = get_project_name(project_dir)
    return get_worktree_base() / project_name


def get_current_branch(project_dir: Path) -> str:
    """Get the current branch name."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            cwd=project_dir,
            timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        raise WorktreeError("Failed to get current branch", result.stderr.strip())
    except subprocess.TimeoutExpired as e:
        raise WorktreeError("Git command timed out") from e
    except FileNotFoundError as e:
        raise WorktreeError("Git is not installed") from e


def generate_branch_name(
    feature_id: str | None = None,
    session_name: str | None = None,
    session_uuid: str | None = None,
) -> str:
    """Generate a unique branch name for a worktree session.

    Format: klondike/<feature-id|session-name>-<uuid-prefix>
    """
    session_uuid = session_uuid or str(uuid.uuid4())
    short_uuid = session_uuid.split("-")[0]

    if feature_id:
        name_part = feature_id.lower()
    elif session_name:
        # Sanitize session name for branch
        name_part = session_name.lower().replace(" ", "-").replace("_", "-")
        # Remove non-alphanumeric except dashes
        name_part = "".join(c for c in name_part if c.isalnum() or c == "-")
    else:
        name_part = "session"

    return f"{BRANCH_PREFIX}/{name_part}-{short_uuid}"


def generate_worktree_dir_name(
    feature_id: str | None = None,
    session_name: str | None = None,
    session_uuid: str | None = None,
) -> str:
    """Generate the worktree directory name."""
    session_uuid = session_uuid or str(uuid.uuid4())
    short_uuid = session_uuid.split("-")[0]

    if feature_id:
        return f"{feature_id.lower()}-{short_uuid}"
    elif session_name:
        sanitized = session_name.lower().replace(" ", "-").replace("_", "-")
        sanitized = "".join(c for c in sanitized if c.isalnum() or c == "-")
        return f"{sanitized}-{short_uuid}"
    else:
        return f"session-{short_uuid}"


def create_worktree(config: WorktreeConfig) -> WorktreeInfo:
    """Create a new git worktree for an agent session.

    Args:
        config: Configuration for the worktree

    Returns:
        WorktreeInfo with details about the created worktree

    Raises:
        WorktreeError: If worktree creation fails
    """
    project_dir = config.project_dir.resolve()

    # Get parent branch
    parent_branch = config.parent_branch or get_current_branch(project_dir)

    # Generate unique session ID
    session_uuid = str(uuid.uuid4())

    # Generate branch and directory names
    branch_name = generate_branch_name(
        feature_id=config.feature_id,
        session_name=config.session_name,
        session_uuid=session_uuid,
    )
    worktree_dir_name = generate_worktree_dir_name(
        feature_id=config.feature_id,
        session_name=config.session_name,
        session_uuid=session_uuid,
    )

    # Create project worktrees directory
    project_worktrees_dir = get_project_worktrees_dir(project_dir)
    project_worktrees_dir.mkdir(parents=True, exist_ok=True)

    # Write project marker file
    marker_path = project_worktrees_dir / PROJECT_MARKER_FILE
    marker_path.write_text(str(project_dir), encoding="utf-8")

    # Full worktree path
    worktree_path = project_worktrees_dir / worktree_dir_name

    # Create the worktree with a new branch
    try:
        result = subprocess.run(
            ["git", "worktree", "add", "-b", branch_name, str(worktree_path), parent_branch],
            capture_output=True,
            text=True,
            cwd=project_dir,
            timeout=60,
        )
        if result.returncode != 0:
            raise WorktreeError("Failed to create worktree", result.stderr.strip())
    except subprocess.TimeoutExpired as e:
        raise WorktreeError("Git worktree command timed out") from e
    except FileNotFoundError as e:
        raise WorktreeError("Git is not installed") from e

    # Add worktree directory to project's .gitignore if not already present
    ensure_worktree_gitignore(project_dir)

    return WorktreeInfo(
        worktree_path=worktree_path,
        branch_name=branch_name,
        parent_branch=parent_branch,
        session_id=session_uuid,
        created_at=datetime.now().isoformat(),
        project_dir=project_dir,
        feature_id=config.feature_id,
    )


def remove_worktree(worktree_path: Path, project_dir: Path, force: bool = False) -> bool:
    """Remove a git worktree.

    Args:
        worktree_path: Path to the worktree to remove
        project_dir: Path to the original project directory
        force: Force removal even with uncommitted changes

    Returns:
        True if successful

    Raises:
        WorktreeError: If removal fails
    """
    cmd = ["git", "worktree", "remove", str(worktree_path)]
    if force:
        cmd.append("--force")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=project_dir,
            timeout=30,
        )
        if result.returncode != 0:
            raise WorktreeError("Failed to remove worktree", result.stderr.strip())
        return True
    except subprocess.TimeoutExpired as e:
        raise WorktreeError("Git worktree remove timed out") from e
    except FileNotFoundError as e:
        raise WorktreeError("Git is not installed") from e


def remove_branch(branch_name: str, project_dir: Path, force: bool = True) -> bool:
    """Remove a git branch.

    Args:
        branch_name: Name of the branch to remove
        project_dir: Path to the project directory
        force: Use -D instead of -d (force delete)

    Returns:
        True if successful

    Raises:
        WorktreeError: If removal fails
    """
    flag = "-D" if force else "-d"
    try:
        result = subprocess.run(
            ["git", "branch", flag, branch_name],
            capture_output=True,
            text=True,
            cwd=project_dir,
            timeout=10,
        )
        if result.returncode != 0:
            raise WorktreeError("Failed to remove branch", result.stderr.strip())
        return True
    except subprocess.TimeoutExpired as e:
        raise WorktreeError("Git branch remove timed out") from e
    except FileNotFoundError as e:
        raise WorktreeError("Git is not installed") from e


def cleanup_worktree(worktree_info: WorktreeInfo, force: bool = False) -> bool:
    """Remove a worktree and its associated branch.

    Args:
        worktree_info: Information about the worktree to clean up
        force: Force removal even with uncommitted changes

    Returns:
        True if successful
    """
    # First remove the worktree
    remove_worktree(worktree_info.worktree_path, worktree_info.project_dir, force)

    # Then remove the branch
    remove_branch(worktree_info.branch_name, worktree_info.project_dir, force=True)

    return True


def list_worktrees(project_dir: Path) -> list[WorktreeInfo]:
    """List all worktrees for a project.

    Args:
        project_dir: Path to the project directory

    Returns:
        List of WorktreeInfo for each worktree
    """
    try:
        result = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            capture_output=True,
            text=True,
            cwd=project_dir,
            timeout=10,
        )
        if result.returncode != 0:
            return []
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []

    worktrees: list[WorktreeInfo] = []
    current_worktree: dict = {}

    for line in result.stdout.strip().split("\n"):
        if not line:
            if current_worktree and current_worktree.get("branch", "").startswith(
                f"refs/heads/{BRANCH_PREFIX}/"
            ):
                # This is a klondike-managed worktree
                branch_name = current_worktree["branch"].replace("refs/heads/", "")
                worktree_path = Path(current_worktree["worktree"])

                # Try to extract session info from branch name
                parts = branch_name.split("/", 1)
                if len(parts) > 1:
                    name_parts = parts[1].rsplit("-", 1)
                    session_id = name_parts[-1] if len(name_parts) > 1 else ""
                    feature_id = None
                    if name_parts[0].upper().startswith("F") and name_parts[0][1:4].isdigit():
                        feature_id = name_parts[0].upper()
                else:
                    session_id = ""
                    feature_id = None

                worktrees.append(
                    WorktreeInfo(
                        worktree_path=worktree_path,
                        branch_name=branch_name,
                        parent_branch="",  # Not easily available from porcelain output
                        session_id=session_id,
                        created_at="",  # Not available from git
                        project_dir=project_dir,
                        feature_id=feature_id,
                    )
                )
            current_worktree = {}
        elif line.startswith("worktree "):
            current_worktree["worktree"] = line[9:]
        elif line.startswith("branch "):
            current_worktree["branch"] = line[7:]
        elif line == "bare":
            current_worktree["bare"] = True

    # Handle last worktree if no trailing newline
    if current_worktree and current_worktree.get("branch", "").startswith(
        f"refs/heads/{BRANCH_PREFIX}/"
    ):
        branch_name = current_worktree["branch"].replace("refs/heads/", "")
        worktree_path = Path(current_worktree["worktree"])
        parts = branch_name.split("/", 1)
        if len(parts) > 1:
            name_parts = parts[1].rsplit("-", 1)
            session_id = name_parts[-1] if len(name_parts) > 1 else ""
            feature_id = None
            if name_parts[0].upper().startswith("F") and name_parts[0][1:4].isdigit():
                feature_id = name_parts[0].upper()
        else:
            session_id = ""
            feature_id = None

        worktrees.append(
            WorktreeInfo(
                worktree_path=worktree_path,
                branch_name=branch_name,
                parent_branch="",
                session_id=session_id,
                created_at="",
                project_dir=project_dir,
                feature_id=feature_id,
            )
        )

    return worktrees


def get_worktree_diff(
    worktree_path: Path,
    parent_branch: str,
    exclude_patterns: list[str] | None = None,
) -> str:
    """Get the diff of changes in a worktree compared to parent branch.

    Args:
        worktree_path: Path to the worktree
        parent_branch: The parent branch to diff against
        exclude_patterns: List of path patterns to exclude (e.g., [".klondike/"])

    Returns:
        Diff content as string
    """
    # Default exclusions - klondike state files should not be patched
    if exclude_patterns is None:
        exclude_patterns = [".klondike/"]

    try:
        cmd = ["git", "diff", parent_branch]
        # Add exclusion patterns
        for pattern in exclude_patterns:
            cmd.extend(["--", f":!{pattern}"])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=worktree_path,
            timeout=30,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode == 0:
            return result.stdout or ""
        return ""
    except (subprocess.TimeoutExpired, FileNotFoundError, UnicodeDecodeError):
        return ""


def apply_worktree_changes(
    worktree_info: WorktreeInfo,
    target_dir: Path | None = None,
) -> bool:
    """Apply changes from worktree back to original project or target directory.

    Creates a patch from the worktree and applies it.

    Args:
        worktree_info: The worktree containing changes
        target_dir: Directory to apply changes to (default: original project)

    Returns:
        True if successful

    Raises:
        WorktreeError: If applying changes fails
    """
    target = target_dir or worktree_info.project_dir

    # Get the diff
    diff_content = get_worktree_diff(worktree_info.worktree_path, worktree_info.parent_branch)

    if not diff_content.strip():
        return True  # No changes to apply

    # Apply the patch
    try:
        result = subprocess.run(
            ["git", "apply", "-"],
            input=diff_content,
            capture_output=True,
            text=True,
            cwd=target,
            timeout=30,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode != 0:
            raise WorktreeError("Failed to apply changes", result.stderr.strip())
        return True
    except subprocess.TimeoutExpired as e:
        raise WorktreeError("Git apply timed out") from e
    except FileNotFoundError as e:
        raise WorktreeError("Git is not installed") from e


def ensure_worktree_gitignore(project_dir: Path) -> bool:
    """Ensure the worktree base directory is in project's .gitignore.

    Adds the klondike-worktrees directory to .gitignore if not present.

    Args:
        project_dir: Path to the project directory

    Returns:
        True if .gitignore was updated, False if already present
    """
    gitignore_path = project_dir / ".gitignore"

    # Entry to add - use home-relative path with comment
    # Since worktrees are in ~/klondike-worktrees, we don't need to ignore
    # anything in the project itself. But if someone runs from worktree base
    # or has a relative symlink, add a safety ignore.
    ignore_entries = [
        "# Klondike worktree directories (auto-generated)",
        "klondike-worktrees/",
    ]

    # Read existing gitignore
    existing_content = ""
    if gitignore_path.exists():
        existing_content = gitignore_path.read_text(encoding="utf-8")

    # Check if already ignored
    if "klondike-worktrees/" in existing_content:
        return False

    # Append to gitignore
    if existing_content and not existing_content.endswith("\n"):
        existing_content += "\n"

    new_content = existing_content + "\n".join(ignore_entries) + "\n"
    gitignore_path.write_text(new_content, encoding="utf-8")

    return True


def prune_worktrees(project_dir: Path) -> int:
    """Prune stale worktree entries.

    Args:
        project_dir: Path to the project directory

    Returns:
        Number of pruned entries
    """
    try:
        result = subprocess.run(
            ["git", "worktree", "prune", "-v"],
            capture_output=True,
            text=True,
            cwd=project_dir,
            timeout=30,
        )
        if result.returncode == 0:
            # Count lines that indicate pruning
            return len([line for line in result.stderr.split("\n") if "Removing" in line])
        return 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return 0
