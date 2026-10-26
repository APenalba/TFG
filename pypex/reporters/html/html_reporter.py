"""HTML Reporter modular que usa componentes especializados para generar reportes jerárquicos."""

import os
from datetime import datetime
from typing import Any

from pypex.core.results import ProjectAnalysisResult
from pypex.core.results_processor import ResultsProcessor
from pypex.services.config_service import get_config
from pypex.services.logging_service import get_logger

from .html_renderer import HTMLRenderer
from .html_scripts import HTMLScripts
from .html_styles import HTMLStyles
from .package_organizer import PackageOrganizer

logger = get_logger(__name__)


class HTMLReporter:
    """
    Generador de reportes HTML modular con estructura jerárquica mejorada.

    Esta clase orquesta los diferentes componentes especializados para generar
    un reporte HTML completo y bien estructurado.
    """

    def __init__(self, output_path: str = "reporte_pypex.html"):
        """
        Inicializa el reporter HTML.

        Args:
            output_path: Ruta donde guardar el reporte HTML
        """
        self.output_path = output_path
        self.processor = ResultsProcessor()
        self.renderer = HTMLRenderer()
        self.organizer = None  # Se establece al generar el reporte
        self.config = get_config()

    def generate_report(self, analysis_results: ProjectAnalysisResult) -> None:
        """
        Genera el reporte HTML completo usando ProjectAnalysisResult.

        Args:
            analysis_results: Resultados del análisis del proyecto
        """
        try:
            # Configurar componentes con la raíz del proyecto
            self.renderer.set_project_root(analysis_results.root_path)
            self.organizer = PackageOrganizer(analysis_results.root_path)

            # Generar el contenido HTML
            html_content = self._build_complete_html(analysis_results)

            # Escribir el archivo
            with open(self.output_path, "w", encoding="utf-8") as f:
                f.write(html_content)

            logger.debug(
                f"Reporte HTML generado exitosamente en: {os.path.abspath(self.output_path)}"
            )

        except OSError as e:
            logger.error(
                f"Error al escribir el reporte HTML en {self.output_path}: {e}",
                exc_info=True,
            )
        except Exception as e:
            logger.error(
                f"Error inesperado al generar el reporte HTML: {e}",
                exc_info=True,
            )

    def _build_complete_html(self, results: ProjectAnalysisResult) -> str:
        """
        Construye el contenido HTML completo del reporte.

        Args:
            results: Resultados del análisis del proyecto

        Returns:
            Contenido HTML completo como string
        """
        # Generar reportes usando el processor (que ya usa la configuración)
        quality_report = self.processor.generate_quality_report(results)
        advanced_quality_report = self.processor.generate_detailed_quality_report(results)
        performance_report = self.processor.create_performance_report(results)

        # Construir índice de módulos con estructura jerárquica
        module_links_html = self.renderer.render_hierarchical_module_index(results)

        # Construir contenido principal del cuerpo
        analysis_content = self._build_analysis_content(
            results,
            quality_report,
            advanced_quality_report,
            performance_report,
        )

        # Construir el sidebar con tabs
        sidebar_content = self._build_vscode_sidebar(
            results, module_links_html, quality_report, advanced_quality_report
        )

        # Determinar score para el header
        header_score = self._get_header_score(quality_report, advanced_quality_report)

        # Ensamblar HTML completo
        return f"""
<!DOCTYPE html>
<html lang='es'>
<head>
    <meta charset='UTF-8'>
    <meta name='viewport' content='width=device-width, initial-scale=1.0'>
    <title>Reporte PyPex - {results.project_name}</title>
    {HTMLStyles.get_styles()}
</head>
<body>
    <div class='container'>
        <header>
            <h1>📊 Reporte de Análisis Estático PyPex</h1>
            <div class='quality-badge'>
                <span class='quality-score {self._get_quality_class(header_score)}'>
                    Score: {header_score:.1f}/100
                </span>
            </div>
        </header>

        {sidebar_content}

        <main class='content'>
            <!-- Contenido del Análisis del Proyecto -->
            <div class='main-content-panel active' id='content-analysis'>
                {analysis_content}
            </div>

            <!-- Contenido de Documentación de Métricas -->
            <div class='main-content-panel' id='content-metrics-docs'>
                {self.renderer.render_metrics_documentation()}
            </div>
        </main>

        <footer>
            <p>Generado por <strong>PyPex</strong> &copy; {datetime.now().year}</p>
            <p>📅 {results.analysis_timestamp} | ⌨️ Presiona <kbd>?</kbd> para ver atajos</p>
        </footer>
    </div>
    {HTMLScripts.get_scripts()}
</body>
</html>
"""

    def _get_header_score(self, quality_report, advanced_quality_report):
        """Obtiene el score apropiado para mostrar en el header."""
        if quality_report:
            return quality_report["overall_quality_score"]
        elif advanced_quality_report:
            return advanced_quality_report["overall_score"]
        return 0.0

    def _build_body_content(
        self,
        results: ProjectAnalysisResult,
        quality_report: dict[str, Any],
        advanced_quality_report: dict[str, Any],
        performance_report: dict[str, Any],
    ) -> str:
        """
        Construye el contenido principal del cuerpo del reporte.

        Args:
            results: Resultados del análisis
            quality_report: Reporte de calidad básico (puede ser None)
            advanced_quality_report: Reporte de calidad avanzado (puede ser None)
            performance_report: Reporte de rendimiento

        Returns:
            HTML del contenido del cuerpo
        """
        content_sections = []

        # Errores globales si existen
        if results.global_errors:
            content_sections.append(self.renderer.render_global_errors(results.global_errors))

        # Resumen del proyecto (usar el reporte disponible)
        summary_report = quality_report or advanced_quality_report
        if summary_report:
            content_sections.append(self.renderer.render_project_summary(results, summary_report))

        # Renderizar análisis según disponibilidad
        if quality_report:
            content_sections.append(self.renderer.render_quality_section(quality_report))

        if advanced_quality_report:
            content_sections.append(
                self.renderer.render_advanced_quality_section(advanced_quality_report)
            )

        # Reporte de rendimiento
        content_sections.append(self.renderer.render_performance_section(performance_report))

        # Métricas de proyecto si están disponibles
        if results.project_metrics:
            content_sections.append(self.renderer.render_project_metrics(results.project_metrics))

        # Análisis detallado de módulos con estructura jerárquica
        content_sections.append(self.renderer.render_hierarchical_modules_section(results))

        return "\n".join(content_sections)

    def _build_analysis_content(
        self,
        results: ProjectAnalysisResult,
        quality_report: dict[str, Any],
        advanced_quality_report: dict[str, Any],
        performance_report: dict[str, Any],
    ) -> str:
        """
        Construye el contenido de análisis del proyecto (original body_content).

        Args:
            results: Resultados del análisis
            quality_report: Reporte de calidad básico (puede ser None)
            advanced_quality_report: Reporte de calidad avanzado (puede ser None)
            performance_report: Reporte de rendimiento

        Returns:
            HTML del contenido de análisis
        """
        content_sections = []

        # Errores globales si existen
        if results.global_errors:
            content_sections.append(self.renderer.render_global_errors(results.global_errors))

        # Resumen del proyecto (usar el reporte disponible)
        summary_report = quality_report or advanced_quality_report
        if summary_report:
            content_sections.append(self.renderer.render_project_summary(results, summary_report))

        # Renderizar análisis según disponibilidad
        if quality_report:
            content_sections.append(self.renderer.render_quality_section(quality_report))

        if advanced_quality_report:
            content_sections.append(
                self.renderer.render_advanced_quality_section(advanced_quality_report)
            )

        # Reporte de rendimiento
        content_sections.append(self.renderer.render_performance_section(performance_report))

        # Métricas de proyecto si están disponibles
        if results.project_metrics:
            content_sections.append(self.renderer.render_project_metrics(results.project_metrics))

        # Análisis detallado de módulos con estructura jerárquica
        content_sections.append(self.renderer.render_hierarchical_modules_section(results))

        return "\n".join(content_sections)

    def _build_vscode_sidebar(
        self,
        results: ProjectAnalysisResult,
        module_links_html: str,
        quality_report,
        advanced_quality_report,
    ) -> str:
        """
        Construye el sidebar estilo VSCode con tabs que controlan el contenido principal.

        Args:
            results: Resultados del análisis
            module_links_html: HTML del índice de módulos
            quality_report: Reporte de calidad básico (puede ser None)
            advanced_quality_report: Reporte de calidad avanzado (puede ser None)

        Returns:
            HTML del sidebar con tabs
        """
        # Construir enlaces de navegación según qué análisis están disponibles
        analysis_links = ['<li><a href="#summary">📊 Resumen del Proyecto</a></li>']

        if quality_report:
            analysis_links.append('<li><a href="#quality">🎯 Análisis de Calidad</a></li>')

        if advanced_quality_report:
            analysis_links.append('<li><a href="#advanced-quality">🔍 Análisis Avanzado</a></li>')

        analysis_links.extend(
            [
                '<li><a href="#performance">⚡ Rendimiento</a></li>',
                '<li><a href="#modules">📁 Análisis por Módulo</a></li>',
            ]
        )

        return f"""
        <nav class='sidebar'>
            <div class='sidebar-header'>
                <div class='sidebar-tabs'>
                    <button class='sidebar-tab active' data-panel='explorer' data-content='analysis'>
                        <div class='sidebar-tab-icon'>📁</div>
                        <div class='sidebar-tab-label'>Explorer</div>
                    </button>
                    <button class='sidebar-tab' data-panel='navigation' data-content='analysis'>
                        <div class='sidebar-tab-icon'>🧭</div>
                        <div class='sidebar-tab-label'>Navigate</div>
                    </button>
                    <button class='sidebar-tab' data-panel='metrics-docs' data-content='metrics-docs'>
                        <div class='sidebar-tab-icon'>📚</div>
                        <div class='sidebar-tab-label'>Métricas</div>
                    </button>
                </div>
            </div>

            <div class='sidebar-content'>
                <!-- Explorer Panel with integrated search -->
                <div class='sidebar-panel explorer-panel active'>
                    <div class='explorer-header'>
                        <div class='explorer-title'>Estructura del Proyecto</div>
                        <div class='search-container'>
                            <input type='text'
                                   id='module-search'
                                   placeholder='Buscar módulos, clases, funciones...'
                                   autocomplete='off'>
                        </div>
                    </div>
                    <div class='explorer-content'>
                        {module_links_html}
                    </div>
                </div>

                <!-- Navigation Panel -->
                <div class='sidebar-panel nav-panel'>
                    <div class='explorer-title'>Navegación del Análisis</div>
                    <ul class='nav-list analysis-nav'>
                        {"".join(analysis_links)}
                    </ul>

                    {self._build_quick_stats(results)}
                </div>

                <!-- Metrics Documentation Panel -->
                <div class='sidebar-panel metrics-docs-panel'>
                    <div class='explorer-header'>
                        <div class='explorer-title'>Documentación de Métricas</div>
                    </div>
                    <div class='explorer-content'>
                        <div class='metrics-sidebar-info'>
                            <p>Explora información detallada sobre cada métrica implementada en PyPex:</p>
                            <ul>
                                <li>💡 Fundamentación teórica</li>
                                <li>🔢 Cálculo y algoritmo</li>
                                <li>🎯 Umbrales de interpretación</li>
                                <li>📝 Ejemplos prácticos</li>
                            </ul>
                            <div class='metrics-sidebar-status'>
                                <div class='sidebar-status-info'>
                                    <strong>Actualmente viendo:</strong><br>
                                    <span class='current-view-text'>Documentación completa de métricas</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </nav>
        """

    def _build_quick_stats(self, results: ProjectAnalysisResult) -> str:
        """
        Construye estadísticas rápidas para el panel de navegación.

        Args:
            results: Resultados del análisis

        Returns:
            HTML de estadísticas rápidas
        """
        summary_stats = results.get_summary_stats()

        return f"""
        <div style='margin-top: 1rem; padding-top: 1rem; border-top: 1px solid var(--vscode-border);'>
            <div class='explorer-title'>Estadísticas Rápidas</div>
            <div style='font-size: 12px; color: var(--vscode-text-muted); line-height: 1.4;'>
                <div style='margin: 4px 0; display: flex; justify-content: space-between;'>
                    <span>Archivos:</span>
                    <span style='color: var(--vscode-text);'>{summary_stats["total_files"]}</span>
                </div>
                <div style='margin: 4px 0; display: flex; justify-content: space-between;'>
                    <span>Exitosos:</span>
                    <span style='color: var(--success-color);'>{summary_stats["successful_files"]}</span>
                </div>
                <div style='margin: 4px 0; display: flex; justify-content: space-between;'>
                    <span>Con errores:</span>
                    <span style='color: var(--error-color);'>{summary_stats["failed_files"]}</span>
                </div>
                <div style='margin: 4px 0; display: flex; justify-content: space-between;'>
                    <span>Líneas:</span>
                    <span style='color: var(--vscode-text);'>{summary_stats["total_lines_of_code"]:,}</span>
                </div>
                <div style='margin: 4px 0; display: flex; justify-content: space-between;'>
                    <span>Tasa éxito:</span>
                    <span style='color: var(--vscode-text);'>{summary_stats["success_rate"]:.1f}%</span>
                </div>
            </div>
        </div>
        """

    def _get_quality_class(self, score: float) -> str:
        """
        Obtiene la clase CSS para el score de calidad.

        Args:
            score: Score de calidad (0-100)

        Returns:
            Nombre de la clase CSS correspondiente
        """
        if score >= 80:
            return "quality-excellent"
        elif score >= 60:
            return "quality-good"
        elif score >= 40:
            return "quality-fair"
        else:
            return "quality-poor"

    def get_package_statistics(self, results: ProjectAnalysisResult) -> dict[str, Any]:
        """
        Obtiene estadísticas de la estructura de packages del proyecto.

        Args:
            results: Resultados del análisis del proyecto

        Returns:
            Diccionario con estadísticas de packages
        """
        if not self.organizer:
            self.organizer = PackageOrganizer(results.root_path)

        root = self.organizer.organize_files_hierarchically(results.files)
        return self.organizer.get_package_statistics(root)
