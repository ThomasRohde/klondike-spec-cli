"""Init and upgrade command handlers."""

from datetime import datetime
from pathlib import Path

from pith import Option, PithException, echo

from klondike_spec_cli.agents import get_agent, get_default_agent, list_agents
from klondike_spec_cli.data import (
    CONFIG_FILE,
    FEATURES_FILE,
    PROGRESS_FILE,
    PROGRESS_MD_FILE,
    get_klondike_dir,
    load_progress,
)
from klondike_spec_cli.models import Config, ProgressLog
from klondike_spec_cli.templates import (
    CONFIG_TEMPLATE,
    FEATURES_TEMPLATE,
    PROGRESS_TEMPLATE,
    read_template,
)


def _parse_agent_option(agent: str | None) -> list[str]:
    """Parse the --agent option into a list of agent names.

    Args:
        agent: The agent option value (e.g., 'copilot', 'claude', 'all', or None)

    Returns:
        List of agent names to initialize

    Raises:
        PithException: If the agent name is invalid
    """
    if agent is None:
        # Default to copilot for backward compatibility
        return [get_default_agent()]

    agent_lower = agent.lower().strip()

    if agent_lower == "all":
        return list_agents()

    if agent_lower in list_agents():
        return [agent_lower]

    valid_agents = ", ".join(list_agents())
    raise PithException(f"Unknown agent: '{agent}'\nValid options: {valid_agents}, all")


def upgrade_project(
    root: Path,
    klondike_dir: Path,
    skip_github: bool,
    prd_source: str | None,
    agent: str | None = None,
) -> None:
    """Upgrade an existing Klondike project by refreshing templates.

    Preserves:
        - features.json (all features and status)
        - agent-progress.json (session history)
        - config.yaml user preferences (merges with new fields)

    Upgrades:
        - Agent templates (based on configured_agents or --agent option)
        - Adds klondike_version to config.yaml

    Args:
        root: Project root directory
        klondike_dir: Path to .klondike directory
        skip_github: If True, skip agent template extraction
        prd_source: Optional PRD document link
        agent: Optional agent selection (if None, uses configured_agents from config)
    """
    import shutil

    from klondike_spec_cli import __version__

    echo("🔄 Upgrading Klondike project...")
    echo("")

    # Load existing config to preserve user preferences
    config_path = klondike_dir / CONFIG_FILE
    existing_config = Config.load(config_path) if config_path.exists() else Config()

    # Determine which agents to upgrade
    if agent is not None:
        # User specified agent(s) - add to existing configured agents
        agents_to_upgrade = _parse_agent_option(agent)
        # Merge with existing agents (add new ones)
        all_agents = list(set(existing_config.configured_agents + agents_to_upgrade))
        existing_config.configured_agents = all_agents
    else:
        # No agent specified - upgrade all currently configured agents
        agents_to_upgrade = existing_config.configured_agents or [get_default_agent()]

    # Backup existing agent directories
    if not skip_github:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        for agent_name in agents_to_upgrade:
            adapter = get_agent(agent_name)
            if adapter.output_directory:
                agent_dir = root / adapter.output_directory
                if agent_dir.exists():
                    backup_name = f"{adapter.output_directory}.backup.{timestamp}"
                    backup_dir = root / backup_name
                    echo(f"📦 Backing up existing {adapter.output_directory}/ to {backup_name}/")
                    shutil.copytree(agent_dir, backup_dir)
            # Also backup CLAUDE.md if upgrading Claude
            if agent_name == "claude":
                claude_md = root / "CLAUDE.md"
                if claude_md.exists():
                    backup_name = f"CLAUDE.md.backup.{timestamp}"
                    echo(f"📦 Backing up existing CLAUDE.md to {backup_name}")
                    shutil.copy2(claude_md, root / backup_name)

    # Update config with new version
    existing_config.klondike_version = __version__
    if prd_source:
        existing_config.prd_source = prd_source

    # Save updated config
    existing_config.save(config_path)
    echo(f"✅ Updated {CONFIG_FILE} (version: {__version__})")

    # Refresh agent templates
    agent_files_extracted: dict[str, int] = {}
    if not skip_github:
        # Determine project name from existing config or directory
        project_name = existing_config.__dict__.get("project_name", root.name)

        # Get existing progress for metadata
        progress_path = klondike_dir / PROGRESS_FILE
        if progress_path.exists():
            progress = ProgressLog.load(progress_path)
            project_name = progress.project_name

        # Prepare template variables
        now = datetime.now().isoformat()
        date_str = datetime.now().strftime("%Y-%m-%d")
        template_vars = {
            "{{PROJECT_NAME}}": project_name,
            "{{CREATED_AT}}": now,
            "{{DATE}}": date_str,
        }

        for agent_name in agents_to_upgrade:
            adapter = get_agent(agent_name)
            extracted = adapter.extract_templates(root, overwrite=True, template_vars=template_vars)
            agent_files_extracted[agent_name] = len(extracted)
            echo(f"✅ Refreshed {adapter.display_name} templates ({len(extracted)} files)")

    # Regenerate agent-progress.md
    if (klondike_dir / PROGRESS_FILE).exists():
        progress = ProgressLog.load(klondike_dir / PROGRESS_FILE)
        progress.save_markdown(root / PROGRESS_MD_FILE, prd_source=existing_config.prd_source)
        echo(f"✅ Regenerated {PROGRESS_MD_FILE}")

    echo("")
    echo("✨ Upgrade complete!")
    echo("   Your features and session history have been preserved.")
    agents_str = ", ".join(agents_to_upgrade)
    echo(f"   Agent templates updated to v{__version__}: {agents_str}")


