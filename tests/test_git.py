"""Tests for git integration module."""

from pathlib import Path
from tempfile import TemporaryDirectory

from klondike_spec_cli.git import (
    GitCommit,
    GitStatus,
    format_git_log,
    format_git_status,
    get_git_status,
    get_recent_commits,
    get_tags,
    is_git_installed,
    is_git_repo,
)


class TestGitDetection:
    """Tests for git detection functions."""

    def test_is_git_installed(self) -> None:
        """Test git installation detection."""
        # This should work in most CI/development environments
        result = is_git_installed()
        assert isinstance(result, bool)

    def test_is_git_repo_current_dir(self) -> None:
        """Test git repo detection on current project."""
        # The klondike project itself is a git repo
        result = is_git_repo()
        assert result is True

    def test_is_git_repo_non_repo(self) -> None:
        """Test git repo detection on non-repo directory."""
        with TemporaryDirectory() as tmpdir:
            result = is_git_repo(Path(tmpdir))
            assert result is False


class TestGitStatus:
    """Tests for git status functions."""

    def test_git_status_dataclass(self) -> None:
        """Test GitStatus dataclass properties."""
        status = GitStatus(is_git_repo=True, has_uncommitted_changes=False)
        assert status.clean is True

        status_dirty = GitStatus(is_git_repo=True, has_uncommitted_changes=True)
        assert status_dirty.clean is False

    def test_get_git_status_non_repo(self) -> None:
        """Test git status on non-repo directory."""
        with TemporaryDirectory() as tmpdir:
            status = get_git_status(Path(tmpdir))
            assert status.is_git_repo is False
            assert status.error == "Not a git repository"

    def test_get_git_status_current_repo(self) -> None:
        """Test git status on current project."""
        status = get_git_status()
        assert status.is_git_repo is True
        assert status.current_branch is not None


class TestGitFormatting:
    """Tests for git formatting functions."""

    def test_format_git_status_clean(self) -> None:
        """Test formatting clean status."""
        status = GitStatus(
            is_git_repo=True,
            has_uncommitted_changes=False,
            current_branch="main",
        )
        result = format_git_status(status)
        assert "Clean" in result
        assert "main" in result

    def test_format_git_status_dirty(self) -> None:
        """Test formatting dirty status."""
        status = GitStatus(
            is_git_repo=True,
            has_uncommitted_changes=True,
            staged_count=2,
            unstaged_count=1,
            current_branch="feature",
        )
        result = format_git_status(status)
        assert "Uncommitted" in result
        assert "2 staged" in result
        assert "1 modified" in result

    def test_format_git_status_non_repo(self) -> None:
        """Test formatting non-repo status."""
        status = GitStatus(is_git_repo=False, error="Not a git repository")
        result = format_git_status(status)
        assert "Not a git repository" in result

    def test_format_git_log_empty(self) -> None:
        """Test formatting empty log."""
        result = format_git_log([])
        assert "No commits" in result

    def test_format_git_log_with_commits(self) -> None:
        """Test formatting log with commits."""
        commits = [
            GitCommit(
                hash="abc123def456",
                short_hash="abc123d",
                message="Fix bug",
                author="Test Author",
                date="2025-01-01",
            ),
            GitCommit(
                hash="def456ghi789",
                short_hash="def456g",
                message="Add feature",
                author="Test Author",
                date="2025-01-02",
            ),
        ]
        result = format_git_log(commits)
        assert "abc123d" in result
        assert "Fix bug" in result
        assert "def456g" in result
        assert "2025-01-01" in result


class TestGitCommits:
    """Tests for git commit functions."""

    def test_get_recent_commits_current_repo(self) -> None:
        """Test getting commits from current repo."""
        commits = get_recent_commits(5)
        # Current project should have commits
        assert len(commits) > 0
        assert all(isinstance(c, GitCommit) for c in commits)

    def test_get_recent_commits_non_repo(self) -> None:
        """Test getting commits from non-repo."""
        with TemporaryDirectory() as tmpdir:
            commits = get_recent_commits(5, Path(tmpdir))
            assert commits == []


class TestGitTags:
    """Tests for git tag functions."""

    def test_get_tags_current_repo(self) -> None:
        """Test getting tags from current repo."""
        tags = get_tags()
        # Current project should have tags after releases
        assert isinstance(tags, list)
        # All tags should be strings
        assert all(isinstance(t, str) for t in tags)

    def test_get_tags_non_repo(self) -> None:
        """Test getting tags from non-repo."""
        with TemporaryDirectory() as tmpdir:
            tags = get_tags(Path(tmpdir))
            assert tags == []
