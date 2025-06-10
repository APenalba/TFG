"""Módulo metrics de PyPex - Sistema de métricas de complejidad de código Python.

Este módulo proporciona un sistema completo para calcular métricas de complejidad
de código Python. Incluye métricas de complejidad, cohesión, acoplamiento, tamaño
y diseño, con un sistema de umbrales configurable y registro automático.

Classes:
    BaseMetric: Implementación base para métricas
    MetricsEngine: Motor principal para cálculo de métricas
    MetricsRegistry: Registro de métricas disponibles
    ComplexityLevel: Niveles de complejidad para interpretación

Interfaces:
    IMetric: Interfaz base para todas las métricas

Exceptions:
    MetricError: Excepción base para errores en métricas
    MetricNotFoundError: Métrica solicitada no existe
    InvalidEntityError: Entidad no soportada por la métrica

Functions:
    get_registry: Obtiene la instancia singleton del registro
    get_threshold_config: Obtiene configuración de umbrales

Note:
    El registro de métricas se inicializa automáticamente al importar el paquete.
    Todas las métricas implementadas se registran automáticamente.

Autor: Alejandro Penalba Tarrida
Licencia: MIT
"""

from pypex.metrics.base import (
    BaseMetric,
    IMetric,
    InvalidEntityError,
    MetricError,
    MetricNotFoundError,
)
from pypex.metrics.cohesion.lcom4 import LCOM4
from pypex.metrics.complexity.cognitive import CognitiveComplexity
from pypex.metrics.complexity.comprehension_complexity import (
    ComprehensionComplexityMetric,
)
from pypex.metrics.complexity.cyclomatic import CyclomaticComplexity
from pypex.metrics.complexity.essential_complexity import (
    EssentialComplexityMetric,
)
from pypex.metrics.complexity.exception_handling_complexity import (
    ExceptionHandlingComplexityMetric,
)
from pypex.metrics.complexity.generator_complexity import (
    GeneratorComplexityMetric,
)
from pypex.metrics.complexity.halstead import HalsteadMetric
from pypex.metrics.complexity.logical_complexity import LogicalComplexityMetric
from pypex.metrics.complexity.nested_comprehension_depth import (
    NestedComprehensionDepthMetric,
)
from pypex.metrics.complexity.nesting_depth import NestingDepth
from pypex.metrics.coupling.advanced_coupling import AdvancedCouplingMetric
from pypex.metrics.coupling.fan_in_out import FanInOutMetric
from pypex.metrics.design.design_complexity import DesignComplexityMetric
from pypex.metrics.engine import MetricsEngine
from pypex.metrics.registry import MetricsRegistry, get_registry
from pypex.metrics.size.lines_of_code import LinesOfCodeMetric
from pypex.metrics.size.parameter_count import ParameterCountMetric
from pypex.metrics.thresholds import ComplexityLevel, get_threshold_config

__all__ = [
    "IMetric",
    "BaseMetric",
    "MetricError",
    "MetricNotFoundError",
    "InvalidEntityError",
    "get_registry",
    "MetricsRegistry",
    "MetricsEngine",
    "ComplexityLevel",
    "get_threshold_config",
    "CyclomaticComplexity",
    "CognitiveComplexity",
    "NestingDepth",
    "EssentialComplexityMetric",
    "LogicalComplexityMetric",
    "ComprehensionComplexityMetric",
    "NestedComprehensionDepthMetric",
    "ExceptionHandlingComplexityMetric",
    "GeneratorComplexityMetric",
    "HalsteadMetric",
    "DesignComplexityMetric",
    "LCOM4",
    "FanInOutMetric",
    "AdvancedCouplingMetric",
    "LinesOfCodeMetric",
    "ParameterCountMetric",
]
