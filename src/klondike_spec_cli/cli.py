"""Klondike Spec CLI - Main CLI application.

This CLI is built with the Pith library for agent-native progressive discovery.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

from pith import Argument, Option, Pith, PithException, echo

from . import formatting
from .models import (
    Config,
    Feature,
    FeatureCategory,
    FeatureRegistry,
    FeatureStatus,
    PriorityFeatureRef,
    ProgressLog,
    Session,
)
from .templates import (
    CONFIG_TEMPLATE,
    FEATURES_TEMPLATE,
    PROGRESS_TEMPLATE,
    read_template,
)

# --- Constants ---

KLONDIKE_DIR = ".klondike"
FEATURES_FILE = "features.json"
PROGRESS_FILE = "agent-progress.json"
CONFIG_FILE = "config.yaml"
PROGRESS_MD_FILE = "agent-progress.md"


# --- Helper Functions ---


def get_klondike_dir(root: Path | None = None) -> Path:
    """Get the .klondike directory path."""
    if root is None:
        root = Path.cwd()
    return root / KLONDIKE_DIR


def ensure_klondike_dir(root: Path | None = None) -> Path:
    """Ensure .klondike directory exists."""
    klondike_dir = get_klondike_dir(root)
    if not klondike_dir.exists():
        raise PithException(
            f"Klondike directory not found: {klondike_dir}\n"
            "Run 'klondike init' to initialize a new project."
        )
    return klondike_dir


def load_features(root: Path | None = None) -> FeatureRegistry:
    """Load the feature registry."""
    klondike_dir = ensure_klondike_dir(root)
    features_path = klondike_dir / FEATURES_FILE
    if not features_path.exists():
        raise PithException(f"Features file not found: {features_path}")
    return FeatureRegistry.load(features_path)


def save_features(registry: FeatureRegistry, root: Path | None = None) -> None:
    """Save the feature registry."""
    klondike_dir = ensure_klondike_dir(root)
    features_path = klondike_dir / FEATURES_FILE
    registry.save(features_path)


def load_progress(root: Path | None = None) -> ProgressLog:
    """Load the progress log."""
    klondike_dir = ensure_klondike_dir(root)
    progress_path = klondike_dir / PROGRESS_FILE
    if not progress_path.exists():
        raise PithException(f"Progress file not found: {progress_path}")
    return ProgressLog.load(progress_path)


def save_progress(progress: ProgressLog, root: Path | None = None) -> None:
    """Save the progress log."""
    klondike_dir = ensure_klondike_dir(root)
    progress_path = klondike_dir / PROGRESS_FILE
    progress.save(progress_path)


def regenerate_progress_md(root: Path | None = None) -> None:
    """Regenerate agent-progress.md from JSON."""
    if root is None:
        root = Path.cwd()
    config = load_config(root)
    progress = load_progress(root)
    md_path = root / config.progress_output_path
    progress.save_markdown(md_path)


def load_config(root: Path | None = None) -> Config:
    """Load the configuration file.

    Returns default config if file doesn't exist.
    """
    klondike_dir = get_klondike_dir(root)
    config_path = klondike_dir / CONFIG_FILE
    return Config.load(config_path)


def update_quick_reference(progress: ProgressLog, registry: FeatureRegistry) -> None:
    """Update the quick reference section with current priority features."""
    priority_features = registry.get_priority_features(3)
    progress.quick_reference.priority_features = [
        PriorityFeatureRef(
            id=f.id,
            description=f.description,
            status=f.status.value if isinstance(f.status, FeatureStatus) else f.status,
        )
        for f in priority_features
    ]


# --- Pith App Definition ---

app = Pith(
    name="klondike",
    pith="Manage Klondike Spec agent workflow artifacts: features, sessions, and progress",
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
)
def init(
    project_name: str | None = Option(None, "--name", "-n", pith="Project name"),
    force: bool = Option(False, "--force", "-f", pith="Overwrite existing .klondike"),
) -> None:
    """Initialize a new Klondike Spec project.

    Creates the .klondike directory with features.json, agent-progress.json,
    and config.yaml. Also generates agent-progress.md in the project root.

    Examples:
        $ klondike init
        $ klondike init --name my-project
        $ klondike init --force

    Related:
        status - Check project status after init
        feature add - Add features to the registry
    """
    root = Path.cwd()
    klondike_dir = get_klondike_dir(root)

    if klondike_dir.exists() and not force:
        raise PithException(
            f"Klondike directory already exists: {klondike_dir}\nUse --force to reinitialize."
        )

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

    # Generate agent-progress.md from the JSON we just created
    progress = load_progress(root)
    progress.save_markdown(root / PROGRESS_MD_FILE)

    echo(f"✅ Initialized Klondike project: {project_name}")
    echo(f"   📁 Created {klondike_dir}")
    echo(f"   📋 Created {FEATURES_FILE}")
    echo(f"   📝 Created {PROGRESS_FILE}")
    echo(f"   ⚙️  Created {CONFIG_FILE}")
    echo(f"   📄 Generated {PROGRESS_MD_FILE}")
    echo("")
    echo("Next steps:")
    echo("  1. Add features: klondike feature add --description 'My feature'")
    echo("  2. List features: klondike feature list")
    echo("  3. Check status: klondike status")


@app.command(pith="Show project status and feature summary", priority=20)
@app.intents(
    "show status",
    "project status",
    "how many features",
    "progress overview",
    "summary",
    "what's done",
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
        status_data = {
            "projectName": registry.project_name,
            "version": registry.version,
            "totalFeatures": registry.metadata.total_features,
            "passingFeatures": registry.metadata.passing_features,
            "progressPercent": (
                round(
                    registry.metadata.passing_features / registry.metadata.total_features * 100, 1
                )
                if registry.metadata.total_features > 0
                else 0
            ),
            "byStatus": {
                status.value: len(registry.get_features_by_status(status))
                for status in FeatureStatus
            },
            "currentSession": progress.get_current_session().to_dict()
            if progress.sessions
            else None,
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

    # Priority features
    priority = registry.get_priority_features(3)
    if priority:
        console.print("[bold]🎯 Next Priority Features:[/bold]")
        for f in priority:
            status_text = formatting.colored_status(f.status)
            console.print("   ", status_text, f" [cyan]{f.id}[/cyan]: {f.description}")


@app.command(name="feature", pith="Manage features: add, list, start, verify, block", priority=30)
@app.intents(
    "manage features",
    "feature operations",
    "add feature",
    "list features",
    "verify feature",
    "edit feature",
)
def feature(
    action: str = Argument(..., pith="Action: add, list, start, verify, block, show, edit"),
    feature_id: str | None = Argument(None, pith="Feature ID (e.g., F001)"),
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
) -> None:
    """Manage features in the registry.

    Actions:
        add    - Add a new feature (requires --description)
        list   - List all features (optional --status filter)
        start  - Mark feature as in-progress (requires feature_id)
        verify - Mark feature as verified (requires feature_id and --evidence)
        block  - Mark feature as blocked (requires feature_id and --reason)
        show   - Show feature details (requires feature_id)
        edit   - Edit feature (requires feature_id, use --notes or --add-criteria)

    Examples:
        $ klondike feature add --description "User login" --category core
        $ klondike feature list --status not-started
        $ klondike feature start F001
        $ klondike feature verify F001 --evidence test-results/F001.png
        $ klondike feature block F002 --reason "Waiting for API"
        $ klondike feature show F001
        $ klondike feature edit F001 --notes "Implementation notes"
        $ klondike feature edit F001 --add-criteria "Must handle edge cases"

    Related:
        status - Project overview
        session start - Begin working on features
    """
    if action == "add":
        _feature_add(description, category, priority, criteria, notes)
    elif action == "list":
        _feature_list(status_filter, json_output)
    elif action == "start":
        _feature_start(feature_id)
    elif action == "verify":
        _feature_verify(feature_id, evidence)
    elif action == "block":
        _feature_block(feature_id, reason)
    elif action == "show":
        _feature_show(feature_id, json_output)
    elif action == "edit":
        _feature_edit(feature_id, description, category, priority, notes, add_criteria)
    else:
        raise PithException(
            f"Unknown action: {action}. Use: add, list, start, verify, block, show, edit"
        )


def _feature_add(
    description: str | None,
    category: str | None,
    priority: int | None,
    criteria: str | None,
    notes: str | None,
) -> None:
    """Add a new feature."""
    if not description:
        raise PithException("--description is required for 'add' action")

    registry = load_features()
    progress = load_progress()
    config = load_config()

    feature_id = registry.next_feature_id()
    # Use config defaults if not specified
    cat = FeatureCategory(category) if category else config.default_category
    prio = priority if priority else config.default_priority
    acceptance = (
        [c.strip() for c in criteria.split(",")] if criteria else ["Feature works as described"]
    )

    feature = Feature(
        id=feature_id,
        description=description,
        category=cat,
        priority=prio,
        acceptance_criteria=acceptance,
        notes=notes,
    )

    registry.add_feature(feature)
    save_features(registry)

    # Update quick reference and regenerate markdown
    update_quick_reference(progress, registry)
    save_progress(progress)
    regenerate_progress_md()

    echo(f"✅ Added feature {feature_id}: {description}")
    echo(f"   Category: {cat.value}, Priority: {prio}")


def _feature_list(status_filter: str | None, json_output: bool) -> None:
    """List features."""
    registry = load_features()

    features = registry.features
    if status_filter:
        try:
            filter_status = FeatureStatus(status_filter)
            features = registry.get_features_by_status(filter_status)
        except ValueError as e:
            raise PithException(
                f"Invalid status: {status_filter}. Use: not-started, in-progress, blocked, verified"
            ) from e

    if json_output:
        echo(json.dumps([f.to_dict() for f in features], indent=2))
        return

    if not features:
        echo("No features found.")
        return

    # Use rich table for formatted output
    title = f"Features ({len(features)} total)"
    if status_filter:
        title += f" - {status_filter}"
    formatting.print_feature_table(list(features), title=title)


def _feature_start(feature_id: str | None) -> None:
    """Mark feature as in-progress."""
    if not feature_id:
        raise PithException("Feature ID is required for 'start' action")

    registry = load_features()
    progress = load_progress()

    feature = registry.get_feature(feature_id)
    if not feature:
        raise PithException(f"Feature not found: {feature_id}")

    # Check for other in-progress features
    in_progress = registry.get_features_by_status(FeatureStatus.IN_PROGRESS)
    if in_progress and feature_id not in [f.id for f in in_progress]:
        echo(f"⚠️  Warning: Other features are in-progress: {', '.join(f.id for f in in_progress)}")

    feature.status = FeatureStatus.IN_PROGRESS
    feature.last_worked_on = datetime.now().isoformat()

    save_features(registry)
    update_quick_reference(progress, registry)
    save_progress(progress)
    regenerate_progress_md()

    echo(f"🔄 Started: {feature_id} - {feature.description}")


def _feature_verify(feature_id: str | None, evidence: str | None) -> None:
    """Mark feature as verified."""
    if not feature_id:
        raise PithException("Feature ID is required for 'verify' action")
    if not evidence:
        raise PithException("--evidence is required for 'verify' action")

    registry = load_features()
    progress = load_progress()
    config = load_config()

    feature = registry.get_feature(feature_id)
    if not feature:
        raise PithException(f"Feature not found: {feature_id}")

    evidence_paths = [p.strip() for p in evidence.split(",")]

    feature.status = FeatureStatus.VERIFIED
    feature.passes = True
    feature.verified_at = datetime.now().isoformat()
    feature.verified_by = config.verified_by
    feature.evidence_links = evidence_paths

    registry.update_metadata()
    save_features(registry)
    update_quick_reference(progress, registry)
    save_progress(progress)
    regenerate_progress_md()

    echo(f"✅ Verified: {feature_id} - {feature.description}")
    echo(f"   Evidence: {', '.join(evidence_paths)}")


def _feature_block(feature_id: str | None, reason: str | None) -> None:
    """Mark feature as blocked."""
    if not feature_id:
        raise PithException("Feature ID is required for 'block' action")
    if not reason:
        raise PithException("--reason is required for 'block' action")

    registry = load_features()
    progress = load_progress()

    feature = registry.get_feature(feature_id)
    if not feature:
        raise PithException(f"Feature not found: {feature_id}")

    feature.status = FeatureStatus.BLOCKED
    feature.blocked_by = reason
    feature.last_worked_on = datetime.now().isoformat()

    save_features(registry)
    update_quick_reference(progress, registry)
    save_progress(progress)
    regenerate_progress_md()

    echo(f"🚫 Blocked: {feature_id} - {feature.description}")
    echo(f"   Reason: {reason}")


def _feature_show(feature_id: str | None, json_output: bool) -> None:
    """Show feature details."""
    if not feature_id:
        raise PithException("Feature ID is required for 'show' action")

    registry = load_features()
    feature = registry.get_feature(feature_id)
    if not feature:
        raise PithException(f"Feature not found: {feature_id}")

    if json_output:
        echo(json.dumps(feature.to_dict(), indent=2))
        return

    status_icon = {
        FeatureStatus.NOT_STARTED: "⏳ Not started",
        FeatureStatus.IN_PROGRESS: "🔄 In progress",
        FeatureStatus.BLOCKED: "🚫 Blocked",
        FeatureStatus.VERIFIED: "✅ Verified",
    }.get(feature.status, str(feature.status))

    echo(f"📋 Feature: {feature.id}")
    echo(f"   Description: {feature.description}")
    echo(f"   Category: {feature.category.value}")
    echo(f"   Priority: {feature.priority}")
    echo(f"   Status: {status_icon}")
    echo(f"   Passes: {'Yes' if feature.passes else 'No'}")

    if feature.acceptance_criteria:
        echo("   Acceptance Criteria:")
        for ac in feature.acceptance_criteria:
            echo(f"     • {ac}")

    if feature.verified_at:
        echo(f"   Verified: {feature.verified_at} by {feature.verified_by}")

    if feature.evidence_links:
        echo(f"   Evidence: {', '.join(feature.evidence_links)}")

    if feature.blocked_by:
        echo(f"   Blocked by: {feature.blocked_by}")

    if feature.notes:
        echo(f"   Notes: {feature.notes}")


def _feature_edit(
    feature_id: str | None,
    description: str | None,
    category: str | None,
    priority: int | None,
    notes: str | None,
    add_criteria: str | None,
) -> None:
    """Edit a feature's mutable properties.

    Allows updating: notes, acceptance criteria (additive), priority, category.
    Forbids changing: id, description (enforces immutability of core spec).
    """
    if not feature_id:
        raise PithException("Feature ID is required for 'edit' action")

    # Check for forbidden modifications
    if description is not None:
        raise PithException(
            "Cannot modify description. Description is immutable once created. "
            "Use --notes to add clarifications."
        )

    registry = load_features()
    progress = load_progress()

    feature = registry.get_feature(feature_id)
    if not feature:
        raise PithException(f"Feature not found: {feature_id}")

    changes: list[str] = []

    # Update mutable fields
    if notes is not None:
        feature.notes = notes
        changes.append(f"notes: {notes}")

    if add_criteria is not None:
        new_criteria = [c.strip() for c in add_criteria.split(",")]
        feature.acceptance_criteria.extend(new_criteria)
        changes.append(f"added criteria: {', '.join(new_criteria)}")

    if category is not None:
        try:
            new_category = FeatureCategory(category)
            feature.category = new_category
            changes.append(f"category: {new_category.value}")
        except ValueError as e:
            valid_cats = ", ".join(c.value for c in FeatureCategory)
            raise PithException(f"Invalid category: {category}. Use: {valid_cats}") from e

    if priority is not None:
        if priority < 1 or priority > 5:
            raise PithException("Priority must be between 1 and 5")
        feature.priority = priority
        changes.append(f"priority: {priority}")

    if not changes:
        raise PithException(
            "No changes specified. Use --notes, --add-criteria, --category, or --priority"
        )

    feature.last_worked_on = datetime.now().isoformat()

    save_features(registry)
    update_quick_reference(progress, registry)
    save_progress(progress)
    regenerate_progress_md()

    echo(f"✏️  Updated: {feature_id} - {feature.description}")
    for change in changes:
        echo(f"   • {change}")


@app.command(name="session", pith="Manage coding sessions: start, end", priority=40)
@app.intents(
    "start session",
    "end session",
    "begin work",
    "finish work",
    "session management",
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
) -> None:
    """Manage coding sessions.

    Actions:
        start - Begin a new session (validates artifacts, shows status)
        end   - End current session (updates progress log)

    Examples:
        $ klondike session start --focus "F001 - User login"
        $ klondike session end --summary "Completed login form" --completed "Added form,Added validation"

    Related:
        status - Check project status
        feature start - Mark feature as in-progress
    """
    if action == "start":
        _session_start(focus)
    elif action == "end":
        _session_end(summary, completed, blockers, next_steps)
    else:
        raise PithException(f"Unknown action: {action}. Use: start, end")


def _session_start(focus: str | None) -> None:
    """Start a new session."""
    registry = load_features()
    progress = load_progress()

    # Validate artifact integrity
    echo("🔍 Validating artifacts...")

    # Check metadata consistency
    actual_total = len(registry.features)
    actual_passing = sum(1 for f in registry.features if f.passes)

    if registry.metadata.total_features != actual_total:
        echo(
            f"⚠️  Warning: metadata.totalFeatures ({registry.metadata.total_features}) != actual ({actual_total})"
        )
        registry.metadata.total_features = actual_total

    if registry.metadata.passing_features != actual_passing:
        echo(
            f"⚠️  Warning: metadata.passingFeatures ({registry.metadata.passing_features}) != actual ({actual_passing})"
        )
        registry.metadata.passing_features = actual_passing

    echo("✅ Artifacts validated")
    echo("")

    # Create new session
    session_num = progress.next_session_number()
    new_session = Session(
        session_number=session_num,
        date=datetime.now().strftime("%Y-%m-%d"),
        agent="Coding Agent",
        duration="(in progress)",
        focus=focus or "General development",
        completed=[],
        in_progress=["Session started"],
        blockers=[],
        next_steps=[],
        technical_notes=[],
    )

    progress.add_session(new_session)
    progress.current_status = "In Progress"

    update_quick_reference(progress, registry)
    save_features(registry)
    save_progress(progress)
    regenerate_progress_md()

    # Show status
    total = registry.metadata.total_features
    passing = registry.metadata.passing_features
    progress_pct = round(passing / total * 100, 1) if total > 0 else 0

    echo(f"🚀 Session {session_num} Started")
    echo(f"   Focus: {new_session.focus}")
    echo("")
    echo(f"📊 Project Status: {passing}/{total} features ({progress_pct}%)")

    # Show priority features
    priority = registry.get_priority_features(3)
    if priority:
        echo("")
        echo("🎯 Priority Features:")
        for f in priority:
            echo(f"   • {f.id}: {f.description}")

    echo("")
    echo("💡 Tip: Use 'klondike feature start <ID>' to mark a feature as in-progress")


def _session_end(
    summary: str | None,
    completed: str | None,
    blockers: str | None,
    next_steps: str | None,
) -> None:
    """End current session."""
    registry = load_features()
    progress = load_progress()

    current = progress.get_current_session()
    if not current:
        raise PithException("No active session found. Use 'klondike session start' first.")

    # Update session
    current.duration = "~session"  # TODO: Calculate actual duration
    current.in_progress = []

    if summary:
        current.focus = summary

    if completed:
        current.completed = [c.strip() for c in completed.split(",")]

    if blockers:
        current.blockers = [b.strip() for b in blockers.split(",")]

    if next_steps:
        current.next_steps = [n.strip() for n in next_steps.split(",")]
    else:
        # Auto-generate next steps from priority features
        priority = registry.get_priority_features(3)
        current.next_steps = [f"Continue {f.id}: {f.description}" for f in priority]

    progress.current_status = "Session Ended"
    update_quick_reference(progress, registry)
    save_progress(progress)
    regenerate_progress_md()

    echo(f"✅ Session {current.session_number} Ended")
    echo(f"   Focus: {current.focus}")

    if current.completed:
        echo("   Completed:")
        for item in current.completed:
            echo(f"     • {item}")

    # Reminder about uncommitted changes
    echo("")
    echo("💡 Remember to commit your changes before ending work!")


@app.command(pith="Validate artifact integrity", priority=50)
@app.intents(
    "validate artifacts",
    "check integrity",
    "verify features.json",
    "check progress",
    "validate",
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


@app.command(pith="Regenerate agent-progress.md from JSON", priority=60)
@app.intents(
    "regenerate markdown",
    "update progress file",
    "generate progress",
    "refresh markdown",
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
    registry = load_features()
    progress_log = load_progress()

    # Calculate metrics
    total = registry.metadata.total_features
    passing = registry.metadata.passing_features
    progress_pct = round(passing / total * 100, 1) if total > 0 else 0

    # Get current session
    current_session = progress_log.get_current_session()

    # Get features by status
    verified = registry.get_features_by_status(FeatureStatus.VERIFIED)
    in_progress = registry.get_features_by_status(FeatureStatus.IN_PROGRESS)
    blocked = registry.get_features_by_status(FeatureStatus.BLOCKED)
    not_started = registry.get_features_by_status(FeatureStatus.NOT_STARTED)

    # Get priority features for next steps
    priority = registry.get_priority_features(5)

    if format_type == "markdown":
        report_content = _generate_markdown_report(
            registry.project_name,
            registry.version,
            total,
            passing,
            progress_pct,
            verified,
            in_progress,
            blocked,
            not_started,
            priority,
            current_session,
            include_details,
        )
    else:
        report_content = _generate_plain_report(
            registry.project_name,
            registry.version,
            total,
            passing,
            progress_pct,
            verified,
            in_progress,
            blocked,
            not_started,
            priority,
            current_session,
            include_details,
        )

    if output:
        output_path = Path(output)
        output_path.write_text(report_content, encoding="utf-8")
        echo(f"✅ Report saved to {output_path}")
    else:
        echo(report_content)


def _generate_markdown_report(
    project_name: str,
    version: str,
    total: int,
    passing: int,
    progress_pct: float,
    verified: list,
    in_progress: list,
    blocked: list,
    not_started: list,
    priority: list,
    current_session,
    include_details: bool,
) -> str:
    """Generate a markdown-formatted stakeholder report."""
    from datetime import datetime

    lines = [
        f"# {project_name} - Progress Report",
        "",
        f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"**Version**: {version}",
        "",
        "---",
        "",
        "## Executive Summary",
        "",
        f"**Overall Progress**: {passing}/{total} features complete ({progress_pct}%)",
        "",
        "```",
        _generate_progress_bar(progress_pct),
        "```",
        "",
        "### Status Breakdown",
        "",
        "| Status | Count |",
        "|--------|-------|",
        f"| ✅ Verified | {len(verified)} |",
        f"| 🔄 In Progress | {len(in_progress)} |",
        f"| 🚫 Blocked | {len(blocked)} |",
        f"| ⏳ Not Started | {len(not_started)} |",
        "",
    ]

    if current_session:
        lines.extend(
            [
                "---",
                "",
                "## Current Session",
                "",
                f"**Focus**: {current_session.focus}",
                f"**Date**: {current_session.date}",
                "",
            ]
        )
        if current_session.completed:
            lines.append("### Completed This Session")
            lines.append("")
            for item in current_session.completed:
                lines.append(f"- {item}")
            lines.append("")

    if verified:
        lines.extend(
            [
                "---",
                "",
                "## Completed Features",
                "",
            ]
        )
        if include_details:
            for f in verified:
                lines.append(f"### {f.id}: {f.description}")
                lines.append("")
                if f.acceptance_criteria:
                    for ac in f.acceptance_criteria:
                        lines.append(f"- [x] {ac}")
                lines.append("")
        else:
            for f in verified:
                lines.append(f"- **{f.id}**: {f.description}")
            lines.append("")

    if in_progress:
        lines.extend(
            [
                "---",
                "",
                "## In Progress",
                "",
            ]
        )
        for f in in_progress:
            lines.append(f"- **{f.id}**: {f.description}")
        lines.append("")

    if blocked:
        lines.extend(
            [
                "---",
                "",
                "## Blocked",
                "",
            ]
        )
        for f in blocked:
            reason = f.blocked_by if f.blocked_by else "No reason specified"
            lines.append(f"- **{f.id}**: {f.description}")
            lines.append(f"  - *Reason*: {reason}")
        lines.append("")

    if priority:
        lines.extend(
            [
                "---",
                "",
                "## Next Steps",
                "",
                "Priority features to be implemented:",
                "",
            ]
        )
        for i, f in enumerate(priority, 1):
            lines.append(f"{i}. **{f.id}**: {f.description}")
        lines.append("")

    lines.extend(
        [
            "---",
            "",
            "*Report generated by klondike-spec-cli*",
        ]
    )

    return "\n".join(lines)


def _generate_plain_report(
    project_name: str,
    version: str,
    total: int,
    passing: int,
    progress_pct: float,
    verified: list,
    in_progress: list,
    blocked: list,
    not_started: list,
    priority: list,
    current_session,
    include_details: bool,
) -> str:
    """Generate a plain text stakeholder report."""
    from datetime import datetime

    lines = [
        f"{project_name} - Progress Report",
        "=" * 50,
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"Version: {version}",
        "",
        "EXECUTIVE SUMMARY",
        "-" * 30,
        "",
        f"Overall Progress: {passing}/{total} features ({progress_pct}%)",
        "",
        _generate_progress_bar(progress_pct),
        "",
        "Status Breakdown:",
        f"  Verified:     {len(verified)}",
        f"  In Progress:  {len(in_progress)}",
        f"  Blocked:      {len(blocked)}",
        f"  Not Started:  {len(not_started)}",
        "",
    ]

    if current_session:
        lines.extend(
            [
                "CURRENT SESSION",
                "-" * 30,
                "",
                f"Focus: {current_session.focus}",
                f"Date: {current_session.date}",
                "",
            ]
        )
        if current_session.completed:
            lines.append("Completed This Session:")
            for item in current_session.completed:
                lines.append(f"  - {item}")
            lines.append("")

    if verified:
        lines.extend(
            [
                "COMPLETED FEATURES",
                "-" * 30,
                "",
            ]
        )
        for f in verified:
            lines.append(f"  [{f.id}] {f.description}")
        lines.append("")

    if in_progress:
        lines.extend(
            [
                "IN PROGRESS",
                "-" * 30,
                "",
            ]
        )
        for f in in_progress:
            lines.append(f"  [{f.id}] {f.description}")
        lines.append("")

    if blocked:
        lines.extend(
            [
                "BLOCKED",
                "-" * 30,
                "",
            ]
        )
        for f in blocked:
            reason = f.blocked_by if f.blocked_by else "No reason specified"
            lines.append(f"  [{f.id}] {f.description}")
            lines.append(f"         Reason: {reason}")
        lines.append("")

    if priority:
        lines.extend(
            [
                "NEXT STEPS",
                "-" * 30,
                "",
            ]
        )
        for i, f in enumerate(priority, 1):
            lines.append(f"  {i}. [{f.id}] {f.description}")
        lines.append("")

    return "\n".join(lines)


def _generate_progress_bar(percentage: float, width: int = 40) -> str:
    """Generate an ASCII progress bar."""
    filled = int(width * percentage / 100)
    empty = width - filled
    bar = "█" * filled + "░" * empty
    return f"[{bar}] {percentage}%"


@app.command(name="import-features", pith="Import features from YAML or JSON file", priority=75)
@app.intents(
    "import features",
    "load features",
    "add features from file",
    "bulk import",
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
    import yaml

    input_path = Path(file_path)
    if not input_path.exists():
        raise PithException(f"File not found: {input_path}")

    # Load file content
    content = input_path.read_text(encoding="utf-8")

    # Parse based on extension
    if input_path.suffix.lower() in [".yaml", ".yml"]:
        try:
            data = yaml.safe_load(content)
        except yaml.YAMLError as e:
            raise PithException(f"Invalid YAML: {e}") from e
    elif input_path.suffix.lower() == ".json":
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            raise PithException(f"Invalid JSON: {e}") from e
    else:
        raise PithException(
            f"Unsupported file format: {input_path.suffix}. Use .yaml, .yml, or .json"
        )

    # Validate structure
    if not isinstance(data, dict):
        raise PithException("File must contain an object with 'features' key")

    features_data = data.get("features", [])
    if not isinstance(features_data, list):
        raise PithException("'features' must be a list")

    if not features_data:
        echo("No features found in file.")
        return

    # Load existing registry
    registry = load_features()
    progress = load_progress()

    existing_ids = {f.id for f in registry.features}
    next_num = len(registry.features) + 1  # Track next ID number locally
    imported = 0
    skipped = 0
    errors: list[str] = []

    for i, feat_data in enumerate(features_data):
        try:
            # Validate required fields
            if not isinstance(feat_data, dict):
                errors.append(f"Feature {i + 1}: must be an object")
                continue

            description = feat_data.get("description")
            if not description:
                errors.append(f"Feature {i + 1}: missing 'description'")
                continue

            # Check for explicit ID (for re-importing)
            feat_id = feat_data.get("id")
            if feat_id and feat_id in existing_ids:
                skipped += 1
                if not dry_run:
                    echo(f"⏭️  Skipped: {feat_id} (already exists)")
                continue

            # Generate new ID if not provided
            if not feat_id:
                feat_id = f"F{next_num:03d}"
                next_num += 1

            # Parse optional fields with defaults
            cat_str = feat_data.get("category", "core")
            try:
                category = FeatureCategory(cat_str)
            except ValueError:
                errors.append(f"Feature {i + 1}: invalid category '{cat_str}'")
                continue

            priority = feat_data.get("priority", 3)
            if not isinstance(priority, int) or priority < 1 or priority > 5:
                errors.append(f"Feature {i + 1}: priority must be 1-5")
                continue

            criteria = feat_data.get("acceptance_criteria", ["Feature works as described"])
            if not isinstance(criteria, list):
                criteria = [criteria]

            notes = feat_data.get("notes")

            if dry_run:
                echo(f"📋 Would import: {feat_id} - {description}")
            else:
                feature = Feature(
                    id=feat_id,
                    description=description,
                    category=category,
                    priority=priority,
                    acceptance_criteria=criteria,
                    notes=notes,
                )
                registry.add_feature(feature)

            imported += 1
            existing_ids.add(feat_id)

        except Exception as e:
            errors.append(f"Feature {i + 1}: {e}")

    # Save changes
    if not dry_run and imported > 0:
        save_features(registry)
        update_quick_reference(progress, registry)
        save_progress(progress)
        regenerate_progress_md()

    # Summary
    echo("")
    if dry_run:
        echo("📊 Dry run complete:")
    else:
        echo("📊 Import complete:")
    echo(f"   ✅ Imported: {imported}")
    echo(f"   ⏭️  Skipped: {skipped}")
    if errors:
        echo(f"   ❌ Errors: {len(errors)}")
        for err in errors[:5]:  # Show first 5 errors
            echo(f"      • {err}")
        if len(errors) > 5:
            echo(f"      ... and {len(errors) - 5} more")


@app.command(name="export-features", pith="Export features to YAML or JSON file", priority=76)
@app.intents(
    "export features",
    "save features",
    "backup features",
    "dump features",
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
    import yaml

    output_path = Path(output)

    # Validate extension
    if output_path.suffix.lower() not in [".yaml", ".yml", ".json"]:
        raise PithException(
            f"Unsupported file format: {output_path.suffix}. Use .yaml, .yml, or .json"
        )

    registry = load_features()
    features = registry.features

    # Apply status filter
    if status_filter:
        try:
            filter_status = FeatureStatus(status_filter)
            features = registry.get_features_by_status(filter_status)
        except ValueError as e:
            raise PithException(
                f"Invalid status: {status_filter}. Use: not-started, in-progress, blocked, verified"
            ) from e

    # Build export data
    features_data = []
    for f in features:
        if include_all:
            feat_dict = f.to_dict()
        else:
            # Export only essential fields for re-import
            feat_dict = {
                "id": f.id,
                "description": f.description,
                "category": f.category.value,
                "priority": f.priority,
                "acceptance_criteria": f.acceptance_criteria,
            }
            if f.notes:
                feat_dict["notes"] = f.notes

        features_data.append(feat_dict)

    export_data = {
        "project": registry.project_name,
        "version": registry.version,
        "exported_at": datetime.now().isoformat(),
        "features": features_data,
    }

    # Write to file
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.suffix.lower() == ".json":
        output_path.write_text(json.dumps(export_data, indent=2), encoding="utf-8")
    else:
        output_path.write_text(yaml.dump(export_data, sort_keys=False), encoding="utf-8")

    echo(f"✅ Exported {len(features_data)} features to {output_path}")


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
