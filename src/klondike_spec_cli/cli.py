"""Klondike Spec CLI - Main CLI application.

This CLI is built with the Pith library for agent-native progressive discovery.
"""

# Note: Do NOT use `from __future__ import annotations` here.
# It breaks FastAPI's WebSocket type detection at runtime (causes 403 on WS handshake).

import json
import sys
from typing import TYPE_CHECKING

from pith import Argument, Option, Pith, PithException, echo

if TYPE_CHECKING:
    pass

from . import formatting

try:
    from ._version import __version__
except ImportError:
    __version__ = "0.0.0+unknown"

from .commands.admin import (
    completion_command,
    config_command,
    progress_command,
    validate_command,
    version_command,
)
from .commands.agents_cmd import agents_generate_command
from .commands.copilot_cmd import (
    copilot_cleanup_worktrees,
    copilot_list_worktrees,
    copilot_start,
)
from .commands.features import (
    feature_add,
    feature_block,
    feature_edit,
    feature_list,
    feature_prompt,
    feature_show,
    feature_start,
    feature_verify,
)
from .commands.init import init_command, upgrade_command
from .commands.io import export_features_command, import_features_command
from .commands.mcp_cmd import mcp_config, mcp_install, mcp_serve
from .commands.release_cmd import release_command
from .commands.reporting import report_command
from .commands.serve_cmd import serve_command
from .commands.sessions import session_end, session_start
from .data import (
    load_features,
    load_progress,
)
from .models import (
    FeatureStatus,
)

# --- Helper Functions ---


# --- Pith App Definition ---

app = Pith(
    name="klondike",
    pith="Manage agent workflows: init to scaffold, feature to track, session to log work",
)


# --- Commands ---


@app.command(pith="Initialize a new Klondike project in current directory", priority=10)
@app.intents(
    "start new project",
    "initialize klondike",
    "create klondike directory",
    "setup project",
    "init",
    "new project",
    "first time setup",
    "getting started",
    "scaffold project",
    "bootstrap workflow",
    "create features.json",
    "setup github copilot",
)
def init(
    project_name: str | None = Option(None, "--name", "-n", pith="Project name"),
    force: bool = Option(
        False,
        "--force",
        "-f",
        pith="Wipe and reinitialize everything (requires confirmation)",
    ),
    upgrade: bool = Option(
        False, "--upgrade", "-u", pith="Upgrade templates while preserving user data"
    ),
    skip_github: bool = Option(False, "--skip-github", pith="Skip creating .github directory"),
    prd_source: str | None = Option(None, "--prd", pith="Link to PRD document for agent context"),
    agent: str | None = Option(
        None,
        "--agent",
        "-a",
        pith="AI agent to configure: copilot (default), claude, or 'all'",
    ),
) -> None:
    """Initialize a new Klondike Spec project or upgrade an existing one.

    Creates the .klondike directory with features.json, agent-progress.json,
    and config.yaml. Also generates agent-progress.md in the project root.

    Agent Selection (--agent):
        By default, configures GitHub Copilot templates (.github/).
        Use --agent to select which AI coding agent(s) to configure:

        --agent copilot  : GitHub Copilot (default) - .github/ directory
        --agent claude   : Claude Code - CLAUDE.md and .claude/ directory
        --agent all      : Both Copilot and Claude templates

    Upgrade Mode (--upgrade):
        Refreshes templates while preserving your:
        - features.json (feature list and status)
        - agent-progress.json (session history)
        - config.yaml (user preferences like default_category)

        Use with --agent to add a new agent to an existing project:
        $ klondike init --upgrade --agent claude

    Force Mode (--force):
        Complete wipe and reinit. Requires confirmation. Use when:
        - Project structure is corrupted
        - You want to start completely fresh

    Examples:
        $ klondike init                         # New project (Copilot default)
        $ klondike init --agent claude          # New project with Claude Code
        $ klondike init --agent all             # New project with all agents
        $ klondike init --upgrade --agent claude  # Add Claude to existing project
        $ klondike init --name my-project       # New project with custom name
        $ klondike init --upgrade               # Upgrade configured agent templates
        $ klondike init --force                 # Wipe and reinit (with confirmation)
        $ klondike init --skip-github           # Skip agent templates entirely
        $ klondike init --prd ./docs/prd.md

    Related:
        status - Check project status after init
        feature add - Add features to the registry
        upgrade - Alias for 'init --upgrade'
    """
    init_command(project_name, force, upgrade, skip_github, prd_source, agent)


