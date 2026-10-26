"""Registro centralizado de métricas disponibles en el sistema PyPex.

Este módulo implementa un registro singleton que gestiona todas las métricas
disponibles del sistema. Proporciona funcionalidades para registro manual,
descoberta automática y acceso a las métricas registradas.

Classes:
    MetricsRegistry: Registro singleton de métricas disponibles

Functions:
    get_registry: Obtiene la instancia singleton del registro

Note:
    El registro implementa el patrón Singleton para garantizar un único punto
    de acceso a las métricas en toda la aplicación.
"""

import importlib
import inspect
import pkgutil

from pypex.metrics.base import IMetric, MetricNotFoundError
from pypex.parser.code_entities import CodeEntity, Project
from pypex.services.logging_service import get_logger

logger = get_logger(__name__)


class MetricsRegistry:
    """Registro singleton para gestión centralizada de métricas del sistema.

    Esta clase implementa un registro único que mantiene todas las métricas
    disponibles del sistema. Proporciona funcionalidades para registro manual,
    descoberta automática de métricas en paquetes y aplicación de métricas a entidades.

    Attributes:
        _metrics: Diccionario de métricas registradas por nombre
        _initialized: Flag para control de inicialización singleton

    Example:
        >>> registry = get_registry()
        >>> registry.register_metric(MiMetrica())
        >>> metrica = registry.get_metric("mi_metrica")
        >>> resultados = registry.apply_all(mi_entidad)

    Note:
        El patrón Singleton garantiza que todas las partes del sistema
        accedan al mismo registro de métricas.
    """

    _instance = None  # Para patrón Singleton

    def __new__(cls):
        """Implementa patrón Singleton para tener un único registro global."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Inicializa el registro de métricas."""
        if not getattr(self, "_initialized", False):
            self._metrics: dict[str, IMetric] = {}
            self._initialized = True
            logger.debug("Registro de métricas inicializado")

    def register_metric(self, metric: IMetric) -> None:
        """Registra una métrica en el sistema.

        Args:
            metric: Métrica a registrar.

        Raises:
            ValueError: Si ya existe una métrica con el mismo nombre.
        """
        if metric.name in self._metrics:
            # Permitir el re-registro si es la misma instancia (útil para el motor)
            if self._metrics[metric.name] is metric:
                logger.debug(
                    f"Métrica '{metric.name}' ya registrada con la misma instancia. Omitiendo."
                )
                return
            raise ValueError(f"Ya existe una métrica con el nombre '{metric.name}'")

        self._metrics[metric.name] = metric
        logger.debug(f"Métrica '{metric.name}' registrada")

    def get_metric(self, name: str) -> IMetric:
        """Obtiene una métrica por su nombre.

        Args:
            name: Nombre de la métrica.

        Returns:
            IMetric: Métrica solicitada.

        Raises:
            MetricNotFoundError: Si la métrica no existe.
        """
        if name not in self._metrics:
            raise MetricNotFoundError(f"No existe una métrica con el nombre '{name}'")

        return self._metrics[name]

    def get_available_metrics(self) -> list[str]:
        """Obtiene los nombres de todas las métricas disponibles.

        Returns:
            List[str]: Lista de nombres de métricas.
        """
        return list(self._metrics.keys())

    def get_all_metrics_instances(self) -> list[IMetric]:
        """Obtiene todas las instancias de métricas registradas.

        Returns:
            List[IMetric]: Lista de instancias de métricas.
        """
        return list(self._metrics.values())

    def apply_all(self, entity: CodeEntity) -> dict[str, float | dict[str, float]]:
        """Aplica todas las métricas registradas a una entidad.

        Llama a metric.calculate(entity) para cada métrica registrada.

        Args:
            entity: Entidad de código.

        Returns:
            Dict[str, Union[float, Dict[str, float]]]: Diccionario con nombres de métricas y sus valores/componentes.
        """
        results: dict[str, float | dict[str, float]] = {}
        for name, metric in self._metrics.items():
            try:
                results[name] = metric.calculate(entity)
            except Exception as e:
                logger.warning(
                    f"Error al aplicar la métrica '{name}' a la entidad {entity.name}: {str(e)}"
                )
                results[name] = -1.0  # Opcional: o None, o un dict de error

        return results

    def apply_project_level_metrics(self, project: Project) -> dict[str, dict[str, float]]:
        """Aplica el método `calculate_project` de cada métrica registrada a un proyecto.

        Args:
            project: Proyecto a analizar.

        Returns:
            Dict[str, Dict[str, float]]: Diccionario con nombres de métricas y los componentes
                                         que cada una calcula para el proyecto.
        """
        results: dict[str, dict[str, float]] = {}
        for metric_name, metric in self._metrics.items():
            try:
                # metric.calculate_project devuelve Dict[str, float]
                results[metric_name] = metric.calculate_project(project)
            except Exception as e:
                logger.warning(
                    f"Error al aplicar métrica de proyecto '{metric_name}' al proyecto {project.name}: {str(e)}"
                )
                results[metric_name] = {"error": -1.0}  # O un valor que indique error
        return results

    def discover_metrics(self, package_name: str = "pypex.metrics") -> None:
        """Descubre automáticamente métricas en los subpaquetes.

        Args:
            package_name: Nombre del paquete a explorar.
        """
        logger.debug(f"Descubriendo métricas en '{package_name}'")

        try:
            package = importlib.import_module(package_name)

            for _, name, is_pkg in pkgutil.iter_modules(package.__path__, package.__name__ + "."):
                if is_pkg:
                    # Recursivamente explorar subpaquetes
                    self.discover_metrics(name)
                else:
                    try:
                        module = importlib.import_module(name)
                        # Buscar clases que implementen IMetric
                        for member_name, obj in inspect.getmembers(module):
                            if (
                                inspect.isclass(obj)
                                and issubclass(obj, IMetric)
                                and obj.__module__ == module.__name__
                                and obj is not IMetric
                                and not inspect.isabstract(obj)  # Ignorar clases abstractas
                            ):
                                # Instanciar la métrica y registrarla
                                try:
                                    metric = obj()
                                    self.register_metric(metric)
                                except Exception as e:
                                    logger.warning(
                                        f"Error al instanciar o registrar métrica descubierta {obj.__name__}: {str(e)}"
                                    )
                    except ImportError as e:
                        logger.warning(
                            f"Error al importar el módulo de métricas {name} para descubrimiento: {str(e)}"
                        )
                    except Exception as e:
                        logger.error(
                            f"Error inesperado al procesar el módulo {name} para descubrimiento de métricas: {str(e)}"
                        )

        except ImportError as e:
            logger.error(
                f"No se pudo importar el paquete de métricas base '{package_name}' para descubrimiento: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Error general al descubrir métricas en '{package_name}': {str(e)}")


