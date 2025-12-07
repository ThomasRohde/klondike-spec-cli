"""Data models for Klondike Spec CLI.

These models represent the core data structures for features.json and
agent-progress.json files.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class FeatureStatus(str, Enum):
    """Status of a feature in the registry."""

    NOT_STARTED = "not-started"
    IN_PROGRESS = "in-progress"
    BLOCKED = "blocked"
    VERIFIED = "verified"


class FeatureCategory(str, Enum):
    """Category of a feature."""

    CORE = "core"
    UI = "ui"
    API = "api"
    TESTING = "testing"
    INFRASTRUCTURE = "infrastructure"
    DOCS = "docs"
    SECURITY = "security"
    PERFORMANCE = "performance"


@dataclass
class Feature:
    """A single feature in the registry."""

    id: str
    description: str
    category: FeatureCategory
    priority: int
    acceptance_criteria: list[str]
    passes: bool = False
    status: FeatureStatus = FeatureStatus.NOT_STARTED
    dependencies: list[str] = field(default_factory=list)
    estimated_effort: str | None = None
    verified_at: str | None = None
    verified_by: str | None = None
    evidence_links: list[str] = field(default_factory=list)
    blocked_by: str | list[str] | None = None
    last_worked_on: str | None = None
    notes: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "category": self.category.value
            if isinstance(self.category, FeatureCategory)
            else self.category,
            "priority": self.priority,
            "description": self.description,
            "dependencies": self.dependencies,
            "acceptanceCriteria": self.acceptance_criteria,
            "estimatedEffort": self.estimated_effort,
            "status": self.status.value if isinstance(self.status, FeatureStatus) else self.status,
            "passes": self.passes,
            "verifiedAt": self.verified_at,
            "verifiedBy": self.verified_by,
            "evidenceLinks": self.evidence_links,
            "blockedBy": self.blocked_by,
            "lastWorkedOn": self.last_worked_on,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Feature:
        """Create Feature from dictionary."""
        return cls(
            id=data["id"],
            description=data["description"],
            category=FeatureCategory(data.get("category", "core")),
            priority=data.get("priority", 2),
            acceptance_criteria=data.get("acceptanceCriteria", []),
            passes=data.get("passes", False),
            status=FeatureStatus(data.get("status", "not-started")),
            dependencies=data.get("dependencies", []),
            estimated_effort=data.get("estimatedEffort"),
            verified_at=data.get("verifiedAt"),
            verified_by=data.get("verifiedBy"),
            evidence_links=data.get("evidenceLinks", []),
            blocked_by=data.get("blockedBy"),
            last_worked_on=data.get("lastWorkedOn"),
            notes=data.get("notes"),
        )


@dataclass
class FeatureMetadata:
    """Metadata for the feature registry."""

    created_at: str
    last_updated: str
    total_features: int
    passing_features: int

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "createdAt": self.created_at,
            "lastUpdated": self.last_updated,
            "totalFeatures": self.total_features,
            "passingFeatures": self.passing_features,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FeatureMetadata:
        """Create FeatureMetadata from dictionary."""
        return cls(
            created_at=data.get("createdAt", datetime.now().isoformat()),
            last_updated=data.get("lastUpdated", datetime.now().isoformat()),
            total_features=data.get("totalFeatures", 0),
            passing_features=data.get("passingFeatures", 0),
        )


@dataclass
class FeatureRegistry:
    """The complete feature registry (features.json)."""

    project_name: str
    version: str
    features: list[Feature]
    metadata: FeatureMetadata

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "projectName": self.project_name,
            "version": self.version,
            "features": [f.to_dict() for f in self.features],
            "metadata": self.metadata.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FeatureRegistry:
        """Create FeatureRegistry from dictionary."""
        return cls(
            project_name=data.get("projectName", "unnamed-project"),
            version=data.get("version", "0.1.0"),
            features=[Feature.from_dict(f) for f in data.get("features", [])],
            metadata=FeatureMetadata.from_dict(data.get("metadata", {})),
        )

    @classmethod
    def load(cls, path: Path) -> FeatureRegistry:
        """Load FeatureRegistry from a JSON file."""
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    def save(self, path: Path) -> None:
        """Save FeatureRegistry to a JSON file."""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    def get_feature(self, feature_id: str) -> Feature | None:
        """Get a feature by ID."""
        for feature in self.features:
            if feature.id == feature_id:
                return feature
        return None

    def add_feature(self, feature: Feature) -> None:
        """Add a feature to the registry."""
        self.features.append(feature)
        self.update_metadata()

    def update_metadata(self) -> None:
        """Update metadata counts."""
        self.metadata.total_features = len(self.features)
        self.metadata.passing_features = sum(1 for f in self.features if f.passes)
        self.metadata.last_updated = datetime.now().isoformat()

    def next_feature_id(self) -> str:
        """Generate the next available feature ID."""
        existing_ids = {f.id for f in self.features}
        for i in range(1, 1000):
            candidate = f"F{i:03d}"
            if candidate not in existing_ids:
                return candidate
        raise ValueError("No available feature IDs")

    def get_features_by_status(self, status: FeatureStatus) -> list[Feature]:
        """Get all features with a given status."""
        return [f for f in self.features if f.status == status]

    def get_priority_features(self, limit: int = 3) -> list[Feature]:
        """Get top priority incomplete features."""
        incomplete = [f for f in self.features if not f.passes]
        sorted_features = sorted(incomplete, key=lambda f: (f.priority, f.id))
        return sorted_features[:limit]


@dataclass
class PriorityFeatureRef:
    """Reference to a priority feature for quick reference."""

    id: str
    description: str
    status: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "description": self.description,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PriorityFeatureRef:
        """Create from dictionary."""
        return cls(
            id=data["id"],
            description=data["description"],
            status=data["status"],
        )


@dataclass
class QuickReference:
    """Quick reference section of progress log."""

    run_command: str
    dev_server_port: int | None
    key_files: list[str]
    priority_features: list[PriorityFeatureRef]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "runCommand": self.run_command,
            "devServerPort": self.dev_server_port,
            "keyFiles": self.key_files,
            "priorityFeatures": [f.to_dict() for f in self.priority_features],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> QuickReference:
        """Create from dictionary."""
        return cls(
            run_command=data.get("runCommand", ""),
            dev_server_port=data.get("devServerPort"),
            key_files=data.get("keyFiles", []),
            priority_features=[
                PriorityFeatureRef.from_dict(f) for f in data.get("priorityFeatures", [])
            ],
        )


@dataclass
class Session:
    """A single session entry in the progress log."""

    session_number: int
    date: str
    agent: str
    duration: str
    focus: str
    completed: list[str]
    in_progress: list[str]
    blockers: list[str]
    next_steps: list[str]
    technical_notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "sessionNumber": self.session_number,
            "date": self.date,
            "agent": self.agent,
            "duration": self.duration,
            "focus": self.focus,
            "completed": self.completed,
            "inProgress": self.in_progress,
            "blockers": self.blockers,
            "nextSteps": self.next_steps,
            "technicalNotes": self.technical_notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Session:
        """Create Session from dictionary."""
        return cls(
            session_number=data.get("sessionNumber", 1),
            date=data.get("date", datetime.now().strftime("%Y-%m-%d")),
            agent=data.get("agent", "Coding Agent"),
            duration=data.get("duration", ""),
            focus=data.get("focus", ""),
            completed=data.get("completed", []),
            in_progress=data.get("inProgress", []),
            blockers=data.get("blockers", []),
            next_steps=data.get("nextSteps", []),
            technical_notes=data.get("technicalNotes", []),
        )

    def to_markdown(self) -> str:
        """Convert session to markdown format."""
        lines = [
            f"### Session {self.session_number} - {self.date}",
            f"**Agent**: {self.agent}",
            f"**Duration**: {self.duration}",
            f"**Focus**: {self.focus}",
            "",
            "#### Completed",
        ]

        if self.completed:
            for item in self.completed:
                lines.append(f"- {item}")
        else:
            lines.append("- None")

        lines.extend(["", "#### In Progress"])
        if self.in_progress:
            for item in self.in_progress:
                lines.append(f"- {item}")
        else:
            lines.append("- None")

        lines.extend(["", "#### Blockers"])
        if self.blockers:
            for item in self.blockers:
                lines.append(f"- {item}")
        else:
            lines.append("- None")

        lines.extend(["", "#### Recommended Next Steps"])
        if self.next_steps:
            for i, item in enumerate(self.next_steps, 1):
                lines.append(f"{i}. {item}")
        else:
            lines.append("1. Continue implementation")

        lines.extend(["", "#### Technical Notes"])
        if self.technical_notes:
            for item in self.technical_notes:
                lines.append(f"- {item}")
        else:
            lines.append("- None")

        return "\n".join(lines)


@dataclass
class ProgressLog:
    """The complete progress log (agent-progress.json)."""

    project_name: str
    started_at: str
    current_status: str
    sessions: list[Session]
    quick_reference: QuickReference

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "projectName": self.project_name,
            "startedAt": self.started_at,
            "currentStatus": self.current_status,
            "sessions": [s.to_dict() for s in self.sessions],
            "quickReference": self.quick_reference.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProgressLog:
        """Create ProgressLog from dictionary."""
        return cls(
            project_name=data.get("projectName", "unnamed-project"),
            started_at=data.get("startedAt", datetime.now().isoformat()),
            current_status=data.get("currentStatus", "Initialized"),
            sessions=[Session.from_dict(s) for s in data.get("sessions", [])],
            quick_reference=QuickReference.from_dict(data.get("quickReference", {})),
        )

    @classmethod
    def load(cls, path: Path) -> ProgressLog:
        """Load ProgressLog from a JSON file."""
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    def save(self, path: Path) -> None:
        """Save ProgressLog to a JSON file."""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    def add_session(self, session: Session) -> None:
        """Add a session to the log."""
        self.sessions.append(session)

    def get_current_session(self) -> Session | None:
        """Get the most recent session."""
        if self.sessions:
            return self.sessions[-1]
        return None

    def next_session_number(self) -> int:
        """Get the next session number."""
        if self.sessions:
            return max(s.session_number for s in self.sessions) + 1
        return 1

    def to_markdown(self) -> str:
        """Generate agent-progress.md content from this log."""
        lines = [
            "# Agent Progress Log",
            "",
            f"## Project: {self.project_name}",
            f"## Started: {self.started_at[:10]}",
            f"## Current Status: {self.current_status}",
            "",
            "---",
            "",
            "## Quick Reference",
            "",
            "### Running the Project",
            "```bash",
            f"{self.quick_reference.run_command}            # Show CLI help",
            f"{self.quick_reference.run_command} status     # Show project status",
            f"{self.quick_reference.run_command} feature list  # List all features",
            "```",
            "",
            "### Key Files",
        ]

        for key_file in self.quick_reference.key_files:
            lines.append(f"- `{key_file}`")

        lines.extend(
            [
                "",
                "### Current Priority Features",
                "| ID | Description | Status |",
                "|----|-------------|--------|",
            ]
        )

        status_icons = {
            "not-started": "⏳ Not started",
            "in-progress": "🔄 In progress",
            "blocked": "🚫 Blocked",
            "verified": "✅ Verified",
        }

        for pf in self.quick_reference.priority_features:
            status_display = status_icons.get(pf.status, pf.status)
            lines.append(f"| {pf.id} | {pf.description} | {status_display} |")

        lines.extend(
            [
                "",
                "---",
                "",
                "## Session Log",
                "",
            ]
        )

        for session in self.sessions:
            lines.append(session.to_markdown())
            lines.append("")
            lines.append("---")
            lines.append("")

        return "\n".join(lines)

    def save_markdown(self, path: Path) -> None:
        """Save as markdown file."""
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_markdown())
