"""Tests for openplan.core.pipeline."""
import datetime
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, call
import pytest

from openplan.core.pipeline import (
    EpicStatus,
    ImplementationPipeline,
    PipelineError,
    PipelineResult,
)
from openplan.core.schemas import (
    Epic,
    FeatureRef,
    Roadmap,
    SuccessMetric,
    ArchitecturalImpact,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def make_metric():
    return SuccessMetric(name="test", target="100", unit="%")


def make_arch():
    return ArchitecturalImpact(component="core", change_type="add", description="d")


def make_epic(epic_id: str, depends_on=None):
    return Epic(
        id=epic_id,
        title=f"Epic {epic_id}",
        outcome="outcome",
        success_metrics=[make_metric()],
        architectural_impact=[make_arch()],
        depends_on=depends_on or [],
    )


def make_roadmap(*epic_ids, deps=None):
    """Build a Roadmap with simple epics. deps: dict of epic_id -> [dep_ids]."""
    deps = deps or {}
    epics = [make_epic(eid, depends_on=deps.get(eid, [])) for eid in epic_ids]
    return Roadmap(
        id="test-roadmap",
        title="Test Roadmap",
        vision_id="v1",
        epics=epics,
    )


def make_mock_factory():
    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_factory = MagicMock(return_value=mock_client)
    return mock_factory, mock_client


# ── EpicStatus ─────────────────────────────────────────────────────────────────

def test_epic_status_has_six_members():
    assert len(EpicStatus) == 6


def test_epic_status_values():
    assert EpicStatus.PENDING == "pending"
    assert EpicStatus.IN_PROGRESS == "in_progress"
    assert EpicStatus.PASSING == "passing"
    assert EpicStatus.FAILED == "failed"
    assert EpicStatus.BLOCKED == "blocked"
    assert EpicStatus.SKIPPED == "skipped"


# ── ImplementationPipeline init ────────────────────────────────────────────────

def test_pipeline_init_defaults(tmp_path):
    factory = MagicMock()
    pipeline = ImplementationPipeline(
        project_dir=tmp_path,
        acp_client_factory=factory,
    )
    assert pipeline.project_dir == tmp_path
    assert pipeline.openspec_dir == tmp_path / "openspec"
    assert pipeline.model is None
    assert pipeline.skip_tests is False
    assert pipeline.from_epic is None
    assert pipeline._client_factory is factory


def test_pipeline_init_custom_openspec_dir(tmp_path):
    custom = tmp_path / "custom_spec"
    pipeline = ImplementationPipeline(
        project_dir=tmp_path,
        openspec_dir=custom,
        acp_client_factory=MagicMock(),
    )
    assert pipeline.openspec_dir == custom


# ── dry_run ────────────────────────────────────────────────────────────────────

def test_dry_run_does_not_call_factory(tmp_path, capsys):
    factory, client = make_mock_factory()
    roadmap = make_roadmap("epic-a", "epic-b")
    pipeline = ImplementationPipeline(
        project_dir=tmp_path,
        acp_client_factory=factory,
    )
    pipeline.dry_run(roadmap)
    factory.assert_not_called()


def test_dry_run_prints_epics(tmp_path, capsys):
    factory, _ = make_mock_factory()
    roadmap = make_roadmap("epic-a", "epic-b")
    pipeline = ImplementationPipeline(
        project_dir=tmp_path,
        acp_client_factory=factory,
    )
    # dry_run imports Console inside the method, patch at rich.console level
    with patch("rich.console.Console") as MockConsole:
        mock_console = MagicMock()
        MockConsole.return_value = mock_console
        pipeline.dry_run(roadmap)
    # console.print was called (at least once for header and each epic)
    assert mock_console.print.called


# ── run() success path ─────────────────────────────────────────────────────────

def test_run_all_passing_no_features(tmp_path):
    """With no feature files, all epics should become PASSING."""
    factory, client = make_mock_factory()
    roadmap = make_roadmap("epic-a", "epic-b")
    pipeline = ImplementationPipeline(
        project_dir=tmp_path,
        skip_tests=True,
        acp_client_factory=factory,
    )
    result = pipeline.run(roadmap)
    assert result.epic_statuses["epic-a"] == EpicStatus.PASSING
    assert result.epic_statuses["epic-b"] == EpicStatus.PASSING
    assert result.features_total == 0
    assert result.features_implemented == 0
    assert result.failed_epic is None


def test_run_with_features_calls_generate(tmp_path):
    """When feature YAML files exist, generate() should be called."""
    factory, client = make_mock_factory()
    roadmap = make_roadmap("epic-a")

    # Create a fake feature YAML
    features_dir = tmp_path / "openplan" / "features"
    features_dir.mkdir(parents=True)
    (features_dir / "epic-a-feat1.yaml").write_text("id: epic-a-feat1\n")

    pipeline = ImplementationPipeline(
        project_dir=tmp_path,
        skip_tests=True,
        acp_client_factory=factory,
    )
    result = pipeline.run(roadmap)

    assert result.features_total == 1
    assert result.features_implemented == 1
    assert client.generate.call_count == 2  # ff + apply
    client.generate.assert_any_call("/opsx-ff epic-a-feat1")
    client.generate.assert_any_call("/opsx-apply epic-a-feat1")


def test_run_passes_pytest(tmp_path):
    """When pytest passes, all epics should be PASSING."""
    factory, _ = make_mock_factory()
    roadmap = make_roadmap("epic-a")
    pipeline = ImplementationPipeline(
        project_dir=tmp_path,
        skip_tests=False,
        acp_client_factory=factory,
    )
    with patch("openplan.core.pipeline.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="passed", stderr="")
        result = pipeline.run(roadmap)
    assert result.epic_statuses["epic-a"] == EpicStatus.PASSING


# ── run() failure path ─────────────────────────────────────────────────────────

def test_run_pytest_fail_raises_pipeline_error(tmp_path):
    factory, _ = make_mock_factory()
    roadmap = make_roadmap("epic-a", "epic-b", deps={"epic-b": ["epic-a"]})
    pipeline = ImplementationPipeline(
        project_dir=tmp_path,
        skip_tests=False,
        acp_client_factory=factory,
    )
    with patch("openplan.core.pipeline.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="test failed!")
        with pytest.raises(PipelineError) as exc_info:
            pipeline.run(roadmap)
    assert "epic-a" in str(exc_info.value)


def test_run_pytest_fail_marks_failed_and_blocked(tmp_path):
    factory, _ = make_mock_factory()
    roadmap = make_roadmap("epic-a", "epic-b", deps={"epic-b": ["epic-a"]})
    pipeline = ImplementationPipeline(
        project_dir=tmp_path,
        skip_tests=False,
        acp_client_factory=factory,
    )
    with patch("openplan.core.pipeline.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="failed")
        try:
            pipeline.run(roadmap)
        except PipelineError:
            pass
    # epic-a failed, epic-b should be blocked (depends on epic-a)
    # We can check via _write_report having been called — inspect the result
    # by re-checking from a captured result
    report_path = tmp_path / "openplan" / "implementation_report.md"
    assert report_path.exists()
    content = report_path.read_text()
    assert "failed" in content
    assert "blocked" in content


# ── from_epic skipping ─────────────────────────────────────────────────────────

def test_from_epic_skips_earlier_epics(tmp_path):
    factory, _ = make_mock_factory()
    roadmap = make_roadmap("epic-a", "epic-b", "epic-c")
    pipeline = ImplementationPipeline(
        project_dir=tmp_path,
        skip_tests=True,
        from_epic="epic-b",
        acp_client_factory=factory,
    )
    result = pipeline.run(roadmap)
    assert result.epic_statuses["epic-a"] == EpicStatus.SKIPPED
    assert result.epic_statuses["epic-b"] == EpicStatus.PASSING
    assert result.epic_statuses["epic-c"] == EpicStatus.PASSING


# ── skip_tests ─────────────────────────────────────────────────────────────────

def test_skip_tests_does_not_call_pytest(tmp_path):
    factory, _ = make_mock_factory()
    roadmap = make_roadmap("epic-a")
    pipeline = ImplementationPipeline(
        project_dir=tmp_path,
        skip_tests=True,
        acp_client_factory=factory,
    )
    with patch("openplan.core.pipeline.subprocess.run") as mock_run:
        result = pipeline.run(roadmap)
        mock_run.assert_not_called()
    assert result.epic_statuses["epic-a"] == EpicStatus.PASSING


# ── _write_report ──────────────────────────────────────────────────────────────

def test_write_report_creates_file(tmp_path):
    factory, _ = make_mock_factory()
    roadmap = make_roadmap("epic-a")
    pipeline = ImplementationPipeline(
        project_dir=tmp_path,
        skip_tests=True,
        acp_client_factory=factory,
    )
    result = pipeline.run(roadmap)
    report_path = tmp_path / "openplan" / "implementation_report.md"
    assert report_path.exists()


def test_write_report_content(tmp_path):
    factory, _ = make_mock_factory()
    roadmap = make_roadmap("epic-a", "epic-b")
    pipeline = ImplementationPipeline(
        project_dir=tmp_path,
        skip_tests=True,
        acp_client_factory=factory,
    )
    result = pipeline.run(roadmap)
    report_path = tmp_path / "openplan" / "implementation_report.md"
    content = report_path.read_text()
    assert "# OpenPlan Implementation Report" in content
    assert "epic-a" in content
    assert "epic-b" in content
    assert "passing" in content
    assert roadmap.id in content
    assert roadmap.title in content


def test_write_report_shows_failure_details(tmp_path):
    factory, _ = make_mock_factory()
    roadmap = make_roadmap("epic-a")
    pipeline = ImplementationPipeline(
        project_dir=tmp_path,
        skip_tests=False,
        acp_client_factory=factory,
    )
    with patch("openplan.core.pipeline.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="SOME FAILURE OUTPUT")
        try:
            pipeline.run(roadmap)
        except PipelineError:
            pass
    report_path = tmp_path / "openplan" / "implementation_report.md"
    content = report_path.read_text()
    assert "SOME FAILURE OUTPUT" in content


# ── _discover_features ─────────────────────────────────────────────────────────

def test_discover_features_returns_stems(tmp_path):
    features_dir = tmp_path / "openplan" / "features"
    features_dir.mkdir(parents=True)
    (features_dir / "epic-a-feat1.yaml").write_text("")
    (features_dir / "epic-a-feat2.yaml").write_text("")
    (features_dir / "epic-b-feat1.yaml").write_text("")

    pipeline = ImplementationPipeline(
        project_dir=tmp_path,
        acp_client_factory=MagicMock(),
    )
    features = pipeline._discover_features("epic-a")
    assert features == ["epic-a-feat1", "epic-a-feat2"]


def test_discover_features_empty(tmp_path):
    pipeline = ImplementationPipeline(
        project_dir=tmp_path,
        acp_client_factory=MagicMock(),
    )
    features = pipeline._discover_features("nonexistent-epic")
    assert features == []


# ── _propagate_blocked ─────────────────────────────────────────────────────────

def test_propagate_blocked_marks_transitive_dependents(tmp_path):
    epics = [
        make_epic("a"),
        make_epic("b", depends_on=["a"]),
        make_epic("c", depends_on=["b"]),
        make_epic("d"),
    ]
    epic_statuses = {e.id: EpicStatus.PENDING for e in epics}
    pipeline = ImplementationPipeline(
        project_dir=tmp_path,
        acp_client_factory=MagicMock(),
    )
    pipeline._propagate_blocked("a", epic_statuses, epics)
    assert epic_statuses["b"] == EpicStatus.BLOCKED
    assert epic_statuses["c"] == EpicStatus.BLOCKED
    assert epic_statuses["d"] == EpicStatus.PENDING  # unrelated
    assert epic_statuses["a"] == EpicStatus.PENDING  # not self-blocked


# ── exit code 5 (no tests collected) ──────────────────────────────────────────

def test_pytest_exit_code_5_is_passing(tmp_path):
    """pytest exit code 5 means 'no tests collected' — should be treated as pass."""
    factory, _ = make_mock_factory()
    roadmap = make_roadmap("epic-a")
    pipeline = ImplementationPipeline(
        project_dir=tmp_path,
        skip_tests=False,
        acp_client_factory=factory,
    )
    with patch("openplan.core.pipeline.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=5, stdout="", stderr="")
        result = pipeline.run(roadmap)
    assert result.epic_statuses["epic-a"] == EpicStatus.PASSING
