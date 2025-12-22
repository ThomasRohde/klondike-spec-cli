"""Klondike MCP Server - Model Context Protocol server for klondike tools.

This module implements an MCP server that exposes klondike operations as tools,
allowing GitHub Copilot and other MCP-compatible clients to interact with
the klondike feature registry and session management.

Tools exposed:
- get_features: List all features with optional status filter
- get_feature: Get details for a specific feature
- start_feature: Mark a feature as in-progress
- verify_feature: Mark a feature as verified
- block_feature: Mark a feature as blocked
- get_status: Get project status summary
- start_session: Start a new coding session
- end_session: End the current session
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from .models import (
    Config,
    FeatureRegistry,
    FeatureStatus,
    PriorityFeatureRef,
    ProgressLog,
    Session,
)

# Configure logging to stderr for MCP compliance
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# MCP SDK imports - core dependency, but use try/except for graceful error handling
try:
    from mcp.server.fastmcp import FastMCP

    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    FastMCP = None  # type: ignore

# Constants
KLONDIKE_DIR = ".klondike"
FEATURES_FILE = "features.json"
PROGRESS_FILE = "agent-progress.json"
CONFIG_FILE = "config.yaml"
PROGRESS_MD_FILE = "agent-progress.md"


def _get_klondike_root() -> Path:
    """Find the klondike project root by searching for .klondike directory."""
    current = Path.cwd()
    while current != current.parent:
        if (current / KLONDIKE_DIR).exists():
            return current
        current = current.parent

    # Check current directory as fallback
    if (Path.cwd() / KLONDIKE_DIR).exists():
        return Path.cwd()

    raise FileNotFoundError(
        "Klondike project not found. Run 'klondike init' to initialize a project."
    )


def _load_features(root: Path | None = None) -> FeatureRegistry:
    """Load the feature registry."""
    if root is None:
        root = _get_klondike_root()
    features_path = root / KLONDIKE_DIR / FEATURES_FILE
    if not features_path.exists():
        raise FileNotFoundError(f"Features file not found: {features_path}")
    return FeatureRegistry.load(features_path)


def _save_features(registry: FeatureRegistry, root: Path | None = None) -> None:
    """Save the feature registry."""
    if root is None:
        root = _get_klondike_root()
    features_path = root / KLONDIKE_DIR / FEATURES_FILE
    registry.save(features_path)


def _load_progress(root: Path | None = None) -> ProgressLog:
    """Load the progress log."""
    if root is None:
        root = _get_klondike_root()
    progress_path = root / KLONDIKE_DIR / PROGRESS_FILE
    if not progress_path.exists():
        raise FileNotFoundError(f"Progress file not found: {progress_path}")
    return ProgressLog.load(progress_path)


def _save_progress(progress: ProgressLog, root: Path | None = None) -> None:
    """Save the progress log."""
    if root is None:
        root = _get_klondike_root()
    progress_path = root / KLONDIKE_DIR / PROGRESS_FILE
    progress.save(progress_path)


def _load_config(root: Path | None = None) -> Config:
    """Load the configuration file.

    Returns default config if file doesn't exist.
    """
    if root is None:
        root = _get_klondike_root()
    config_path = root / KLONDIKE_DIR / CONFIG_FILE
    return Config.load(config_path)


def _regenerate_progress_md(root: Path | None = None) -> None:
    """Regenerate agent-progress.md from JSON."""
    if root is None:
        root = _get_klondike_root()
    config = _load_config(root)
    progress = _load_progress(root)
    md_path = root / PROGRESS_MD_FILE
    progress.save_markdown(md_path, prd_source=config.prd_source)


def _update_quick_reference(progress: ProgressLog, registry: FeatureRegistry) -> None:
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


def create_mcp_server() -> FastMCP | None:
    """Create and configure the klondike MCP server.

    Returns None if MCP SDK is not available.
    """
    if not MCP_AVAILABLE:
        return None

    mcp = FastMCP(
        name="klondike",
        instructions=(
            "Klondike Spec Agent Tools - Manage features, sessions, and progress "
            "for agent-driven development workflows. Use these tools to track work, "
            "verify features, and maintain project status."
        ),
    )

    # --- Tool Definitions ---

    @mcp.tool()
    def get_features(status: str | None = None) -> dict[str, Any]:
        """Get all features from the klondike registry.

        Args:
            status: Optional filter by status (not-started, in-progress, blocked, verified)

        Returns:
            Dictionary with project info and list of features
        """
        try:
            registry = _load_features()

            features = registry.features
            if status:
                try:
                    filter_status = FeatureStatus(status)
                    features = registry.get_features_by_status(filter_status)
                except ValueError:
                    return {
                        "error": f"Invalid status: {status}. "
                        "Use: not-started, in-progress, blocked, verified"
                    }

            return {
                "project": registry.project_name,
                "version": registry.version,
                "total": registry.metadata.total_features,
                "passing": registry.metadata.passing_features,
                "features": [
                    {
                        "id": f.id,
                        "description": f.description,
                        "category": f.category,
                        "priority": f.priority,
                        "status": f.status.value,
                        "passes": f.passes,
                    }
                    for f in features
                ],
            }
        except FileNotFoundError as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": f"Failed to load features: {e}"}

    @mcp.tool()
    def get_feature(feature_id: str) -> dict[str, Any]:
        """Get details for a specific feature.

        Args:
            feature_id: The feature ID (e.g., F001)

        Returns:
            Feature details including acceptance criteria, status, and notes
        """
        try:
            registry = _load_features()
            feature = registry.get_feature(feature_id)

            if not feature:
                return {"error": f"Feature not found: {feature_id}"}

            return {
                "id": feature.id,
                "description": feature.description,
                "category": feature.category,
                "priority": feature.priority,
                "status": feature.status.value,
                "passes": feature.passes,
                "acceptance_criteria": feature.acceptance_criteria,
                "notes": feature.notes,
                "verified_at": feature.verified_at,
                "verified_by": feature.verified_by,
                "evidence_links": feature.evidence_links,
                "blocked_by": feature.blocked_by,
                "last_worked_on": feature.last_worked_on,
            }
        except FileNotFoundError as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": f"Failed to get feature: {e}"}

    @mcp.tool()
    def start_feature(feature_id: str) -> dict[str, Any]:
        """Mark a feature as in-progress.

        Args:
            feature_id: The feature ID to start (e.g., F001)

        Returns:
            Confirmation message or error
        """
        try:
            registry = _load_features()
            progress = _load_progress()

            feature = registry.get_feature(feature_id)
            if not feature:
                return {"error": f"Feature not found: {feature_id}"}

            # Check for other in-progress features
            in_progress = registry.get_features_by_status(FeatureStatus.IN_PROGRESS)
            warnings = []
            if in_progress and feature_id not in [f.id for f in in_progress]:
                warnings.append(
                    f"Other features are in-progress: {', '.join(f.id for f in in_progress)}"
                )

            feature.status = FeatureStatus.IN_PROGRESS
            feature.last_worked_on = datetime.now().isoformat()

            _save_features(registry)
            _update_quick_reference(progress, registry)
            _save_progress(progress)
            _regenerate_progress_md()

            result: dict[str, Any] = {
                "success": True,
                "message": f"Started: {feature_id} - {feature.description}",
                "feature": {
                    "id": feature.id,
                    "description": feature.description,
                    "status": feature.status.value,
                },
            }
            if warnings:
                result["warnings"] = warnings

            return result
        except FileNotFoundError as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": f"Failed to start feature: {e}"}

    @mcp.tool()
    def verify_feature(feature_id: str, evidence: str) -> dict[str, Any]:
        """Mark a feature as verified with evidence.

        Args:
            feature_id: The feature ID to verify (e.g., F001)
            evidence: Comma-separated list of evidence file paths or descriptions

        Returns:
            Confirmation message or error
        """
        try:
            registry = _load_features()
            progress = _load_progress()

            feature = registry.get_feature(feature_id)
            if not feature:
                return {"error": f"Feature not found: {feature_id}"}

            evidence_list = [e.strip() for e in evidence.split(",") if e.strip()]
            if not evidence_list:
                return {"error": "Evidence is required for verification"}

            feature.status = FeatureStatus.VERIFIED
            feature.passes = True
            feature.verified_at = datetime.now().isoformat()
            feature.verified_by = "MCP Agent"
            feature.evidence_links = evidence_list

            registry.update_metadata()
            _save_features(registry)
            _update_quick_reference(progress, registry)
            _save_progress(progress)
            _regenerate_progress_md()

            return {
                "success": True,
                "message": f"Verified: {feature_id} - {feature.description}",
                "feature": {
                    "id": feature.id,
                    "description": feature.description,
                    "status": feature.status.value,
                    "passes": feature.passes,
                    "evidence": evidence_list,
                },
            }
        except FileNotFoundError as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": f"Failed to verify feature: {e}"}

    @mcp.tool()
    def block_feature(feature_id: str, reason: str) -> dict[str, Any]:
        """Mark a feature as blocked with a reason.

        Args:
            feature_id: The feature ID to block (e.g., F001)
            reason: The reason for blocking

        Returns:
            Confirmation message or error
        """
        try:
            registry = _load_features()
            progress = _load_progress()

            feature = registry.get_feature(feature_id)
            if not feature:
                return {"error": f"Feature not found: {feature_id}"}

            if not reason:
                return {"error": "Reason is required for blocking"}

            feature.status = FeatureStatus.BLOCKED
            feature.blocked_by = reason
            feature.last_worked_on = datetime.now().isoformat()

            _save_features(registry)
            _update_quick_reference(progress, registry)
            _save_progress(progress)
            _regenerate_progress_md()

            return {
                "success": True,
                "message": f"Blocked: {feature_id} - {feature.description}",
                "feature": {
                    "id": feature.id,
                    "description": feature.description,
                    "status": feature.status.value,
                    "blocked_by": reason,
                },
            }
        except FileNotFoundError as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": f"Failed to block feature: {e}"}

    @mcp.tool()
    def get_status() -> dict[str, Any]:
        """Get project status summary.

        Returns:
            Project status including progress, feature counts, and current session
        """
        try:
            registry = _load_features()
            progress = _load_progress()

            total = registry.metadata.total_features
            passing = registry.metadata.passing_features
            progress_pct = round(passing / total * 100, 1) if total > 0 else 0

            current_session = progress.get_current_session()
            priority_features = registry.get_priority_features(3)

            by_status = {}
            for status in FeatureStatus:
                features = registry.get_features_by_status(status)
                by_status[status.value] = len(features)

            return {
                "project": registry.project_name,
                "version": registry.version,
                "progress": {
                    "total": total,
                    "passing": passing,
                    "percent": progress_pct,
                },
                "by_status": by_status,
                "current_session": (current_session.to_dict() if current_session else None),
                "priority_features": [
                    {"id": f.id, "description": f.description, "priority": f.priority}
                    for f in priority_features
                ],
            }
        except FileNotFoundError as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": f"Failed to get status: {e}"}

    @mcp.tool()
    def start_session(focus: str) -> dict[str, Any]:
        """Start a new coding session.

        Args:
            focus: What you'll be working on (e.g., "F001 - User login")

        Returns:
            Session information and project status
        """
        try:
            registry = _load_features()
            progress = _load_progress()

            session_num = progress.next_session_number()
            new_session = Session(
                session_number=session_num,
                date=datetime.now().strftime("%Y-%m-%d"),
                agent="MCP Agent",
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

            _update_quick_reference(progress, registry)
            _save_features(registry)
            _save_progress(progress)
            _regenerate_progress_md()

            total = registry.metadata.total_features
            passing = registry.metadata.passing_features
            progress_pct = round(passing / total * 100, 1) if total > 0 else 0

            priority_features = registry.get_priority_features(3)

            return {
                "success": True,
                "message": f"Session {session_num} started",
                "session": {
                    "number": session_num,
                    "focus": focus,
                    "date": new_session.date,
                },
                "project_status": {
                    "total": total,
                    "passing": passing,
                    "percent": progress_pct,
                },
                "priority_features": [
                    {"id": f.id, "description": f.description} for f in priority_features
                ],
            }
        except FileNotFoundError as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": f"Failed to start session: {e}"}

    @mcp.tool()
    def end_session(
        summary: str, completed: str | None = None, next_steps: str | None = None
    ) -> dict[str, Any]:
        """End the current coding session.

        Args:
            summary: Brief summary of what was accomplished
            completed: Comma-separated list of completed items (optional)
            next_steps: Comma-separated list of next steps (optional)

        Returns:
            Session summary or error
        """
        try:
            registry = _load_features()
            progress = _load_progress()

            current = progress.get_current_session()
            if not current:
                return {"error": "No active session found. Use start_session first."}

            current.duration = "~session"
            current.in_progress = []
            current.focus = summary

            if completed:
                current.completed = [c.strip() for c in completed.split(",") if c.strip()]

            if next_steps:
                current.next_steps = [n.strip() for n in next_steps.split(",") if n.strip()]
            else:
                priority = registry.get_priority_features(3)
                current.next_steps = [f"Continue {f.id}: {f.description}" for f in priority]

            progress.current_status = "Session Ended"
            _update_quick_reference(progress, registry)
            _save_progress(progress)
            _regenerate_progress_md()

            return {
                "success": True,
                "message": f"Session {current.session_number} ended",
                "session": {
                    "number": current.session_number,
                    "summary": summary,
                    "completed": current.completed,
                    "next_steps": current.next_steps,
                },
            }
        except FileNotFoundError as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": f"Failed to end session: {e}"}

    @mcp.tool()
    def validate_artifacts() -> dict[str, Any]:
        """Validate klondike artifact integrity.

        Returns:
            Validation results including any issues found
        """
        try:
            issues: list[str] = []

            try:
                registry = _load_features()
            except Exception as e:
                return {"error": f"Failed to load features.json: {e}"}

            try:
                progress = _load_progress()
            except Exception as e:
                return {"error": f"Failed to load agent-progress.json: {e}"}

            # Check features.json
            actual_total = len(registry.features)
            actual_passing = sum(1 for f in registry.features if f.passes)

            if registry.metadata.total_features != actual_total:
                issues.append(
                    f"metadata.totalFeatures ({registry.metadata.total_features}) "
                    f"!= actual ({actual_total})"
                )

            if registry.metadata.passing_features != actual_passing:
                issues.append(
                    f"metadata.passingFeatures ({registry.metadata.passing_features}) "
                    f"!= actual ({actual_passing})"
                )

            # Check for duplicate IDs
            ids = [f.id for f in registry.features]
            duplicates = [fid for fid in ids if ids.count(fid) > 1]
            if duplicates:
                issues.append(f"Duplicate feature IDs: {set(duplicates)}")

            # Check session numbers are sequential
            session_nums = [s.session_number for s in progress.sessions]
            expected = list(range(1, len(session_nums) + 1))
            if session_nums != expected:
                issues.append(f"Session numbers not sequential: {session_nums}")

            return {
                "valid": len(issues) == 0,
                "features": {
                    "total": actual_total,
                    "passing": actual_passing,
                },
                "sessions": len(progress.sessions),
                "issues": issues,
            }
        except Exception as e:
            return {"error": f"Validation failed: {e}"}

    return mcp


def generate_mcp_config(output_path: Path | None = None) -> dict[str, Any]:
    """Generate MCP configuration for copilot (legacy format).

    Args:
        output_path: Optional path to write the config file

    Returns:
        MCP configuration dictionary
    """
    import sys

    # Get the path to the klondike module
    python_path = sys.executable

    config = {
        "mcpServers": {
            "klondike": {
                "command": python_path,
                "args": ["-m", "klondike_spec_cli.mcp_server"],
                "env": {},
            }
        }
    }

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(config, indent=2), encoding="utf-8")

    return config


def generate_vscode_mcp_config(output_path: Path | None = None) -> dict[str, Any]:
    """Generate VS Code workspace MCP configuration (.vscode/mcp.json format).

    Creates configuration in the format expected by VS Code's MCP support:
    {
      "servers": {
        "klondike": {
          "type": "stdio",
          "command": "klondike",
          "args": ["mcp", "serve"]
        }
      }
    }

    Args:
        output_path: Optional path to write the config file

    Returns:
        MCP configuration dictionary in VS Code format
    """
    import shutil

    # Try to find klondike in PATH first (preferred - more portable)
    klondike_path = shutil.which("klondike")

    if klondike_path:
        # Use the klondike CLI directly (works across environments)
        config: dict[str, Any] = {
            "servers": {
                "klondike": {
                    "type": "stdio",
                    "command": klondike_path,
                    "args": ["mcp", "serve"],
                }
            }
        }
    else:
        # Fallback: use python -m approach
        import sys

        python_path = sys.executable
        config = {
            "servers": {
                "klondike": {
                    "type": "stdio",
                    "command": python_path,
                    "args": ["-m", "klondike_spec_cli.mcp_server"],
                }
            }
        }

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(config, indent=2), encoding="utf-8")

    return config


def run_server(transport: str = "stdio") -> None:
    """Run the MCP server.

    Args:
        transport: Transport type (stdio or streamable-http)
    """
    from typing import Literal, cast

    if not MCP_AVAILABLE:
        logger.error(
            "MCP SDK import failed. Try reinstalling: pip install --force-reinstall klondike-spec-cli"
        )
        raise ImportError("MCP SDK not available")

    mcp = create_mcp_server()
    if mcp is None:
        raise RuntimeError("Failed to create MCP server")

    logger.info("Starting klondike MCP server...")
    # Cast transport to the literal type expected by FastMCP
    transport_literal = cast(Literal["stdio", "sse", "streamable-http"], transport)
    mcp.run(transport=transport_literal)


# Entry point for running as module: python -m klondike_spec_cli.mcp_server
if __name__ == "__main__":
    run_server()