# Singleton para acceso global
def get_registry() -> MetricsRegistry:
    """Obtiene la instancia global del registro de métricas.

    Returns:
        MetricsRegistry: Instancia del registro.
    """
    registry = MetricsRegistry()

    # Auto-registrar métricas por defecto la primera vez
    if not hasattr(registry, "_auto_registered") or not registry._auto_registered:
        _register_default_metrics(registry)
        registry._auto_registered = True

    return registry


def _register_default_metrics(registry: MetricsRegistry) -> None:
    """Registra las métricas por defecto del sistema.

    Args:
        registry: Instancia del registro donde registrar las métricas.
    """
    # Importar localmente para evitar ciclos de importación
    try:
        from pypex.metrics.cohesion.lcom4 import LCOM4
        from pypex.metrics.complexity.cognitive import CognitiveComplexity
        from pypex.metrics.complexity.comprehension_complexity import (
            ComprehensionComplexityMetric,
        )
        from pypex.metrics.complexity.cyclomatic import CyclomaticComplexity
        from pypex.metrics.complexity.essential_complexity import (
            EssentialComplexityMetric,
        )
        from pypex.metrics.complexity.exception_handling_complexity import (
            ExceptionHandlingComplexityMetric,
        )
        from pypex.metrics.complexity.generator_complexity import (
            GeneratorComplexityMetric,
        )
        from pypex.metrics.complexity.halstead import HalsteadMetric
        from pypex.metrics.complexity.logical_complexity import LogicalComplexityMetric
        from pypex.metrics.complexity.nested_comprehension_depth import (
            NestedComprehensionDepthMetric,
        )
        from pypex.metrics.complexity.nesting_depth import NestingDepth
        from pypex.metrics.coupling.advanced_coupling import AdvancedCouplingMetric
        from pypex.metrics.coupling.fan_in_out import FanInOutMetric
        from pypex.metrics.design.design_complexity import DesignComplexityMetric
        from pypex.metrics.size.lines_of_code import LinesOfCodeMetric
        from pypex.metrics.size.parameter_count import ParameterCountMetric

        registry.register_metric(CyclomaticComplexity())
        registry.register_metric(CognitiveComplexity())
        registry.register_metric(NestingDepth())
        registry.register_metric(EssentialComplexityMetric())
        registry.register_metric(LogicalComplexityMetric())
        registry.register_metric(ComprehensionComplexityMetric())
        registry.register_metric(NestedComprehensionDepthMetric())
        registry.register_metric(ExceptionHandlingComplexityMetric())
        registry.register_metric(GeneratorComplexityMetric())
        registry.register_metric(HalsteadMetric())
        registry.register_metric(DesignComplexityMetric())
        registry.register_metric(LCOM4())
        registry.register_metric(FanInOutMetric())
        registry.register_metric(AdvancedCouplingMetric())
        registry.register_metric(LinesOfCodeMetric())
        registry.register_metric(ParameterCountMetric())

        logger.debug("Métricas por defecto registradas automáticamente")

    except Exception as e:
        logger.warning(f"Error registrando métricas por defecto: {e}")
