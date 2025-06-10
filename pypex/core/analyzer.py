"""Analizador principal para el cálculo de métricas de complejidad en código Python.

Este módulo contiene la implementación principal del analizador PyPex, que coordina
todo el proceso de análisis de código Python. Maneja tanto archivos individuales
como proyectos completos, integrando parseo AST con cálculo de métricas.

Classes:
    Analyzer: Coordinador principal del proceso de análisis

Note:
    Utiliza estrategia de fallback: Astroid para análisis avanzado, AST estándar
    como alternativa si Astroid falla.
"""

from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from pypex.core.interfaces import (
    FileAnalysisResult,
    IAnalyzer,
    IASTParser,
    IFileProcessor,
    InvalidProjectError,
    IProject,
    ProjectAnalysisResult,
)
from pypex.core.project import Project
from pypex.core.results import AnalysisError, ErrorSeverity
from pypex.parser.astroid_visitor import AstroidNodeVisitor
from pypex.parser.code_entities import Module as ModuleEntity
from pypex.parser.code_entities import Project as ProjectEntity
from pypex.parser.node_visitor import ASTNodeVisitor
from pypex.services.config_service import get_config
from pypex.services.logging_service import get_logger, get_progress_manager

if TYPE_CHECKING:
    from pypex.metrics.base import IMetric
    from pypex.metrics.engine import MetricsEngine

logger = get_logger(__name__)


