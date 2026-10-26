"""Definición de interfaces y clases base para el sistema de métricas PyPex.

Este módulo define la interfaz IMetric y la clase base BaseMetric que deben
ser implementadas por todas las métricas del sistema. Proporciona funcionalidad
común como cálculo automático por tipo de entidad y manejo de umbrales.

Interfaces:
    IMetric: Contrato principal para todas las métricas

Classes:
    BaseMetric: Implementación base con funcionalidad común

Exceptions:
    MetricError: Excepción base para errores en métricas
    MetricNotFoundError: Métrica solicitada no encontrada
    InvalidEntityError: Tipo de entidad no soportado

Note:
    Todas las métricas deben heredar de BaseMetric o implementar IMetric directamente.
    El sistema soporta métricas simples (float) y compuestas (Dict[str, float]).
"""

from abc import ABC, abstractmethod

from pypex.metrics.thresholds import get_threshold_config
from pypex.parser.code_entities import (
    Class,
    CodeEntity,
    Function,
    Module,
    Project,
)
from pypex.services.logging_service import get_logger

logger = get_logger(__name__)


class MetricError(Exception):
    """Excepción base para errores en métricas."""


class MetricNotFoundError(MetricError):
    """Se lanza cuando se solicita una métrica que no existe."""


class InvalidEntityError(MetricError):
    """Se lanza cuando se intenta aplicar una métrica a un tipo de entidad no soportado."""