@app.command(pith="Upgrade templates in existing Klondike project", priority=11)
@app.intents(
    "upgrade project",
    "update templates",
    "refresh github templates",
    "update copilot instructions",
    "upgrade klondike",
)
def upgrade(
    skip_github: bool = Option(False, "--skip-github", pith="Skip updating agent templates"),
    prd_source: str | None = Option(None, "--prd", pith="Link to PRD document for agent context"),
    agent: str | None = Option(
        None,
        "--agent",
        "-a",
        pith="AI agent to upgrade or add: copilot, claude, or 'all'",
    ),
) -> None:
    """Upgrade an existing Klondike project (alias for 'init --upgrade').

    Refreshes agent templates to the latest version while preserving:
    - features.json (all your features and their status)
    - agent-progress.json (session history)
    - config.yaml (your preferences like default_category)

    Use --agent to add a new agent or upgrade a specific one.
    Without --agent, upgrades all currently configured agents.

    This is safe to run - it backs up existing templates before upgrading.

    Examples:
        $ klondike upgrade                    # Upgrade configured agents
        $ klondike upgrade --agent claude     # Add Claude Code support
        $ klondike upgrade --agent all        # Upgrade all agent templates
        $ klondike upgrade --skip-github
        $ klondike upgrade --prd ./docs/prd.md

    Related:
        init - Initialize or upgrade a project
        status - Check project status
    """
    upgrade_command(skip_github, prd_source, agent)


@app.command(pith="Show project status and feature summary", priority=20)
@app.intents(
    "show status",
    "project status",
    "how many features",
    "progress overview",
    "summary",
    "what's done",
    "check progress",
    "dashboard",
    "project health",
    "feature count",
    "current state",
    "git status",
    "recent commits",
)
def status(
    json_output: bool = Option(False, "--json", pith="Output as JSON"),
) -> None:
    """Show current project status and feature summary.

    Displays the project name, feature counts by status, overall progress,
    and information about the current/last session.

    Examples:
        $ klondike status
        $ klondike status --json

    Related:
        feature list - Detailed feature listing
        session start - Begin a new session
    """
    registry = load_features()
    progress = load_progress()

    if json_output:
        current_session = progress.get_current_session()
        status_data = {
            "projectName": registry.project_name,
            "version": registry.version,
            "totalFeatures": registry.metadata.total_features,
            "passingFeatures": registry.metadata.passing_features,
            "progressPercent": (
                round(
                    registry.metadata.passing_features / registry.metadata.total_features * 100,
                    1,
                )
                if registry.metadata.total_features > 0
                else 0
            ),
            "byStatus": {
                status.value: len(registry.get_features_by_status(status))
                for status in FeatureStatus
            },
            "currentSession": (current_session.to_dict() if current_session is not None else None),
        }
        echo(json.dumps(status_data, indent=2))
        return

    # Text output with rich formatting
    # Use rich console for colored output
    console = formatting.get_console()

    # Print status summary with colors
    formatting.print_status_summary(registry, f"{registry.project_name} v{registry.version}")

    # Current session info
    current = progress.get_current_session()
    if current:
        console.print(f"[bold]📅 Last Session:[/bold] #{current.session_number} ({current.date})")
        console.print(f"   [dim]Focus:[/dim] {current.focus}")
        console.print()

    # Git status and recent commits
    from klondike_spec_cli.git import (
        format_git_log,
        format_git_status,
        get_git_status,
        get_recent_commits,
    )

    git_status = get_git_status()
    if git_status.is_git_repo:
        console.print(f"[bold]📂 Git Status:[/bold] {format_git_status(git_status)}")
        commits = get_recent_commits(5)
        if commits:
            console.print("[dim]Recent commits:[/dim]")
            console.print(format_git_log(commits))
        console.print()

    # Priority features
    priority = registry.get_priority_features(3)
    if priority:
        console.print("[bold]♠️  Next Priority Features:[/bold]")
        for f in priority:
            status_text = formatting.colored_status(f.status)
            console.print("   ", status_text, f" [cyan]{f.id}[/cyan]: {f.description}")


