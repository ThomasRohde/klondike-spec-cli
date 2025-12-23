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

                # Second init with --force (confirm with 'yes')
                result = runner.invoke(app, ["init", "--force", "--name", "second"], input="yes\n")

                assert result.exit_code == 0

                # Check project name was updated
                features_path = Path(tmpdir) / ".klondike" / "features.json"
                with open(features_path) as f:
                    data = json.load(f)
                assert data["projectName"] == "second"
            finally:
                os.chdir(original_cwd)

    def test_init_force_requires_confirmation(self) -> None:
        """Test that init --force requires user confirmation."""
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                # First init
                runner.invoke(app, ["init"])

                # Second init with --force but no confirmation (simulate "no")
                result = runner.invoke(app, ["init", "--force"], input="no\n")

                assert result.exit_code == 0
                assert "Type 'yes' to continue" in result.output
                assert "Aborted" in result.output
            finally:
                os.chdir(original_cwd)

    def test_init_suggests_upgrade_for_existing_project(self) -> None:
        """Test that init suggests --upgrade when project exists."""
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                # First init
                runner.invoke(app, ["init"])

                # Second init without flags should suggest upgrade
                result = runner.invoke(app, ["init"])

                assert result.exit_code != 0
                assert "already exists" in result.output
                assert "--upgrade" in result.output
            finally:
                os.chdir(original_cwd)


class TestUpgradeCommand:
    """Integration tests for 'klondike upgrade' and 'klondike init --upgrade' commands."""

    def test_upgrade_preserves_features(self) -> None:
        """Test that upgrade preserves existing features."""
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                # Init and add feature
                runner.invoke(app, ["init"])
                runner.invoke(app, ["feature", "add", "--description", "Test feature"])

                # Upgrade
                result = runner.invoke(app, ["upgrade"])

                assert result.exit_code == 0
                assert "Upgrade complete" in result.output

                # Verify feature still exists
                features_path = Path(tmpdir) / ".klondike" / "features.json"
                with open(features_path) as f:
                    data = json.load(f)
                assert len(data["features"]) == 1
                assert data["features"][0]["description"] == "Test feature"
            finally:
                os.chdir(original_cwd)

    def test_upgrade_preserves_session_history(self) -> None:
        """Test that upgrade preserves session history."""
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                # Init and start session
                runner.invoke(app, ["init"])
                runner.invoke(app, ["session", "start", "--focus", "Testing"])

                # Upgrade
                result = runner.invoke(app, ["upgrade"])

                assert result.exit_code == 0

                # Verify session exists (init creates session #1, start creates #2)
                progress_path = Path(tmpdir) / ".klondike" / "agent-progress.json"
                with open(progress_path) as f:
                    data = json.load(f)
                assert len(data["sessions"]) == 2
                assert data["sessions"][1]["focus"] == "Testing"
            finally:
                os.chdir(original_cwd)

    def test_upgrade_updates_github_templates(self) -> None:
        """Test that upgrade refreshes .github/ templates."""
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                # Init
                runner.invoke(app, ["init"])

                # Modify a template
                copilot_path = Path(tmpdir) / ".github" / "copilot-instructions.md"
                original_content = copilot_path.read_text(encoding="utf-8")
                copilot_path.write_text("# MODIFIED", encoding="utf-8")

                # Upgrade
                result = runner.invoke(app, ["upgrade"])

                assert result.exit_code == 0
                assert "Refreshed GitHub Copilot templates" in result.output

                # Verify template was restored (and backed up)
                new_content = copilot_path.read_text(encoding="utf-8")
                assert new_content != "# MODIFIED"
                assert new_content == original_content

                # Check backup was created
                backup_dirs = list(Path(tmpdir).glob(".github.backup.*"))
                assert len(backup_dirs) == 1
            finally:
                os.chdir(original_cwd)

    def test_upgrade_updates_klondike_version(self) -> None:
        """Test that upgrade updates klondike_version in config."""
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                # Init
                runner.invoke(app, ["init"])

                # Upgrade
                result = runner.invoke(app, ["upgrade"])

                assert result.exit_code == 0

                # Verify version was updated in config
                config_path = Path(tmpdir) / ".klondike" / "config.yaml"
                config_text = config_path.read_text()
                assert "klondike_version:" in config_text
            finally:
                os.chdir(original_cwd)

    def test_init_upgrade_flag_works(self) -> None:
        """Test that 'klondike init --upgrade' works as alias."""
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                # Init
                runner.invoke(app, ["init"])
                runner.invoke(app, ["feature", "add", "--description", "Test"])

                # Upgrade via init --upgrade
                result = runner.invoke(app, ["init", "--upgrade"])

                assert result.exit_code == 0
                assert "Upgrade complete" in result.output

                # Verify feature preserved
                features_path = Path(tmpdir) / ".klondike" / "features.json"
                with open(features_path) as f:
                    data = json.load(f)
                assert len(data["features"]) == 1
            finally:
                os.chdir(original_cwd)

    def test_upgrade_fails_without_klondike_dir(self) -> None:
        """Test that upgrade command fails if no .klondike directory exists."""
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)

                # Try to upgrade without init
                result = runner.invoke(app, ["upgrade"])

                assert result.exit_code != 0
                assert "not found" in result.output
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

                result = runner.invoke(app, ["feature", "add", "--description", "Test feature"])

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

    def test_feature_add_positional_description(self) -> None:
        """Test feature add with description as positional argument."""
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                runner.invoke(app, ["init"])

                # Use description as positional argument (after 'add')
                result = runner.invoke(
                    app,
                    ["feature", "add", "My positional feature", "--category", "core"],
                )

                assert result.exit_code == 0
                assert "✅ Added feature F001" in result.output
                assert "My positional feature" in result.output

                features_path = Path(tmpdir) / ".klondike" / "features.json"
                with open(features_path) as f:
                    data = json.load(f)
                assert data["features"][0]["description"] == "My positional feature"
            finally:
                os.chdir(original_cwd)

    def test_feature_add_setup_category(self) -> None:
        """Test feature add with 'setup' category."""
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                runner.invoke(app, ["init"])

                result = runner.invoke(
                    app,
                    ["feature", "add", "Setup feature", "--category", "setup"],
                )

                assert result.exit_code == 0
                assert "Category: setup" in result.output

                features_path = Path(tmpdir) / ".klondike" / "features.json"
                with open(features_path) as f:
                    data = json.load(f)
                assert data["features"][0]["category"] == "setup"
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
                result = runner.invoke(app, ["feature", "add", "--description", "Second"])

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

                result = runner.invoke(app, ["feature", "list", "--status", "in-progress"])

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
                # Rich output uses "Completion" instead of feature count format
                assert "Completion" in result.output or "0%" in result.output
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


