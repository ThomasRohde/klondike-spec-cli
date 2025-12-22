"""Klondike Spec CLI - Agent workflow artifact management.

This package provides CLI tools for managing the Klondike Spec framework
artifacts including features.json and agent-progress tracking.
"""

from .cli import app, main
from .models import Feature, FeatureRegistry, ProgressLog, Session

try:
    from ._version import __version__
except ImportError:
    __version__ = "0.0.0+unknown"

__all__ = [
    "Feature",
    "FeatureRegistry",
    "ProgressLog",
    "Session",
    "app",
    "main",
    "__version__",
]
