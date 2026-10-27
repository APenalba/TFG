"""Behavioral tests for the text console reporter."""

import io
import sys
from datetime import datetime
from pathlib import Path

import pytest

from pypex.core.results import (
    AnalysisError,
    EntityAnalysisResult,
    ErrorSeverity,
    FileAnalysisResult,
    MetricsResult,
    ProjectAnalysisResult,
)
from pypex.reporters import console_reporter
from pypex.reporters.console_reporter import Colors, ConsoleReporter, Icons
from pypex.services.config_service import get_config

WIDTH = 60


@pytest.fixture(autouse=True)
def _clean_state(monkeypatch):
    get_config().reset_for_testing()
    yield
    get_config().reset_for_testing()


class _FixedDatetime(datetime):
    @classmethod
    def now(cls, tz=None):
        return cls(2026, 1, 2, 3, 4, 5)


@pytest.fixture
def fixed_now(monkeypatch):
    monkeypatch.setattr(console_reporter, "datetime", _FixedDatetime)


class _StubThresholds:
    _active_profile = "strict"

    def get_thresholds(self, metric_name, profile=None):
        return {"low": 5, "medium": 10, "high": 20}


@pytest.fixture
def stub_thresholds(monkeypatch):
    monkeypatch.setattr("pypex.metrics.thresholds.get_threshold_config", lambda: _StubThresholds())


def _entity(name, entity_type="function", cc=None, line=1, children=(), **extra):
    metrics = {} if cc is None else {"cyclomatic_complexity": cc}
    metrics.update(extra)
    return EntityAnalysisResult(
        name=name,
        entity_type=entity_type,
        metrics=MetricsResult(name, entity_type, metrics),
        children=list(children),
        source_info={"line_start": line},
    )


def _file(
    path,
    *,
    line_count=40,
    file_size=100,
    module_metrics=None,
    entities=(),
    errors=(),
    analysis_time_ms=0.0,
):
    p = Path(path)
    mm = MetricsResult(p.stem, "module", module_metrics) if module_metrics is not None else None
    return FileAnalysisResult(
        file_path=p,
        module_name=".".join(p.with_suffix("").parts),
        file_size=file_size,
        line_count=line_count,
        module_metrics=mm,
        entities=list(entities),
        errors=list(errors),
        analysis_time_ms=analysis_time_ms,
    )


def _project(*files, project_metrics=None, analysis_time_ms=1500.0, global_errors=(), loc=None):
    ok = sum(1 for f in files if f.was_successful)
    return ProjectAnalysisResult(
        project_name="demo",
        root_path=Path("pkg"),
        analysis_timestamp="2026-01-01T00:00:00",
        project_metrics=MetricsResult("demo", "project", project_metrics)
        if project_metrics
        else None,
        files={str(f.file_path): f for f in files},
        total_files=len(files),
        successful_files=ok,
        failed_files=len(files) - ok,
        total_lines_of_code=loc if loc is not None else sum(f.line_count for f in files),
        analysis_time_ms=analysis_time_ms,
        global_errors=list(global_errors),
    )


def _good():
    return _file(
        "pkg/good.py",
        file_size=120,
        module_metrics={"cyclomatic_complexity": 4, "cognitive_complexity": 2},
        entities=[
            _entity("helper", cc=3, line=5),
            _entity(
                "Svc", "class", cc=2, line=10, children=[_entity("run", "method", cc=4, line=12)]
            ),
        ],
        analysis_time_ms=12.5,
    )


def _bad():
    return _file(
        "pkg/bad.py",
        line_count=700,
        file_size=9000,
        module_metrics={
            "cyclomatic_complexity": 80,
            "lines_of_code": 700,
            "fan_in_out": 25,
            "lcom4": 7,
        },
        entities=[
            _entity("tangled", cc=25, line=3, cognitive_complexity=30),
            _entity("knot", cc=12, line=50),
        ],
    )