class TestReportCommand:
    """Integration tests for 'klondike report' command."""

    def test_report_generates_markdown(self) -> None:
        """Test report generates markdown output."""
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                runner.invoke(app, ["init", "--name", "test-project"])
                runner.invoke(app, ["feature", "add", "--description", "Feature One"])
                runner.invoke(app, ["feature", "verify", "F001", "--evidence", "test.txt"])

                result = runner.invoke(app, ["report"])

                assert result.exit_code == 0
                assert "# test-project - Progress Report" in result.output
                assert "Executive Summary" in result.output
                assert "1/1 features complete (100.0%)" in result.output
                assert "Feature One" in result.output
            finally:
                os.chdir(original_cwd)

    def test_report_plain_format(self) -> None:
        """Test report with plain text format."""
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                runner.invoke(app, ["init", "--name", "plain-test"])
                runner.invoke(app, ["feature", "add", "--description", "Plain Feature"])

                result = runner.invoke(app, ["report", "--format", "plain"])

                assert result.exit_code == 0
                assert "plain-test - Progress Report" in result.output
                assert "EXECUTIVE SUMMARY" in result.output
                assert "0/1 features (0.0%)" in result.output
            finally:
                os.chdir(original_cwd)

    def test_report_output_to_file(self) -> None:
        """Test report saves to file with --output flag."""
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                runner.invoke(app, ["init"])

                result = runner.invoke(app, ["report", "--output", "report.md"])

                assert result.exit_code == 0
                assert "Report saved to" in result.output

                # Verify file was created
                report_path = Path(tmpdir) / "report.md"
                assert report_path.exists()
                content = report_path.read_text(encoding="utf-8")
                assert "Progress Report" in content
            finally:
                os.chdir(original_cwd)

    def test_report_shows_in_progress_features(self) -> None:
        """Test report shows in-progress features."""
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                runner.invoke(app, ["init"])
                runner.invoke(app, ["feature", "add", "--description", "WIP Feature"])
                runner.invoke(app, ["feature", "start", "F001"])

                result = runner.invoke(app, ["report"])

                assert result.exit_code == 0
                assert "In Progress" in result.output
                assert "WIP Feature" in result.output
            finally:
                os.chdir(original_cwd)


