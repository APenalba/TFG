"""Gestión de proyectos Python para análisis de código.

Este módulo proporciona la implementación de la clase Project, que gestiona
la estructura y análisis de proyectos Python completos. Incluye descoberta
de archivos, parseo de módulos y extracción de entidades de código.

Classes:
    Project: Gestor principal de proyectos Python

Note:
    Soporta tanto archivos individuales como directorios completos,
    con análisis robusto usando Astroid y fallback a AST estándar.
"""

import os
from pathlib import Path
from typing import Any

from pypex.core.interfaces import IASTParser, IFileProcessor, InvalidProjectError, IProject
from pypex.core.results import AnalysisError, ErrorSeverity
from pypex.parser.astroid_visitor import AstroidNodeVisitor
from pypex.parser.code_entities import Module
from pypex.parser.code_entities import Project as ProjectEntity
from pypex.services.logging_service import get_logger

logger = get_logger(__name__)


class Project(IProject):
    """Clase que maneja la estructura y el análisis de un proyecto Python completo.

    Esta clase encapsula toda la lógica necesaria para analizar un proyecto Python,
    incluyendo la descoberta de archivos, parseo de módulos y extracción de entidades.
    Soporta tanto archivos individuales como directorios completos.

    Attributes:
        path: Ruta al directorio raíz del proyecto o archivo individual
        name: Nombre del proyecto
        python_files: Lista de archivos Python encontrados
        modules: Diccionario de módulos parseados
        file_processor: Procesador de archivos utilizado
        ast_parser: Parser AST utilizado
        errors: Lista de errores encontrados durante el procesamiento
    """

    def __init__(
        self,
        path: str | Path,
        file_processor: IFileProcessor,
        ast_parser: IASTParser,
        name: str | None = None,
        ignore_patterns: list[str] | None = None,
        max_file_size: int = 1024 * 1024,  # 1MB por defecto
    ):
        """Inicializa un proyecto para análisis.

        Args:
            path: Ruta al directorio raíz del proyecto o archivo individual.
            file_processor: Procesador de archivos a utilizar.
            ast_parser: Parser AST a utilizar.
            name: Nombre del proyecto. Si no se proporciona, se usa el nombre del directorio.
            ignore_patterns: Lista de patrones glob para ignorar archivos/directorios.
                            Se ignora si se pasa, el file_processor ya tiene sus patrones.
            max_file_size: Tamaño máximo de archivo a procesar en bytes.
                          Se ignora si se pasa, el file_processor ya tiene su límite.

        Raises:
            FileNotFoundError: Si la ruta no existe.
            ValueError: Si el archivo no es Python válido.
            InvalidProjectError: Si no se encuentran archivos Python válidos.
        """
        # Validación de argumentos
        if not path:
            raise ValueError("La ruta no puede estar vacía")
        if not file_processor:
            raise ValueError("file_processor es requerido")
        if not ast_parser:
            raise ValueError("ast_parser es requerido")

        self._path = Path(path).resolve()
        self._validate_path()

        self._name = name or self._generate_project_name()
        self.file_processor = file_processor
        self.ast_parser = ast_parser
        self._python_files: list[Path] = []
        self.modules: dict[str, Module] = {}
        self.errors: list[AnalysisError] = []

        # Cargar archivos del proyecto
        try:
            self._load_project_files()
            if not self._python_files:
                raise InvalidProjectError(
                    f"No se encontraron archivos Python válidos en {self._path}"
                )
        except Exception as e:
            if isinstance(e, InvalidProjectError):
                raise
            logger.error(f"Error inicializando proyecto en {self._path}: {str(e)}")
            raise InvalidProjectError(f"Error al inicializar proyecto: {str(e)}") from e

        logger.info(f"Proyecto '{self._name}' inicializado con {len(self._python_files)} archivos")

    def _validate_path(self) -> None:
        """Valida que la ruta sea válida y accesible.

        Raises:
            FileNotFoundError: Si la ruta no existe.
            ValueError: Si el archivo no es Python válido.
            PermissionError: Si no hay permisos para acceder a la ruta.
        """
        if not self._path.exists():
            raise FileNotFoundError(f"La ruta {self._path} no existe")

        # Verificar permisos de lectura
        if not os.access(self._path, os.R_OK):
            raise PermissionError(f"Sin permisos de lectura en {self._path}")

        # Si es un archivo, verificar que sea Python
        if self._path.is_file():
            if self._path.suffix != ".py":
                raise ValueError(f"El archivo {self._path} no es un archivo Python")

            # Verificar que el archivo no esté vacío o corrupto
            try:
                if self._path.stat().st_size == 0:
                    logger.warning(f"El archivo {self._path} está vacío")
            except OSError as e:
                raise ValueError(f"No se puede acceder al archivo {self._path}: {e}") from e

    def _generate_project_name(self) -> str:
        """Genera un nombre de proyecto basado en la ruta.

        Returns:
            str: Nombre del proyecto generado
        """
        if self._path.is_file():
            return self._path.stem
        else:
            # Para directorios, usar el nombre del directorio
            name = self._path.name
            if not name or name == ".":
                # Si es el directorio actual, usar "current_project"
                return "current_project"
            return name

    @property
    def path(self) -> Path:
        """Ruta al directorio raíz del proyecto o archivo individual."""
        return self._path

    @property
    def name(self) -> str:
        """Nombre del proyecto."""
        return self._name

    @property
    def python_files(self) -> list[Path]:
        """Lista de archivos Python en el proyecto."""
        return self._python_files.copy()  # Retornar copia para evitar modificaciones

    def _load_project_files(self) -> None:
        """Carga todos los archivos Python del proyecto.

        Raises:
            InvalidProjectError: Si no se encuentran archivos Python.
            Exception: Si hay errores durante la búsqueda de archivos.
        """
        logger.info(f"Buscando archivos Python en {self.path}")

        try:
            self._python_files = self.file_processor.find_python_files(self.path)

            if not self._python_files:
                raise InvalidProjectError(f"No se encontraron archivos Python en {self.path}")

            logger.info(f"Encontrados {len(self._python_files)} archivos Python")

            # Log de archivos encontrados en modo debug
            for file_path in self._python_files:
                logger.debug(f"Archivo encontrado: {file_path}")

        except Exception as e:
            logger.error(f"Error al buscar archivos Python: {str(e)}")
            self.errors.append(
                AnalysisError(
                    message=f"Error buscando archivos Python: {str(e)}",
                    severity=ErrorSeverity.CRITICAL,
                    component="project_loader",
                    file_path=str(self.path),
                )
            )
            raise

    def get_module_name(self, file_path: Path) -> str:
        """Determina el nombre del módulo a partir de la ruta del archivo.

        Args:
            file_path: Ruta al archivo Python.

        Returns:
            str: Nombre del módulo en notación de puntos.

        Raises:
            ValueError: Si file_path no es relativo al proyecto.
        """
        if not isinstance(file_path, Path):
            file_path = Path(file_path)

        # Si es un archivo individual, solo usar el nombre del archivo
        if self.path.is_file():
            return self.path.stem

        # Verificar que el archivo esté dentro del proyecto
        try:
            rel_path = file_path.relative_to(self.path)
        except ValueError as e:
            raise ValueError(
                f"El archivo {file_path} no está dentro del proyecto {self.path}"
            ) from e

        # Convertir path a notación de punto, excluyendo la extensión .py
        parts = list(rel_path.parts)
        if parts[-1].endswith(".py"):
            parts[-1] = parts[-1][:-3]  # Quitar la extensión .py

        # Ignorar __init__.py en el nombre del módulo
        if parts[-1] == "__init__":
            parts = parts[:-1]

        # Si no quedan partes, usar el nombre del directorio padre
        if not parts:
            return self.path.name

        return ".".join(parts)

    def parse_file(self, file_path: Path) -> Module | None:
        """Parsea un archivo Python y crea un objeto Module completo.

        Este método utiliza Astroid para realizar un análisis completo del archivo,
        extrayendo todas las entidades de código (funciones, clases, imports, etc.).

        Args:
            file_path: Ruta al archivo Python.

        Returns:
            Optional[Module]: Objeto Module si el parseo fue exitoso, None en caso contrario.
        """
        if not isinstance(file_path, Path):
            file_path = Path(file_path)

        logger.debug(f"Parseando archivo: {file_path}")

        try:
            # Validar que el archivo existe y es accesible
            if not file_path.exists():
                self._add_parsing_error(file_path, f"El archivo {file_path} no existe")
                return None

            if not file_path.is_file():
                self._add_parsing_error(file_path, f"La ruta {file_path} no es un archivo")
                return None

            # Leer el contenido del archivo
            try:
                content = self.file_processor.read_file(file_path)
            except Exception as e:
                self._add_parsing_error(file_path, f"Error leyendo archivo: {str(e)}")
                return None

            # Obtener información básica del archivo
            line_count = len(content.splitlines()) if content else 0
            module_name = self.get_module_name(file_path)

            # Crear módulo base con información básica
            module = Module(
                name=module_name,
                line_start=1,
                line_end=line_count,
                source_file=file_path,
                path=file_path,
            )

            # Parsear con astroid para extraer entidades detalladas
            try:
                astroid_module = self.ast_parser.parse_with_astroid(str(file_path))

                if astroid_module:
                    # Usar AstroidNodeVisitor para extraer entidades completas
                    visitor = AstroidNodeVisitor(astroid_module, str(file_path))
                    detailed_module = visitor.analyze()

                    if detailed_module:
                        # Actualizar el módulo con información detallada
                        module = self._merge_module_data(module, detailed_module)
                        module.astroid_node = astroid_module
                    else:
                        logger.warning(f"AstroidNodeVisitor no pudo analizar {file_path}")

                else:
                    logger.warning(f"Astroid no pudo parsear {file_path}")

            except Exception as e:
                # Si Astroid falla, intentar extraer información básica con AST estándar
                logger.warning(
                    f"Error con Astroid en {file_path}: {str(e)}. Usando información básica."
                )
                self._add_parsing_error(
                    file_path, f"Análisis avanzado falló: {str(e)}", ErrorSeverity.WARNING
                )

                try:
                    # Fallback: usar AST estándar para información básica
                    ast_tree = self.ast_parser.parse_file(str(file_path))
                    if ast_tree:
                        module.ast_node = ast_tree
                        # Extraer docstring básica si está disponible
                        if hasattr(ast_tree, "body") and ast_tree.body:
                            first_stmt = ast_tree.body[0]
                            if hasattr(first_stmt, "value") and hasattr(first_stmt.value, "s"):
                                module.docstring = first_stmt.value.s
                except Exception as ast_e:
                    logger.error(f"También falló el fallback AST para {file_path}: {str(ast_e)}")
                    self._add_parsing_error(
                        file_path, f"Análisis básico también falló: {str(ast_e)}"
                    )

            logger.debug(f"Archivo {file_path} parseado correctamente")
            return module

        except Exception as e:
            logger.error(f"Error crítico parseando {file_path}: {str(e)}")
            self._add_parsing_error(file_path, f"Error crítico: {str(e)}")
            return None

    def _merge_module_data(self, basic_module: Module, detailed_module: Module) -> Module:
        """Combina información básica con datos detallados del módulo.

        Args:
            basic_module: Módulo con información básica
            detailed_module: Módulo con análisis detallado de Astroid

        Returns:
            Module: Módulo combinado con toda la información disponible
        """
        # Copiar información detallada al módulo básico
        basic_module.docstring = detailed_module.docstring
        basic_module.functions = detailed_module.functions
        basic_module.classes = detailed_module.classes
        basic_module.imports = detailed_module.imports
        basic_module.variables = detailed_module.variables
        basic_module.module_level_constants = detailed_module.module_level_constants
        basic_module.future_imports = detailed_module.future_imports
        basic_module.shebang = detailed_module.shebang
        basic_module.is_package_init = detailed_module.is_package_init
        basic_module.has_main_block = detailed_module.has_main_block

        # Copiar métricas de líneas de código
        basic_module.source_lines_of_code = detailed_module.source_lines_of_code
        basic_module.docstring_sloc = detailed_module.docstring_sloc
        basic_module.comment_sloc = detailed_module.comment_sloc
        basic_module.blank_lines_count = detailed_module.blank_lines_count

        return basic_module

    def _add_parsing_error(
        self, file_path: Path, message: str, severity: ErrorSeverity = ErrorSeverity.ERROR
    ) -> None:
        """Añade un error de parseo a la lista de errores del proyecto.

        Args:
            file_path: Ruta del archivo donde ocurrió el error
            message: Mensaje de error
            severity: Severidad del error
        """
        error = AnalysisError(
            message=message, severity=severity, component="project_parser", file_path=str(file_path)
        )
        self.errors.append(error)

    def parse_all_files(self) -> None:
        """Parsea todos los archivos Python del proyecto.

        Este método procesa todos los archivos encontrados y los almacena
        en el diccionario de módulos. Los errores se almacenan pero no
        detienen el procesamiento de otros archivos.
        """
        logger.info(f"Iniciando parseo de {len(self.python_files)} archivos")

        successful_count = 0
        failed_count = 0

        for file_path in self.python_files:
            try:
                module = self.parse_file(file_path)
                if module:
                    self.modules[module.name] = module
                    successful_count += 1
                    logger.debug(f"Módulo {module.name} parseado correctamente")
                else:
                    failed_count += 1
                    logger.warning(f"No se pudo parsear {file_path}")

            except Exception as e:
                failed_count += 1
                logger.error(f"Error crítico procesando {file_path}: {str(e)}")
                self._add_parsing_error(file_path, f"Error crítico durante parseo: {str(e)}")

        logger.info(
            f"Parseo completado. {successful_count} módulos procesados correctamente, "
            f"{failed_count} fallos"
        )

        if successful_count == 0:
            logger.warning("No se pudo parsear ningún archivo correctamente")

    def to_entity(self) -> ProjectEntity:
        """Convierte el proyecto a una entidad ProjectEntity.

        Returns:
            ProjectEntity: Entidad del proyecto con métricas agregadas.
        """
        # Calcular métricas agregadas
        total_sloc = sum(module.source_lines_of_code for module in self.modules.values())
        total_docstring_sloc = sum(module.docstring_sloc for module in self.modules.values())
        total_comment_sloc = sum(module.comment_sloc for module in self.modules.values())
        total_blank_lines = sum(module.blank_lines_count for module in self.modules.values())

        # Recopilar dependencias externas (imports que no están en el proyecto)
        external_deps = set()
        module_names = set(self.modules.keys())

        for module in self.modules.values():
            for import_stmt in module.imports:
                # Verificar si el import es externo al proyecto
                if import_stmt.module not in module_names:
                    # Excluir imports estándar y built-ins comunes
                    if not self._is_standard_library_import(import_stmt.module):
                        external_deps.add(import_stmt.module)

        return ProjectEntity(
            name=self.name,
            root_path=self.path,
            modules=list(self.modules.values()),
            total_sloc_code=total_sloc,
            total_sloc_docstrings=total_docstring_sloc,
            total_sloc_comments=total_comment_sloc,
            total_blank_lines=total_blank_lines,
            external_dependencies=external_deps,
            line_start=1,
            line_end=total_sloc + total_docstring_sloc + total_comment_sloc + total_blank_lines,
        )

    def _is_standard_library_import(self, module_name: str) -> bool:
        """Verifica si un módulo pertenece a la biblioteca estándar de Python.

        Args:
            module_name: Nombre del módulo a verificar

        Returns:
            bool: True si es un módulo estándar, False en caso contrario
        """
        # Lista simplificada de módulos estándar comunes
        # En una implementación más robusta, esto podría ser más completo
        standard_modules = {
            "os",
            "sys",
            "pathlib",
            "json",
            "csv",
            "datetime",
            "time",
            "collections",
            "itertools",
            "functools",
            "re",
            "math",
            "random",
            "urllib",
            "http",
            "email",
            "logging",
            "typing",
            "dataclasses",
            "abc",
            "enum",
            "weakref",
            "copy",
            "pickle",
            "unittest",
            "threading",
            "multiprocessing",
            "subprocess",
            "argparse",
            "configparser",
            "tempfile",
            "shutil",
            "glob",
            "ast",
            "inspect",
            "importlib",
            "pkgutil",
            "sqlite3",
        }

        # Obtener el módulo raíz (antes del primer punto)
        root_module = module_name.split(".")[0]
        return root_module in standard_modules

    def get_summary(self) -> dict[str, Any]:
        """Obtiene un resumen detallado del proyecto.

        Returns:
            Dict[str, Any]: Información resumida del proyecto incluyendo estadísticas.
        """
        total_functions = sum(len(module.functions) for module in self.modules.values())
        total_classes = sum(len(module.classes) for module in self.modules.values())
        total_imports = sum(len(module.imports) for module in self.modules.values())

        # Contar métodos en clases
        total_methods = 0
        for module in self.modules.values():
            for class_entity in module.classes:
                total_methods += len(class_entity.methods)

        return {
            "name": self.name,
            "path": str(self.path),
            "files_count": len(self.python_files),
            "modules_count": len(self.modules),
            "modules": [m.name for m in self.modules.values()],
            "total_functions": total_functions,
            "total_classes": total_classes,
            "total_methods": total_methods,
            "total_imports": total_imports,
            "errors_count": len(self.errors),
            "critical_errors": len(
                [e for e in self.errors if e.severity == ErrorSeverity.CRITICAL]
            ),
            "warnings": len([e for e in self.errors if e.severity == ErrorSeverity.WARNING]),
        }

    def has_errors(self, min_severity: ErrorSeverity = ErrorSeverity.WARNING) -> bool:
        """Verifica si el proyecto tiene errores de al menos cierta severidad.

        Args:
            min_severity: Severidad mínima de errores a considerar

        Returns:
            bool: True si hay errores de la severidad especificada o mayor
        """
        severities = [ErrorSeverity.WARNING, ErrorSeverity.ERROR, ErrorSeverity.CRITICAL]
        min_index = severities.index(min_severity)

        return any(severities.index(error.severity) >= min_index for error in self.errors)

    def get_errors_by_severity(self, severity: ErrorSeverity) -> list[AnalysisError]:
        """Obtiene todos los errores de una severidad específica.

        Args:
            severity: Severidad de errores a filtrar

        Returns:
            List[AnalysisError]: Lista de errores de la severidad especificada
        """
        return [error for error in self.errors if error.severity == severity]

    def __str__(self) -> str:
        """Representación en string del proyecto."""
        return f"Project(name='{self.name}', path='{self.path}', modules={len(self.modules)})"

    def __repr__(self) -> str:
        """Representación detallada del proyecto."""
        return (
            f"Project(name='{self.name}', path='{self.path}', "
            f"files={len(self.python_files)}, modules={len(self.modules)}, "
            f"errors={len(self.errors)})"
        )
