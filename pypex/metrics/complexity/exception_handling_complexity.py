"""Módulo para calcular la métrica de complejidad de manejo de excepciones."""

from typing import Dict

from pypex.metrics.base import BaseMetric
from pypex.parser.code_entities import Class, Function, Module, Project
from pypex.services.logging_service import get_logger

logger = get_logger(__name__)


class ExceptionHandlingComplexityMetric(BaseMetric):
    """Calcula la complejidad de manejo de excepciones.

    ## ¿Qué es la Complejidad de Manejo de Excepciones?

    Esta métrica mide la complejidad del manejo de excepciones en el código Python.
    El manejo de excepciones es crucial para la robustez del software, pero cuando
    se vuelve excesivamente complejo puede indicar problemas de diseño o lógica
    de error demasiado intrincada.

    ### Elementos que Contribuyen:
    - **Bloques try**: Cada bloque try-except incrementa complejidad
    - **Handlers except**: Cada cláusula except individual añade complejidad
    - **Anidamiento**: try-except dentro de otros try-except
    - **Múltiples excepciones**: except que manejan múltiples tipos

    ### Tipos de Manejo de Excepciones:
    - **Try-Except básico**: try/except simple
    - **Try-Except-Finally**: Con limpieza garantizada
    - **Try-Except-Else**: Ejecución cuando no hay excepciones
    - **Múltiples except**: Diferentes handlers para diferentes excepciones
    - **Exception chaining**: raise...from para mantener contexto
    - **Context managers**: with statements (manejo implícito)

    ## ¿Cómo se calcula?

    ### Fórmula:
    Exception Complexity = exception_handlers_count + try_blocks_count

    ### Elementos que contribuyen:
    - **exception_handlers_count**: Número de cláusulas except
    - **try_blocks_count**: Número de bloques try
    - **Se suman ambos**: Cada elemento añade al total

    ## Interpretación de valores:

    - **0**: Sin manejo de excepciones (puede ser problemático)
    - **1-2**: Manejo básico y apropiado
    - **3-5**: Manejo moderado, revisar si es necesario
    - **6+**: Manejo complejo, considerar refactoring

    ## Ejemplo de cálculo:

    ```python
    def ejemplo_sin_excepciones():  # Exception = 0
        return "hello world"

    def ejemplo_basico():  # Exception = 2
        try:                    # +1 (try block)
            return risky_operation()
        except ValueError:      # +1 (exception handler)
            return None

    def ejemplo_complejo():  # Exception = 5
        try:                    # +1 (try block)
            try:                # +1 (nested try block)
                result = operation1()
            except TypeError:   # +1 (exception handler)
                result = fallback()

            process(result)
        except ValueError:      # +1 (exception handler)
            log_error()
        except Exception:       # +1 (exception handler)
            handle_all()
    ```

    ## Cuándo es Problemático:
    - **Demasiados handlers**: Más de 3-4 except en una función
    - **Anidamiento profundo**: try-except dentro de try-except
    - **Catch-all genérico**: except Exception sin especificidad
    - **Lógica compleja**: Lógica de negocio dentro de handlers
    - **Silencing errors**: except pass que oculta errores

    ## Beneficios de la Métrica:
    - **Identifica complejidad**: Encuentra código con manejo excesivo
    - **Mejora robustez**: Evalúa estrategias de error handling
    - **Facilita testing**: Código con menos excepciones es más testeable
    - **Guía refactoring**: Indica dónde simplificar manejo de errores

    ## Mejores Prácticas:
    - **Principio de responsabilidad única**: Una función, un tipo de error
    - **Fail fast**: Detectar errores temprano
    - **Specific exceptions**: Capturar excepciones específicas
    - **Context managers**: Usar with para manejo automático
    - **Logging apropiado**: Registrar errores sin ocultarlos

    ## Referencias:
    - PEP 3134 - Exception Chaining and Embedded Tracebacks
    - PEP 343 - The "with" Statement
    - "Effective Python" by Brett Slatkin - Exception Handling
    - "Clean Code" by Robert Martin - Error Handling
    """

    def __init__(self):
        """Inicializa el calculador de complejidad de manejo de excepciones."""
        super().__init__(
            name="exception_handling_complexity",
            description="Mide la complejidad del manejo de excepciones en el código.",
        )

    def get_default_thresholds(self) -> Dict[str, float]:
        """Obtiene los umbrales por defecto para exception_handling_complexity.
        
        Basado en manejo de excepciones y flujo de error.
        
        Returns:
            Dict[str, float]: Umbrales por defecto {low, medium, high}.
        """
        return {
            "low": 1.0,
            "medium": 3.0,
            "high": 6.0,
        }


    def calculate_function(self, function: Function) -> float:
        """Calcula la complejidad de manejo de excepciones de una función."""
        logger.debug(
            f"Calculando complejidad de excepciones para función: {function.name}"
        )

        # Combinar bloques try y manejadores de excepciones
        exception_complexity = (
            function.exception_handlers_count + function.try_blocks_count
        )

        return float(exception_complexity)

    def calculate_class(self, cls: Class) -> Dict[str, float]:
        """Calcula estadísticas de complejidad de manejo de excepciones para una clase."""
        logger.debug(
            f"Calculando complejidad de excepciones para clase: {cls.name}"
        )

        if not cls.methods:
            return {
                "average": 0.0,
                "max": 0.0,
                "method_count": 0.0,
                "methods_with_exceptions": 0.0,
            }

        method_exceptions = []

        for method in cls.methods:
            method_exc = self.calculate_function(method)
            method_exceptions.append(method_exc)

        result = {
            "average": sum(method_exceptions) / len(method_exceptions),
            "max": max(method_exceptions),
            "method_count": float(len(cls.methods)),
            "methods_with_exceptions": len(
                [e for e in method_exceptions if e > 0]
            ),
        }

        return result

    def calculate_module(self, module: Module) -> None:
        """La complejidad de manejo de excepciones no se calcula a nivel de módulo."""
        logger.debug(
            f"Complejidad de excepciones no aplica a módulo: {module.name} - devolviendo None"
        )
        return None

    def calculate_project(self, project: Project) -> None:
        """La complejidad de manejo de excepciones no se calcula a nivel de proyecto."""
        logger.debug(
            f"Complejidad de excepciones no aplica a proyecto: {project.name} - devolviendo None"
        )
        return None
