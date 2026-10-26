"""Módulo para calcular la métrica de profundidad de comprensión anidada."""

from pypex.metrics.base import BaseMetric
from pypex.parser.code_entities import Class, Function, Module, Project
from pypex.services.logging_service import get_logger

logger = get_logger(__name__)


class NestedComprehensionDepthMetric(BaseMetric):
    """Calcula la profundidad máxima de anidamiento en comprensiones.

    ## ¿Qué es la Profundidad de Comprensión Anidada?

    Esta métrica mide la profundidad máxima de anidamiento en expresiones de comprensión.
    Las comprensiones anidadas pueden volverse extremadamente difíciles de leer y entender,
    especialmente cuando combinan múltiples niveles de iteración y condiciones complejas.

    ### Tipos de Anidamiento:
    - **Comprensiones dentro de comprensiones**: [[x for x in row] for row in matrix]
    - **Generadores anidados**: (item for sublist in data for item in sublist)
    - **Condicionales complejos**: [x for x in items if any(c for c in x if c.isdigit())]
    - **Múltiples iteradores**: [(x, y) for x in range(3) for y in range(3)]

    ### Factores de Complejidad:
    - **Nivel de anidamiento**: Profundidad de estructuras anidadas
    - **Múltiples iteradores**: for dentro de for incrementa complejidad
    - **Condiciones anidadas**: if dentro de comprensiones anidadas
    - **Combinaciones complejas**: Mezcla de tipos de comprensión

    ## ¿Cómo se calcula?

    ### Fórmula:
    Nested Depth = max(nesting_level for each comprehension)

    ### Elementos que contribuyen:
    - **nesting_level**: Profundidad máxima de anidamiento
    - **Se evalúa por función**: Máximo entre todas las comprensiones
    - **Anidamiento real**: No cuenta comprensiones separadas

    ## Interpretación de valores:

    - **0**: Sin comprensiones
    - **1**: Comprensiones simples, sin anidamiento
    - **2**: Anidamiento moderado, aún legible
    - **3+**: Anidamiento profundo, considerar refactoring

    ## Ejemplo de cálculo:

    ```python
    def ejemplo_simple():  # Depth = 1
        result = [x for x in range(10)]  # Nivel 1
        return result

    def ejemplo_anidado():  # Depth = 2
        matrix = [[x for x in row] for row in data]  # Nivel 2
        return matrix

    def ejemplo_profundo():  # Depth = 3
        # Comprensión profundamente anidada
        result = [[[z for z in y] for y in x] for x in data]  # Nivel 3
        return result
    ```

    ## Cuándo Refactorizar:
    - **Nivel 3+**: Considerar extraer a funciones separadas
    - **Múltiples condiciones**: Simplificar lógica condicional
    - **Difícil de leer**: Si requiere comentarios para entender
    - **Hard to test**: Si es difícil escribir tests unitarios

    ## Beneficios:
    - **Mejora legibilidad**: Identifica código difícil de leer
    - **Facilita debugging**: Estructuras simples son más fáciles de debuggear
    - **Reduce errores**: Anidamiento profundo es propenso a bugs
    - **Mejora mantenibilidad**: Código más claro es más fácil de mantener

    ## Referencias:
    - PEP 202 - List Comprehensions
    - "Code Complete" by Steve McConnell - Chapter on Complexity
    - "Clean Code" by Robert Martin - Comprehension Guidelines
    """

    def __init__(self):
        """Inicializa el calculador de profundidad de comprensión anidada."""
        super().__init__(
            name="nested_comprehension_depth",
            description="Mide la profundidad máxima de anidamiento en expresiones de comprensión.",
        )

    def get_default_thresholds(self) -> dict[str, float]:
        """Obtiene los umbrales por defecto para nested_comprehension_depth.

        Basado en legibilidad de comprehensions anidadas.

        Returns:
            Dict[str, float]: Umbrales por defecto {low, medium, high}.
        """
        return {
            "low": 1.0,
            "medium": 2.0,
            "high": 3.0,
        }

    def calculate_function(self, function: Function) -> float:
        """Calcula la profundidad máxima de comprensión anidada de una función.

        Analiza directamente el nodo AST para encontrar comprensiones anidadas
        y determinar la máxima profundidad de anidamiento.

        Args:
            function: Función a analizar.

        Returns:
            float: Profundidad máxima de anidamiento en comprensiones.
        """
        logger.debug(f"Calculando profundidad de comprensión anidada para función: {function.name}")

        # Calcular directamente desde el nodo AST si está disponible
        if function.astroid_node is not None:
            max_depth = self._calculate_comprehension_depth_from_ast(function.astroid_node)
            return float(max_depth)

        # Fallback: función sin AST detectable
        logger.debug(f"No hay nodo AST disponible para {function.name}")
        return 0.0

    def _calculate_comprehension_depth_from_ast(self, func_node) -> int:
        """Calcula la profundidad de comprensiones anidadas directamente desde el AST.

        Args:
            func_node: Nodo de función de Astroid.

        Returns:
            int: Profundidad máxima de anidamiento en comprensiones.
        """
        try:
            from astroid import nodes as astroid_nodes
        except ImportError:
            logger.warning("Astroid no disponible para análisis de comprensiones")
            return 0

        max_depth = 0

        def calculate_comprehension_depth(node, current_depth=0):
            nonlocal max_depth

            # Nodos de comprensión que incrementan el nivel de anidamiento
            comprehension_nodes = (
                astroid_nodes.ListComp,
                astroid_nodes.DictComp,
                astroid_nodes.SetComp,
                astroid_nodes.GeneratorExp,
            )

            if isinstance(node, comprehension_nodes):
                current_depth += 1
                max_depth = max(max_depth, current_depth)

            # Recursión sobre hijos
            for child in node.get_children():
                calculate_comprehension_depth(child, current_depth)

        # Analizar el cuerpo de la función
        if hasattr(func_node, "body"):
            for stmt in func_node.body:
                calculate_comprehension_depth(stmt)
        elif isinstance(func_node, astroid_nodes.Lambda):
            calculate_comprehension_depth(func_node.body)

        return max_depth

    def calculate_class(self, cls: Class) -> dict[str, float]:
        """Calcula estadísticas de profundidad de comprensión anidada para una clase."""
        logger.debug(f"Calculando profundidad de comprensión anidada para clase: {cls.name}")

        if not cls.methods:
            return {
                "max_depth": 0.0,
                "average_depth": 0.0,
                "method_count": 0.0,
                "methods_with_nested": 0.0,
            }

        method_depths = []

        for method in cls.methods:
            method_depth = self.calculate_function(method)
            method_depths.append(method_depth)

        result = {
            "max_depth": max(method_depths),
            "average_depth": sum(method_depths) / len(method_depths),
            "method_count": float(len(cls.methods)),
            "methods_with_nested": len([d for d in method_depths if d > 1]),
        }

        return result

    def calculate_module(self, module: Module) -> None:
        """La profundidad de comprensión anidada no se calcula a nivel de módulo."""
        logger.debug(
            f"Profundidad de comprensión anidada no aplica a módulo: {module.name} - devolviendo None"
        )
        return None

    def calculate_project(self, project: Project) -> None:
        """La profundidad de comprensión anidada no se calcula a nivel de proyecto."""
        logger.debug(
            f"Profundidad de comprensión anidada no aplica a proyecto: {project.name} - devolviendo None"
        )
        return None
