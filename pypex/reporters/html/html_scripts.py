"""Scripts JavaScript limpios y profesionales para el reporte HTML.

El JavaScript vive en ``static/scripts.js`` y se incrusta inline para que el
reporte siga siendo un único archivo autocontenido.
"""

from .static_assets import load_static_asset


class HTMLScripts:
    """Maneja los scripts JavaScript del reporte HTML con funcionalidad esencial."""

    @staticmethod
    def get_scripts() -> str:
        """Retorna el bloque ``<script>`` con el JavaScript del reporte."""
        return f"\n<script>\n{load_static_asset('scripts.js')}</script>\n"
