"""Tests para el JSONReporter."""

from pypex.reporters.json_reporter import JSONReporter
from tests.unit.core.test_results_processor import _project_with_entities


class TestJSONReporterHotSpots:
    """Los hot spots deben incluir las entidades con mayor valor de cada métrica."""

    def test_top_hot_spots_are_not_empty(self):
        hot_spots = JSONReporter()._get_top_hot_spots(_project_with_entities())

        assert hot_spots[0] == {
            "metric": "cyclomatic_complexity",
            "entity_name": "Service.run",
            "entity_type": "method",
            "value": 9,
            "file_path": "pkg/module.py",
            "line_start": 3,
        }

    def test_entities_by_metric_are_not_empty(self):
        top = JSONReporter()._get_entities_by_metric(
            _project_with_entities(), "cyclomatic_complexity", 10
        )

        assert [e["entity_name"] for e in top] == ["Service.run", "helper", "Service"]
