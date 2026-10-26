"""JSON Reporter para PyPex - Genera reportes estructurados en formato JSON.

Este módulo proporciona funcionalidad para exportar los resultados del análisis
de PyPex en formato JSON con diferentes niveles de detalle y configuraciones.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from pypex.core.results import (
    AnalysisError,
    EntityAnalysisResult,
    ErrorSeverity,
    FileAnalysisResult,
    MetricsResult,
    ProjectAnalysisResult,
)
from pypex.core.results_processor import ResultsProcessor
from pypex.services.config_service import get_config
from pypex.services.logging_service import get_logger

logger = get_logger(__name__)


class JSONReporter:
    """
    Generador de reportes JSON para PyPex.

    Proporciona múltiples niveles de detalle y configuraciones flexibles
    para exportar resultados de análisis en formato JSON estructurado.
    """

    def __init__(self, output_path: str = "pypex_report.json"):
        """
        Inicializa el reporter JSON.

        Args:
            output_path: Ruta donde guardar el reporte JSON
        """
        self.output_path = output_path
        self.processor = ResultsProcessor()
        self.config = get_config()

    def generate_report(
        self,
        analysis_results: ProjectAnalysisResult,
        detail_level: str = "detailed",
        include_source_code: bool = False,
        include_ast_data: bool = False,
        pretty_print: bool = True,
    ) -> None:
        """
        Genera el reporte JSON completo.

        Args:
            analysis_results: Resultados del análisis del proyecto
            detail_level: Nivel de detalle ("summary", "detailed", "full")
            include_source_code: Si incluir fragmentos de código fuente
            include_ast_data: Si incluir datos del AST (solo en nivel "full")
            pretty_print: Si formatear el JSON con indentación
        """
        try:
            # Generar el contenido JSON según el nivel de detalle
            if detail_level == "summary":
                json_data = self._generate_summary_report(analysis_results)
            elif detail_level == "detailed":
                json_data = self._generate_detailed_report(analysis_results, include_source_code)
            elif detail_level == "full":
                json_data = self._generate_full_report(
                    analysis_results, include_source_code, include_ast_data
                )
            else:
                raise ValueError(f"Nivel de detalle no válido: {detail_level}")

            # Escribir el archivo
            indent = 2 if pretty_print else None
            Path(self.output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(self.output_path, "w", encoding="utf-8") as f:
                json.dump(
                    json_data,
                    f,
                    indent=indent,
                    ensure_ascii=False,
                    default=self._json_serializer,
                )

            logger.info(
                f"Reporte JSON generado exitosamente en: {os.path.abspath(self.output_path)}"
            )

        except Exception as e:
            logger.error(f"Error al generar el reporte JSON: {e}", exc_info=True)
            raise

    def _generate_summary_report(self, results: ProjectAnalysisResult) -> dict[str, Any]:
        """
        Genera un reporte de resumen con información básica.

        Args:
            results: Resultados del análisis del proyecto

        Returns:
            Dict con información de resumen
        """
        # Generar estadísticas agregadas
        quality_report = self.processor.generate_quality_report(results)
        performance_report = self.processor.create_performance_report(results)

        # Agregar métricas principales
        main_metrics = {}
        if results.project_metrics:
            main_metrics = self._extract_key_metrics(results.project_metrics)

        # Encontrar hot spots principales
        hot_spots = self._get_top_hot_spots(results, limit=5)

        return {
            "pypex_report": {
                "version": "1.0",
                "level": "summary",
                "generated_at": datetime.now().isoformat(),
                "generator": "PyPex JSON Reporter",
            },
            "project": {
                "name": results.project_name,
                "root_path": str(results.root_path),
                "analysis_timestamp": results.analysis_timestamp,
                "summary_stats": results.get_summary_stats(),
            },
            "metrics_summary": main_metrics,
            "quality_assessment": {
                "overall_score": quality_report.get("overall_quality_score", 0.0)
                if quality_report
                else 0.0,
                "quality_level": self._get_quality_level(
                    quality_report.get("overall_quality_score", 0.0) if quality_report else 0.0
                ),
                "recommendations_count": len(quality_report.get("recommendations", []))
                if quality_report
                else 0,
            },
            "performance": {
                "analysis_time_seconds": results.analysis_time_ms / 1000,
                "files_per_second": performance_report.get("files_per_second", 0),
                "memory_usage": performance_report.get("estimated_memory_usage", "N/A"),
            },
            "hot_spots": hot_spots,
            "errors_summary": {
                "critical_errors": len(
                    [e for e in results.global_errors if e.severity == ErrorSeverity.CRITICAL]
                ),
                "total_errors": len(results.get_all_errors()),
                "files_with_errors": len([f for f in results.files.values() if f.errors]),
            },
        }

    def _generate_detailed_report(
        self, results: ProjectAnalysisResult, include_source: bool = False
    ) -> dict[str, Any]:
        """
        Genera un reporte detallado con métricas por archivo y entidad.

        Args:
            results: Resultados del análisis del proyecto
            include_source: Si incluir fragmentos de código fuente

        Returns:
            Dict con información detallada
        """
        # Obtener reportes de calidad
        quality_report = self.processor.generate_quality_report(results)
        advanced_quality_report = self.processor.generate_detailed_quality_report(results)
        performance_report = self.processor.create_performance_report(results)

        # Procesar archivos
        files_data = {}
        for file_path, file_result in results.files.items():
            files_data[file_path] = self._process_file_detailed(file_result, include_source)

        # Métricas agregadas por categoría
        aggregated_metrics = self._generate_aggregated_metrics(results)

        return {
            "pypex_report": {
                "version": "1.0",
                "level": "detailed",
                "generated_at": datetime.now().isoformat(),
                "generator": "PyPex JSON Reporter",
            },
            "project": {
                "name": results.project_name,
                "root_path": str(results.root_path),
                "analysis_timestamp": results.analysis_timestamp,
                "summary_stats": results.get_summary_stats(),
                "project_metrics": self._serialize_metrics_result(results.project_metrics)
                if results.project_metrics
                else None,
            },
            "quality_reports": {
                "basic_quality": quality_report,
                "advanced_quality": advanced_quality_report,
            },
            "metrics_aggregation": aggregated_metrics,
            "performance_analysis": performance_report,
            "files": files_data,
            "hot_spots": {
                "top_complexity": self._get_entities_by_metric(
                    results, "cyclomatic_complexity", 10
                ),
                "top_cognitive": self._get_entities_by_metric(results, "cognitive_complexity", 10),
                "large_functions": self._get_entities_by_metric(results, "lines_of_code", 10),
                "high_coupling": self._get_entities_by_metric(results, "fan_in_out", 5),
            },
            "error_analysis": self._generate_error_analysis(results),
            "recommendations": self._generate_recommendations(
                quality_report, advanced_quality_report
            ),
        }

    def _generate_full_report(
        self,
        results: ProjectAnalysisResult,
        include_source: bool = False,
        include_ast: bool = False,
    ) -> dict[str, Any]:
        """
        Genera un reporte completo con toda la información disponible.

        Args:
            results: Resultados del análisis del proyecto
            include_source: Si incluir fragmentos de código fuente
            include_ast: Si incluir datos del AST

        Returns:
            Dict con información completa
        """
        # Comenzar con el reporte detallado
        full_report = self._generate_detailed_report(results, include_source)

        # Añadir información adicional
        full_report["pypex_report"]["level"] = "full"

        # Información extendida de archivos
        for file_path, file_result in results.files.items():
            if file_path in full_report["files"]:
                full_report["files"][file_path].update(
                    {
                        "extended_metrics": self._get_extended_file_metrics(file_result),
                        "dependency_analysis": self._analyze_file_dependencies(file_result),
                        "complexity_distribution": self._get_complexity_distribution(file_result),
                    }
                )

                if include_ast and file_result.basic_ast_data:
                    full_report["files"][file_path]["ast_data"] = file_result.basic_ast_data

        # Análisis de dependencias del proyecto
        full_report["dependency_analysis"] = self._generate_dependency_analysis(results)

        # Análisis de tendencias y patrones
        full_report["pattern_analysis"] = self._generate_pattern_analysis(results)

        # Configuración utilizada
        full_report["analysis_configuration"] = {
            "config": self.config,
            "thresholds_used": self._get_thresholds_info(),
        }

        return full_report

    def _process_file_detailed(
        self, file_result: FileAnalysisResult, include_source: bool = False
    ) -> dict[str, Any]:
        """Procesa un archivo para el reporte detallado."""
        file_data = {
            "file_info": {
                "path": str(file_result.file_path),
                "module_name": file_result.module_name,
                "file_size_bytes": file_result.file_size,
                "line_count": file_result.line_count,
                "analysis_time_ms": file_result.analysis_time_ms,
                "was_successful": file_result.was_successful,
                "has_detailed_metrics": file_result.has_detailed_metrics,
            },
            "module_metrics": self._serialize_metrics_result(file_result.module_metrics)
            if file_result.module_metrics
            else None,
            "entities": [],
        }

        # Procesar entidades (funciones y clases)
        for entity in file_result.entities:
            entity_data = self._process_entity_detailed(entity, include_source)
            file_data["entities"].append(entity_data)

        # Errores del archivo
        if file_result.errors:
            file_data["errors"] = [self._serialize_error(error) for error in file_result.errors]

        # Datos básicos del AST como fallback
        if file_result.basic_ast_data:
            file_data["basic_ast_summary"] = {
                key: value
                for key, value in file_result.basic_ast_data.items()
                if key
                in [
                    "function_count",
                    "class_count",
                    "import_count",
                    "complexity_sum",
                ]
            }

        return file_data

    def _process_entity_detailed(
        self, entity: EntityAnalysisResult, include_source: bool = False
    ) -> dict[str, Any]:
        """Procesa una entidad para el reporte detallado."""
        entity_data = {
            "name": entity.name,
            "type": entity.entity_type,
            "metrics": self._serialize_metrics_result(entity.metrics),
            "source_info": entity.source_info,
        }

        # Procesar entidades hijas (métodos de clases)
        if entity.children:
            entity_data["children"] = []
            for child in entity.children:
                child_data = self._process_entity_detailed(child, include_source)
                entity_data["children"].append(child_data)

        return entity_data

    def _serialize_metrics_result(self, metrics: MetricsResult) -> dict[str, Any]:
        """Serializa un MetricsResult a un diccionario."""
        return {
            "entity_name": metrics.entity_name,
            "entity_type": metrics.entity_type,
            "metrics": metrics.metrics,
            "metadata": metrics.metadata,
            "errors": [self._serialize_error(error) for error in metrics.errors]
            if metrics.errors
            else [],
        }

    def _serialize_error(self, error: AnalysisError) -> dict[str, Any]:
        """Serializa un AnalysisError a un diccionario."""
        return {
            "message": error.message,
            "severity": error.severity.value,
            "component": error.component,
            "file_path": error.file_path,
            "line_number": error.line_number,
        }

    def _extract_key_metrics(self, project_metrics: MetricsResult) -> dict[str, Any]:
        """Extrae métricas clave del proyecto para el resumen."""
        key_metrics = {}

        # Métricas principales a incluir en el resumen
        important_metrics = [
            "cyclomatic_complexity",
            "cognitive_complexity",
            "lines_of_code",
            "fan_in_out",
            "lcom4",
            "nesting_depth",
        ]

        for metric_name in important_metrics:
            if metric_name in project_metrics.metrics:
                value = project_metrics.metrics[metric_name]
                if isinstance(value, dict):
                    # Para métricas complejas, extraer valor total o agregado
                    if "total" in value:
                        key_metrics[metric_name] = value["total"]
                    elif "sum" in value:
                        key_metrics[metric_name] = value["sum"]
                    else:
                        # Incluir el diccionario completo para métricas complejas
                        key_metrics[metric_name] = value
                else:
                    key_metrics[metric_name] = value

        return key_metrics

    def _get_top_hot_spots(
        self, results: ProjectAnalysisResult, limit: int = 5
    ) -> list[dict[str, Any]]:
        """Obtiene los hot spots principales del proyecto."""
        hot_spots = []

        # Métricas importantes para hot spots
        important_metrics = [
            "cyclomatic_complexity",
            "cognitive_complexity",
            "lines_of_code",
        ]

        for metric_name in important_metrics:
            try:
                entities = self.processor.get_top_entities_by_metric(
                    results,
                    metric_name,
                    limit=limit,
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
            except Exception as e:
                logger.warning(f"No se pudieron obtener hot spots para {metric_name}: {e}")

        # Ordenar por valor descendente y limitar
        hot_spots.sort(key=lambda x: x["value"], reverse=True)
        return hot_spots[: limit * len(important_metrics)]

    def _get_entities_by_metric(
        self, results: ProjectAnalysisResult, metric_name: str, limit: int
    ) -> list[dict[str, Any]]:
        """Obtiene entidades ordenadas por una métrica específica."""
        try:
            return self.processor.get_top_entities_by_metric(
                results,
                metric_name,
                limit=limit,
                entity_types=["function", "method", "class"],
            )
        except Exception as e:
            logger.warning(f"No se pudieron obtener entidades para métrica {metric_name}: {e}")
            return []

    def _generate_aggregated_metrics(self, results: ProjectAnalysisResult) -> dict[str, Any]:
        """Genera métricas agregadas por categoría."""
        aggregated = {
            "complexity": {},
            "size": {},
            "coupling": {},
            "cohesion": {},
        }

        # Definir métricas por categoría
        metric_categories = {
            "complexity": [
                "cyclomatic_complexity",
                "cognitive_complexity",
                "nesting_depth",
            ],
            "size": ["lines_of_code", "parameter_count"],
            "coupling": ["fan_in_out"],
            "cohesion": ["lcom4"],
        }

        for category, metrics in metric_categories.items():
            for metric_name in metrics:
                try:
                    aggregation = self.processor.aggregate_metrics(
                        results, metric_name, aggregation_type="sum"
                    )
                    aggregated[category][metric_name] = aggregation
                except Exception as e:
                    logger.warning(f"No se pudo agregar métrica {metric_name}: {e}")

        return aggregated

    def _generate_error_analysis(self, results: ProjectAnalysisResult) -> dict[str, Any]:
        """Genera un análisis detallado de errores."""
        all_errors = results.get_all_errors()

        error_analysis = {
            "total_errors": len(all_errors),
            "by_severity": {},
            "by_component": {},
            "by_file": {},
            "error_details": [],
        }

        # Análisis por severidad
        for severity in ErrorSeverity:
            count = len([e for e in all_errors if e.severity == severity])
            error_analysis["by_severity"][severity.value] = count

        # Análisis por componente
        components = {}
        for error in all_errors:
            components[error.component] = components.get(error.component, 0) + 1
        error_analysis["by_component"] = components

        # Análisis por archivo
        files = {}
        for error in all_errors:
            if error.file_path:
                files[error.file_path] = files.get(error.file_path, 0) + 1
        error_analysis["by_file"] = files

        # Detalles de errores (limitado a los más importantes)
        critical_errors = [e for e in all_errors if e.severity == ErrorSeverity.CRITICAL][:10]
        error_analysis["error_details"] = [self._serialize_error(e) for e in critical_errors]

        return error_analysis

    def _generate_recommendations(
        self,
        quality_report: dict | None,
        advanced_quality_report: dict | None,
    ) -> list[str]:
        """Genera recomendaciones basadas en los reportes de calidad."""
        recommendations = []

        if quality_report and "recommendations" in quality_report:
            recommendations.extend(quality_report["recommendations"])

        if advanced_quality_report and "recommendations" in advanced_quality_report:
            recommendations.extend(advanced_quality_report["recommendations"])

        # Eliminar duplicados manteniendo el orden
        seen = set()
        unique_recommendations = []
        for rec in recommendations:
            if rec not in seen:
                seen.add(rec)
                unique_recommendations.append(rec)

        return unique_recommendations

    def _get_extended_file_metrics(self, file_result: FileAnalysisResult) -> dict[str, Any]:
        """Obtiene métricas extendidas de un archivo."""
        metrics = {
            "entity_count": len(file_result.entities),
            "function_count": len([e for e in file_result.entities if e.entity_type == "function"]),
            "class_count": len([e for e in file_result.entities if e.entity_type == "class"]),
            "method_count": sum(
                len(e.children) for e in file_result.entities if e.entity_type == "class"
            ),
        }

        # Estadísticas de complejidad
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
            metrics["complexity_stats"] = {
                "average": sum(complexities) / len(complexities),
                "max": max(complexities),
                "min": min(complexities),
                "total": sum(complexities),
            }

        return metrics

    def _analyze_file_dependencies(self, file_result: FileAnalysisResult) -> dict[str, Any]:
        """Analiza las dependencias de un archivo."""
        # Esta información tendría que extraerse del código fuente
        # Por ahora, retornamos estructura básica
        return {
            "import_count": 0,  # Se podría extraer del AST
            "external_dependencies": [],
            "internal_dependencies": [],
        }

    def _get_complexity_distribution(self, file_result: FileAnalysisResult) -> dict[str, Any]:
        """Obtiene la distribución de complejidad en el archivo."""
        distribution = {"low": 0, "medium": 0, "high": 0, "very_high": 0}

        for entity in file_result.entities:
            complexity = entity.metrics.get_metric_value("cyclomatic_complexity")
            if complexity:
                level = self._classify_complexity(complexity)
                distribution[level] += 1

            # Incluir métodos
            for child in entity.children:
                child_complexity = child.metrics.get_metric_value("cyclomatic_complexity")
                if child_complexity:
                    level = self._classify_complexity(child_complexity)
                    distribution[level] += 1

        return distribution

    def _classify_complexity(self, value: float) -> str:
        """Clasifica un valor de complejidad en categorías."""
        if value <= 5:
            return "low"
        elif value <= 10:
            return "medium"
        elif value <= 20:
            return "high"
        else:
            return "very_high"

    def _generate_dependency_analysis(self, results: ProjectAnalysisResult) -> dict[str, Any]:
        """Genera análisis de dependencias del proyecto."""
        return {
            "module_count": results.total_files,
            "internal_dependencies": {},  # Se podría implementar análisis de imports
            "external_dependencies": [],
            "circular_dependencies": [],
        }

    def _generate_pattern_analysis(self, results: ProjectAnalysisResult) -> dict[str, Any]:
        """Genera análisis de patrones en el código."""
        patterns = {
            "large_classes": [],
            "long_methods": [],
            "god_classes": [],
            "feature_envy": [],
        }

        # Identificar clases grandes
        for file_result in results.files.values():
            if not file_result.was_successful:
                continue

            for entity in file_result.entities:
                if entity.entity_type == "class":
                    method_count = len(entity.children)
                    if method_count > 10:  # Threshold configurable
                        patterns["large_classes"].append(
                            {
                                "name": entity.name,
                                "file": str(file_result.file_path),
                                "method_count": method_count,
                            }
                        )

                # Métodos largos
                if entity.entity_type in ["function", "method"]:
                    loc = entity.metrics.get_metric_value("lines_of_code")
                    if loc and loc > 50:  # Threshold configurable
                        patterns["long_methods"].append(
                            {
                                "name": entity.name,
                                "file": str(file_result.file_path),
                                "lines_of_code": loc,
                            }
                        )

        return patterns

    def _get_thresholds_info(self) -> dict[str, Any]:
        """Obtiene información sobre los thresholds utilizados."""
        try:
            from pypex.metrics.thresholds import get_threshold_config

            threshold_config = get_threshold_config()

            # Obtener thresholds para métricas principales
            thresholds_info = {}
            main_metrics = [
                "cyclomatic_complexity",
                "cognitive_complexity",
                "lines_of_code",
            ]

            for metric_name in main_metrics:
                try:
                    thresholds = threshold_config.get_thresholds(metric_name)
                    thresholds_info[metric_name] = thresholds
                except Exception:
                    pass

            return thresholds_info
        except Exception:
            return {}

    def _get_quality_level(self, score: float) -> str:
        """Convierte un score numérico a nivel de calidad."""
        if score >= 80:
            return "excellent"
        elif score >= 60:
            return "good"
        elif score >= 40:
            return "fair"
        elif score >= 20:
            return "poor"
        else:
            return "critical"

    def _json_serializer(self, obj):
        """Serializador personalizado para objetos no serializables por defecto."""
        if isinstance(obj, Path):
            return str(obj)
        elif isinstance(obj, set):
            return list(obj)
        elif hasattr(obj, "__dict__"):
            return obj.__dict__
        else:
            return str(obj)

    # Métodos de conveniencia para generar reportes específicos

    def generate_summary(
        self,
        analysis_results: ProjectAnalysisResult,
        output_path: str | None = None,
    ) -> dict[str, Any]:
        """Genera solo un reporte de resumen y lo retorna."""
        if output_path:
            original_path = self.output_path
            self.output_path = output_path
            try:
                self.generate_report(analysis_results, detail_level="summary")
            finally:
                self.output_path = original_path

        return self._generate_summary_report(analysis_results)

    def generate_metrics_only(self, analysis_results: ProjectAnalysisResult) -> dict[str, Any]:
        """Genera un reporte que contiene solo las métricas."""
        metrics_report = {
            "pypex_report": {
                "version": "1.0",
                "level": "metrics_only",
                "generated_at": datetime.now().isoformat(),
                "generator": "PyPex JSON Reporter",
            },
            "project": {
                "name": analysis_results.project_name,
                "root_path": str(analysis_results.root_path),
            },
            "project_metrics": self._serialize_metrics_result(analysis_results.project_metrics)
            if analysis_results.project_metrics
            else None,
            "file_metrics": {},
        }

        for file_path, file_result in analysis_results.files.items():
            if file_result.was_successful and file_result.module_metrics:
                metrics_report["file_metrics"][file_path] = {
                    "module_metrics": self._serialize_metrics_result(file_result.module_metrics),
                    "entities": [
                        {
                            "name": entity.name,
                            "type": entity.entity_type,
                            "metrics": self._serialize_metrics_result(entity.metrics),
                        }
                        for entity in file_result.entities
                    ],
                }

        return metrics_report
