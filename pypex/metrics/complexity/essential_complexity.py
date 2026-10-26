"""Módulo para calcular la métrica de complejidad esencial."""

from pypex.metrics.base import BaseMetric
from pypex.parser.code_entities import Class, Function, Module, Project
from pypex.services.logging_service import get_logger

logger = get_logger(__name__)


class EssentialComplexityMetric(BaseMetric):
    """Calcula la complejidad esencial basada en elementos de flujo irreducibles.

    ## ¿Qué es la Complejidad Esencial?

    La complejidad esencial es una métrica desarrollada por Thomas McCabe que mide
    la complejidad mínima que no puede ser reducida mediante refactoring estructurado.
    Esta métrica identifica código que tiene estructuras de control irreducibles
    o "spaghetti code" que es inherentemente difícil de entender y mantener.

    ### Conceptos Fundamentales:

    **Complejidad Reducible**: Estructuras de control bien formadas
    - Secuencias lineales de código
    - Estructuras if-else balanceadas
    - Bucles con una sola entrada y salida
    - Bloques try-except bien estructurados

    **Complejidad Esencial**: Estructuras irreducibles
    - Múltiples puntos de salida (return, break, continue)
    - Manejo de excepciones con raise en lugares inesperados
    - Bucles con break/continue múltiples
    - Flujo de control excepcional no estructurado

    ## ¿Cómo se calcula?

    ### Algoritmo Base:
    1. **Identificar elementos de flujo excepcional** en control_flow_elements
    2. **Contar elementos marcados** como is_exceptional_flow
    3. **Sumar complejidad base** + elementos excepcionales
    4. **La fórmula**: Essential = 1 + elementos_excepcionales

    ### Elementos que contribuyen:
    - **Elementos excepcionales**: is_exceptional_flow = True
    - **Return statements**: return fuera del final de función
    - **Break/Continue**: en bucles anidados
    - **Raise statements**: manejo de excepciones no estructurado
    - **Yield expressions**: en lugares no esperados

    ## Interpretación de valores:

    - **1**: Código completamente estructurado, sin complejidad esencial
    - **2-3**: Complejidad esencial baja, pocas estructuras irreducibles
    - **4-6**: Complejidad esencial moderada, algunas mejoras posibles
    - **7+**: Complejidad esencial alta, refactoring urgente necesario

    ## ¿Cuándo se aplica?

    **✅ FUNCIONES**: Aplicación principal y más valiosa
    - Identificar funciones con flujo de control desestructurado
    - Detectar "spaghetti code" que necesita refactoring
    - Evaluar la facilidad de testing y debugging
    - Priorizar esfuerzos de refactoring estructural

    **✅ CLASES**: Aplicación agregada útil
    - Identificar clases con métodos mal estructurados
    - Evaluar complejidad arquitectónica de la clase
    - Detectar patrones de diseño problemáticos

    **✅ MÓDULOS**: Aplicación para métricas generales
    - Evaluar calidad estructural del módulo
    - Identificar áreas que necesitan restructuración
    - Métricas de mantenibilidad

    ## Ejemplo de cálculo:

    ```python
    def ejemplo_estructurado(x):  # Essential = 1
        if x > 0:
            return x * 2
        else:
            return 0
    # Solo flujo estructurado

    def ejemplo_no_estructurado(x):  # Essential = 4
        for i in range(x):
            if i == 5:
                break        # +1 (exceptional flow)
            if i < 0:
                continue     # +1 (exceptional flow)
            if i == 10:
                raise ValueError("Error")  # +1 (exceptional flow)
        return x
    # 1 (base) + 3 (exceptional) = 4
    ```

    ## Beneficios de usar esta métrica:
    - **Detecta código spaghetti**: Identifica estructuras irreducibles
    - **Guía de refactoring**: Prioriza qué código restructurar
    - **Mejora testing**: Código estructurado es más fácil de testear
    - **Reduce bugs**: Código estructurado tiene menos defectos
    - **Facilita mantenimiento**: Estructuras claras son más mantenibles

    ## Referencias:
    - McCabe, T. J. (1976). "A Complexity Measure"
    - IEEE Standard 982.1-2005 for Software Engineering
    - Watson, A. H., & McCabe, T. J. (1996). "Structured Testing"
    """

    def __init__(self):
        """Inicializa el calculador de complejidad esencial."""
        super().__init__(
            name="essential_complexity",
            description="Mide la complejidad irreducible basada en elementos de flujo excepcional.",
        )

    def get_default_thresholds(self) -> dict[str, float]:
        """Obtiene los umbrales por defecto para essential_complexity.

        Basado en teoría de grafos de flujo de control.

        Returns:
            Dict[str, float]: Umbrales por defecto {low, medium, high}.
        """
        return {
            "low": 1.0,
            "medium": 3.0,
            "high": 6.0,
        }

    def calculate_function(self, function: Function) -> float:
        """Calcula la complejidad esencial de una función.

        Analiza directamente el nodo AST para identificar elementos de flujo
        excepcional que contribuyen a la complejidad irreducible. Si no hay
        nodo AST disponible, utiliza control_flow_elements como fallback.

        Args:
            function: Función a analizar.

        Returns:
            float: Complejidad esencial de la función.
        """
        logger.debug(f"Calculando complejidad esencial para función: {function.name}")

        # Prioridad 1: Calcular directamente desde el nodo AST si está disponible
        if function.astroid_node is not None:
            exceptional_elements = self._calculate_exceptional_flow_from_ast(function.astroid_node)
            essential_complexity = 1 + exceptional_elements
            return float(essential_complexity)

        # Prioridad 2: Fallback usando control_flow_elements (para testing y compatibilidad)
        if (
            hasattr(function, "control_flow_elements")
            and function.control_flow_elements is not None
        ):
            exceptional_elements = self._count_exceptional_elements_in_control_flow(
                function.control_flow_elements
            )
            essential_complexity = 1 + exceptional_elements
            return float(essential_complexity)

        # Fallback final: función sin AST ni control_flow_elements
        logger.debug(f"No hay nodo AST ni control_flow_elements disponibles para {function.name}")
        return 1.0  # Solo complejidad base

    def _calculate_exceptional_flow_from_ast(self, func_node) -> int:
        """Calcula elementos de flujo excepcional directamente desde el AST.

        Args:
            func_node: Nodo de función de Astroid.

        Returns:
            int: Número de elementos de flujo excepcional.
        """
        try:
            from astroid import nodes as astroid_nodes
        except ImportError:
            logger.warning("Astroid no disponible para análisis de complejidad esencial")
            return 0

        exceptional_count = 0

        def count_exceptional_elements(node, in_loop=False, in_function_body=True):
            nonlocal exceptional_count

            # Elementos que indican flujo excepcional
            if isinstance(node, astroid_nodes.Break):
                exceptional_count += 1
            elif isinstance(node, astroid_nodes.Continue):
                exceptional_count += 1
            elif isinstance(node, astroid_nodes.Return):
                # Return no es excepcional si es la última statement de la función
                if not self._is_final_return(node, func_node):
                    exceptional_count += 1
            elif isinstance(node, astroid_nodes.Raise):
                exceptional_count += 1
            elif isinstance(node, (astroid_nodes.Yield, astroid_nodes.YieldFrom)):
                # Yield en posiciones no esperadas puede ser excepcional
                exceptional_count += 1

            # Actualizar contexto de bucle
            new_in_loop = in_loop or isinstance(node, (astroid_nodes.For, astroid_nodes.While))

            # Recursión sobre hijos
            for child in node.get_children():
                count_exceptional_elements(child, new_in_loop, in_function_body)

        # Analizar el cuerpo de la función
        if hasattr(func_node, "body"):
            for stmt in func_node.body:
                count_exceptional_elements(stmt)
        elif isinstance(func_node, astroid_nodes.Lambda):
            count_exceptional_elements(func_node.body, in_function_body=False)

        return exceptional_count

    def _is_final_return(self, return_node, func_node) -> bool:
        """Verifica si un return es la última statement de la función.

        Args:
            return_node: Nodo return a verificar.
            func_node: Nodo de función contenedora.

        Returns:
            bool: True si es el return final, False si es excepcional.
        """
        try:
            if not hasattr(func_node, "body") or not func_node.body:
                return True

            # Verificar si es la última statement directa del cuerpo de la función
            last_stmt = func_node.body[-1]

            # Si el último statement es el return directamente
            if return_node is last_stmt:
                return True

            # Si está dentro del último statement (ej: if en la última línea)
            parent = return_node.parent
            while parent and parent is not func_node:
                if parent is last_stmt:
                    return True
                parent = parent.parent

            return False
        except Exception:
            # En caso de error, asumir que no es final (más conservador)
            return False

    def _count_exceptional_elements_in_control_flow(self, control_flow_elements) -> int:
        """Cuenta elementos excepcionales en la lista de control_flow_elements.

        Este método proporciona compatibilidad con el sistema de testing
        y análisis alternativo cuando no hay nodos AST disponibles.

        Args:
            control_flow_elements: Lista de elementos de control de flujo.

        Returns:
            int: Número de elementos excepcionales.
        """
        exceptional_count = 0

        try:
            for element in control_flow_elements:
                # Verificar si el elemento está marcado como excepcional
                if hasattr(element, "is_exceptional_flow") and element.is_exceptional_flow:
                    exceptional_count += 1
        except (TypeError, AttributeError) as e:
            logger.debug(f"Error procesando control_flow_elements: {e}")
            # En caso de error, retornar 0 (conservador)
            return 0

        return exceptional_count

    def calculate_class(self, cls: Class) -> dict[str, float]:
        """Calcula estadísticas de complejidad esencial para una clase.

        Analiza cada método de la clase para proporcionar estadísticas útiles
        pero no suma total que no sería comparable con umbrales.

        Args:
            cls: Clase a analizar.

        Returns:
            Dict[str, float]: Estadísticas de complejidad esencial de la clase.
        """
        logger.debug(f"Calculando complejidad esencial para clase: {cls.name}")

        if not cls.methods:
            return {
                "average": 0.0,
                "max": 0.0,
                "min": 0.0,
                "method_count": 0.0,
                "high_essential_methods": 0.0,
            }

        method_essentials = []

        for method in cls.methods:
            method_essential = self.calculate_function(method)
            method_essentials.append(method_essential)

        result = {
            "average": sum(method_essentials) / len(method_essentials),
            "max": max(method_essentials),
            "min": min(method_essentials),
            "method_count": float(len(cls.methods)),
            "high_essential_methods": len([e for e in method_essentials if e >= 4]),
        }

        return result

    def calculate_module(self, module: Module) -> None:
        """La complejidad esencial no se calcula a nivel de módulo.

        La complejidad esencial es una métrica específica para evaluar
        la complejidad irreducible de funciones individuales. No tiene
        sentido agregar esta métrica a nivel de módulo.

        Args:
            module: Módulo a analizar.

        Returns:
            None: Siempre None porque no aplica a módulos.
        """
        logger.debug(f"Complejidad esencial no aplica a módulo: {module.name} - devolviendo None")
        return None

    def calculate_project(self, project: Project) -> None:
        """La complejidad esencial no se calcula a nivel de proyecto.

        Args:
            project: Proyecto a analizar.

        Returns:
            None: Siempre None porque no aplica a proyectos.
        """
        logger.debug(
            f"Complejidad esencial no aplica a proyecto: {project.name} - devolviendo None"
        )
        return None
