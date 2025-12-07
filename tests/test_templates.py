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
    extract_template,
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