def _broken():
    return _file(
        "pkg/broken.py",
        line_count=1,
        file_size=10,
        errors=[
            AnalysisError("Syntax error", ErrorSeverity.CRITICAL, "parser", "pkg/broken.py", 1)
        ],
    )


def _render(project, verbosity="normal", *, colors=False, reporter=None, **kwargs):
    buf = io.StringIO()
    rep = reporter or ConsoleReporter(output_stream=buf, use_colors=colors, width=WIDTH)
    if reporter is not None:
        rep.output = buf
    rep.generate_report(project, verbosity=verbosity, **kwargs)
    return buf.getvalue()


def _section(output: str, title: str) -> list[str]:
    lines = output.splitlines()
    start = next(i for i, line in enumerate(lines) if title in line)
    end = next((j for j in range(start + 1, len(lines)) if not lines[j].strip()), len(lines))
    return lines[start:end]


class TestColorsAndStreams:
    def test_colorize_disabled_returns_plain_text(self):
        assert (
            ConsoleReporter(output_stream=io.StringIO(), use_colors=False).colorize("x", Colors.RED)
            == "x"
        )

    def test_colorize_enabled_wraps_with_ansi(self):
        assert (
            ConsoleReporter(output_stream=io.StringIO(), use_colors=True).colorize("x", Colors.RED)
            == f"{Colors.RED}x{Colors.RESET}"
        )

    def test_auto_colors_disabled_for_non_tty(self):
        assert ConsoleReporter(output_stream=io.StringIO()).use_colors is False

    @pytest.mark.parametrize(
        ("term", "wt_session", "vscode", "expected"),
        [
            ("xterm-256color", None, None, True),
            ("dumb", "1", None, True),
            ("dumb", None, "1", True),
            ("dumb", None, None, False),
        ],
    )
    def test_auto_colors_tty(self, monkeypatch, term, wt_session, vscode, expected):
        class Tty(io.StringIO):
            def isatty(self):
                return True

        for key, value in (
            ("TERM", term),
            ("WT_SESSION", wt_session),
            ("VSCODE_INJECTION", vscode),
        ):
            if value is None:
                monkeypatch.delenv(key, raising=False)
            else:
                monkeypatch.setenv(key, value)
        assert ConsoleReporter(output_stream=Tty()).use_colors is expected

    def test_default_stream_is_stdout(self):
        assert ConsoleReporter(use_colors=False).output is sys.stdout

    def test_colored_report_contains_ansi(self):
        out = _render(_project(_good()), colors=True)
        assert Colors.RESET in out
        assert (
            f"{Colors.BOLD}{Colors.BRIGHT_GREEN}{Icons.QUALITY} Quality Score: 100.0/100 (Excellent)"
            in out
        )


class TestScoringHelpers:
    @pytest.mark.parametrize(
        ("score", "level"),
        [
            (80, "Excellent"),
            (79.9, "Good"),
            (60, "Good"),
            (40, "Fair"),
            (20, "Poor"),
            (19.9, "Critical"),
        ],
    )
    def test_quality_level(self, score, level):
        assert ConsoleReporter(output_stream=io.StringIO())._get_quality_level(score) == level

    @pytest.mark.parametrize(
        ("score", "color"),
        [
            (80, Colors.BRIGHT_GREEN),
            (60, Colors.GREEN),
            (40, Colors.YELLOW),
            (20, Colors.RED),
            (0, Colors.BRIGHT_RED),
        ],
    )
    def test_quality_color(self, score, color):
        assert ConsoleReporter(output_stream=io.StringIO())._get_quality_color(score) == color

    @pytest.mark.parametrize(
        ("complexity", "color"),
        [(5, Colors.GREEN), (10, Colors.YELLOW), (20, Colors.RED), (21, Colors.BRIGHT_RED)],
    )
    def test_complexity_color(self, complexity, color):
        assert (
            ConsoleReporter(output_stream=io.StringIO())._get_complexity_color(complexity) == color
        )

    @pytest.mark.parametrize(("value", "status"), [(5, "good"), (10, "warning"), (11, "critical")])
    def test_metric_status(self, stub_thresholds, value, status):
        assert (
            ConsoleReporter(output_stream=io.StringIO())._get_metric_status(
                "cyclomatic_complexity", value
            )
            == status
        )


