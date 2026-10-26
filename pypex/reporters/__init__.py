"""Reporters package - Generadores de reportes para PyPex.

Autor: Alejandro Penalba Tarrida
Licencia: MIT
"""

from typing import Dict, Type

from pypex.reporters.console_reporter import ConsoleReporter
from pypex.reporters.html import HTMLReporter
from pypex.reporters.json_reporter import JSONReporter


class ReporterRegistry:
    """Registro de reporteros disponibles en PyPex."""

    _registry: dict[str, type] = {}

    @classmethod
    def register(cls, name: str, reporter_cls: type):
        cls._registry[name] = reporter_cls

    @classmethod
    def get_reporter(cls, name: str):
        if name not in cls._registry:
            raise ValueError(f"Reporter '{name}' no registrado.")
        return cls._registry[name]

    @classmethod
    def get_available_reporters(cls):
        return list(cls._registry.keys())


# Registrar los reporteros por defecto
ReporterRegistry.register("json", JSONReporter)
ReporterRegistry.register("html", HTMLReporter)
ReporterRegistry.register("console", ConsoleReporter)

__all__ = ["HTMLReporter", "JSONReporter", "ConsoleReporter"]

# Mapeo de nombres de reporters para facilitar su uso
REPORTERS = {
    "html": HTMLReporter,
    "json": JSONReporter,
    "console": ConsoleReporter,
}


def get_reporter(name: str, **kwargs):
    """
    Obtiene una instancia del reporter especificado.

    Args:
        name: Nombre del reporter ('html', 'json', 'console')
        **kwargs: Argumentos adicionales para el constructor del reporter

    Returns:
        Instancia del reporter solicitado

    Raises:
        ValueError: Si el nombre del reporter no es válido
    """
    if name not in REPORTERS:
        available = ", ".join(REPORTERS.keys())
        raise ValueError(f"Reporter '{name}' no encontrado. Disponibles: {available}")

    return REPORTERS[name](**kwargs)
