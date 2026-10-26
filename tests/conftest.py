"""Configuración común de pytest."""

import pytest

from pypex.metrics.registry import get_registry


@pytest.fixture(autouse=True)
def _restore_metrics_registry():
    """Restaura el registro global de métricas tras cada test.

    El registro es un singleton y MetricsEngine registra en él las métricas
    que recibe, así que las métricas falsas de un test afectarían a los demás.
    """
    registry = get_registry()
    saved = dict(registry._metrics)
    yield
    registry._metrics.clear()
    registry._metrics.update(saved)
