"""Klondike Spec CLI - Agent workflow artifact management.

This package provides CLI tools for managing the Klondike Spec framework
artifacts including features.json and agent-progress tracking.
"""

from .cli import app, main
from .models import Feature, FeatureRegistry, ProgressLog, Session

__version__ = "0.1.0"

__all__ = [
    "Feature",
    "FeatureRegistry",
    "ProgressLog",
    "Session",
    "app",
    "main",
]
