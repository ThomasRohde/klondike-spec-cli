"""Tests for data models."""

from __future__ import annotations

import tempfile
from pathlib import Path

from klondike_spec_cli.models import (
    Config,
    Feature,
    FeatureCategory,
    FeatureMetadata,
    FeatureRegistry,
    FeatureStatus,
    PriorityFeatureRef,
    ProgressLog,
    QuickReference,
    Session,
)


class TestFeature:
    """Tests for Feature model."""

    def test_feature_creation(self) -> None:
        """Test creating a feature."""
        feature = Feature(
            id="F001",
            description="Test feature",
            category=FeatureCategory.CORE,
            priority=1,
            acceptance_criteria=["Criterion 1", "Criterion 2"],
        )

        assert feature.id == "F001"
        assert feature.description == "Test feature"
        assert feature.category == "core"
        assert feature.priority == 1
        assert feature.passes is False
        assert feature.status == FeatureStatus.NOT_STARTED

    def test_feature_to_dict(self) -> None:
        """Test feature serialization."""
        feature = Feature(
            id="F001",
            description="Test feature",
            category=FeatureCategory.CORE,
            priority=1,
            acceptance_criteria=["Criterion 1"],
        )

        data = feature.to_dict()

        assert data["id"] == "F001"
        assert data["description"] == "Test feature"
        assert data["category"] == "core"
        assert data["acceptanceCriteria"] == ["Criterion 1"]

    def test_feature_from_dict(self) -> None:
        """Test feature deserialization."""
        data = {
            "id": "F001",
            "description": "Test feature",
            "category": "core",
            "priority": 1,
            "acceptanceCriteria": ["Criterion 1"],
            "passes": True,
            "status": "verified",
        }

        feature = Feature.from_dict(data)

        assert feature.id == "F001"
        assert feature.category == "core"
        assert feature.passes is True
        assert feature.status == FeatureStatus.VERIFIED

    def test_feature_custom_category(self) -> None:
        """Test feature with custom category."""
        feature = Feature(
            id="F002",
            description="Integration test",
            category="integration",  # Custom category
            priority=2,
            acceptance_criteria=["Test passes"],
        )

        assert feature.category == "integration"
        data = feature.to_dict()
        assert data["category"] == "integration"

        # Test round-trip
        feature2 = Feature.from_dict(data)
        assert feature2.category == "integration"