class Analyzer(IAnalyzer):
    """Analizador principal para código Python con cálculo de métricas de complejidad.
    
    Esta clase coordina todo el proceso de análisis de código Python, desde la carga
    de archivos hasta el cálculo de métricas. Implementa la interfaz IAnalyzer y
    proporciona funcionalidades robustas para análisis tanto de archivos individuales
    como de proyectos completos.
    
    El analizador utiliza una estrategia de fallback que intenta primero usar Astroid
    para análisis avanzado y, si falla, utiliza el módulo AST estándar de Python.
    
    Attributes:
        config: Configuración del analizador obtenida del ConfigService
        file_processor: Procesador de archivos utilizado
        parser: Parser AST utilizado
        project_class: Clase utilizada para crear proyectos
        reporters: Lista de reporteros configurados
        metrics: Lista de métricas a calcular
        metrics_engine: Motor de métricas inicializado
        
    Example:
        >>> from pypex.core import Analyzer, FileProcessor
        >>> from pypex.parser.ast_parser import ASTParser
        >>> 
        >>> analyzer = Analyzer(
        ...     file_processor=FileProcessor(),
        ...     parser=ASTParser()
        ... )
        >>> result = analyzer.analyze_file("mi_archivo.py")
        >>> print(f"Métricas calculadas: {len(result.entities)}")
    """

    def __init__(
        self,
        parser: IASTParser,
        file_processor: IFileProcessor,
        specific_metrics: Optional[List[IMetric]] = None,
    ):
        """Inicializa el analizador con sus dependencias.

        Args:
            parser: Parser de código a utilizar
            file_processor: Procesador de archivos a utilizar
            specific_metrics: Lista opcional de métricas específicas a usar

        Note:
            Si no se especifican métricas, se utilizarán todas las disponibles.
        """
        logger.debug("Inicializando analizador de código")
        self.parser = parser
        self.file_processor = file_processor
        self.config = get_config()  # Configuración centralizada
        
        # Configurar clase de proyecto desde configuración o usar por defecto
        self.project_class = Project
        
        # Importar en tiempo de ejecución para evitar imports circulares
        from pypex.metrics.engine import MetricsEngine
        
        self.metrics_engine = MetricsEngine(specific_metrics)
        logger.debug("Analizador inicializado correctamente")

    def set_reporters(self, reporters: List[Any]) -> None:
        """Configura los generadores de informes a utilizar.

        Args:
            reporters: Lista de reporteros a utilizar
        """
        self.reporters = reporters

    def set_metrics(self, metrics: List[IMetric]) -> None:
        """Configura las métricas a calcular durante el análisis.

        Args:
            metrics: Lista de métricas a utilizar
        """
        from pypex.metrics.engine import MetricsEngine
        
        self.metrics = metrics
        self.metrics_engine = MetricsEngine(specific_metrics=metrics)
        logger.debug(
            f"Motor de métricas configurado con {len(metrics)} métricas específicas"
        )

    def _ensure_metrics_engine(self) -> MetricsEngine:
        """Asegura que el motor de métricas esté inicializado y lo devuelve."""
        if self.metrics_engine is None:
            logger.debug(
                "Motor de métricas no inicializado, creando instancia por defecto."
            )
            from pypex.metrics.engine import MetricsEngine
            self.metrics_engine = MetricsEngine(specific_metrics=getattr(self, 'metrics', None))
        return self.metrics_engine

    def analyze_file(
        self,
        file_path: Union[str, Path],
        config: Optional[Dict[str, Any]] = None,
    ) -> FileAnalysisResult:
        """Analiza un archivo Python y calcula sus métricas.

        Args:
            file_path: Ruta al archivo a analizar.
            config: Configuración opcional para el análisis.

        Returns:
            FileAnalysisResult: Resultados del análisis.

        Raises:
            FileNotFoundError: Si el archivo no existe.
            InvalidPythonFileError: Si el archivo no es un archivo Python.
        """
        start_time = time.time()
        path = Path(file_path)

        # Obtener información del archivo
        file_size = 0
        line_count = 0
        try:
            if path.exists():
                file_size = path.stat().st_size
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    line_count = sum(1 for _ in f)
        except Exception:
            pass

        result = FileAnalysisResult(
            file_path=path,
            module_name=path.stem,
            file_size=file_size,
            line_count=line_count,
        )

        # Validaciones básicas
        if not path.exists() or not path.is_file():
            result.errors.append(
                AnalysisError(
                    message=f"El archivo {path} no existe o no es un archivo.",
                    severity=ErrorSeverity.CRITICAL,
                    component="file_analyzer",
                    file_path=str(path),
                )
            )
            result.analysis_time_ms = (time.time() - start_time) * 1000
            return result

        if path.suffix != ".py":
            result.errors.append(
                AnalysisError(
                    message=f"El archivo {path} no es un archivo Python.",
                    severity=ErrorSeverity.CRITICAL,
                    component="file_analyzer",
                    file_path=str(path),
                )
            )
            result.analysis_time_ms = (time.time() - start_time) * 1000
            return result

        logger.debug(f"Analizando archivo: {path}")

        try:
            # Intentar análisis con Astroid
            detailed_module_entity: Optional[ModuleEntity] = None
            try:
                logger.debug(f"Intentando análisis con astroid para {path}")
                astroid_tree_root = self.parser.parse_with_astroid(
                    str(path)
                )
                astroid_visitor = AstroidNodeVisitor(
                    astroid_tree_root, str(path)
                )
                detailed_module_entity = astroid_visitor.analyze()

                if detailed_module_entity:
                    engine = self._ensure_metrics_engine()

                    # Métricas del módulo
                    result.module_metrics = engine.calculate_all_for_module(
                        detailed_module_entity
                    )

                    # Entidades (funciones y clases)
                    result.entities = engine.get_entities_from_module(
                        detailed_module_entity
                    )

                logger.debug(f"Análisis con astroid completado para {path}")

            except Exception as e_astroid:
                logger.warning(
                    f"No se pudo realizar análisis avanzado con astroid para {path}: {str(e_astroid)}. "
                    f"Utilizando AST estándar como alternativa."
                )
                result.errors.append(
                    AnalysisError(
                        message=f"Astroid analysis failed: {str(e_astroid)}",
                        severity=ErrorSeverity.WARNING,
                        component="astroid_parser",
                        file_path=str(path),
                    )
                )

                try:
                    ast_tree = self.parser.parse_file(str(path))
                    ast_visitor = ASTNodeVisitor()
                    ast_visitor.visit(ast_tree)
                    basic_metrics = ast_visitor.get_metrics()
                    result.basic_ast_data = basic_metrics
                except Exception as e_ast:
                    logger.error(
                        f"Fallback a AST estándar también falló para {path}: {str(e_ast)}"
                    )
                    result.errors.append(
                        AnalysisError(
                            message=f"AST fallback failed: {str(e_ast)}",
                            severity=ErrorSeverity.ERROR,
                            component="ast_parser",
                            file_path=str(path),
                        )
                    )

        except Exception as e_critical:
            logger.error(
                f"Error crítico al analizar {file_path}: {str(e_critical)}"
            )
            result.errors.append(
                AnalysisError(
                    message=f"Critical error: {str(e_critical)}",
                    severity=ErrorSeverity.CRITICAL,
                    component="file_analyzer",
                    file_path=str(path),
                )
            )

        result.analysis_time_ms = (time.time() - start_time) * 1000
        return result

    def analyze_project(
        self,
        path: Union[str, Path],
        config: Optional[Dict[str, Any]] = None,
    ) -> ProjectAnalysisResult:
        """Analiza un proyecto completo en la ruta especificada.

        Args:
            path: Ruta al directorio del proyecto
            config: Configuración opcional para el análisis

        Returns:
            ProjectAnalysisResult: Resultados completos del análisis.

        Raises:
            FileNotFoundError: Si la ruta no existe
            InvalidProjectError: Si la ruta no contiene archivos Python válidos
        """
        start_time = time.time()
        path_obj = Path(path)

        # Crear resultado del proyecto
        result = ProjectAnalysisResult(
            project_name=path_obj.name,
            root_path=path_obj,
            analysis_timestamp=datetime.now().isoformat(),
        )

        # Validaciones básicas
        if not path_obj.exists() or not path_obj.is_dir():
            error_msg = f"El directorio del proyecto {path_obj} no existe o no es un directorio."
            logger.error(error_msg)
            result.global_errors.append(
                AnalysisError(
                    message=error_msg,
                    severity=ErrorSeverity.CRITICAL,
                    component="project_analyzer",
                )
            )
            result.analysis_time_ms = (time.time() - start_time) * 1000
            return result

        logger.info(f"Analizando proyecto en: {path_obj}")

        project_config = config or self.config.get_all()
        try:
            project_manager = self.project_class(
                path=path_obj,
                file_processor=self.file_processor,
                ast_parser=self.parser,
                ignore_patterns=project_config.get("ignore_patterns"),
                max_file_size=project_config.get("max_file_size", 1024 * 1024),
            )
            if not project_manager.python_files:
                raise InvalidProjectError(
                    f"El directorio {path_obj} no contiene archivos Python válidos."
                )
        except InvalidProjectError as ipe:
            logger.error(str(ipe))
            result.global_errors.append(
                AnalysisError(
                    message=str(ipe),
                    severity=ErrorSeverity.CRITICAL,
                    component="project_manager",
                )
            )
            result.analysis_time_ms = (time.time() - start_time) * 1000
            return result
        except Exception as e_proj_init:
            error_msg = (
                f"Error al inicializar el gestor de proyecto: {e_proj_init}"
            )
            logger.error(error_msg)
            result.global_errors.append(
                AnalysisError(
                    message=error_msg,
                    severity=ErrorSeverity.CRITICAL,
                    component="project_manager",
                )
            )
            result.analysis_time_ms = (time.time() - start_time) * 1000
            return result

        # Procesar archivos
        processed_module_entities: List[ModuleEntity] = []
        file_iter = project_manager.python_files
        total_files = len(project_manager.python_files)
        result.total_files = total_files

        use_progress_bar = not project_config.get("no_progress_bar", False)
        progress_manager = get_progress_manager()

        with progress_manager.create_progress_bar(
            total=total_files,
            description="Analizando archivos del proyecto...",
            disable=not use_progress_bar,
        ) as progress_bar:
            for idx, file_path_obj in enumerate(file_iter):
                file_path_str = str(file_path_obj)

                # Actualizar descripción de la barra de progreso
                progress_bar.update(
                    0, description=f"Analizando: {file_path_obj.name}"
                )

                # Si no hay barra de progreso visual, logear el progreso periodicamente
                if not use_progress_bar:
                    if (
                        (idx + 1) % 10 == 0
                        or idx == total_files - 1
                        or total_files < 10
                    ):
                        logger.info(
                            f"Procesando archivo {idx+1}/{total_files}: {file_path_str}"
                        )

                file_analysis_result = self.analyze_file(
                    file_path_obj, project_config
                )
                result.files[file_path_str] = file_analysis_result

                if file_analysis_result.was_successful:
                    result.successful_files += 1
                    # Recopilar entidades de módulo para métricas de proyecto
                    # Necesitamos reconstruir la entidad del módulo si no está disponible
                    self._collect_module_entity(
                        file_path_obj,
                        file_analysis_result,
                        processed_module_entities,
                    )
                else:
                    result.failed_files += 1

                result.total_lines_of_code += file_analysis_result.line_count
                progress_bar.update(1)

        # Calcular métricas a nivel de proyecto si hay módulos procesados
        if processed_module_entities:
            try:
                project_entity = ProjectEntity(
                    name=path_obj.name,
                    root_path=path_obj,
                    modules=processed_module_entities,
                )
                engine = self._ensure_metrics_engine()
                result.project_metrics = engine.calculate_all_for_project(
                    project_entity
                )
            except Exception as e_proj_metrics:
                logger.error(
                    f"Error al calcular métricas a nivel de proyecto: {e_proj_metrics}"
                )
                result.global_errors.append(
                    AnalysisError(
                        message=f"Error calculando métricas de proyecto: {e_proj_metrics}",
                        severity=ErrorSeverity.WARNING,
                        component="project_metrics",
                    )
                )

        result.analysis_time_ms = (time.time() - start_time) * 1000
        return result

    def _collect_module_entity(
        self,
        file_path: Path,
        file_result: FileAnalysisResult,
        module_entities: List[ModuleEntity],
    ) -> None:
        """Recopila entidades de módulo para el análisis de proyecto."""
        try:
            # Intentar recrear la entidad del módulo usando Astroid
            astroid_tree_root = self.parser.parse_with_astroid(
                str(file_path)
            )
            astroid_visitor = AstroidNodeVisitor(
                astroid_tree_root, str(file_path)
            )
            module_entity = astroid_visitor.analyze()

            if module_entity:
                module_entities.append(module_entity)
        except Exception as e:
            logger.warning(
                f"No se pudo recopilar entidad de módulo para {file_path}: {e}"
            )

    def analyze(
        self, path: Union[str, Path], config: Optional[Dict[str, Any]] = None
    ) -> ProjectAnalysisResult:
        """Analiza la ruta especificada, que puede ser un archivo o directorio.

        Args:
            path: Ruta al archivo o directorio a analizar.
            config: Configuración opcional para el análisis.

        Returns:
            ProjectAnalysisResult: Resultados del análisis.

        Raises:
            FileNotFoundError: Si la ruta no existe o no es archivo/directorio.
        """
        path_obj = Path(path)

        if not path_obj.exists():
            # Crear resultado de error
            result = ProjectAnalysisResult(
                project_name="Unknown",
                root_path=path_obj,
                analysis_timestamp=datetime.now().isoformat(),
            )
            error_msg = f"La ruta {path_obj} no existe."
            logger.error(error_msg)
            result.global_errors.append(
                AnalysisError(
                    message=error_msg,
                    severity=ErrorSeverity.CRITICAL,
                    component="analyzer",
                )
            )
            return result

        current_config = config or self.config.get_all()

        if path_obj.is_file():
            # Análisis de archivo único - crear proyecto con un solo archivo
            result = ProjectAnalysisResult(
                project_name=path_obj.stem,
                root_path=path_obj.parent,
                analysis_timestamp=datetime.now().isoformat(),
                total_files=1,
            )

            file_result = self.analyze_file(path_obj, current_config)
            result.files[str(path_obj)] = file_result

            if file_result.was_successful:
                result.successful_files = 1
            else:
                result.failed_files = 1

            result.total_lines_of_code = file_result.line_count
            result.analysis_time_ms = file_result.analysis_time_ms

            return result
        elif path_obj.is_dir():
            return self.analyze_project(path_obj, current_config)
        else:
            # Crear resultado de error para tipos no soportados
            result = ProjectAnalysisResult(
                project_name="Unknown",
                root_path=path_obj,
                analysis_timestamp=datetime.now().isoformat(),
            )
            error_msg = (
                f"La ruta {path_obj} no es un archivo o directorio analizable."
            )
            logger.error(error_msg)
            result.global_errors.append(
                AnalysisError(
                    message=error_msg,
                    severity=ErrorSeverity.CRITICAL,
                    component="analyzer",
                )
            )
            return result
