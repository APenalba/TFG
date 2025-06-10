"""Módulo de métricas de diseño para PyPex.

Este módulo contiene métricas relacionadas con aspectos de diseño y arquitectura del código:
- Complejidad de diseño
- Métricas de acoplamiento arquitectónico
- Análisis de dependencias inter-módulos

Autor: Alejandro Penalba Tarrida
Licencia: MIT
"""

from .design_complexity import DesignComplexityMetric

__all__ = [
    "DesignComplexityMetric",
]
