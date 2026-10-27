"""Fixtures de los tests de referencia (golden)."""

import pytest

from pypex.core.results import ProjectAnalysisResult
from pypex.services.config_service import get_config
from tests.golden.snapshot import build_snapshots, run_pipeline, update_requested, write_snapshots


@pytest.fixture(scope="session")
def golden_result() -> ProjectAnalysisResult:
    return run_pipeline()


@pytest.fixture(scope="session")
def golden_snapshots(golden_result):
    snapshots = build_snapshots(golden_result)
    if update_requested():
        write_snapshots(snapshots)
    return snapshots


@pytest.fixture
def reset_config():
    """El comando analyze modifica el ConfigService global; se restaura al terminar."""
    yield
    get_config().reset_for_testing()
