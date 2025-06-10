"""Paquete de métricas de complejidad de código Python para PyPex.

Este paquete implementa diversas métricas para medir la complejidad del código Python,
incluyendo métricas clásicas y avanzadas que analizan diferentes aspectos estructurales
y cognitivos del código fuente.

Classes:
    CyclomaticComplexity: Métrica de complejidad ciclomática de McCabe
    CognitiveComplexity: Métrica de complejidad cognitiva
    NestingDepth: Métrica de profundidad de anidamiento
    EssentialComplexityMetric: Métrica de complejidad esencial
    LogicalComplexityMetric: Métrica de complejidad lógica
    ComprehensionComplexityMetric: Métrica de complejidad de comprensiones
    NestedComprehensionDepthMetric: Métrica de profundidad de comprensiones anidadas
    ExceptionHandlingComplexityMetric: Métrica de complejidad de manejo de excepciones
    GeneratorComplexityMetric: Métrica de complejidad de generadores
    HalsteadMetric: Métricas de Halstead (volumen, dificultad, esfuerzo)

Autor: Alejandro Penalba Tarrida
Licencia: MIT
"""

from .cognitive import CognitiveComplexity
from .comprehension_complexity import ComprehensionComplexityMetric
from .cyclomatic import CyclomaticComplexity
from .essential_complexity import EssentialComplexityMetric
from .exception_handling_complexity import ExceptionHandlingComplexityMetric
from .generator_complexity import GeneratorComplexityMetric
from .halstead import HalsteadMetric
from .logical_complexity import LogicalComplexityMetric
from .nested_comprehension_depth import NestedComprehensionDepthMetric
from .nesting_depth import NestingDepth

__all__ = [
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
]
