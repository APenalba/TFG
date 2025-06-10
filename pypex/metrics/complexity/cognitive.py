"""Módulo para calcular la complejidad cognitiva."""

import ast
from typing import Dict, Optional, Union

import astroid

from pypex.metrics.base import BaseMetric
from pypex.parser.code_entities import Class, Function, Module, Project
from pypex.services.logging_service import get_logger

logger = get_logger(__name__)


class CognitiveComplexity(BaseMetric):
    """Calcula la complejidad cognitiva de código Python.

    ## ¿Qué es la Complejidad Cognitiva?

    La complejidad cognitiva es una métrica de software desarrollada por SonarSource que mide
    qué tan difícil es entender el flujo de control de un código. A diferencia de la complejidad
    ciclomática, la complejidad cognitiva considera el anidamiento y la dificultad mental
    de seguir el flujo del código.

    ## ¿Cómo se calcula?

    La complejidad cognitiva se basa en tres reglas fundamentales:

    ### B0 - Incremento básico:
    Las siguientes estructuras incrementan la complejidad en +1:
    - `if` / `elif` / `else if`
    - `switch` / `match` (y cada `case`)
    - `while` / `for` / `do-while`
    - `catch` / `except`
    - `goto` / `break` / `continue` que salta múltiples niveles
    - Operadores binarios en secuencias (`&&` / `and`, `||` / `or`)
    - Cada función/método recursivo

    ### N - Penalización por anidamiento:
    Por cada nivel de anidamiento, se añade una penalización adicional:
    - Nivel 1: +0 penalización
    - Nivel 2: +1 penalización
    - Nivel 3: +2 penalización
    - Nivel n: +(n-1) penalización

    ### Estructuras que incrementan el anidamiento:
    - `if` / `else if` / `else`
    - `switch` / `match`
    - `for` / `while` / `do-while`
    - `catch` / `except`
    - Funciones/métodos anidados

    ### Algoritmo paso a paso:
    1. Recorrer el AST manteniendo el nivel de anidamiento actual
    2. Para cada estructura B0: incrementar complejidad en 1 + nivel_anidamiento
    3. Para cada secuencia de operadores booleanos: +número_operadores_adicionales
    4. Al entrar en estructuras anidables: incrementar nivel_anidamiento
    5. Al salir de estructuras anidables: decrementar nivel_anidamiento

    ## Interpretación de valores:

    - **0-5**: **Bajo** - Código muy fácil de entender
    - **6-10**: **Moderado** - Código fácil de entender
    - **11-15**: **Alto** - Código difícil de entender, considerar refactoring
    - **16-25**: **Muy alto** - Código muy difícil de entender, refactoring recomendado
    - **25+**: **Extremo** - Código extremadamente difícil, refactoring urgente

    ## ¿Cuándo se aplica?

    **✅ FUNCIONES**: Aplicación principal y más valiosa
    - Mide la dificultad cognitiva de entender una función específica
    - Identifica funciones que necesitan simplificación
    - Mejor predictor de dificultad de mantenimiento que la complejidad ciclomática
    - Útil para establecer límites en revisiones de código

    **❓ CLASES**: Aplicación limitada, principalmente para decoradores
    - La definición de clase en sí no suele tener flujo de control
    - Principalmente útil para analizar decoradores complejos
    - Los métodos se analizan individualmente
    - En la mayoría de casos devuelve valores muy bajos o cero

    **❓ MÓDULOS**: Aplicación limitada, solo para código a nivel de módulo
    - Analiza únicamente el código ejecutable directo del módulo
    - No incluye funciones ni clases (se analizan por separado)
    - Útil para scripts con lógica a nivel de módulo
    - En muchos casos devuelve cero (módulos solo con definiciones)

    **❓ PROYECTOS**: Aplicación teórica, principalmente para análisis de dependencias
    - No es una aplicación estándar de complejidad cognitiva
    - Podría usarse para analizar patrones de dependencias complejas
    - Generalmente no se usa en la práctica
    - En la mayoría de casos devuelve valores muy bajos

    ## Diferencias con Complejidad Ciclomática:

    | Aspecto | Ciclomática | Cognitiva |
    |---------|-------------|-----------|
    | **Anidamiento** | No considera | Penaliza fuertemente |
    | **else/elif** | Cuenta todas | No cuenta else simples |
    | **Operadores booleanos** | Cuenta todos | Solo secuencias |
    | **switch/match** | Cuenta cases | Cuenta estructura + cases |
    | **Enfoque** | Caminos de ejecución | Dificultad mental |

    ## Ejemplo de cálculo:

    ```python
    def ejemplo_cognitiva(items):           # Base = 0
        total = 0
        if len(items) > 0:                  # +1 (B0) + 0 (nivel 0) = 1
            for item in items:              # +1 (B0) + 1 (nivel 1) = 2
                if item.is_valid():         # +1 (B0) + 2 (nivel 2) = 3
                    if item.process():      # +1 (B0) + 3 (nivel 3) = 4
                        total += item.value
                    else:                   # +0 (else simple no cuenta)
                        logger.warning("Failed")
                elif item.is_special():     # +1 (B0) + 2 (nivel 2) = 3
                    total += item.special_value
        return total
    # Complejidad cognitiva total = 1 + 2 + 3 + 4 + 3 = 13
    ```

    ## Beneficios de usar esta métrica:
    - Mejor correlación con la percepción humana de complejidad
    - Identifica código realmente difícil de entender
    - Enfoque en la legibilidad y mantenibilidad
    - Útil para establecer estándares de código
    - Complementa la complejidad ciclomática

    ## Referencias:
    - Campbell, G. A. (2018). "Cognitive Complexity: An Overview and Evaluation"
    - SonarSource White Paper on Cognitive Complexity
    - ISO/IEC 25023:2016 Systems and software engineering
    """

    def __init__(self):
        """Inicializa el calculador de complejidad cognitiva."""
        super().__init__(
            name="cognitive_complexity",
            description="Mide la dificultad de comprensión del código para los desarrolladores.",
        )

    def get_default_thresholds(self) -> Dict[str, float]:
        """Obtiene los umbrales por defecto para complejidad cognitiva.
        
        Basado en investigación de SonarSource y mejores prácticas:
        - 0-15: Fácil de entender
        - 16-25: Moderadamente complejo
        - 26+: Difícil de entender, refactoring recomendado
        
        Returns:
            Dict[str, float]: Umbrales por defecto {low, medium, high}.
        """
        return {
            "low": 15.0,   # 0-15: fácil de entender
            "medium": 25.0, # 16-25: moderadamente complejo
            "high": 50.0,   # 26+: difícil de entender
        }

    def _calculate_cognitive_complexity_ast(
        self, node: ast.AST, nesting_level: int = 0
    ) -> int:
        """Calcula la complejidad cognitiva de un nodo AST.

        Args:
            node: Nodo AST a analizar.
            nesting_level: Nivel de anidamiento actual.

        Returns:
            int: Complejidad cognitiva.
        """
        complexity = 0

        # Estructuras que incrementan complejidad
        if isinstance(node, (ast.If, ast.While, ast.For)):
            # +1 por la estructura de control
            complexity += 1

            # Penalización adicional por anidamiento
            complexity += nesting_level

            # Incrementar nivel de anidamiento para hijos
            nesting_level += 1

        elif isinstance(node, ast.BoolOp):
            # +1 por cada operador booleano adicional
            complexity += len(node.values) - 1

        # Recursivamente analizar hijos
        for child in ast.iter_child_nodes(node):
            complexity += self._calculate_cognitive_complexity_ast(
                child, nesting_level
            )

        return complexity

    def _calculate_cognitive_complexity_astroid(
        self, node: astroid.NodeNG, nesting_level: int = 0
    ) -> int:
        """Calcula la complejidad cognitiva de un nodo Astroid.

        Args:
            node: Nodo Astroid a analizar.
            nesting_level: Nivel de anidamiento actual.

        Returns:
            int: Complejidad cognitiva.
        """
        complexity = 0
        new_nesting_level = nesting_level

        # Estructuras que incrementan complejidad y/o anidamiento
        if isinstance(
            node,
            (
                astroid.nodes.If,
                astroid.nodes.While,
                astroid.nodes.For,
                astroid.nodes.AsyncFor,
            ),
        ):
            complexity += 1  # B0: Incremento base por estructura de control
            complexity += nesting_level  # N: Incremento por anidamiento
            new_nesting_level += (
                1  # Incrementa el nivel para los hijos de esta estructura
            )

        elif isinstance(node, astroid.nodes.Match):
            complexity += 1  # B0: Incremento base por la estructura match
            complexity += nesting_level  # N: Incremento por anidamiento
            # Los case dentro del match no incrementan el new_nesting_level entre sí,
            # pero el contenido de cada case está anidado.
            # El incremento de new_nesting_level para el contenido de los MatchCase se maneja abajo.

        elif isinstance(
            node, astroid.nodes.Try
        ):  # try...except, try...finally, try...except...else...finally
            # El try en sí no incrementa, pero cada handler (except/except*) sí.
            # El contenido de los handlers está anidado.
            pass  # El incremento se maneja al iterar sobre los handlers abajo.

        elif isinstance(node, astroid.nodes.BoolOp):  # and, or
            # B1: Incremento por cada operador booleano adicional en una secuencia
            # (ej. 'a and b and c' tiene +2)
            # No incrementa el nivel de anidamiento.
            complexity += len(node.values) - 1

        elif isinstance(node, astroid.nodes.FunctionDef) or isinstance(
            node, astroid.nodes.AsyncFunctionDef
        ):
            # Las definiciones de funciones anidadas incrementan el nivel de anidamiento
            # pero no la complejidad del método/función exterior directamente.
            # La complejidad de la función anidada se calcula por separado.
            # Aquí, solo ajustamos el nivel de anidamiento para su cuerpo.
            new_nesting_level += 1

        # Recursivamente analizar hijos, aplicando el new_nesting_level
        for child in node.get_children():
            current_child_nesting_level = new_nesting_level
            child_increment = 0

            if isinstance(node, astroid.nodes.Match) and isinstance(
                child, astroid.nodes.MatchCase
            ):
                # Cada MatchCase (case) añade +1 a la complejidad
                # y su cuerpo está anidado dentro del Match.
                complexity += 1  # B0: Incremento por cada case
                current_child_nesting_level += (
                    1  # Cuerpo del case está más anidado
                )
            elif isinstance(node, astroid.nodes.Try) and isinstance(
                child, astroid.nodes.ExceptHandler
            ):
                # Cada ExceptHandler (except/except*) añade +1
                # y su cuerpo está anidado.
                complexity += 1  # B0: Incremento por cada except/except*
                current_child_nesting_level += (
                    1  # Cuerpo del handler está más anidado
                )

            complexity += self._calculate_cognitive_complexity_astroid(
                child, current_child_nesting_level
            )

        return complexity

    def calculate_function(self, function: Function) -> float:
        """Calcula la complejidad cognitiva de una función.

        Esta es la aplicación principal y más valiosa de la complejidad cognitiva.
        Mide qué tan difícil es mentalmente seguir el flujo de control de la función,
        considerando tanto las estructuras de control como su anidamiento.

        Args:
            function: Función a analizar.

        Returns:
            float: Complejidad cognitiva de la función.
        """
        logger.debug(
            f"Calculando complejidad cognitiva para función: {function.name}"
        )
        
        # Calcular directamente desde el nodo AST si está disponible
        if function.astroid_node is not None:
            complexity = self._calculate_cognitive_complexity_astroid(function.astroid_node, 0)
            return float(complexity)

        # Fallback: función sin AST detectable
        logger.debug(f"No hay nodo AST disponible para {function.name}")
        return 0.0

    def calculate_class(self, cls: Class) -> Optional[Dict[str, float]]:
        """Calcula estadísticas de complejidad cognitiva para una clase.

        Analiza la complejidad cognitiva de los métodos de la clase para
        proporcionar estadísticas útiles, pero no suma total.

        Args:
            cls: Clase a analizar.

        Returns:
            Optional[Dict[str, float]]: Estadísticas de complejidad cognitiva de la clase,
                                      o None si no hay métodos.
        """
        logger.debug(
            f"Calculando estadísticas de complejidad cognitiva para clase: {cls.name}"
        )

        if not cls.methods:
            logger.debug(f"Clase {cls.name} sin métodos - devolviendo None")
            return None

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
            "high_complexity_methods": len(
                [c for c in method_complexities if c > 15]
            ),
        }

        return result

    def calculate_module(self, module: Module) -> None:
        """La complejidad cognitiva no se calcula a nivel de módulo.

        La complejidad cognitiva es una métrica específica para evaluar
        la dificultad mental de seguir el flujo de control de funciones
        individuales. No tiene sentido agregar esta métrica a nivel
        de módulo, ya que:

        - Los umbrales están definidos para funciones individuales
        - La suma no proporciona información sobre mantenibilidad
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
            f"Complejidad cognitiva no aplica a módulo: {module.name} - devolviendo None"
        )
        return None

    def calculate_project(self, project: Project) -> None:
        """La complejidad cognitiva no se calcula a nivel de proyecto.

        Similar a módulos, la complejidad cognitiva es una métrica específica
        para funciones individuales y no debe agregarse a nivel de proyecto.

        Args:
            project: Proyecto a analizar.

        Returns:
            None: Siempre None porque no aplica a proyectos.
        """
        logger.debug(
            f"Complejidad cognitiva no aplica a proyecto: {project.name} - devolviendo None"
        )
        return None
