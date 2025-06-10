"""Módulo para calcular métricas de Halstead de Software."""

import math
from typing import Dict, Optional, Set, Union

from pypex.metrics.base import BaseMetric
from pypex.parser.code_entities import (
    Class,
    CodeEntity,
    Function,
    Module,
    Project,
)
from pypex.services.logging_service import get_logger

logger = get_logger(__name__)


class HalsteadMetric(BaseMetric):
    """Calcula las métricas de Halstead para evaluar complejidad de software.

    ## ¿Qué son las métricas de Halstead?

    Las métricas de Halstead, desarrolladas por Maurice Howard Halstead en 1977,
    son un conjunto de métricas de software que miden la complejidad de programas
    basándose en el conteo de operadores y operandos únicos y totales.

    ### Fundamentos teóricos:
    - **Operadores**: Símbolos que representan acciones (ej: +, -, =, if, while, def)
    - **Operandos**: Símbolos que representan datos (ej: variables, constantes, nombres de funciones)
    - **Vocabulario**: Conjunto de operadores y operandos únicos
    - **Longitud**: Total de operadores y operandos utilizados

    ## Métricas calculadas:

    ### 1. Program Length (N):
    **N = N1 + N2**
    - N1: Total de operadores utilizados
    - N2: Total de operandos utilizados
    - Representa el tamaño total del programa

    ### 2. Vocabulary (η):
    **η = η1 + η2**
    - η1: Número de operadores únicos
    - η2: Número de operandos únicos
    - Indica la riqueza del vocabulario del programa

    ### 3. Program Volume (V):
    **V = N × log₂(η)**
    - Mide el "volumen" de información en el programa
    - Unidades: bits de información
    - Relacionado con el esfuerzo mental requerido para entender el código

    ### 4. Difficulty (D):
    **D = (η1 / 2) × (N2 / η2)**
    - η1/2: Dificultad inherente (número de operadores únicos / 2)
    - N2/η2: Frecuencia promedio de uso de operandos
    - Mide qué tan difícil es escribir o entender el programa

    ### 5. Effort (E):
    **E = D × V**
    - Esfuerzo mental requerido para desarrollar el programa
    - Unidades: discriminaciones mentales elementales
    - Útil para estimación de tiempo de desarrollo

    ### 6. Time to Program (T):
    **T = E / 18**
    - Tiempo estimado para programar en segundos
    - Basado en que un programador hace ~18 discriminaciones por segundo
    - Factor 18 es empírico de estudios de Halstead

    ### 7. Bugs Delivered (B):
    **B = V / 3000**
    - Número estimado de errores en el programa entregado
    - Basado en observaciones empíricas de que hay ~1 error por cada 3000 bits
    - Factor 3000 es empírico de estudios de Halstead

    ## ¿Cómo se identifican operadores y operandos?

    ### Operadores típicos en Python:
    - **Aritméticos**: +, -, *, /, //, %, **
    - **Comparación**: ==, !=, <, >, <=, >=, is, in
    - **Lógicos**: and, or, not
    - **Asignación**: =, +=, -=, *=, etc.
    - **Control de flujo**: if, elif, else, for, while, break, continue
    - **Funciones**: def, return, yield, lambda
    - **Clases**: class, self
    - **Excepciones**: try, except, finally, raise
    - **Importaciones**: import, from, as
    - **Acceso**: ., [], ()

    ### Operandos típicos en Python:
    - **Variables**: nombres de variables locales y globales
    - **Literales**: números, strings, None, True, False
    - **Nombres de funciones**: cuando se llaman
    - **Nombres de clases**: cuando se instancian
    - **Nombres de módulos**: en importaciones
    - **Atributos**: después del operador punto

    ## Interpretación de valores:

    ### Program Length (N):
    - **< 100**: Programa muy pequeño
    - **100-500**: Programa pequeño a moderado
    - **500-2000**: Programa moderado a grande
    - **> 2000**: Programa muy grande

    ### Vocabulary (η):
    - **< 20**: Vocabulario muy limitado
    - **20-50**: Vocabulario moderado
    - **50-100**: Vocabulario rico
    - **> 100**: Vocabulario muy rico

    ### Program Volume (V):
    - **< 500**: Volumen bajo, código simple
    - **500-2000**: Volumen moderado
    - **2000-8000**: Volumen alto
    - **> 8000**: Volumen muy alto, considerar modularización

    ### Difficulty (D):
    - **< 10**: Dificultad baja, código fácil de entender
    - **10-20**: Dificultad moderada
    - **20-40**: Dificultad alta
    - **> 40**: Dificultad muy alta, refactoring recomendado

    ### Effort (E):
    - **< 5000**: Esfuerzo bajo
    - **5000-20000**: Esfuerzo moderado
    - **20000-80000**: Esfuerzo alto
    - **> 80000**: Esfuerzo muy alto

    ### Time to Program (T):
    - Se interpreta directamente en segundos
    - Dividir por 3600 para obtener horas
    - Útil para estimaciones de desarrollo

    ### Bugs Delivered (B):
    - Se interpreta directamente como número de errores esperados
    - Útil para planificación de testing y QA
    - Valores altos indican necesidad de revisión exhaustiva

    ## ¿Cuándo se aplica?

    **✅ FUNCIONES**: Aplicación principal y más útil
    - Análisis detallado de complejidad a nivel granular
    - Identificación de funciones problemáticas
    - Estimación de esfuerzo de desarrollo
    - Predicción de errores potenciales

    **✅ CLASES**: Aplicación valiosa
    - Análisis de complejidad de definición de clase
    - Evaluación de diseño de clase
    - Métricas agregadas de métodos
    - Útil para decisiones de refactoring

    **✅ MÓDULOS**: Aplicación importante
    - Análisis de complejidad a nivel de archivo
    - Evaluación de tamaño y organización del módulo
    - Identificación de módulos sobrecargados
    - Planificación de división de módulos

    **✅ PROYECTOS**: Aplicación agregada muy valiosa
    - Métricas de complejidad general del proyecto
    - Comparación entre proyectos
    - Tracking de evolución de complejidad
    - Estimaciones de esfuerzo total
    - Predicción de errores totales

    ## Beneficios de usar estas métricas:
    - **Estimación objetiva**: Predicción de tiempo y esfuerzo de desarrollo
    - **Detección de complejidad**: Identificación de código problemático
    - **Predicción de errores**: Estimación de bugs potenciales
    - **Comparación**: Evaluación objetiva entre diferentes implementaciones
    - **Evolución**: Tracking de cambios de complejidad a lo largo del tiempo
    - **Planificación**: Ayuda en decisiones de arquitectura y refactoring

    ## Limitaciones:
    - **Factor empírico**: Los factores 18 y 3000 son empíricos y pueden no aplicar universalmente
    - **Lenguaje específico**: Métricas desarrolladas originalmente para lenguajes procedurales
    - **Contexto**: No considera complejidad conceptual o del dominio
    - **Calidad**: No mide directamente la calidad del código

    ## Referencias:
    - Halstead, M. H. (1977). "Elements of Software Science"
    - IEEE Standard 982.1-2005 for Software Engineering Metrics
    - ISO/IEC 25023:2016 Systems and software engineering
    - McCabe, T. J. (1976). "A Complexity Measure" (para comparación con métricas relacionadas)
    """

    def __init__(self):
        """Inicializa el calculador de métricas de Halstead."""
        super().__init__(
            name="halstead",
            description="Calcula métricas de Halstead basadas en operadores y operandos: longitud, vocabulario, volumen, dificultad, esfuerzo, tiempo y errores estimados.",
        )

    def get_default_thresholds(self) -> Dict[str, float]:
        """Obtiene los umbrales por defecto para halstead.
        
        Basado en volumen de Halstead y vocabulario.
        
        Returns:
            Dict[str, float]: Umbrales por defecto {low, medium, high}.
        """
        return {
            "low": 500.0,
            "medium": 2000.0,
            "high": 8000.0,
        }


    def _calculate_halstead_metrics(
        self, operators_count: Dict[str, int], operands_count: Dict[str, int]
    ) -> Dict[str, float]:
        """Calcula todas las métricas de Halstead a partir de conteos de operadores y operandos.

        Args:
            operators_count: Diccionario con conteo de operadores.
            operands_count: Diccionario con conteo de operandos.

        Returns:
            Dict[str, float]: Diccionario con todas las métricas de Halstead.
        """
        # Métricas básicas
        eta1 = len(operators_count)  # η1: operadores únicos
        eta2 = len(operands_count)  # η2: operandos únicos
        N1 = sum(operators_count.values())  # N1: total operadores
        N2 = sum(operands_count.values())  # N2: total operandos

        # Prevenir división por cero
        if eta1 == 0 and eta2 == 0:
            return {
                "eta1": 0.0,
                "eta2": 0.0,
                "N1": 0.0,
                "N2": 0.0,
                "vocabulary": 0.0,
                "length": 0.0,
                "volume": 0.0,
                "difficulty": 0.0,
                "effort": 0.0,
                "time": 0.0,
                "bugs": 0.0,
            }

        # Métricas derivadas
        vocabulary = eta1 + eta2  # η: vocabulario total
        length = N1 + N2  # N: longitud total

        # Volume (V = N * log2(η))
        volume = 0.0
        if vocabulary > 0:
            volume = length * math.log2(vocabulary)

        # Difficulty (D = (η1/2) * (N2/η2))
        difficulty = 0.0
        if eta1 > 0 and eta2 > 0:
            difficulty = (eta1 / 2.0) * (N2 / eta2)

        # Effort (E = D * V)
        effort = difficulty * volume

        # Time to Program (T = E / 18)
        time = effort / 18.0

        # Bugs Delivered (B = V / 3000)
        bugs = volume / 3000.0

        return {
            "eta1": float(eta1),
            "eta2": float(eta2),
            "N1": float(N1),
            "N2": float(N2),
            "vocabulary": vocabulary,
            "length": length,
            "volume": volume,
            "difficulty": difficulty,
            "effort": effort,
            "time": time,
            "bugs": bugs,
        }

    def _extract_operators_and_operands_from_ast(
        self, func_node
    ) -> tuple[Dict[str, int], Dict[str, int]]:
        """Extrae operadores y operandos de un nodo AST de Astroid.

        Args:
            func_node: Nodo de función de Astroid.

        Returns:
            tuple[Dict[str, int], Dict[str, int]]: Conteos de operadores y operandos.
        """
        # Importar aquí para evitar dependencias circulares
        try:
            from astroid import nodes as astroid_nodes
        except ImportError:
            logger.warning("Astroid no disponible para análisis de Halstead")
            return {}, {}

        operators: Dict[str, int] = {}
        operands: Dict[str, int] = {}

        def visit(node):
            if isinstance(
                node,
                (
                    astroid_nodes.BinOp,
                    astroid_nodes.UnaryOp,
                    astroid_nodes.Compare,
                    astroid_nodes.BoolOp,
                    astroid_nodes.Assign,
                ),
            ):
                op_name = type(node).__name__
                if hasattr(node, "op"):
                    op_name = (
                        node.op
                        if isinstance(node.op, str)
                        else type(node.op).__name__
                    )
                elif isinstance(node, astroid_nodes.Compare):
                    op_name = node.ops[0][0]

                operators[op_name] = operators.get(op_name, 0) + 1

            elif isinstance(node, astroid_nodes.Call):
                operators["Call"] = operators.get("Call", 0) + 1
                if hasattr(node.func, "as_string"):
                    operands[node.func.as_string()] = (
                        operands.get(node.func.as_string(), 0) + 1
                    )

            elif isinstance(node, astroid_nodes.Name):
                operands[node.name] = operands.get(node.name, 0) + 1
            elif isinstance(node, astroid_nodes.Const):
                operands[str(node.value)] = (
                    operands.get(str(node.value), 0) + 1
                )
            elif isinstance(node, astroid_nodes.Attribute):
                if hasattr(node.expr, "as_string"):
                    operands[node.expr.as_string()] = (
                        operands.get(node.expr.as_string(), 0) + 1
                    )
                operators["."] = operators.get(".", 0) + 1

            for child in node.get_children():
                visit(child)

        if isinstance(func_node, astroid_nodes.Lambda):
            visit(func_node.body)
        elif hasattr(func_node, "body"):
            for stmt in func_node.body:
                visit(stmt)

        return operators, operands

    def calculate_function(
        self, function: Function
    ) -> Optional[Dict[str, float]]:
        """Calcula métricas de Halstead para una función.

        Analiza directamente el nodo AST para identificar operadores y operandos.
        Si no hay nodo AST disponible, utiliza operators_count y operands_count
        como fallback (útil para testing y compatibilidad).

        Args:
            function: Función a analizar.

        Returns:
            Optional[Dict[str, float]]: Métricas de Halstead de la función.
        """
        logger.debug(
            f"Calculando métricas de Halstead para función: {function.name}"
        )

        # Prioridad 1: Calcular operadores y operandos directamente desde el nodo AST
        if function.astroid_node is not None:
            operators_count, operands_count = self._extract_operators_and_operands_from_ast(
                function.astroid_node
            )
            
            # Si el análisis AST produjo resultados, usarlos
            if operators_count or operands_count:
                return self._calculate_halstead_metrics(operators_count, operands_count)

        # Prioridad 2: Fallback usando operators_count y operands_count (para testing y compatibilidad)
        if (hasattr(function, 'operators_count') and hasattr(function, 'operands_count') and
            function.operators_count is not None and function.operands_count is not None):
            
            return self._calculate_halstead_metrics(
                function.operators_count, function.operands_count
            )

        # Fallback final: función sin AST ni conteos disponibles
        logger.debug(
            f"No hay nodo AST ni conteos disponibles para {function.name}"
        )
        return {
            "eta1": 0.0,
            "eta2": 0.0,
            "N1": 0.0,
            "N2": 0.0,
            "vocabulary": 0.0,
            "length": 0.0,
            "volume": 0.0,
            "difficulty": 0.0,
            "effort": 0.0,
            "time": 0.0,
            "bugs": 0.0,
        }

    def calculate_class(self, cls: Class) -> Optional[Dict[str, float]]:
        """Calcula estadísticas de métricas de Halstead para una clase.

        En lugar de agregar conteos (que no serían comparables con umbrales),
        calcula estadísticas útiles e interpretables de los métodos de la clase.

        Args:
            cls: Clase a analizar.

        Returns:
            Optional[Dict[str, float]]: Estadísticas de Halstead de la clase.
        """
        logger.debug(
            f"Calculando estadísticas de Halstead para clase: {cls.name}"
        )

        if not cls.methods:
            return {
                "avg_volume": 0.0,
                "max_volume": 0.0,
                "min_volume": 0.0,
                "avg_difficulty": 0.0,
                "max_difficulty": 0.0,
                "method_count": 0.0,
                "high_volume_methods": 0.0,
                "high_difficulty_methods": 0.0,
            }

        method_volumes = []
        method_difficulties = []

        # Calcular métricas para cada método
        for method in cls.methods:
            method_halstead = self.calculate_function(method)
            if method_halstead:
                method_volumes.append(method_halstead.get("volume", 0.0))
                method_difficulties.append(
                    method_halstead.get("difficulty", 0.0)
                )

        if not method_volumes:
            return {
                "avg_volume": 0.0,
                "max_volume": 0.0,
                "min_volume": 0.0,
                "avg_difficulty": 0.0,
                "max_difficulty": 0.0,
                "method_count": float(len(cls.methods)),
                "high_volume_methods": 0.0,
                "high_difficulty_methods": 0.0,
            }

        # Estadísticas interpretables
        result = {
            "avg_volume": sum(method_volumes) / len(method_volumes),
            "max_volume": max(method_volumes),
            "min_volume": min(method_volumes),
            "avg_difficulty": sum(method_difficulties)
            / len(method_difficulties),
            "max_difficulty": max(method_difficulties),
            "method_count": float(len(cls.methods)),
            "high_volume_methods": len(
                [v for v in method_volumes if v > 2000]
            ),
            "high_difficulty_methods": len(
                [d for d in method_difficulties if d > 20]
            ),
        }

        return result

    def calculate_module(self, module: Module) -> Optional[Dict[str, float]]:
        """Calcula estadísticas de métricas de Halstead para un módulo.

        En lugar de agregar conteos, proporciona estadísticas útiles e interpretables
        sobre la distribución de complejidad Halstead en el módulo.

        Args:
            module: Módulo a analizar.

        Returns:
            Optional[Dict[str, float]]: Estadísticas de Halstead del módulo.
        """
        logger.debug(
            f"Calculando estadísticas de Halstead para módulo: {module.name}"
        )

        all_volumes = []
        all_difficulties = []
        entity_count = 0

        # Recopilar métricas de funciones del módulo
        for function in module.functions:
            function_halstead = self.calculate_function(function)
            if function_halstead:
                all_volumes.append(function_halstead.get("volume", 0.0))
                all_difficulties.append(
                    function_halstead.get("difficulty", 0.0)
                )
                entity_count += 1

        # Recopilar métricas de métodos de clases del módulo
        for cls in module.classes:
            for method in cls.methods:
                method_halstead = self.calculate_function(method)
                if method_halstead:
                    all_volumes.append(method_halstead.get("volume", 0.0))
                    all_difficulties.append(
                        method_halstead.get("difficulty", 0.0)
                    )
                    entity_count += 1

        if not all_volumes:
            return {
                "avg_volume": 0.0,
                "max_volume": 0.0,
                "min_volume": 0.0,
                "avg_difficulty": 0.0,
                "max_difficulty": 0.0,
                "entity_count": 0.0,
                "high_volume_entities": 0.0,
                "high_difficulty_entities": 0.0,
                "volume_distribution": 0.0,  # Desviación estándar del volumen
            }

        # Calcular desviación estándar del volumen para medir distribución
        avg_volume = sum(all_volumes) / len(all_volumes)
        volume_variance = sum(
            (v - avg_volume) ** 2 for v in all_volumes
        ) / len(all_volumes)
        volume_std = volume_variance**0.5

        result = {
            "avg_volume": avg_volume,
            "max_volume": max(all_volumes),
            "min_volume": min(all_volumes),
            "avg_difficulty": sum(all_difficulties) / len(all_difficulties),
            "max_difficulty": max(all_difficulties),
            "entity_count": float(entity_count),
            "high_volume_entities": len([v for v in all_volumes if v > 2000]),
            "high_difficulty_entities": len(
                [d for d in all_difficulties if d > 20]
            ),
            "volume_distribution": volume_std,
        }

        return result

    def calculate_project(
        self, project: Project
    ) -> Optional[Dict[str, float]]:
        """Calcula estadísticas de métricas de Halstead para un proyecto.

        Proporciona métricas agregadas e interpretables para evaluar
        la complejidad general de Halstead del proyecto.

        Args:
            project: Proyecto a analizar.

        Returns:
            Optional[Dict[str, float]]: Estadísticas de Halstead del proyecto.
        """
        logger.debug(
            f"Calculando estadísticas de Halstead para proyecto: {project.name}"
        )

        all_volumes = []
        all_difficulties = []
        module_avg_volumes = []
        total_entities = 0

        # Recopilar métricas de todos los módulos
        for module in project.modules:
            module_volumes = []

            # Funciones del módulo
            for function in module.functions:
                function_halstead = self.calculate_function(function)
                if function_halstead:
                    volume = function_halstead.get("volume", 0.0)
                    difficulty = function_halstead.get("difficulty", 0.0)
                    all_volumes.append(volume)
                    all_difficulties.append(difficulty)
                    module_volumes.append(volume)
                    total_entities += 1

            # Métodos de clases del módulo
            for cls in module.classes:
                for method in cls.methods:
                    method_halstead = self.calculate_function(method)
                    if method_halstead:
                        volume = method_halstead.get("volume", 0.0)
                        difficulty = method_halstead.get("difficulty", 0.0)
                        all_volumes.append(volume)
                        all_difficulties.append(difficulty)
                        module_volumes.append(volume)
                        total_entities += 1

            # Promedio del módulo para análisis de distribución
            if module_volumes:
                module_avg_volumes.append(
                    sum(module_volumes) / len(module_volumes)
                )

        if not all_volumes:
            return {
                "avg_volume": 0.0,
                "max_volume": 0.0,
                "min_volume": 0.0,
                "avg_difficulty": 0.0,
                "max_difficulty": 0.0,
                "total_entities": 0.0,
                "module_count": float(len(project.modules)),
                "high_volume_entities": 0.0,
                "high_difficulty_entities": 0.0,
                "project_volume_distribution": 0.0,
                "module_volume_distribution": 0.0,
            }

        # Estadísticas a nivel de proyecto
        avg_volume = sum(all_volumes) / len(all_volumes)
        avg_difficulty = sum(all_difficulties) / len(all_difficulties)

        # Distribución del volumen a nivel de entidades
        project_volume_variance = sum(
            (v - avg_volume) ** 2 for v in all_volumes
        ) / len(all_volumes)
        project_volume_std = project_volume_variance**0.5

        # Distribución del volumen a nivel de módulos
        module_volume_std = 0.0
        if len(module_avg_volumes) > 1:
            avg_module_volume = sum(module_avg_volumes) / len(
                module_avg_volumes
            )
            module_variance = sum(
                (v - avg_module_volume) ** 2 for v in module_avg_volumes
            ) / len(module_avg_volumes)
            module_volume_std = module_variance**0.5

        result = {
            "avg_volume": avg_volume,
            "max_volume": max(all_volumes),
            "min_volume": min(all_volumes),
            "avg_difficulty": avg_difficulty,
            "max_difficulty": max(all_difficulties),
            "total_entities": float(total_entities),
            "module_count": float(len(project.modules)),
            "high_volume_entities": len([v for v in all_volumes if v > 2000]),
            "high_difficulty_entities": len(
                [d for d in all_difficulties if d > 20]
            ),
            "project_volume_distribution": project_volume_std,
            "module_volume_distribution": module_volume_std,
        }

        return result

    def calculate(self, entity: CodeEntity) -> Union[Dict[str, float], None]:
        """Calcula las métricas de Halstead para una entidad específica.

        Args:
            entity: Entidad de código a analizar.

        Returns:
            Union[Dict[str, float], None]: Métricas de Halstead para la entidad.
        """
        if isinstance(entity, Function):
            return self.calculate_function(entity)
        elif isinstance(entity, Class):
            return self.calculate_class(entity)
        elif isinstance(entity, Module):
            return self.calculate_module(entity)
        elif isinstance(entity, Project):
            return self.calculate_project(entity)
        else:
            logger.warning(f"Tipo de entidad no soportado: {type(entity)}")
            return None

    def get_aggregated_value(self, entity: CodeEntity) -> float:
        """Obtiene un valor agregado interpretable para usar con umbrales.

        Para funciones devuelve volumen directo, para otras entidades devuelve
        el volumen promedio que sí es comparable con umbrales de función.

        Args:
            entity: Entidad de código a analizar.

        Returns:
            float: Valor interpretable para comparar con umbrales.
        """
        result = self.calculate(entity)
        if result is None:
            return 0.0

        if isinstance(entity, Function):
            # Para funciones, devolver volumen directo
            return result.get("volume", 0.0)
        elif isinstance(entity, (Class, Module, Project)):
            # Para agregaciones, devolver volumen promedio que es comparable con umbrales
            return result.get("avg_volume", 0.0)
        else:
            return 0.0
