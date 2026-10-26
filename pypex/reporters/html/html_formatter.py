"""Utilidades de formateo para el reporte HTML."""

import html
from typing import Any

from pypex.metrics import MetricNotFoundError, get_registry


class HTMLFormatter:
    """Utilidades de formateo para el reporte HTML."""

    def __init__(self):
        self.metric_registry = get_registry()

    def safe_id(self, text: str) -> str:
        """Convierte texto a un ID HTML seguro."""
        return "".join(c if c.isalnum() or c in ["-", "_"] else "_" for c in str(text)).strip("_")

    def get_quality_class(self, score: float) -> str:
        """Obtiene la clase CSS para el score de calidad."""
        if score >= 80:
            return "quality-excellent"
        elif score >= 60:
            return "quality-good"
        elif score >= 40:
            return "quality-fair"
        else:
            return "quality-poor"

    def get_metric_color_class(self, metric_name: str, value: Any) -> str:
        """Obtiene la clase CSS para colorear métricas según su valor."""
        try:
            if not isinstance(value, (int, float)):
                return "metric-na"

            base_metric = metric_name.split(".")[0]
            metric = self.metric_registry.get_metric(base_metric)
            level = metric.interpret(float(value))

            level_map = {
                "Muy Alta": "metric-very-high",
                "Alta": "metric-high",
                "Media": "metric-medium",
                "Baja": "metric-low",
            }
            return level_map.get(level, "metric-unknown")
        except (MetricNotFoundError, Exception):
            # Heurística simple para métricas no registradas
            if isinstance(value, (int, float)):
                if value >= 50:
                    return "metric-very-high"
                if value >= 20:
                    return "metric-high"
                if value >= 10:
                    return "metric-medium"
                return "metric-low"
            return "metric-na"

    def get_metric_tooltip(self, metric_name: str) -> str:
        """Obtiene tooltip descriptivo para una métrica con escapado HTML seguro."""
        try:
            base_metric = metric_name.split(".")[0]
            metric = self.metric_registry.get_metric(base_metric)
            # Escapar HTML para prevenir caracteres problemáticos
            description = html.escape(metric.description, quote=True)
            return description
        except MetricNotFoundError:
            # Crear tooltip predeterminado para métrica no encontrada
            safe_metric_name = html.escape(metric_name.replace("_", " ").title(), quote=True)
            return f"Métrica: {safe_metric_name}"
        except Exception:
            # Fallback seguro para cualquier error inesperado
            safe_metric_name = html.escape(str(metric_name).replace("_", " ").title(), quote=True)
            return f"Métrica: {safe_metric_name} (descripción no disponible)"
