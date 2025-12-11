"""Data access layer for Klondike Spec CLI.

This module handles all file I/O operations for features, progress, and configuration.
"""

from __future__ import annotations

from pathlib import Path

from pith import PithException

from .models import (
    Config,
    FeatureRegistry,
    FeatureStatus,
    PriorityFeatureRef,
    ProgressLog,
)

# --- Constants ---

KLONDIKE_DIR = ".klondike"
FEATURES_FILE = "features.json"
PROGRESS_FILE = "agent-progress.json"
CONFIG_FILE = "config.yaml"
PROGRESS_MD_FILE = "agent-progress.md"


# --- Directory Functions ---


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


# --- Feature Registry Functions ---


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


# --- Progress Log Functions ---


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
    progress.save_markdown(md_path, prd_source=config.prd_source)


# --- Config Functions ---


def load_config(root: Path | None = None) -> Config:
    """Load the configuration file.

    Returns default config if file doesn't exist.
    """
    klondike_dir = get_klondike_dir(root)
    config_path = klondike_dir / CONFIG_FILE
    return Config.load(config_path)


# --- Quick Reference Functions ---


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
