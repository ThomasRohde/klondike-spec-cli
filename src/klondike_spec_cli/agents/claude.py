"""Claude Code agent adapter.

This module provides template extraction for Claude Code CLI integration.
"""

from __future__ import annotations

import importlib.resources
from pathlib import Path

from .base import AgentAdapter


class ClaudeAdapter(AgentAdapter):
    """Claude Code CLI integration adapter.

    Claude Code uses a different file structure than Copilot:
    - CLAUDE.md at project root (main instructions)
    - .claude/settings.json (project settings)
    - .claude/commands/*.md (custom slash commands)
    """

    @property
    def name(self) -> str:
        return "claude"

    @property
    def display_name(self) -> str:
        return "Claude Code"

    @property
    def template_package(self) -> str:
        return "klondike_spec_cli.templates.claude_templates"

    @property
    def output_directory(self) -> str:
        # Claude has files both at root (CLAUDE.md) and in .claude/
        # We handle this specially in extract_templates
        return ""

    @property
    def description(self) -> str:
        return "Claude Code CLI with CLAUDE.md and .claude/commands/"

    def extract_templates(
        self,
        destination: Path,
        overwrite: bool = False,
        template_vars: dict[str, str] | None = None,
    ) -> list[Path]:
        """Extract Claude Code templates with special handling.

        Claude templates have a mixed structure:
        - CLAUDE.md goes to project root
        - settings.json goes to .claude/settings.json
        - commands/ goes to .claude/commands/

        Args:
            destination: Project root directory
            overwrite: If True, overwrite existing files
            template_vars: Optional dict of template variables

        Returns:
            List of paths to extracted files
        """
        extracted: list[Path] = []

        try:
            templates = importlib.resources.files(self.template_package)
        except ModuleNotFoundError:
            return extracted

        claude_dir = destination / ".claude"

        for item in templates.iterdir():
            # Skip Python package artifacts
            if item.name in ("__pycache__", "__init__.py") or item.name.endswith(".pyc"):
                continue

            if item.name == "CLAUDE.md":
                # CLAUDE.md goes to project root
                dest_path = destination / "CLAUDE.md"
                extracted.extend(self._copy_traversable(item, dest_path, overwrite))
            elif item.name == "settings.json":
                # settings.json goes to .claude/settings.json
                dest_path = claude_dir / "settings.json"
                extracted.extend(self._copy_traversable(item, dest_path, overwrite))
            elif item.name == "commands":
                # commands/ directory goes to .claude/commands/
                dest_path = claude_dir / "commands"
                extracted.extend(self._copy_traversable(item, dest_path, overwrite))
            elif item.name == "skills":
                # skills/ directory goes to .claude/skills/
                dest_path = claude_dir / "skills"
                extracted.extend(self._copy_traversable(item, dest_path, overwrite))
            else:
                # Other files go to .claude/
                dest_path = claude_dir / item.name
                extracted.extend(self._copy_traversable(item, dest_path, overwrite))

        # Apply template variable substitution
        if template_vars:
            self._substitute_vars(extracted, template_vars)

        return extracted
