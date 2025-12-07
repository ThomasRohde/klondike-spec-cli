"""Input validation and sanitization for klondike CLI.

Provides validation for feature IDs, file paths, and structured data.
"""

from __future__ import annotations

import re
from pathlib import Path

from pith import PithException

# --- Feature ID Validation ---

FEATURE_ID_PATTERN = re.compile(r"^F\d{3,4}$")


def validate_feature_id(feature_id: str) -> str:
    """Validate a feature ID against the expected pattern.

    Args:
        feature_id: The ID to validate (e.g., "F001")

    Returns:
        The validated feature ID (uppercased)

    Raises:
        PithException: If the ID doesn't match the pattern
    """
    if not feature_id:
        raise PithException("Feature ID is required")

    # Normalize to uppercase
    normalized = feature_id.upper().strip()

    if not FEATURE_ID_PATTERN.match(normalized):
        raise PithException(
            f"Invalid feature ID: '{feature_id}'. "
            "Feature IDs must match pattern 'F###' (e.g., F001, F123)."
        )

    return normalized


def is_valid_feature_id(feature_id: str | None) -> bool:
    """Check if a string is a valid feature ID.

    Args:
        feature_id: The ID to check

    Returns:
        True if valid, False otherwise
    """
    if not feature_id:
        return False
    try:
        validate_feature_id(feature_id)
        return True
    except PithException:
        return False


# --- Path Validation ---


def validate_file_path(file_path: str | Path, must_exist: bool = False) -> Path:
    """Validate and sanitize a file path.

    Args:
        file_path: The path to validate
        must_exist: Whether the file must exist

    Returns:
        The validated Path object

    Raises:
        PithException: If the path is invalid or violates security constraints
    """
    if not file_path:
        raise PithException("File path is required")

    path = Path(file_path)

    # Check for path traversal attempts
    try:
        # Resolve to absolute path
        resolved = path.resolve()

        # Check if path tries to escape current directory using ..
        path_str = str(path)
        if ".." in path_str:
            # Verify it doesn't escape beyond CWD
            cwd = Path.cwd().resolve()
            if not str(resolved).startswith(str(cwd)):
                raise PithException(
                    f"Path traversal detected: '{file_path}'. "
                    "Paths must not escape the current directory."
                )
    except OSError as e:
        raise PithException(f"Invalid path: '{file_path}'. {e}") from e

    # Check existence if required
    if must_exist and not path.exists():
        raise PithException(f"File not found: '{file_path}'")

    return path


def validate_output_path(file_path: str | Path, extensions: list[str] | None = None) -> Path:
    """Validate an output file path.

    Args:
        file_path: The output path to validate
        extensions: Allowed file extensions (e.g., [".yaml", ".json"])

    Returns:
        The validated Path object

    Raises:
        PithException: If the path is invalid or has wrong extension
    """
    path = validate_file_path(file_path, must_exist=False)

    if extensions:
        if path.suffix.lower() not in extensions:
            ext_str = ", ".join(extensions)
            raise PithException(
                f"Invalid file extension: '{path.suffix}'. Allowed extensions: {ext_str}"
            )

    return path


# --- Content Validation ---


def validate_priority(priority: int | str | None) -> int:
    """Validate a priority value.

    Args:
        priority: The priority value (1-5)

    Returns:
        The validated priority as an integer

    Raises:
        PithException: If priority is not in valid range
    """
    if priority is None:
        return 3  # Default priority

    try:
        prio = int(priority)
    except (ValueError, TypeError) as e:
        raise PithException(f"Priority must be an integer: '{priority}'") from e

    if prio < 1 or prio > 5:
        raise PithException(f"Priority must be between 1 and 5: {prio}")

    return prio


def validate_category(category: str | None, valid_categories: list[str]) -> str | None:
    """Validate a category value.

    Args:
        category: The category to validate
        valid_categories: List of valid category values

    Returns:
        The validated category or None

    Raises:
        PithException: If category is not valid
    """
    if category is None:
        return None

    cat = category.lower().strip()

    if cat not in valid_categories:
        valid_str = ", ".join(valid_categories)
        raise PithException(f"Invalid category: '{category}'. Valid categories: {valid_str}")

    return cat


def validate_description(description: str | None, max_length: int = 500) -> str:
    """Validate a feature description.

    Args:
        description: The description text
        max_length: Maximum allowed length

    Returns:
        The validated description

    Raises:
        PithException: If description is invalid
    """
    if not description:
        raise PithException("Description is required")

    desc = description.strip()

    if len(desc) > max_length:
        raise PithException(f"Description too long ({len(desc)} chars). Maximum is {max_length}.")

    # Check for suspicious content
    if "<script" in desc.lower() or "javascript:" in desc.lower():
        raise PithException("Description contains potentially unsafe content")

    return desc


def sanitize_string(value: str | None, max_length: int = 1000) -> str | None:
    """Sanitize a string value for safe storage.

    Args:
        value: The string to sanitize
        max_length: Maximum allowed length

    Returns:
        The sanitized string or None
    """
    if value is None:
        return None

    # Strip whitespace
    sanitized = value.strip()

    # Truncate if too long
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]

    return sanitized if sanitized else None
