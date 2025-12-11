"""Import/export command handlers."""

import json
from datetime import datetime

from pith import Argument, Option, PithException, echo

from klondike_spec_cli.data import (
    load_features,
    load_progress,
    regenerate_progress_md,
    save_features,
    save_progress,
    update_quick_reference,
)
from klondike_spec_cli.models import Feature, FeatureStatus
from klondike_spec_cli.validation import validate_file_path, validate_output_path


def import_features_command(
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

    # Validate file path
    input_path = validate_file_path(file_path, must_exist=True)

    # Validate extension
    if input_path.suffix.lower() not in [".yaml", ".yml", ".json"]:
        raise PithException(
            f"Unsupported file format: {input_path.suffix}. Use .yaml, .yml, or .json"
        )

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
            # Accept any category string
            category = cat_str

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


def export_features_command(
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

    # Validate output path
    output_path = validate_output_path(output, extensions=[".yaml", ".yml", ".json"])

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
                "category": f.category,
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