class TestQuietMode:
    def test_quiet_single_line(self):
        project = _project(_good(), _file("pkg/b.py", line_count=10))
        out = _render(project, "quiet")
        assert [line for line in out.splitlines() if line.strip()] == [
            f"{Icons.SUCCESS} demo: 2/2 files, 50 LOC, Quality: 100.0/100"
        ]

    def test_quiet_warning_icon_on_low_success(self):
        out = _render(_project(_good(), _broken()), "quiet")
        assert out.startswith(Icons.WARNING) and "1/2 files" in out

    @pytest.mark.xfail(
        strict=True,
        reason="BUG console_reporter.py:211-214,1113-1114: quiet ignora la puntuación detallada strict",
    )
    def test_quiet_uses_detailed_score_in_strict_profile(self):
        project = _project(_good())
        reporter = ConsoleReporter(output_stream=io.StringIO(), use_colors=False, width=WIDTH)
        reporter.processor.config = {"thresholds_profile": "strict"}
        assert "Quality: 100.0/100" in _render(project, "quiet", reporter=reporter)
        assert reporter.quick_summary(project).endswith("Quality: 100.0/100")


class TestNormalMode:
    @pytest.fixture
    def project(self):
        return _project(_good(), _bad(), _broken())

    def test_section_order(self, project, fixed_now):
        out = _render(project)
        expected = [
            "PyPex Analysis Report - demo",
            "Summary:",
            "Quality Score:",
            "Project Overview:",
            "Hot Spots",
            "Files Summary:",
            "Top Recommendations:",
            "Performance:",
            "Generated by PyPex",
        ]
        indices = [out.index(item) for item in expected]
        assert indices == sorted(indices)
        for absent in (
            "Project Statistics:",
            "Error Analysis",
            "Detailed File Analysis:",
            "Configuration:",
        ):
            assert absent not in out

    def test_header_and_footer(self, project, fixed_now):
        lines = _render(project).splitlines()
        assert lines[0] == lines[2] == "═" * WIDTH
        assert len(lines[1]) == WIDTH
        assert "PyPex Analysis Report - demo" in lines[1]
        assert "Generated by PyPex © 2026 | 2026-01-02 03:04:05" in "\n".join(lines)

    def test_summary_stats(self, project):
        out = _render(project)
        assert _section(out, "Summary:")[1:] == [
            "   Files analyzed: 3 | Success: 2 | Failed: 1 | Rate: 66.7%",
            "   Total LOC: 741 | Analysis time: 1.50s",
        ]
        assert "Total LOC: 1,234" in _render(_project(_good(), loc=1234))

    def test_project_overview(self, project):
        section = _section(_render(project), "Project Overview:")
        assert any("📏 File sizes: 2 small, 0 medium, 1 large" in line for line in section)
        assert any("🔄 Total Complexity: CC 44, Cognitive 30" in line for line in section)
        assert any("📊 Code Volume: 741 lines" in line for line in section)

    def test_hot_spots_ranked_with_location(self, project):
        section = _section(_render(project), "Hot Spots (Top 3):")
        assert section[1:4] == [
            "   1. tangled() - CogC: 30 📍 bad.py:3",
            "   2. tangled() - CC: 25 📍 bad.py:3",
            "   3. knot() - CC: 12 📍 bad.py:50",
        ]

    def test_hot_spots_methods_prefixed_and_missing_line(self):
        project = _project(
            _file(
                "pkg/a.py",
                entities=[
                    _entity("Svc", "class", children=[_entity("run", "method", cc=4, line=0)])
                ],
            )
        )
        spot = next(line for line in _render(project).splitlines() if "Svc.run() - CC: 4" in line)
        assert "Svc.run() - CC: 4 📍 a.py" in spot and "a.py:" not in spot

    def test_no_hot_spots_without_entities(self):
        assert "Hot Spots" not in _render(_project(_file("pkg/a.py")))

    def test_files_summary_categories(self, project):
        out = _render(project)
        section = _section(out, "Files Summary:")
        for item in (
            "⚠️ Files with issues (1):",
            "• pkg.bad - large file, high complexity, high coupling, low cohesion, 2 complex functions",
            "✅ Good files (1):",
            "• pkg.good (40 LOC, 2 entities, avg CC: 3.0, max CC: 4)",
            "❌ Failed files (1):",
            "• pkg.broken (1 errors)",
        ):
            assert any(item in line for line in section)

    def test_files_summary_truncation(self):
        files = [_file(f"pkg/good{i}.py") for i in range(5)]
        files += [
            _file(f"pkg/large{i}.py", module_metrics={"lines_of_code": 600}) for i in range(4)
        ]
        out = _render(_project(*files))
        assert "... and 2 more good files" in out
        assert "... and 1 more with issues" in out

    def test_show_files_false_hides_summary(self, project):
        assert "Files Summary:" not in _render(project, show_files=False)

    def test_top_recommendations_deduplicated(self, project, monkeypatch):
        reporter = ConsoleReporter(output_stream=io.StringIO(), use_colors=False, width=WIDTH)
        monkeypatch.setattr(
            reporter.processor,
            "generate_quality_report",
            lambda r: {"overall_quality_score": 50.0, "recommendations": ["r1", "r2", "r3"]},
        )
        monkeypatch.setattr(
            reporter.processor,
            "generate_detailed_quality_report",
            lambda r: {"overall_score": 50.0, "recommendations": ["r3", "r4"]},
        )
        out = _render(project, reporter=reporter)
        assert _section(out, "Top Recommendations:") == [
            "💡 Top Recommendations:",
            "   1. r1",
            "   2. r2",
            "   3. r3",
            "   ... and 1 more (use --verbosity verbose for details)",
        ]
        assert "Quality Score: 50.0/100 (Fair)" in out

    def test_no_recommendations_message(self, project, monkeypatch):
        reporter = ConsoleReporter(output_stream=io.StringIO(), use_colors=False, width=WIDTH)
        monkeypatch.setattr(
            reporter.processor,
            "generate_quality_report",
            lambda r: {"overall_quality_score": 90.0, "recommendations": []},
        )
        monkeypatch.setattr(
            reporter.processor,
            "generate_detailed_quality_report",
            lambda r: {"overall_score": 90.0, "recommendations": []},
        )
        assert "Excellent! No recommendations needed." in _render(project, reporter=reporter)

    def test_quality_falls_back_to_detailed_report(self, project, monkeypatch):
        reporter = ConsoleReporter(output_stream=io.StringIO(), use_colors=False, width=WIDTH)
        monkeypatch.setattr(reporter.processor, "generate_quality_report", lambda r: None)
        monkeypatch.setattr(
            reporter.processor,
            "generate_detailed_quality_report",
            lambda r: {"overall_score": 30.0},
        )
        assert "Quality Score: 30.0/100 (Poor)" in _render(project, reporter=reporter)

    def test_no_quality_section_without_reports(self, project, monkeypatch):
        reporter = ConsoleReporter(output_stream=io.StringIO(), use_colors=False, width=WIDTH)
        monkeypatch.setattr(reporter.processor, "generate_quality_report", lambda r: None)
        monkeypatch.setattr(reporter.processor, "generate_detailed_quality_report", lambda r: None)
        assert "Quality Score" not in _render(project, reporter=reporter)

    def test_performance_basic(self, project):
        section = _section(_render(project), "Performance:")
        assert any("Analysis time: 1.50s" in line for line in section)
        assert "Memory usage" not in "\n".join(section)

    @pytest.mark.xfail(
        strict=True,
        reason="BUG console_reporter.py:836,846: create_performance_report omite velocidad y memoria",
    )
    def test_performance_speed(self, project):
        assert "Speed: 2.0 files/sec" in _render(project)

    def test_unknown_verbosity_falls_back_to_normal(self, project):
        a, b = _render(project), _render(project, verbosity="loquesea")
        headings = [
            "PyPex Analysis Report",
            "Summary:",
            "Quality Score:",
            "Project Overview:",
            "Hot Spots",
            "Files Summary:",
            "Top Recommendations:",
            "Performance:",
        ]
        assert [x for x in headings if x in a] == [x for x in headings if x in b]


