"""Módulo para calcular la métrica de complejidad de generadores."""

from typing import Dict

from pypex.metrics.base import BaseMetric
from pypex.parser.code_entities import Class, Function, Module, Project
from pypex.services.logging_service import get_logger

logger = get_logger(__name__)


class GeneratorComplexityMetric(BaseMetric):
    """Calcula la complejidad de generadores basada en expresiones yield.

    ## ¿Qué es la Complejidad de Generadores?

    Esta métrica mide la complejidad de las funciones generadoras en Python,
    basada en el número de expresiones yield y yield from. Los generadores son
    una característica poderosa de Python para crear iteradores eficientes,
    pero pueden volverse complejos cuando contienen múltiples puntos de yield
    o lógica de control compleja.

    ### Tipos de Expresiones Yield:
    - **yield value**: Produce un valor y pausa la ejecución
    - **yield from iterable**: Delega a otro iterador/generador
    - **yield (expression)**: Puede incluir expresiones complejas
    - **yield in loops**: Múltiples yields en estructuras repetitivas
    - **yield with conditions**: Yields condicionales

    ### Factores de Complejidad:
    - **Número de yields**: Cada yield incrementa puntos de control
    - **yield from**: Delegación a otros generadores
    - **Yields en bucles**: Múltiples puntos de producción
    - **Estado del generador**: Manejo de variables entre yields
    - **Lógica condicional**: Yields en diferentes ramas de código

    ## ¿Cómo se calcula?

    ### Fórmula:
    Generator Complexity = yield_expressions_count

    ### Elementos que contribuyen:
    - **yield_expressions_count**: Número total de expresiones yield/yield from
    - **Cada yield/yield from cuenta como 1**: Sin diferenciación de tipo
    - **Se cuentan todos los yields**: Independiente de la lógica de control

    ## Interpretación de valores:

    - **0**: Función regular, no es un generador
    - **1-2**: Generador simple, fácil de entender
    - **3-5**: Generador moderado, revisar lógica
    - **6+**: Generador complejo, considerar refactoring

    ## Ejemplo de cálculo:

    ```python
    def regular_function():  # Generator = 0
        return [1, 2, 3]

    def simple_generator():  # Generator = 1
        yield 1            # +1

    def moderate_generator():  # Generator = 3
        yield 1            # +1
        yield 2            # +1
        yield 3            # +1

    def complex_generator():  # Generator = 6
        for i in range(3):
            yield i        # +1 (x3 en el bucle)
        yield from [4, 5]  # +1 (yield from)
        if condition:
            yield 6        # +1
            yield 7        # +1
    ```

    ## Cuándo es Problemático:
    - **Demasiados yields**: Más de 5-6 yields en una función
    - **Lógica compleja**: Yields en múltiples ramas condicionales
    - **Estado compartido**: Variables que cambian entre yields
    - **yield from anidado**: Delegación profunda a otros generadores
    - **Difícil de testear**: Múltiples estados del generador

    ## Beneficios de la Métrica:
    - **Evalúa complejidad**: Identifica generadores difíciles de entender
    - **Mejora mantenibilidad**: Generadores simples son más fáciles de mantener
    - **Facilita testing**: Pocos yields = menos estados a testear
    - **Optimización**: Generadores complejos pueden necesitar optimización
    - **Documentación**: Indica dónde se necesita más documentación

    ## Mejores Prácticas para Generadores:
    - **Single Responsibility**: Un generador, una responsabilidad
    - **Pocos yields**: Mantener número de yields bajo
    - **Estado mínimo**: Minimizar variables entre yields
    - **Documentación**: Documentar comportamiento de yields múltiples
    - **Testing exhaustivo**: Testear todos los paths de yield

    ## Cuándo Refactorizar:
    - **6+ yields**: Considerar dividir en múltiples generadores
    - **Lógica compleja**: Extraer lógica a funciones auxiliares
    - **yield from múltiple**: Simplificar delegación
    - **Estado compartido**: Minimizar variables mutables

    ## Referencias:
    - PEP 255 - Simple Generators
    - PEP 342 - Coroutines via Enhanced Generators
    - PEP 380 - Syntax for Delegating to a Subgenerator (yield from)
    - "Effective Python" by Brett Slatkin - Generator Guidelines
    - "Fluent Python" by Luciano Ramalho - Generator Patterns
    """

    def __init__(self):
        """Inicializa el calculador de complejidad de generadores."""
        super().__init__(
            name="generator_complexity",
            description="Mide la complejidad de generadores basada en expresiones yield.",
        )

    def get_default_thresholds(self) -> Dict[str, float]:
        """Obtiene los umbrales por defecto para generator_complexity.
        
        Basado en complejidad de generadores y yield.
        
        Returns:
            Dict[str, float]: Umbrales por defecto {low, medium, high}.
        """
        return {
            "low": 1.0,
            "medium": 3.0,
            "high": 6.0,
        }


    def calculate_function(self, function: Function) -> float:
        """Calcula la complejidad de generador de una función."""
        logger.debug(
            f"Calculando complejidad de generador para función: {function.name}"
        )

        return float(function.yield_expressions_count)

    def calculate_class(self, cls: Class) -> Dict[str, float]:
        """Calcula estadísticas de complejidad de generador para una clase."""
        logger.debug(
            f"Calculando complejidad de generador para clase: {cls.name}"
        )

        if not cls.methods:
            return {
                "average": 0.0,
                "max": 0.0,
                "method_count": 0.0,
                "generator_methods": 0.0,
            }

        method_yields = []

        for method in cls.methods:
            method_yield = self.calculate_function(method)
            method_yields.append(method_yield)

        result = {
            "average": sum(method_yields) / len(method_yields),
            "max": max(method_yields),
            "method_count": float(len(cls.methods)),
            "generator_methods": len([y for y in method_yields if y > 0]),
        }

        return result

    def calculate_module(self, module: Module) -> None:
        """La complejidad de generador no se calcula a nivel de módulo."""
        logger.debug(
            f"Complejidad de generador no aplica a módulo: {module.name} - devolviendo None"
        )
        return None

    def calculate_project(self, project: Project) -> None:
        """La complejidad de generador no se calcula a nivel de proyecto."""
        logger.debug(
            f"Complejidad de generador no aplica a proyecto: {project.name} - devolviendo None"
        )
        return None
