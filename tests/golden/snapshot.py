"""Utilidades de los tests de referencia (golden) de PyPex."""

from __future__ import annotations

import json
import math
import os
from pathlib import Path
from typing import Any

from pypex.core.analyzer import Analyzer
from pypex.core.file_processor import FileProcessor
from pypex.core.results import AnalysisError, EntityAnalysisResult, ProjectAnalysisResult
from pypex.parser.ast_parser import ASTParser

GOLDEN_DIR = Path(__file__).resolve().parent
CORPUS_DIR = GOLDEN_DIR / "corpus"
EXPECTED_DIR = GOLDEN_DIR / "expected"
PROJECT_SNAPSHOT = "__project__"
UPDATE_ENV_VAR = "PYPEX_UPDATE_GOLDEN"
FLOAT_DIGITS = 6
REGENERATE_HINT = (
    f"\nSi el cambio es intencionado, regenera con: {UPDATE_ENV_VAR}=1 uv run pytest tests/golden"
)
ANALYSIS_CONFIG: dict[str, Any] = {
    "ignore_patterns": [],
    "max_file_size": 1024 * 1024,
    "no_progress_bar": True,
}


def update_requested() -> bool:
    return os.environ.get(UPDATE_ENV_VAR, "") == "1"


def corpus_names() -> list[str]:
    return sorted(p.stem for p in CORPUS_DIR.glob("*.py"))


def run_pipeline() -> ProjectAnalysisResult:
    """Ejecuta el pipeline real (parser + visitor + motor de métricas) sobre el corpus."""
    analyzer = Analyzer(parser=ASTParser(), file_processor=FileProcessor())
    return analyzer.analyze(CORPUS_DIR, dict(ANALYSIS_CONFIG))


def normalize(value: Any) -> Any:
    """Convierte valores a una forma JSON estable (floats redondeados, claves ordenadas)."""
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            return repr(value)
        rounded = round(value, FLOAT_DIGITS)
        return 0.0 if rounded == 0 else rounded
    if isinstance(value, dict):
        return {str(k): normalize(value[k]) for k in sorted(value, key=str)}
    if isinstance(value, (list, tuple)):
        return [normalize(v) for v in value]
    if isinstance(value, (set, frozenset)):
        return sorted(normalize(v) for v in value)
    raise TypeError(f"Tipo no serializable en el snapshot: {type(value).__name__}")


def clean_message(message: str) -> str:
    return message.replace(str(CORPUS_DIR), "<corpus>")


def _messages(errors: list[AnalysisError]) -> list[str]:
    return [clean_message(e.message) for e in errors]


def entity_snapshot(entity: EntityAnalysisResult) -> dict[str, Any]:
    data: dict[str, Any] = {
        "name": entity.name,
        "type": entity.entity_type,
        "line_start": entity.source_info.get("line_start"),
        "line_end": entity.source_info.get("line_end"),
        "metrics": normalize(entity.metrics.metrics),
        "metric_errors": _messages(entity.metrics.errors),
    }
    if entity.children:
        data["children"] = [entity_snapshot(c) for c in entity.children]
    return data


def build_snapshots(result: ProjectAnalysisResult) -> dict[str, dict[str, Any]]:
    snapshots: dict[str, dict[str, Any]] = {}
    for path_str, fr in result.files.items():
        rel = Path(path_str).resolve().relative_to(CORPUS_DIR)
        assert rel.parent == Path("."), "El corpus debe ser plano (sin subdirectorios)"
        mm = fr.module_metrics
        snapshots[rel.stem] = {
            "file": rel.as_posix(),
            "line_count": fr.line_count,
            "file_errors": _messages(fr.errors),
            "module_metrics": normalize(mm.metrics) if mm else None,
            "module_metric_errors": _messages(mm.errors) if mm else [],
            "entities": [entity_snapshot(e) for e in fr.entities],
        }
    pm = result.project_metrics
    snapshots[PROJECT_SNAPSHOT] = {
        "total_files": result.total_files,
        "successful_files": result.successful_files,
        "failed_files": result.failed_files,
        "total_lines_of_code": result.total_lines_of_code,
        "global_errors": _messages(result.global_errors),
        "project_metrics": normalize(pm.metrics) if pm else None,
        "project_metric_errors": _messages(pm.errors) if pm else [],
    }
    return dict(sorted(snapshots.items()))


def render(snapshot: dict[str, Any]) -> str:
    return json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n"


def write_snapshots(snapshots: dict[str, dict[str, Any]]) -> None:
    EXPECTED_DIR.mkdir(exist_ok=True)
    for stale in EXPECTED_DIR.glob("*.json"):
        if stale.stem not in snapshots:
            stale.unlink()
    for name, snap in snapshots.items():
        (EXPECTED_DIR / f"{name}.json").write_text(render(snap), encoding="utf-8", newline="\n")


def _short(value: Any, limit: int = 200) -> str:
    text = repr(value)
    return text if len(text) <= limit else text[:limit] + "..."


def _index_entities(items: list[Any]) -> dict[str, Any] | None:
    if not all(isinstance(x, dict) and "name" in x and "line_start" in x for x in items):
        return None
    index = {f"{e['name']}@{e['line_start']}": e for e in items}
    return index if len(index) == len(items) else None


def describe_differences(expected: Any, actual: Any, path: str = "") -> list[str]:
    """Lista legible de diferencias (ruta.a.la.métrica: esperado -> obtenido)."""
    if isinstance(expected, dict) and isinstance(actual, dict):
        lines: list[str] = []
        for key in sorted(set(expected) | set(actual), key=str):
            sub = f"{path}.{key}" if path else str(key)
            if key not in actual:
                lines.append(f"- {sub}: desaparece (era {_short(expected[key])})")
            elif key not in expected:
                lines.append(f"+ {sub}: nuevo ({_short(actual[key])})")
            else:
                lines.extend(describe_differences(expected[key], actual[key], sub))
        return lines
    if isinstance(expected, list) and isinstance(actual, list):
        exp_idx, act_idx = _index_entities(expected), _index_entities(actual)
        if exp_idx is not None and act_idx is not None:
            return describe_differences(exp_idx, act_idx, path)
    if expected != actual or type(expected) is not type(actual):
        return [f"~ {path}: {_short(expected)} -> {_short(actual)}"]
    return []