class IMetric(ABC):
    """Interfaz base para todas las métricas de complejidad de código.

    Define el contrato que deben implementar todas las métricas del sistema.
    Soporta cálculo específico por tipo de entidad (función, clase, módulo, proyecto)
    y proporciona funcionalidades para interpretación y manejo de umbrales.

    Methods:
        calculate: Calcula la métrica para cualquier entidad
        calculate_function: Calcula para funciones específicamente
        calculate_class: Calcula para definiciones de clase
        calculate_module: Calcula para definiciones de módulo
        calculate_project: Calcula para proyectos completos
        get_thresholds: Obtiene umbrales configurados
        interpret: Interpreta valores usando umbrales
        get_aggregated_value: Obtiene valor simple para comparación
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Obtiene el nombre único de la métrica.

        Returns:
            str: Nombre de la métrica.
        """

    @property
    @abstractmethod
    def description(self) -> str:
        """Obtiene la descripción de la métrica.

        Returns:
            str: Descripción de la métrica.
        """

    @abstractmethod
    def calculate(self, entity: CodeEntity) -> float | dict[str, float] | None:
        """Calcula la métrica para una entidad de código.

        Args:
            entity: Entidad de código a analizar.

        Returns:
            Union[float, Dict[str, float], None]: Valor numérico de la métrica,
                                                 diccionario de componentes si la métrica es compuesta,
                                                 o None si la métrica no aplica para este tipo de entidad.

        Raises:
            InvalidEntityError: Si la entidad no es de un tipo soportado.
        """

    @abstractmethod
    def calculate_function(self, function: Function) -> float | None:
        """Calcula la métrica para una función.

        Args:
            function: Función a analizar.

        Returns:
            Optional[float]: Valor numérico de la métrica, o None si no aplica.
        """

    @abstractmethod
    def calculate_class(self, cls: Class) -> dict[str, float] | None:
        """Calcula la métrica para la *definición* de una clase.

        Los métodos dentro de la clase son manejados por el MetricsEngine.
        Este método debe devolver componentes de la métrica específicos de la
        estructura de la clase en sí (ej: herencia, atributos, decoradores de clase).

        Args:
            cls: Clase a analizar.

        Returns:
            Optional[Dict[str, float]]: Componentes de la métrica para la definición de la clase,
                                       o None si la métrica no aplica a definiciones de clase.
        """

    @abstractmethod
    def calculate_module(self, module: Module) -> dict[str, float] | None:
        """Calcula la métrica para la *definición* de un módulo.

        Funciones y clases dentro del módulo son manejados por el MetricsEngine.
        Este método debe devolver componentes de la métrica específicos del
        código a nivel de módulo (ej: imports, variables globales, complejidad de
        scripts a nivel de módulo si aplica).

        Args:
            module: Módulo a analizar.

        Returns:
            Optional[Dict[str, float]]: Componentes de la métrica para la definición del módulo,
                                       o None si la métrica no aplica a definiciones de módulo.
        """

    @abstractmethod
    def calculate_project(self, project: Project) -> dict[str, float] | None:
        """Calcula la métrica a nivel de proyecto.

        Esto es para componentes de la métrica que son inherentes al proyecto
        en su totalidad, no simplemente una agregación de sus partes (lo cual
        puede hacerse externamente con los resultados de otras entidades).

        Args:
            project: Proyecto a analizar.

        Returns:
            Optional[Dict[str, float]]: Componentes de la métrica para el proyecto,
                                       o None si la métrica no aplica a nivel de proyecto.
        """

    @abstractmethod
    def get_thresholds(self) -> dict[str, float]:
        """Obtiene los umbrales para interpretar la métrica desde ThresholdConfig."""
        return get_threshold_config().get_thresholds(self.name)

    @abstractmethod
    def get_default_thresholds(self) -> dict[str, float]:
        """Obtiene los umbrales por defecto específicos de esta métrica.

        Cada métrica debe definir sus propios umbrales por defecto basados
        en investigación y mejores prácticas para esa métrica específica.

        Returns:
            Dict[str, float]: Diccionario con umbrales por defecto (low, medium, high).
        """

    @abstractmethod
    def interpret(self, value: float) -> str:
        """Interpreta un valor de la métrica utilizando ThresholdConfig."""
        return get_threshold_config().interpret_value(self.name, value).value

    def get_aggregated_value(self, entity: CodeEntity) -> float:
        """Obtiene un valor agregado simple para usar con thresholds.

        Para métricas que devuelven diccionarios complejos, este método
        debe devolver un valor numérico simple que represente la métrica
        de forma agregada para su uso con umbrales.

        Si la métrica devuelve None (no aplica), devuelve 0.0.

        Args:
            entity: Entidad de código a analizar.

        Returns:
            float: Valor numérico agregado.
        """
        result = self.calculate(entity)

        # Si la métrica no aplica, devolver 0
        if result is None:
            return 0.0

        # Si la métrica devuelve un valor simple, usarlo directamente
        if isinstance(result, (int, float)):
            return float(result)

        # Si es un diccionario, buscar valor total o suma
        if isinstance(result, dict):
            # Buscar claves comunes para valores agregados
            for key in ["total", "sum", "aggregate", "value"]:
                if key in result:
                    return float(result[key])

            # Si no hay clave obvia, sumar valores numéricos
            numeric_values = [v for v in result.values() if isinstance(v, (int, float))]
            if numeric_values:
                return sum(numeric_values)

        # Fallback: devolver 0 si no se puede obtener valor agregado
        logger.warning(
            f"No se pudo obtener un valor agregado para la métrica {self.name} en {entity.name}"
        )
        return 0.0