def init_command(
    project_name: str | None = Option(None, "--name", "-n", pith="Project name"),
    force: bool = Option(
        False, "--force", "-f", pith="Wipe and reinitialize everything (requires confirmation)"
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
    from klondike_spec_cli import __version__

    root = Path.cwd()
    klondike_dir = get_klondike_dir(root)

    # Check for conflicting flags
    if force and upgrade:
        raise PithException("Cannot use --force and --upgrade together. Choose one mode.")

    # Handle existing project scenarios
    exists = klondike_dir.exists()

    if exists and force:
        # Force mode: wipe and reinit with confirmation
        echo("⚠️  WARNING: --force will DELETE all existing Klondike data:")
        echo(f"   • {FEATURES_FILE} (all features and status)")
        echo(f"   • {PROGRESS_FILE} (all session history)")
        echo(f"   • {CONFIG_FILE} (user preferences)")
        echo("   • .github/ templates (if not --skip-github)")
        echo("")
        response = input("Type 'yes' to continue: ")
        if response.lower() != "yes":
            echo("❌ Aborted")
            return

    elif exists and upgrade:
        # Upgrade mode: preserve user data, refresh templates
        upgrade_project(root, klondike_dir, skip_github, prd_source, agent)
        return

    elif exists and not force and not upgrade:
        # Existing project, suggest upgrade
        config_path = klondike_dir / CONFIG_FILE
        if config_path.exists():
            config = Config.load(config_path)
            if config.klondike_version and config.klondike_version != __version__:
                echo(f"📦 Existing project detected (v{config.klondike_version})")
                echo(f"   Current CLI version: v{__version__}")
                echo("")
                echo("💡 Tip: Run 'klondike init --upgrade' to update .github/ templates")
                echo("        while preserving your features and progress.")
                echo("")
        raise PithException(
            f"Klondike directory already exists: {klondike_dir}\\n"
            "Use --upgrade to refresh templates or --force to wipe and reinit."
        )

    # New project initialization
    # Determine project name
    if project_name is None:
        project_name = root.name

    # Create directory
    klondike_dir.mkdir(parents=True, exist_ok=True)

    # Prepare template variables
    now = datetime.now().isoformat()
    date = datetime.now().strftime("%Y-%m-%d")
    template_vars = {
        "{{PROJECT_NAME}}": project_name,
        "{{CREATED_AT}}": now,
        "{{DATE}}": date,
    }

    # Load and substitute features.json template
    features_content = read_template(FEATURES_TEMPLATE)
    for var, value in template_vars.items():
        features_content = features_content.replace(var, value)
    (klondike_dir / FEATURES_FILE).write_text(features_content, encoding="utf-8")

    # Load and substitute agent-progress.json template
    progress_content = read_template(PROGRESS_TEMPLATE)
    for var, value in template_vars.items():
        progress_content = progress_content.replace(var, value)
    (klondike_dir / PROGRESS_FILE).write_text(progress_content, encoding="utf-8")

    # Load and substitute config.yaml template
    config_content = read_template(CONFIG_TEMPLATE)
    for var, value in template_vars.items():
        config_content = config_content.replace(var, value)
    (klondike_dir / CONFIG_FILE).write_text(config_content, encoding="utf-8")

    # Determine which agents to initialize
    agents_to_init = _parse_agent_option(agent)

    # Update config with version, PRD source, and configured agents
    config = Config.load(klondike_dir / CONFIG_FILE)
    config.klondike_version = __version__
    if prd_source:
        config.prd_source = prd_source
    config.configured_agents = agents_to_init
    config.save(klondike_dir / CONFIG_FILE)

    # Generate agent-progress.md from the JSON we just created
    progress = load_progress(root)
    progress.save_markdown(root / PROGRESS_MD_FILE, prd_source=prd_source)

    # Extract agent templates unless skipped
    agent_files_extracted: dict[str, int] = {}
    if not skip_github:
        for agent_name in agents_to_init:
            adapter = get_agent(agent_name)
            extracted = adapter.extract_templates(
                root, overwrite=force, template_vars=template_vars
            )
            agent_files_extracted[agent_name] = len(extracted)

    echo(f"✅ Initialized Klondike project: {project_name}")
    echo(f"   📁 Created {klondike_dir}")
    echo(f"   📋 Created {FEATURES_FILE}")
    echo(f"   📝 Created {PROGRESS_FILE}")
    echo(f"   ⚙️  Created {CONFIG_FILE}")
    echo(f"   📄 Generated {PROGRESS_MD_FILE}")
    if prd_source:
        echo(f"   📑 PRD source: {prd_source}")
    for agent_name, file_count in agent_files_extracted.items():
        if file_count > 0:
            adapter = get_agent(agent_name)
            echo(f"   🤖 Configured {adapter.display_name} ({file_count} files)")
    echo("")
    echo("Next steps:")
    echo("  1. Add features: klondike feature add --description 'My feature'")
    echo("  2. List features: klondike feature list")
    echo("  3. Check status: klondike status")


def upgrade_command(
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
    root = Path.cwd()
    klondike_dir = get_klondike_dir(root)

    if not klondike_dir.exists():
        raise PithException(
            f"Klondike directory not found: {klondike_dir}\\n"
            "Run 'klondike init' to initialize a new project first."
        )

    upgrade_project(root, klondike_dir, skip_github, prd_source, agent)