class TestVerboseMode:
    @pytest.fixture
    def project(self):
        warning = AnalysisError("notice", ErrorSeverity.WARNING, "analyzer", "pkg/a.py", 2)
        warning_without_path = AnalysisError(
            "another notice", ErrorSeverity.WARNING, "analyzer", "", 0
        )
        metrics = {
            "cyclomatic_complexity": {"total": 120.0, "avg": 5.0},
            "lines_of_code": {"sum": 741},
            "fan_in_out": {"x": 1},
            "lcom4": 2.0,
        }
        return _project(
            _good(),
            _bad(),
            _broken(),
            project_metrics=metrics,
            global_errors=[warning, warning_without_path],
        )

    def test_section_order_verbose(self, project):
        out = _render(project, verbosity="verbose")
        headings = [
            "Project Statistics:",
            "Metrics Overview:",
            "Hot Spots",
            "Error Analysis",
            "Detailed File Analysis:",
            "Recommendations:",
            "Performance:",
        ]
        assert [out.index(h) for h in headings] == sorted(out.index(h) for h in headings)
        assert "Project Overview:" not in out and "Configuration:" not in out

    def test_project_statistics(self, project, stub_thresholds):
        section = _section(_render(project, verbosity="verbose"), "Project Statistics:")
        for text in (
            "Small (<100 LOC): 2",
            "Medium (100-500 LOC): 0",
            "Large (>500 LOC): 1",
            "Low: 2",
            "Medium: 1",
            "High: 1",
            "Cyclomatic Complexity: 44",
            "Lines Of Code: 741",
        ):
            assert any(text in line for line in section)

    def test_metrics_overview_value_shapes(self, project):
        assert _section(_render(project, verbosity="verbose"), "Metrics Overview:") == [
            "📈 Metrics Overview:",
            "   🔄 Complexity: 120.0",
            "   📏 Lines of Code: 741.0",
            "   🔗 Coupling: Complex",
            "   🎯 Cohesion: 2.0",
        ]

    def test_no_metrics_overview_without_project_metrics(self):
        assert "Metrics Overview:" not in _render(_project(_good()), verbosity="verbose")

    def test_error_analysis_counts_by_severity(self, project):
        out = _render(project, verbosity="verbose")
        section = _section(out, "Error Analysis")
        assert "⚠️ Error Analysis (2 total):" in section
        assert "Warning: 2" in "\n".join(section)
        assert not any(line.strip().startswith("•") for line in section)

    @pytest.mark.xfail(
        strict=True,
        reason="BUG results.py:214-218: get_all_errors compara severidades como cadenas",
    )
    def test_error_analysis_includes_critical(self):
        section = _section(_render(_project(_broken()), verbosity="verbose"), "Error Analysis")
        assert "Critical: 1" in section

    def test_detailed_file_analysis(self, project):
        out = _render(project, verbosity="verbose", show_entities=True)
        for text in (
            "✅ good.py",
            "Path: pkg/good.py",
            "Size: 120 bytes | Lines: 40",
            "Metrics: CC: 4, Cog: 2",
            "⚠️ bad.py",
            "Size: 9,000 bytes | Lines: 700",
            "Issues: large file, high complexity, high coupling, low cohesion, 2 complex functions",
            "Metrics: CC: 80",
            "❌ broken.py",
            "Errors:",
            "❌ Syntax error",
        ):
            assert text in out
        detailed = _section(out, "Detailed File Analysis:")
        assert "Analysis time:" not in "\n".join(detailed)

    def test_entities_listed_only_with_flag(self):
        file = _file(
            "pkg/a.py",
            entities=[
                _entity("fn", cc=1),
                _entity("Svc", "class", cc=2),
                _entity("other", cc=3),
                _entity("none"),
            ],
        )
        project = _project(file)
        out = _render(project, verbosity="verbose", show_entities=True)
        assert "Entities (4):" in out and "🏗️ Svc (CC: 2)" in out
        assert "none (CC:" not in out and "... and 1 more" in out
        assert "Entities (" not in _render(project, verbosity="verbose", show_entities=False)

    def test_full_recommendations_top5(self, project, monkeypatch):
        reporter = ConsoleReporter(output_stream=io.StringIO(), use_colors=False, width=WIDTH)
        monkeypatch.setattr(
            reporter.processor,
            "generate_quality_report",
            lambda r: {
                "overall_quality_score": 70.0,
                "recommendations": [f"r{i}" for i in range(1, 8)],
            },
        )
        monkeypatch.setattr(
            reporter.processor,
            "generate_detailed_quality_report",
            lambda r: {"overall_score": 70.0, "recommendations": [f"r{i}" for i in range(1, 8)]},
        )
        out = _render(project, verbosity="verbose", reporter=reporter)
        for i in range(1, 6):
            assert f"   {i}. r{i}" in out
        assert "   ... and 2 more" in out
        monkeypatch.setattr(
            reporter.processor,
            "generate_quality_report",
            lambda r: {"overall_quality_score": 90.0, "recommendations": []},
        )
        monkeypatch.setattr(
            reporter.processor,
            "generate_detailed_quality_report",
            lambda r: {"overall_score": 90.0, "recommendations": []},
        )
        assert "Excellent! No recommendations." in _render(
            project, verbosity="verbose", reporter=reporter
        )


