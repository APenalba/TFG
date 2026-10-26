"""Console Reporter para PyPex - Genera reportes formateados para la consola.

Este módulo proporciona un reporter optimizado para mostrar resultados del análisis
de PyPex en la consola con colores, formateo atractivo y diferentes niveles de detalle.
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import TextIO

from pypex.core.results import (
    FileAnalysisResult,
    MetricsResult,
    ProjectAnalysisResult,
)
from pypex.core.results_processor import ResultsProcessor
from pypex.services.config_service import get_config
from pypex.services.logging_service import get_logger

logger = get_logger(__name__)


class Colors:
    """Constantes para códigos de color ANSI."""

    # Colores básicos
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    GRAY = "\033[90m"

    # Colores brillantes
    BRIGHT_RED = "\033[91;1m"
    BRIGHT_GREEN = "\033[92;1m"
    BRIGHT_YELLOW = "\033[93;1m"
    BRIGHT_BLUE = "\033[94;1m"
    BRIGHT_MAGENTA = "\033[95;1m"
    BRIGHT_CYAN = "\033[96;1m"

    # Formato
    BOLD = "\033[1m"
    DIM = "\033[2m"
    UNDERLINE = "\033[4m"
    RESET = "\033[0m"

    # Fondo
    BG_RED = "\033[101m"
    BG_GREEN = "\033[102m"
    BG_YELLOW = "\033[103m"
    BG_BLUE = "\033[104m"


class Icons:
    """Iconos Unicode para diferentes elementos."""

    # Estados
    SUCCESS = "✅"
    WARNING = "⚠️"
    ERROR = "❌"
    INFO = "ℹ️"

    # Métricas
    COMPLEXITY = "🔄"
    SIZE = "📏"
    COUPLING = "🔗"
    COHESION = "🎯"
    QUALITY = "💎"

    # Elementos
    FILE = "📄"
    FOLDER = "📁"
    FUNCTION = "⚡"
    CLASS = "🏗️"
    METHOD = "🔧"

    # Análisis
    HOT_SPOT = "🔥"
    TREND_UP = "📈"
    TREND_DOWN = "📉"
    CLOCK = "⏱️"
    ROCKET = "🚀"
    TARGET = "🎯"
    CHART = "📊"
    STATS = "📈"


class ConsoleReporter:
    """Reporter para generar reportes de análisis en consola con formato avanzado.

    Esta clase genera reportes formateados para la consola con soporte para colores,
    iconos Unicode, múltiples niveles de verbosidad y presentación estructurada.

    Attributes:
        output: Stream de salida (default: sys.stdout)
        width: Ancho de la consola en caracteres
        use_colors: Si usar colores en la salida
        processor: Procesador de resultados para análisis
        config: Configuración del sistema

    Responsibilities:
        - Formateo de output para consola
        - Colorización y iconos
        - Múltiples niveles de verbosidad (quiet, normal, verbose, debug)
        - Análisis de archivos problemáticos
        - Generación de resúmenes de calidad
        - Estadísticas de rendimiento

    Note:
        Esta clase tiene múltiples responsabilidades que podrían beneficiarse
        de refactoring futuro:
        - ConsoleFormatter: Para formateo y colores
        - ReportGenerator: Para lógica de generación
        - QualityAnalyzer: Para análisis de calidad
        - PerformanceReporter: Para estadísticas de rendimiento
    """

    def __init__(
        self,
        output_stream: TextIO | None = None,
        use_colors: bool | None = None,
        width: int = 80,
    ):
        """
        Inicializa el reporter de consola.

        Args:
            output_stream: Stream de salida (default: sys.stdout)
            use_colors: Si usar colores (auto-detecta si None)
            width: Ancho de la consola en caracteres
        """
        self.output = output_stream or sys.stdout
        self.width = width
        self.processor = ResultsProcessor()
        self.config = get_config()

        # Auto-detectar soporte de colores
        if use_colors is None:
            self.use_colors = self._should_use_colors()
        else:
            self.use_colors = use_colors

    def _should_use_colors(self) -> bool:
        """Detecta si la terminal soporta colores."""
        # Desactivar colores si se redirige la salida
        if not self.output.isatty():
            return False

        # Verificar variables de entorno
        term = os.environ.get("TERM", "")
        if "color" in term or term in ["xterm", "xterm-256color", "screen"]:
            return True

        # Windows Terminal y VS Code
        if os.environ.get("WT_SESSION") or os.environ.get("VSCODE_INJECTION"):
            return True

        return False

    def colorize(self, text: str, color: str) -> str:
        """Aplica color al texto si está habilitado."""
        if not self.use_colors:
            return text
        return f"{color}{text}{Colors.RESET}"

    def generate_report(
        self,
        analysis_results: ProjectAnalysisResult,
        verbosity: str = "normal",
        show_files: bool = True,
        show_entities: bool = False,
        show_metrics: bool = False,
    ) -> None:
        """
        Genera el reporte completo en consola.

        Args:
            analysis_results: Resultados del análisis del proyecto
            verbosity: Nivel de detalle ("quiet", "normal", "verbose", "debug")
            show_files: Si mostrar información de archivos
            show_entities: Si mostrar entidades individuales
            show_metrics: Si mostrar métricas detalladas
        """
        try:
            if verbosity == "quiet":
                self._generate_quiet_report(analysis_results)
            elif verbosity == "verbose":
                self._generate_verbose_report(analysis_results, show_files, show_entities)
            elif verbosity == "debug":
                self._generate_debug_report(
                    analysis_results, show_files, show_entities, show_metrics
                )
            else:  # normal
                self._generate_normal_report(analysis_results, show_files)

        except Exception as e:
            self.print_error(f"Error al generar reporte de consola: {e}")
            raise

    def _generate_quiet_report(self, results: ProjectAnalysisResult) -> None:
        """Genera un reporte mínimo (solo estadísticas esenciales)."""
        stats = results.get_summary_stats()

        # Score de calidad si está disponible
        quality_report = self.processor.generate_quality_report(results)
        score = 0.0
        if quality_report:
            score = quality_report.get("overall_quality_score", 0.0)

        # Línea única con información esencial
        status_icon = Icons.SUCCESS if stats["success_rate"] >= 90 else Icons.WARNING
        quality_color = self._get_quality_color(score)

        self.print(
            f"{status_icon} {results.project_name}: "
            f"{stats['successful_files']}/{stats['total_files']} files, "
            f"{stats['total_lines_of_code']} LOC, "
            f"Quality: {self.colorize(f'{score:.1f}/100', quality_color)}"
        )

    def _generate_normal_report(self, results: ProjectAnalysisResult, show_files: bool) -> None:
        """Genera un reporte normal con información balanceada."""
        self._print_header(results)
        self._print_summary_stats(results)
        self._print_quality_assessment(results)
        self._print_project_overview(results)
        self._print_hot_spots(results, limit=5)

        if show_files:
            self._print_files_summary_enhanced(results)

        self._print_recommendations_summary(results)
        self._print_performance_info(results)
        self._print_footer(results)

    def _generate_verbose_report(
        self,
        results: ProjectAnalysisResult,
        show_files: bool,
        show_entities: bool,
    ) -> None:
        """Genera un reporte detallado."""
        self._print_header(results)
        self._print_summary_stats(results)
        self._print_quality_assessment(results, detailed=True)
        self._print_project_statistics(results)
        self._print_metrics_overview(results)
        self._print_hot_spots(results, limit=10)
        self._print_error_analysis(results)

        if show_files:
            self._print_files_detailed_enhanced(results, show_entities)

        self._print_recommendations(results)
        self._print_performance_info(results)
        self._print_footer(results)

    def _generate_debug_report(
        self,
        results: ProjectAnalysisResult,
        show_files: bool,
        show_entities: bool,
        show_metrics: bool,
    ) -> None:
        """Genera un reporte completo con toda la información."""
        self._print_header(results)
        self._print_summary_stats(results)
        self._print_quality_assessment(results, detailed=True)
        self._print_project_statistics(results)
        self._print_metrics_overview(results)

        if show_metrics and results.project_metrics:
            self._print_project_metrics_detailed(results.project_metrics)

        self._print_hot_spots(results, limit=15)
        self._print_error_analysis(results, detailed=True)

        if show_files:
            self._print_files_detailed_enhanced(results, show_entities, debug=True)

        self._print_recommendations(results)
        self._print_performance_info(results, detailed=True)
        self._print_configuration_info(results)
        self._print_footer(results)

    def _print_header(self, results: ProjectAnalysisResult) -> None:
        """Imprime el encabezado del reporte."""
        separator = "═" * self.width
        title = f"🔍 PyPex Analysis Report - {results.project_name}"

        self.print(self.colorize(separator, Colors.CYAN))
        self.print(self.colorize(title.center(self.width), Colors.BRIGHT_CYAN + Colors.BOLD))
        self.print(self.colorize(separator, Colors.CYAN))
        self.print()

    def _print_summary_stats(self, results: ProjectAnalysisResult) -> None:
        """Imprime estadísticas de resumen."""
        stats = results.get_summary_stats()

        self.print(self.colorize("📊 Summary:", Colors.BOLD))

        # Primera fila de estadísticas
        success_color = (
            Colors.GREEN
            if stats["success_rate"] >= 90
            else Colors.YELLOW
            if stats["success_rate"] >= 70
            else Colors.RED
        )

        self.print(
            f"   Files analyzed: {self.colorize(str(stats['total_files']), Colors.CYAN)} "
            f"| Success: {self.colorize(str(stats['successful_files']), Colors.GREEN)} "
            f"| Failed: {self.colorize(str(stats['failed_files']), Colors.RED if stats['failed_files'] > 0 else Colors.GREEN)} "
            f"| Rate: {self.colorize(f'{stats["success_rate"]:.1f}%', success_color)}"
        )

        # Segunda fila
        self.print(
            f"   Total LOC: {self.colorize(f'{stats["total_lines_of_code"]:,}', Colors.CYAN)} "
            f"| Analysis time: {self.colorize(f'{stats["analysis_time_seconds"]:,.2f}s', Colors.YELLOW)}"
        )

        self.print()

    def _print_quality_assessment(
        self, results: ProjectAnalysisResult, detailed: bool = False
    ) -> None:
        """Imprime evaluación de calidad."""
        quality_report = self.processor.generate_quality_report(results)
        advanced_quality_report = self.processor.generate_detailed_quality_report(results)

        # Usar el reporte disponible
        report = quality_report or advanced_quality_report
        if not report:
            return

        score = report.get("overall_quality_score", 0.0) or report.get("overall_score", 0.0)
        quality_level = self._get_quality_level(score)
        quality_color = self._get_quality_color(score)

        self.print(
            self.colorize(
                f"{Icons.QUALITY} Quality Score: {score:.1f}/100 ({quality_level})",
                Colors.BOLD + quality_color,
            )
        )

        if detailed and "detailed_scores" in report:
            self.print("   Breakdown:")
            for category, category_score in report["detailed_scores"].items():
                category_color = self._get_quality_color(category_score)
                self.print(
                    f"   ├─ {category.title()}: {self.colorize(f'{category_score:.1f}/100', category_color)}"
                )

        self.print()

    def _print_project_overview(self, results: ProjectAnalysisResult) -> None:
        """Imprime una vista general del proyecto (para modo normal)."""
        self.print(self.colorize(f"{Icons.CHART} Project Overview:", Colors.BOLD))

        # Estadísticas básicas de distribución
        try:
            project_report = self.processor.create_project_report(results)

            # Distribución de archivos por tamaño
            size_distribution = project_report.get("file_size_distribution", {})
            if size_distribution:
                small = size_distribution.get("small", 0)
                medium = size_distribution.get("medium", 0)
                large = size_distribution.get("large", 0)
                self.print(
                    f"   📏 File sizes: {self.colorize(str(small), Colors.GREEN)} small, "
                    f"{self.colorize(str(medium), Colors.YELLOW)} medium, "
                    f"{self.colorize(str(large), Colors.RED)} large"
                )

            # Métricas principales del proyecto
            if results.project_metrics:
                complexity_metrics = {}
                for metric_name in [
                    "cyclomatic_complexity",
                    "cognitive_complexity",
                    "lines_of_code",
                ]:
                    if metric_name in results.project_metrics.metrics:
                        value = results.project_metrics.metrics[metric_name]
                        if isinstance(value, dict):
                            complexity_metrics[metric_name] = value.get(
                                "total", value.get("sum", 0)
                            )
                        else:
                            complexity_metrics[metric_name] = value

                if complexity_metrics:
                    cc_total = complexity_metrics.get("cyclomatic_complexity", 0)
                    cog_total = complexity_metrics.get("cognitive_complexity", 0)
                    loc_total = complexity_metrics.get("lines_of_code", 0)

                    cc_color = self._get_complexity_color(cc_total / max(len(results.files), 1))
                    cog_color = self._get_complexity_color(cog_total / max(len(results.files), 1))

                    self.print(
                        f"   🔄 Total Complexity: CC {self.colorize(f'{cc_total:.0f}', cc_color)}, "
                        f"Cognitive {self.colorize(f'{cog_total:.0f}', cog_color)}"
                    )
                    self.print(
                        f"   📊 Code Volume: {self.colorize(f'{loc_total:,}', Colors.CYAN)} lines"
                    )

        except Exception as e:
            logger.debug(f"Error en project overview: {e}")

        self.print()

    def _print_project_statistics(self, results: ProjectAnalysisResult) -> None:
        """Imprime estadísticas detalladas del proyecto (para modo verbose)."""
        self.print(self.colorize(f"{Icons.STATS} Project Statistics:", Colors.BOLD))

        try:
            project_report = self.processor.create_project_report(results)

            # Distribución de archivos
            size_dist = project_report.get("file_size_distribution", {})
            if size_dist:
                self.print("   📏 File Size Distribution:")
                self.print(
                    f"      Small (<100 LOC): {self.colorize(str(size_dist.get('small', 0)), Colors.GREEN)}"
                )
                self.print(
                    f"      Medium (100-500 LOC): {self.colorize(str(size_dist.get('medium', 0)), Colors.YELLOW)}"
                )
                self.print(
                    f"      Large (>500 LOC): {self.colorize(str(size_dist.get('large', 0)), Colors.RED)}"
                )

            # Distribución de complejidad
            complexity_dist = project_report.get("complexity_distribution", {})
            if complexity_dist:
                self.print("   🔄 Complexity Distribution:")
                for level, count in complexity_dist.items():
                    color = {
                        "low": Colors.GREEN,
                        "medium": Colors.YELLOW,
                        "high": Colors.RED,
                    }.get(level, Colors.GRAY)
                    self.print(f"      {level.title()}: {self.colorize(str(count), color)}")

            # Top métricas
            if results.project_metrics:
                self.print("   📊 Key Metrics:")
                key_metrics = [
                    "cyclomatic_complexity",
                    "cognitive_complexity",
                    "lines_of_code",
                    "lcom4",
                ]
                for metric_name in key_metrics:
                    if metric_name in results.project_metrics.metrics:
                        value = results.project_metrics.metrics[metric_name]
                        if isinstance(value, dict):
                            total_val = value.get(
                                "total",
                                value.get("sum", value.get("average", 0)),
                            )
                            self.print(
                                f"      {metric_name.replace('_', ' ').title()}: {self.colorize(f'{total_val:.1f}', Colors.CYAN)}"
                            )
                        else:
                            self.print(
                                f"      {metric_name.replace('_', ' ').title()}: {self.colorize(f'{value:.1f}', Colors.CYAN)}"
                            )

        except Exception as e:
            logger.debug(f"Error en project statistics: {e}")

        self.print()

    def _print_metrics_overview(self, results: ProjectAnalysisResult) -> None:
        """Imprime resumen de métricas principales."""
        if not results.project_metrics:
            return

        self.print(self.colorize("📈 Metrics Overview:", Colors.BOLD))

        # Métricas principales para mostrar
        key_metrics = {
            "cyclomatic_complexity": (Icons.COMPLEXITY, "Complexity"),
            "cognitive_complexity": (Icons.COMPLEXITY, "Cognitive"),
            "lines_of_code": (Icons.SIZE, "Lines of Code"),
            "fan_in_out": (Icons.COUPLING, "Coupling"),
            "lcom4": (Icons.COHESION, "Cohesion"),
        }

        for metric_name, (icon, display_name) in key_metrics.items():
            if metric_name in results.project_metrics.metrics:
                value = results.project_metrics.metrics[metric_name]

                # Manejar métricas complejas (diccionarios)
                if isinstance(value, dict):
                    if "total" in value:
                        display_value = f"{value['total']:.1f}"
                        status = self._get_metric_status(metric_name, value["total"])
                    elif "sum" in value:
                        display_value = f"{value['sum']:.1f}"
                        status = self._get_metric_status(metric_name, value["sum"])
                    else:
                        display_value = "Complex"
                        status = "unknown"
                else:
                    display_value = f"{value:.1f}"
                    status = self._get_metric_status(metric_name, value)

                status_color = {
                    "good": Colors.GREEN,
                    "warning": Colors.YELLOW,
                    "critical": Colors.RED,
                }.get(status, Colors.CYAN)
                self.print(
                    f"   {icon} {display_name}: {self.colorize(display_value, status_color)}"
                )

        self.print()

    def _print_hot_spots(self, results: ProjectAnalysisResult, limit: int = 5) -> None:
        """Imprime los hot spots del código."""
        try:
            hot_spots = []

            # Obtener hot spots para diferentes métricas
            for metric_name in [
                "cyclomatic_complexity",
                "cognitive_complexity",
                "lines_of_code",
            ]:
                try:
                    entities = self.processor.get_top_entities_by_metric(
                        results,
                        metric_name,
                        limit=limit // 3 + 1,
                        entity_types=["function", "method"],
                    )

                    for entity_info in entities:
                        hot_spots.append(
                            {
                                "metric": metric_name,
                                "entity_name": entity_info["entity_name"],
                                "entity_type": entity_info["entity_type"],
                                "value": entity_info["metric_value"],
                                "file_path": entity_info.get("file_path"),
                                "line_start": entity_info.get("line_start"),
                            }
                        )
                except Exception:
                    continue

            if not hot_spots:
                return

            # Ordenar y limitar
            hot_spots.sort(key=lambda x: x["value"], reverse=True)
            hot_spots = hot_spots[:limit]

            self.print(
                self.colorize(
                    f"{Icons.HOT_SPOT} Hot Spots (Top {len(hot_spots)}):",
                    Colors.BOLD,
                )
            )

            for i, spot in enumerate(hot_spots, 1):
                metric_display = {
                    "cyclomatic_complexity": "CC",
                    "cognitive_complexity": "CogC",
                    "lines_of_code": "LOC",
                }.get(spot["metric"], spot["metric"])

                file_display = Path(spot["file_path"]).name if spot["file_path"] else "unknown"
                line_info = f":{spot['line_start']}" if spot.get("line_start") else ""

                value_color = (
                    Colors.BRIGHT_RED
                    if spot["value"] > 20
                    else Colors.RED
                    if spot["value"] > 10
                    else Colors.YELLOW
                )
                spot_value = f"{spot['value']:.0f}"
                location_info = f"📍 {file_display}{line_info}"

                self.print(
                    f"   {i}. {spot['entity_name']}() - "
                    f"{metric_display}: {self.colorize(spot_value, value_color)} "
                    f"{self.colorize(location_info, Colors.GRAY)}"
                )

            self.print()

        except Exception as e:
            logger.warning(f"Error al generar hot spots: {e}")

    def _print_files_summary_enhanced(self, results: ProjectAnalysisResult) -> None:
        """Imprime resumen de archivos mejorado con indicadores de problema."""
        if not results.files:
            return

        self.print(self.colorize("📁 Files Summary:", Colors.BOLD))

        # Categorizar archivos por estado
        successful_files = [f for f in results.files.values() if f.was_successful]
        failed_files = [f for f in results.files.values() if not f.was_successful]

        # Clasificar archivos exitosos por complejidad
        files_with_issues = []
        good_files = []

        for file_result in successful_files:
            issues = self._analyze_file_issues(file_result)
            if issues:
                files_with_issues.append((file_result, issues))
            else:
                good_files.append(file_result)

        # Mostrar archivos problemáticos primero
        if files_with_issues:
            self.print(f"   ⚠️ Files with issues ({len(files_with_issues)}):")
            for file_result, issues in files_with_issues[:3]:  # Mostrar solo los primeros 3
                issue_text = ", ".join(issues)
                self.print(
                    f"     • {self.colorize(file_result.module_name, Colors.YELLOW)} - {issue_text}"
                )

            if len(files_with_issues) > 3:
                self.print(f"     ... and {len(files_with_issues) - 3} more with issues")

        # Mostrar algunos archivos buenos
        if good_files:
            self.print(f"   ✅ Good files ({len(good_files)}):")
            for file_result in good_files[:3]:  # Mostrar solo los primeros 3
                entities_count = len(file_result.entities)
                complexity_info = self._get_file_complexity_summary(file_result)

                self.print(
                    f"     • {file_result.module_name} "
                    f"({file_result.line_count} LOC, {entities_count} entities{complexity_info})"
                )

            if len(good_files) > 3:
                self.print(f"     ... and {len(good_files) - 3} more good files")

        # Mostrar archivos fallidos
        if failed_files:
            self.print(f"   ❌ Failed files ({len(failed_files)}):")
            for file_result in failed_files:
                error_info = f" ({len(file_result.errors)} errors)" if file_result.errors else ""
                self.print(
                    f"     • {self.colorize(file_result.module_name + error_info, Colors.RED)}"
                )

        self.print()

    def _print_files_detailed_enhanced(
        self,
        results: ProjectAnalysisResult,
        show_entities: bool,
        debug: bool = False,
    ) -> None:
        """Imprime información detallada de archivos con análisis de problemas."""
        if not results.files:
            return

        self.print(self.colorize("📄 Detailed File Analysis:", Colors.BOLD))

        for file_path, file_result in results.files.items():
            # Determinar estado del archivo
            if not file_result.was_successful:
                status_icon = Icons.ERROR
                status_color = Colors.RED
            else:
                issues = self._analyze_file_issues(file_result)
                if issues:
                    status_icon = Icons.WARNING
                    status_color = Colors.YELLOW
                else:
                    status_icon = Icons.SUCCESS
                    status_color = Colors.GREEN

            file_name = Path(file_path).name

            self.print(f"   {status_icon} {self.colorize(file_name, status_color)}")
            self.print(f"      Path: {self.colorize(str(file_result.file_path), Colors.GRAY)}")
            self.print(
                f"      Size: {file_result.file_size:,} bytes | Lines: {file_result.line_count}"
            )

            if file_result.was_successful:
                # Mostrar problemas específicos si los hay
                issues = self._analyze_file_issues(file_result)
                if issues:
                    self.print(f"      Issues: {self.colorize(', '.join(issues), Colors.YELLOW)}")

                # Mostrar métricas principales del archivo
                if file_result.module_metrics:
                    complexity_summary = self._get_file_metrics_summary(file_result)
                    if complexity_summary:
                        self.print(f"      Metrics: {complexity_summary}")

                if file_result.entities and show_entities:
                    self.print(f"      Entities ({len(file_result.entities)}):")
                    for entity in file_result.entities[:3]:  # Mostrar solo las primeras 3
                        entity_icon = (
                            Icons.CLASS if entity.entity_type == "class" else Icons.FUNCTION
                        )
                        complexity = entity.metrics.get_metric_value("cyclomatic_complexity")
                        complexity_str = f" (CC: {complexity:.0f})" if complexity else ""

                        # Color basado en complejidad
                        if complexity:
                            complexity_color = self._get_complexity_color(complexity)
                            colored_complexity = self.colorize(complexity_str, complexity_color)
                        else:
                            colored_complexity = complexity_str

                        self.print(f"        {entity_icon} {entity.name}{colored_complexity}")

                    if len(file_result.entities) > 3:
                        self.print(f"        ... and {len(file_result.entities) - 3} more")
            else:
                if file_result.errors:
                    self.print("      Errors:")
                    for error in file_result.errors:
                        self.print(f"        {Icons.ERROR} {error.message}")

            if debug:
                self.print(f"      Analysis time: {file_result.analysis_time_ms:.1f}ms")

            self.print()

    def _print_error_analysis(self, results: ProjectAnalysisResult, detailed: bool = False) -> None:
        """Imprime análisis de errores."""
        all_errors = results.get_all_errors()
        if not all_errors:
            return

        self.print(self.colorize(f"⚠️ Error Analysis ({len(all_errors)} total):", Colors.BOLD))

        # Agrupar por severidad
        by_severity = {}
        for error in all_errors:
            severity = error.severity.value
            if severity not in by_severity:
                by_severity[severity] = []
            by_severity[severity].append(error)

        for severity, errors in by_severity.items():
            severity_color = {
                "critical": Colors.BRIGHT_RED,
                "error": Colors.RED,
                "warning": Colors.YELLOW,
            }.get(severity, Colors.GRAY)

            icon = {
                "critical": Icons.ERROR,
                "error": Icons.ERROR,
                "warning": Icons.WARNING,
            }.get(severity, Icons.INFO)

            self.print(
                f"   {icon} {self.colorize(f'{severity.title()}: {len(errors)}', severity_color)}"
            )

            if detailed:
                for error in errors[:3]:  # Mostrar solo los primeros 3
                    file_info = f" in {Path(error.file_path).name}" if error.file_path else ""
                    self.print(f"      • {error.message}{file_info}")

                if len(errors) > 3:
                    self.print(f"      ... and {len(errors) - 3} more")

        self.print()

    def _print_recommendations_summary(self, results: ProjectAnalysisResult) -> None:
        """Imprime un resumen de recomendaciones (para modo normal)."""
        quality_report = self.processor.generate_quality_report(results)
        advanced_quality_report = self.processor.generate_detailed_quality_report(results)

        recommendations = []
        if quality_report and "recommendations" in quality_report:
            recommendations.extend(quality_report["recommendations"])
        if advanced_quality_report and "recommendations" in advanced_quality_report:
            recommendations.extend(advanced_quality_report["recommendations"])

        # Eliminar duplicados
        unique_recommendations = list(dict.fromkeys(recommendations))

        if not unique_recommendations:
            self.print(
                self.colorize(
                    f"{Icons.SUCCESS} Excellent! No recommendations needed.",
                    Colors.GREEN + Colors.BOLD,
                )
            )
            self.print()
            return

        # Mostrar solo las top 3 en modo normal
        self.print(self.colorize("💡 Top Recommendations:", Colors.BOLD))

        for i, rec in enumerate(unique_recommendations[:3], 1):
            self.print(f"   {i}. {rec}")

        if len(unique_recommendations) > 3:
            self.print(
                f"   ... and {len(unique_recommendations) - 3} more (use --verbosity verbose for details)"
            )

        self.print()

    def _print_recommendations(self, results: ProjectAnalysisResult) -> None:
        """Imprime recomendaciones completas."""
        quality_report = self.processor.generate_quality_report(results)
        advanced_quality_report = self.processor.generate_detailed_quality_report(results)

        recommendations = []
        if quality_report and "recommendations" in quality_report:
            recommendations.extend(quality_report["recommendations"])
        if advanced_quality_report and "recommendations" in advanced_quality_report:
            recommendations.extend(advanced_quality_report["recommendations"])

        # Eliminar duplicados
        unique_recommendations = list(dict.fromkeys(recommendations))

        if not unique_recommendations:
            self.print(
                self.colorize(
                    f"{Icons.SUCCESS} Excellent! No recommendations.",
                    Colors.GREEN + Colors.BOLD,
                )
            )
            self.print()
            return

        self.print(self.colorize("💡 Recommendations:", Colors.BOLD))

        for i, rec in enumerate(unique_recommendations[:5], 1):  # Mostrar solo las primeras 5
            self.print(f"   {i}. {rec}")

        if len(unique_recommendations) > 5:
            self.print(f"   ... and {len(unique_recommendations) - 5} more")

        self.print()

    def _print_performance_info(
        self, results: ProjectAnalysisResult, detailed: bool = False
    ) -> None:
        """Imprime información de rendimiento."""
        try:
            performance_report = self.processor.create_performance_report(results)

            self.print(self.colorize(f"{Icons.ROCKET} Performance:", Colors.BOLD))

            analysis_time = results.analysis_time_ms / 1000
            files_per_second = performance_report.get("files_per_second", 0)

            self.print(
                f"   {Icons.CLOCK} Analysis time: {self.colorize(f'{analysis_time:.2f}s', Colors.CYAN)}"
            )
            self.print(
                f"   {Icons.TREND_UP} Speed: {self.colorize(f'{files_per_second:.1f} files/sec', Colors.CYAN)}"
            )

            if detailed:
                memory_usage = performance_report.get("estimated_memory_usage", "N/A")
                self.print(f"   💾 Memory usage: {self.colorize(str(memory_usage), Colors.CYAN)}")

                avg_file_time = (
                    (analysis_time / results.total_files * 1000) if results.total_files > 0 else 0
                )
                self.print(
                    f"   ⚡ Avg. file time: {self.colorize(f'{avg_file_time:.1f}ms', Colors.CYAN)}"
                )

            self.print()

        except Exception as e:
            logger.warning(f"Error al generar información de rendimiento: {e}")

    def _print_project_metrics_detailed(self, project_metrics: MetricsResult) -> None:
        """Imprime métricas de proyecto detalladas."""
        self.print(self.colorize("🔬 Project Metrics (Detailed):", Colors.BOLD))

        for metric_name, value in project_metrics.metrics.items():
            if isinstance(value, dict):
                self.print(f"   {metric_name}:")
                for component, component_value in value.items():
                    self.print(
                        f"     • {component}: {self.colorize(f'{component_value:.2f}', Colors.CYAN)}"
                    )
            else:
                self.print(f"   {metric_name}: {self.colorize(f'{value:.2f}', Colors.CYAN)}")

        self.print()

    def _print_configuration_info(self, results: ProjectAnalysisResult) -> None:
        """Imprime información de configuración (solo en modo debug)."""
        self.print(self.colorize("⚙️ Configuration:", Colors.BOLD))
        self.print(f"   Project root: {self.colorize(str(results.root_path), Colors.GRAY)}")
        self.print(
            f"   Analysis timestamp: {self.colorize(results.analysis_timestamp, Colors.GRAY)}"
        )

        # Información de thresholds si está disponible
        try:
            from pypex.metrics.thresholds import get_threshold_config

            threshold_config = get_threshold_config()
            profile = getattr(threshold_config, "_active_profile", "unknown")
            self.print(f"   Threshold profile: {self.colorize(profile, Colors.GRAY)}")
        except Exception:
            pass

        self.print()

    def _print_footer(self, results: ProjectAnalysisResult) -> None:
        """Imprime el pie del reporte."""
        separator = "═" * self.width
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        footer_text = f"Generated by PyPex © {datetime.now().year} | {timestamp}"

        self.print(self.colorize(separator, Colors.CYAN))
        self.print(self.colorize(footer_text.center(self.width), Colors.GRAY))
        self.print()

    # Métodos de utilidad y análisis

    def _analyze_file_issues(self, file_result: FileAnalysisResult) -> list[str]:
        """Analiza los problemas específicos de un archivo."""
        issues = []

        try:
            # Verificar métricas del módulo
            if file_result.module_metrics:
                # Líneas de código
                loc = file_result.module_metrics.get_metric_value("lines_of_code")
                if loc and loc > 500:
                    issues.append("large file")

                # Complejidad ciclomática total
                cc = file_result.module_metrics.get_metric_value("cyclomatic_complexity")
                if cc and cc > 50:
                    issues.append("high complexity")

                # Acoplamiento
                coupling = file_result.module_metrics.get_metric_value("fan_in_out")
                if isinstance(coupling, dict):
                    fan_out = coupling.get("fan_out", 0)
                    if fan_out > 20:
                        issues.append("high coupling")
                elif coupling and coupling > 20:
                    issues.append("high coupling")

                # LCOM4 para cohesión
                lcom4 = file_result.module_metrics.get_metric_value("lcom4")
                if lcom4 and lcom4 > 5:
                    issues.append("low cohesion")

            # Verificar entidades problemáticas
            high_complexity_entities = 0
            for entity in file_result.entities:
                entity_cc = entity.metrics.get_metric_value("cyclomatic_complexity")
                if entity_cc and entity_cc > 10:
                    high_complexity_entities += 1

            if high_complexity_entities > 3:
                issues.append(f"{high_complexity_entities} complex functions")
            elif high_complexity_entities > 0:
                issues.append(
                    f"{high_complexity_entities} complex function"
                    + ("s" if high_complexity_entities > 1 else "")
                )

        except Exception as e:
            logger.debug(f"Error analizando problemas del archivo {file_result.file_path}: {e}")

        return issues

    def _get_file_metrics_summary(self, file_result: FileAnalysisResult) -> str:
        """Obtiene un resumen de métricas del archivo."""
        if not file_result.module_metrics:
            return ""

        summary_parts = []

        try:
            # Complejidad ciclomática
            cc = file_result.module_metrics.get_metric_value("cyclomatic_complexity")
            if cc:
                cc_color = self._get_complexity_color(cc)
                summary_parts.append(f"CC: {self.colorize(f'{cc:.0f}', cc_color)}")

            # Complejidad cognitiva
            cog = file_result.module_metrics.get_metric_value("cognitive_complexity")
            if cog:
                cog_color = self._get_complexity_color(cog)
                summary_parts.append(f"Cog: {self.colorize(f'{cog:.0f}', cog_color)}")

            # Acoplamiento
            coupling = file_result.module_metrics.get_metric_value("fan_in_out")
            if isinstance(coupling, dict):
                fan_out = coupling.get("fan_out", 0)
                coupling_color = (
                    Colors.RED if fan_out > 20 else Colors.YELLOW if fan_out > 10 else Colors.GREEN
                )
                summary_parts.append(f"Coupling: {self.colorize(f'{fan_out:.0f}', coupling_color)}")

        except Exception as e:
            logger.debug(f"Error obteniendo resumen de métricas: {e}")

        return ", ".join(summary_parts) if summary_parts else ""

    def _get_complexity_color(self, complexity: float) -> str:
        """Obtiene el color apropiado para un valor de complejidad."""
        if complexity <= 5:
            return Colors.GREEN
        elif complexity <= 10:
            return Colors.YELLOW
        elif complexity <= 20:
            return Colors.RED
        else:
            return Colors.BRIGHT_RED

    def _get_metric_status(self, metric_name: str, value: float) -> str:
        """Determina el estado de una métrica basado en thresholds."""
        try:
            from pypex.metrics.thresholds import get_threshold_config

            threshold_config = get_threshold_config()
            thresholds = threshold_config.get_thresholds(metric_name)

            if value <= thresholds.get("low", 0):
                return "good"
            elif value <= thresholds.get("medium", 10):
                return "warning"
            else:
                return "critical"
        except Exception:
            # Fallback basado en valores típicos
            if metric_name in [
                "cyclomatic_complexity",
                "cognitive_complexity",
            ]:
                if value <= 5:
                    return "good"
                elif value <= 10:
                    return "warning"
                else:
                    return "critical"

            return "unknown"

    # Métodos de utilidad existentes

    def _get_quality_level(self, score: float) -> str:
        """Convierte un score numérico a nivel de calidad."""
        if score >= 80:
            return "Excellent"
        elif score >= 60:
            return "Good"
        elif score >= 40:
            return "Fair"
        elif score >= 20:
            return "Poor"
        else:
            return "Critical"

    def _get_quality_color(self, score: float) -> str:
        """Obtiene el color apropiado para un score de calidad."""
        if score >= 80:
            return Colors.BRIGHT_GREEN
        elif score >= 60:
            return Colors.GREEN
        elif score >= 40:
            return Colors.YELLOW
        elif score >= 20:
            return Colors.RED
        else:
            return Colors.BRIGHT_RED

    def _get_file_complexity_summary(self, file_result: FileAnalysisResult) -> str:
        """Obtiene un resumen de la complejidad del archivo."""
        if not file_result.entities:
            return ""

        complexities = []
        for entity in file_result.entities:
            complexity = entity.metrics.get_metric_value("cyclomatic_complexity")
            if complexity:
                complexities.append(complexity)

            # Incluir métodos
            for child in entity.children:
                child_complexity = child.metrics.get_metric_value("cyclomatic_complexity")
                if child_complexity:
                    complexities.append(child_complexity)

        if complexities:
            avg_complexity = sum(complexities) / len(complexities)
            max_complexity = max(complexities)
            return f", avg CC: {avg_complexity:.1f}, max CC: {max_complexity:.0f}"

        return ""

    # Métodos de salida

    def print(self, text: str = "") -> None:
        """Imprime texto en el stream de salida."""
        print(text, file=self.output)

    def print_success(self, message: str) -> None:
        """Imprime un mensaje de éxito."""
        self.print(f"{Icons.SUCCESS} {self.colorize(message, Colors.GREEN)}")

    def print_warning(self, message: str) -> None:
        """Imprime un mensaje de advertencia."""
        self.print(f"{Icons.WARNING} {self.colorize(message, Colors.YELLOW)}")

    def print_error(self, message: str) -> None:
        """Imprime un mensaje de error."""
        self.print(f"{Icons.ERROR} {self.colorize(message, Colors.RED)}")

    def print_info(self, message: str) -> None:
        """Imprime un mensaje informativo."""
        self.print(f"{Icons.INFO} {self.colorize(message, Colors.BLUE)}")

    # Métodos de conveniencia

    def quick_summary(self, results: ProjectAnalysisResult) -> str:
        """Genera un resumen rápido en una línea."""
        stats = results.get_summary_stats()
        quality_report = self.processor.generate_quality_report(results)
        score = quality_report.get("overall_quality_score", 0.0) if quality_report else 0.0

        return (
            f"{results.project_name}: {stats['successful_files']}/{stats['total_files']} files, "
            f"{stats['total_lines_of_code']} LOC, Quality: {score:.1f}/100"
        )

    def print_separator(self, char: str = "─", color: str = Colors.GRAY) -> None:
        """Imprime una línea separadora."""
        self.print(self.colorize(char * self.width, color))

    def print_section_header(self, title: str, icon: str = "") -> None:
        """Imprime un encabezado de sección."""
        header = f"{icon} {title}" if icon else title
        self.print(self.colorize(header, Colors.BOLD + Colors.CYAN))
        self.print_separator("─", Colors.CYAN)
