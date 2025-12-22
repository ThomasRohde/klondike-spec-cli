"""Klondike Spec CLI - Main CLI application.

This CLI is built with the Pith library for agent-native progressive discovery.
"""

# Note: Do NOT use `from __future__ import annotations` here.
# It breaks FastAPI's WebSocket type detection at runtime (causes 403 on WS handshake).

import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from pith import Argument, Option, Pith, PithException, echo

if TYPE_CHECKING:
    pass

from . import formatting

try:
    from ._version import __version__
except ImportError:
    __version__ = "0.0.0+unknown"

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
from .commands.reporting import report_command
from .commands.sessions import session_end, session_start
from .data import (
    CONFIG_FILE,
    get_klondike_dir,
    load_config,
    load_features,
    load_progress,
    regenerate_progress_md,
)
from .git import (
    get_git_status,
    get_tags,
    git_add_all,
    git_commit,
    git_push,
    git_push_tag,
    git_tag,
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
        console.print("[bold]🎯 Next Priority Features:[/bold]")
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
    issues: list[str] = []

    try:
        registry = load_features()
    except Exception as e:
        echo(f"❌ Failed to load features.json: {e}")
        return

    try:
        progress = load_progress()
    except Exception as e:
        echo(f"❌ Failed to load agent-progress.json: {e}")
        return

    # Check features.json
    echo("🔍 Checking features.json...")

    actual_total = len(registry.features)
    actual_passing = sum(1 for f in registry.features if f.passes)

    if registry.metadata.total_features != actual_total:
        issues.append(
            f"metadata.totalFeatures ({registry.metadata.total_features}) != actual ({actual_total})"
        )

    if registry.metadata.passing_features != actual_passing:
        issues.append(
            f"metadata.passingFeatures ({registry.metadata.passing_features}) != actual ({actual_passing})"
        )

    # Check for duplicate IDs
    ids = [f.id for f in registry.features]
    duplicates = [id for id in ids if ids.count(id) > 1]
    if duplicates:
        issues.append(f"Duplicate feature IDs: {set(duplicates)}")

    # Check feature ID format
    import re

    for f in registry.features:
        if not re.match(r"^F\d{3}$", f.id):
            issues.append(f"Invalid feature ID format: {f.id}")

    # Check verified features have evidence
    for f in registry.features:
        if f.status == FeatureStatus.VERIFIED and not f.evidence_links:
            issues.append(f"Feature {f.id} is verified but has no evidence links")

    # Check agent-progress.json
    echo("🔍 Checking agent-progress.json...")

    # Check session numbers are sequential
    session_nums = [s.session_number for s in progress.sessions]
    expected = list(range(1, len(session_nums) + 1))
    if session_nums != expected:
        issues.append(f"Session numbers not sequential: {session_nums}")

    # Report results
    echo("")
    if issues:
        echo(f"❌ Found {len(issues)} issue(s):")
        for issue in issues:
            echo(f"   • {issue}")
        echo("")
        echo("Run 'klondike session start' to auto-fix metadata counts.")
    else:
        echo("✅ All artifacts valid!")
        echo(f"   Features: {actual_total} total, {actual_passing} passing")
        echo(f"   Sessions: {len(progress.sessions)}")


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
    root = Path.cwd()
    cfg = load_config(root)
    klondike_dir = get_klondike_dir(root)

    if key is None:
        # Show all config
        echo("⚙️  Configuration:")
        echo(f"   default_category: {cfg.default_category}")
        echo(f"   default_priority: {cfg.default_priority}")
        echo(f"   verified_by: {cfg.verified_by}")
        echo(f"   progress_output_path: {cfg.progress_output_path}")
        echo(f"   auto_regenerate_progress: {cfg.auto_regenerate_progress}")
        echo(f"   prd_source: {cfg.prd_source or '(not set)'}")
        return

    # Normalize key name
    key = key.lower().replace("-", "_")

    if value is not None:
        # Set value
        if key == "prd_source":
            cfg.prd_source = value if value.lower() != "null" else None
        elif key == "default_category":
            # Accept any category string
            cfg.default_category = value.lower()
        elif key == "default_priority":
            try:
                priority = int(value)
                if not 1 <= priority <= 5:
                    raise ValueError()
                cfg.default_priority = priority
            except ValueError:
                raise PithException("Priority must be an integer 1-5") from None
        elif key == "verified_by":
            cfg.verified_by = value
        elif key == "progress_output_path":
            cfg.progress_output_path = value
        elif key == "auto_regenerate_progress":
            cfg.auto_regenerate_progress = value.lower() in ("true", "1", "yes")
        else:
            raise PithException(f"Unknown config key: {key}")

        cfg.save(klondike_dir / CONFIG_FILE)
        echo(f"✅ Set {key} = {value}")

        # Regenerate progress.md if prd_source changed
        if key == "prd_source":
            regenerate_progress_md(root)
            echo("   📄 Regenerated agent-progress.md")
        return

    # Get specific value
    if key == "prd_source":
        echo(cfg.prd_source or "(not set)")
    elif key == "default_category":
        echo(cfg.default_category)
    elif key == "default_priority":
        echo(str(cfg.default_priority))
    elif key == "verified_by":
        echo(cfg.verified_by)
    elif key == "progress_output_path":
        echo(cfg.progress_output_path)
    elif key == "auto_regenerate_progress":
        echo(str(cfg.auto_regenerate_progress).lower())
    else:
        raise PithException(f"Unknown config key: {key}")


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
    from klondike_spec_cli.completion import (
        generate_bash_completion,
        generate_powershell_completion,
        generate_zsh_completion,
    )

    generators = {
        "bash": generate_bash_completion,
        "zsh": generate_zsh_completion,
        "powershell": generate_powershell_completion,
    }

    if shell not in generators:
        raise PithException(f"Unsupported shell: {shell}. Use: bash, zsh, powershell")

    content = generators[shell]()

    if output:
        from pathlib import Path

        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content)
        echo(f"✅ Completion script written to: {output_path}")
        if shell == "bash":
            echo(f"   Run: source {output_path}")
        elif shell == "zsh":
            echo("   Add the directory to your fpath and restart shell")
        elif shell == "powershell":
            echo("   Run: . " + str(output_path))
    else:
        # Print to stdout for piping
        print(content)


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
    progress_log = load_progress()
    config = load_config()

    root = Path.cwd()
    if output:
        output_path = Path(output)
    else:
        output_path = root / config.progress_output_path

    progress_log.save_markdown(output_path)
    echo(f"✅ Generated {output_path}")


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
    from klondike_spec_cli import __version__

    if json_output:
        version_info = {
            "version": __version__,
            "package": "klondike-spec-cli",
        }
        echo(json.dumps(version_info, indent=2))
        return

    echo(f"klondike-spec-cli {__version__}")


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

    root = Path.cwd()
    registry = load_features(root)
    progress = load_progress(root)
    config = load_config(root)

    lines: list[str] = []
    lines.append(f"# {registry.project_name} — Agents Guide")
    lines.append("")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")
    lines.append("## Workflow Overview")
    lines.append("- Use klondike CLI to manage features and sessions")
    lines.append("- Do not edit .klondike JSON files directly; use CLI commands")
    lines.append("- Keep one feature in progress at a time")
    lines.append("")
    lines.append("## Key Commands")
    lines.append("```bash")
    lines.append("klondike status")
    lines.append("klondike feature list")
    lines.append('klondike session start --focus "F00X - description"')
    lines.append("klondike feature start F00X")
    lines.append("```")
    lines.append("")
    lines.append("## Configuration")
    lines.append(f"- default_category: {config.default_category}")
    lines.append(f"- default_priority: {config.default_priority}")
    lines.append(f"- verified_by: {config.verified_by}")
    lines.append(f"- progress_output_path: {config.progress_output_path}")
    lines.append("")
    lines.append("## Current Priority Features")
    for pf in progress.quick_reference.priority_features:
        lines.append(f"- {pf.id}: {pf.description} ({pf.status})")

    output_path = root / "AGENTS.md"
    output_path.write_text("\n".join(lines), encoding="utf-8")
    echo(f"✅ Generated {output_path}")


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
    host: str = Option("127.0.0.1", "--host", "-h", pith="Host to bind server to"),
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
    try:
        import uvicorn
        from fastapi import FastAPI, WebSocket, WebSocketDisconnect
        from fastapi.responses import FileResponse, HTMLResponse
        from fastapi.staticfiles import StaticFiles
    except ImportError as err:
        raise PithException(
            "FastAPI and uvicorn are required for serve command.\n"
            "Install with: pip install klondike-spec-cli[serve]"
        ) from err

    try:
        from watchdog.events import FileSystemEventHandler
        from watchdog.observers import Observer
    except ImportError as err:
        raise PithException(
            "watchdog is required for serve command.\n"
            "Install with: pip install klondike-spec-cli[serve]"
        ) from err

    # Verify .klondike directory exists
    root = Path.cwd()
    klondike_dir = get_klondike_dir(root)
    if not klondike_dir:
        raise PithException(
            "No .klondike directory found in current directory.\n"
            "Run 'klondike init' first to initialize a project."
        )

    # Initialize FastAPI app
    app_instance = FastAPI(
        title="Klondike Spec CLI",
        description="Project management web UI for agent workflows",
        version=__version__,
    )

    # Custom middleware to add CORS headers for local development
    from starlette.requests import Request

    @app_instance.middleware("http")
    async def add_cors_headers(request: Request, call_next):
        """Add CORS headers to all responses for local development."""
        # Handle preflight OPTIONS requests
        if request.method == "OPTIONS":
            from starlette.responses import Response

            response = Response()
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "*"
            response.headers["Access-Control-Allow-Headers"] = "*"
            return response

        response = await call_next(request)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
        return response

    # WebSocket connection manager
    class ConnectionManager:
        """Manages WebSocket connections and broadcasts events."""

        def __init__(self):
            self.active_connections: list[WebSocket] = []

        async def connect(self, websocket: WebSocket):
            await websocket.accept()
            self.active_connections.append(websocket)

        def disconnect(self, websocket: WebSocket):
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)

        async def broadcast(self, event_type: str, data: dict):
            """Broadcast an event to all connected clients."""
            message = {
                "type": event_type,
                "data": data,
                "timestamp": datetime.now().isoformat(),
            }
            disconnected = []
            for connection in self.active_connections:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.append(connection)

            # Clean up disconnected clients
            for conn in disconnected:
                self.disconnect(conn)

    manager = ConnectionManager()

    # File watcher for detecting external CLI changes
    class KlondikeFileHandler(FileSystemEventHandler):
        """Watches .klondike directory for changes."""

        def __init__(self, manager: ConnectionManager, root_path: Path):
            self.manager = manager
            self.root_path = root_path
            self.last_event_time = {}
            super().__init__()

        def _should_process_event(self, path: str) -> bool:
            """Debounce events - only process if > 100ms since last event for this file."""
            import time

            now = time.time()
            if path in self.last_event_time:
                if now - self.last_event_time[path] < 0.1:
                    return False
            self.last_event_time[path] = now
            return True

        def on_modified(self, event):
            if event.is_directory:
                return

            path = Path(event.src_path)
            if not self._should_process_event(str(path)):
                return

            # Detect which file changed and emit appropriate event
            if path.name == "features.json":
                self._emit_features_changed()
            elif path.name == "agent-progress.json":
                self._emit_session_changed()
            elif path.name == "config.yaml":
                self._emit_config_changed()

        def _emit_features_changed(self):
            """Emit featureUpdated event."""
            try:
                from .data import load_features

                registry = load_features(self.root_path)
                # Create task to run async broadcast
                import asyncio

                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                loop.create_task(
                    self.manager.broadcast(
                        "featureUpdated",
                        {
                            "total": len(registry.features),
                            "passing": sum(1 for f in registry.features if f.passes),
                        },
                    )
                )
            except Exception:
                pass  # Silently ignore errors in file watcher

        def _emit_session_changed(self):
            """Emit sessionUpdated event."""
            try:
                from .data import load_progress

                progress = load_progress(self.root_path)
                import asyncio

                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                loop.create_task(
                    self.manager.broadcast(
                        "sessionUpdated",
                        {
                            "status": progress.current_status,
                            "sessionCount": len(progress.sessions),
                        },
                    )
                )
            except Exception:
                pass

        def _emit_config_changed(self):
            """Emit configChanged event."""
            import asyncio

            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            loop.create_task(self.manager.broadcast("configChanged", {}))

    # Start file watcher
    event_handler = KlondikeFileHandler(manager, root)
    observer = Observer()
    observer.schedule(event_handler, str(klondike_dir), recursive=False)
    observer.start()

    # Get static files directory from package
    static_dir = Path(__file__).parent / "static"
    if not static_dir.exists():
        raise PithException(
            f"Static files directory not found: {static_dir}\n"
            "This may indicate a broken installation."
        )

    # Mount static files
    app_instance.mount("/assets", StaticFiles(directory=str(static_dir / "assets")), name="assets")

    @app_instance.get("/health")
    async def health():
        """Health check endpoint."""
        return {"status": "ok", "version": __version__}

    @app_instance.websocket("/api/updates")
    async def websocket_endpoint(websocket: WebSocket):
        """WebSocket endpoint for real-time updates.

        Emits events:
        - featureAdded: When a new feature is added
        - featureUpdated: When features change (add/update/status)
        - sessionStarted: When a session starts
        - sessionEnded: When a session ends
        - sessionUpdated: When session data changes
        - configChanged: When configuration is updated
        """
        await manager.connect(websocket)
        try:
            # Send initial sync event
            from .data import load_features, load_progress

            registry = load_features(root)
            progress = load_progress(root)

            await websocket.send_json(
                {
                    "type": "connected",
                    "data": {
                        "features": {
                            "total": len(registry.features),
                            "passing": sum(1 for f in registry.features if f.passes),
                        },
                        "session": {
                            "status": progress.current_status,
                            "sessionCount": len(progress.sessions),
                        },
                    },
                    "timestamp": datetime.now().isoformat(),
                }
            )

            # Keep connection alive and wait for disconnect
            while True:
                # Wait for messages (though we don't expect any from client)
                try:
                    await websocket.receive_text()
                except WebSocketDisconnect:
                    break
        except WebSocketDisconnect:
            pass
        finally:
            manager.disconnect(websocket)

    @app_instance.get("/api/status")
    async def api_status():
        """Get project status overview.

        Returns project metadata, progress counts, feature status summary,
        current session info, priority features, and recent git commits.
        """
        from .data import load_config, load_features, load_progress
        from .git import get_git_status, get_recent_commits

        try:
            # Load project data
            load_config(root)
            registry = load_features(root)
            progress_log = load_progress(root)

            # Calculate progress
            total = len(registry.features)
            passing = sum(1 for f in registry.features if f.passes)
            percent = round((passing / total * 100), 1) if total > 0 else 0.0

            # Count features by status
            by_status = {
                "not-started": 0,
                "in-progress": 0,
                "blocked": 0,
                "verified": 0,
            }
            for feature in registry.features:
                status_key = (
                    feature.status.value if hasattr(feature.status, "value") else feature.status
                )
                if status_key in by_status:
                    by_status[status_key] += 1

            # Get current session (if active)
            current_session = None
            if progress_log.sessions and progress_log.current_status == "In Progress":
                last_session = progress_log.sessions[-1]
                current_session = {
                    "id": last_session.session_number,
                    "focus": last_session.focus,
                    "agent": last_session.agent,
                    "date": last_session.date,
                }

            # Get priority features
            priority_features = []
            for pf in progress_log.quick_reference.priority_features[:3]:
                priority_features.append(
                    {
                        "id": pf.id,
                        "description": pf.description,
                        "status": pf.status,
                    }
                )

            # Get git status and recent commits
            git_status_obj = get_git_status(root)
            git_data = None
            if git_status_obj.is_git_repo:
                recent_commits = get_recent_commits(5, root)
                git_data = {
                    "branch": git_status_obj.current_branch,
                    "clean": git_status_obj.clean,
                    "staged": git_status_obj.staged_count,
                    "unstaged": git_status_obj.unstaged_count,
                    "untracked": git_status_obj.untracked_count,
                    "recent_commits": [
                        {
                            "hash": c.short_hash,
                            "message": c.message,
                            "author": c.author,
                            "date": c.date,
                        }
                        for c in recent_commits
                    ],
                }

            return {
                "project_name": root.name,
                "project_version": registry.version,
                "completion_percentage": percent,
                "feature_counts": {
                    "total": total,
                    "verified": by_status["verified"],
                    "blocked": by_status["blocked"],
                    "in_progress": by_status["in-progress"],
                    "not_started": by_status["not-started"],
                },
                "last_session": current_session,
                "priority_features": priority_features,
                "git_status": git_data,
            }

        except Exception as e:
            return {"error": str(e)}

    @app_instance.get("/api/features")
    async def api_features_list(status: str | None = None):
        """Get all features with optional status filter.

        Query Parameters:
            status: Filter by status (not-started, in-progress, blocked, verified)

        Returns:
            List of features with all properties.
        """
        from .data import load_features
        from .models import FeatureStatus

        try:
            registry = load_features(root)
            features = registry.features

            # Apply status filter if provided
            if status:
                try:
                    status_filter = FeatureStatus(status)
                    features = [f for f in features if f.status == status_filter]
                except ValueError:
                    return {
                        "error": f"Invalid status: {status}. Use: not-started, in-progress, blocked, verified"
                    }

            return {
                "features": [f.to_dict() for f in features],
                "total": len(features),
            }
        except Exception as e:
            return {"error": str(e)}

    @app_instance.get("/api/features/{feature_id}")
    async def api_feature_get(feature_id: str):
        """Get single feature by ID.

        Path Parameters:
            feature_id: Feature ID (e.g., F001)

        Returns:
            Feature details or 404 error.
        """
        from .data import load_features

        try:
            registry = load_features(root)
            registry._build_index()

            if feature_id not in registry._feature_index:
                from fastapi import HTTPException

                raise HTTPException(status_code=404, detail=f"Feature not found: {feature_id}")

            feature = registry._feature_index[feature_id]
            return feature.to_dict()
        except Exception as e:
            if hasattr(e, "status_code"):
                raise
            return {"error": str(e)}

    @app_instance.post("/api/features")
    async def api_feature_create(feature_data: dict):
        """Create a new feature.

        Request Body:
            {
                "description": str (required),
                "category": str (optional, default: "core"),
                "priority": int (optional, default: 2),
                "acceptance_criteria": list[str] (optional),
                "notes": str (optional),
                "dependencies": list[str] (optional)
            }

        Returns:
            Created feature with auto-assigned ID.
        """
        from datetime import datetime

        from .data import load_features, save_features
        from .models import Feature, FeatureStatus

        try:
            # Validate required fields
            if not feature_data.get("description"):
                from fastapi import HTTPException

                raise HTTPException(status_code=400, detail="Description is required")

            registry = load_features(root)

            # Auto-assign next feature ID
            existing_ids = [
                int(f.id[1:])
                for f in registry.features
                if f.id.startswith("F") and f.id[1:].isdigit()
            ]
            next_id = max(existing_ids) + 1 if existing_ids else 1
            feature_id = f"F{next_id:03d}"

            # Validate priority range (1-5)
            priority = feature_data.get("priority", 2)
            if not isinstance(priority, int) or priority < 1 or priority > 5:
                from fastapi import HTTPException

                raise HTTPException(
                    status_code=400,
                    detail="Priority must be an integer between 1 and 5",
                )

            # Create new feature
            new_feature = Feature(
                id=feature_id,
                description=feature_data["description"],
                category=feature_data.get("category", "core"),
                priority=priority,
                acceptance_criteria=feature_data.get("acceptance_criteria", []),
                notes=feature_data.get("notes"),
                dependencies=feature_data.get("dependencies", []),
                status=FeatureStatus.NOT_STARTED,
                passes=False,
            )

            # Add to registry and save
            registry.features.append(new_feature)
            registry._invalidate_index()

            # Update metadata
            registry.metadata.total_features = len(registry.features)
            registry.metadata.last_updated = datetime.now().isoformat()

            save_features(registry, root)

            # Broadcast event to WebSocket clients
            await manager.broadcast(
                "featureAdded",
                {
                    "id": feature_id,
                    "description": new_feature.description,
                    "category": new_feature.category,
                    "status": new_feature.status.value,
                },
            )

            return {
                "success": True,
                "feature": new_feature.to_dict(),
                "message": f"Created feature {feature_id}",
            }
        except Exception as e:
            if hasattr(e, "status_code"):
                raise
            return {"error": str(e)}

    @app_instance.put("/api/features/{feature_id}")
    async def api_feature_update(feature_id: str, update_data: dict):
        """Update an existing feature.

        Path Parameters:
            feature_id: Feature ID (e.g., F001)

        Request Body:
            Any Feature properties to update (description, category, priority, etc.)

        Returns:
            Updated feature or 404 error.
        """
        from datetime import datetime

        from .data import load_features, save_features
        from .models import FeatureStatus

        try:
            registry = load_features(root)
            registry._build_index()

            if feature_id not in registry._feature_index:
                from fastapi import HTTPException

                raise HTTPException(status_code=404, detail=f"Feature not found: {feature_id}")

            feature = registry._feature_index[feature_id]

            # Update allowed fields
            if "description" in update_data and update_data["description"]:
                feature.description = update_data["description"]
            elif "description" in update_data and not update_data["description"]:
                from fastapi import HTTPException

                raise HTTPException(status_code=400, detail="Description cannot be empty")

            if "category" in update_data:
                feature.category = update_data["category"]

            if "priority" in update_data:
                priority = update_data["priority"]
                if not isinstance(priority, int) or priority < 1 or priority > 5:
                    from fastapi import HTTPException

                    raise HTTPException(
                        status_code=400,
                        detail="Priority must be an integer between 1 and 5",
                    )
                feature.priority = priority

            if "acceptance_criteria" in update_data:
                feature.acceptance_criteria = update_data["acceptance_criteria"]

            if "notes" in update_data:
                feature.notes = update_data["notes"]

            if "dependencies" in update_data:
                feature.dependencies = update_data["dependencies"]

            if "status" in update_data:
                try:
                    feature.status = FeatureStatus(update_data["status"])
                except ValueError:
                    from fastapi import HTTPException

                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid status: {update_data['status']}",
                    ) from None

            if "blocked_by" in update_data:
                feature.blocked_by = update_data["blocked_by"]

            if "estimated_effort" in update_data:
                feature.estimated_effort = update_data["estimated_effort"]

            # Update metadata
            feature.last_worked_on = datetime.now().isoformat()
            registry.metadata.last_updated = datetime.now().isoformat()

            save_features(registry, root)

            # Broadcast event to WebSocket clients
            await manager.broadcast(
                "featureUpdated",
                {
                    "id": feature_id,
                    "description": feature.description,
                    "category": feature.category,
                    "status": feature.status.value,
                },
            )

            return {
                "success": True,
                "feature": feature.to_dict(),
                "message": f"Updated feature {feature_id}",
            }
        except Exception as e:
            if hasattr(e, "status_code"):
                raise
            return {"error": str(e)}

    @app_instance.post("/api/features/{feature_id}/start")
    async def api_feature_start(feature_id: str):
        """Mark feature as in-progress.

        Path Parameters:
            feature_id: Feature ID (e.g., F001)

        Returns:
            Updated feature or 404 error.
            Includes warning if other features are in-progress.
        """
        from datetime import datetime

        from .data import load_features, load_progress, save_features, save_progress
        from .models import FeatureStatus

        try:
            registry = load_features(root)
            registry._build_index()

            if feature_id not in registry._feature_index:
                from fastapi import HTTPException

                raise HTTPException(status_code=404, detail=f"Feature not found: {feature_id}")

            feature = registry._feature_index[feature_id]

            # Check for other in-progress features
            in_progress = [f for f in registry.features if f.status == FeatureStatus.IN_PROGRESS]
            warning = None
            if in_progress and feature_id not in [f.id for f in in_progress]:
                warning = f"Other features are in-progress: {', '.join(f.id for f in in_progress)}"

            # Update feature status
            feature.status = FeatureStatus.IN_PROGRESS
            feature.last_worked_on = datetime.now().isoformat()
            registry.metadata.last_updated = datetime.now().isoformat()

            save_features(registry, root)

            # Broadcast event to WebSocket clients
            await manager.broadcast(
                "featureUpdated",
                {
                    "id": feature_id,
                    "status": "in-progress",
                    "action": "started",
                },
            )

            # Update progress
            try:
                from .commands.features import (
                    regenerate_progress_md,
                    update_quick_reference,
                )

                progress = load_progress(root)
                update_quick_reference(progress, registry)
                save_progress(progress, root)
                regenerate_progress_md(root)
            except Exception:
                pass  # Progress update is optional

            result = {
                "success": True,
                "feature": feature.to_dict(),
                "message": f"Started feature {feature_id}",
            }
            if warning:
                result["warning"] = warning

            return result
        except Exception as e:
            if hasattr(e, "status_code"):
                raise
            return {"error": str(e)}

    @app_instance.post("/api/features/{feature_id}/verify")
    async def api_feature_verify(feature_id: str, verify_data: dict):
        """Mark feature as verified with evidence.

        Path Parameters:
            feature_id: Feature ID (e.g., F001)

        Request Body:
            {
                "evidence": str (required) - Evidence links/description (comma-separated)
            }

        Returns:
            Updated feature or 404/400 error.
        """
        from datetime import datetime

        from .data import (
            load_config,
            load_features,
            load_progress,
            save_features,
            save_progress,
        )
        from .models import FeatureStatus
        from .validation import sanitize_string

        try:
            # Validate evidence
            evidence = verify_data.get("evidence", "")
            if not evidence:
                from fastapi import HTTPException

                raise HTTPException(status_code=400, detail="Evidence is required for verification")

            # Sanitize evidence
            evidence = sanitize_string(evidence)
            if not evidence:
                from fastapi import HTTPException

                raise HTTPException(status_code=400, detail="Evidence cannot be empty")

            registry = load_features(root)
            registry._build_index()

            if feature_id not in registry._feature_index:
                from fastapi import HTTPException

                raise HTTPException(status_code=404, detail=f"Feature not found: {feature_id}")

            feature = registry._feature_index[feature_id]
            config = load_config(root)

            # Parse evidence paths
            evidence_paths = [
                sanitize_string(p.strip()) or "" for p in evidence.split(",") if p.strip()
            ]

            # Update feature status
            feature.status = FeatureStatus.VERIFIED
            feature.passes = True
            feature.verified_at = datetime.now().isoformat()
            feature.verified_by = config.verified_by
            feature.evidence_links = evidence_paths

            # Update metadata
            registry.update_metadata()
            registry.metadata.last_updated = datetime.now().isoformat()

            save_features(registry, root)

            # Broadcast event to WebSocket clients
            await manager.broadcast(
                "featureUpdated",
                {
                    "id": feature_id,
                    "status": "verified",
                    "action": "verified",
                    "passes": True,
                },
            )

            # Update progress
            try:
                from .commands.features import (
                    regenerate_progress_md,
                    update_quick_reference,
                )

                progress = load_progress(root)
                update_quick_reference(progress, registry)
                save_progress(progress, root)
                regenerate_progress_md(root)
            except Exception:
                pass  # Progress update is optional

            return {
                "success": True,
                "feature": feature.to_dict(),
                "message": f"Verified feature {feature_id}",
                "evidence": evidence_paths,
            }
        except Exception as e:
            if hasattr(e, "status_code"):
                raise
            return {"error": str(e)}

    @app_instance.post("/api/features/{feature_id}/block")
    async def api_feature_block(feature_id: str, block_data: dict):
        """Mark feature as blocked with reason.

        Path Parameters:
            feature_id: Feature ID (e.g., F001)

        Request Body:
            {
                "reason": str (required) - Reason for blocking
            }

        Returns:
            Updated feature or 404/400 error.
        """
        from datetime import datetime

        from .data import load_features, load_progress, save_features, save_progress
        from .models import FeatureStatus
        from .validation import sanitize_string

        try:
            # Validate reason
            reason = block_data.get("reason", "")
            if not reason:
                from fastapi import HTTPException

                raise HTTPException(status_code=400, detail="Reason is required for blocking")

            # Sanitize reason
            reason = sanitize_string(reason)
            if not reason:
                from fastapi import HTTPException

                raise HTTPException(status_code=400, detail="Reason cannot be empty")

            registry = load_features(root)
            registry._build_index()

            if feature_id not in registry._feature_index:
                from fastapi import HTTPException

                raise HTTPException(status_code=404, detail=f"Feature not found: {feature_id}")

            feature = registry._feature_index[feature_id]

            # Update feature status
            feature.status = FeatureStatus.BLOCKED
            feature.blocked_by = reason
            feature.last_worked_on = datetime.now().isoformat()
            registry.metadata.last_updated = datetime.now().isoformat()

            save_features(registry, root)

            # Broadcast event to WebSocket clients
            await manager.broadcast(
                "featureUpdated",
                {
                    "id": feature_id,
                    "status": "blocked",
                    "action": "blocked",
                    "reason": reason,
                },
            )

            # Update progress
            try:
                from .commands.features import (
                    regenerate_progress_md,
                    update_quick_reference,
                )

                progress = load_progress(root)
                update_quick_reference(progress, registry)
                save_progress(progress, root)
                regenerate_progress_md(root)
            except Exception:
                pass  # Progress update is optional

            return {
                "success": True,
                "feature": feature.to_dict(),
                "message": f"Blocked feature {feature_id}",
                "reason": reason,
            }
        except Exception as e:
            if hasattr(e, "status_code"):
                raise
            return {"error": str(e)}

    @app_instance.get("/api/progress")
    async def api_progress():
        """Get all session history.

        Returns:
            ProgressLog with all session history.
        """
        from .data import load_progress

        try:
            progress = load_progress(root)
            return {
                "sessions": [s.to_dict() for s in progress.sessions],
                "current_status": progress.current_status,
                "total_sessions": len(progress.sessions),
            }
        except Exception as e:
            return {"error": str(e)}

    @app_instance.get("/api/commits")
    async def api_commits(count: int = 10):
        """Get recent git commits.

        Args:
            count: Number of commits to return (default 10)

        Returns:
            List of commit objects with hash, author, date, and message.
            Returns empty list if not a git repo.
        """
        from .git import get_recent_commits

        try:
            commits = get_recent_commits(count=count, path=root)
            return [
                {
                    "hash": commit.hash,
                    "author": commit.author,
                    "date": commit.date,
                    "message": commit.message,
                }
                for commit in commits
            ]
        except Exception:
            # Return empty list if not a git repo or any other error
            return []

    @app_instance.get("/api/config")
    async def api_config_get():
        """Get current configuration.

        Returns:
            Configuration settings including:
            - default_category: Default category for new features
            - default_priority: Default priority for new features (1-5)
            - verified_by: Identifier for verification field
            - progress_output_path: Path for generated progress file
            - auto_regenerate_progress: Whether to auto-regenerate progress
            - prd_source: Link to PRD document (optional)
            - klondike_version: Version of klondike that created config
            - configured_agents: List of configured AI agents
        """
        from .data import load_config

        try:
            config = load_config(root)
            return config.to_dict()
        except Exception as e:
            return {"error": str(e)}

    @app_instance.put("/api/config")
    async def api_config_update(config_data: dict):
        """Update configuration.

        Request Body:
            Partial or complete config object with fields to update:
            - default_category: str (any category name)
            - default_priority: int (1-5, 1=critical)
            - verified_by: str
            - progress_output_path: str
            - auto_regenerate_progress: bool
            - prd_source: str (optional)
            - configured_agents: list[str]

        Returns:
            Updated configuration or validation error.
        """
        from .data import get_klondike_dir, load_config

        try:
            # Load current config
            config = load_config(root)

            # Validate and apply updates
            if "default_priority" in config_data:
                priority = config_data["default_priority"]
                if not isinstance(priority, int) or not (1 <= priority <= 5):
                    from fastapi import HTTPException

                    raise HTTPException(
                        status_code=400,
                        detail="default_priority must be an integer between 1 and 5",
                    )
                config.default_priority = priority

            if "default_category" in config_data:
                category = config_data["default_category"]
                if not isinstance(category, str) or not category.strip():
                    from fastapi import HTTPException

                    raise HTTPException(
                        status_code=400,
                        detail="default_category must be a non-empty string",
                    )
                config.default_category = category.strip()

            if "verified_by" in config_data:
                verified_by = config_data["verified_by"]
                if not isinstance(verified_by, str) or not verified_by.strip():
                    from fastapi import HTTPException

                    raise HTTPException(
                        status_code=400, detail="verified_by must be a non-empty string"
                    )
                config.verified_by = verified_by.strip()

            if "progress_output_path" in config_data:
                output_path = config_data["progress_output_path"]
                if not isinstance(output_path, str) or not output_path.strip():
                    from fastapi import HTTPException

                    raise HTTPException(
                        status_code=400,
                        detail="progress_output_path must be a non-empty string",
                    )
                config.progress_output_path = output_path.strip()

            if "auto_regenerate_progress" in config_data:
                auto_regen = config_data["auto_regenerate_progress"]
                if not isinstance(auto_regen, bool):
                    from fastapi import HTTPException

                    raise HTTPException(
                        status_code=400,
                        detail="auto_regenerate_progress must be a boolean",
                    )
                config.auto_regenerate_progress = auto_regen

            if "prd_source" in config_data:
                prd_source = config_data["prd_source"]
                if prd_source is not None and not isinstance(prd_source, str):
                    from fastapi import HTTPException

                    raise HTTPException(
                        status_code=400, detail="prd_source must be a string or null"
                    )
                config.prd_source = prd_source.strip() if prd_source else None

            if "configured_agents" in config_data:
                agents = config_data["configured_agents"]
                if not isinstance(agents, list) or not all(isinstance(a, str) for a in agents):
                    from fastapi import HTTPException

                    raise HTTPException(
                        status_code=400,
                        detail="configured_agents must be a list of strings",
                    )
                config.configured_agents = [a.strip() for a in agents if a.strip()]

            # Save updated config
            klondike_dir = get_klondike_dir(root)
            config_path = klondike_dir / "config.yaml"
            config.save(config_path)

            # Broadcast event to WebSocket clients
            await manager.broadcast(
                "configChanged",
                {
                    "updated": list(config_data.keys()),
                },
            )

            return {
                "success": True,
                "config": config.to_dict(),
                "message": "Configuration updated successfully",
            }

        except Exception as e:
            if hasattr(e, "status_code"):
                raise
            return {"error": str(e)}

    @app_instance.post("/api/session/start")
    async def api_session_start(session_data: dict):
        """Start a new session.

        Request Body:
            {
                "focus": str (required) - Session focus/description
            }

        Returns:
            Created session or validation error.
        """
        from datetime import datetime

        from .data import (
            load_features,
            load_progress,
            regenerate_progress_md,
            save_features,
            save_progress,
        )
        from .git import get_git_status
        from .models import Session

        try:
            # Validate focus
            focus = session_data.get("focus", "")
            if not focus:
                from fastapi import HTTPException

                raise HTTPException(status_code=400, detail="Focus is required")

            registry = load_features(root)
            progress = load_progress(root)

            # Check if there's already an active session
            current = progress.get_current_session()
            if current and progress.current_status == "In Progress":
                from fastapi import HTTPException

                raise HTTPException(
                    status_code=400,
                    detail=f"Session {current.session_number} is already active. End it first.",
                )

            # Validate artifact integrity
            actual_total = len(registry.features)
            actual_passing = sum(1 for f in registry.features if f.passes)

            warnings = []
            if registry.metadata.total_features != actual_total:
                warnings.append(
                    f"metadata.totalFeatures ({registry.metadata.total_features}) != actual ({actual_total})"
                )
                registry.metadata.total_features = actual_total

            if registry.metadata.passing_features != actual_passing:
                warnings.append(
                    f"metadata.passingFeatures ({registry.metadata.passing_features}) != actual ({actual_passing})"
                )
                registry.metadata.passing_features = actual_passing

            # Get git status
            git_status = get_git_status(root)
            git_info = None
            if git_status.is_git_repo:
                git_info = {
                    "branch": git_status.current_branch,
                    "has_uncommitted": git_status.has_uncommitted_changes,
                }

            # Create new session
            session_num = progress.next_session_number()
            new_session = Session(
                session_number=session_num,
                date=datetime.now().strftime("%Y-%m-%d"),
                agent="Coding Agent",
                duration="(in progress)",
                focus=focus,
                completed=[],
                in_progress=["Session started"],
                blockers=[],
                next_steps=[],
                technical_notes=[],
            )

            progress.add_session(new_session)
            progress.current_status = "In Progress"

            # Save changes
            from .commands.features import update_quick_reference

            update_quick_reference(progress, registry)
            save_features(registry, root)
            save_progress(progress, root)
            regenerate_progress_md(root)

            # Broadcast event to WebSocket clients
            await manager.broadcast(
                "sessionStarted",
                {
                    "sessionNumber": new_session.session_number,
                    "focus": new_session.focus,
                },
            )

            # Build response
            result = {
                "success": True,
                "session": new_session.to_dict(),
                "project_status": {
                    "total": registry.metadata.total_features,
                    "passing": registry.metadata.passing_features,
                    "percent": (
                        round(
                            registry.metadata.passing_features
                            / registry.metadata.total_features
                            * 100,
                            1,
                        )
                        if registry.metadata.total_features > 0
                        else 0
                    ),
                },
                "message": f"Session {session_num} started",
            }

            if warnings:
                result["warnings"] = warnings
            if git_info:
                result["git"] = git_info

            return result
        except Exception as e:
            if hasattr(e, "status_code"):
                raise
            return {"error": str(e)}

    @app_instance.post("/api/session/end")
    async def api_session_end(end_data: dict):
        """End the current session.

        Request Body:
            {
                "summary": str (optional) - Session summary
                "completed": list[str] (optional) - Completed items
                "blockers": list[str] (optional) - Blockers encountered
                "nextSteps": list[str] (optional) - Next steps (auto-generated if not provided)
            }

        Returns:
            Updated session or error if no active session.
        """
        from .data import (
            load_features,
            load_progress,
            regenerate_progress_md,
            save_progress,
        )

        try:
            registry = load_features(root)
            progress = load_progress(root)

            current = progress.get_current_session()
            if not current or progress.current_status != "In Progress":
                from fastapi import HTTPException

                raise HTTPException(
                    status_code=400,
                    detail="No active session found. Start a session first.",
                )

            # Update session
            current.duration = "~session"  # TODO: Calculate actual duration
            current.in_progress = []

            if "summary" in end_data and end_data["summary"]:
                current.focus = end_data["summary"]

            if "completed" in end_data:
                current.completed = end_data["completed"]

            if "blockers" in end_data:
                current.blockers = end_data["blockers"]

            if "nextSteps" in end_data:
                current.next_steps = end_data["nextSteps"]
            else:
                # Auto-generate next steps from priority features
                priority = registry.get_priority_features(3)
                current.next_steps = [f"Continue {f.id}: {f.description}" for f in priority]

            progress.current_status = "Session Ended"

            # Save changes
            from .commands.features import update_quick_reference

            update_quick_reference(progress, registry)
            save_progress(progress, root)
            regenerate_progress_md(root)

            # Broadcast event to WebSocket clients
            await manager.broadcast(
                "sessionEnded",
                {
                    "sessionNumber": current.session_number,
                    "focus": current.focus,
                },
            )

            return {
                "success": True,
                "session": current.to_dict(),
                "message": f"Session {current.session_number} ended",
            }
        except Exception as e:
            if hasattr(e, "status_code"):
                raise
            return {"error": str(e)}

    @app_instance.get("/{full_path:path}", response_class=HTMLResponse)
    async def serve_spa(full_path: str):
        """Serve index.html for all routes (React Router support)."""
        # Serve static files directly if they exist
        static_file = static_dir / full_path
        if static_file.is_file():
            return FileResponse(static_file)

        # Otherwise serve index.html for client-side routing
        index_path = static_dir / "index.html"
        if not index_path.exists():
            return HTMLResponse(
                content="<h1>Klondike Spec CLI</h1><p>Static files not found</p>",
                status_code=500,
            )
        return FileResponse(index_path)

    # Print startup message
    echo("")
    echo("🚀 Starting Klondike Spec Web UI")
    echo("=" * 50)
    echo(f"   Project: {root.name}")
    echo(f"   URL:     http://{host}:{port}")
    echo(f"   Version: {__version__}")
    echo("")
    echo("Press Ctrl+C to stop the server")
    echo("")

    # Open browser after a short delay to ensure server is ready
    if open_browser:
        import threading
        import webbrowser

        def open_browser_delayed():
            import time

            time.sleep(1.5)  # Wait for server to be ready
            url = f"http://{host}:{port}"
            webbrowser.open(url)

        browser_thread = threading.Thread(target=open_browser_delayed, daemon=True)
        browser_thread.start()

    # Start server
    try:
        uvicorn.run(app_instance, host=host, port=port, log_level="info")
    except OSError as err:
        if "address already in use" in str(err).lower():
            raise PithException(
                f"Port {port} is already in use.\n"
                f"Try a different port: klondike serve --port {port + 1}"
            ) from err
        raise
    except KeyboardInterrupt:
        echo("\n👋 Server stopped")
    finally:
        # Cleanup file watcher
        observer.stop()
        observer.join()


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
    pyproject_path = Path.cwd() / "pyproject.toml"

    if not pyproject_path.exists():
        raise PithException("pyproject.toml not found in current directory")

    # Read current version
    content = pyproject_path.read_text()
    match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
    if not match:
        raise PithException("Could not find version in pyproject.toml")

    current_version = match.group(1)

    # If no version or bump specified, show current version
    if not version and not bump:
        echo(f"📦 Current version: {current_version}")
        tags = get_tags()
        if tags:
            echo(f"📌 Latest tag: {tags[0]}")
        echo("")
        echo("Usage:")
        echo("  klondike release 0.3.0        # Release specific version")
        echo("  klondike release --bump patch # Bump patch (0.2.0 -> 0.2.1)")
        echo("  klondike release --bump minor # Bump minor (0.2.0 -> 0.3.0)")
        echo("  klondike release --bump major # Bump major (0.2.0 -> 1.0.0)")
        return

    # Calculate new version
    if bump:
        new_version = _bump_version(current_version, bump)
    elif version:
        new_version = version.lstrip("v")
    else:
        raise PithException("Either version or --bump must be specified")

    # Validate version format
    if not re.match(r"^\d+\.\d+\.\d+$", new_version):
        raise PithException(f"Invalid version format: {new_version}. Expected X.Y.Z (e.g., 0.3.0)")

    tag_name = f"v{new_version}"
    release_msg = message or f"Release {tag_name}"

    echo("📋 Release Plan")
    echo("=" * 40)
    echo(f"  Current version: {current_version}")
    echo(f"  New version:     {new_version}")
    echo(f"  Tag:             {tag_name}")
    echo(f"  Message:         {release_msg}")
    echo("")

    if dry_run:
        echo("⚠️  DRY RUN - No changes will be made")
        echo("")
        echo("Steps that would be performed:")
        echo("  1. Update version in pyproject.toml")
        if not skip_tests:
            echo("  2. Run tests")
        echo(f"  {'3' if not skip_tests else '2'}. Commit version bump")
        if push:
            echo(f"  {'4' if not skip_tests else '3'}. Push commit to remote")
        echo(f"  {'5' if not skip_tests else '4'}. Create tag {tag_name}")
        if push:
            echo(f"  {'6' if not skip_tests else '5'}. Push tag to remote")
        echo("")
        echo("After completion:")
        echo("  - TestPyPI: Automatic (triggered by tag push)")
        echo("  - PyPI: Create GitHub Release from tag")
        return

    # Check for uncommitted changes
    status = get_git_status()
    if status.has_uncommitted_changes:
        raise PithException(
            "Working directory has uncommitted changes. Please commit or stash them first."
        )

    # Run tests unless skipped
    if not skip_tests:
        echo("🧪 Running tests...")
        try:
            result = subprocess.run(
                ["uv", "run", "pytest", "-q"],
                capture_output=True,
                text=True,
                timeout=300,
            )
            if result.returncode != 0:
                echo("❌ Tests failed:")
                echo(result.stdout)
                echo(result.stderr)
                raise PithException("Tests must pass before release")
            echo("✅ Tests passed")
        except FileNotFoundError:
            # Try with pytest directly
            result = subprocess.run(
                ["pytest", "-q"],
                capture_output=True,
                text=True,
                timeout=300,
            )
            if result.returncode != 0:
                raise PithException("Tests must pass before release") from None
            echo("✅ Tests passed")
        except subprocess.TimeoutExpired as err:
            raise PithException("Tests timed out") from err

    # Update version in pyproject.toml
    echo(f"📝 Updating version to {new_version}...")
    new_content = re.sub(
        r'^(version\s*=\s*")[^"]+(")',
        f"\\g<1>{new_version}\\g<2>",
        content,
        flags=re.MULTILINE,
    )
    pyproject_path.write_text(new_content)

    # Stage and commit
    echo("📦 Committing version bump...")
    git_add_all()
    commit_success, output = git_commit(f"chore: bump version to {new_version}")
    if not commit_success:
        # Restore original content on failure
        pyproject_path.write_text(content)
        raise PithException(f"Failed to commit: {output}")
    echo(f"✅ Committed: chore: bump version to {new_version}")

    # Push commit if requested
    if push:
        echo("⬆️  Pushing commit...")
        push_success, output = git_push()
        if not push_success:
            raise PithException(f"Failed to push: {output}")
        echo("✅ Pushed commit")

    # Create tag
    echo(f"🏷️  Creating tag {tag_name}...")
    tag_success, output = git_tag(tag_name, release_msg)
    if not tag_success:
        raise PithException(f"Failed to create tag: {output}")
    echo(f"✅ Created tag {tag_name}")

    # Push tag if requested
    if push:
        echo(f"⬆️  Pushing tag {tag_name}...")
        push_tag_success, output = git_push_tag(tag_name)
        if not push_tag_success:
            raise PithException(f"Failed to push tag: {output}")
        echo("✅ Pushed tag")

    echo("")
    echo(f"🎉 Released {tag_name}!")
    echo("")
    echo("Next steps:")
    echo("  📦 TestPyPI: Publishing automatically (triggered by tag)")
    echo("  📦 PyPI: Create a GitHub Release from the tag:")
    echo(f"     https://github.com/ThomasRohde/klondike-spec-cli/releases/new?tag={tag_name}")


def _bump_version(version: str, bump_type: str) -> str:
    """Bump a semantic version.

    Args:
        version: Current version (e.g., "0.2.0")
        bump_type: Type of bump: "major", "minor", or "patch"

    Returns:
        New version string
    """
    parts = version.split(".")
    if len(parts) != 3:
        raise PithException(f"Invalid version format: {version}")

    try:
        major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
    except ValueError as err:
        raise PithException(f"Invalid version format: {version}") from err

    if bump_type == "major":
        return f"{major + 1}.0.0"
    elif bump_type == "minor":
        return f"{major}.{minor + 1}.0"
    elif bump_type == "patch":
        return f"{major}.{minor}.{patch + 1}"
    else:
        raise PithException(f"Invalid bump type: {bump_type}. Use major, minor, or patch")


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