@app.command(
    name="feature",
    pith="Manage features: add, list, start, verify, block, show, edit, prompt",
    priority=30,
)
@app.intents(
    "manage features",
    "feature operations",
    "add feature",
    "list features",
    "verify feature",
    "edit feature",
    "create feature",
    "track feature",
    "mark complete",
    "feature status",
    "show feature",
    "block feature",
    "start working",
    "update feature",
    "feature details",
    "acceptance criteria",
    "generate prompt",
    "feature prompt",
    "copilot prompt",
)
def feature(
    action: str = Argument(..., pith="Action: add, list, start, verify, block, show, edit, prompt"),
    feature_id: str | None = Argument(
        None, pith="Feature ID (e.g., F001) or description for 'add'"
    ),
    description: str | None = Option(None, "--description", "-d", pith="Feature description"),
    category: str | None = Option(None, "--category", "-c", pith="Feature category"),
    priority: int | None = Option(None, "--priority", "-p", pith="Priority (1-5)"),
    criteria: str | None = Option(None, "--criteria", pith="Acceptance criteria (comma-separated)"),
    add_criteria: str | None = Option(
        None, "--add-criteria", pith="Add acceptance criteria (comma-separated)"
    ),
    evidence: str | None = Option(
        None, "--evidence", "-e", pith="Evidence file paths (comma-separated)"
    ),
    reason: str | None = Option(None, "--reason", "-r", pith="Block reason"),
    status_filter: str | None = Option(None, "--status", "-s", pith="Filter by status"),
    json_output: bool = Option(False, "--json", pith="Output as JSON"),
    notes: str | None = Option(None, "--notes", pith="Additional notes"),
    output: str | None = Option(None, "--output", "-o", pith="Output file path for prompt"),
    interactive: bool = Option(False, "--interactive", "-i", pith="Launch copilot with prompt"),
) -> None:
    """Manage features in the registry.

    Actions:
        add    - Add a new feature (description as positional or --description)
        list   - List all features (optional --status filter)
        start  - Mark feature as in-progress (requires feature_id)
        verify - Mark feature as verified (requires feature_id and --evidence)
        block  - Mark feature as blocked (requires feature_id and --reason)
        show   - Show feature details (requires feature_id)
        edit   - Edit feature (requires feature_id, use --notes or --add-criteria)
        prompt - Generate copilot-ready prompt for a feature (requires feature_id)

    Examples:
        $ klondike feature add "User login" --category core --notes "Use JWT tokens. Handle: expired sessions, invalid creds."
        $ klondike feature add --description "User login" --category core --criteria "Returns JWT,Handles invalid creds" --notes "Implementation: AuthService. Gotchas: Rate limit after 5 failures."
        $ klondike feature list --status not-started
        $ klondike feature start F001
        $ klondike feature verify F001 --evidence test-results/F001.png
        $ klondike feature block F002 --reason "Waiting for API"
        $ klondike feature show F001
        $ klondike feature edit F001 --notes "Implementation notes"
        $ klondike feature edit F001 --add-criteria "Must handle edge cases"
        $ klondike feature prompt F001
        $ klondike feature prompt F001 --output prompt.md
        $ klondike feature prompt F001 --interactive

    Related:
        status - Project overview
        session start - Begin working on features
        copilot start - Launch copilot with context
    """
    if action == "add":
        # For 'add' action, feature_id position is used as description if --description not given
        effective_description = description if description else feature_id
        feature_add(effective_description, category, priority, criteria, notes)
    elif action == "list":
        feature_list(status_filter, json_output)
    elif action == "start":
        feature_start(feature_id)
    elif action == "verify":
        feature_verify(feature_id, evidence)
    elif action == "block":
        feature_block(feature_id, reason)
    elif action == "show":
        feature_show(feature_id, json_output)
    elif action == "edit":
        feature_edit(feature_id, description, category, priority, notes, add_criteria)
    elif action == "prompt":
        feature_prompt(feature_id, output, interactive)
    else:
        raise PithException(
            f"Unknown action: {action}. Use: add, list, start, verify, block, show, edit, prompt"
        )


