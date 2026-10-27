"""Estilos CSS profesionales para el reporte HTML con sistema de temas.

El CSS vive en ``static/styles.css`` y se incrusta inline para que el reporte
siga siendo un único archivo autocontenido.
"""

from .static_assets import load_static_asset


class HTMLStyles:
    """Maneja los estilos CSS del reporte HTML con diseño limpio y profesional."""

    @staticmethod
    def get_styles() -> str:
        """Retorna el bloque ``<style>`` con los estilos CSS del reporte."""
        return f"\n<style>\n{load_static_asset('styles.css')}</style>\n"
