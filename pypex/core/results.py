"""Estructuras de datos para resultados de análisis de código PyPex.

Este módulo define todas las estructuras de datos para representar resultados
de análisis de código Python. Incluye jerarquías desde entidades individuales
hasta proyectos completos con funcionalidades de filtrado y estadísticas.

Classes:
    AnalysisError: Representa errores durante el análisis
    MetricsResult: Resultado unificado de métricas para cualquier entidad
    EntityAnalysisResult: Resultado de análisis para entidades específicas
    FileAnalysisResult: Resultado de análisis para archivos completos
    ProjectAnalysisResult: Resultado completo de análisis de proyecto

Enums:
    ErrorSeverity: Niveles de severidad para errores de análisis

Types:
    MetricValue: Valor numérico de una métrica (int o float)
    MetricComponents: Diccionario de componentes de métrica
    MetricResult: Resultado que puede ser valor simple o compuesto

Note:
    Todas las estructuras usan dataclasses para inmutabilidad y eficiencia,
    con métodos de conveniencia para consultas y filtrado de resultados.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, TypeAlias

MetricValue: TypeAlias = float | int
MetricComponents: TypeAlias = dict[str, MetricValue]
MetricResult: TypeAlias = MetricValue | MetricComponents


class ErrorSeverity(Enum):
    """Niveles de severidad para errores de análisis."""

    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AnalysisError:
    """Representa un error durante el análisis."""

    message: str
    severity: ErrorSeverity
    component: str  # analyzer, parser, metric, etc.
    file_path: str | None = None
    line_number: int | None = None

    def __str__(self) -> str:
        location = (
            f" at {self.file_path}:{self.line_number}"
            if self.file_path and self.line_number
            else ""
        )
        return f"[{self.severity.value.upper()}] {self.component}: {self.message}{location}"


@dataclass
class MetricsResult:
    """Resultado unificado para métricas de cualquier entidad."""

    entity_name: str
    entity_type: str
    metrics: dict[str, MetricResult]
    errors: list[AnalysisError] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def get_metric_value(
        self, metric_name: str, component: str | None = None
    ) -> MetricValue | None:
        """Obtiene el valor de una métrica específica."""
        if metric_name not in self.metrics:
            return None

        result = self.metrics[metric_name]
        if component is None:
            return result if isinstance(result, (int, float)) else None

        if isinstance(result, dict):
            return result.get(component)
        return None

    def has_errors(self, min_severity: ErrorSeverity = ErrorSeverity.WARNING) -> bool:
        """Verifica si hay errores de al menos cierta severidad."""
        severities = [
            ErrorSeverity.WARNING,
            ErrorSeverity.ERROR,
            ErrorSeverity.CRITICAL,
        ]
        min_index = severities.index(min_severity)
        return any(severities.index(error.severity) >= min_index for error in self.errors)


@dataclass
class EntityAnalysisResult:
    """Resultado del análisis para una entidad específica (función, clase)."""

    name: str
    entity_type: str
    metrics: MetricsResult
    children: list["EntityAnalysisResult"] = field(default_factory=list)
    source_info: dict[str, Any] = field(default_factory=dict)


@dataclass
class FileAnalysisResult:
    """Resultado del análisis para un archivo completo."""

    file_path: Path
    module_name: str
    file_size: int
    line_count: int

    module_metrics: MetricsResult | None = None
    entities: list[EntityAnalysisResult] = field(default_factory=list)

    analysis_time_ms: float = 0.0
    errors: list[AnalysisError] = field(default_factory=list)
    warnings: list[AnalysisError] = field(default_factory=list)

    basic_ast_data: dict[str, Any] | None = None

    @property
    def was_successful(self) -> bool:
        """Indica si el análisis fue exitoso (sin errores críticos)."""
        return not any(error.severity == ErrorSeverity.CRITICAL for error in self.errors)

    @property
    def has_detailed_metrics(self) -> bool:
        """Indica si se pudieron calcular métricas detalladas."""
        return self.module_metrics is not None and len(self.entities) > 0


@dataclass
class ProjectAnalysisResult:
    """Resultado completo del análisis de proyecto."""

    project_name: str
    root_path: Path
    analysis_timestamp: str

    # Métricas agregadas a nivel proyecto
    project_metrics: MetricsResult | None = None

    # Resultados por archivo
    files: dict[str, FileAnalysisResult] = field(default_factory=dict)

    # Resumen estadístico
    total_files: int = 0
    successful_files: int = 0
    failed_files: int = 0
    total_lines_of_code: int = 0
    analysis_time_ms: float = 0.0

    # Errores globales
    global_errors: list[AnalysisError] = field(default_factory=list)

    def get_summary_stats(self) -> dict[str, Any]:
        """Genera estadísticas resumen del proyecto."""
        return {
            "project_name": self.project_name,
            "total_files": self.total_files,
            "successful_files": self.successful_files,
            "failed_files": self.failed_files,
            "success_rate": (
                (self.successful_files / self.total_files * 100) if self.total_files > 0 else 0
            ),
            "total_lines_of_code": self.total_lines_of_code,
            "analysis_time_seconds": self.analysis_time_ms / 1000,
            "critical_errors": len(
                [e for e in self.global_errors if e.severity == ErrorSeverity.CRITICAL]
            ),
            "has_project_metrics": self.project_metrics is not None,
        }

    def get_hot_spots(
        self, metric_name: str, threshold: float, limit: int = 10
    ) -> list[EntityAnalysisResult]:
        """Encuentra las entidades con valores más altos para una métrica."""
        hot_spots = []

        for file_result in self.files.values():
            if not file_result.was_successful:
                continue

            for entity in file_result.entities:
                value = entity.metrics.get_metric_value(metric_name)
                if value and value >= threshold:
                    hot_spots.append(entity)

                # Incluir hijos (métodos de clases)
                for child in entity.children:
                    child_value = child.metrics.get_metric_value(metric_name)
                    if child_value and child_value >= threshold:
                        hot_spots.append(child)

        # Ordenar por valor de métrica descendente
        hot_spots.sort(
            key=lambda e: e.metrics.get_metric_value(metric_name) or 0,
            reverse=True,
        )
        return hot_spots[:limit]

    def get_all_errors(
        self, min_severity: ErrorSeverity = ErrorSeverity.WARNING
    ) -> list[AnalysisError]:
        """Obtiene todos los errores del análisis filtrados por severidad."""
        all_errors = [e for e in self.global_errors if e.severity.value >= min_severity.value]

        for file_result in self.files.values():
            all_errors.extend(
                [e for e in file_result.errors if e.severity.value >= min_severity.value]
            )
            if file_result.module_metrics:
                all_errors.extend(
                    [
                        e
                        for e in file_result.module_metrics.errors
                        if e.severity.value >= min_severity.value
                    ]
                )

            for entity in file_result.entities:
                all_errors.extend(
                    [e for e in entity.metrics.errors if e.severity.value >= min_severity.value]
                )
                for child in entity.children:
                    all_errors.extend(
                        [e for e in child.metrics.errors if e.severity.value >= min_severity.value]
                    )

        return sorted(
            all_errors,
            key=lambda e: (
                e.severity.value,
                e.file_path or "",
                e.line_number or 0,
            ),
        )
