"""GitHub Copilot CLI integration with worktree support.

Provides functions for launching GitHub Copilot CLI with klondike context,
including support for isolated git worktree sessions.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from pith import echo

from .models import Feature, FeatureRegistry
from .worktree import (
    WorktreeConfig,
    WorktreeError,
    WorktreeInfo,
    cleanup_worktree,
    create_worktree,
    get_worktree_diff,
    list_worktrees,
)


@dataclass
class CopilotConfig:
    """Configuration for launching Copilot."""

    model: str | None = None
    resume: bool = False
    feature_id: str | None = None
    instructions: str | None = None
    allow_tools: str | None = None
    dry_run: bool = False

    # Worktree settings
    use_worktree: bool = False
    parent_branch: str | None = None
    session_name: str | None = None
    cleanup_after: bool = False
    apply_changes: bool = False


def find_copilot_executable() -> str | None:
    """Find the real GitHub Copilot CLI executable.

    On Windows, shutil.which("copilot") may find a PowerShell wrapper script
    (copilot.ps1) instead of the actual executable. We need to find:
    - Windows: copilot.cmd (npm batch wrapper) or node calling the JS directly
    - Unix/WSL: copilot (shell script from npm)

    Returns the path to the executable, or None if not found.
    """
    # First, try to find the npm-installed copilot
    if sys.platform == "win32":
        # On Windows, look for copilot.cmd specifically in npm global bin
        # This avoids the VS Code PS1 wrapper that shutil.which might find first

        # Method 1: Check npm global prefix
        try:
            result = subprocess.run(
                ["npm", "config", "get", "prefix"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                npm_prefix = result.stdout.strip()
                copilot_cmd = Path(npm_prefix) / "copilot.cmd"
                if copilot_cmd.exists():
                    return str(copilot_cmd)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        # Method 2: Check common npm locations
        common_paths = [
            Path(os.environ.get("APPDATA", "")) / "npm" / "copilot.cmd",
            Path(os.environ.get("LOCALAPPDATA", "")) / "npm" / "copilot.cmd",
        ]
        for path in common_paths:
            if path.exists():
                return str(path)

        # Method 3: Fall back to shutil.which but verify it's not a PS1 file
        copilot_path = shutil.which("copilot")
        if copilot_path:
            # If it's a .ps1 file, it won't work with subprocess.run directly
            if not copilot_path.lower().endswith(".ps1"):
                return copilot_path
            # Try to find copilot.cmd in the same directory
            copilot_dir = Path(copilot_path).parent
            copilot_cmd = copilot_dir / "copilot.cmd"
            if copilot_cmd.exists():
                return str(copilot_cmd)

    else:
        # On Unix/Linux/WSL, shutil.which should work correctly
        copilot_path = shutil.which("copilot")
        if copilot_path:
            return copilot_path

    return None


def _load_prompt_template(template_name: str) -> str:
    """Load a prompt template from the templates directory.

    Args:
        template_name: Name of the template file (e.g., 'session-start.prompt.md')

    Returns:
        The template content, or a fallback message if not found
    """
    from importlib import resources

    try:
        # Load from package templates
        files = resources.files("klondike_spec_cli.templates.copilot_templates.prompts")
        template_path = files.joinpath(template_name)
        content = template_path.read_text(encoding="utf-8")

        # Strip the frontmatter (everything between first ``` and ```)
        # The prompt files have ````prompt ... ```` wrapper
        lines = content.strip().split("\n")

        # Find content between frontmatter markers
        start_idx = 0
        end_idx = len(lines)

        # Skip the opening ````prompt or similar
        if lines and lines[0].startswith("```"):
            start_idx = 1

        # Skip YAML frontmatter if present
        if start_idx < len(lines) and lines[start_idx] == "---":
            for i in range(start_idx + 1, len(lines)):
                if lines[i] == "---":
                    start_idx = i + 1
                    break

        # Skip closing ````
        if lines and lines[-1].startswith("```"):
            end_idx = len(lines) - 1

        return "\n".join(lines[start_idx:end_idx]).strip()

    except (FileNotFoundError, TypeError):
        return f"(Template '{template_name}' not found - proceed with standard session startup)"


def build_prompt(
    focus_feature: Feature | None = None,
    instructions: str | None = None,
    worktree_info: WorktreeInfo | None = None,
) -> str:
    """Build a brief prompt for Copilot.

    Behavioral rules and project context come from .github/copilot-instructions.md
    which Copilot CLI auto-loads. This function only needs to specify the task.

    Args:
        focus_feature: Optional feature to focus on
        instructions: Additional instructions
        worktree_info: Worktree information if running in worktree

    Returns:
        The prompt string (brief task description)
    """
    prompt_parts: list[str] = []

    if worktree_info:
        # Worktree mode - Copilot reads .github/copilot-instructions.md for rules
        # We only need to specify WHAT to do, not HOW to behave

        if focus_feature:
            # Feature implementation task
            prompt_parts.append(f"Implement {focus_feature.id}: {focus_feature.description}")
            prompt_parts.append("")
            if focus_feature.acceptance_criteria:
                prompt_parts.append("Acceptance criteria:")
                for ac in focus_feature.acceptance_criteria:
                    prompt_parts.append(f"- {ac}")
                prompt_parts.append("")
            prompt_parts.append(
                "You are in an isolated git worktree. Implement the feature and commit when done."
            )
        else:
            # No feature specified - let Copilot pick based on klondike status
            prompt_parts.append(
                "Run `klondike status` to see the project state and pick a feature to implement."
            )
            prompt_parts.append("You are in an isolated git worktree.")
    else:
        # Normal mode - use template for session startup
        template_content = _load_prompt_template("session-start.prompt.md")
        prompt_parts.append(template_content)

        # Add feature focus if specified
        if focus_feature:
            prompt_parts.append("")
            prompt_parts.append(
                f"Focus on implementing {focus_feature.id}: {focus_feature.description}"
            )
            if focus_feature.acceptance_criteria:
                prompt_parts.append("Acceptance criteria:")
                for ac in focus_feature.acceptance_criteria:
                    prompt_parts.append(f"- {ac}")

    # Additional instructions from CLI
    if instructions:
        prompt_parts.append("")
        prompt_parts.append(instructions)

    return "\n".join(prompt_parts)


def build_copilot_command(
    copilot_path: str,
    prompt: str,
    config: CopilotConfig,
) -> list[str]:
    """Build the copilot CLI command.

    Args:
        copilot_path: Path to copilot executable
        prompt: The prompt to send
        config: Copilot configuration

    Returns:
        Command as list of strings
    """
    cmd = [copilot_path]

    if config.resume:
        cmd.append("--resume")

    if config.model:
        cmd.extend(["--model", config.model])

    # Tool permissions
    if config.allow_tools:
        tools = config.allow_tools.split(",")
        for tool in tools:
            cmd.extend(["--allow-tool", tool.strip()])
    else:
        # Default to allowing all tools for non-interactive workflow
        cmd.append("--allow-all-tools")

    # Add the prompt for non-interactive execution
    cmd.extend(["--prompt", prompt])

    return cmd


def launch_copilot(
    config: CopilotConfig,
    registry: FeatureRegistry,
    project_dir: Path | None = None,
) -> None:
    """Launch GitHub Copilot CLI with project context.

    Args:
        config: Copilot configuration
        registry: Feature registry for context
        project_dir: Project directory (default: cwd)

    Raises:
        CopilotError: If copilot cannot be launched
    """
    from pith import PithException

    from .validation import validate_feature_id

    project_dir = project_dir or Path.cwd()

    # Check if copilot CLI is available
    copilot_path = find_copilot_executable()
    if not copilot_path and not config.dry_run:
        raise PithException(
            "GitHub Copilot CLI not found. Install with: npm install -g @github/copilot\n"
            "Or see: https://docs.github.com/en/copilot/github-copilot-in-the-cli"
        )

    # Determine focus feature
    focus_feature = None
    if config.feature_id:
        validated_id = validate_feature_id(config.feature_id)
        focus_feature = registry.get_feature(validated_id)
        if not focus_feature:
            raise PithException(f"Feature not found: {validated_id}")

    # Handle worktree mode
    worktree_info: WorktreeInfo | None = None
    working_dir = project_dir

    if config.use_worktree:
        if config.dry_run:
            # In dry-run mode, simulate worktree creation without actually creating it
            from .worktree import (
                generate_branch_name,
                generate_worktree_dir_name,
                get_current_branch,
                get_project_worktrees_dir,
            )

            parent_branch = config.parent_branch or get_current_branch(project_dir)
            session_uuid = "dry-run-uuid"
            branch_name = generate_branch_name(
                feature_id=focus_feature.id if focus_feature else None,
                session_name=config.session_name,
                session_uuid=session_uuid,
            )
            worktree_dir_name = generate_worktree_dir_name(
                feature_id=focus_feature.id if focus_feature else None,
                session_name=config.session_name,
                session_uuid=session_uuid,
            )
            worktree_path = get_project_worktrees_dir(project_dir) / worktree_dir_name

            worktree_info = WorktreeInfo(
                worktree_path=worktree_path,
                branch_name=branch_name,
                parent_branch=parent_branch,
                session_id=session_uuid,
                created_at="(dry-run)",
                project_dir=project_dir,
                feature_id=focus_feature.id if focus_feature else None,
            )
            working_dir = worktree_path

            echo("🌳 Would create isolated git worktree...")
            echo(f"   📂 Worktree: {worktree_path}")
            echo(f"   🌿 Branch: {branch_name}")
            echo(f"   📍 Parent: {parent_branch}")
            echo("")
        else:
            echo("🌳 Creating isolated git worktree...")

            worktree_config = WorktreeConfig(
                project_dir=project_dir,
                parent_branch=config.parent_branch,
                session_name=config.session_name,
                feature_id=focus_feature.id if focus_feature else None,
            )

            try:
                worktree_info = create_worktree(worktree_config)
                working_dir = worktree_info.worktree_path

                echo(f"   📂 Worktree: {worktree_info.worktree_path}")
                echo(f"   🌿 Branch: {worktree_info.branch_name}")
                echo(f"   📍 Parent: {worktree_info.parent_branch}")
                echo("")

            except WorktreeError as e:
                raise PithException(f"Failed to create worktree: {e}") from e

    # Build prompt
    prompt = build_prompt(
        focus_feature=focus_feature,
        instructions=config.instructions,
        worktree_info=worktree_info,
    )

    # Build command
    cmd = build_copilot_command(
        copilot_path=copilot_path or "copilot",
        prompt=prompt,
        config=config,
    )

    if config.dry_run:
        echo("🔍 Dry run - would execute:")
        echo("")
        echo(f"  {' '.join(cmd)}")
        if worktree_info:
            echo(f"  (in directory: {working_dir})")
        echo("")
        echo("📋 Context prompt:")
        echo("---")
        echo(prompt)
        echo("---")
        return

    # Show what we're doing
    echo("🚀 Launching GitHub Copilot with klondike context...")
    if worktree_info:
        echo(f"   🌳 Worktree: {worktree_info.worktree_path}")
    if focus_feature:
        echo(f"   📋 Focus: {focus_feature.id} - {focus_feature.description}")
    if config.model:
        echo(f"   🤖 Model: {config.model}")
    if config.resume:
        echo("   🔄 Resuming previous session")
    echo("")

    # Launch copilot in the working directory
    try:
        subprocess.run(cmd, check=True, cwd=working_dir)
    except subprocess.CalledProcessError as e:
        # Don't cleanup on error - let user investigate
        raise PithException(f"Copilot exited with error code {e.returncode}") from e
    except FileNotFoundError as e:
        raise PithException("GitHub Copilot CLI not found in PATH") from e

    # Handle post-session cleanup/apply
    if worktree_info:
        _handle_worktree_cleanup(worktree_info, config)


def _handle_worktree_cleanup(worktree_info: WorktreeInfo, config: CopilotConfig) -> None:
    """Handle worktree cleanup after copilot session.

    Args:
        worktree_info: The worktree that was used
        config: Copilot configuration with cleanup settings
    """
    from pith import PithException

    echo("")
    echo("🌳 Copilot session ended in worktree")

    # Check if there are changes
    diff = get_worktree_diff(worktree_info.worktree_path, worktree_info.parent_branch) or ""
    has_changes = bool(diff.strip())

    if has_changes:
        echo("   📝 Changes detected in worktree")

        if config.apply_changes:
            echo("   📥 Applying changes to main project...")
            from .worktree import apply_worktree_changes

            try:
                apply_worktree_changes(worktree_info)
                echo("   ✅ Changes applied successfully")

                # Auto-cleanup after successful apply (changes are now in main project)
                echo("   🧹 Cleaning up worktree...")
                try:
                    cleanup_worktree(worktree_info, force=True)
                    echo("   ✅ Worktree removed")
                except WorktreeError as e:
                    echo(f"   ⚠️  Failed to cleanup: {e}")
                    echo("   💡 Run: klondike copilot cleanup --force")
            except WorktreeError as e:
                raise PithException(f"Failed to apply changes: {e}") from e
        elif config.cleanup_after:
            echo("   🧹 Cleaning up worktree...")
            try:
                cleanup_worktree(worktree_info, force=True)
                echo("   ✅ Worktree removed")
            except WorktreeError as e:
                echo(f"   ⚠️  Failed to cleanup: {e}")
        else:
            echo("")
            echo("💡 Worktree preserved. To manage:")
            echo(f"   cd {worktree_info.worktree_path}")
            echo("   # Or cleanup with: klondike copilot cleanup --force")
    else:
        echo("   ℹ️  No changes detected")

        if config.cleanup_after:
            echo("   🧹 Cleaning up worktree...")
            try:
                cleanup_worktree(worktree_info, force=True)
                echo("   ✅ Worktree removed")
            except WorktreeError as e:
                echo(f"   ⚠️  Failed to cleanup: {e}")


def list_copilot_worktrees(project_dir: Path | None = None) -> list[WorktreeInfo]:
    """List all copilot worktrees for the project.

    Args:
        project_dir: Project directory (default: cwd)

    Returns:
        List of WorktreeInfo
    """
    project_dir = project_dir or Path.cwd()
    return list_worktrees(project_dir)


def cleanup_copilot_worktrees(
    project_dir: Path | None = None,
    force: bool = False,
) -> int:
    """Cleanup all copilot worktrees for the project.

    Args:
        project_dir: Project directory (default: cwd)
        force: Force cleanup even with uncommitted changes

    Returns:
        Number of worktrees cleaned up
    """
    project_dir = project_dir or Path.cwd()
    worktrees = list_worktrees(project_dir)

    cleaned = 0
    for wt in worktrees:
        try:
            cleanup_worktree(wt, force=force)
            echo(f"   ✅ Removed: {wt.branch_name}")
            cleaned += 1
        except WorktreeError as e:
            echo(f"   ⚠️  Failed to remove {wt.branch_name}: {e}")

    return cleaned
