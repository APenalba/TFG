"""Renderizador de secciones HTML para el reporte PyPex."""

from pathlib import Path
from typing import Any

from pypex.core.results import (
    AnalysisError,
    EntityAnalysisResult,
    FileAnalysisResult,
    MetricsResult,
    ProjectAnalysisResult,
)
from pypex.metrics import MetricNotFoundError, get_registry

from .html_formatter import HTMLFormatter
from .metrics_documentation import MetricsDocumentationGenerator
from .package_organizer import PackageNode, PackageOrganizer


class HTMLRenderer:
    """Renderiza las diferentes secciones del reporte HTML."""

    def __init__(self):
        self.metric_registry = get_registry()
        self.formatter = HTMLFormatter()
        self.organizer = None  # Se establece al generar el reporte
        self.metrics_doc_generator = MetricsDocumentationGenerator()

    def set_project_root(self, project_root: str):
        """Establece la raíz del proyecto para las rutas relativas."""
        self.organizer = PackageOrganizer(project_root)

    def render_hierarchical_module_index(self, results: ProjectAnalysisResult) -> str:
        """Renderiza el índice de módulos con estructura jerárquica."""
        if not results.files:
            return "<ul><li>No hay módulos</li></ul>"

        if not self.organizer:
            self.organizer = PackageOrganizer(results.root_path)

        root = self.organizer.organize_files_hierarchically(results.files)
        return self._render_package_tree(root, is_root=True)

    def _render_package_tree(self, node: PackageNode, is_root: bool = False, depth: int = 0) -> str:
        """Renderiza un árbol de packages de forma recursiva."""
        html_parts = []

        if is_root:
            html_parts.append('<div class="package-tree">')

        # Renderizar sub-packages primero (directorios)
        for child_name, child_node in sorted(node.children.items()):
            # Aplicar padding basado en la profundidad usando CSS classes o inline styles
            indent_style = f"padding-left: {(depth + 1) * 16}px" if depth > 0 else ""

            html_parts.append(
                f"""
            <details class='package-group'>
                <summary class='package-header' style='{indent_style}'>
                    <span class='folder-content'>{child_node.name}</span>
                </summary>
                <div class="package-contents">
            """
            )
            html_parts.append(self._render_package_tree(child_node, False, depth + 1))
            html_parts.append("</div></details>")

        # Renderizar archivos en este nivel
        if node.files:
            if not is_root and not node.children:
                # Si no hay subcarpetas, usar lista simple
                html_parts.append('<ul class="module-list">')
            elif not is_root:
                # Si hay subcarpetas, separar archivos
                html_parts.append('<div class="files-in-directory"><ul class="module-list">')
            else:
                html_parts.append('<ul class="module-list">')

            # Renderizar archivos ordenados por tipo y nombre
            sorted_files = sorted(
                node.files,
                key=lambda x: (
                    0 if x[0].endswith("__init__.py") else 1,  # __init__.py primero
                    1 if x[0].startswith("test_") else 0,  # tests al final
                    x[0].lower(),  # alfabético
                ),
            )

            for rel_path, file_result in sorted_files:
                module_name = file_result.module_name
                file_id = self.formatter.safe_id(rel_path)
                file_icon = self.organizer._get_file_icon(file_result) if self.organizer else "🐍"

                # Aplicar indentación basada en la profundidad para archivos
                file_indent_style = f"padding-left: {(depth + 1) * 16 + 32}px" if depth > 0 else ""

                html_parts.append(
                    f'<li><a href="#file_{file_id}" title="{rel_path}" style="{file_indent_style}">{file_icon} {module_name}</a></li>'
                )

            if not is_root and node.children:
                html_parts.append("</ul></div>")
            else:
                html_parts.append("</ul>")

        if is_root:
            html_parts.append("</div>")

        return "".join(html_parts)

    def render_global_errors(self, errors: list[AnalysisError]) -> str:
        """Renderiza errores globales del proyecto."""
        error_items = []
        for error in errors:
            severity_class = f"error-{error.severity.value}"
            error_items.append(f'<li class="{severity_class}">{error}</li>')

        return f"""
        <div class='card error-card'>
            <h2>⚠️ Errores del Análisis</h2>
            <ul class='error-list'>
                {"".join(error_items)}
            </ul>
        </div>
        """

    def render_project_summary(
        self, results: ProjectAnalysisResult, quality_report: dict[str, Any]
    ) -> str:
        """Renderiza el resumen del proyecto."""
        summary_stats = results.get_summary_stats()

        # Determinar qué campos usar según el tipo de reporte
        if quality_report and "total_entities" in quality_report:
            # Es un quality_report básico
            total_entities = quality_report["total_entities"]
            critical_errors = quality_report.get("critical_errors", 0)
        elif quality_report and "total_entities_analyzed" in quality_report:
            # Es un advanced_quality_report
            total_entities = quality_report.get("total_entities_analyzed", 0)
            critical_errors = quality_report.get("total_problems", 0)
        else:
            # Fallback si no hay datos de calidad
            total_entities = 0
            critical_errors = 0

        return f"""
        <div class='card summary-card' id='summary'>
            <h2>📊 Resumen del Proyecto</h2>
            <div class='stats-grid'>
                <div class='stat-item'>
                    <span class='stat-label'>Nombre</span>
                    <span class='stat-value'>{results.project_name}</span>
                </div>
                <div class='stat-item'>
                    <span class='stat-label'>Archivos Totales</span>
                    <span class='stat-value'>{summary_stats["total_files"]}</span>
                </div>
                <div class='stat-item'>
                    <span class='stat-label'>Archivos Exitosos</span>
                    <span class='stat-value success'>{summary_stats["successful_files"]}</span>
                </div>
                <div class='stat-item'>
                    <span class='stat-label'>Archivos Fallidos</span>
                    <span class='stat-value error'>{summary_stats["failed_files"]}</span>
                </div>
                <div class='stat-item'>
                    <span class='stat-label'>Líneas de Código</span>
                    <span class='stat-value'>{summary_stats["total_lines_of_code"]:,}</span>
                </div>
                <div class='stat-item'>
                    <span class='stat-label'>Tasa de Éxito</span>
                    <span class='stat-value'>{summary_stats["success_rate"]:.1f}%</span>
                </div>
                <div class='stat-item'>
                    <span class='stat-label'>Entidades Totales</span>
                    <span class='stat-value'>{total_entities}</span>
                </div>
                <div class='stat-item'>
                    <span class='stat-label'>Errores Críticos</span>
                    <span class='stat-value error'>{critical_errors}</span>
                </div>
            </div>
        </div>
        """

    def render_quality_section(self, quality_report: dict[str, Any]) -> str:
        """Renderiza la sección de calidad."""
        recommendations_html = ""
        if quality_report["recommendations"]:
            rec_items = [f"<li>{rec}</li>" for rec in quality_report["recommendations"]]
            recommendations_html = f"<ul class='recommendations-list'>{''.join(rec_items)}</ul>"
        else:
            recommendations_html = (
                "<p class='no-recommendations'>¡Excelente! No hay recomendaciones.</p>"
            )

        quality_class = self.formatter.get_quality_class(quality_report["overall_quality_score"])

        # Obtener información del threshold profile
        threshold_profile = quality_report.get("threshold_profile", "normal")
        threshold_level = quality_report.get("threshold_level", "medium")

        # Determinar título y descripción según el profile
        if threshold_profile == "permissive":
            title = "🎯 Análisis de Calidad - Detección Inclusiva"
            profile_description = (
                f"Thresholds {threshold_level.upper()} (detección inclusiva de problemas)"
            )
            algorithm_description = "Algoritmo inclusivo que detecta problemas leves, moderados y serios para ayudar en la mejora continua del código."
        else:  # normal
            title = "🎯 Análisis de Calidad - Detección Balanceada"
            profile_description = f"Thresholds {threshold_level.upper()} (detección balanceada)"
            algorithm_description = "Algoritmo balanceado que detecta problemas moderados y serios, ideal para desarrollo activo."

        return f"""
        <div class='card quality-card' id='quality'>
            <h2>
                {title}
                <button class='help-button' onclick='showAnalysisHelp("basic", "{threshold_profile}")' title='¿Qué es este análisis?'>
                    <span class='help-icon'>?</span>
                </button>
            </h2>
            <div class='quality-overview'>
                <div class='quality-score-large {quality_class}'>
                    {quality_report["overall_quality_score"]:.1f}
                    <span class='score-label'>Score {threshold_profile.title()}</span>
                </div>
                <div class='quality-details'>
                    <div class='quality-item'>
                        <span class='label'>Algoritmo:</span>
                        <span class='value'>{profile_description}</span>
                    </div>
                    <div class='quality-item'>
                        <span class='label'>Entidades Analizadas:</span>
                        <span class='value'>{quality_report["total_entities"]}</span>
                    </div>
                    <div class='quality-item'>
                        <span class='label'>Archivos con Problemas:</span>
                        <span class='value'>{quality_report["files_with_issues"]}</span>
                    </div>
                    <div class='quality-item'>
                        <span class='label'>Errores Críticos:</span>
                        <span class='value error'>{quality_report["critical_errors"]}</span>
                    </div>
                </div>
            </div>

            <h3>💡 Recomendaciones</h3>
            {recommendations_html}
        </div>
        """

    def render_performance_section(self, performance_report: dict[str, Any]) -> str:
        """Renderiza la sección de rendimiento."""
        perf_data = performance_report["analysis_performance"]
        file_stats = performance_report["file_statistics"]

        return f"""
        <div class='card performance-card' id='performance'>
            <h2>⚡ Rendimiento del Análisis</h2>
            <div class='perf-grid'>
                <div class='perf-item'>
                    <span class='perf-label'>Tiempo Total</span>
                    <span class='perf-value'>{perf_data["total_analysis_time_ms"]:.0f} ms</span>
                </div>
                <div class='perf-item'>
                    <span class='perf-label'>Tiempo por Archivo</span>
                    <span class='perf-value'>{perf_data["average_time_per_file_ms"]:.1f} ms</span>
                </div>
                <div class='perf-item'>
                    <span class='perf-label'>Tasa de Éxito</span>
                    <span class='perf-value'>{perf_data["success_rate_percent"]:.1f}%</span>
                </div>
                <div class='perf-item'>
                    <span class='perf-label'>Archivo Más Grande</span>
                    <span class='perf-value'>{file_stats["largest_file_lines"]} líneas</span>
                </div>
                <div class='perf-item'>
                    <span class='perf-label'>Promedio por Archivo</span>
                    <span class='perf-value'>{file_stats["average_file_size_lines"]:.0f} líneas</span>
                </div>
                <div class='perf-item'>
                    <span class='perf-label'>Archivos con Errores</span>
                    <span class='perf-value error'>{file_stats["files_with_errors"]}</span>
                </div>
            </div>
        </div>
        """

    def render_project_metrics(self, project_metrics: MetricsResult) -> str:
        """Renderiza las métricas del proyecto."""
        if not project_metrics.metrics:
            return ""

        # Filtrar métricas para mostrar solo valores generales del proyecto
        clean_metrics = self._filter_project_metrics(project_metrics.metrics)

        if not clean_metrics:
            return ""

        metrics_rows = []
        for metric_name, metric_value in clean_metrics.items():
            tooltip = self.formatter.get_metric_tooltip(metric_name)

            # Agregar información adicional al tooltip si es una métrica del proyecto
            enhanced_tooltip = f"{tooltip} | Métrica de proyecto"

            if isinstance(metric_value, dict):
                components_html = "<ul class='metric-components'>"
                for comp_name, comp_value in metric_value.items():
                    comp_class = self.formatter.get_metric_color_class(
                        f"{metric_name}.{comp_name}", comp_value
                    )
                    # Tooltip para componentes de métricas de proyecto
                    comp_tooltip = f"Proyecto - {metric_name.replace('_', ' ').title()}: {comp_name.replace('_', ' ').title()} = {comp_value}"
                    components_html += f"<li class='{comp_class}' title='{comp_tooltip}'>{comp_name}: {comp_value}</li>"
                components_html += "</ul>"
                value_cell = components_html
            else:
                color_class = self.formatter.get_metric_color_class(metric_name, metric_value)
                value_cell = f"<span class='{color_class}'>{metric_value}</span>"

            display_name = metric_name.replace("_summary", " (Resumen)").replace("_", " ").title()
            metrics_rows.append(
                f"""
            <tr>
                <th class='tooltip' title='{enhanced_tooltip}'>{display_name}</th>
                <td>{value_cell}</td>
            </tr>
            """
            )

        return f"""
        <div class='card project-metrics-card'>
            <h2>📈 Métricas del Proyecto</h2>
            <table class='metrics-table'>
                <thead>
                    <tr>
                        <th>Métrica</th>
                        <th>Valor</th>
                    </tr>
                </thead>
                <tbody>
                    {"".join(metrics_rows)}
                </tbody>
            </table>
        </div>
        """

    def _filter_project_metrics(self, metrics: dict[str, Any]) -> dict[str, Any]:
        """Filtra métricas de proyecto para mostrar solo las relevantes."""
        filtered = {}

        # Incluir métricas que contengan estas palabras clave
        include_keywords = [
            "project",
            "total",
            "summary",
            "overall",
            "average",
        ]

        for metric_name, metric_value in metrics.items():
            metric_lower = metric_name.lower()
            if any(keyword in metric_lower for keyword in include_keywords):
                # Excluir métricas muy específicas o de debugging
                if not any(exclude in metric_lower for exclude in ["debug", "raw", "temp"]):
                    filtered[metric_name] = metric_value

        return filtered

    def render_hierarchical_modules_section(self, results: ProjectAnalysisResult) -> str:
        """Renderiza la sección de módulos con estructura jerárquica mejorada."""
        if not results.files:
            return """
            <div class='card modules-card' id='modules'>
                <h2>📁 Análisis por Módulo</h2>
                <p>No hay módulos para mostrar.</p>
            </div>
            """

        if not self.organizer:
            self.organizer = PackageOrganizer(results.root_path)

        root = self.organizer.organize_files_hierarchically(results.files)
        modules_html = self._render_package_modules(root, is_root=True)

        return f"""
        <div class='card modules-card' id='modules'>
            <h2>📁 Análisis por Módulo</h2>
            <div class='modules-hierarchy'>
                {modules_html}
            </div>
        </div>
        """

    def _render_package_modules(
        self, node: PackageNode, is_root: bool = False, depth: int = 0
    ) -> str:
        """Renderiza módulos organizados jerárquicamente."""
        html_parts = []

        # Renderizar sub-packages primero
        for child_name, child_node in sorted(node.children.items()):
            html_parts.append(
                f"""
            <div class='package-section' style='margin-left: {depth * 20}px'>
                <h3 class='package-title'>{child_node.name}</h3>
                <div class='package-modules'>
            """
            )
            html_parts.append(self._render_package_modules(child_node, False, depth + 1))
            html_parts.append("</div></div>")

        # Renderizar archivos en este nivel
        if node.files:
            for rel_path, file_result in sorted(node.files, key=lambda x: x[0]):
                html_parts.append(self.render_file_analysis(rel_path, file_result))

        return "".join(html_parts)

    def render_file_analysis(self, file_path: str, file_result: FileAnalysisResult) -> str:
        """Renderiza el análisis de un archivo individual."""
        file_id = self.formatter.safe_id(file_path)

        # Indicadores de estado
        status_class = "success" if file_result.was_successful else "error"
        file_icon = self.organizer._get_file_icon(file_result) if self.organizer else "🐍"
        error_indicator = "❌" if not file_result.was_successful else ""

        content = f"""
        <details class='file-analysis {status_class}' id='file_{file_id}'>
            <summary class='file-header {status_class}'>
                <div class="file-header-content">
                    <div class="file-info">
                        <span class="expand-arrow"></span>
                        <span class="file-icon-name">{file_icon} {file_result.module_name} {error_indicator}</span>
                        <span class='file-path' title="{file_result.file_path}">{file_path}</span>
                    </div>
                    <div class='file-stats'>
                        <span class='stat'>{file_result.line_count} líneas</span>
                        <span class='stat'>{file_result.file_size} bytes</span>
                        {'<span class="stat error-stat">Con Errores</span>' if not file_result.was_successful else ""}
                    </div>
                </div>
            </summary>
            <div class='file-content'>
        """

        # Errores si existen
        if file_result.errors:
            error_items = [f"<li>{error}</li>" for error in file_result.errors]
            content += f"""
            <div class='file-errors'>
                <h5>❌ Errores</h5>
                <ul class='error-list'>
                    {"".join(error_items)}
                </ul>
            </div>
            """

        # Métricas del módulo
        if file_result.module_metrics:
            content += self.render_entity_metrics("Módulo", file_result.module_metrics)

        # Entidades (funciones y clases)
        if file_result.entities:
            content += self.render_entities(file_result.entities)

        # Datos AST básicos si están disponibles
        if file_result.basic_ast_data and not file_result.has_detailed_metrics:
            content += self.render_basic_ast_data(file_result.basic_ast_data)

        content += """
            </div>
        </details>
        """

        return content

    def render_entities(self, entities: list[EntityAnalysisResult]) -> str:
        """Renderiza las entidades de código."""
        entities_html = []

        for entity in entities:
            # Determinar la clase de métrica para la entidad
            metric_class = self._get_metric_class_from_entity(entity)

            entities_html.append(
                f"""
            <details class='entity-container {metric_class}'>
                <summary>
                    <span class="entity-header">{entity.entity_type.title()}: {entity.name}</span>
                </summary>
                <div class='entity-content'>
                    {self.render_entity_metrics(entity.entity_type, entity.metrics)}
                    {self.render_children(entity.children)}
                </div>
            </details>
            """
            )

        return f"""
        <div class='entities-section'>
            <h5>Entidades de Código</h5>
            {"".join(entities_html)}
        </div>
        """

    def _get_metric_class_from_entity(self, entity: EntityAnalysisResult) -> str:
        """Determina la clase de métrica basada en los resultados de la entidad."""
        if not entity.metrics or not entity.metrics.metrics:
            return "metric-unknown"

        metrics = entity.metrics.metrics

        # Priorizar métricas en este orden para entidades
        priority_metrics = [
            "cognitive_complexity",
            "cyclomatic_complexity",
            "maintainability_index",
            "code_smells",
            "lines_of_code",
        ]

        for metric_name in priority_metrics:
            if metric_name in metrics:
                value = metrics[metric_name]
                if isinstance(value, (int, float)):
                    return self.formatter.get_metric_color_class(metric_name, value)

        return "metric-unknown"

    def render_children(self, children: list[EntityAnalysisResult]) -> str:
        """Renderiza entidades hijas (métodos de clase)."""
        if not children:
            return ""

        children_html = []
        for child in children:
            children_html.append(
                f"""
            <div class='child-entity'>
                <h6>{child.entity_type.title()}: {child.name}</h6>
                {self.render_entity_metrics(child.entity_type, child.metrics, is_child=True)}
            </div>
            """
            )

        return f"""
        <div class='children-section'>
            <h6>Métodos</h6>
            {"".join(children_html)}
        </div>
        """

    def render_entity_metrics(
        self, entity_type: str, metrics: MetricsResult, is_child: bool = False
    ) -> str:
        """Renderiza las métricas de una entidad con interpretaciones basadas en thresholds."""
        if not metrics.metrics:
            return "<p class='no-metrics'>No hay métricas disponibles.</p>"

        metrics_rows = []
        for metric_name, metric_value in metrics.metrics.items():
            tooltip = self.formatter.get_metric_tooltip(metric_name)
            color_class = self.formatter.get_metric_color_class(metric_name, metric_value)

            # Obtener interpretación basada en thresholds
            interpretation = self._get_metric_interpretation(metric_name, metric_value)

            # Mejorar tooltip con información adicional si está disponible
            if interpretation:
                enhanced_tooltip = f"{tooltip} | Nivel actual: {interpretation}"
            else:
                enhanced_tooltip = tooltip

            if isinstance(metric_value, dict):
                components_html = "<ul class='metric-components'>"
                for comp_name, comp_value in metric_value.items():
                    comp_class = self.formatter.get_metric_color_class(
                        f"{metric_name}.{comp_name}", comp_value
                    )
                    comp_interpretation = self._get_metric_interpretation(
                        f"{metric_name}.{comp_name}", comp_value
                    )
                    comp_badge = (
                        f"<span class='metric-badge {comp_class}'>{comp_interpretation}</span>"
                        if comp_interpretation
                        else ""
                    )
                    # Tooltip para componentes individuales
                    comp_tooltip = f"{metric_name.replace('_', ' ').title()} - {comp_name.replace('_', ' ').title()}: {comp_value}"
                    components_html += f"<li class='{comp_class}' title='{comp_tooltip}'>{comp_name}: {comp_value} {comp_badge}</li>"
                components_html += "</ul>"
                value_cell = components_html
            else:
                interpretation_badge = (
                    f"<span class='metric-badge {color_class}'>{interpretation}</span>"
                    if interpretation
                    else ""
                )
                value_cell = (
                    f"<span class='{color_class}'>{metric_value}</span> {interpretation_badge}"
                )

            # Formatear nombre de métrica de forma más legible
            display_name = metric_name.replace("_", " ").title()

            metrics_rows.append(
                f"""
            <tr>
                <td class='tooltip metric-name' title='{enhanced_tooltip}'>{display_name}</td>
                <td class='metric-value'>{value_cell}</td>
            </tr>
            """
            )

        table_class = "child-metrics-table" if is_child else "entity-metrics-table"

        return f"""
        <table class='metrics-table {table_class}'>
            <tbody>
                {"".join(metrics_rows)}
            </tbody>
        </table>
        """

    def _get_metric_interpretation(self, metric_name: str, value: any) -> str:
        """Obtiene la interpretación de una métrica basada en thresholds."""
        try:
            if not isinstance(value, (int, float)):
                return ""

            base_metric = metric_name.split(".")[0]
            metric = self.metric_registry.get_metric(base_metric)
            return metric.interpret(float(value))
        except (MetricNotFoundError, Exception):
            return ""

    def render_basic_ast_data(self, ast_data: dict[str, Any]) -> str:
        """Renderiza datos AST básicos como fallback."""
        if not ast_data:
            return ""

        data_rows = []
        for key, value in ast_data.items():
            data_rows.append(
                f"""
            <tr>
                <td>{key}</td>
                <td>{value}</td>
            </tr>
            """
            )

        return f"""
        <div class='basic-ast-section'>
            <h5>Métricas AST Básicas</h5>
            <table class='basic-ast-table'>
                <tbody>
                    {"".join(data_rows)}
                </tbody>
            </table>
        </div>
        """

    def render_advanced_quality_section(self, advanced_report: dict[str, Any]) -> str:
        """Renderiza la sección de análisis avanzado de calidad."""
        overall_score = advanced_report.get("overall_score", 0)
        quality_class = self.formatter.get_quality_class(overall_score)

        metrics_analysis_html = ""
        if advanced_report.get("metrics_analysis"):
            # Ordenar métricas por complejidad alta (descendente), luego por complejidad media (descendente)
            sorted_metrics = sorted(
                advanced_report["metrics_analysis"].items(),
                key=lambda x: (
                    x[1].get("high_complexity_entities", 0),
                    x[1].get("medium_complexity_entities", 0),
                ),
                reverse=True,
            )

            analysis_items = []
            metrics_with_problems = 0

            for metric_name, analysis in sorted_metrics:
                # Contar métricas con problemas para estadísticas
                high_count = analysis.get("high_complexity_entities", 0)
                medium_count = analysis.get("medium_complexity_entities", 0)

                if high_count > 0 or medium_count > 0:
                    metrics_with_problems += 1
                    analysis_items.append(self._render_metric_analysis(metric_name, analysis))
                elif isinstance(analysis, dict) and not analysis.get("error"):
                    # También mostrar métricas sin problemas pero que se analizaron correctamente
                    # Solo si no hay muchas métricas con problemas
                    if (
                        len(
                            [
                                m
                                for m, a in sorted_metrics
                                if a.get("high_complexity_entities", 0) > 0
                                or a.get("medium_complexity_entities", 0) > 0
                            ]
                        )
                        < 5
                    ):
                        analysis_items.append(self._render_metric_analysis(metric_name, analysis))

            if analysis_items:
                metrics_analysis_html = f"""
                <div class='metrics-analysis-grid'>
                    {"".join(analysis_items)}
                </div>
                """

        recommendations_html = ""
        if advanced_report.get("recommendations"):
            rec_items = [f"<li>{rec}</li>" for rec in advanced_report["recommendations"]]
            recommendations_html = f"""
            <div class='advanced-recommendations-list'>
                <h4>💡 Recomendaciones Críticas</h4>
                <ul>{"".join(rec_items)}</ul>
            </div>
            """

        # Contar métricas analizadas (no solo las problemáticas)
        total_metrics_analyzed = len(
            [
                m
                for m, a in advanced_report.get("metrics_analysis", {}).items()
                if isinstance(a, dict) and not a.get("error")
            ]
        )

        return f"""
        <div class='card advanced-quality-card' id='advanced-quality'>
            <h2>
                🔍 Análisis Avanzado de Calidad - Detección Crítica
                <button class='help-button help-button-light' onclick='showAnalysisHelp("advanced")' title='¿Qué es este análisis?'>
                    <span class='help-icon'>?</span>
                </button>
            </h2>
            <div class='advanced-quality-overview'>
                <div class='quality-score-large {quality_class}'>
                    {overall_score:.1f}
                    <span class='score-label'>Score Crítico</span>
                </div>
                <div class='advanced-quality-details'>
                    <div class='quality-item quality-item-light'>
                        <span class='label'>Algoritmo:</span>
                        <span class='value'>Thresholds HIGH (ponderación 3x)</span>
                    </div>
                    <div class='quality-item quality-item-light'>
                        <span class='label'>Entidades Analizadas:</span>
                        <span class='value'>{advanced_report.get("total_entities_analyzed", 0)}</span>
                    </div>
                    <div class='quality-item quality-item-light'>
                        <span class='label'>Métricas Evaluadas:</span>
                        <span class='value'>{total_metrics_analyzed}</span>
                    </div>
                    <div class='quality-item quality-item-light'>
                        <span class='label'>Problemas Críticos:</span>
                        <span class='value error'>{advanced_report.get("total_problems", 0)}</span>
                    </div>
                </div>
            </div>

            <h3>📊 Análisis Detallado por Métrica</h3>
            {metrics_analysis_html}

            {recommendations_html}
        </div>
        """

    def _render_metric_analysis(self, metric_name: str, analysis: dict[str, Any]) -> str:
        """Renderiza el análisis de una métrica específica."""
        metric_display_name = metric_name.replace("_", " ").title()

        top_problematic_html = ""
        if analysis.get("top_problematic"):
            rows = []
            for item in analysis["top_problematic"][:5]:  # Top 5
                # Obtener el nombre del archivo correctamente
                file_path = item.get("file", "")
                if file_path and file_path != "N/A":
                    # Si es una ruta completa, obtener solo el nombre del archivo
                    file_name = Path(file_path).name
                    # Mostrar tanto el nombre como un tooltip con la ruta completa
                    file_display = f'<span title="{file_path}">{file_name}</span>'
                else:
                    file_display = "N/A"

                rows.append(
                    f"""
                <tr>
                    <td><code>{item.get("entity", "N/A")}</code></td>
                    <td>{item.get("type", "N/A")}</td>
                    <td>{file_display}</td>
                    <td class='metric-value'>{item.get("value", "N/A")}</td>
                </tr>
                """
                )

            top_problematic_html = (
                f"""
            <div class='table-container'>
                <table class='top-problematic-table'>
                    <thead>
                        <tr><th>Entidad</th><th>Tipo</th><th>Archivo</th><th>Valor</th></tr>
                    </thead>
                    <tbody>
                        {"".join(rows)}
                    </tbody>
                </table>
            </div>
            """
                if rows
                else "<p class='no-problems'>No hay problemas detectados</p>"
            )

        return f"""
        <div class='metric-analysis-card'>
            <h4>📈 {metric_display_name}</h4>
            <div class='metric-stats'>
                <div class='stat-item'>
                    <span class='stat-label'>Alta Complejidad:</span>
                    <span class='stat-value error'>{analysis.get("high_complexity_entities", 0)}</span>
                </div>
                <div class='stat-item'>
                    <span class='stat-label'>Complejidad Media:</span>
                    <span class='stat-value warning'>{analysis.get("medium_complexity_entities", 0)}</span>
                </div>
            </div>

            <h5>🎯 Top Entidades Problemáticas</h5>
            {top_problematic_html}
        </div>
        """

    def render_metrics_documentation(self) -> str:
        """Renderiza la documentación completa de métricas."""
        return self.metrics_doc_generator.generate_metrics_documentation()