class TestFeatureRegistry:
    """Tests for FeatureRegistry model."""

    def test_registry_creation(self) -> None:
        """Test creating a registry."""
        registry = FeatureRegistry(
            project_name="test-project",
            version="1.0.0",
            features=[],
            metadata=FeatureMetadata(
                created_at="2025-01-01T00:00:00Z",
                last_updated="2025-01-01T00:00:00Z",
                total_features=0,
                passing_features=0,
            ),
        )

        assert registry.project_name == "test-project"
        assert registry.version == "1.0.0"
        assert len(registry.features) == 0

    def test_add_feature(self) -> None:
        """Test adding a feature."""
        registry = FeatureRegistry(
            project_name="test-project",
            version="1.0.0",
            features=[],
            metadata=FeatureMetadata(
                created_at="2025-01-01T00:00:00Z",
                last_updated="2025-01-01T00:00:00Z",
                total_features=0,
                passing_features=0,
            ),
        )

        feature = Feature(
            id="F001",
            description="Test feature",
            category=FeatureCategory.CORE,
            priority=1,
            acceptance_criteria=["Criterion 1"],
        )

        registry.add_feature(feature)

        assert len(registry.features) == 1
        assert registry.metadata.total_features == 1

    def test_next_feature_id(self) -> None:
        """Test generating next feature ID."""
        registry = FeatureRegistry(
            project_name="test-project",
            version="1.0.0",
            features=[
                Feature(
                    id="F001",
                    description="Feature 1",
                    category=FeatureCategory.CORE,
                    priority=1,
                    acceptance_criteria=["Criterion"],
                ),
                Feature(
                    id="F002",
                    description="Feature 2",
                    category=FeatureCategory.CORE,
                    priority=1,
                    acceptance_criteria=["Criterion"],
                ),
            ],
            metadata=FeatureMetadata(
                created_at="2025-01-01T00:00:00Z",
                last_updated="2025-01-01T00:00:00Z",
                total_features=2,
                passing_features=0,
            ),
        )

        next_id = registry.next_feature_id()
        assert next_id == "F003"

    def test_get_features_by_status(self) -> None:
        """Test filtering features by status."""
        registry = FeatureRegistry(
            project_name="test-project",
            version="1.0.0",
            features=[
                Feature(
                    id="F001",
                    description="Feature 1",
                    category=FeatureCategory.CORE,
                    priority=1,
                    acceptance_criteria=["Criterion"],
                    status=FeatureStatus.NOT_STARTED,
                ),
                Feature(
                    id="F002",
                    description="Feature 2",
                    category=FeatureCategory.CORE,
                    priority=1,
                    acceptance_criteria=["Criterion"],
                    status=FeatureStatus.IN_PROGRESS,
                ),
            ],
            metadata=FeatureMetadata(
                created_at="2025-01-01T00:00:00Z",
                last_updated="2025-01-01T00:00:00Z",
                total_features=2,
                passing_features=0,
            ),
        )

        not_started = registry.get_features_by_status(FeatureStatus.NOT_STARTED)
        in_progress = registry.get_features_by_status(FeatureStatus.IN_PROGRESS)

        assert len(not_started) == 1
        assert len(in_progress) == 1
        assert not_started[0].id == "F001"
        assert in_progress[0].id == "F002"

    def test_save_and_load(self) -> None:
        """Test saving and loading registry."""
        registry = FeatureRegistry(
            project_name="test-project",
            version="1.0.0",
            features=[
                Feature(
                    id="F001",
                    description="Test feature",
                    category=FeatureCategory.CORE,
                    priority=1,
                    acceptance_criteria=["Criterion 1"],
                ),
            ],
            metadata=FeatureMetadata(
                created_at="2025-01-01T00:00:00Z",
                last_updated="2025-01-01T00:00:00Z",
                total_features=1,
                passing_features=0,
            ),
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = Path(f.name)

        try:
            registry.save(temp_path)
            loaded = FeatureRegistry.load(temp_path)

            assert loaded.project_name == "test-project"
            assert len(loaded.features) == 1
            assert loaded.features[0].id == "F001"
        finally:
            temp_path.unlink()


class TestSession:
    """Tests for Session model."""

    def test_session_creation(self) -> None:
        """Test creating a session."""
        session = Session(
            session_number=1,
            date="2025-01-01",
            agent="Test Agent",
            duration="~1 hour",
            focus="Testing",
            completed=["Task 1"],
            in_progress=[],
            blockers=[],
            next_steps=["Task 2"],
            technical_notes=["Note 1"],
        )

        assert session.session_number == 1
        assert session.agent == "Test Agent"
        assert len(session.completed) == 1

    def test_session_to_markdown(self) -> None:
        """Test session markdown generation."""
        session = Session(
            session_number=1,
            date="2025-01-01",
            agent="Test Agent",
            duration="~1 hour",
            focus="Testing",
            completed=["Task 1"],
            in_progress=[],
            blockers=[],
            next_steps=["Task 2"],
            technical_notes=[],
        )

        md = session.to_markdown()

        assert "### Session 1 - 2025-01-01" in md
        assert "**Agent**: Test Agent" in md
        assert "- Task 1" in md


class TestProgressLog:
    """Tests for ProgressLog model."""

    def test_progress_log_creation(self) -> None:
        """Test creating a progress log."""
        progress = ProgressLog(
            project_name="test-project",
            started_at="2025-01-01T00:00:00Z",
            current_status="Initialized",
            sessions=[],
            quick_reference=QuickReference(
                run_command="klondike",
                dev_server_port=None,
                key_files=[],
                priority_features=[],
            ),
        )

        assert progress.project_name == "test-project"
        assert progress.current_status == "Initialized"

    def test_add_session(self) -> None:
        """Test adding a session."""
        progress = ProgressLog(
            project_name="test-project",
            started_at="2025-01-01T00:00:00Z",
            current_status="Initialized",
            sessions=[],
            quick_reference=QuickReference(
                run_command="klondike",
                dev_server_port=None,
                key_files=[],
                priority_features=[],
            ),
        )

        session = Session(
            session_number=1,
            date="2025-01-01",
            agent="Test Agent",
            duration="~1 hour",
            focus="Testing",
            completed=[],
            in_progress=[],
            blockers=[],
            next_steps=[],
            technical_notes=[],
        )

        progress.add_session(session)

        assert len(progress.sessions) == 1
        assert progress.next_session_number() == 2

    def test_to_markdown(self) -> None:
        """Test markdown generation."""
        progress = ProgressLog(
            project_name="test-project",
            started_at="2025-01-01T00:00:00Z",
            current_status="Initialized",
            sessions=[
                Session(
                    session_number=1,
                    date="2025-01-01",
                    agent="Test Agent",
                    duration="~1 hour",
                    focus="Testing",
                    completed=["Task 1"],
                    in_progress=[],
                    blockers=[],
                    next_steps=[],
                    technical_notes=[],
                ),
            ],
            quick_reference=QuickReference(
                run_command="klondike",
                dev_server_port=None,
                key_files=[".klondike/features.json"],
                priority_features=[
                    PriorityFeatureRef(
                        id="F001",
                        description="Test feature",
                        status="not-started",
                    ),
                ],
            ),
        )

        md = progress.to_markdown()

        assert "# Agent Progress Log" in md
        assert "## Project: test-project" in md
        assert "| F001 | Test feature |" in md
        assert "### Session 1 - 2025-01-01" in md

    def test_to_markdown_with_prd_source(self) -> None:
        """Test markdown generation includes PRD source when provided."""
        progress = ProgressLog(
            project_name="test-project",
            started_at="2025-01-01T00:00:00Z",
            current_status="Initialized",
            sessions=[],
            quick_reference=QuickReference(
                run_command="klondike",
                dev_server_port=None,
                key_files=[],
                priority_features=[],
            ),
        )

        md = progress.to_markdown(prd_source="./docs/prd.md")

        assert "## PRD Source: [./docs/prd.md](./docs/prd.md)" in md

    def test_to_markdown_without_prd_source(self) -> None:
        """Test markdown generation excludes PRD line when not provided."""
        progress = ProgressLog(
            project_name="test-project",
            started_at="2025-01-01T00:00:00Z",
            current_status="Initialized",
            sessions=[],
            quick_reference=QuickReference(
                run_command="klondike",
                dev_server_port=None,
                key_files=[],
                priority_features=[],
            ),
        )

        md = progress.to_markdown()

        assert "PRD Source" not in md


class TestConfig:
    """Tests for Config model."""

    def test_config_defaults(self) -> None:
        """Test config default values."""
        config = Config()

        assert config.default_category == "core"
        assert config.default_priority == 2
        assert config.verified_by == "coding-agent"
        assert config.progress_output_path == "agent-progress.md"
        assert config.auto_regenerate_progress is True
        assert config.prd_source is None

    def test_config_to_dict(self) -> None:
        """Test config serialization."""
        config = Config(
            default_category=FeatureCategory.TESTING,
            default_priority=3,
            verified_by="test-agent",
            progress_output_path="docs/progress.md",
            auto_regenerate_progress=False,
        )

        data = config.to_dict()

        assert data["default_category"] == "testing"
        assert data["default_priority"] == 3
        assert data["verified_by"] == "test-agent"
        assert data["progress_output_path"] == "docs/progress.md"
        assert data["auto_regenerate_progress"] is False
        # prd_source should not be in dict when None
        assert "prd_source" not in data

    def test_config_to_dict_with_prd_source(self) -> None:
        """Test config serialization includes prd_source when set."""
        config = Config(
            default_category=FeatureCategory.CORE,
            default_priority=2,
            prd_source="./docs/prd.md",
        )

        data = config.to_dict()

        assert data["prd_source"] == "./docs/prd.md"

    def test_config_from_dict(self) -> None:
        """Test config deserialization."""
        data = {
            "default_category": "infrastructure",
            "default_priority": 1,
            "verified_by": "my-agent",
            "progress_output_path": "PROGRESS.md",
            "auto_regenerate_progress": True,
        }

        config = Config.from_dict(data)

        assert config.default_category == "infrastructure"
        assert config.default_priority == 1
        assert config.verified_by == "my-agent"
        assert config.progress_output_path == "PROGRESS.md"
        assert config.auto_regenerate_progress is True
        assert config.prd_source is None

    def test_config_from_dict_with_prd_source(self) -> None:
        """Test config deserialization with prd_source."""
        data = {
            "default_category": "core",
            "prd_source": "https://example.com/prd.md",
        }

        config = Config.from_dict(data)

        assert config.prd_source == "https://example.com/prd.md"

    def test_config_from_dict_with_custom_category(self) -> None:
        """Test config accepts custom categories."""
        data = {
            "default_category": "integration",
        }

        config = Config.from_dict(data)

        assert config.default_category == "integration"

    def test_config_save_and_load(self) -> None:
        """Test saving and loading config."""
        config = Config(
            default_category=FeatureCategory.UI,
            default_priority=4,
            verified_by="save-test-agent",
            progress_output_path="output/progress.md",
            auto_regenerate_progress=False,
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            temp_path = Path(f.name)

        try:
            config.save(temp_path)
            loaded = Config.load(temp_path)

            assert loaded.default_category == "ui"
            assert loaded.default_priority == 4
            assert loaded.verified_by == "save-test-agent"
            assert loaded.progress_output_path == "output/progress.md"
            assert loaded.auto_regenerate_progress is False
        finally:
            temp_path.unlink()

    def test_config_save_and_load_with_prd_source(self) -> None:
        """Test saving and loading config with prd_source."""
        config = Config(
            default_category=FeatureCategory.CORE,
            prd_source="./docs/requirements.md",
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            temp_path = Path(f.name)

        try:
            config.save(temp_path)
            loaded = Config.load(temp_path)

            assert loaded.prd_source == "./docs/requirements.md"
        finally:
            temp_path.unlink()

    def test_config_load_nonexistent_returns_defaults(self) -> None:
        """Test loading nonexistent config returns defaults."""
        config = Config.load(Path("/nonexistent/path/config.yaml"))

        assert config.default_category == "core"
        assert config.default_priority == 2
        assert config.verified_by == "coding-agent"
        assert config.prd_source is None


class TestFeatureRegistryPerformance:
    """Tests for FeatureRegistry performance with large registries."""

    def _create_large_registry(self, num_features: int) -> FeatureRegistry:
        """Create a registry with many features for testing."""
        features = [
            Feature(
                id=f"F{i:03d}",
                description=f"Feature {i} - Test description for performance testing",
                category=FeatureCategory.CORE,
                priority=(i % 5) + 1,
                acceptance_criteria=[f"Criterion {j}" for j in range(3)],
                passes=(i % 3 == 0),
                status=[
                    FeatureStatus.NOT_STARTED,
                    FeatureStatus.IN_PROGRESS,
                    FeatureStatus.VERIFIED,
                ][i % 3],
            )
            for i in range(1, num_features + 1)
        ]
        return FeatureRegistry(
            project_name="large-project",
            version="1.0.0",
            features=features,
            metadata=FeatureMetadata(
                created_at="2025-01-01T00:00:00Z",
                last_updated="2025-01-01T00:00:00Z",
                total_features=num_features,
                passing_features=num_features // 3,
            ),
        )

    def test_handles_100_features(self) -> None:
        """Test registry handles 100+ features efficiently."""
        import time

        registry = self._create_large_registry(150)

        # Test get_feature with indexed lookup is fast
        start = time.perf_counter()
        for i in range(1, 151):
            result = registry.get_feature(f"F{i:03d}")
            assert result is not None
        elapsed = time.perf_counter() - start

        # Should complete 150 lookups in under 100ms
        assert elapsed < 0.1, f"150 feature lookups took {elapsed:.3f}s"

    def test_indexed_lookup_faster_than_linear(self) -> None:
        """Test that indexed lookup is O(1) not O(n)."""
        registry = self._create_large_registry(100)

        # First access builds index
        registry.get_feature("F050")

        # Subsequent accesses should be instant
        import time

        start = time.perf_counter()
        for _ in range(1000):
            registry.get_feature("F050")
        elapsed = time.perf_counter() - start

        # 1000 lookups should be very fast
        assert elapsed < 0.05, f"1000 indexed lookups took {elapsed:.3f}s"

    def test_get_feature_ids_efficient(self) -> None:
        """Test get_feature_ids uses index."""
        registry = self._create_large_registry(100)

        ids = registry.get_feature_ids()

        assert len(ids) == 100
        assert "F001" in ids
        assert "F100" in ids

    def test_next_feature_id_with_gaps(self) -> None:
        """Test next_feature_id finds gaps in large registry."""
        registry = self._create_large_registry(50)

        # Remove F025 from the feature list (simulate gap)
        registry.features = [f for f in registry.features if f.id != "F025"]
        registry._invalidate_index()

        next_id = registry.next_feature_id()
        assert next_id == "F025"  # Should find the gap

    def test_add_feature_invalidates_index(self) -> None:
        """Test adding a feature invalidates and rebuilds index correctly."""
        registry = self._create_large_registry(10)

        # Trigger index build
        registry.get_feature("F001")
        assert registry._index_built is True

        # Add a new feature
        new_feature = Feature(
            id="F011",
            description="New feature",
            category=FeatureCategory.CORE,
            priority=1,
            acceptance_criteria=["Test"],
        )
        registry.add_feature(new_feature)

        # Index should be invalidated
        assert registry._index_built is False

        # Should still be able to find the new feature
        found = registry.get_feature("F011")
        assert found is not None
        assert found.description == "New feature"
