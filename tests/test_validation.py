"""Tests for validation module."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from pith import PithException

from klondike_spec_cli.validation import (
    is_valid_feature_id,
    sanitize_string,
    validate_description,
    validate_feature_id,
    validate_file_path,
    validate_output_path,
    validate_priority,
)


class TestFeatureIdValidation:
    """Tests for feature ID validation."""

    def test_valid_feature_id(self) -> None:
        """Test valid feature IDs."""
        assert validate_feature_id("F001") == "F001"
        assert validate_feature_id("f001") == "F001"  # Uppercase conversion
        assert validate_feature_id("F123") == "F123"
        assert validate_feature_id("F0001") == "F0001"  # 4 digits ok

    def test_invalid_feature_id(self) -> None:
        """Test invalid feature IDs."""
        with pytest.raises(PithException):
            validate_feature_id("")
        with pytest.raises(PithException):
            validate_feature_id("001")  # Missing F
        with pytest.raises(PithException):
            validate_feature_id("F01")  # Only 2 digits
        with pytest.raises(PithException):
            validate_feature_id("FEATURE-001")  # Wrong format

    def test_is_valid_feature_id(self) -> None:
        """Test is_valid_feature_id helper."""
        assert is_valid_feature_id("F001") is True
        assert is_valid_feature_id("invalid") is False
        assert is_valid_feature_id(None) is False
        assert is_valid_feature_id("") is False


class TestPathValidation:
    """Tests for path validation."""

    def test_validate_file_path_existing(self) -> None:
        """Test validating existing file paths."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("test")

            result = validate_file_path(str(test_file), must_exist=True)
            assert result == test_file

    def test_validate_file_path_not_existing(self) -> None:
        """Test validating non-existing paths fails when must_exist=True."""
        with pytest.raises(PithException):
            validate_file_path("/nonexistent/path.txt", must_exist=True)

    def test_validate_output_path_valid_extension(self) -> None:
        """Test output path with valid extension."""
        result = validate_output_path("export.yaml", extensions=[".yaml", ".json"])
        assert result.suffix == ".yaml"

    def test_validate_output_path_invalid_extension(self) -> None:
        """Test output path with invalid extension fails."""
        with pytest.raises(PithException):
            validate_output_path("export.txt", extensions=[".yaml", ".json"])


class TestContentValidation:
    """Tests for content validation."""

    def test_validate_priority_valid(self) -> None:
        """Test valid priorities."""
        assert validate_priority(1) == 1
        assert validate_priority(5) == 5
        assert validate_priority("3") == 3
        assert validate_priority(None) == 3  # Default

    def test_validate_priority_invalid(self) -> None:
        """Test invalid priorities."""
        with pytest.raises(PithException):
            validate_priority(0)
        with pytest.raises(PithException):
            validate_priority(6)
        with pytest.raises(PithException):
            validate_priority("abc")

    def test_validate_description_valid(self) -> None:
        """Test valid descriptions."""
        result = validate_description("A valid feature description")
        assert result == "A valid feature description"

    def test_validate_description_empty(self) -> None:
        """Test empty description fails."""
        with pytest.raises(PithException):
            validate_description(None)
        with pytest.raises(PithException):
            validate_description("")

    def test_validate_description_too_long(self) -> None:
        """Test description that's too long fails."""
        with pytest.raises(PithException):
            validate_description("x" * 600, max_length=500)

    def test_sanitize_string(self) -> None:
        """Test string sanitization."""
        assert sanitize_string("  test  ") == "test"
        assert sanitize_string(None) is None
        assert sanitize_string("") is None
        assert sanitize_string("   ") is None

    def test_sanitize_string_truncation(self) -> None:
        """Test sanitization truncates long strings."""
        result = sanitize_string("x" * 100, max_length=50)
        assert len(result) == 50
