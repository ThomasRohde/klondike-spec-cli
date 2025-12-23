"""Administrative commands: validate, config, completion, progress, version."""

import re
import sys
from pathlib import Path

from pith import PithException, echo

from ..data import (
    CONFIG_FILE,
    get_klondike_dir,
    load_config,
    load_features,
    load_progress,
)
from ..models import FeatureStatus

try:
    from .._version import __version__
except ImportError:
    __version__ = "0.0.0+unknown"


def validate_command() -> None:
    """Validate Klondike artifact integrity.

    Checks features.json and agent-progress.json for consistency,
    validates metadata counts, and reports any issues.
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


def config_command(
    key: str | None = None,
    value: str | None = None,
) -> None:
    """View or set project configuration.

    Without arguments, displays all configuration values.
    With a key, displays that specific value.
    With value, updates the configuration.
    """
    root = Path.cwd()
    klondike_dir = get_klondike_dir(root)
    if not klondike_dir:
        raise PithException("Not in a Klondike project. Run 'klondike init' first.")

    config_path = klondike_dir / CONFIG_FILE

    if not key:
        # Display all config
        if not config_path.exists():
            echo("⚙️  No configuration file found. Using defaults.")
            echo("")
            echo("Available settings:")
            echo("  • default_category: core")
            echo("  • default_priority: 2")
            echo("  • verified_by: coding-agent")
            echo("  • progress_output_path: agent-progress.md")
            echo("  • auto_regenerate_progress: true")
            echo("  • prd_source: (not set)")
            return

        cfg = load_config(root)
        echo("⚙️  Project Configuration")
        echo("=" * 40)
        echo(f"  default_category: {cfg.default_category}")
        echo(f"  default_priority: {cfg.default_priority}")
        echo(f"  verified_by: {cfg.verified_by}")
        echo(f"  progress_output_path: {cfg.progress_output_path}")
        echo(f"  auto_regenerate_progress: {cfg.auto_regenerate_progress}")
        if cfg.prd_source:
            echo(f"  prd_source: {cfg.prd_source}")
        else:
            echo("  prd_source: (not set)")
        return

    # Display specific key
    if value is None:
        cfg = load_config(root)
        val = getattr(cfg, key, None)
        if val is None:
            echo(f"⚠️  Config key '{key}' not found or is None")
        else:
            echo(f"{key}: {val}")
        return

    # Set config value
    cfg = load_config(root)

    # Handle special case for null/None
    if value.lower() in ("null", "none", ""):
        value = None
    elif key in ("default_priority",):
        try:
            value = int(value)
        except ValueError:
            raise PithException(f"Invalid value for {key}: must be an integer") from None
    elif key == "auto_regenerate_progress":
        if value.lower() in ("true", "1", "yes"):
            value = True
        elif value.lower() in ("false", "0", "no"):
            value = False
        else:
            raise PithException(f"Invalid value for {key}: must be true or false")

    if not hasattr(cfg, key):
        raise PithException(f"Unknown config key: {key}")

    setattr(cfg, key, value)

    klondike_dir = get_klondike_dir(root)
    cfg.save(klondike_dir / CONFIG_FILE)

    echo(f"✅ Set {key} = {value}")


def completion_command(shell: str = "bash") -> None:
    """Generate shell completion scripts.

    Outputs completion script for the specified shell.
    Source this in your shell config file.
    """
    if shell not in ("bash", "zsh", "powershell"):
        raise PithException(f"Unsupported shell: {shell}. Use: bash, zsh, powershell")

    echo(f"# Klondike completion for {shell}")
    echo("# Add this to your shell config file")
    echo("")

    if shell == "bash":
        echo("_klondike_completion() {")
        echo('    local cur="${COMP_WORDS[COMP_CWORD]}"')
        echo(
            '    local commands="init upgrade status feature session validate config completion progress report import-features export-features copilot mcp version agents serve release"'
        )
        echo('    COMPREPLY=($(compgen -W "$commands" -- "$cur"))')
        echo("}")
        echo("complete -F _klondike_completion klondike")
    elif shell == "zsh":
        echo("#compdef klondike")
        echo("_klondike() {")
        echo("    local commands=(")
        echo('        "init:Initialize a new Klondike project"')
        echo('        "upgrade:Upgrade templates"')
        echo('        "status:Show project status"')
        echo('        "feature:Manage features"')
        echo('        "session:Manage sessions"')
        echo('        "validate:Validate artifacts"')
        echo('        "config:View or set configuration"')
        echo('        "completion:Generate shell completions"')
        echo('        "progress:Regenerate progress file"')
        echo('        "report:Generate progress report"')
        echo('        "import-features:Import features from file"')
        echo('        "export-features:Export features to file"')
        echo('        "copilot:Launch GitHub Copilot"')
        echo('        "mcp:Manage MCP server"')
        echo('        "version:Show version"')
        echo('        "agents:Generate AGENTS.md"')
        echo('        "serve:Start web UI"')
        echo('        "release:Automate release"')
        echo("    )")
        echo('    _describe "command" commands')
        echo("}")
        echo("compdef _klondike klondike")
    elif shell == "powershell":
        echo("Register-ArgumentCompleter -CommandName klondike -ScriptBlock {")
        echo("    param($commandName, $wordToComplete, $commandAst, $fakeBoundParameters)")
        echo("    $commands = @(")
        echo('        "init", "upgrade", "status", "feature", "session",')
        echo('        "validate", "config", "completion", "progress", "report",')
        echo('        "import-features", "export-features", "copilot", "mcp",')
        echo('        "version", "agents", "serve", "release"')
        echo("    )")
        echo('    $commands | Where-Object { $_ -like "$wordToComplete*" } |')
        echo("        ForEach-Object { [System.Management.Automation.CompletionResult]::new($_) }")
        echo("}")


def progress_command(
    output: str | None = None,
    force: bool = False,
) -> None:
    """Regenerate agent-progress.md from JSON.

    Rebuilds the human-readable progress file from agent-progress.json.
    """
    root = Path.cwd()
    klondike_dir = get_klondike_dir(root)
    if not klondike_dir:
        raise PithException("Not in a Klondike project. Run 'klondike init' first.")

    try:
        progress = load_progress()
        registry = load_features()
        cfg = load_config(root)
    except Exception as e:
        raise PithException(f"Failed to load Klondike data: {e}") from e

    # Determine output path
    output_path = Path(output) if output else root / cfg.progress_output_path

    # Check if file exists and force not set
    if output_path.exists() and not force:
        echo(f"⚠️  {output_path.name} already exists.")
        echo("Use --force to overwrite, or specify a different --output path.")
        return

    # Generate markdown content using Progress model's to_markdown() method
    content = progress.to_markdown(prd_source=cfg.prd_source)
    output_path.write_text(content, encoding="utf-8")

    echo(f"✅ Regenerated {output_path.name}")
    echo(f"   Sessions: {len(progress.sessions)}")
    echo(f"   Features: {len(registry.features)}")


def version_command(verbose: bool = False) -> None:
    """Show klondike version information."""
    echo(f"klondike {__version__}")

    if verbose:
        echo("")
        echo(f"Python: {sys.version.split()[0]}")
        echo(f"Platform: {sys.platform}")
