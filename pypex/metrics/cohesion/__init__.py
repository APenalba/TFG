"""Paquete de métricas de cohesión.

Este paquete contiene implementaciones de métricas relacionadas con la
cohesión de clases y módulos, como LCOM (Lack of Cohesion of Methods).

Autor: Alejandro Penalba Tarrida
Licencia: MIT
"""

from pypex.metrics.cohesion.lcom4 import LCOM4

__all__ = [
    "LCOM4",
]
