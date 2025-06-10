"""Módulo para calcular la métrica de complejidad lógica."""

from typing import Dict

from pypex.metrics.base import BaseMetric
from pypex.parser.code_entities import Class, Function, Module, Project
from pypex.services.logging_service import get_logger

logger = get_logger(__name__)


class LogicalComplexityMetric(BaseMetric):
    """Calcula la complejidad lógica basada en operadores booleanos.

    ## ¿Qué es la Complejidad Lógica?

    La complejidad lógica es una métrica que mide la complejidad de las condiciones
    lógicas en el código, específicamente contando los operadores booleanos (and/or)
    en expresiones condicionales. Esta métrica es importante porque las condiciones
    complejas son una fuente común de errores y dificultan la comprensión del código.

    ### Fundamentos Teóricos:

    **Operadores Lógicos Binarios**:
    - **AND (and, &&)**: Ambas condiciones deben ser verdaderas
    - **OR (or, ||)**: Al menos una condición debe ser verdadera
    - **NOT (not, !)**: Invierte el valor lógico (menos impacto)

    **Complejidad Combinatorial**:
    - **Cada operador** incrementa los caminos de ejecución posibles
    - **Expresiones anidadas** incrementan exponencialmente la complejidad
    - **Testing exhaustivo** requiere cubrir todas las combinaciones

    ## ¿Cómo se calcula?

    ### Algoritmo:
    1. **Buscar elementos bool_op_sequence** en control_flow_elements
    2. **Sumar condition_complexity** de cada elemento
    3. **La fórmula**: Logical = 1 + sum(condition_complexity)

    ### Elementos que contribuyen:
    - **Operadores AND/OR**: En condiciones if/while
    - **Expresiones booleanas complejas**: En comprensiones
    - **Condiciones anidadas**: En estructuras de control
    - **Operadores ternarios**: Con condiciones complejas

    ## Interpretación de valores:

    - **1-2**: Condiciones simples, fáciles de entender y testear
    - **3-5**: Condiciones moderadas, aceptables pero revisar
    - **6-10**: Condiciones complejas, considerar simplificación
    - **10+**: Condiciones muy complejas, refactoring urgente

    ## ¿Cuándo se aplica?

    **✅ FUNCIONES**: Aplicación principal
    - Identificar funciones con lógica condicional compleja
    - Evaluar dificultad de testing de condiciones
    - Detectar expresiones que necesitan simplificación
    - Priorizar refactoring de lógica booleana

    **✅ CLASES**: Aplicación valiosa
    - Evaluar complejidad lógica de métodos
    - Identificar clases con lógica de negocio compleja
    - Detectar patrones de validación complejos

    ## Ejemplo de cálculo:

    ```python
    def ejemplo_simple(x, y):  # Logical = 1
        if x > 0:
            return True
        return False
    # Sin operadores lógicos complejos

    def ejemplo_complejo(x, y, z):  # Logical = 4
        if x > 0 and y < 10 or z == 5:  # 2 operadores (and, or)
            if a and b and c:           # 2 operadores (and, and)
                return True
        return False
    # 1 (base) + 2 + 2 = 5 (aproximado)
    ```

    ## Beneficios:
    - **Mejora legibilidad**: Identifica lógica difícil de leer
    - **Facilita testing**: Condiciones simples son más fáciles de testear
    - **Reduce errores**: Lógica compleja es propensa a bugs
    - **Guía refactoring**: Indica dónde extraer métodos/variables

    ## Referencias:
    - McCabe, T. J. (1976). "A Complexity Measure"
    - Fenton, N. E., & Pfleeger, S. L. (1997). "Software Metrics"
    """

    def __init__(self):
        """Inicializa el calculador de complejidad lógica."""
        super().__init__(
            name="logical_complexity",
            description="Mide la complejidad de condiciones lógicas basada en operadores booleanos.",
        )

    def get_default_thresholds(self) -> Dict[str, float]:
        """Obtiene los umbrales por defecto para logical_complexity.
        
        Basado en operadores lógicos y de decisión.
        
        Returns:
            Dict[str, float]: Umbrales por defecto {low, medium, high}.
        """
        return {
            "low": 2.0,
            "medium": 5.0,
            "high": 10.0,
        }


    def calculate_function(self, function: Function) -> float:
        """Calcula la complejidad lógica de una función.

        Analiza las expresiones booleanas complejas en la función contando
        operadores lógicos (and/or) en todas las estructuras de control.

        Args:
            function: Función a analizar.

        Returns:
            float: Complejidad lógica de la función.
        """
        logger.debug(
            f"Calculando complejidad lógica para función: {function.name}"
        )

        # Calcular directamente desde el nodo AST si está disponible
        if function.astroid_node is not None:
            logical_operators_count = self._count_logical_operators_from_ast(function.astroid_node)
            return float(1 + logical_operators_count)  # +1 por la complejidad base

        # Fallback: función sin AST detectable
        logger.debug(f"No hay nodo AST disponible para {function.name}")
        return 1.0

    def _count_logical_operators_from_ast(self, func_node) -> int:
        """Cuenta operadores lógicos (and/or) en un nodo AST de Astroid.

        Args:
            func_node: Nodo de función de Astroid.

        Returns:
            int: Número de operadores lógicos encontrados.
        """
        try:
            from astroid import nodes as astroid_nodes
        except ImportError:
            logger.warning("Astroid no disponible para análisis de complejidad lógica")
            return 0

        logical_ops_count = 0

        def count_logical_operators(node):
            nonlocal logical_ops_count

            # Nodos BoolOp contienen operadores and/or
            if isinstance(node, astroid_nodes.BoolOp):
                # Cada operador lógico incrementa la complejidad
                # Si hay n valores, hay n-1 operadores
                if hasattr(node, 'values') and len(node.values) > 1:
                    logical_ops_count += len(node.values) - 1

            # Recursión sobre todos los hijos
            for child in node.get_children():
                count_logical_operators(child)

        # Analizar el cuerpo de la función
        if hasattr(func_node, 'body'):
            for stmt in func_node.body:
                count_logical_operators(stmt)
        elif isinstance(func_node, astroid_nodes.Lambda):
            count_logical_operators(func_node.body)

        return logical_ops_count

    def calculate_class(self, cls: Class) -> Dict[str, float]:
        """Calcula estadísticas de complejidad lógica para una clase.

        Analiza cada método de la clase para proporcionar estadísticas útiles
        pero no suma total que no sería comparable con umbrales.

        Args:
            cls: Clase a analizar.

        Returns:
            Dict[str, float]: Estadísticas de complejidad lógica de la clase.
        """
        logger.debug(f"Calculando complejidad lógica para clase: {cls.name}")

        if not cls.methods:
            return {
                "average": 0.0,
                "max": 0.0,
                "min": 0.0,
                "method_count": 0.0,
                "complex_logic_methods": 0.0,
            }

        method_logicals = []

        for method in cls.methods:
            method_logical = self.calculate_function(method)
            method_logicals.append(method_logical)

        result = {
            "average": sum(method_logicals) / len(method_logicals),
            "max": max(method_logicals),
            "min": min(method_logicals),
            "method_count": float(len(cls.methods)),
            "complex_logic_methods": len(
                [l for l in method_logicals if l >= 6]
            ),
        }

        return result

    def calculate_module(self, module: Module) -> None:
        """La complejidad lógica no se calcula a nivel de módulo.

        La complejidad lógica es una métrica específica para evaluar
        la complejidad de condiciones lógicas en funciones individuales.
        No tiene sentido agregar esta métrica a nivel de módulo.

        Args:
            module: Módulo a analizar.

        Returns:
            None: Siempre None porque no aplica a módulos.
        """
        logger.debug(
            f"Complejidad lógica no aplica a módulo: {module.name} - devolviendo None"
        )
        return None

    def calculate_project(self, project: Project) -> None:
        """La complejidad lógica no se calcula a nivel de proyecto.

        Args:
            project: Proyecto a analizar.

        Returns:
            None: Siempre None porque no aplica a proyectos.
        """
        logger.debug(
            f"Complejidad lógica no aplica a proyecto: {project.name} - devolviendo None"
        )
        return None
