"""Tests de referencia: fijan las métricas de PyPex sobre tests/golden/corpus."""

import difflib
import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from pypex.cli import analyze
from tests.golden.snapshot import (
    CORPUS_DIR,
    EXPECTED_DIR,
    PROJECT_SNAPSHOT,
    REGENERATE_HINT,
    UPDATE_ENV_VAR,
    build_snapshots,
    clean_message,
    corpus_names,
    describe_differences,
    normalize,
    render,
    run_pipeline,
    update_requested,
)

pytestmark = pytest.mark.golden
SNAPSHOT_NAMES = [*corpus_names(), PROJECT_SNAPSHOT]


@pytest.mark.parametrize("name", SNAPSHOT_NAMES)
def test_snapshot_matches(name, golden_snapshots):
    if update_requested():
        pytest.skip(f"Snapshot regenerado ({UPDATE_ENV_VAR}=1)")
    expected_path = EXPECTED_DIR / f"{name}.json"
    if not expected_path.exists():
        pytest.fail(f"Falta expected/{name}.json." + REGENERATE_HINT, pytrace=False)
    expected_text = expected_path.read_text(encoding="utf-8")
    actual_text = render(golden_snapshots[name])
    if actual_text == expected_text:
        return
    details = describe_differences(json.loads(expected_text), json.loads(actual_text))
    diff = "".join(
        difflib.unified_diff(
            expected_text.splitlines(keepends=True),
            actual_text.splitlines(keepends=True),
            fromfile=f"expected/{name}.json",
            tofile="actual",
            n=3,
        )
    )
    pytest.fail(
        f"Las métricas de '{name}' difieren del snapshot:\n"
        + "\n".join(details)
        + "\n\nDiff completo:\n"
        + diff
        + REGENERATE_HINT,
        pytrace=False,
    )


def test_snapshot_set_matches_corpus():
    if update_requested():
        pytest.skip("Regenerando")
    present = sorted(p.stem for p in EXPECTED_DIR.glob("*.json"))
    assert present == sorted(SNAPSHOT_NAMES), "Snapshots sobrantes o ausentes." + REGENERATE_HINT


def test_corpus_analyzed_without_file_errors(golden_result):
    assert golden_result.failed_files == 0
    assert golden_result.successful_files == len(corpus_names())
    assert not golden_result.global_errors
    assert all(not f.errors for f in golden_result.files.values())


def test_pipeline_is_deterministic(golden_snapshots):
    assert build_snapshots(run_pipeline()) == golden_snapshots


def _entity_from_json(e: dict) -> dict:
    data = {
        "name": e["name"],
        "type": e["type"],
        "line_start": e["source_info"].get("line_start"),
        "line_end": e["source_info"].get("line_end"),
        "metrics": normalize(e["metrics"]["metrics"]),
        "metric_errors": sorted(clean_message(x["message"]) for x in e["metrics"]["errors"]),
    }
    if e.get("children"):
        data["children"] = [_entity_from_json(c) for c in e["children"]]
    return data


def _sort_entity_errors(entity: dict) -> dict:
    result = dict(entity)
    result["metric_errors"] = sorted(result["metric_errors"])
    if result.get("children"):
        result["children"] = [_sort_entity_errors(child) for child in result["children"]]
    return result


def test_cli_json_report_matches_analyzer(tmp_path, golden_snapshots, reset_config):
    report = tmp_path / "report.json"
    result = CliRunner().invoke(
        analyze, [str(CORPUS_DIR), "--format", "json", "--output", str(report)]
    )
    assert result.exit_code == 0, result.output
    data = json.loads(report.read_text(encoding="utf-8"))
    problems: list[str] = []
    for path_str, file_data in data["files"].items():
        name = Path(path_str).stem
        snap = golden_snapshots[name]
        from_cli = {
            "module_metrics": normalize(file_data["module_metrics"]["metrics"]),
            "entities": [_entity_from_json(e) for e in file_data["entities"]],
        }
        expected = {
            "module_metrics": snap["module_metrics"],
            "entities": [_sort_entity_errors(e) for e in snap["entities"]],
        }
        problems += describe_differences(expected, from_cli, name)
    cli_project = normalize(data["project"]["project_metrics"]["metrics"])
    problems += describe_differences(
        golden_snapshots[PROJECT_SNAPSHOT]["project_metrics"], cli_project, PROJECT_SNAPSHOT
    )
    assert sorted(Path(p).stem for p in data["files"]) == corpus_names()
    assert not problems, "El JSON del CLI no coincide con el Analyzer:\n" + "\n".join(problems)