class TestDebugMode:
    @pytest.fixture
    def project(self):
        metrics = {
            "cyclomatic_complexity": {"total": 120.0, "avg": 5.0},
            "lines_of_code": {"sum": 741},
            "fan_in_out": {"x": 1},
            "lcom4": 2.0,
        }
        return _project(_good(), _bad(), _broken(), project_metrics=metrics)

    def test_project_metrics_detailed_with_flag(self, project):
        out = _render(project, verbosity="debug", show_metrics=True)
        section = _section(out, "Project Metrics (Detailed):")
        assert "   cyclomatic_complexity:" in section
        assert "     • total: 120.00" in section
        assert "   lcom4: 2.00" in section
        assert "Project Metrics (Detailed):" not in _render(
            project, verbosity="debug", show_metrics=False
        )

    def test_error_analysis_detailed(self):
        errors = [
            AnalysisError(f"warn{i}", ErrorSeverity.WARNING, "analyzer", f"pkg/x{i}.py", i)
            for i in range(5)
        ]
        errors.append(AnalysisError("no path", ErrorSeverity.WARNING, "analyzer", "", 0))
        section = _section(
            _render(_project(_good(), global_errors=errors), verbosity="debug"), "Error Analysis"
        )
        assert any("• no path" in line for line in section)
        for i in range(2):
            assert any(f"• warn{i} in x{i}.py" in line for line in section)
        assert any("... and 3 more" in line for line in section)

    def test_file_analysis_time_shown(self):
        assert "Analysis time: 12.5ms" in _render(_project(_good()), verbosity="debug")

    def test_performance_detailed(self):
        section = _section(
            _render(_project(_good(), _bad(), _broken()), verbosity="debug"), "Performance:"
        )
        assert any("Memory usage:" in line for line in section)
        assert any("Avg. file time: 500.0ms" in line for line in section)
        empty = _section(_render(_project(), verbosity="debug"), "Performance:")
        assert any("Avg. file time: 0.0ms" in line for line in empty)

    def test_configuration_info(self, fixed_now, stub_thresholds):
        out = _render(_project(_good()), verbosity="debug")
        assert "Project root: pkg" in out
        assert "Analysis timestamp: 2026-01-01T00:00:00" in out
        assert "Threshold profile: strict" in out
        assert out.index("Configuration:") < out.index("Generated by PyPex")


