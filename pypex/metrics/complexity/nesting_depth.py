"""Módulo para calcular la métrica de profundidad de anidamiento (Nesting Depth)."""

from pypex.metrics.base import BaseMetric
from pypex.parser.code_entities import Class, Function, Module, Project
from pypex.services.logging_service import get_logger

logger = get_logger(__name__)


class NestingDepth(BaseMetric):
    """Calcula la profundidad máxima de anidamiento en estructuras de control.

    ## ¿Qué es la Profundidad de Anidamiento?

    La profundidad de anidamiento (Nesting Depth) es una métrica que mide qué tan
    profundamente están anidadas las estructuras de control en el código. Es una
    medida directa de la complejidad estructural que indica cuántos niveles de
    indentación tiene el código en su punto más profundo.

    ## ¿Cómo se calcula?

    La métrica cuenta el número máximo de niveles de estructuras de control anidadas:

    ### Estructuras que incrementan el nivel:
    - `if` / `elif` / `else`: +1 nivel por cada estructura
    - `while` / `for` / `async for`: +1 nivel por cada bucle
    - `try` / `except` / `finally`: +1 nivel por cada bloque
    - `with` / `async with`: +1 nivel por cada administrador de contexto
    - `match` / `case`: +1 nivel por la estructura match y cada case
    - Funciones/métodos anidados: +1 nivel por cada definición
    - Clases anidadas: +1 nivel por cada definición
    - Comprehensions anidadas: +1 nivel por cada comprensión

    ### Algoritmo paso a paso:
    1. Inicializar nivel_actual = 0, nivel_máximo = 0
    2. Recorrer el AST del código
    3. Al entrar en una estructura anidable: nivel_actual++
    4. Actualizar nivel_máximo = max(nivel_máximo, nivel_actual)
    5. Al salir de una estructura anidable: nivel_actual--
    6. Retornar nivel_máximo

    ## Interpretación de valores:

    - **0-2**: **Excelente** - Código plano y fácil de leer
    - **3-4**: **Bueno** - Complejidad manejable, estructura clara
    - **5-6**: **Moderado** - Considerar refactoring para mejorar legibilidad
    - **7-8**: **Alto** - Código difícil de seguir, refactoring recomendado
    - **9+**: **Crítico** - Código muy complejo, refactoring urgente

    ## ¿Cuándo se aplica?

    **✅ FUNCIONES**: Aplicación principal y más útil
    - Mide la complejidad estructural de la lógica de la función
    - Identifica funciones con demasiada lógica anidada
    - Útil para establecer límites de complejidad en revisiones
    - Correlaciona fuertemente con dificultad de mantenimiento

    **✅ CLASES**: Aplicación agregada valiosa
    - Analiza cada método individualmente
    - Proporciona estadísticas (máximo, promedio) para toda la clase
    - Ayuda a identificar clases con métodos muy complejos
    - Útil para evaluar la calidad general de la clase

    **✅ MÓDULOS**: Aplicación agregada útil
    - Analiza todas las funciones y métodos del módulo
    - Identifica módulos con alta complejidad estructural
    - Útil para priorizar refactoring a nivel de módulo
    - Proporciona métricas de calidad del módulo

    **✅ PROYECTOS**: Aplicación agregada para métricas generales
    - Proporciona estadísticas de complejidad del proyecto completo
    - Útil para tracking de calidad a lo largo del tiempo
    - Ayuda a identificar áreas problemáticas del proyecto
    - Permite comparar complejidad entre proyectos

    ## Ejemplo de cálculo:

    ```python
    def ejemplo_anidamiento():         # Nivel base = 0
        if True:                       # Nivel 1
            for i in range(10):        # Nivel 2
                if i % 2 == 0:         # Nivel 3
                    try:               # Nivel 4
                        with open('file') as f:  # Nivel 5 ← Máximo
                            if f.readable():     # Nivel 6 ← Nuevo máximo
                                print(f.read())
                    except IOError:    # Nivel 4 (vuelve al try)
                        pass
        # Profundidad máxima = 6
    ```

    ## Diferencias con otras métricas:

    | Métrica | Enfoque | Considera |
    |---------|---------|-----------|
    | **Profundidad** | Estructura física | Solo anidamiento |
    | **Ciclomática** | Caminos de ejecución | Decisiones + bucles |
    | **Cognitiva** | Dificultad mental | Anidamiento + complejidad |

    ## Beneficios de usar esta métrica:
    - Fácil de entender y calcular
    - Correlaciona directamente con legibilidad
    - Identifica código que necesita extracción de métodos
    - Útil para establecer estándares de codificación
    - Complementa bien otras métricas de complejidad

    ## Estrategias de refactoring para alta profundidad:
    - **Extracción de métodos**: Crear métodos auxiliares para lógica anidada
    - **Early returns**: Usar return temprano para reducir anidamiento
    - **Guard clauses**: Usar condiciones de guarda para validaciones
    - **Patrones de estrategia**: Reemplazar if-else anidados con polimorfismo
    - **Funciones de orden superior**: Usar map, filter, reduce para bucles anidados

    ## Referencias:
    - Halstead, M. H. (1977). "Elements of Software Science"
    - IEEE Standard 982.1-2005 for Software Engineering
    - Martin, R. C. (2008). "Clean Code: A Handbook of Agile Software Craftsmanship"
    """

    def __init__(self):
        """Inicializa el calculador de profundidad de anidamiento."""
        super().__init__(
            name="nesting_depth",
            description="Mide la profundidad máxima de anidamiento de estructuras de control en el código.",
        )

    def get_default_thresholds(self) -> dict[str, float]:
        """Obtiene los umbrales por defecto para nesting_depth.

        Basado en mejores prácticas de legibilidad de código.

        Returns:
            Dict[str, float]: Umbrales por defecto {low, medium, high}.
        """
        return {
            "low": 3.0,
            "medium": 6.0,
            "high": 9.0,
        }

    def calculate_function(self, function: Function) -> float:
        """Calcula la profundidad máxima de anidamiento para una función.

        Calcula analizando directamente el nodo AST para encontrar la máxima
        profundidad de anidamiento de estructuras de control.

        Args:
            function: Función a analizar.

        Returns:
            float: Profundidad máxima de anidamiento.
        """
        logger.debug(f"Calculando profundidad de anidamiento para función: {function.name}")

        # Calcular directamente desde el nodo AST si está disponible
        if function.astroid_node is not None:
            max_depth = self._calculate_nesting_from_ast(function.astroid_node)
            return float(max_depth)

        # Fallback: función sin AST detectable
        logger.debug(f"No hay nodo AST disponible para {function.name}")
        return 0.0

    def _calculate_nesting_from_ast(self, func_node) -> int:
        """Calcula la profundidad de anidamiento directamente desde el AST.

        Args:
            func_node: Nodo de función de Astroid.

        Returns:
            int: Profundidad máxima de anidamiento.
        """
        try:
            from astroid import nodes as astroid_nodes
        except ImportError:
            logger.warning("Astroid no disponible para análisis de anidamiento")
            return 0

        max_depth = 0

        def calculate_depth(node, current_depth=0):
            nonlocal max_depth
            max_depth = max(max_depth, current_depth)

            # Nodos que incrementan el nivel de anidamiento
            nesting_nodes = (
                astroid_nodes.If,
                astroid_nodes.For,
                astroid_nodes.While,
                astroid_nodes.Try,
                astroid_nodes.With,
                astroid_nodes.ExceptHandler,
                astroid_nodes.Match,
                astroid_nodes.MatchCase,
                # Comprensiones también anidam
                astroid_nodes.ListComp,
                astroid_nodes.DictComp,
                astroid_nodes.SetComp,
                astroid_nodes.GeneratorExp,
            )

            if isinstance(node, nesting_nodes):
                current_depth += 1
                max_depth = max(max_depth, current_depth)

            # Recursión sobre hijos
            for child in node.get_children():
                calculate_depth(child, current_depth)

        # Analizar el cuerpo de la función
        if hasattr(func_node, "body"):
            for stmt in func_node.body:
                calculate_depth(stmt)
        elif isinstance(func_node, astroid_nodes.Lambda):
            calculate_depth(func_node.body)

        return max_depth

    def calculate_class(self, cls: Class) -> dict[str, float]:
        """Calcula estadísticas de profundidad de anidamiento para una clase.

        Analiza cada método de la clase individualmente para calcular estadísticas
        útiles de la clase, pero no suma total que no sería comparable con umbrales.

        Args:
            cls: Clase a analizar.

        Returns:
            Dict[str, float]: Diccionario con estadísticas de profundidad de la clase.
        """
        logger.debug(f"Calculando profundidad de anidamiento para clase: {cls.name}")

        if not cls.methods:
            return {
                "max_depth": 0.0,
                "avg_depth": 0.0,
                "min_depth": 0.0,
                "method_count": 0.0,
                "high_nesting_methods": 0.0,
            }

        depths = []

        # Calcular profundidad para cada método
        for method in cls.methods:
            method_depth = self.calculate_function(method)
            depths.append(method_depth)

        # Solo estadísticas útiles
        result = {
            "max_depth": max(depths),
            "avg_depth": sum(depths) / len(depths),
            "min_depth": min(depths),
            "method_count": float(len(cls.methods)),
            "high_nesting_methods": len([d for d in depths if d > 6]),
        }

        return result

    def calculate_module(self, module: Module) -> None:
        """La profundidad de anidamiento no se calcula a nivel de módulo.

        La profundidad de anidamiento es una métrica específica para evaluar
        la complejidad estructural de funciones individuales. No tiene sentido
        agregar esta métrica a nivel de módulo, ya que:

        - Los umbrales están definidos para funciones individuales
        - La profundidad máxima no es representativa del módulo completo
        - No hay forma meaningful de interpretar la agregación

        Para análisis a nivel de módulo, use métricas específicas como:
        - Métricas de acoplamiento
        - Análisis de dependencias
        - Líneas de código

        Args:
            module: Módulo a analizar.

        Returns:
            None: Siempre None porque no aplica a módulos.
        """
        logger.debug(
            f"Profundidad de anidamiento no aplica a módulo: {module.name} - devolviendo None"
        )
        return None

    def calculate_project(self, project: Project) -> None:
        """La profundidad de anidamiento no se calcula a nivel de proyecto.

        Similar a módulos, la profundidad de anidamiento es una métrica específica
        para funciones individuales y no debe agregarse a nivel de proyecto.

        Args:
            project: Proyecto a analizar.

        Returns:
            None: Siempre None porque no aplica a proyectos.
        """
        logger.debug(
            f"Profundidad de anidamiento no aplica a proyecto: {project.name} - devolviendo None"
        )
        return None

    def get_aggregated_value(self, entity) -> float:
        """Obtiene un valor agregado para usar con umbrales.

        Para funciones devuelve la profundidad directamente.
        Para clases/módulos devuelve la profundidad máxima.

        Args:
            entity: Entidad de código a analizar.

        Returns:
            float: Valor agregado de profundidad.
        """
        result = self.calculate(entity)

        if isinstance(result, (int, float)):
            return float(result)

        if isinstance(result, dict):
            # Buscar claves de valor máximo
            for key in ["max_depth", "total"]:
                if key in result:
                    return float(result[key])

        return 0.0

    def interpret_nesting_level(self, depth: float) -> str:
        """Interpreta el nivel de profundidad de anidamiento.

        Args:
            depth: Profundidad de anidamiento.

        Returns:
            str: Interpretación del nivel.
        """
        if depth <= 3:
            return "Óptimo"
        elif depth <= 6:
            return "Moderado"
        else:
            return "Excesivo"
