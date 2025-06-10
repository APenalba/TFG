"""Motor de cálculo de métricas para análisis de código Python.

Este módulo implementa el motor principal que coordina el cálculo de métricas
sobre entidades de código. Actúa como intermediario entre el analizador y el
registro de métricas, proporcionando una API unificada para aplicar métricas.

Classes:
    MetricsEngine: Motor principal para cálculo de métricas

Note:
    El motor puede usar todas las métricas registradas o un subconjunto específico.
    Maneja automáticamente errores en métricas individuales sin afectar el análisis global.
"""

from typing import Dict, List, Optional, Union

from pypex.core.results import (
    AnalysisError,
    EntityAnalysisResult,
    ErrorSeverity,
    MetricsResult,
)
from pypex.metrics.base import IMetric
from pypex.metrics.registry import get_registry
from pypex.parser.code_entities import (
    Class,
    CodeEntity,
    Function,
    Module,
    Project,
)
from pypex.services.logging_service import get_logger

logger = get_logger(__name__)


class MetricsEngine:
    """Motor de cálculo de métricas para entidades de código Python.

    Esta clase coordina el cálculo de métricas aplicando automáticamente todas
    las métricas registradas o un subconjunto específico a las entidades de código.
    Proporciona una API unificada para el análisis de funciones, clases, módulos y proyectos.

    Attributes:
        registry: Registro de métricas disponibles
        specific_metrics: Lista opcional de métricas específicas a usar

    Example:
        >>> engine = MetricsEngine()
        >>> resultado = engine.calculate_all(mi_funcion)
        >>> print(resultado.metrics)
        
    Note:
        Los errores en métricas individuales se capturan y reportan sin detener
        el análisis completo. Las métricas que no aplican devuelven None.
    """

    def __init__(self, specific_metrics: Optional[List[IMetric]] = None):
        """Inicializa el motor de métricas.

        Args:
            specific_metrics: Lista opcional de métricas específicas a utilizar.
                Si no se proporciona, se usarán todas las métricas disponibles.
        """
        self.registry = get_registry()
        self.specific_metrics = specific_metrics
        logger.debug("Motor de métricas inicializado")

        # Registrar métricas específicas si se proporcionaron
        if specific_metrics:
            for metric in specific_metrics:
                try:
                    self.registry.register_metric(metric)
                    logger.debug(
                        f"Métrica '{metric.name}' registrada desde el motor"
                    )
                except ValueError:
                    # La métrica ya está registrada, ignoramos el error
                    pass

    def calculate_all(self, entity: CodeEntity) -> MetricsResult:
        """Calcula todas las métricas aplicables a una entidad.

        Args:
            entity: Entidad de código a analizar.

        Returns:
            MetricsResult: Resultado unificado de métricas para la entidad.
        """
        logger.debug(
            f"Calculando todas las métricas para la entidad: {entity.name} (Tipo: {type(entity).__name__})"
        )

        metrics_to_apply = (
            self.specific_metrics
            if self.specific_metrics
            else self.registry.get_all_metrics_instances()
        )
        metrics_dict: Dict[str, Union[float, Dict[str, float]]] = {}
        errors: List[AnalysisError] = []

        # Determinar el tipo de entidad
        entity_type = "unknown"
        if isinstance(entity, Function):
            entity_type = (
                "function"
                if not hasattr(entity, "is_method") or not entity.is_method
                else "method"
            )
        elif isinstance(entity, Class):
            entity_type = "class"
        elif isinstance(entity, Module):
            entity_type = "module"
        elif isinstance(entity, Project):
            entity_type = "project"

        for metric in metrics_to_apply:
            try:
                # IMetric.calculate ahora devuelve Union[float, Dict[str, float], None]
                result = metric.calculate(entity)

                # Solo incluir métricas que devuelven valores (no None)
                if result is not None:
                    metrics_dict[metric.name] = result
                else:
                    logger.debug(
                        f"Métrica '{metric.name}' no aplica a {entity_type}: {entity.name}"
                    )

            except Exception as e:
                logger.warning(
                    f"Error al calcular métrica '{metric.name}' para {entity.name}: {str(e)}"
                )
                errors.append(
                    AnalysisError(
                        message=f"Error calculando {metric.name}: {str(e)}",
                        severity=ErrorSeverity.WARNING,
                        component="metrics_engine",
                    )
                )
                # No agregamos valores de fallback para errores

        return MetricsResult(
            entity_name=entity.name,
            entity_type=entity_type,
            metrics=metrics_dict,
            errors=errors,
        )

    def calculate_all_for_function(self, function: Function) -> MetricsResult:
        """Calcula todas las métricas aplicables a una función.

        Args:
            function: Función a analizar.

        Returns:
            MetricsResult: Resultado unificado de métricas para la función.
        """
        logger.debug(f"Calculando métricas para función: {function.name}")
        return self.calculate_all(function)

    def calculate_all_for_class(self, cls: Class) -> EntityAnalysisResult:
        """Calcula todas las métricas aplicables a una clase y sus métodos.

        Args:
            cls: Clase a analizar.

        Returns:
            EntityAnalysisResult: Resultado completo del análisis de la clase.
        """
        logger.debug(f"Calculando métricas para clase: {cls.name}")

        # Métricas de la definición de la clase
        class_metrics = self.calculate_all(cls)

        # Crear resultado de entidad
        class_result = EntityAnalysisResult(
            name=cls.name, entity_type="class", metrics=class_metrics
        )

        # Calcular métricas para cada método
        for method in cls.methods:
            method_metrics = self.calculate_all(method)
            method_result = EntityAnalysisResult(
                name=method.name, entity_type="method", metrics=method_metrics
            )
            class_result.children.append(method_result)

        return class_result

    def calculate_all_for_module(self, module: Module) -> MetricsResult:
        """Calcula todas las métricas aplicables a un módulo.

        Args:
            module: Módulo a analizar.

        Returns:
            MetricsResult: Resultado unificado de métricas para el módulo.
        """
        logger.debug(f"Calculando métricas para módulo: {module.name}")
        return self.calculate_all(module)

    def calculate_all_for_project(self, project: Project) -> MetricsResult:
        """Calcula todas las métricas aplicables a un proyecto.

        Args:
            project: Proyecto a analizar.

        Returns:
            MetricsResult: Resultado unificado de métricas para el proyecto.
        """
        logger.debug(f"Calculando métricas para proyecto: {project.name}")

        metrics_dict: Dict[str, Union[float, Dict[str, float]]] = {}
        errors: List[AnalysisError] = []
        metrics_to_apply = (
            self.specific_metrics
            if self.specific_metrics
            else self.registry.get_all_metrics_instances()
        )

        for metric in metrics_to_apply:
            try:
                # Usar metric.calculate_project() que devuelve Optional[Dict[str, float]]
                project_result = metric.calculate_project(project)

                # Solo incluir métricas que devuelven valores (no None)
                if project_result is not None:
                    metrics_dict[metric.name] = project_result
                else:
                    logger.debug(
                        f"Métrica '{metric.name}' no aplica a proyecto: {project.name}"
                    )

            except Exception as e:
                logger.warning(
                    f"Error al calcular métrica de proyecto '{metric.name}' para el proyecto {project.name}: {str(e)}"
                )
                errors.append(
                    AnalysisError(
                        message=f"Error calculando métrica de proyecto {metric.name}: {str(e)}",
                        severity=ErrorSeverity.WARNING,
                        component="metrics_engine",
                    )
                )
                # No agregamos valores de fallback para errores

        return MetricsResult(
            entity_name=project.name,
            entity_type="project",
            metrics=metrics_dict,
            errors=errors,
        )

    def get_entities_from_module(
        self, module: Module
    ) -> List[EntityAnalysisResult]:
        """Extrae entidades (funciones y clases) de un módulo con sus métricas.

        Args:
            module: Módulo a procesar.

        Returns:
            List[EntityAnalysisResult]: Lista de entidades analizadas.
        """
        entities: List[EntityAnalysisResult] = []

        # Procesar funciones a nivel de módulo
        for func in module.functions:
            func_metrics = self.calculate_all(func)
            func_result = EntityAnalysisResult(
                name=func.name, entity_type="function", metrics=func_metrics
            )
            entities.append(func_result)

        # Procesar clases en el módulo
        for cls in module.classes:
            class_result = self.calculate_all_for_class(cls)
            entities.append(class_result)

        return entities

    def get_metrics_info(self) -> Dict[str, Dict]:
        """Obtiene información sobre todas las métricas disponibles (descripción, umbrales).

        Returns:
            Dict: Diccionario con información sobre las métricas disponibles.
        """
        metrics_info = {}
        available_metric_names = self.registry.get_available_metrics()

        for metric_name in available_metric_names:
            try:
                metric = self.registry.get_metric(metric_name)
                metrics_info[metric_name] = {
                    "name": metric.name,
                    "description": metric.description,
                    "thresholds": getattr(metric, "thresholds", {}),
                }
            except Exception as e:
                logger.warning(
                    f"No se pudo obtener información de la métrica '{metric_name}': {str(e)}"
                )

        return metrics_info