@app.command(name="session", pith="Manage coding sessions: start, end", priority=40)
@app.intents(
    "start session",
    "end session",
    "begin work",
    "finish work",
    "session management",
    "start coding",
    "end coding",
    "log work",
    "track session",
    "work log",
    "handoff",
    "context bridge",
    "save progress",
)
def session(
    action: str = Argument(..., pith="Action: start, end"),
    focus: str | None = Option(None, "--focus", "-f", pith="Session focus/feature"),
    summary: str | None = Option(None, "--summary", "-s", pith="Session summary"),
    completed: str | None = Option(
        None, "--completed", "-c", pith="Completed items (comma-separated)"
    ),
    blockers: str | None = Option(None, "--blockers", "-b", pith="Blockers encountered"),
    next_steps: str | None = Option(None, "--next", "-n", pith="Next steps (comma-separated)"),
    auto_commit: bool = Option(False, "--auto-commit", pith="Auto-commit changes on session end"),
) -> None:
    """Manage coding sessions.

    Actions:
        start - Begin a new session (validates artifacts, shows status)
        end   - End current session (updates progress log)

    Examples:
        $ klondike session start --focus "F001 - User login"
        $ klondike session end --summary "Completed login form" --completed "Added form,Added validation"
        $ klondike session end --summary "Done" --auto-commit

    Related:
        status - Check project status
        feature start - Mark feature as in-progress
    """
    if action == "start":
        session_start(focus)
    elif action == "end":
        session_end(summary, completed, blockers, next_steps, auto_commit)
    else:
        raise PithException(f"Unknown action: {action}. Use: start, end")


@app.command(pith="Validate artifact integrity", priority=50)
@app.intents(
    "validate artifacts",
    "check integrity",
    "verify features.json",
    "check progress",
    "validate",
    "lint features",
    "check consistency",
    "verify metadata",
    "find issues",
    "health check",
    "audit artifacts",
)
def validate() -> None:
    """Validate Klondike artifact integrity.

    Checks features.json and agent-progress.json for consistency,
    validates metadata counts, and reports any issues.

    Examples:
        $ klondike validate

    Related:
        status - Quick project overview
        session start - Validates on session start
    """
    validate_command()


@app.command(pith="View or set project configuration", priority=52)
@app.intents(
    "view config",
    "set config",
    "configuration",
    "project settings",
    "set prd",
    "prd source",
    "config get",
    "config set",
)
def config(
    key: str | None = Argument(None, pith="Config key to get/set (e.g., prd_source)"),
    value: str | None = Option(None, "--set", "-s", pith="Value to set"),
) -> None:
    """View or set project configuration.

    Without arguments, displays all configuration values.
    With a key, displays that specific value.
    With --set, updates the configuration value.

    Supported keys:
    - prd_source: Link to PRD document for agent context
    - default_category: Default category for new features
    - default_priority: Default priority for new features (1-5)
    - verified_by: Identifier for feature verification
    - progress_output_path: Path for agent-progress.md

    Examples:
        $ klondike config                          # Show all config
        $ klondike config prd_source               # Show PRD source
        $ klondike config prd_source --set ./docs/prd.md  # Set PRD source
        $ klondike config prd_source -s https://example.com/prd

    Related:
        init - Initialize project with --prd option
        status - Show project status
    """
    config_command(key, value)


@app.command(pith="Generate shell completion scripts", priority=55)
@app.intents(
    "shell completion",
    "bash completion",
    "zsh completion",
    "powershell completion",
    "generate completions",
    "tab completion",
    "autocomplete",
    "install completions",
    "enable tab",
)
def completion(
    shell: str = Argument(..., pith="Shell type: bash, zsh, powershell"),
    output: str | None = Option(None, "--output", "-o", pith="Output file path"),
) -> None:
    """Generate shell completion scripts.

    Creates completion scripts for Bash, Zsh, or PowerShell that enable
    tab completion for klondike commands, options, and feature IDs.

    Examples:
        $ klondike completion bash
        $ klondike completion zsh --output ~/.zsh/completions/_klondike
        $ klondike completion powershell >> $PROFILE

    Installation:
        Bash: source <(klondike completion bash)
        Zsh:  klondike completion zsh > ~/.zsh/completions/_klondike
        PowerShell: klondike completion powershell >> $PROFILE

    Related:
        help - Show command help
    """
    completion_command(shell)