class TestErrorsAndUtilities:
    def test_generate_report_prints_error_and_reraises(self, monkeypatch):
        reporter = ConsoleReporter(output_stream=io.StringIO(), use_colors=False, width=WIDTH)
        monkeypatch.setattr(
            reporter.processor,
            "generate_quality_report",
            lambda r: (_ for _ in ()).throw(RuntimeError("boom")),
        )
        with pytest.raises(RuntimeError):
            reporter.generate_report(_project(_good()), verbosity="quiet")
        assert (
            f"{Icons.ERROR} Error al generar reporte de consola: boom" in reporter.output.getvalue()
        )

    @pytest.mark.parametrize(
        ("module_metrics", "entities_cc", "expected"),
        [
            ({"lines_of_code": 501}, [], ["large file"]),
            ({"lines_of_code": 500}, [], []),
            ({"cyclomatic_complexity": 51}, [], ["high complexity"]),
            ({"fan_in_out": 21}, [], ["high coupling"]),
            ({"lcom4": 6}, [], ["low cohesion"]),
            (None, [11], ["1 complex function"]),
            (None, [11, 12], ["2 complex functions"]),
            (None, [11, 11, 11, 11], ["4 complex functions"]),
            (None, [10], []),
        ],
    )
    def test_analyze_file_issues(self, module_metrics, entities_cc, expected):
        entities = [_entity(f"f{i}", cc=cc) for i, cc in enumerate(entities_cc)]
        result = _file("pkg/a.py", module_metrics=module_metrics, entities=entities)
        assert (
            ConsoleReporter(output_stream=io.StringIO(), use_colors=False)._analyze_file_issues(
                result
            )
            == expected
        )

    def test_file_complexity_summary(self):
        reporter = ConsoleReporter(output_stream=io.StringIO(), use_colors=False)
        assert reporter._get_file_complexity_summary(_good()).endswith(", avg CC: 3.0, max CC: 4")
        assert reporter._get_file_complexity_summary(_file("pkg/empty.py")) == ""
        no_cc = _file("pkg/no_cc.py", entities=[_entity("f")])
        assert reporter._get_file_complexity_summary(no_cc) == ""

    def test_file_metrics_summary_empty(self):
        reporter = ConsoleReporter(output_stream=io.StringIO(), use_colors=False)
        assert reporter._get_file_metrics_summary(_file("pkg/a.py")) == ""
        assert (
            reporter._get_file_metrics_summary(
                _file("pkg/a.py", module_metrics={"lines_of_code": 3})
            )
            == ""
        )

    def test_message_helpers(self):
        reporter = ConsoleReporter(output_stream=io.StringIO(), use_colors=False)
        for method, icon in (
            (reporter.print_success, Icons.SUCCESS),
            (reporter.print_warning, Icons.WARNING),
            (reporter.print_error, Icons.ERROR),
            (reporter.print_info, Icons.INFO),
        ):
            reporter.output = io.StringIO()
            method("m")
            assert reporter.output.getvalue() == f"{icon} m\n"

    def test_separator_and_section_header(self):
        reporter = ConsoleReporter(output_stream=io.StringIO(), use_colors=False, width=WIDTH)
        reporter.print_section_header("T", "★")
        assert reporter.output.getvalue().splitlines() == ["★ T", "─" * WIDTH]
        reporter.output = io.StringIO()
        reporter.print_separator("=")
        assert reporter.output.getvalue() == "=" * WIDTH + "\n"

    def test_quick_summary(self):
        project = _project(_good(), _file("pkg/b.py", line_count=10))
        assert (
            ConsoleReporter(output_stream=io.StringIO(), use_colors=False).quick_summary(project)
            == "demo: 2/2 files, 50 LOC, Quality: 100.0/100"
        )
