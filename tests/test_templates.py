"""Tests for the templates module."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from klondike_spec_cli.templates import (
    AVAILABLE_TEMPLATES,
    CONFIG_TEMPLATE,
    FEATURES_TEMPLATE,
    PROGRESS_TEMPLATE,
    extract_all_templates,
    extract_github_templates,
    extract_template,
    get_github_templates_list,
    list_templates,
    read_template,
)


class TestTemplates:
    """Tests for template loading and extraction."""

    def test_list_templates(self) -> None:
        """Test listing available templates."""
        templates = list_templates()
        assert FEATURES_TEMPLATE in templates
        assert PROGRESS_TEMPLATE in templates
        assert CONFIG_TEMPLATE in templates
        assert len(templates) == 3

    def test_read_features_template(self) -> None:
        """Test reading the features.json template."""
        content = read_template(FEATURES_TEMPLATE)
        assert "{{PROJECT_NAME}}" in content
        assert "{{CREATED_AT}}" in content
        assert '"features": []' in content
        assert '"totalFeatures": 0' in content

    def test_read_progress_template(self) -> None:
        """Test reading the agent-progress.json template."""
        content = read_template(PROGRESS_TEMPLATE)
        assert "{{PROJECT_NAME}}" in content
        assert "{{DATE}}" in content
        assert '"sessions"' in content
        assert '"quickReference"' in content

    def test_read_config_template(self) -> None:
        """Test reading the config.yaml template."""
        content = read_template(CONFIG_TEMPLATE)
        assert "{{PROJECT_NAME}}" in content
        assert "default_category: core" in content
        assert "verified_by: coding-agent" in content

    def test_read_invalid_template(self) -> None:
        """Test reading an invalid template raises error."""
        with pytest.raises(ValueError, match="Unknown template"):
            read_template("nonexistent.txt")

    def test_extract_template(self) -> None:
        """Test extracting a template to a file."""
        with TemporaryDirectory() as tmpdir:
            dest = Path(tmpdir) / "features.json"
            result = extract_template(FEATURES_TEMPLATE, dest)

            assert result == dest
            assert dest.exists()

            content = dest.read_text()
            assert "{{PROJECT_NAME}}" in content

    def test_extract_template_creates_parent_dirs(self) -> None:
        """Test extracting a template creates parent directories."""
        with TemporaryDirectory() as tmpdir:
            dest = Path(tmpdir) / "nested" / "dir" / "features.json"
            result = extract_template(FEATURES_TEMPLATE, dest)

            assert result == dest
            assert dest.exists()

    def test_extract_template_no_overwrite(self) -> None:
        """Test extracting a template doesn't overwrite by default."""
        with TemporaryDirectory() as tmpdir:
            dest = Path(tmpdir) / "features.json"
            dest.write_text("existing content")

            with pytest.raises(FileExistsError):
                extract_template(FEATURES_TEMPLATE, dest)

    def test_extract_template_with_overwrite(self) -> None:
        """Test extracting a template with overwrite enabled."""
        with TemporaryDirectory() as tmpdir:
            dest = Path(tmpdir) / "features.json"
            dest.write_text("existing content")

            extract_template(FEATURES_TEMPLATE, dest, overwrite=True)

            content = dest.read_text()
            assert "{{PROJECT_NAME}}" in content
            assert "existing content" not in content

    def test_extract_all_templates(self) -> None:
        """Test extracting all templates to a directory."""
        with TemporaryDirectory() as tmpdir:
            dest_dir = Path(tmpdir)
            results = extract_all_templates(dest_dir)

            assert len(results) == len(AVAILABLE_TEMPLATES)
            for template in AVAILABLE_TEMPLATES:
                assert (dest_dir / template).exists()

    def test_extract_specific_templates(self) -> None:
        """Test extracting specific templates."""
        with TemporaryDirectory() as tmpdir:
            dest_dir = Path(tmpdir)
            results = extract_all_templates(
                dest_dir, templates=[FEATURES_TEMPLATE, CONFIG_TEMPLATE]
            )

            assert len(results) == 2
            assert (dest_dir / FEATURES_TEMPLATE).exists()
            assert (dest_dir / CONFIG_TEMPLATE).exists()
            assert not (dest_dir / PROGRESS_TEMPLATE).exists()