@app.command(pith="Regenerate agent-progress.md from JSON", priority=60)
@app.intents(
    "regenerate markdown",
    "update progress file",
    "generate progress",
    "refresh markdown",
    "sync markdown",
    "update agent-progress",
    "export progress",
    "create progress file",
)
def progress(
    output: str | None = Option(None, "--output", "-o", pith="Output file path"),
) -> None:
    """Regenerate agent-progress.md from agent-progress.json.

    Creates a human-readable markdown file from the JSON progress data.

    Examples:
        $ klondike progress
        $ klondike progress --output docs/progress.md

    Related:
        status - Quick status check
        session end - Auto-regenerates on session end
    """
    progress_command(output, force=False)


@app.command(pith="Generate stakeholder progress report", priority=70)
@app.intents(
    "generate report",
    "stakeholder report",
    "progress report",
    "share progress",
    "report",
    "executive summary",
    "status report",
    "email update",
    "team report",
    "project summary",
    "milestone report",
)
def report(
    format_type: str = Option("markdown", "--format", "-f", pith="Output format: markdown, plain"),
    output: str | None = Option(None, "--output", "-o", pith="Output file path"),
    include_details: bool = Option(False, "--details", "-d", pith="Include feature details"),
) -> None:
    """Generate a stakeholder-friendly progress report.

    Creates a formatted report suitable for sharing with stakeholders,
    showing overall progress, completed features, and next steps.

    Examples:
        $ klondike report
        $ klondike report --format plain
        $ klondike report --output report.md --details

    Related:
        status - Quick status check
        progress - Regenerate agent-progress.md
    """
    report_command(format_type, output, include_details)


@app.command(name="import-features", pith="Import features from YAML or JSON file", priority=75)
@app.intents(
    "import features",
    "load features",
    "add features from file",
    "bulk import",
    "restore features",
    "merge features",
    "batch add",
    "import backlog",
    "load yaml",
    "load json",
)
def import_features(
    file_path: str = Argument(..., pith="Path to YAML or JSON file with features"),
    dry_run: bool = Option(False, "--dry-run", pith="Preview import without making changes"),
) -> None:
    """Import features from a YAML or JSON file.

    Imports features from an external file and merges them with existing features.
    Duplicate feature IDs are skipped to prevent data loss.

    File format (YAML or JSON):
        features:
          - description: "Feature description"
            category: core
            priority: 1
            acceptance_criteria:
              - "Criterion 1"
              - "Criterion 2"

    Examples:
        $ klondike import-features features.yaml
        $ klondike import-features backlog.json --dry-run

    Related:
        export-features - Export features to file
        feature add - Add individual features
    """
    import_features_command(file_path, dry_run)


@app.command(name="copilot", pith="Launch GitHub Copilot CLI with klondike context", priority=77)
@app.intents(
    "start copilot",
    "launch copilot",
    "run copilot",
    "copilot agent",
    "ai agent",
    "ai assistant",
    "coding agent",
    "launch ai",
    "start ai",
    "copilot chat",
    "agent mode",
    "worktree session",
    "isolated session",
)
def copilot(
    action: str = Argument(..., pith="Action: start, list, cleanup"),
    model: str | None = Option(
        None, "--model", "-m", pith="Model to use (e.g., claude-sonnet, gpt-4)"
    ),
    resume: bool = Option(False, "--resume", "-r", pith="Resume previous session"),
    feature_id: str | None = Option(None, "--feature", "-f", pith="Focus on specific feature"),
    instructions: str | None = Option(None, "--instructions", "-i", pith="Additional instructions"),
    allow_tools: str | None = Option(
        None, "--allow-tools", pith="Comma-separated list of allowed tools"
    ),
    dry_run: bool = Option(False, "--dry-run", pith="Show command without executing"),
    # Worktree options
    worktree: bool = Option(False, "--worktree", "-w", pith="Run in isolated git worktree"),
    parent_branch: str | None = Option(
        None, "--branch", "-b", pith="Parent branch for worktree (default: current)"
    ),
    session_name: str | None = Option(
        None, "--name", "-n", pith="Custom session/branch name for worktree"
    ),
    cleanup_after: bool = Option(False, "--cleanup", pith="Remove worktree after session ends"),
    apply_changes: bool = Option(
        False, "--apply", pith="Apply worktree changes to main project after session"
    ),
    force: bool = Option(False, "--force", pith="Force cleanup of worktrees"),
) -> None:
    """Launch GitHub Copilot CLI with klondike project context.

    Automatically includes project status, in-progress features, and
    klondike workflow instructions in the prompt context. Pre-configures
    safe tool permissions for file operations and terminal commands.

    Actions:
        start   - Launch copilot with project context
        list    - List active worktree sessions
        cleanup - Remove all worktree sessions

    Worktree Mode (--worktree):
        Creates an isolated git worktree in ~/klondike-worktrees/<project>/
        with a dedicated branch (klondike/<feature-or-session>-<uuid>).
        Changes in the worktree do NOT affect the main project until
        explicitly applied with --apply.

    Examples:
        $ klondike copilot start                      # Launch with project context
        $ klondike copilot start --worktree           # Launch in isolated worktree
        $ klondike copilot start -w --feature F001   # Worktree for feature F001
        $ klondike copilot start -w --cleanup        # Auto-cleanup after session
        $ klondike copilot start -w --apply          # Apply changes after session
        $ klondike copilot list                       # List active worktrees
        $ klondike copilot cleanup                    # Remove all worktrees

    Related:
        status - Check project status first
        feature start - Mark a feature as in-progress
    """
    if action == "start":
        copilot_start(
            model=model,
            resume=resume,
            feature_id=feature_id,
            instructions=instructions,
            allow_tools=allow_tools,
            dry_run=dry_run,
            use_worktree=worktree,
            parent_branch=parent_branch,
            session_name=session_name,
            cleanup_after=cleanup_after,
            apply_changes=apply_changes,
        )
    elif action == "list":
        copilot_list_worktrees()
    elif action == "cleanup":
        copilot_cleanup_worktrees(force=force)
    else:
        raise PithException(f"Unknown action: {action}. Use: start, list, cleanup")


