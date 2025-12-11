"""GitHub Copilot agent adapter.

This module provides template extraction for GitHub Copilot CLI integration.
The launcher functionality remains in the main copilot.py module for now.
"""

from __future__ import annotations

from .base import AgentAdapter


class CopilotAdapter(AgentAdapter):
    """GitHub Copilot CLI integration adapter."""

    @property
    def name(self) -> str:
        return "copilot"

    @property
    def display_name(self) -> str:
        return "GitHub Copilot"

    @property
    def template_package(self) -> str:
        return "klondike_spec_cli.templates.copilot_templates"

    @property
    def output_directory(self) -> str:
        return ".github"

    @property
    def description(self) -> str:
        return "GitHub Copilot CLI with copilot-instructions.md and prompt templates"
