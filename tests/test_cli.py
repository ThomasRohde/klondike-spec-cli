"""Integration tests for CLI commands.

Uses pith's CliRunner for testing CLI commands end-to-end.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory

from pith import CliRunner

from klondike_spec_cli.cli import app


class TestInitCommand:
    """Integration tests for 'klondike init' command."""

    def test_init_creates_klondike_directory(self) -> None:
        """Test that init creates .klondike directory."""
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                result = runner.invoke(app, ["init", "--name", "test-project"])

                assert result.exit_code == 0
                assert "✅ Initialized Klondike project" in result.output

                klondike_dir = Path(tmpdir) / ".klondike"
                assert klondike_dir.exists()
                assert (klondike_dir / "features.json").exists()
                assert (klondike_dir / "agent-progress.json").exists()
                assert (klondike_dir / "config.yaml").exists()
                assert (Path(tmpdir) / "agent-progress.md").exists()
            finally:
                os.chdir(original_cwd)

    def test_init_uses_folder_name_as_default_project_name(self) -> None:
        """Test that init uses folder name when no name provided."""
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                result = runner.invoke(app, ["init"])

                assert result.exit_code == 0

                # Check features.json has folder name
                features_path = Path(tmpdir) / ".klondike" / "features.json"
                with open(features_path) as f:
                    data = json.load(f)
                assert data["projectName"] == Path(tmpdir).name
            finally:
                os.chdir(original_cwd)

    def test_init_refuses_to_overwrite_without_force(self) -> None:
        """Test that init refuses to overwrite without --force."""
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                # First init
                runner.invoke(app, ["init"])

                # Second init should fail
                result = runner.invoke(app, ["init"])

                assert result.exit_code != 0
                assert "already exists" in result.output
            finally:
                os.chdir(original_cwd)

    def test_init_overwrites_with_force(self) -> None:
        """Test that init --force reinitializes."""
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                # First init
                runner.invoke(app, ["init", "--name", "first"])

                # Second init with --force
                result = runner.invoke(app, ["init", "--force", "--name", "second"])

                assert result.exit_code == 0

                # Check project name was updated
                features_path = Path(tmpdir) / ".klondike" / "features.json"
                with open(features_path) as f:
                    data = json.load(f)
                assert data["projectName"] == "second"
            finally:
                os.chdir(original_cwd)


class TestFeatureAddCommand:
    """Integration tests for 'klondike feature add' command."""

    def test_feature_add_creates_feature(self) -> None:
        """Test that feature add creates a new feature."""
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                runner.invoke(app, ["init"])

                result = runner.invoke(
                    app, ["feature", "add", "--description", "Test feature"]
                )

                assert result.exit_code == 0
                assert "✅ Added feature F001" in result.output
                assert "Test feature" in result.output

                # Verify feature was saved
                features_path = Path(tmpdir) / ".klondike" / "features.json"
                with open(features_path) as f:
                    data = json.load(f)
                assert len(data["features"]) == 1
                assert data["features"][0]["id"] == "F001"
                assert data["features"][0]["description"] == "Test feature"
            finally:
                os.chdir(original_cwd)

    def test_feature_add_with_options(self) -> None:
        """Test feature add with category and priority."""
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                runner.invoke(app, ["init"])

                result = runner.invoke(
                    app,
                    [
                        "feature",
                        "add",
                        "--description",
                        "UI Feature",
                        "--category",
                        "ui",
                        "--priority",
                        "1",
                    ],
                )

                assert result.exit_code == 0
                assert "Category: ui" in result.output
                assert "Priority: 1" in result.output

                features_path = Path(tmpdir) / ".klondike" / "features.json"
                with open(features_path) as f:
                    data = json.load(f)
                assert data["features"][0]["category"] == "ui"
                assert data["features"][0]["priority"] == 1
            finally:
                os.chdir(original_cwd)

    def test_feature_add_increments_id(self) -> None:
        """Test that feature IDs increment correctly."""
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                runner.invoke(app, ["init"])

                runner.invoke(app, ["feature", "add", "--description", "First"])
                result = runner.invoke(
                    app, ["feature", "add", "--description", "Second"]
                )

                assert "F002" in result.output

                features_path = Path(tmpdir) / ".klondike" / "features.json"
                with open(features_path) as f:
                    data = json.load(f)
                assert len(data["features"]) == 2
                assert data["features"][0]["id"] == "F001"
                assert data["features"][1]["id"] == "F002"
            finally:
                os.chdir(original_cwd)


class TestFeatureListCommand:
    """Integration tests for 'klondike feature list' command."""

    def test_feature_list_empty(self) -> None:
        """Test feature list with no features."""
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                runner.invoke(app, ["init"])

                result = runner.invoke(app, ["feature", "list"])

                assert result.exit_code == 0
                assert "No features found" in result.output
            finally:
                os.chdir(original_cwd)

    def test_feature_list_shows_features(self) -> None:
        """Test feature list displays all features."""
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                runner.invoke(app, ["init"])
                runner.invoke(app, ["feature", "add", "--description", "Feature One"])
                runner.invoke(app, ["feature", "add", "--description", "Feature Two"])

                result = runner.invoke(app, ["feature", "list"])

                assert result.exit_code == 0
                assert "F001" in result.output
                assert "F002" in result.output
                assert "Feature One" in result.output
                assert "Feature Two" in result.output
            finally:
                os.chdir(original_cwd)

    def test_feature_list_json_output(self) -> None:
        """Test feature list with JSON output."""
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                runner.invoke(app, ["init"])
                runner.invoke(app, ["feature", "add", "--description", "Test"])

                result = runner.invoke(app, ["feature", "list", "--json"])

                assert result.exit_code == 0
                # Verify it's valid JSON
                data = json.loads(result.output)
                assert len(data) == 1
                assert data[0]["id"] == "F001"
            finally:
                os.chdir(original_cwd)

    def test_feature_list_status_filter(self) -> None:
        """Test feature list with status filter."""
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                runner.invoke(app, ["init"])
                runner.invoke(app, ["feature", "add", "--description", "Feature A"])
                runner.invoke(app, ["feature", "add", "--description", "Feature B"])
                runner.invoke(app, ["feature", "start", "F001"])

                result = runner.invoke(
                    app, ["feature", "list", "--status", "in-progress"]
                )

                assert result.exit_code == 0
                assert "F001" in result.output
                assert "F002" not in result.output
            finally:
                os.chdir(original_cwd)


class TestStatusCommand:
    """Integration tests for 'klondike status' command."""

    def test_status_shows_project_info(self) -> None:
        """Test status command shows project information."""
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                runner.invoke(app, ["init", "--name", "my-project"])
                runner.invoke(app, ["feature", "add", "--description", "Feature"])

                result = runner.invoke(app, ["status"])

                assert result.exit_code == 0
                assert "my-project" in result.output
                assert "0/1" in result.output or "0%" in result.output
            finally:
                os.chdir(original_cwd)


class TestValidateCommand:
    """Integration tests for 'klondike validate' command."""

    def test_validate_passes_for_valid_project(self) -> None:
        """Test validate passes for a properly initialized project."""
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                runner.invoke(app, ["init"])

                result = runner.invoke(app, ["validate"])

                assert result.exit_code == 0
                assert "✅ All artifacts valid!" in result.output
            finally:
                os.chdir(original_cwd)