class BaseMetric(IMetric):
    """Implementación base para métricas con funcionalidad común predefinida.

    Esta clase proporciona una implementación común de la interfaz IMetric,
    incluyendo dispatching automático por tipo de entidad, manejo de umbrales
    y funcionalidades de interpretación. Las métricas concretas solo necesitan
    implementar los métodos específicos de cálculo.

    Attributes:
        _name: Nombre único de la métrica
        _description: Descripción de la métrica

    Example:
        >>> class MiMetrica(BaseMetric):
        ...     def calculate_function(self, function):
        ...         return len(function.parameters)
        >>> metrica = MiMetrica("params", "Cuenta parámetros")
        >>> valor = metrica.calculate(mi_funcion)

    Note:
        Los métodos calculate_* deben devolver None si la métrica no aplica
        al tipo de entidad específico.
    """

    def __init__(self, name: str, description: str):
        """Inicializa la métrica base.

        Args:
            name: Nombre único de la métrica.
            description: Descripción de la métrica.
        """
        self._name = name
        self._description = description
        logger.debug(f"Inicializando métrica {name}")

    @property
    def name(self) -> str:
        """Obtiene el nombre único de la métrica.

        Returns:
            str: Nombre de la métrica.
        """
        return self._name

    @property
    def description(self) -> str:
        """Obtiene la descripción de la métrica.

        Returns:
            str: Descripción de la métrica.
        """
        return self._description

    def calculate(self, entity: CodeEntity) -> float | dict[str, float] | None:
        """Calcula la métrica para una entidad de código.

        Delega a los métodos calculate_X específicos según el tipo de entidad.
        Devuelve un float para funciones, un Dict[str, float] para clases,
        módulos y proyectos, o None si la métrica no aplica al tipo de entidad.

        Args:
            entity: Entidad de código a analizar.

        Returns:
            Union[float, Dict[str, float], None]: Valor o componentes de la métrica,
                                                 o None si no aplica.

        Raises:
            InvalidEntityError: Si la entidad no es de un tipo soportado o si
                                se intenta calcular un Proyecto genéricamente.
        """
        logger.debug(f"Calculando métrica {self.name} para entidad {entity.name}")
        if isinstance(entity, Function):
            return self.calculate_function(entity)
        elif isinstance(entity, Class):
            return self.calculate_class(entity)
        elif isinstance(entity, Module):
            return self.calculate_module(entity)
        elif isinstance(entity, Project):
            logger.error(
                f"Intento de calcular métrica {self.name} para Project usando método genérico"
            )
            raise InvalidEntityError(
                f"Para entidades Project ({entity.name}), utilice el método 'calculate_project' "
                f"específico de la métrica '{self.name}'. El método 'calculate' genérico "
                f"no está destinado a entidades Project."
            )
        else:
            logger.error(f"Tipo de entidad no soportado: {type(entity).__name__}")
            raise InvalidEntityError(
                f"El tipo de entidad {type(entity).__name__} no está soportado por el "
                f"método 'calculate' genérico de la métrica '{self.name}'."
            )

    def calculate_function(self, function: Function) -> float | None:
        """Método base para calcular métrica en función.

        Por defecto devuelve None indicando que la métrica no se implementa
        para funciones en esta métrica específica.
        """
        logger.debug(
            f"Métrica '{self.name}' no implementa 'calculate_function' - devolviendo None para función: {function.name}"
        )
        return None

    def calculate_class(self, cls: Class) -> dict[str, float] | None:
        """Método base para calcular métrica en clase.

        Por defecto devuelve None indicando que la métrica no se implementa
        para clases en esta métrica específica.
        """
        logger.debug(
            f"Métrica '{self.name}' no implementa 'calculate_class' - devolviendo None para clase: {cls.name}"
        )
        return None

    def calculate_module(self, module: Module) -> dict[str, float] | None:
        """Método base para calcular métrica en módulo.

        Por defecto devuelve None indicando que la métrica no se implementa
        para módulos en esta métrica específica.
        """
        logger.debug(
            f"Métrica '{self.name}' no implementa 'calculate_module' - devolviendo None para módulo: {module.name}"
        )
        return None

    def calculate_project(self, project: Project) -> dict[str, float] | None:
        """Método base para calcular métrica en proyecto.

        Por defecto devuelve None indicando que la métrica no se implementa
        para proyectos en esta métrica específica.
        """
        logger.debug(
            f"Métrica '{self.name}' no implementa 'calculate_project' - devolviendo None para proyecto: {project.name}"
        )
        return None

    def get_thresholds(self) -> dict[str, float]:
        """Obtiene los umbrales para interpretar la métrica desde ThresholdConfig."""
        return get_threshold_config().get_thresholds(self.name)

    def get_default_thresholds(self) -> dict[str, float]:
        """Obtiene los umbrales por defecto específicos de esta métrica.

        Implementación por defecto que devuelve umbrales genéricos.
        Las métricas específicas deben sobreescribir este método con
        umbrales basados en investigación y mejores prácticas.

        Returns:
            Dict[str, float]: Diccionario con umbrales genéricos por defecto.
        """
        logger.warning(
            f"Métrica '{self.name}' usando umbrales genéricos. "
            f"Considere implementar get_default_thresholds() específicos."
        )
        return {"low": 5.0, "medium": 10.0, "high": 15.0}

    def interpret(self, value: float) -> str:
        """Interpreta un valor de la métrica utilizando ThresholdConfig."""
        return get_threshold_config().interpret_value(self.name, value).value