class TestFeatureEditCommand:
    """Tests for klondike feature edit command."""

    def test_edit_updates_notes(self) -> None:
        """Test edit command updates notes."""
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                runner.invoke(app, ["init"])
                runner.invoke(app, ["feature", "add", "--description", "Test feature"])

                result = runner.invoke(
                    app, ["feature", "edit", "F001", "--notes", "Implementation note"]
                )

                assert result.exit_code == 0
                assert "Updated" in result.output
                assert "notes: Implementation note" in result.output

                # Verify the note is saved
                show_result = runner.invoke(app, ["feature", "show", "F001"])
                assert "Notes: Implementation note" in show_result.output
            finally:
                os.chdir(original_cwd)

    def test_edit_adds_criteria(self) -> None:
        """Test edit command adds acceptance criteria."""
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                runner.invoke(app, ["init"])
                runner.invoke(app, ["feature", "add", "--description", "Test feature"])

                result = runner.invoke(
                    app, ["feature", "edit", "F001", "--add-criteria", "New criterion,Another one"]
                )

                assert result.exit_code == 0
                assert "added criteria" in result.output

                # Verify the criteria are saved
                show_result = runner.invoke(app, ["feature", "show", "F001"])
                assert "New criterion" in show_result.output
                assert "Another one" in show_result.output
            finally:
                os.chdir(original_cwd)

    def test_edit_forbids_description_change(self) -> None:
        """Test edit command forbids description modification."""
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                runner.invoke(app, ["init"])
                runner.invoke(app, ["feature", "add", "--description", "Original desc"])

                result = runner.invoke(
                    app, ["feature", "edit", "F001", "--description", "Changed desc"]
                )

                assert result.exit_code == 1
                assert "Cannot modify description" in result.output
                assert "immutable" in result.output
            finally:
                os.chdir(original_cwd)

    def test_edit_updates_priority(self) -> None:
        """Test edit command can update priority."""
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                runner.invoke(app, ["init"])
                runner.invoke(
                    app,
                    ["feature", "add", "--description", "Test feature", "--priority", "3"],
                )

                result = runner.invoke(app, ["feature", "edit", "F001", "--priority", "1"])

                assert result.exit_code == 0
                assert "priority: 1" in result.output

                # Verify the priority is saved
                show_result = runner.invoke(app, ["feature", "show", "F001"])
                assert "Priority: 1" in show_result.output
            finally:
                os.chdir(original_cwd)

    def test_edit_requires_changes(self) -> None:
        """Test edit command requires at least one change."""
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                runner.invoke(app, ["init"])
                runner.invoke(app, ["feature", "add", "--description", "Test feature"])

                result = runner.invoke(app, ["feature", "edit", "F001"])

                assert result.exit_code == 1
                assert "No changes specified" in result.output
            finally:
                os.chdir(original_cwd)


