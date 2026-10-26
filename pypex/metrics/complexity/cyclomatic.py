"""Módulo para calcular la complejidad ciclomática."""

from pypex.metrics.base import BaseMetric
from pypex.parser.code_entities import Class, Function, Module, Project
from pypex.services.logging_service import get_logger

logger = get_logger(__name__)


class CyclomaticComplexity(BaseMetric):
    """Calcula la complejidad ciclomática de código Python.

    ## ¿Qué es la Complejidad Ciclomática?

    La complejidad ciclomática es una métrica de software desarrollada por Thomas J. McCabe en 1976
    que mide la complejidad estructural de un programa contando el número de caminos de ejecución
    linealmente independientes a través del código fuente.

    ## ¿Cómo se calcula?

    La fórmula básica es: **M = E - N + 2P**
    Donde:
    - M = Complejidad ciclomática
    - E = Número de aristas en el grafo de flujo
    - N = Número de nodos en el grafo de flujo
    - P = Número de componentes conectados

    En la práctica, se calcula contando:
    **M = 1 + número de puntos de decisión**

    ### Puntos de decisión que incrementan la complejidad:
    - `if` / `elif` / `else`: +1 por cada condición
    - `while` / `for` / `async for`: +1 por cada bucle
    - `try` / `except`: +1 por cada manejador de excepción
    - `match` / `case`: +1 por cada patrón de match
    - Operadores booleanos `and` / `or`: +1 por cada operador adicional
    - Expresiones condicionales (operador ternario): +1
    - Comprensiones con condiciones: +1 por cada `if` en la comprensión

    ### Algoritmo paso a paso:
    1. Inicializar complejidad = 1 (camino base)
    2. Recorrer el AST del código
    3. Por cada estructura de control encontrada, incrementar en 1
    4. Para operadores booleanos, incrementar por cada operador adicional
    5. Sumar todos los incrementos al valor base

    ## Interpretación de valores:

    - **1-10**: **Baja complejidad** - Código simple y fácil de testear
    - **11-20**: **Complejidad moderada** - Código manejable, revisar complejidad
    - **21-50**: **Alta complejidad** - Código difícil de mantener, refactoring recomendado
    - **50+**: **Complejidad muy alta** - Código crítico, refactoring urgente

    ## ¿Cuándo se aplica?

    **✅ FUNCIONES**: Aplicación principal y más útil
    - Mide la complejidad de la lógica de control dentro de una función
    - Ayuda a identificar funciones que necesitan refactoring
    - Útil para determinar el número de casos de prueba necesarios

    **✅ CLASES**: Aplicación agregada útil
    - Calcula la complejidad de cada método individualmente
    - Proporciona estadísticas agregadas (total, promedio) para la clase
    - Ayuda a identificar clases con lógica muy compleja

    **✅ MÓDULOS**: Aplicación agregada con valor
    - Suma la complejidad de todas las funciones y métodos del módulo
    - Útil para identificar módulos que requieren refactoring
    - Proporciona una visión general de la complejidad del módulo

    **✅ PROYECTOS**: Aplicación agregada para métricas generales
    - Suma la complejidad total del proyecto
    - Útil para tracking de métricas a lo largo del tiempo
    - Ayuda a identificar áreas problemáticas del proyecto

    ## Ejemplo de cálculo:

    ```python
    def ejemplo_funcion(x, y):     # Complejidad base = 1
        if x > 0:                  # +1 (decisión if)
            if y > 0:              # +1 (decisión if anidada)
                return x + y
            else:                  # +0 (else no suma)
                return x
        elif x < 0:                # +1 (decisión elif)
            for i in range(y):     # +1 (bucle for)
                if i % 2 == 0:     # +1 (decisión if en bucle)
                    x += i
        else:                      # +0 (else no suma)
            try:                   # +0 (try no suma)
                result = x / y
            except ZeroDivisionError:  # +1 (manejador except)
                result = 0
        return result
    # Complejidad total = 1 + 1 + 1 + 1 + 1 + 1 + 1 = 7
    ```

    ## Beneficios de usar esta métrica:
    - Predice el esfuerzo de testing (número de casos de prueba)
    - Identifica código difícil de mantener
    - Ayuda en decisiones de refactoring
    - Útil para revisiones de código
    - Correlaciona con defectos en el software

    ## Referencias:
    - McCabe, T. J. (1976). "A Complexity Measure"
    - IEEE Standard 982.1-2005 for Software Engineering
    - ISO/IEC 25023:2016 Systems and software engineering
    """

    def __init__(self):
        """Inicializa el calculador de complejidad ciclomática."""
        super().__init__(
            name="cyclomatic_complexity",
            description="Medida de la complejidad estructural de un programa basada en el número de caminos de ejecución.",
        )

    def get_default_thresholds(self) -> dict[str, float]:
        """Obtiene los umbrales por defecto para complejidad ciclomática.

        Basado en las recomendaciones de McCabe y mejores prácticas de la industria:
        - 1-10: Código simple y fácil de testear
        - 11-20: Complejidad moderada, revisar si es necesario
        - 21+: Alta complejidad, refactoring recomendado

        Returns:
            Dict[str, float]: Umbrales por defecto {low, medium, high}.
        """
        return {
            "low": 10.0,  # Hasta 10: baja complejidad
            "medium": 20.0,  # 11-20: complejidad moderada
            "high": 50.0,  # 21-50: alta complejidad, 50+: muy alta
        }

    def calculate_function(self, function: Function) -> float:
        """Calcula la complejidad ciclomática de una función.

        Esta es la aplicación principal de la complejidad ciclomática.
        Analiza las estructuras de control dentro de la función para
        determinar el número de caminos de ejecución linealmente independientes.

        Args:
            function: Función a analizar.

        Returns:
            float: Complejidad ciclomática de la función.
        """
        logger.debug(f"Calculando complejidad ciclomática para función: {function.name}")

        # Calcular directamente desde el nodo AST si está disponible
        if function.astroid_node is not None:
            decision_points = self._calculate_decision_points_from_ast(function.astroid_node)
            return float(decision_points + 1)  # +1 por el camino base

        # Fallback: función sin AST detectable
        logger.debug(f"No hay nodo AST disponible para {function.name}")
        return 1.0

    def _calculate_decision_points_from_ast(self, func_node) -> int:
        """Calcula puntos de decisión directamente desde el AST.

        Args:
            func_node: Nodo de función de Astroid.

        Returns:
            int: Número de puntos de decisión.
        """
        try:
            from astroid import nodes as astroid_nodes
        except ImportError:
            logger.warning("Astroid no disponible para análisis ciclomático")
            return 0

        decision_count = 0

        def count_decision_points(node):
            nonlocal decision_count

            # Nodos que representan puntos de decisión
            if isinstance(node, astroid_nodes.If):
                decision_count += 1
                # elif también cuenta como decisión adicional
                if hasattr(node, "orelse") and node.orelse:
                    for elif_node in node.orelse:
                        if isinstance(elif_node, astroid_nodes.If):
                            decision_count += 1

            elif isinstance(node, (astroid_nodes.For, astroid_nodes.While)):
                decision_count += 1

            elif isinstance(node, astroid_nodes.Try):
                # Cada except handler es un punto de decisión
                if hasattr(node, "handlers"):
                    decision_count += len(node.handlers)

            elif isinstance(node, astroid_nodes.Match):
                # Cada case es un punto de decisión
                if hasattr(node, "cases"):
                    decision_count += len(node.cases)

            elif isinstance(node, astroid_nodes.BoolOp):
                # Operadores lógicos and/or crean caminos adicionales
                if hasattr(node, "values") and len(node.values) > 1:
                    decision_count += len(node.values) - 1

            # Recursión sobre hijos
            for child in node.get_children():
                count_decision_points(child)

        # Analizar el cuerpo de la función
        if hasattr(func_node, "body"):
            for stmt in func_node.body:
                count_decision_points(stmt)
        elif isinstance(func_node, astroid_nodes.Lambda):
            count_decision_points(func_node.body)

        return decision_count

    def calculate_class(self, cls: Class) -> dict[str, float]:
        """Calcula estadísticas de complejidad ciclomática para una clase.

        Analiza cada método de la clase individualmente para calcular estadísticas
        útiles de la clase, pero no suma total (que no sería comparable con umbrales).

        Args:
            cls: Clase a analizar.

        Returns:
            Dict[str, float]: Diccionario con estadísticas de complejidad de la clase.
        """
        logger.debug(f"Calculando complejidad ciclomática para clase: {cls.name}")

        if not cls.methods:
            return {
                "average": 0.0,
                "max": 0.0,
                "min": 0.0,
                "method_count": 0.0,
                "high_complexity_methods": 0.0,
            }

        method_complexities = []

        # Calcular complejidad para cada método
        for method in cls.methods:
            method_complexity = self.calculate_function(method)
            method_complexities.append(method_complexity)

        # Solo estadísticas útiles, NO suma total
        result = {
            "average": sum(method_complexities) / len(method_complexities),
            "max": max(method_complexities),
            "min": min(method_complexities),
            "method_count": float(len(cls.methods)),
            "high_complexity_methods": len([c for c in method_complexities if c > 10]),
        }

        return result

    def calculate_module(self, module: Module) -> None:
        """La complejidad ciclomática no se calcula a nivel de módulo.

        La complejidad ciclomática es una métrica a nivel de función que mide
        la complejidad estructural de funciones individuales. Sumar o agregar
        estas métricas a nivel de módulo no proporciona información útil y
        puede ser engañoso, ya que:

        - Los umbrales están definidos para funciones individuales
        - Un módulo con muchas funciones simples tendría una suma alta
        - No hay forma meaningful de interpretar la suma total

        Para análisis a nivel de módulo, use métricas específicas como:
        - Métricas de acoplamiento entre módulos
        - Análisis de dependencias
        - Líneas de código (que sí se puede agregar)

        Args:
            module: Módulo a analizar.

        Returns:
            None: Siempre None porque no aplica a módulos.
        """
        logger.debug(
            f"Complejidad ciclomática no aplica a módulo: {module.name} - devolviendo None"
        )
        return None

    def calculate_project(self, project: Project) -> None:
        """La complejidad ciclomática no se calcula a nivel de proyecto.

        Similar a módulos, la complejidad ciclomática es una métrica específica
        para funciones individuales y no debe agregarse a nivel de proyecto.

        Para análisis de proyecto, considere:
        - Distribución de complejidades individuales
        - Métricas arquitectónicas
        - Métricas de calidad del código
        - Análisis de patrones y anti-patrones

        Args:
            project: Proyecto a analizar.

        Returns:
            None: Siempre None porque no aplica a proyectos.
        """
        logger.debug(
            f"Complejidad ciclomática no aplica a proyecto: {project.name} - devolviendo None"
        )
        return None
