"""Tests for shell completion module."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from klondike_spec_cli.completion import (
    generate_bash_completion,
    generate_powershell_completion,
    generate_zsh_completion,
    save_completion_script,
)


class TestCompletionGeneration:
    """Tests for completion script generation."""

    def test_generate_bash_completion(self) -> None:
        """Test Bash completion script generation."""
        script = generate_bash_completion()
        assert "_klondike_completion()" in script
        assert "complete -F _klondike_completion klondike" in script
        assert "feature" in script
        assert "session" in script
        assert "F[0-9]" in script  # Feature ID pattern

    def test_generate_zsh_completion(self) -> None:
        """Test Zsh completion script generation."""
        script = generate_zsh_completion()
        assert "#compdef klondike" in script
        assert "_klondike()" in script
        assert "feature" in script
        assert "session" in script
        assert "_describe" in script

    def test_generate_powershell_completion(self) -> None:
        """Test PowerShell completion script generation."""
        script = generate_powershell_completion()
        assert "Register-ArgumentCompleter" in script
        assert "klondike" in script
        assert "$script:KlondikeCommands" in script
        assert "Get-KlondikeFeatureIds" in script


class TestCompletionOutput:
    """Tests for completion script file output."""

    def test_save_bash_completion(self) -> None:
        """Test saving Bash completion to file."""
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "completions" / "_klondike"
            result = save_completion_script("bash", output_path)
            assert result == output_path
            assert result.exists()
            content = result.read_text()
            assert "_klondike_completion()" in content

    def test_save_zsh_completion(self) -> None:
        """Test saving Zsh completion to file."""
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "_klondike"
            result = save_completion_script("zsh", output_path)
            assert result == output_path
            assert result.exists()
            content = result.read_text()
            assert "#compdef klondike" in content

    def test_save_powershell_completion(self) -> None:
        """Test saving PowerShell completion to file."""
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "klondike.ps1"
            result = save_completion_script("powershell", output_path)
            assert result == output_path
            assert result.exists()
            content = result.read_text()
            assert "Register-ArgumentCompleter" in content

    def test_save_completion_default_path(self) -> None:
        """Test saving completion with default path."""
        with TemporaryDirectory() as tmpdir:
            # Change to temp directory for test
            import os

            old_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                result = save_completion_script("bash")
                assert result.name == "_klondike"
                assert result.exists()
            finally:
                os.chdir(old_cwd)

    def test_save_completion_invalid_shell(self) -> None:
        """Test saving completion with invalid shell raises error."""
        with pytest.raises(ValueError) as exc_info:
            save_completion_script("fish")
        assert "Unsupported shell" in str(exc_info.value)
