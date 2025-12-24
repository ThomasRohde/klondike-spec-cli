"""Base classes for agent adapters.

This module defines the abstract interface that all agent adapters must implement.
"""

from __future__ import annotations

import importlib.resources
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from importlib.abc import Traversable


class AgentAdapter(ABC):
    """Abstract base class for AI coding agent integrations.

    Each agent adapter provides template extraction and (optionally) launching
    capabilities for a specific AI coding agent.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the agent name (e.g., 'copilot', 'claude').

        This name is used for:
        - CLI --agent option values
        - Config file agent tracking
        - Template package naming
        """
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Return the human-readable agent name (e.g., 'GitHub Copilot', 'Claude Code')."""
        pass

    @property
    @abstractmethod
    def template_package(self) -> str:
        """Return the full package path for this agent's templates.

        Example: 'klondike_spec_cli.templates.copilot_templates'
        """
        pass

    @property
    @abstractmethod
    def output_directory(self) -> str:
        """Return the output directory name for templates.

        This is the directory created in the project root.
        - Copilot: '.github'
        - Claude: '.claude' (plus CLAUDE.md at root)

        Return empty string if files go directly to project root.
        """
        pass

    @property
    def description(self) -> str:
        """Return a short description of the agent."""
        return f"{self.display_name} integration"

    def extract_templates(
        self,
        destination: Path,
        overwrite: bool = False,
        template_vars: dict[str, str] | None = None,
    ) -> list[Path]:
        """Extract agent-specific templates to the destination directory.

        Args:
            destination: Project root directory
            overwrite: If True, overwrite existing files
            template_vars: Optional dict of template variables to substitute
                          (e.g., {"{{PROJECT_NAME}}": "my-project"})

        Returns:
            List of paths to extracted files
        """
        extracted: list[Path] = []

        try:
            templates = importlib.resources.files(self.template_package)
        except ModuleNotFoundError:
            return extracted

        # Determine target directory
        if self.output_directory:
            target_dir = destination / self.output_directory
        else:
            target_dir = destination

        # Copy all files from the package
        for item in templates.iterdir():
            # Skip Python package artifacts
            if item.name in ("__pycache__", "__init__.py") or item.name.endswith(".pyc"):
                continue
            dest_path = target_dir / item.name
            extracted.extend(self._copy_traversable(item, dest_path, overwrite))

        # Apply template variable substitution
        if template_vars:
            self._substitute_vars(extracted, template_vars)

        return extracted

    def _copy_traversable(
        self,
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

        try:
            if source.is_file():
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
                    # Skip Python package artifacts
                    if child.name in (
                        "__pycache__",
                        "__init__.py",
                    ) or child.name.endswith(".pyc"):
                        continue
                    child_dest = destination / child.name
                    extracted.extend(self._copy_traversable(child, child_dest, overwrite))
        except Exception:
            # If copying fails, return what we've extracted so far
            # to allow partial success and continue processing other files
            pass

        return extracted

    def _substitute_vars(
        self,
        files: list[Path],
        template_vars: dict[str, str],
    ) -> None:
        """Apply template variable substitution to extracted files.

        Attempts to substitute variables in all text files. Silently skips
        files that cannot be processed (e.g., encoding errors, permission issues).

        Args:
            files: List of file paths to process
            template_vars: Dict of variable names to values
        """
        substitutable_extensions = {".md", ".json", ".yaml", ".yml", ".sh", ".ps1"}

        for file_path in files:
            if file_path.suffix not in substitutable_extensions:
                continue
            try:
                content = file_path.read_text(encoding="utf-8")
                for var, value in template_vars.items():
                    content = content.replace(var, value)
                file_path.write_text(content, encoding="utf-8")
            except (OSError, UnicodeDecodeError, UnicodeEncodeError):
                # Skip files that can't be read/written or have encoding issues
                # This allows partial success when processing template files
                pass
