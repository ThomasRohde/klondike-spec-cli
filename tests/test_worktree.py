"""Tests for worktree module."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from klondike_spec_cli.worktree import (
    BRANCH_PREFIX,
    DEFAULT_WORKTREE_BASE,
    PROJECT_MARKER_FILE,
    WorktreeConfig,
    WorktreeError,
    WorktreeInfo,
    ensure_worktree_gitignore,
    generate_branch_name,
    generate_worktree_dir_name,
    get_current_branch,
    get_project_name,
    get_project_worktrees_dir,
    get_worktree_base,
)


class TestWorktreeConstants:
    """Tests for worktree constants."""

    def test_default_worktree_base(self) -> None:
        """Test default worktree base is in home directory."""
        assert DEFAULT_WORKTREE_BASE == Path.home() / "klondike-worktrees"

    def test_branch_prefix(self) -> None:
        """Test branch prefix."""
        assert BRANCH_PREFIX == "klondike"

    def test_project_marker_file(self) -> None:
        """Test project marker file name."""
        assert PROJECT_MARKER_FILE == ".klondike-project"


class TestWorktreeConfig:
    """Tests for WorktreeConfig dataclass."""

    def test_worktree_config_defaults(self) -> None:
        """Test WorktreeConfig with defaults."""
        config = WorktreeConfig(project_dir=Path("/test/project"))
        assert config.project_dir == Path("/test/project")
        assert config.parent_branch is None
        assert config.session_name is None
        assert config.feature_id is None
        assert config.worktree_base is None

    def test_worktree_config_get_base(self) -> None:
        """Test get_worktree_base method."""
        config = WorktreeConfig(project_dir=Path("/test/project"))
        assert config.get_worktree_base() == DEFAULT_WORKTREE_BASE

        custom_base = Path("/custom/worktrees")
        config_custom = WorktreeConfig(
            project_dir=Path("/test/project"),
            worktree_base=custom_base,
        )
        assert config_custom.get_worktree_base() == custom_base


class TestWorktreeInfo:
    """Tests for WorktreeInfo dataclass."""

    def test_worktree_info_to_dict(self) -> None:
        """Test WorktreeInfo serialization."""
        info = WorktreeInfo(
            worktree_path=Path("/worktrees/project/session-abc"),
            branch_name="klondike/session-abc",
            parent_branch="main",
            session_id="abc123",
            created_at="2025-01-01T00:00:00",
            project_dir=Path("/projects/myproject"),
            feature_id="F001",
        )
        d = info.to_dict()
        # Path is converted to string with OS-specific separators
        assert "worktrees" in d["worktree_path"]
        assert "session-abc" in d["worktree_path"]
        assert d["branch_name"] == "klondike/session-abc"
        assert d["parent_branch"] == "main"
        assert d["feature_id"] == "F001"

    def test_worktree_info_from_dict(self) -> None:
        """Test WorktreeInfo deserialization."""
        d = {
            "worktree_path": "/worktrees/project/session-abc",
            "branch_name": "klondike/session-abc",
            "parent_branch": "main",
            "session_id": "abc123",
            "created_at": "2025-01-01T00:00:00",
            "project_dir": "/projects/myproject",
            "feature_id": "F001",
        }
        info = WorktreeInfo.from_dict(d)
        assert info.worktree_path == Path("/worktrees/project/session-abc")
        assert info.branch_name == "klondike/session-abc"
        assert info.feature_id == "F001"


class TestWorktreeError:
    """Tests for WorktreeError exception."""

    def test_error_message_only(self) -> None:
        """Test error with message only."""
        err = WorktreeError("Failed to create")
        assert str(err) == "Failed to create"

    def test_error_with_details(self) -> None:
        """Test error with message and details."""
        err = WorktreeError("Failed to create", "Branch already exists")
        assert str(err) == "Failed to create: Branch already exists"


class TestBranchNaming:
    """Tests for branch naming functions."""

    def test_generate_branch_name_with_feature(self) -> None:
        """Test branch name with feature ID."""
        name = generate_branch_name(feature_id="F001", session_uuid="abc-123-def")
        assert name == "klondike/f001-abc"

    def test_generate_branch_name_with_session(self) -> None:
        """Test branch name with session name."""
        name = generate_branch_name(session_name="my-session", session_uuid="xyz-789")
        assert name == "klondike/my-session-xyz"

    def test_generate_branch_name_sanitizes_session(self) -> None:
        """Test branch name sanitizes special chars."""
        # Spaces become dashes, exclamation marks removed
        name = generate_branch_name(session_name="My Cool Session!", session_uuid="abc-123")
        assert name == "klondike/my-cool-session-abc"

    def test_generate_branch_name_default(self) -> None:
        """Test default branch name."""
        name = generate_branch_name(session_uuid="test-uuid")
        assert name == "klondike/session-test"

    def test_generate_worktree_dir_name_feature(self) -> None:
        """Test worktree dir name with feature."""
        name = generate_worktree_dir_name(feature_id="F042", session_uuid="abc-123")
        assert name == "f042-abc"

    def test_generate_worktree_dir_name_session(self) -> None:
        """Test worktree dir name with session."""
        name = generate_worktree_dir_name(session_name="dev work", session_uuid="xyz-789")
        assert name == "dev-work-xyz"


class TestGitIgnore:
    """Tests for gitignore handling."""

    def test_ensure_worktree_gitignore_creates(self) -> None:
        """Test creating gitignore entry."""
        with TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            result = ensure_worktree_gitignore(project_dir)
            assert result is True

            gitignore = project_dir / ".gitignore"
            assert gitignore.exists()
            content = gitignore.read_text()
            assert "klondike-worktrees/" in content

    def test_ensure_worktree_gitignore_appends(self) -> None:
        """Test appending to existing gitignore."""
        with TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            gitignore = project_dir / ".gitignore"
            gitignore.write_text("node_modules/\n.env\n")

            result = ensure_worktree_gitignore(project_dir)
            assert result is True

            content = gitignore.read_text()
            assert "node_modules/" in content
            assert "klondike-worktrees/" in content

    def test_ensure_worktree_gitignore_idempotent(self) -> None:
        """Test that function is idempotent."""
        with TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)

            # First call
            result1 = ensure_worktree_gitignore(project_dir)
            assert result1 is True

            # Second call should not add again
            result2 = ensure_worktree_gitignore(project_dir)
            assert result2 is False

            content = (project_dir / ".gitignore").read_text()
            assert content.count("klondike-worktrees/") == 1


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_get_worktree_base(self) -> None:
        """Test get_worktree_base returns default."""
        assert get_worktree_base() == DEFAULT_WORKTREE_BASE

    def test_get_project_name_simple(self) -> None:
        """Test project name from path."""
        # Use a path that won't conflict
        project_path = Path("/nonexistent/unique-project-name-12345")
        name = get_project_name(project_path)
        assert name == "unique-project-name-12345"

    def test_get_project_worktrees_dir(self) -> None:
        """Test getting project worktrees directory."""
        project_path = Path("/nonexistent/my-project-xyz")
        worktrees_dir = get_project_worktrees_dir(project_path)
        assert worktrees_dir.name == "my-project-xyz"
        assert worktrees_dir.parent == DEFAULT_WORKTREE_BASE


class TestGetCurrentBranch:
    """Tests for get_current_branch function."""

    def test_get_current_branch_real_repo(self) -> None:
        """Test getting current branch in real repo."""
        # Current project is a git repo
        branch = get_current_branch(Path.cwd())
        assert isinstance(branch, str)
        assert len(branch) > 0

    def test_get_current_branch_not_git_repo(self) -> None:
        """Test getting current branch in non-repo raises error."""
        with TemporaryDirectory() as tmpdir:
            with pytest.raises(WorktreeError):
                get_current_branch(Path(tmpdir))
