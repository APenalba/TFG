"""Módulo para calcular métricas de líneas de código."""

from typing import Dict, Optional

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


class LinesOfCodeMetric(BaseMetric):
    """Calcula métricas de líneas de código para evaluar el tamaño del software.

    ## ¿Qué son las Líneas de Código?

    Las métricas de líneas de código son medidas básicas pero fundamentales del tamaño
    del software. Fueron introducidas en los primeros estudios de ingeniería de software
    y siguen siendo ampliamente utilizadas para estimación, seguimiento y evaluación.

    ### Tipos de Líneas:

    **LOC (Lines of Code)**: Líneas totales incluyendo espacios en blanco y comentarios
    - **Ventaja**: Métrica simple y objetiva
    - **Uso**: Estimación inicial de tamaño y esfuerzo

    **SLOC (Source Lines of Code)**: Solo líneas con código fuente efectivo
    - **Excluye**: Comentarios, líneas en blanco, solo llaves/paréntesis
    - **Incluye**: Declaraciones, expresiones, sentencias ejecutables
    - **Ventaja**: Mejor indicador de complejidad funcional

    **DLOC (Documentation Lines of Code)**: Líneas de documentación (docstrings)
    - **Uso**: Medir calidad de documentación
    - **Importante**: Para mantenibilidad y comprensión del código

    **CLOC (Comment Lines of Code)**: Líneas de comentarios (excluyendo docstrings)
    - **Uso**: Evaluar nivel de comentarios explicativos
    - **Balance**: Ni muy pocos ni excesivos comentarios

    ## ¿Cómo se calcula?

    ### Para Funciones:
    - **Total LOC**: line_end - line_start + 1
    - **SLOC**: source_lines_of_code (extraído por el parser)
    - **DLOC**: docstring_sloc (extraído por el parser)
    - **CLOC**: comment_sloc (extraído por el parser)
    - **Blank Lines**: blank_lines_count (extraído por el parser)

    ### Para Clases:
    - **Agregación** de métricas de todos los métodos
    - **Plus**: líneas de definición de clase y atributos
    - **Densidad de métodos**: SLOC promedio por método

    ### Para Módulos:
    - **Agregación** de todas las funciones y clases
    - **Plus**: imports, variables globales, código a nivel módulo
    - **Densidad**: SLOC por entidad definida

    ### Algoritmo paso a paso:
    1. **Obtener límites** de la entidad (line_start, line_end)
    2. **Usar datos pre-calculados** del parser (source_lines_of_code, etc.)
    3. **Calcular métricas derivadas** (densidades, ratios)
    4. **Agregar estadísticas** para entidades compuestas

    ## Interpretación de valores:

    ### Para Funciones:
    - **1-20 SLOC**: Función pequeña, fácil de entender
    - **21-50 SLOC**: Función moderada, aceptable
    - **51-100 SLOC**: Función grande, considerar división
    - **100+ SLOC**: Función muy grande, refactoring recomendado

    ### Para Clases:
    - **1-200 SLOC**: Clase pequeña/moderada
    - **201-500 SLOC**: Clase grande, revisar responsabilidades
    - **501-1000 SLOC**: Clase muy grande, probable violación SRP
    - **1000+ SLOC**: Clase excesiva, refactoring urgente

    ### Para Módulos:
    - **1-500 SLOC**: Módulo manejable
    - **501-1500 SLOC**: Módulo grande pero aceptable
    - **1501-3000 SLOC**: Módulo muy grande, considerar división
    - **3000+ SLOC**: Módulo excesivo, modularización necesaria

    ### Ratios Importantes:
    - **Documentation Ratio**: DLOC / SLOC
      - 0.1-0.3: Buena documentación
      - < 0.1: Documentación insuficiente
      - > 0.5: Posible sobre-documentación

    - **Comment Ratio**: CLOC / SLOC
      - 0.1-0.2: Comentarios adecuados
      - < 0.05: Comentarios insuficientes
      - > 0.3: Posibles comentarios excesivos

    ## ¿Cuándo se aplica?

    **✅ FUNCIONES**: Aplicación fundamental
    - Identificar funciones muy largas que requieren división
    - Estimar esfuerzo de testing y review
    - Detectar complejidad potencial
    - Útil para métricas de productividad

    **✅ CLASES**: Aplicación muy valiosa
    - Evaluar si la clase tiene demasiadas responsabilidades
    - Identificar candidatos para refactoring
    - Métricas de cohesión y diseño
    - Planificación de testing de integración

    **✅ MÓDULOS**: Aplicación crítica
    - Decisiones de modularización y arquitectura
    - Identificar módulos que necesitan división
    - Métricas de mantenibilidad
    - Planificación de releases y desarrollo

    **✅ PROYECTOS**: Aplicación esencial
    - Seguimiento de crecimiento del proyecto
    - Estimaciones de esfuerzo y tiempo
    - Métricas de productividad del equipo
    - Decisiones arquitectónicas de alto nivel

    ## Ejemplo de cálculo:

    ```python
    def ejemplo_funcion(param1, param2):
        '''Esta es la docstring de la función.
        Explica lo que hace la función.'''

        # Este es un comentario explicativo
        if param1 > 0:
            result = param1 + param2
            return result
        else:
            # Otro comentario
            return 0

    # Métricas calculadas:
    # Total LOC = 11 líneas (incluyendo blancos)
    # SLOC = 6 líneas (código ejecutable)
    # DLOC = 2 líneas (docstring)
    # CLOC = 2 líneas (comentarios)
    # Blank Lines = 1 línea
    ```

    ## Beneficios de usar estas métricas:
    - **Simplicidad**: Fáciles de entender y calcular
    - **Universalidad**: Aplicables a cualquier lenguaje
    - **Seguimiento**: Útiles para tracking temporal
    - **Estimación**: Base para estimaciones de esfuerzo
    - **Calidad**: Correlación con complejidad y defectos
    - **Mantenimiento**: Identificar código que necesita atención

    ## Limitaciones importantes:
    - **No miden complejidad real**: Líneas simples vs. complejas
    - **Pueden incentivar mal código**: Muchas líneas ≠ más productividad
    - **Dependiente del estilo**: Formatting afecta los números
    - **No consideran algoritmos**: Implementación eficiente vs. verbosa

    ## Referencias:
    - Jones, C. (2013). "The Economics of Software Quality"
    - IEEE Standard 982.1-2005 for Software Engineering
    - ISO/IEC 25023:2016 Systems and software engineering
    - Boehm, B. (1981). "Software Engineering Economics"
    """

    def __init__(self):
        """Inicializa el calculador de métricas de líneas de código."""
        super().__init__(
            name="lines_of_code",
            description="Mide el tamaño del software contando diferentes tipos de líneas de código.",
        )

    def get_default_thresholds(self) -> Dict[str, float]:
        """Obtiene los umbrales por defecto para lines_of_code.
        
        Basado en estudios de mantenibilidad de código.
        
        Returns:
            Dict[str, float]: Umbrales por defecto {low, medium, high}.
        """
        return {
            "low": 30.0,
            "medium": 75.0,
            "high": 150.0,
        }


    def calculate_function(self, function: Function) -> float:
        """Calcula las líneas de código fuente efectivas para una función.

        Esta es la aplicación principal de la métrica LOC para funciones individuales.
        Retorna el SLOC como valor primario ya que es el más indicativo de complejidad.

        Args:
            function: Función a analizar.

        Returns:
            float: Líneas de código fuente efectivas (SLOC) de la función.
        """
        logger.debug(f"Calculando LOC para función: {function.name}")
        return float(function.source_lines_of_code)

    def calculate_class(self, cls: Class) -> Dict[str, float]:
        """Calcula métricas de líneas de código para una clase.

        Analiza el tamaño de la clase tanto a nivel de definición como agregando
        las métricas de sus métodos. No incluye resultados individuales de métodos
        ya que el MetricsEngine los analiza por separado.

        Args:
            cls: Clase a analizar.

        Returns:
            Dict[str, float]: Diccionario con métricas de líneas de código de la clase.
        """
        logger.debug(f"Calculando LOC para clase: {cls.name}")

        # Métricas básicas de la clase
        total_loc = cls.length
        class_sloc = cls.source_lines_of_code
        class_dloc = cls.docstring_sloc
        class_cloc = cls.comment_sloc
        class_blank = cls.blank_lines_count

        # Agregación de métricas de métodos
        total_methods_sloc = 0
        method_slocs = []

        for method in cls.methods:
            method_sloc = method.source_lines_of_code
            total_methods_sloc += method_sloc
            method_slocs.append(method_sloc)

        # Cálculos agregados
        total_sloc = class_sloc + total_methods_sloc
        avg_method_sloc = (
            total_methods_sloc / len(cls.methods) if cls.methods else 0.0
        )
        max_method_sloc = max(method_slocs) if method_slocs else 0.0

        # Ratios de calidad
        doc_ratio = class_dloc / total_sloc if total_sloc > 0 else 0.0
        comment_ratio = class_cloc / total_sloc if total_sloc > 0 else 0.0

        result = {
            "total_loc": float(total_loc),
            "total_sloc": float(total_sloc),
            "class_sloc": float(class_sloc),
            "methods_sloc": float(total_methods_sloc),
            "avg_method_sloc": avg_method_sloc,
            "max_method_sloc": max_method_sloc,
            "documentation_lines": float(class_dloc),
            "comment_lines": float(class_cloc),
            "blank_lines": float(class_blank),
            "documentation_ratio": doc_ratio,
            "comment_ratio": comment_ratio,
        }

        return result

    def calculate_module(self, module: Module) -> Dict[str, float]:
        """Calcula métricas de líneas de código para un módulo.

        Analiza el tamaño total del módulo incluyendo funciones, clases e imports.
        No incluye resultados individuales ya que el MetricsEngine los analiza por separado.

        Args:
            module: Módulo a analizar.

        Returns:
            Dict[str, float]: Diccionario con métricas de líneas de código del módulo.
        """
        logger.debug(f"Calculando LOC para módulo: {module.name}")

        # Métricas básicas del módulo
        total_loc = module.length
        module_sloc = module.source_lines_of_code
        module_dloc = module.docstring_sloc
        module_cloc = module.comment_sloc
        module_blank = module.blank_lines_count

        # Agregación de funciones a nivel módulo
        functions_sloc = sum(
            func.source_lines_of_code for func in module.functions
        )

        # Agregación de clases y sus métodos
        classes_sloc = 0
        for cls in module.classes:
            classes_sloc += cls.source_lines_of_code
            for method in cls.methods:
                classes_sloc += method.source_lines_of_code

        # Métricas derivadas
        total_entities = len(module.functions) + len(module.classes)
        total_code_sloc = functions_sloc + classes_sloc
        avg_entity_sloc = (
            total_code_sloc / total_entities if total_entities > 0 else 0.0
        )

        # Densidad de imports
        import_density = (
            len(module.imports) / total_loc if total_loc > 0 else 0.0
        )

        # Ratios de calidad
        doc_ratio = module_dloc / module_sloc if module_sloc > 0 else 0.0
        comment_ratio = module_cloc / module_sloc if module_sloc > 0 else 0.0

        result = {
            "total_loc": float(total_loc),
            "total_sloc": float(module_sloc),
            "functions_sloc": float(functions_sloc),
            "classes_sloc": float(classes_sloc),
            "total_code_sloc": float(total_code_sloc),
            "avg_entity_sloc": avg_entity_sloc,
            "documentation_lines": float(module_dloc),
            "comment_lines": float(module_cloc),
            "blank_lines": float(module_blank),
            "import_count": float(len(module.imports)),
            "import_density": import_density,
            "documentation_ratio": doc_ratio,
            "comment_ratio": comment_ratio,
            "entity_count": float(total_entities),
        }

        return result

    def calculate_project(self, project: Project) -> Dict[str, float]:
        """Calcula estadísticas de líneas de código a nivel de proyecto.

        Proporciona métricas agregadas de tamaño para todo el proyecto.
        Esto es útil para métricas de seguimiento, estimación y calidad general.

        Args:
            project: Proyecto a analizar.

        Returns:
            Dict[str, float]: Diccionario con estadísticas agregadas de LOC del proyecto.
        """
        logger.debug(f"Calculando LOC para proyecto: {project.name}")

        # Agregación de todos los módulos
        total_loc = 0
        total_sloc = 0
        total_dloc = 0
        total_cloc = 0
        total_blank = 0
        total_imports = 0

        module_slocs = []
        all_function_slocs = []
        all_class_slocs = []

        for module in project.modules:
            # Métricas del módulo
            module_loc = module.length
            module_sloc_val = module.source_lines_of_code

            total_loc += module_loc
            total_sloc += module_sloc_val
            total_dloc += module.docstring_sloc
            total_cloc += module.comment_sloc
            total_blank += module.blank_lines_count
            total_imports += len(module.imports)

            module_slocs.append(module_sloc_val)

            # Funciones del módulo
            for func in module.functions:
                all_function_slocs.append(func.source_lines_of_code)

            # Clases del módulo
            for cls in module.classes:
                class_total_sloc = cls.source_lines_of_code
                for method in cls.methods:
                    class_total_sloc += method.source_lines_of_code
                all_class_slocs.append(class_total_sloc)

        # Estadísticas agregadas
        total_entities = len(all_function_slocs) + len(all_class_slocs)
        avg_entity_sloc = (
            (sum(all_function_slocs) + sum(all_class_slocs)) / total_entities
            if total_entities > 0
            else 0.0
        )
        avg_module_sloc = (
            total_sloc / len(project.modules) if project.modules else 0.0
        )

        # Ratios de calidad del proyecto
        doc_ratio = total_dloc / total_sloc if total_sloc > 0 else 0.0
        comment_ratio = total_cloc / total_sloc if total_sloc > 0 else 0.0
        import_density = total_imports / total_loc if total_loc > 0 else 0.0

        result = {
            "total_loc": float(total_loc),
            "total_sloc": float(total_sloc),
            "total_documentation_lines": float(total_dloc),
            "total_comment_lines": float(total_cloc),
            "total_blank_lines": float(total_blank),
            "total_imports": float(total_imports),
            "module_count": float(len(project.modules)),
            "total_entities": float(total_entities),
            "avg_module_sloc": avg_module_sloc,
            "avg_entity_sloc": avg_entity_sloc,
            "max_module_sloc": float(max(module_slocs))
            if module_slocs
            else 0.0,
            "documentation_ratio": doc_ratio,
            "comment_ratio": comment_ratio,
            "import_density": import_density,
        }

        return result

    def calculate(self, entity: CodeEntity) -> float:
        """Calcula la métrica para una entidad específica delegando al método apropiado.

        Args:
            entity: Entidad de código a analizar.

        Returns:
            float: Valor de la métrica para la entidad.
        """
        if isinstance(entity, Function):
            return self.calculate_function(entity)
        elif isinstance(entity, Class):
            class_result = self.calculate_class(entity)
            return class_result.get("total_sloc", 0.0)
        elif isinstance(entity, Module):
            module_result = self.calculate_module(entity)
            return module_result.get("total_sloc", 0.0)
        elif isinstance(entity, Project):
            project_result = self.calculate_project(entity)
            return project_result.get("total_sloc", 0.0)
        else:
            logger.warning(f"Tipo de entidad no soportado: {type(entity)}")
            return 0.0

    def get_aggregated_value(self, entity: CodeEntity) -> float:
        """Obtiene un valor agregado para usar con umbrales.

        Args:
            entity: Entidad de código a analizar.

        Returns:
            float: Valor agregado de líneas de código.
        """
        result = self.calculate(entity)
        return float(result) if isinstance(result, (int, float)) else 0.0