class TestImportExportFeatures:
    """Integration tests for import-features and export-features commands."""

    def test_export_features_to_yaml(self) -> None:
        """Test exporting features to YAML."""
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                runner.invoke(app, ["init"])
                runner.invoke(app, ["feature", "add", "--description", "Feature 1"])
                runner.invoke(app, ["feature", "add", "--description", "Feature 2"])

                result = runner.invoke(app, ["export-features", "export.yaml"])

                assert result.exit_code == 0
                assert "Exported 2 features" in result.output
                assert Path("export.yaml").exists()

                content = Path("export.yaml").read_text()
                assert "Feature 1" in content
                assert "Feature 2" in content
            finally:
                os.chdir(original_cwd)

    def test_export_features_to_json(self) -> None:
        """Test exporting features to JSON."""
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                runner.invoke(app, ["init"])
                runner.invoke(app, ["feature", "add", "--description", "Feature JSON"])

                result = runner.invoke(app, ["export-features", "export.json"])

                assert result.exit_code == 0
                assert Path("export.json").exists()

                import json

                data = json.loads(Path("export.json").read_text())
                assert "features" in data
                assert len(data["features"]) == 1
            finally:
                os.chdir(original_cwd)

    def test_import_features_from_yaml(self) -> None:
        """Test importing features from YAML."""
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                runner.invoke(app, ["init"])

                # Create import file
                import_content = """features:
  - description: "Imported Feature 1"
    category: core
    priority: 2
    acceptance_criteria:
      - "Works correctly"
  - description: "Imported Feature 2"
    category: ui
    priority: 3
"""
                Path("import.yaml").write_text(import_content)

                result = runner.invoke(app, ["import-features", "import.yaml"])

                assert result.exit_code == 0
                assert "Imported: 2" in result.output

                # Verify features exist
                list_result = runner.invoke(app, ["feature", "list", "--json"])
                assert "Imported Feature 1" in list_result.output
                assert "Imported Feature 2" in list_result.output
            finally:
                os.chdir(original_cwd)

    def test_import_skips_duplicates(self) -> None:
        """Test that import skips existing feature IDs."""
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                runner.invoke(app, ["init"])
                runner.invoke(app, ["feature", "add", "--description", "Existing feature"])

                # Create import file with same ID
                import_content = """features:
  - id: F001
    description: "Duplicate feature"
    category: core
    priority: 1
  - description: "New feature"
    category: core
    priority: 2
"""
                Path("import.yaml").write_text(import_content)

                result = runner.invoke(app, ["import-features", "import.yaml"])

                assert result.exit_code == 0
                assert "Imported: 1" in result.output
                assert "Skipped: 1" in result.output
            finally:
                os.chdir(original_cwd)

    def test_import_dry_run(self) -> None:
        """Test import dry-run mode."""
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                runner.invoke(app, ["init"])

                import_content = """features:
  - description: "Dry run feature"
    category: core
"""
                Path("import.yaml").write_text(import_content)

                result = runner.invoke(app, ["import-features", "import.yaml", "--dry-run"])

                assert result.exit_code == 0
                assert "Dry run complete" in result.output
                assert "Would import" in result.output

                # Verify feature was NOT actually created
                list_result = runner.invoke(app, ["feature", "list", "--json"])
                assert "Dry run feature" not in list_result.output
            finally:
                os.chdir(original_cwd)

    def test_export_with_status_filter(self) -> None:
        """Test exporting features with status filter."""
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                runner.invoke(app, ["init"])
                runner.invoke(app, ["feature", "add", "--description", "Feature 1"])
                runner.invoke(app, ["feature", "add", "--description", "Feature 2"])
                runner.invoke(app, ["feature", "start", "F001"])

                result = runner.invoke(
                    app, ["export-features", "in-progress.yaml", "--status", "in-progress"]
                )

                assert result.exit_code == 0
                assert "Exported 1 features" in result.output
            finally:
                os.chdir(original_cwd)


