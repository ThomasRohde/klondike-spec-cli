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
