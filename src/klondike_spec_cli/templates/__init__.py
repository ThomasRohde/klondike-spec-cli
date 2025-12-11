"""Templates package for Klondike Spec CLI.

This package contains template files that are baked into the executable.
Templates can be extracted on demand using the functions in this module.
"""

from __future__ import annotations

import importlib.resources
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from importlib.abc import Traversable

# Template file names
FEATURES_TEMPLATE = "features.json"
PROGRESS_TEMPLATE = "agent-progress.json"
CONFIG_TEMPLATE = "config.yaml"

# All available templates
AVAILABLE_TEMPLATES = [
    FEATURES_TEMPLATE,
    PROGRESS_TEMPLATE,
    CONFIG_TEMPLATE,
]

# Agent-specific templates packages
COPILOT_TEMPLATES_PACKAGE = "klondike_spec_cli.templates.copilot_templates"
CLAUDE_TEMPLATES_PACKAGE = "klondike_spec_cli.templates.claude_templates"

# Backward compatibility alias
GITHUB_TEMPLATES_PACKAGE = COPILOT_TEMPLATES_PACKAGE


def get_template_path(template_name: str) -> Traversable:
    """Get a traversable path to a template file.

    Args:
        template_name: Name of the template file (e.g., 'features.json')

    Returns:
        Traversable path to the template resource

    Raises:
        ValueError: If template_name is not a valid template
    """
    if template_name not in AVAILABLE_TEMPLATES:
        raise ValueError(
            f"Unknown template: {template_name}. "
            f"Available templates: {', '.join(AVAILABLE_TEMPLATES)}"
        )

    return importlib.resources.files(__package__).joinpath(template_name)


def read_template(template_name: str) -> str:
    """Read a template file's content.

    Args:
        template_name: Name of the template file

    Returns:
        Template content as string
    """
    template_path = get_template_path(template_name)
    return template_path.read_text(encoding="utf-8")


def extract_template(template_name: str, destination: Path, overwrite: bool = False) -> Path:
    """Extract a template file to a destination path.

    Args:
        template_name: Name of the template file
        destination: Path where the template should be extracted
        overwrite: If True, overwrite existing files

    Returns:
        Path to the extracted file

    Raises:
        FileExistsError: If destination exists and overwrite is False
    """
    if destination.exists() and not overwrite:
        raise FileExistsError(f"Destination already exists: {destination}")

    content = read_template(template_name)

    # Ensure parent directory exists
    destination.parent.mkdir(parents=True, exist_ok=True)

    destination.write_text(content, encoding="utf-8")
    return destination


def extract_all_templates(
    destination_dir: Path,
    overwrite: bool = False,
    templates: list[str] | None = None,
) -> list[Path]:
    """Extract all (or specified) templates to a directory.

    Args:
        destination_dir: Directory where templates should be extracted
        overwrite: If True, overwrite existing files
        templates: Optional list of specific templates to extract.
                   If None, extracts all available templates.

    Returns:
        List of paths to extracted files
    """
    template_list = templates if templates is not None else AVAILABLE_TEMPLATES
    extracted = []

    for template_name in template_list:
        dest_path = destination_dir / template_name
        extract_template(template_name, dest_path, overwrite=overwrite)
        extracted.append(dest_path)

    return extracted


def list_templates() -> list[str]:
    """List all available template names.

    Returns:
        List of template file names
    """
    return AVAILABLE_TEMPLATES.copy()


def _copy_traversable_to_path(
    source: Traversable,
    destination: Path,
    overwrite: bool = False,
) -> list[Path]:
    """Recursively copy a Traversable resource to a filesystem path.

    Args:
        source: Traversable resource (file or directory)
        destination: Destination path on filesystem
        overwrite: If True, overwrite existing files

    Returns:
        List of paths to extracted files
    """
    extracted: list[Path] = []

    if source.is_file():
        # It's a file - copy it
        if destination.exists() and not overwrite:
            return extracted
        destination.parent.mkdir(parents=True, exist_ok=True)
        content = source.read_text(encoding="utf-8")
        destination.write_text(content, encoding="utf-8")
        extracted.append(destination)
    else:
        # It's a directory - recurse
        destination.mkdir(parents=True, exist_ok=True)
        for child in source.iterdir():
            # Skip Python package artifacts - not needed in extracted templates
            if child.name in ("__pycache__", "__init__.py") or child.name.endswith(".pyc"):
                continue
            child_dest = destination / child.name
            extracted.extend(_copy_traversable_to_path(child, child_dest, overwrite=overwrite))

    return extracted


def extract_github_templates(
    destination: Path,
    overwrite: bool = False,
    template_vars: dict[str, str] | None = None,
) -> list[Path]:
    """Extract .github templates to the destination directory.

    Creates the .github directory structure with:
    - copilot-instructions.md
    - instructions/ (git-practices, session-artifacts, testing-practices)
    - prompts/ (session-start, session-end, verify-feature, etc.)
    - templates/ (init scripts, schemas)

    Args:
        destination: Path where .github directory should be created
        overwrite: If True, overwrite existing files
        template_vars: Optional dict of template variables to substitute
                      (e.g., {"{{PROJECT_NAME}}": "my-project"})

    Returns:
        List of paths to extracted files
    """
    github_dir = destination / ".github"
    extracted: list[Path] = []

    # Get the github_templates package
    try:
        github_templates = importlib.resources.files(GITHUB_TEMPLATES_PACKAGE)
    except ModuleNotFoundError:
        # Fallback for older Python or edge cases
        return extracted

    # Copy all files from the package
    for item in github_templates.iterdir():
        # Skip Python package artifacts
        if item.name in ("__pycache__", "__init__.py") or item.name.endswith(".pyc"):
            continue
        dest_path = github_dir / item.name
        extracted.extend(_copy_traversable_to_path(item, dest_path, overwrite=overwrite))

    # Apply template variable substitution if provided
    if template_vars:
        for file_path in extracted:
            if file_path.suffix in [".md", ".json", ".yaml", ".yml", ".sh", ".ps1"]:
                try:
                    content = file_path.read_text(encoding="utf-8")
                    for var, value in template_vars.items():
                        content = content.replace(var, value)
                    file_path.write_text(content, encoding="utf-8")
                except Exception:
                    # Skip files that can't be processed
                    pass

    return extracted


def get_github_templates_list() -> list[str]:
    """List all files available in the github_templates package.

    Returns:
        List of relative paths within the github_templates
    """
    files: list[str] = []

    try:
        github_templates = importlib.resources.files(GITHUB_TEMPLATES_PACKAGE)
    except ModuleNotFoundError:
        return files

    def _collect_files(traversable: Traversable, prefix: str = "") -> None:
        for item in traversable.iterdir():
            # Skip Python package artifacts
            if item.name in ("__pycache__", "__init__.py") or item.name.endswith(".pyc"):
                continue
            rel_path = f"{prefix}/{item.name}" if prefix else item.name
            if item.is_file():
                files.append(rel_path)
            else:
                _collect_files(item, rel_path)

    _collect_files(github_templates)
    return files
