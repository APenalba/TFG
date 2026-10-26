"""Organizador de estructura jerárquica de packages para el reporte HTML."""

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pypex.core.results import FileAnalysisResult

from .svg_icons import SVGIconManager


@dataclass
class PackageNode:
    """Representa un nodo en la estructura jerárquica de packages."""

    name: str
    full_path: str
    files: list[tuple[str, FileAnalysisResult]]
    children: dict[str, "PackageNode"]
    is_root: bool = False
    node_type: str = "directory"  # "directory", "file", "root"

    def __post_init__(self):
        if self.children is None:
            self.children = {}


class PackageOrganizer:
    """Organiza los módulos en una estructura jerárquica de packages."""

    def __init__(self, project_root: str = None):
        """
        Inicializa el organizador de packages.

        Args:
            project_root: Ruta raíz del proyecto a analizar
        """
        self.project_root = project_root
        # Extraer el nombre base del directorio analizado
        if project_root:
            self.base_dir = Path(project_root).name
            # Convertir project_root a Path y resolver cualquier símbolo relativo
            self.project_path = Path(project_root).resolve()
        else:
            self.base_dir = "."
            self.project_path = Path(".").resolve()

        # Inicializar el manager de iconos SVG
        self.svg_manager = SVGIconManager()

    def organize_files_hierarchically(self, files: dict[str, FileAnalysisResult]) -> PackageNode:
        """
        Organiza los archivos en una estructura jerárquica de packages.

        Args:
            files: Diccionario de archivos analizados

        Returns:
            Nodo raíz de la estructura jerárquica
        """
        # Icono de carpeta raíz con Python
        root_icon = self.svg_manager.get_python_folder_icon(self.base_dir, is_open=True)

        root = PackageNode(
            name=f"{root_icon} {self.base_dir}",
            full_path="",
            files=[],
            children={},
            is_root=True,
            node_type="root",
        )

        for file_path, file_result in files.items():
            rel_path = self._get_relative_path(file_path)
            if rel_path:  # Solo procesar si tenemos una ruta relativa válida
                self._insert_file_in_hierarchy(root, rel_path, file_result)

        return root

    def _get_relative_path(self, file_path: str) -> str:
        """
        Convierte una ruta absoluta a relativa del proyecto, ignorando la estructura superior.

        Args:
            file_path: Ruta del archivo a convertir

        Returns:
            Ruta relativa desde el directorio de análisis, o None si está fuera del proyecto
        """
        try:
            path_obj = Path(file_path).resolve()

            # Intentar hacer la ruta relativa al directorio del proyecto
            try:
                relative_path = path_obj.relative_to(self.project_path)
                return str(relative_path).replace("\\", "/")
            except ValueError:
                # Si el archivo está fuera del directorio del proyecto, ignorarlo
                return None

        except Exception:
            # En caso de cualquier error, retornar None para ignorar el archivo
            return None

    def _insert_file_in_hierarchy(
        self, root: PackageNode, rel_path: str, file_result: FileAnalysisResult
    ) -> None:
        """
        Inserta un archivo en la estructura jerárquica.

        Args:
            root: Nodo raíz donde insertar
            rel_path: Ruta relativa del archivo
            file_result: Resultado del análisis del archivo
        """
        if not rel_path:
            return

        path_obj = Path(rel_path)
        path_parts = path_obj.parts

        if len(path_parts) == 1:
            # Archivo en la raíz
            root.files.append((rel_path, file_result))
            return

        # Navegar/crear la estructura de directorios
        current_node = root
        for i, part in enumerate(path_parts[:-1]):  # Excluir el nombre del archivo
            if part not in current_node.children:
                # Crear nuevo nodo para este directorio
                full_path = "/".join(path_parts[: i + 1])

                # Determinar el icono según el tipo de directorio usando SVG
                icon = self.svg_manager.get_python_folder_icon(part, is_open=False)

                current_node.children[part] = PackageNode(
                    name=f"{icon} {part}",
                    full_path=full_path,
                    files=[],
                    children={},
                    node_type="directory",
                )
            current_node = current_node.children[part]

        # Añadir el archivo al nodo final
        current_node.files.append((rel_path, file_result))

    def _get_directory_icon(self, directory_name: str) -> str:
        """Obtiene el icono apropiado para un directorio (método legacy)."""
        # Usar el nuevo sistema SVG en lugar de emojis
        return self.svg_manager.get_python_folder_icon(directory_name, is_open=False)

    def _get_file_icon(self, file_result: FileAnalysisResult) -> str:
        """Obtiene el icono apropiado para un archivo según su estado y tipo."""
        if not file_result.was_successful:
            return "🔴"  # Error - mantener emoji para errores

        file_name = Path(file_result.file_path).name

        # Usar el nuevo sistema SVG para archivos Python
        return self.svg_manager.get_python_file_icon(file_name)

    def generate_flat_package_dict(
        self, files: dict[str, FileAnalysisResult]
    ) -> dict[str, list[tuple[str, FileAnalysisResult]]]:
        """
        Genera la estructura de packages plana (para compatibilidad).

        Args:
            files: Diccionario de archivos analizados

        Returns:
            Diccionario de packages con sus archivos
        """
        packages = defaultdict(list)

        for file_path, file_result in files.items():
            rel_path = self._get_relative_path(file_path)
            if not rel_path:
                continue

            # Obtener el directorio del archivo
            path_obj = Path(rel_path)
            if len(path_obj.parts) > 1:
                package_path = str(path_obj.parent).replace("\\", "/")
            else:
                package_path = "."  # Raíz del proyecto

            packages[package_path].append((rel_path, file_result))

        return dict(packages)

    def get_package_statistics(self, root: PackageNode) -> dict[str, Any]:
        """
        Obtiene estadísticas de la estructura de packages.

        Args:
            root: Nodo raíz de la estructura

        Returns:
            Diccionario con estadísticas
        """
        stats = {
            "total_packages": 0,
            "total_files": 0,
            "max_depth": 0,
            "packages_by_depth": defaultdict(int),
        }

        def _count_recursive(node: PackageNode, depth: int) -> None:
            if not node.is_root:
                stats["total_packages"] += 1
                stats["packages_by_depth"][depth] += 1

            stats["total_files"] += len(node.files)
            stats["max_depth"] = max(stats["max_depth"], depth)

            for child in node.children.values():
                _count_recursive(child, depth + 1)

        _count_recursive(root, 0)
        return stats
