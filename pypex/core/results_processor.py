"""Procesador avanzado para análisis y agregación de resultados de análisis PyPex.

Este módulo implementa funcionalidades avanzadas para procesamiento de resultados
de análisis de código, incluyendo agregación de métricas, detección de problemas,
generación de reportes de calidad y recomendaciones automáticas.

Classes:
    ResultsProcessor: Procesador principal para análisis de resultados

Note:
    Es independiente del motor de métricas específico y utiliza umbrales
    configurables para identificar entidades problemáticas y generar reportes.
"""

from pathlib import Path
from typing import Any

from pypex.core.results import (
    EntityAnalysisResult,
    ErrorSeverity,
    ProjectAnalysisResult,
)
from pypex.metrics.thresholds import get_threshold_config
from pypex.services.config_service import get_config
from pypex.services.logging_service import get_logger

logger = get_logger(__name__)


class ResultsProcessor:
    """Procesador avanzado para agregación y análisis de resultados de análisis.

    Esta clase proporciona funcionalidades completas para procesar y analizar
    los resultados de análisis de código, incluyendo agregación de métricas,
    identificación de problemas y generación de reportes detallados.

    El procesador utiliza umbrales configurables para clasificar entidades
    como problemáticas y generar recomendaciones automáticas para mejoras.
    También calcula puntuaciones de calidad y genera estadísticas de rendimiento.

    Attributes:
        aggregation_functions: Diccionario de funciones de agregación disponibles
        config: Configuración del sistema cargada

    Example:
        >>> processor = ResultsProcessor()
        >>> metrics = processor.aggregate_metrics(
        ...     results, "cyclomatic_complexity", "avg"
        ... )
        >>> report = processor.generate_quality_report(results)
        >>> print(f"Puntuación de calidad: {report['quality_score']}")
    """

    def __init__(self):
        self.aggregation_functions = {
            "sum": lambda values: sum(values),
            "avg": lambda values: sum(values) / len(values) if values else 0,
            "max": lambda values: max(values) if values else 0,
            "min": lambda values: min(values) if values else 0,
            "count": lambda values: len(values),
        }
        self.config = get_config()

        logger.debug(
            f"ResultsProcessor inicializado con {len(self.aggregation_functions)} funciones de agregación"
        )
        logger.debug(
            f"Configuración cargada: threshold_profile={self.config.get('thresholds_profile', 'normal')}"
        )

    def aggregate_metrics(
        self,
        results: ProjectAnalysisResult,
        metric_name: str,
        aggregation_type: str = "sum",
        entity_types: list[str] | None = None,
    ) -> dict[str, float]:
        """Agrega métricas a través de entidades del proyecto."""

        logger.debug(f"Agregando métricas '{metric_name}' usando tipo '{aggregation_type}'")

        if aggregation_type not in self.aggregation_functions:
            logger.error(f"Tipo de agregación no soportado: {aggregation_type}")
            raise ValueError(f"Tipo de agregación no soportado: {aggregation_type}")

        entity_types = entity_types or ["function", "class", "method"]
        aggregation_func = self.aggregation_functions[aggregation_type]

        collected_values = []
        file_aggregations = {}
        files_processed = 0
        files_with_data = 0

        for file_path, file_result in results.files.items():
            files_processed += 1
            if not file_result.was_successful:
                logger.debug(f"Saltando archivo fallido: {file_path}")
                continue

            file_values = []

            for entity in file_result.entities:
                if entity.entity_type in entity_types:
                    value = entity.metrics.get_metric_value(metric_name)
                    if value is not None:
                        file_values.append(value)
                        collected_values.append(value)

                for child in entity.children:
                    if child.entity_type in entity_types:
                        value = child.metrics.get_metric_value(metric_name)
                        if value is not None:
                            file_values.append(value)
                            collected_values.append(value)

            if file_values:
                file_aggregations[file_path] = aggregation_func(file_values)
                files_with_data += 1

        logger.debug(
            f"Agregación completada: {files_processed} archivos procesados, {files_with_data} con datos, {len(collected_values)} valores recolectados"
        )

        return {
            "project_total": (aggregation_func(collected_values) if collected_values else 0),
            "files_count": len(file_aggregations),
            "average_per_file": (
                sum(file_aggregations.values()) / len(file_aggregations) if file_aggregations else 0
            ),
            **{f"file_{Path(fp).stem}": val for fp, val in file_aggregations.items()},
        }

    def find_problematic_entities(
        self, results: ProjectAnalysisResult, thresholds: dict[str, float]
    ) -> dict[str, list[EntityAnalysisResult]]:
        """Encuentra entidades que superan umbrales específicos."""

        problematic = {metric: [] for metric in thresholds.keys()}

        for file_result in results.files.values():
            if not file_result.was_successful:
                continue

            for entity in file_result.entities:
                self._check_entity_thresholds(entity, thresholds, problematic)

                for child in entity.children:
                    self._check_entity_thresholds(child, thresholds, problematic)

        return problematic

    def _check_entity_thresholds(
        self,
        entity: EntityAnalysisResult,
        thresholds: dict[str, float],
        problematic: dict[str, list[EntityAnalysisResult]],
    ) -> None:
        """Verifica si una entidad supera los umbrales."""
        from pypex.metrics import get_registry

        registry = get_registry()

        for metric_name, threshold in thresholds.items():
            # Intentar obtener valor simple primero
            value = entity.metrics.get_metric_value(metric_name)

            # Si el valor es un diccionario complejo, usar valor agregado
            if value is None or isinstance(value, dict):
                try:
                    # Lanza una excepción si la métrica no existe
                    registry.get_metric(metric_name)
                    # Necesitaríamos la entidad original para calcular valor agregado
                    # Por ahora, extraer valor total si existe
                    if isinstance(value, dict):
                        # Buscar valores agregados en el diccionario
                        aggregated_value = None
                        for key in ["total", "sum", "aggregate", "value"]:
                            if key in value:
                                aggregated_value = value[key]
                                break

                        if aggregated_value is None:
                            # Sumar valores numéricos
                            numeric_values = [
                                v for v in value.values() if isinstance(v, (int, float))
                            ]
                            aggregated_value = sum(numeric_values) if numeric_values else 0

                        value = aggregated_value
                except Exception:
                    continue  # Skip si no se puede obtener la métrica

            if value is not None and isinstance(value, (int, float)) and value > threshold:
                problematic[metric_name].append(entity)

    def _get_all_registered_metrics(self) -> list[str]:
        """Obtiene dinámicamente todas las métricas registradas."""
        from pypex.metrics import get_registry

        try:
            registry = get_registry()
            return registry.get_available_metrics()
        except Exception:
            # Fallback a métricas conocidas si hay problemas
            return [
                "cyclomatic_complexity",
                "cognitive_complexity",
                "fan_in_out",
                "lcom4",
                "nesting_depth",
            ]

    def _get_quality_metrics_config(self, threshold_level: str = "medium") -> dict[str, float]:
        """Obtiene configuración de métricas para evaluación de calidad.

        Args:
            threshold_level: Nivel de threshold a usar ("low", "medium", "high")
        """
        threshold_config = get_threshold_config()
        metrics = self._get_all_registered_metrics()

        thresholds = {}
        for metric_name in metrics:
            try:
                metric_thresholds = threshold_config.get_thresholds(metric_name)
                thresholds[metric_name] = metric_thresholds.get(threshold_level, 10)
            except Exception:
                # Si no hay thresholds configurados, usar valores por defecto según el nivel
                default_values = {"low": 5, "medium": 10, "high": 20}
                thresholds[metric_name] = default_values.get(threshold_level, 10)

        return thresholds

    def generate_quality_report(self, results: ProjectAnalysisResult) -> dict[str, Any] | None:
        """Genera un reporte de calidad basado en el threshold profile configurado.

        Returns:
            None si el profile no requiere este tipo de análisis, Dict con el reporte en caso contrario.
        """

        threshold_profile = self.config.get("thresholds_profile", "normal")
        logger.debug(f"Generando reporte de calidad con profile: {threshold_profile}")

        if threshold_profile == "strict":
            logger.debug("Profile 'strict' detectado - saltando análisis básico")
            return None

        if threshold_profile == "permissive":
            threshold_level = "low"
        else:  # normal
            threshold_level = "medium"

        logger.debug(f"Usando threshold level: {threshold_level}")

        thresholds = self._get_quality_metrics_config(threshold_level)
        logger.debug(f"Thresholds obtenidos para {len(thresholds)} métricas")

        problematic = self.find_problematic_entities(results, thresholds)
        total_problematic = sum(len(entities) for entities in problematic.values())
        logger.debug(f"Encontradas {total_problematic} entidades problemáticas en total")

        quality_score = self._calculate_quality_score(results, problematic)
        logger.info(f"Puntuación de calidad calculada: {quality_score:.2f}")

        return {
            "analysis_type": "basic",
            "threshold_profile": threshold_profile,
            "threshold_level": threshold_level,
            "overall_quality_score": quality_score,
            "total_entities": sum(
                len(file.entities) + sum(len(entity.children) for entity in file.entities)
                for file in results.files.values()
                if file.was_successful
            ),
            "problematic_entities": {
                metric: len(entities) for metric, entities in problematic.items()
            },
            "files_with_issues": len(
                [file for file in results.files.values() if not file.was_successful or file.errors]
            ),
            "critical_errors": len(
                [
                    error
                    for error in results.get_all_errors()
                    if error.severity == ErrorSeverity.CRITICAL
                ]
            ),
            "recommendations": self._generate_dynamic_recommendations(problematic),
        }

    def _calculate_quality_score(
        self,
        results: ProjectAnalysisResult,
        problematic: dict[str, list[EntityAnalysisResult]],
    ) -> float:
        """Calcula un score de calidad simple (0-100).

        NOTA: Algoritmo simple para análisis básico. El análisis avanzado usa ponderación diferente.
        """

        total_entities = sum(
            len(file.entities) + sum(len(entity.children) for entity in file.entities)
            for file in results.files.values()
            if file.was_successful
        )
        if total_entities == 0:
            return 100.0

        total_problematic = sum(len(entities) for entities in problematic.values())

        # Score base
        base_score = max(0, 100 - (total_problematic / total_entities * 100))

        # Penalización por errores críticos
        critical_errors = len(
            [
                error
                for error in results.get_all_errors()
                if error.severity == ErrorSeverity.CRITICAL
            ]
        )
        error_penalty = min(critical_errors * 10, 50)  # Max 50 puntos de penalización

        return max(0, base_score - error_penalty)

    def _generate_dynamic_recommendations(
        self,
        problematic: dict[str, list[EntityAnalysisResult]] | dict[str, int],
    ) -> list[str]:
        """Genera recomendaciones dinámicas basadas en métricas problemáticas.

        Args:
            problematic: Diccionario con métricas y sus entidades problemáticas o conteos.
        """

        recommendations = []

        # Mapeo de métricas a recomendaciones genéricas
        metric_recommendations = {
            "cyclomatic_complexity": {
                "icon": "🔄",
                "priority": "Alta",
                "action": "Refactorizar",
                "description": "función(es) con alta complejidad ciclomática. Considere aplicar patrones como Strategy o Command.",
            },
            "cognitive_complexity": {
                "icon": "🧠",
                "priority": "Alta",
                "action": "Simplificar",
                "description": "función(es) con alta complejidad cognitiva. Extraiga métodos auxiliares y reduzca el anidamiento.",
            },
            "fan_in_out": {
                "icon": "🔗",
                "priority": "Media",
                "action": "Reducir acoplamiento en",
                "description": "entidad(es) con alto acoplamiento. Considere Dependency Injection o patrones de desacoplamiento.",
            },
            "lcom4": {
                "icon": "🎯",
                "priority": "Media",
                "action": "Mejorar cohesión en",
                "description": "clase(s) con baja cohesión. Considere dividir la clase en clases más específicas.",
            },
            "nesting_depth": {
                "icon": "📊",
                "priority": "Media",
                "action": "Reducir anidamiento en",
                "description": "función(es) con anidamiento excesivo. Use cláusulas de guarda y extracción de métodos.",
            },
        }

        total_issues = 0

        for metric_name, entities in problematic.items():
            # Determinar el conteo basado en el tipo de valor
            if isinstance(entities, list):
                if not entities:
                    continue
                count = len(entities)
            elif isinstance(entities, int):
                if entities <= 0:
                    continue
                count = entities
            else:
                continue  # Tipo no soportado

            total_issues += count

            config = metric_recommendations.get(
                metric_name,
                {
                    "icon": "⚠️",
                    "priority": "Media",
                    "action": "Revisar",
                    "description": f"entidad(es) con valores altos en {metric_name.replace('_', ' ')}.",
                },
            )

            recommendation = (
                f"{config['icon']} Prioridad {config['priority']}: "
                f"{config['action']} {count} {config['description']}"
            )
            recommendations.append(recommendation)

        # Recomendación general si hay muchos problemas
        if total_issues > 10:
            recommendations.append(
                f"📋 Recomendación General: Con {total_issues} entidades problemáticas, "
                f"considere implementar un proceso de revisión de código más estricto "
                f"y establecer límites de complejidad en su pipeline de CI/CD."
            )

        return recommendations

    def create_performance_report(self, results: ProjectAnalysisResult) -> dict[str, Any]:
        """Genera un reporte de rendimiento del análisis."""

        total_files = len(results.files)
        successful_files = results.successful_files
        failed_files = results.failed_files

        # Calcular tiempo promedio por archivo (si está disponible)
        avg_time_per_file = results.analysis_time_ms / total_files if total_files > 0 else 0

        return {
            "analysis_performance": {
                "total_analysis_time_ms": results.analysis_time_ms,
                "total_files_processed": total_files,
                "successful_files": successful_files,
                "failed_files": failed_files,
                "success_rate_percent": (
                    (successful_files / total_files * 100) if total_files > 0 else 0
                ),
                "average_time_per_file_ms": avg_time_per_file,
                "total_lines_processed": results.total_lines_of_code,
            },
            "file_statistics": {
                "largest_file_lines": max(
                    (file.line_count for file in results.files.values()),
                    default=0,
                ),
                "average_file_size_lines": (
                    results.total_lines_of_code / total_files if total_files > 0 else 0
                ),
                "files_with_errors": len([file for file in results.files.values() if file.errors]),
            },
        }

    def get_top_entities_by_metric(
        self,
        results: ProjectAnalysisResult,
        metric_name: str,
        limit: int = 10,
        entity_types: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Obtiene las entidades con los valores más altos para una métrica específica."""

        entity_types = entity_types or ["function", "class", "method"]
        entities_with_values = []

        def add_entity(
            entity: EntityAnalysisResult, file_path: str, parent_name: str | None = None
        ) -> None:
            if entity.entity_type not in entity_types:
                return
            value = entity.metrics.get_metric_value(metric_name)
            if value is None:
                return
            entities_with_values.append(
                {
                    "entity_name": f"{parent_name}.{entity.name}" if parent_name else entity.name,
                    "entity_type": entity.entity_type,
                    "file_path": str(file_path),
                    "line_start": entity.source_info.get("line_start"),
                    "metric_value": value,
                }
            )

        for file_path, file_result in results.files.items():
            if not file_result.was_successful:
                continue

            for entity in file_result.entities:
                add_entity(entity, file_path)

                # Incluir métodos de clases
                for child in entity.children:
                    add_entity(child, file_path, parent_name=entity.name)

        # Ordenar por valor de métrica descendente
        entities_with_values.sort(key=lambda x: x["metric_value"], reverse=True)

        return entities_with_values[:limit]

    def get_entities_by_threshold_level(
        self,
        results: ProjectAnalysisResult,
        metric_name: str,
        level: str = "high",  # "low", "medium", "high", "very_high"
    ) -> list[EntityAnalysisResult]:
        """Obtiene entidades que superan un nivel específico de threshold para una métrica.

        NOTA: Este método usa thresholds fijos independientes del threshold profile del CLI.
        El threshold profile solo determina qué análisis mostrar, no los valores de los thresholds.
        """

        # Usar ThresholdConfig pero sin usar el perfil activo
        threshold_config = get_threshold_config()

        try:
            # Obtener thresholds usando el perfil por defecto (no el activo)
            thresholds = threshold_config.get_thresholds(metric_name, profile="normal")

            # Determinar threshold según el nivel solicitado
            if level == "low":
                threshold_value = thresholds.get("low", 0)
            elif level == "medium":
                threshold_value = thresholds.get("medium", 0)
            elif level == "high":
                threshold_value = thresholds.get("high", 0)
            else:  # very_high - usar "high" como mínimo
                threshold_value = thresholds.get("high", 0)
        except Exception:
            # Si no hay thresholds configurados, usar valores por defecto fijos
            default_values = {"low": 5, "medium": 10, "high": 20}
            threshold_value = default_values.get(level, 20)

        problematic_entities = []

        for file_result in results.files.values():
            if not file_result.was_successful:
                continue

            for entity in file_result.entities:
                value = entity.metrics.get_metric_value(metric_name)
                if value is not None and value > threshold_value:
                    problematic_entities.append(entity)

                # Incluir métodos de clases
                for child in entity.children:
                    child_value = child.metrics.get_metric_value(metric_name)
                    if child_value is not None and child_value > threshold_value:
                        problematic_entities.append(child)

        # Ordenar por valor de métrica descendente
        problematic_entities.sort(
            key=lambda e: e.metrics.get_metric_value(metric_name) or 0,
            reverse=True,
        )

        return problematic_entities

    def _get_entities_with_file_info(
        self,
        results: ProjectAnalysisResult,
        metric_name: str,
        level: str = "high",
    ) -> list[dict[str, Any]]:
        """Obtiene entidades problemáticas junto con la información del archivo donde se encuentran.

        Args:
            results: Resultados del análisis del proyecto
            metric_name: Nombre de la métrica a evaluar
            level: Nivel de threshold ("low", "medium", "high", "very_high")

        Returns:
            Lista de diccionarios con información de entidad y archivo
        """
        threshold_config = get_threshold_config()

        try:
            # Obtener thresholds usando el perfil por defecto
            thresholds = threshold_config.get_thresholds(metric_name, profile="normal")

            # Determinar threshold según el nivel solicitado
            if level == "low":
                threshold_value = thresholds.get("low", 0)
            elif level == "medium":
                threshold_value = thresholds.get("medium", 0)
            elif level == "high":
                threshold_value = thresholds.get("high", 0)
            else:  # very_high - usar "high" como mínimo
                threshold_value = thresholds.get("high", 0)
        except Exception:
            # Si no hay thresholds configurados, usar valores por defecto fijos
            default_values = {"low": 5, "medium": 10, "high": 20}
            threshold_value = default_values.get(level, 20)

        entities_with_file = []

        for file_path, file_result in results.files.items():
            if not file_result.was_successful:
                continue

            for entity in file_result.entities:
                value = entity.metrics.get_metric_value(metric_name)
                if value is not None and value > threshold_value:
                    entities_with_file.append(
                        {
                            "entity": entity,
                            "file_path": file_path,
                            "metric_value": value,
                        }
                    )

            # Incluir métodos de clases
            for child in entity.children:
                child_value = child.metrics.get_metric_value(metric_name)
                if child_value is not None and child_value > threshold_value:
                    entities_with_file.append(
                        {
                            "entity": child,
                            "file_path": file_path,
                            "metric_value": child_value,
                        }
                    )

        # Ordenar por valor de métrica descendente
        entities_with_file.sort(key=lambda x: x["metric_value"], reverse=True)

        return entities_with_file

    def generate_detailed_quality_report(
        self, results: ProjectAnalysisResult
    ) -> dict[str, Any] | None:
        """Genera un reporte de calidad detallado basado en el threshold profile configurado.

        Returns:
            None si el profile no requiere este tipo de análisis, Dict con el reporte en caso contrario.
        """

        # Obtener el threshold profile configurado
        threshold_profile = self.config.get("thresholds_profile", "normal")

        # Determinar si debe generarse este análisis según el profile
        if threshold_profile == "permissive":
            # Profile permissive solo usa análisis básico con thresholds bajos
            return None

        from pypex.metrics import get_registry

        registry = get_registry()

        # Obtener todas las métricas registradas dinámicamente
        metrics_to_analyze = self._get_all_registered_metrics()

        detailed_analysis = {}
        overall_issues = []

        for metric_name in metrics_to_analyze:
            try:
                metric_instance = registry.get_metric(metric_name)

                # Obtener entidades problemáticas con información del archivo
                high_entities_with_file = self._get_entities_with_file_info(
                    results, metric_name, "high"
                )
                medium_entities_with_file = self._get_entities_with_file_info(
                    results, metric_name, "medium"
                )

                # Construir análisis detallado para esta métrica
                top_problematic = []
                for entity_info in high_entities_with_file[:5]:  # Top 5 más problemáticas
                    entity = entity_info["entity"]
                    file_path = entity_info["file_path"]
                    metric_value = entity.metrics.get_metric_value(metric_name)

                    if metric_value is not None:
                        interpretation = "N/A"
                        try:
                            interpretation = metric_instance.interpret(float(metric_value))
                        except Exception:
                            pass

                        top_problematic.append(
                            {
                                "entity": entity.name,
                                "type": entity.entity_type,
                                "value": metric_value,
                                "interpretation": interpretation,
                                "file": file_path,
                            }
                        )

                detailed_analysis[metric_name] = {
                    "high_complexity_entities": len(high_entities_with_file),
                    "medium_complexity_entities": len(medium_entities_with_file),
                    "top_problematic": top_problematic,
                }

                overall_issues.extend([info["entity"] for info in high_entities_with_file])

            except Exception as e:
                detailed_analysis[metric_name] = {"error": str(e)}

        # Calcular score de calidad más sofisticado
        total_entities = sum(
            len(file.entities) + sum(len(entity.children) for entity in file.entities)
            for file in results.files.values()
            if file.was_successful
        )

        if total_entities > 0:
            # Ponderar las entidades problemáticas (ponderación 3x para análisis avanzado)
            high_weight = len([e for e in overall_issues]) * 3
            quality_score = max(0, 100 - (high_weight / total_entities * 10))
        else:
            quality_score = 100.0

        return {
            "analysis_type": "advanced",
            "threshold_profile": threshold_profile,
            "threshold_level": "high",
            "overall_score": quality_score,
            "total_entities_analyzed": total_entities,
            "metrics_analysis": detailed_analysis,
            "total_problems": len(overall_issues),
            "recommendations": self._generate_dynamic_recommendations(
                {
                    metric: detailed_analysis[metric].get("high_complexity_entities", 0)
                    for metric in detailed_analysis
                    if isinstance(detailed_analysis[metric], dict)
                    and "high_complexity_entities" in detailed_analysis[metric]
                }
            ),
        }

    def _generate_advanced_recommendations(self, detailed_analysis: dict[str, Any]) -> list[str]:
        """Genera recomendaciones avanzadas basadas en análisis detallado."""

        recommendations = []

        # Usar el método dinámico en lugar de hardcodear métricas específicas
        problematic_counts = {}

        for metric_name, analysis in detailed_analysis.items():
            if isinstance(analysis, dict) and "high_complexity_entities" in analysis:
                count = analysis.get("high_complexity_entities", 0)
                if count > 0:
                    problematic_counts[metric_name] = count

        # Generar recomendaciones usando el método dinámico
        dynamic_recommendations = self._generate_dynamic_recommendations(problematic_counts)

        recommendations.extend(dynamic_recommendations)

        return recommendations
