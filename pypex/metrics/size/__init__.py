"""Paquete de métricas de tamaño de código Python para PyPex.

Este paquete implementa métricas relacionadas con el tamaño y longitud del código,
proporcionando medidas objetivas sobre la magnitud y complejidad estructural
de diferentes entidades de código.

Classes:
    LinesOfCodeMetric: Métrica de líneas de código (físicas, lógicas, comentarios)
    ParameterCountMetric: Métrica de conteo de parámetros en funciones

Autor: Alejandro Penalba Tarrida
Licencia: MIT
"""

from .lines_of_code import LinesOfCodeMetric
from .parameter_count import ParameterCountMetric

__all__ = [
    "LinesOfCodeMetric",
    "ParameterCountMetric",
]
