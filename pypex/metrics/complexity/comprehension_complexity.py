"""Módulo para calcular la métrica de complejidad de comprensión."""

from pypex.metrics.base import BaseMetric
from pypex.parser.code_entities import Class, Function, Module, Project
from pypex.services.logging_service import get_logger

logger = get_logger(__name__)


class ComprehensionComplexityMetric(BaseMetric):
    """Calcula la complejidad de expresiones de comprensión.

    ## ¿Qué es la Complejidad de Comprensión?

    Esta métrica mide la complejidad de las expresiones de comprensión (list, dict, set, generator)
    en Python. Las comprensiones pueden volverse complejas con múltiples iteradores, condiciones
    anidadas y lógica condicional, lo que afecta la legibilidad y mantenibilidad del código.

    ### Tipos de Comprensiones:
    - **List Comprehensions**: [x for x in items if condition]
    - **Dict Comprehensions**: {k: v for k, v in items if condition}
    - **Set Comprehensions**: {x for x in items if condition}
    - **Generator Expressions**: (x for x in items if condition)

    ### Factores de Complejidad:
    - **Número de condiciones if**: Cada condición incrementa complejidad
    - **Iteradores anidados**: for dentro de for incrementa exponencialmente
    - **Nivel de anidamiento**: Profundidad de estructuras anidadas
    - **Operaciones complejas**: Transformaciones complejas en la expresión

    ## ¿Cómo se calcula?

    ### Fórmula:
    Comprehension Complexity = sum(condition_count for each comprehension)

    ### Elementos que contribuyen:
    - **condition_count**: Número de cláusulas if en cada comprensión
    - **Comprensiones anidadas**: Se suman todas las condiciones
    - **Múltiples comprensiones**: Se agregan todas en la función

    ## Interpretación de valores:

    - **0**: Sin comprensiones, código tradicional
    - **1-2**: Comprensiones simples, fáciles de leer
    - **3-5**: Comprensiones moderadas, revisar claridad
    - **6+**: Comprensiones complejas, considerar refactoring

    ## Ejemplo de cálculo:

    ```python
    def ejemplo_simple():  # Comprehension = 1
        result = [x for x in range(10) if x > 5]  # 1 condición
        return result

    def ejemplo_complejo():  # Comprehension = 4
        # 2 condiciones en primera comprensión
        result1 = [x for x in range(10) if x > 5 if x < 8]  # 2
        # 2 condiciones en segunda comprensión
        result2 = {k: v for k, v in items.items() if k if v}  # 2
        return result1, result2
    ```

    ## Beneficios:
    - **Mejora legibilidad**: Identifica comprensiones difíciles de leer
    - **Facilita debugging**: Comprensiones simples son más fáciles de debuggear
    - **Optimización**: Comprensiones complejas pueden necesitar optimización
    - **Mantenibilidad**: Código más claro es más fácil de mantener

    ## Referencias:
    - PEP 202 - List Comprehensions
    - PEP 274 - Dict Comprehensions
    - PEP 289 - Generator Expressions
    """

    def __init__(self):
        """Inicializa el calculador de complejidad de comprensión."""
        super().__init__(
            name="comprehension_complexity",
            description="Mide la complejidad de expresiones de comprensión basada en condiciones.",
        )

    def get_default_thresholds(self) -> dict[str, float]:
        """Obtiene los umbrales por defecto para comprehension_complexity.

        Basado en dificultad de comprensión de sintaxis Python.

        Returns:
            Dict[str, float]: Umbrales por defecto {low, medium, high}.
        """
        return {
            "low": 2.0,
            "medium": 5.0,
            "high": 8.0,
        }

    def calculate_function(self, function: Function) -> float:
        """Calcula la complejidad de comprensión de una función.

        Analiza directamente el nodo AST para encontrar comprensiones
        y contar sus condiciones if.

        Args:
            function: Función a analizar.

        Returns:
            float: Complejidad total de comprensiones.
        """
        logger.debug(f"Calculando complejidad de comprensión para función: {function.name}")

        # Calcular directamente desde el nodo AST si está disponible
        if function.astroid_node is not None:
            complexity = self._calculate_comprehension_complexity_from_ast(function.astroid_node)
            return float(complexity)

        # Fallback: función sin AST detectable
        logger.debug(f"No hay nodo AST disponible para {function.name}")
        return 0.0

    def _calculate_comprehension_complexity_from_ast(self, func_node) -> int:
        """Calcula la complejidad de comprensiones directamente desde el AST.

        Args:
            func_node: Nodo de función de Astroid.

        Returns:
            int: Complejidad total de comprensiones.
        """
        try:
            from astroid import nodes as astroid_nodes
        except ImportError:
            logger.warning("Astroid no disponible para análisis de comprensiones")
            return 0

        total_complexity = 0

        def count_comprehension_conditions(node):
            nonlocal total_complexity

            # Nodos de comprensión
            comprehension_nodes = (
                astroid_nodes.ListComp,
                astroid_nodes.DictComp,
                astroid_nodes.SetComp,
                astroid_nodes.GeneratorExp,
            )

            if isinstance(node, comprehension_nodes):
                # Contar condiciones if en la comprensión
                condition_count = 0
                for generator in node.generators:
                    # Cada generador puede tener múltiples ifs
                    condition_count += len(generator.ifs)

                total_complexity += condition_count

            # Recursión sobre hijos
            for child in node.get_children():
                count_comprehension_conditions(child)

        # Analizar el cuerpo de la función
        if hasattr(func_node, "body"):
            for stmt in func_node.body:
                count_comprehension_conditions(stmt)
        elif isinstance(func_node, astroid_nodes.Lambda):
            count_comprehension_conditions(func_node.body)

        return total_complexity

    def calculate_class(self, cls: Class) -> dict[str, float]:
        """Calcula estadísticas de complejidad de comprensión para una clase."""
        logger.debug(f"Calculando complejidad de comprensión para clase: {cls.name}")

        if not cls.methods:
            return {
                "average": 0.0,
                "max": 0.0,
                "method_count": 0.0,
                "methods_with_comprehensions": 0.0,
            }

        method_comprehensions = []

        for method in cls.methods:
            method_comp = self.calculate_function(method)
            method_comprehensions.append(method_comp)

        result = {
            "average": sum(method_comprehensions) / len(method_comprehensions),
            "max": max(method_comprehensions),
            "method_count": float(len(cls.methods)),
            "methods_with_comprehensions": len([c for c in method_comprehensions if c > 0]),
        }

        return result

    def calculate_module(self, module: Module) -> None:
        """La complejidad de comprensión no se calcula a nivel de módulo."""
        logger.debug(
            f"Complejidad de comprensión no aplica a módulo: {module.name} - devolviendo None"
        )
        return None

    def calculate_project(self, project: Project) -> None:
        """La complejidad de comprensión no se calcula a nivel de proyecto."""
        logger.debug(
            f"Complejidad de comprensión no aplica a proyecto: {project.name} - devolviendo None"
        )
        return None
