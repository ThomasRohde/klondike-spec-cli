"""Feature command handlers for Klondike Spec CLI."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime

from pith import PithException, echo

from .. import formatting
from ..data import (
    load_config,
    load_features,
    load_progress,
    regenerate_progress_md,
    save_features,
    save_progress,
    update_quick_reference,
)
from ..models import Feature, FeatureStatus
from ..ntfy import get_ntfy_client
from ..validation import (
    sanitize_string,
    validate_description,
    validate_feature_id,
    validate_output_path,
)


def feature_add(
    description: str | None,
    category: str | None,
    priority: int | str | None,
    criteria: str | None,
    notes: str | None,
) -> None:
    """Add a new feature."""
    # Validate description
    validated_desc = validate_description(description)

    registry = load_features()
    progress = load_progress()
    config = load_config()

    feature_id = registry.next_feature_id()
    # Use config defaults if not specified, accept any category string
    cat = category if category else config.default_category
    # Ensure priority is an integer (CLI may pass as string)
    prio = int(priority) if priority is not None else config.default_priority
    acceptance = (
        [sanitize_string(c.strip()) or "" for c in criteria.split(",") if c.strip()]
        if criteria
        else ["Feature works as described"]
    )

    # Sanitize notes
    sanitized_notes = sanitize_string(notes)

    feature = Feature(
        id=feature_id,
        description=validated_desc,
        category=cat,
        priority=prio,
        acceptance_criteria=acceptance,
        notes=sanitized_notes,
    )

    registry.add_feature(feature)
    save_features(registry)

    # Update quick reference and regenerate markdown
    update_quick_reference(progress, registry)
    save_progress(progress)
    regenerate_progress_md()

    echo(f"✅ Added feature {feature_id}: {description}")
    echo(f"   Category: {cat}, Priority: {prio}")


def feature_list(status_filter: str | None, json_output: bool) -> None:
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


def feature_start(feature_id: str | None) -> None:
    """Mark feature as in-progress."""
    validated_id = validate_feature_id(feature_id or "")

    registry = load_features()
    progress = load_progress()

    feature = registry.get_feature(validated_id)
    if not feature:
        raise PithException(f"Feature not found: {validated_id}")

    # Check for other in-progress features
    in_progress = registry.get_features_by_status(FeatureStatus.IN_PROGRESS)
    if in_progress and validated_id not in [f.id for f in in_progress]:
        echo(f"⚠️  Warning: Other features are in-progress: {', '.join(f.id for f in in_progress)}")

    feature.status = FeatureStatus.IN_PROGRESS
    feature.last_worked_on = datetime.now().isoformat()

    save_features(registry)
    update_quick_reference(progress, registry)
    save_progress(progress)
    regenerate_progress_md()

    echo(f"🔄 Started: {validated_id} - {feature.description}")
    echo(f"   Category: {feature.category}, Priority: {feature.priority}")
    echo("")

    # Show acceptance criteria
    if feature.acceptance_criteria:
        echo("   📋 Acceptance Criteria:")
        for ac in feature.acceptance_criteria:
            echo(f"      • {ac}")
        echo("")

    # Show notes if present
    if feature.notes:
        echo("   📝 Notes:")
        echo(f"      {feature.notes}")
        echo("")

    # Show if previously blocked
    if feature.blocked_by:
        echo(f"   ⚠️  Previously blocked by: {feature.blocked_by}")
        echo("")


def feature_verify(feature_id: str | None, evidence: str | None) -> None:
    """Mark feature as verified."""
    validated_id = validate_feature_id(feature_id or "")
    if not evidence:
        raise PithException("--evidence is required for 'verify' action")

    # Sanitize evidence input
    evidence = sanitize_string(evidence)
    if not evidence:
        raise PithException("--evidence cannot be empty")

    registry = load_features()
    progress = load_progress()
    config = load_config()

    feature = registry.get_feature(validated_id)
    if not feature:
        raise PithException(f"Feature not found: {validated_id}")

    evidence_paths = [sanitize_string(p.strip()) or "" for p in evidence.split(",") if p.strip()]

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

    # Send notification
    ntfy_client = get_ntfy_client(config.ntfy)
    if ntfy_client:
        ntfy_client.feature_verified(validated_id, feature.description)


def feature_block(feature_id: str | None, reason: str | None) -> None:
    """Mark feature as blocked."""
    if not feature_id:
        raise PithException("Feature ID is required for 'block' action")
    if not reason:
        raise PithException("--reason is required for 'block' action")

    registry = load_features()
    progress = load_progress()
    config = load_config()

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

    # Send notification
    ntfy_client = get_ntfy_client(config.ntfy)
    if ntfy_client:
        ntfy_client.feature_blocked(feature_id, feature.description, reason)
    echo(f"   Reason: {reason}")


def feature_show(feature_id: str | None, json_output: bool) -> None:
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
    echo(f"   Category: {feature.category}")
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


def feature_edit(
    feature_id: str | None,
    description: str | None,
    category: str | None,
    priority: int | str | None,
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
        # Accept any category string
        feature.category = category
        changes.append(f"category: {category}")

    if priority is not None:
        # Ensure priority is an integer (CLI may pass as string)
        prio = int(priority)
        if prio < 1 or prio > 5:
            raise PithException("Priority must be between 1 and 5")
        feature.priority = prio
        changes.append(f"priority: {prio}")

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


def feature_prompt(
    feature_id: str | None,
    output: str | None,
    interactive: bool,
) -> None:
    """Generate a copilot-ready prompt for implementing a feature.

    Creates a detailed prompt with feature description, acceptance criteria,
    dependencies, and pre-commit verification instructions.
    """
    if not feature_id:
        raise PithException("Feature ID is required for 'prompt' action")

    validated_id = validate_feature_id(feature_id)
    registry = load_features()

    feature = registry.get_feature(validated_id)
    if not feature:
        raise PithException(f"Feature not found: {validated_id}")

    # Build the prompt
    prompt_lines = [
        f"# Implement Feature {feature.id}",
        "",
        f"**Description:** {feature.description}",
        "",
        f"**Category:** {feature.category}",
        f"**Priority:** {feature.priority}",
        f"**Status:** {feature.status.value}",
        "",
    ]

    # Acceptance criteria
    if feature.acceptance_criteria:
        prompt_lines.append("## Acceptance Criteria")
        prompt_lines.append("")
        for i, criterion in enumerate(feature.acceptance_criteria, 1):
            prompt_lines.append(f"{i}. {criterion}")
        prompt_lines.append("")

    # Notes
    if feature.notes:
        prompt_lines.append("## Implementation Notes")
        prompt_lines.append("")
        prompt_lines.append(feature.notes)
        prompt_lines.append("")

    # Dependencies - check if feature has blocked_by or related features
    if feature.blocked_by:
        prompt_lines.append("## Dependencies/Blockers")
        prompt_lines.append("")
        prompt_lines.append(f"- {feature.blocked_by}")
        prompt_lines.append("")

    # Add project context
    total = registry.metadata.total_features
    passing = registry.metadata.passing_features
    progress_pct = round(passing / total * 100, 1) if total > 0 else 0

    prompt_lines.extend(
        [
            "## Project Context",
            "",
            f"- **Project:** {registry.project_name} v{registry.version}",
            f"- **Progress:** {passing}/{total} features ({progress_pct}%)",
            "",
        ]
    )

    # Pre-commit verification instructions
    prompt_lines.extend(
        [
            "## Pre-Commit Verification Requirements",
            "",
            "Before committing any changes, you MUST:",
            "",
            "1. **Run linting:** Check for code style issues",
            "   - Python: `uv run ruff check src tests`",
            "   - Node.js: `npm run lint`",
            "",
            "2. **Run format check:** Ensure code is properly formatted",
            "   - Python: `uv run ruff format --check src tests`",
            "   - Node.js: `npm run format`",
            "",
            "3. **Run tests:** Verify all tests pass",
            "   - Python: `uv run pytest`",
            "   - Node.js (Bash): `CI=true npm test`",
            "   - Node.js (PowerShell): `$env:CI='true'; npm test`",
            "",
            "4. **Build (if applicable):** Ensure project builds",
            "   - Node.js: `npm run build`",
            "",
            "5. **Record results:** Document each command's exit code",
            "",
            "Only commit if ALL checks pass. Fix any issues before committing.",
            "",
        ]
    )

    # Workflow instructions
    prompt_lines.extend(
        [
            "## Klondike Workflow",
            "",
            "1. Mark feature as started: `klondike feature start " + validated_id + "`",
            "2. Implement the feature following acceptance criteria",
            "3. Run pre-commit verification",
            "4. Commit changes with descriptive message",
            f"5. Verify feature: `klondike feature verify {validated_id} --evidence <test-output>`",
            "",
        ]
    )

    prompt_content = "\n".join(prompt_lines)

    # Handle output
    if interactive:
        # Launch copilot with this prompt
        from ..copilot import find_copilot_executable

        copilot_path = find_copilot_executable()
        if not copilot_path:
            raise PithException(
                "GitHub Copilot CLI not found. Install with: npm install -g @github/copilot\n"
                "Or see: https://docs.github.com/en/copilot/github-copilot-in-the-cli"
            )

        echo(f"🚀 Launching Copilot with prompt for {validated_id}...")

        # Build copilot command with safe tools
        cmd = [copilot_path]
        safe_tools = [
            "read_file",
            "list_dir",
            "grep_search",
            "file_search",
            "run_in_terminal",
            "create_file",
            "replace_string_in_file",
        ]
        for tool in safe_tools:
            cmd.extend(["--allow-tool", tool])
        cmd.extend(["--interactive", prompt_content])

        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            raise PithException(f"Copilot exited with error code {e.returncode}") from e
        except FileNotFoundError as e:
            raise PithException("GitHub Copilot CLI not found in PATH") from e

    elif output:
        # Write to file
        output_path = validate_output_path(output, extensions=[".md", ".txt"])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(prompt_content, encoding="utf-8")
        echo(f"✅ Prompt written to: {output_path}")
    else:
        # Print to stdout
        print(prompt_content)