class TestGitHubTemplates:
    """Tests for GitHub templates extraction."""

    def test_get_github_templates_list(self) -> None:
        """Test listing available GitHub templates."""
        templates = get_github_templates_list()
        # Should have at least the main files
        assert len(templates) > 0
        # Check for expected template files
        template_names = [t.split("/")[-1] for t in templates]
        assert "copilot-instructions.md" in template_names

    def test_extract_github_templates(self) -> None:
        """Test extracting GitHub templates to a directory."""
        with TemporaryDirectory() as tmpdir:
            dest_dir = Path(tmpdir)
            results = extract_github_templates(dest_dir)

            # Should have extracted files
            assert len(results) > 0

            # Should have created .github directory
            github_dir = dest_dir / ".github"
            assert github_dir.exists()

            # Check for main instruction file
            assert (github_dir / "copilot-instructions.md").exists()

    def test_extract_github_templates_with_subdirs(self) -> None:
        """Test that GitHub templates include subdirectories."""
        with TemporaryDirectory() as tmpdir:
            dest_dir = Path(tmpdir)
            extract_github_templates(dest_dir)

            github_dir = dest_dir / ".github"

            # Check for expected subdirectories
            assert (github_dir / "instructions").is_dir()
            assert (github_dir / "prompts").is_dir()
            assert (github_dir / "templates").is_dir()

    def test_extract_github_templates_instruction_files(self) -> None:
        """Test that instruction files are extracted."""
        with TemporaryDirectory() as tmpdir:
            dest_dir = Path(tmpdir)
            extract_github_templates(dest_dir)

            instructions_dir = dest_dir / ".github" / "instructions"
            assert instructions_dir.exists()

            # Should have instruction files
            instruction_files = list(instructions_dir.glob("*.md"))
            assert len(instruction_files) > 0

    def test_extract_github_templates_prompt_files(self) -> None:
        """Test that prompt files are extracted."""
        with TemporaryDirectory() as tmpdir:
            dest_dir = Path(tmpdir)
            extract_github_templates(dest_dir)

            prompts_dir = dest_dir / ".github" / "prompts"
            assert prompts_dir.exists()

            # Should have prompt files
            prompt_files = list(prompts_dir.glob("*.md"))
            assert len(prompt_files) > 0

    def test_extract_github_templates_with_variables(self) -> None:
        """Test template variable substitution."""
        with TemporaryDirectory() as tmpdir:
            dest_dir = Path(tmpdir)
            template_vars = {
                "{{PROJECT_NAME}}": "my-test-project",
                "{{DATE}}": "2025-01-01",
            }
            extract_github_templates(dest_dir, template_vars=template_vars)

            # Check that variables were substituted in agent-progress.template.md
            template_path = dest_dir / ".github" / "templates" / "agent-progress.template.md"
            content = template_path.read_text(encoding="utf-8")

            # Should have the substituted project name
            assert "my-test-project" in content
            # Should not have the raw template variable
            assert "{{PROJECT_NAME}}" not in content

    def test_extract_github_templates_no_overwrite(self) -> None:
        """Test that existing files are not overwritten by default."""
        with TemporaryDirectory() as tmpdir:
            dest_dir = Path(tmpdir)
            github_dir = dest_dir / ".github"
            github_dir.mkdir(parents=True)

            existing_file = github_dir / "copilot-instructions.md"
            existing_file.write_text("existing content", encoding="utf-8")

            extract_github_templates(dest_dir, overwrite=False)

            # Original content should be preserved
            assert existing_file.read_text(encoding="utf-8") == "existing content"

    def test_extract_github_templates_with_overwrite(self) -> None:
        """Test that existing files are overwritten when flag is set."""
        with TemporaryDirectory() as tmpdir:
            dest_dir = Path(tmpdir)
            github_dir = dest_dir / ".github"
            github_dir.mkdir(parents=True)

            existing_file = github_dir / "copilot-instructions.md"
            existing_file.write_text("existing content", encoding="utf-8")

            results = extract_github_templates(dest_dir, overwrite=True)

            # File should be in results
            assert existing_file in results

            # Content should be new template content
            content = existing_file.read_text(encoding="utf-8")
            assert "existing content" not in content

    def test_extract_github_templates_creates_init_scripts(self) -> None:
        """Test that init scripts are created in templates dir."""
        with TemporaryDirectory() as tmpdir:
            dest_dir = Path(tmpdir)
            extract_github_templates(dest_dir)

            templates_dir = dest_dir / ".github" / "templates"
            assert templates_dir.exists()

            # Check for init scripts
            init_sh = templates_dir / "init.sh"
            init_ps1 = templates_dir / "init.ps1"

            assert init_sh.exists() or init_ps1.exists()