@app.command(name="export-features", pith="Export features to YAML or JSON file", priority=76)
@app.intents(
    "export features",
    "save features",
    "backup features",
    "dump features",
    "share features",
    "export yaml",
    "export json",
    "serialize features",
    "archive features",
)
def export_features(
    output: str = Argument(..., pith="Output file path (.yaml, .yml, or .json)"),
    status_filter: str | None = Option(None, "--status", "-s", pith="Filter by status"),
    include_all: bool = Option(False, "--all", pith="Include all fields including internal ones"),
) -> None:
    """Export features to a YAML or JSON file.

    Exports features from the registry to a file format suitable for
    sharing, backup, or importing into another project.

    Examples:
        $ klondike export-features features.yaml
        $ klondike export-features backlog.json --status not-started
        $ klondike export-features full-export.yaml --all

    Related:
        import-features - Import features from file
        feature list - View features
    """
    export_features_command(output, status_filter, include_all)


@app.command(name="mcp", pith="Manage MCP server for AI agent integration", priority=78)
@app.intents(
    "mcp server",
    "start mcp",
    "run mcp server",
    "install mcp",
    "copilot mcp",
    "ai tools",
    "model context protocol",
    "expose tools",
    "agent tools",
    "serve mcp",
    "mcp config",
    "vscode mcp",
)
def mcp(
    action: str = Argument(..., pith="Action: serve, install, config"),
    transport: str = Option("stdio", "--transport", "-t", pith="Transport: stdio, streamable-http"),
    output: str | None = Option(None, "--output", "-o", pith="Output path for config file"),
) -> None:
    """Manage MCP (Model Context Protocol) server for AI agent integration.

    Exposes klondike tools to AI agents like GitHub Copilot through the
    Model Context Protocol.

    Actions:
        serve   - Start the MCP server (default: stdio transport)
        install - Generate config and install MCP server for copilot
        config  - Generate MCP configuration file

    Tools exposed:
        get_features    - List all features with optional status filter
        get_feature     - Get details for a specific feature
        start_feature   - Mark a feature as in-progress
        verify_feature  - Mark a feature as verified
        block_feature   - Mark a feature as blocked
        get_status      - Get project status summary
        start_session   - Start a new coding session
        end_session     - End the current session
        validate_artifacts - Check artifact integrity

    Examples:
        $ klondike mcp serve
        $ klondike mcp serve --transport streamable-http
        $ klondike mcp config --output mcp-config.json
        $ klondike mcp install

    Related:
        copilot start - Launch copilot with klondike context
        status - Check project status
    """
    if action == "serve":
        mcp_serve(transport)
    elif action == "install":
        mcp_install(output)
    elif action == "config":
        mcp_config(output)
    else:
        raise PithException(f"Unknown action: {action}. Use: serve, install, config")