class TestCopilotCommand:
    """Integration tests for 'klondike copilot' command."""

    def test_copilot_start_dry_run(self) -> None:
        """Test copilot start with --dry-run shows command without executing."""
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                runner.invoke(app, ["init", "--name", "test-project"])
                runner.invoke(app, ["feature", "add", "--description", "Test feature"])

                result = runner.invoke(app, ["copilot", "start", "--dry-run"])

                assert result.exit_code == 0
                assert "Dry run - would execute" in result.output
                assert "copilot" in result.output
                # Verify template content is embedded (not file path reference)
                assert "standardized startup routine" in result.output
            finally:
                os.chdir(original_cwd)

    def test_copilot_start_includes_feature_with_flag(self) -> None:
        """Test copilot start includes feature when using --feature flag."""
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                runner.invoke(app, ["init"])
                runner.invoke(
                    app,
                    [
                        "feature",
                        "add",
                        "--description",
                        "Important feature",
                        "--criteria",
                        "Must work,Must be fast",
                    ],
                )

                result = runner.invoke(app, ["copilot", "start", "--dry-run", "--feature", "F001"])

                assert result.exit_code == 0
                assert "F001" in result.output
                assert "Important feature" in result.output
                assert "Must work" in result.output
                assert "Must be fast" in result.output
            finally:
                os.chdir(original_cwd)

    def test_copilot_start_with_model_flag(self) -> None:
        """Test copilot start with --model flag."""
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                runner.invoke(app, ["init"])

                result = runner.invoke(
                    app, ["copilot", "start", "--dry-run", "--model", "claude-sonnet"]
                )

                assert result.exit_code == 0
                assert "--model" in result.output
                assert "claude-sonnet" in result.output
            finally:
                os.chdir(original_cwd)

    def test_copilot_start_with_resume_flag(self) -> None:
        """Test copilot start with --resume flag."""
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                runner.invoke(app, ["init"])

                result = runner.invoke(app, ["copilot", "start", "--dry-run", "--resume"])

                assert result.exit_code == 0
                assert "--resume" in result.output
            finally:
                os.chdir(original_cwd)

    def test_copilot_start_with_feature_flag(self) -> None:
        """Test copilot start with --feature flag to focus on specific feature."""
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                runner.invoke(app, ["init"])
                runner.invoke(app, ["feature", "add", "--description", "Feature One"])
                runner.invoke(app, ["feature", "add", "--description", "Feature Two"])

                result = runner.invoke(app, ["copilot", "start", "--dry-run", "--feature", "F002"])

                assert result.exit_code == 0
                assert "F002" in result.output
                assert "Feature Two" in result.output
            finally:
                os.chdir(original_cwd)

    def test_copilot_start_with_additional_instructions(self) -> None:
        """Test copilot start with --instructions flag."""
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                runner.invoke(app, ["init"])

                result = runner.invoke(
                    app,
                    [
                        "copilot",
                        "start",
                        "--dry-run",
                        "--instructions",
                        "Focus on performance",
                    ],
                )

                assert result.exit_code == 0
                assert "Focus on performance" in result.output
            finally:
                os.chdir(original_cwd)

    def test_copilot_start_with_custom_tools(self) -> None:
        """Test copilot start with --allow-tools flag."""
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                runner.invoke(app, ["init"])

                result = runner.invoke(
                    app,
                    [
                        "copilot",
                        "start",
                        "--dry-run",
                        "--allow-tools",
                        "read_file,run_in_terminal",
                    ],
                )

                assert result.exit_code == 0
                assert "--allow-tool" in result.output
                assert "read_file" in result.output
                assert "run_in_terminal" in result.output
            finally:
                os.chdir(original_cwd)

    def test_copilot_start_uses_allow_all_tools_by_default(self) -> None:
        """Test copilot start uses --allow-all-tools by default."""
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                runner.invoke(app, ["init"])

                result = runner.invoke(app, ["copilot", "start", "--dry-run"])

                assert result.exit_code == 0
                # Should use --allow-all-tools by default
                assert "--allow-all-tools" in result.output
            finally:
                os.chdir(original_cwd)

    def test_copilot_start_embeds_prompt_template(self) -> None:
        """Test copilot start embeds the session-start prompt template content."""
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                runner.invoke(app, ["init"])

                result = runner.invoke(app, ["copilot", "start", "--dry-run"])

                assert result.exit_code == 0
                assert "--prompt" in result.output
                # Verify template content is embedded directly in the prompt
                assert "standardized startup routine" in result.output
                assert "klondike status" in result.output
            finally:
                os.chdir(original_cwd)

    def test_copilot_invalid_feature_id(self) -> None:
        """Test copilot start with invalid feature ID."""
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                runner.invoke(app, ["init"])

                result = runner.invoke(app, ["copilot", "start", "--dry-run", "--feature", "F999"])

                assert result.exit_code != 0
                assert "Feature not found" in result.output
            finally:
                os.chdir(original_cwd)

    def test_copilot_unknown_action(self) -> None:
        """Test copilot with unknown action."""
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                runner.invoke(app, ["init"])

                result = runner.invoke(app, ["copilot", "unknown"])

                assert result.exit_code != 0
                assert "Unknown action" in result.output
            finally:
                os.chdir(original_cwd)


