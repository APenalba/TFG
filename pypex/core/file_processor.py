"""Procesador de archivos y directorios para análisis de código Python.

Este módulo implementa el procesamiento de archivos, incluyendo descoberta
de archivos Python, filtrado mediante patrones de exclusión, validación
de tamaños y lectura robusta de contenido con soporte multiplataforma.

Classes:
    FileProcessor: Procesador principal de archivos y directorios

Note:
    Utiliza patrones glob compilados para optimizar rendimiento y soporta
    tanto patrones absolutos como relativos con validación de permisos.
"""

import os
import re
from pathlib import Path
from re import Pattern

from pypex.core.interfaces import IFileProcessor, ParsingError
from pypex.services.logging_service import get_logger

logger = get_logger(__name__)


class FileProcessor(IFileProcessor):
    """Procesador robusto de archivos y directorios de código Python.

    Esta clase implementa la interfaz IFileProcessor y proporciona funcionalidades
    completas para el manejo de archivos Python en proyectos de análisis estático.

    Gestiona patrones de exclusión complejos usando sintaxis glob, con soporte
    para patrones absolutos y relativos. Incluye validación de tamaños de archivo,
    manejo de permisos y lectura robusta con múltiples encodings.

    Attributes:
        ignore_patterns: Lista de patrones glob para ignorar archivos/directorios
        max_file_size: Tamaño máximo de archivo a procesar en bytes

    Example:
        >>> processor = FileProcessor(
        ...     ignore_patterns=["**/tests/**", "**/*.pyc"],
        ...     max_file_size=2 * 1024 * 1024  # 2MB
        ... )
        >>> files = processor.find_python_files("/mi/proyecto")
        >>> content = processor.read_file(files[0])
    """

    def __init__(
        self,
        ignore_patterns: list[str] | None = None,
        max_file_size: int = 1024 * 1024,  # 1MB por defecto
    ):
        """Inicializa el procesador de archivos.

        Args:
            ignore_patterns: Lista de patrones glob para ignorar archivos/directorios.
            max_file_size: Tamaño máximo de archivo a procesar en bytes.
        """
        self.ignore_patterns = ignore_patterns or [
            "**/__pycache__/**",
            "**/.git/**",
            "**/.venv/**",
            "**/venv/**",
            "**/.tox/**",
            "**/.mypy_cache/**",
            "**/.pytest_cache/**",
            "**/node_modules/**",
            "**/.ipynb_checkpoints/**",
        ]
        self.max_file_size = max_file_size

        logger.debug(
            f"FileProcessor inicializado con {len(self.ignore_patterns)} patrones de exclusión"
        )
        logger.debug(f"Tamaño máximo de archivo: {max_file_size / (1024 * 1024):.1f}MB")

        (
            self._compiled_absolute_patterns,
            self._compiled_relative_patterns,
        ) = self._compile_patterns()

        logger.debug(
            f"Compilados {len(self._compiled_absolute_patterns)} patrones absolutos y {len(self._compiled_relative_patterns)} patrones relativos"
        )

    def _compile_patterns(self) -> tuple[list[Pattern], list[Pattern]]:
        """Compila los patrones glob a expresiones regulares.

        Returns:
            Tuple[List[Pattern], List[Pattern]]: Un par de listas:
                - Patrones compilados para matching absoluto (contienen '**' o similar).
                - Patrones compilados para matching relativo (anclados ^...$).
        """
        compiled_absolute_patterns: list[Pattern] = []
        compiled_relative_patterns: list[Pattern] = []
        re_flags = re.IGNORECASE if os.name == "nt" else 0

        for pattern_glob in self.ignore_patterns:
            temp_re_core = ""
            is_absolute_pattern_logic = False

            if pattern_glob.startswith("**/") and pattern_glob.endswith("/**"):
                # e.g., "**/__pycache__/**" -> ".*__pycache__.*"
                dir_name = re.escape(pattern_glob[3:-3])
                temp_re_core = f".*{dir_name}.*"
                is_absolute_pattern_logic = True
            elif pattern_glob.endswith("/**"):
                # e.g., ".git/**" or "foo/**"
                # Matches if base_name is a directory, anywhere in the path.
                base_name = re.escape(pattern_glob[:-3])
                # Matches base_name itself or base_name/anything
                temp_re_core = f".*{base_name}($|[\\/](.*|$))"
                is_absolute_pattern_logic = True
            elif pattern_glob.startswith("**/"):
                # e.g., "**/*.md", "**/foo.py", "**/temp*"
                # Matches if path ends with item_pattern_glob, anywhere in the path.
                item_pattern_glob = pattern_glob[3:]
                item_regex_part = item_pattern_glob.replace(".", r"\.").replace("*", r"[^/\\]*")
                temp_re_core = f".*{item_regex_part}$"
                is_absolute_pattern_logic = True
            else:
                # "Normal" pattern, e.g., "tests/*", "foo.py", "build/"
                # These are relative patterns. Convert to regex and anchor with ^$.
                core_re_for_relative = (
                    pattern_glob.replace(".", r"\.")
                    .replace("**", r".*")  # For patterns like "foo/**/bar"
                    .replace("*", r"[^/\\]*")
                )
                temp_re_core = f"^{core_re_for_relative}$"
                is_absolute_pattern_logic = False

            if is_absolute_pattern_logic:
                compiled_absolute_patterns.append(re.compile(temp_re_core, re_flags))
            else:
                compiled_relative_patterns.append(re.compile(temp_re_core, re_flags))
        return compiled_absolute_patterns, compiled_relative_patterns

    def should_ignore(self, path_to_check: str | Path, scan_root_abs: Path) -> bool:
        """Determina si un archivo o directorio debe ser ignorado.

        Args:
            path_to_check: Ruta del archivo o directorio.
            scan_root_abs: Ruta absoluta raíz del escaneo actual.

        Returns:
            bool: True si el archivo debe ser ignorado, False en caso contrario.
        """
        path_to_check_abs = Path(path_to_check).resolve()
        path_to_check_str_abs = str(path_to_check_abs)

        if os.name == "nt":
            path_to_check_str_abs = path_to_check_str_abs.replace("\\", "/")

        # 1. Check absolute patterns against the full absolute path
        for regex_pattern in self._compiled_absolute_patterns:
            if regex_pattern.search(path_to_check_str_abs):
                return True

        # 2. Check relative patterns against path relative to scan_root_abs
        try:
            relative_path_str = str(path_to_check_abs.relative_to(scan_root_abs))
            if os.name == "nt":
                relative_path_str = relative_path_str.replace("\\", "/")

            for regex_pattern in self._compiled_relative_patterns:
                if regex_pattern.fullmatch(relative_path_str):
                    return True
        except ValueError:
            # path_to_check_abs is not under scan_root_abs.
            # Relative patterns should not match.
            pass

        # 3. Check file size (only for files)
        if path_to_check_abs.is_file():
            try:
                if path_to_check_abs.stat().st_size > self.max_file_size:
                    return True
            except OSError:
                pass

        return False

    def find_python_files(self, path: str | Path) -> list[Path]:
        """Encuentra todos los archivos Python en una ruta.

        Args:
            path: Ruta del archivo o directorio.

        Returns:
            List[Path]: Lista de archivos Python encontrados.

        Raises:
            FileNotFoundError: Si la ruta no existe.
        """
        path_obj = Path(path).resolve()
        scan_root_abs = path_obj

        logger.debug(f"Iniciando búsqueda de archivos Python en: {path_obj}")

        if not path_obj.exists():
            logger.error(f"La ruta {path} no existe")
            raise FileNotFoundError(f"La ruta {path} no existe")

        if path_obj.is_file():
            if path_obj.suffix == ".py" and not self.should_ignore(path_obj, scan_root_abs):
                logger.debug(f"Archivo Python individual encontrado: {path_obj}")
                return [path_obj]
            logger.debug(f"Archivo ignorado o no es Python: {path_obj}")
            return []

        python_files = []
        logger.debug(f"Explorando directorio recursivamente: {path_obj}")

        for root, dirs, files in os.walk(path_obj):
            current_root_path = Path(root)

            # Filtrar directorios a ignorar
            initial_dirs_count = len(dirs)
            dirs[:] = [
                d for d in dirs if not self.should_ignore(current_root_path / d, scan_root_abs)
            ]
            ignored_dirs_count = initial_dirs_count - len(dirs)
            if ignored_dirs_count > 0:
                logger.debug(f"Ignorados {ignored_dirs_count} directorios en {current_root_path}")

            # Añadir archivos Python no ignorados
            files_found_in_dir = 0
            for file in files:
                if file.endswith(".py"):
                    file_path = current_root_path / file
                    if not self.should_ignore(file_path, scan_root_abs):
                        python_files.append(file_path)
                        files_found_in_dir += 1

            if files_found_in_dir > 0:
                logger.debug(
                    f"Encontrados {files_found_in_dir} archivos Python en {current_root_path}"
                )

        logger.info(
            f"Búsqueda completada: {len(python_files)} archivos Python encontrados en total"
        )
        return python_files

    def read_file(self, file_path: str | Path) -> str:
        """Lee el contenido de un archivo.

        Args:
            file_path: Ruta al archivo.

        Returns:
            str: Contenido del archivo.

        Raises:
            FileNotFoundError: Si el archivo no existe.
        """
        path = Path(file_path)

        logger.debug(f"Leyendo archivo: {path}")

        if not path.exists() or not path.is_file():
            logger.error(f"El archivo {file_path} no existe o no es un archivo")
            raise FileNotFoundError(f"El archivo {file_path} no existe")

        try:
            with open(path, encoding="utf-8") as f:
                content = f.read()
            logger.debug(f"Archivo leído correctamente con UTF-8: {len(content)} caracteres")
            return content
        except UnicodeDecodeError as e:
            logger.warning(f"Error de codificación UTF-8 en {path}: {e}. Intentando con latin-1")
            try:
                with open(path, encoding="latin-1") as f:
                    content = f.read()
                logger.debug(f"Archivo leído con latin-1: {len(content)} caracteres")
                return content
            except Exception as e:
                logger.error(
                    f"No se puede leer el archivo {file_path} con ninguna codificación: {str(e)}"
                )
                raise ValueError(f"No se puede leer el archivo {file_path}: {str(e)}")
        except Exception as e:
            logger.error(f"Error inesperado leyendo {file_path}: {str(e)}")
            raise ValueError(f"Error al leer el archivo {file_path}: {str(e)}")

    def process_file(self, file_path: str | Path) -> dict[str, any]:
        """Procesa un archivo Python y extrae su información estructural.

        Args:
            file_path: Ruta al archivo Python

        Returns:
            Información estructural del archivo

        Raises:
            FileNotFoundError: Si el archivo no existe
            ParsingError: Si hay errores al parsear el archivo
        """
        path = Path(file_path)
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"El archivo {file_path} no existe")

        if path.suffix != ".py":
            raise ParsingError(f"El archivo {file_path} no es un archivo Python")

        try:
            content = self.read_file(file_path)
            lines = content.splitlines()

            # Información básica del archivo
            file_info = {
                "path": str(path),
                "name": path.name,
                "size": path.stat().st_size,
                "lines": len(lines),
                "content": content,
            }

            return file_info
        except Exception as e:
            raise ParsingError(f"Error al procesar el archivo {file_path}: {str(e)}")