@app.command(pith="Show klondike version", priority=5)
@app.intents(
    "show version",
    "version number",
    "what version",
    "current version",
    "cli version",
    "klondike version",
    "check version",
)
def version(
    json_output: bool = Option(False, "--json", pith="Output as JSON"),
) -> None:
    """Show the klondike CLI version.

    Displays the version that would be published to PyPI/GitHub.
    Uses dynamic versioning based on git tags via hatch-vcs.

    Version format:
        - On a tag (v0.3.0): Shows "0.3.0"
        - After commits: Shows "0.3.1.dev3" (3 commits after 0.3.0)

    Examples:
        $ klondike version
        $ klondike version --json

    Related:
        release - Create a new release
        status - Show project status
    """
    version_command(verbose=json_output)


@app.command(pith="Generate AGENTS.md from configuration", priority=35)
@app.intents(
    "generate agents",
    "agents markdown",
    "create agents.md",
    "agents file",
)
def agents(action: str = Argument(..., pith="Action: generate")) -> None:
    """Generate AGENTS.md based on klondike configuration and project state.

    Creates AGENTS.md in the repository root with basic agent workflow and context.
    """
    if action != "generate":
        raise PithException("Unknown action: use 'generate'")
    agents_generate_command()


# --- Serve Command ---


@app.command(pith="Start web UI server for project management", priority=79)
@app.intents(
    "start server",
    "web ui",
    "serve web",
    "launch ui",
    "start web server",
)
def serve(
    port: int = Option(8000, "--port", "-p", pith="Port to run server on"),
    host: str = Option("127.0.0.1", "--host", pith="Host to bind server to"),
    open_browser: bool = Option(False, "--open", "-o", pith="Open browser automatically"),
) -> None:
    """Start FastAPI web server for Klondike Spec project management.

    Launches a web UI for managing features, sessions, and project progress.
    Requires .klondike directory in current directory.

    Examples:
        $ klondike serve                  # Start on http://127.0.0.1:8000
        $ klondike serve --port 3000      # Use custom port
        $ klondike serve --host 0.0.0.0   # Allow external connections
        $ klondike serve --open           # Auto-launch browser

    Related:
        status - View project status (CLI alternative)
    """
    serve_command(port, host, open_browser)


# --- Release Command ---


@app.command(pith="Automate version bumping and release tagging", priority=80)
@app.intents(
    "release version",
    "bump version",
    "create release",
    "tag release",
    "publish",
    "version bump",
    "semantic version",
    "patch release",
    "minor release",
    "major release",
    "push tag",
    "prepare release",
)
def release(
    version: str = Argument(
        None,
        pith="Version to release (e.g., 0.2.0). If not provided, shows current version.",
    ),
    bump: str = Option(
        None,
        "--bump",
        "-b",
        pith="Version bump type: major, minor, or patch",
    ),
    message: str = Option(
        None,
        "--message",
        "-m",
        pith="Release message (default: 'Release vX.Y.Z')",
    ),
    dry_run: bool = Option(
        False,
        "--dry-run",
        pith="Show what would be done without making changes",
    ),
    push: bool = Option(
        True,
        "--push/--no-push",
        pith="Push commits and tags to remote",
    ),
    skip_tests: bool = Option(
        False,
        "--skip-tests",
        pith="Skip running tests before release",
    ),
) -> None:
    """Automate version bumping and release tagging.

    Handles the complete release workflow: runs tests, bumps version in
    pyproject.toml, commits, tags, and pushes to trigger CI/CD.

    Examples:
        $ klondike release                    # Show current version
        $ klondike release 0.3.0              # Release version 0.3.0
        $ klondike release --bump patch       # Bump patch (0.2.0 -> 0.2.1)
        $ klondike release --bump minor       # Bump minor (0.2.0 -> 0.3.0)
        $ klondike release --bump major       # Bump major (0.2.0 -> 1.0.0)
        $ klondike release 0.3.0 --dry-run    # Preview release

    Related:
        validate - Check project health before release
        status - View current project state
    """
    release_command(version, bump, message, dry_run, push, skip_tests)


# --- Entry Point ---


def main() -> None:
    """Entry point for klondike CLI."""
    # Check for --no-color flag before running pith
    if "--no-color" in sys.argv:
        formatting.set_no_color(True)
        sys.argv.remove("--no-color")

    app.run()


if __name__ == "__main__":
    main()