class TestReleaseCommand:
    """Integration tests for 'klondike release' command."""

    def test_release_shows_current_version(self) -> None:
        """Test release without args shows current version."""
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                # Create directory structure and _version.py (hatch-vcs style)
                version_dir = Path(tmpdir) / "src" / "klondike_spec_cli"
                version_dir.mkdir(parents=True)
                version_file = version_dir / "_version.py"
                version_file.write_text("__version__ = version = '1.2.3'\n")

                result = runner.invoke(app, ["release"])

                assert result.exit_code == 0
                assert "Current version: 1.2.3" in result.output
            finally:
                os.chdir(original_cwd)

    def test_release_dry_run(self) -> None:
        """Test release dry run shows plan without changes."""
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                # Create directory structure and _version.py
                version_dir = Path(tmpdir) / "src" / "klondike_spec_cli"
                version_dir.mkdir(parents=True)
                version_file = version_dir / "_version.py"
                version_file.write_text("__version__ = version = '1.0.0'\n")

                result = runner.invoke(app, ["release", "1.1.0", "--dry-run", "--skip-tests"])

                assert result.exit_code == 0
                assert "DRY RUN" in result.output
                assert "New version:     1.1.0" in result.output
                assert "Tag:             v1.1.0" in result.output

                # Verify file wasn't changed
                content = version_file.read_text()
                assert "1.0.0" in content
            finally:
                os.chdir(original_cwd)

    def test_release_bump_patch(self) -> None:
        """Test release with --bump patch."""
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                # Create directory structure and _version.py
                version_dir = Path(tmpdir) / "src" / "klondike_spec_cli"
                version_dir.mkdir(parents=True)
                version_file = version_dir / "_version.py"
                version_file.write_text("__version__ = version = '1.2.3'\n")

                result = runner.invoke(
                    app, ["release", "--bump", "patch", "--dry-run", "--skip-tests"]
                )

                assert result.exit_code == 0
                assert "New version:     1.2.4" in result.output
            finally:
                os.chdir(original_cwd)

    def test_release_bump_minor(self) -> None:
        """Test release with --bump minor."""
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                # Create directory structure and _version.py
                version_dir = Path(tmpdir) / "src" / "klondike_spec_cli"
                version_dir.mkdir(parents=True)
                version_file = version_dir / "_version.py"
                version_file.write_text("__version__ = version = '1.2.3'\n")

                result = runner.invoke(
                    app, ["release", "--bump", "minor", "--dry-run", "--skip-tests"]
                )

                assert result.exit_code == 0
                assert "New version:     1.3.0" in result.output
            finally:
                os.chdir(original_cwd)

    def test_release_bump_major(self) -> None:
        """Test release with --bump major."""
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                # Create directory structure and _version.py
                version_dir = Path(tmpdir) / "src" / "klondike_spec_cli"
                version_dir.mkdir(parents=True)
                version_file = version_dir / "_version.py"
                version_file.write_text("__version__ = version = '1.2.3'\n")

                result = runner.invoke(
                    app, ["release", "--bump", "major", "--dry-run", "--skip-tests"]
                )

                assert result.exit_code == 0
                assert "New version:     2.0.0" in result.output
            finally:
                os.chdir(original_cwd)

    def test_release_no_version_file(self) -> None:
        """Test release fails without _version.py or git tags."""
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)

                result = runner.invoke(app, ["release", "1.0.0"])

                assert result.exit_code != 0
                assert "Could not determine version" in result.output
            finally:
                os.chdir(original_cwd)

    def test_release_invalid_version(self) -> None:
        """Test release fails with invalid version format."""
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                # Create directory structure and _version.py
                version_dir = Path(tmpdir) / "src" / "klondike_spec_cli"
                version_dir.mkdir(parents=True)
                version_file = version_dir / "_version.py"
                version_file.write_text("__version__ = version = '1.0.0'\n")

                result = runner.invoke(app, ["release", "invalid"])

                assert result.exit_code != 0
                assert "Invalid version format" in result.output
            finally:
                os.chdir(original_cwd)

    def test_release_invalid_bump_type(self) -> None:
        """Test release fails with invalid bump type."""
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                # Create directory structure and _version.py
                version_dir = Path(tmpdir) / "src" / "klondike_spec_cli"
                version_dir.mkdir(parents=True)
                version_file = version_dir / "_version.py"
                version_file.write_text("__version__ = version = '1.0.0'\n")

                result = runner.invoke(
                    app, ["release", "--bump", "invalid", "--dry-run", "--skip-tests"]
                )

                assert result.exit_code != 0
                assert "Invalid bump type" in result.output
            finally:
                os.chdir(original_cwd)
