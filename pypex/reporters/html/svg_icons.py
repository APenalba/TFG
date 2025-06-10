"""Manejador de iconos SVG para el reporter HTML.

Posibles iconos SVG que se intentarán cargar:

Iconos de archivos:
- file_type_pytest.svg - Para archivos de pruebas pytest
- file_type_python.svg - Para archivos Python genéricos

Iconos de carpetas:
- folder_type_pytest.svg - Para carpetas de pruebas
- folder_type_pytest_opened.svg - Para carpetas de pruebas abiertas
- folder_type_python.svg - Para carpetas Python
- folder_type_python_opened.svg - Para carpetas Python abiertas
- folder_type_docs.svg / folder_type_docs_opened.svg - Para carpetas de documentación
- folder_type_tools.svg / folder_type_tools_opened.svg - Para carpetas de utilidades
- folder_type_core.svg / folder_type_core_opened.svg - Para carpetas core
- folder_type_services.svg / folder_type_services_opened.svg - Para carpetas de servicios
- folder_type_models.svg / folder_type_models_opened.svg - Para carpetas de modelos
- folder_type_view.svg / folder_type_view_opened.svg - Para carpetas de vistas
- folder_type_api.svg / folder_type_api_opened.svg - Para carpetas de API
- folder_type_config.svg / folder_type_config_opened.svg - Para carpetas de configuración
- folder_type_metrics.svg / folder_type_metrics_opened.svg - Para carpetas de métricas
- folder_type_reports.svg / folder_type_reports_opened.svg - Para carpetas de reportes
- folder_type_parser.svg / folder_type_parser_opened.svg - Para carpetas de parseo
- folder_type_analysis.svg / folder_type_analysis_opened.svg - Para carpetas de análisis
- folder_type_charts.svg / folder_type_charts_opened.svg - Para carpetas de visualización
"""

import re
import uuid
from pathlib import Path
from typing import Dict, Optional


class SVGIconManager:
    """Maneja la carga y provisión de iconos SVG desde la carpeta assets."""

    def __init__(self):
        """Inicializa el manager de iconos SVG."""
        self.assets_path = Path(__file__).parent.parent.parent / "assets"
        self._svg_cache: Dict[str, str] = {}
        self._load_svg_icons()

    def _load_svg_icons(self) -> None:
        """Carga todos los iconos SVG disponibles en el cache."""
        if not self.assets_path.exists():
            return

        for svg_file in self.assets_path.glob("*.svg"):
            try:
                with open(svg_file, "r", encoding="utf-8") as f:
                    svg_content = f.read()
                    # Limpiar el SVG removiendo atributos innecesarios
                    svg_content = self._clean_svg(svg_content)
                    self._svg_cache[svg_file.stem] = svg_content
            except Exception:
                # Ignorar archivos que no se pueden leer
                continue

    def _clean_svg(self, svg_content: str) -> str:
        """Limpia el contenido SVG para uso inline en HTML."""
        # Remover doctype y comentarios XML si existen
        svg_content = re.sub(r"<\?xml[^>]*\?>", "", svg_content)
        svg_content = re.sub(r"<!DOCTYPE[^>]*>", "", svg_content)

        # Agregar atributos básicos si no existen
        if "width=" not in svg_content:
            svg_content = svg_content.replace("<svg", '<svg width="16"', 1)
        if "height=" not in svg_content:
            svg_content = svg_content.replace("<svg", '<svg height="16"', 1)

        # Agregar clase CSS para styling
        if "class=" not in svg_content:
            svg_content = svg_content.replace(
                "<svg", '<svg class="file-icon"', 1
            )

        return svg_content.strip()

    def _make_svg_ids_unique(self, svg_content: str) -> str:
        """Hace únicos los IDs de un SVG para evitar conflictos."""
        # Generar un sufijo único para los IDs
        unique_suffix = str(uuid.uuid4())[:8]

        # Encontrar todos los IDs en el SVG y hacerlos únicos
        def replace_id(match):
            old_id = match.group(1)
            new_id = f"{old_id}_{unique_suffix}"
            return f'id="{new_id}"'

        def replace_url_reference(match):
            old_id = match.group(1)
            new_id = f"{old_id}_{unique_suffix}"
            return f"url(#{new_id})"

        # Reemplazar definiciones de ID
        svg_content = re.sub(r'id="([^"]+)"', replace_id, svg_content)

        # Reemplazar referencias a IDs (url(#id))
        svg_content = re.sub(
            r"url\(#([^)]+)\)", replace_url_reference, svg_content
        )

        return svg_content

    def get_python_file_icon(self, file_name: str) -> str:
        """Obtiene el icono apropiado para un archivo Python."""
        file_name_lower = file_name.lower()

        # Archivos de test que usan pytest
        if (
            file_name_lower.startswith("test_")
            or file_name_lower.endswith("_test.py")
            or "pytest" in file_name_lower
        ):
            return self.get_svg_icon("file_type_pytest") or "🧪"

        # Archivos Python genéricos
        if file_name_lower.endswith(".py"):
            return self.get_svg_icon("file_type_python") or "🐍"

        return "📄"  # Fallback para otros tipos

    def get_python_folder_icon(
        self, folder_name: str, is_open: bool = False
    ) -> str:
        """Obtiene el icono apropiado para una carpeta Python."""
        folder_name_lower = folder_name.lower()

        # Carpetas específicas de Python
        if folder_name_lower in ["tests", "test"]:
            icon_name = (
                "folder_type_pytest_opened"
                if is_open
                else "folder_type_pytest"
            )
            return self.get_svg_icon(icon_name) or (
                "🧪" if not is_open else "📂"
            )

        # Carpetas Python genéricas
        python_folders = ["src", "lib", "pypex", "python"]
        if any(py_name in folder_name_lower for py_name in python_folders):
            icon_name = (
                "folder_type_python_opened"
                if is_open
                else "folder_type_python"
            )
            return self.get_svg_icon(icon_name) or (
                "📁" if not is_open else "📂"
            )

        # Otros tipos de carpetas específicas
        folder_icons = {
            "docs": "folder_type_docs",
            "utils": "folder_type_tools",
            "core": "folder_type_core",
            "services": "folder_type_services",
            "models": "folder_type_models",
            "views": "folder_type_view",
            "api": "folder_type_api",
            "config": "folder_type_config",
            "metrics": "folder_type_metrics",
            "reporters": "folder_type_reports",
            "parser": "folder_type_parser",
            "analysis": "folder_type_analysis",
            "visualization": "folder_type_charts",
        }

        for folder_key, icon_name in folder_icons.items():
            if folder_key in folder_name_lower:
                full_icon_name = (
                    f"{icon_name}_opened" if is_open else icon_name
                )
                svg_icon = self.get_svg_icon(full_icon_name)
                if svg_icon:
                    return svg_icon
                # Fallback a versión sin _opened
                return self.get_svg_icon(icon_name) or "📁"

        return "📁"  # Fallback genérico

    def get_svg_icon(self, icon_name: str) -> Optional[str]:
        """Obtiene un icono SVG por nombre con IDs únicos para evitar conflictos."""
        svg_content = self._svg_cache.get(icon_name)
        if svg_content:
            # Hacer únicos los IDs para evitar conflictos en el HTML
            return self._make_svg_ids_unique(svg_content)
        return None

    def get_available_icons(self) -> list[str]:
        """Retorna una lista de todos los iconos disponibles."""
        return list(self._svg_cache.keys())

    def has_icon(self, icon_name: str) -> bool:
        """Verifica si un icono específico está disponible."""
        return icon_name in self._svg_cache
