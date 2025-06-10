"""Módulo para calcular métricas de conteo de parámetros."""

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


class ParameterCountMetric(BaseMetric):
    """Calcula métricas de conteo de parámetros para evaluar complejidad de interfaces.

    ## ¿Qué es el Conteo de Parámetros?

    El conteo de parámetros es una métrica fundamental que mide la complejidad de la
    interfaz de funciones y métodos. Esta métrica está directamente relacionada con
    la facilidad de uso, testing y mantenimiento del código.

    ### Importancia de la Métrica:

    **Complejidad de Interfaz**: Número de parámetros indica complejidad de uso
    - **Pocas parámetros**: Función fácil de entender y usar
    - **Muchos parámetros**: Interfaz compleja, propensa a errores

    **Facilidad de Testing**: Parámetros afectan combinaciones de pruebas
    - **Pocos parámetros**: Testing exhaustivo factible
    - **Muchos parámetros**: Testing combinatorial explota exponencialmente

    **Mantenibilidad**: Cambios en parámetros afectan todos los llamadores
    - **Interfaz estable**: Pocos parámetros, cambios poco frecuentes
    - **Interfaz volátil**: Muchos parámetros, cambios frecuentes y riesgosos

    ### Tipos de Parámetros Analizados:

    **Parámetros Regulares**: Parámetros posicionales y con nombre
    - Conteo básico y más importante
    - Indica complejidad directa de la función

    **Parámetros con Valores por Defecto**: Parámetros opcionales
    - Reducen complejidad percibida de uso
    - Indican flexibilidad de la interfaz

    **Parámetros Varargs**: *args y **kwargs
    - *args: Parámetros posicionales variables
    - **kwargs: Parámetros de palabra clave variables
    - Indican interfaces muy flexibles pero potencialmente complejas

    **Parámetros con Anotaciones de Tipo**: Parámetros tipados
    - Mejoran claridad y documentación
    - Facilitan detección temprana de errores

    ## ¿Cómo se calcula?

    ### Para Funciones:
    - **Total Parameters**: len(function.parameters)
    - **Required Parameters**: parámetros sin valor por defecto
    - **Optional Parameters**: parámetros con valor por defecto
    - **Varargs Count**: conteo de *args y **kwargs
    - **Typed Parameters**: parámetros con anotaciones de tipo

    ### Para Clases:
    - **Agregación** de conteos de todos los métodos
    - **Constructor Parameters**: parámetros de __init__ específicamente
    - **Method Parameter Statistics**: promedio, máximo, distribución

    ### Para Módulos:
    - **Function Parameter Statistics**: agregación de funciones del módulo
    - **Class Method Parameter Statistics**: agregación de métodos de clases
    - **Public Interface Complexity**: parámetros de funciones/métodos públicos

    ### Algoritmo paso a paso:
    1. **Obtener lista de parámetros** de la función
    2. **Clasificar parámetros** por tipo (regular, default, varargs, typed)
    3. **Contar cada categoría** independientemente
    4. **Calcular métricas derivadas** (ratios, complejidad)
    5. **Agregar estadísticas** para entidades compuestas

    ## Interpretación de valores:

    ### Para Funciones (Parámetros Totales):
    - **0-3**: Interfaz simple, fácil de usar y testear
    - **4-6**: Interfaz moderada, aceptable pero revisar
    - **7-10**: Interfaz compleja, considerar refactoring
    - **10+**: Interfaz muy compleja, refactoring urgente

    ### Para Funciones (Parámetros Requeridos):
    - **0-2**: Muy fácil de usar
    - **3-4**: Moderado, requiere más atención
    - **5+**: Difícil de usar, probable error de diseño

    ### Patrones Específicos:
    - **Constructor (__init__)**: Hasta 5-7 parámetros aceptables
    - **Métodos de configuración**: Muchos parámetros opcionales OK
    - **Funciones de utilidad**: Preferible 1-3 parámetros
    - **APIs públicas**: Minimize parámetros requeridos

    ### Ratios Importantes:
    - **Optional Ratio**: parámetros opcionales / total parámetros
      - > 0.5: Buena flexibilidad
      - < 0.2: Interfaz rígida

    - **Typed Ratio**: parámetros tipados / total parámetros
      - > 0.8: Excelente documentación de tipos
      - < 0.3: Documentación de tipos insuficiente

    ## ¿Cuándo se aplica?

    **✅ FUNCIONES**: Aplicación principal y más valiosa
    - Identificar funciones con interfaces demasiado complejas
    - Evaluar facilidad de uso y testing
    - Detectar violaciones del principio de responsabilidad única
    - Útil para decisiones de refactoring de interfaces

    **✅ CLASES**: Aplicación muy útil
    - Evaluar complejidad de constructores
    - Identificar clases con métodos muy parametrizados
    - Detectar clases con interfaces inconsistentes
    - Útil para decisiones de diseño de APIs

    **✅ MÓDULOS**: Aplicación agregada valiosa
    - Evaluar complejidad general de interfaces del módulo
    - Identificar módulos con APIs complejas
    - Útil para decisiones de documentación y ejemplos
    - Detectar inconsistencias en estilo de APIs

    **✅ PROYECTOS**: Aplicación para métricas generales
    - Evaluar consistencia de diseño de APIs en el proyecto
    - Identificar áreas que necesitan simplificación
    - Métricas de calidad de interfaces
    - Útil para guías de estilo y estándares

    ## Ejemplo de cálculo:

    ```python
    def ejemplo_simple(x, y):
        # Total: 2, Required: 2, Optional: 0, Typed: 0
        return x + y

    def ejemplo_complejo(
        required_param: str,
        optional_param: int = 0,
        *args,
        keyword_only: bool = True,
        **kwargs
    ) -> str:
        # Total: 5 parámetros
        # Required: 1 (required_param)
        # Optional: 2 (optional_param, keyword_only)
        # Varargs: 2 (*args, **kwargs)
        # Typed: 4 de 5 (80% typed ratio)
        return f"Result: {required_param}"

    class ExampleClass:
        def __init__(self, a: int, b: str = "default"):
            # Constructor: 2 parámetros (sin contar self)
            pass

        def method(self, x, y, z=None):
            # Método: 3 parámetros (sin contar self)
            pass

    # Métricas de clase:
    # - Constructor parameters: 2
    # - Average method parameters: 2.5
    # - Max method parameters: 3
    ```

    ## Relación con Principios de Diseño:

    ### Single Responsibility Principle (SRP):
    - **Muchos parámetros** pueden indicar múltiples responsabilidades
    - **Funciones enfocadas** típicamente requieren pocos parámetros

    ### Interface Segregation Principle (ISP):
    - **Interfaces grandes** (muchos parámetros) violan ISP
    - **Preferir interfaces específicas** con pocos parámetros

    ### Dependency Inversion Principle (DIP):
    - **Inyección de dependencias** puede incrementar parámetros
    - **Balance entre flexibilidad y simplicidad**

    ## Técnicas de Refactoring:

    ### Parameter Object Pattern:
    - **Agrupar parámetros relacionados** en objetos/dataclasses
    - **Reducir conteo aparente** manteniendo información

    ### Builder Pattern:
    - **Para constructores complejos** con muchos parámetros opcionales
    - **Interfaz fluida** vs. muchos parámetros

    ### Configuration Objects:
    - **Parámetros de configuración** en objetos separados
    - **Separar datos de comportamiento**

    ## Beneficios de usar esta métrica:
    - **Simplicidad de cálculo**: Métrica muy directa y objetiva
    - **Correlación con usabilidad**: Directamente relacionada con facilidad de uso
    - **Detección temprana**: Identifica problemas de diseño rápidamente
    - **Guía de refactoring**: Indica dónde simplificar interfaces
    - **Útil para code review**: Fácil de evaluar durante revisiones

    ## Referencias:
    - Martin, R. C. (2008). "Clean Code: A Handbook of Agile Software Craftsmanship"
    - Fowler, M. (1999). "Refactoring: Improving the Design of Existing Code"
    - McConnell, S. (2004). "Code Complete: A Practical Handbook"
    - IEEE Standard 982.1-2005 for Software Engineering
    """

    def __init__(self):
        """Inicializa el calculador de métricas de conteo de parámetros."""
        super().__init__(
            name="parameter_count",
            description="Mide la complejidad de interfaces contando parámetros de funciones y métodos.",
        )

    def get_default_thresholds(self) -> Dict[str, float]:
        """Obtiene los umbrales por defecto para parameter_count.
        
        Basado en principios de Clean Code de Robert Martin.
        
        Returns:
            Dict[str, float]: Umbrales por defecto {low, medium, high}.
        """
        return {
            "low": 3.0,
            "medium": 5.0,
            "high": 7.0,
        }


    def _analyze_parameters(self, parameters: list) -> Dict[str, int]:
        """Analiza una lista de parámetros y devuelve estadísticas detalladas.

        Args:
            parameters: Lista de objetos Parameter a analizar.

        Returns:
            Dict[str, int]: Diccionario con estadísticas de parámetros.
        """
        stats = {
            "total": len(parameters),
            "required": 0,
            "optional": 0,
            "varargs_positional": 0,
            "varargs_keyword": 0,
            "positional_only": 0,
            "keyword_only": 0,
            "typed": 0,
        }

        for param in parameters:
            # Contar parámetros requeridos vs opcionales
            if (
                param.default_value is None
                and not param.is_variadic_positional
                and not param.is_variadic_keyword
            ):
                stats["required"] += 1
            else:
                stats["optional"] += 1

            # Contar tipos especiales de parámetros
            if param.is_variadic_positional:
                stats["varargs_positional"] += 1
            if param.is_variadic_keyword:
                stats["varargs_keyword"] += 1
            if param.is_positional_only:
                stats["positional_only"] += 1
            if param.is_keyword_only:
                stats["keyword_only"] += 1

            # Contar parámetros con anotaciones de tipo
            if param.annotation:
                stats["typed"] += 1

        return stats

    def calculate_function(self, function: Function) -> float:
        """Calcula el conteo de parámetros para una función.

        Esta es la aplicación principal de la métrica de conteo de parámetros.
        Retorna el número total de parámetros como valor primario.

        Args:
            function: Función a analizar.

        Returns:
            float: Número total de parámetros de la función.
        """
        logger.debug(
            f"Calculando conteo de parámetros para función: {function.name}"
        )
        return float(len(function.parameters))

    def calculate_class(self, cls: Class) -> Dict[str, float]:
        """Calcula estadísticas de conteo de parámetros para una clase.

        Analiza los parámetros de todos los métodos de la clase, con especial
        atención al constructor. Proporciona estadísticas útiles pero no suma total.

        Args:
            cls: Clase a analizar.

        Returns:
            Dict[str, float]: Diccionario con estadísticas de parámetros de la clase.
        """
        logger.debug(f"Calculando conteo de parámetros para clase: {cls.name}")

        if not cls.methods:
            return {
                "avg_parameters": 0.0,
                "max_parameters": 0.0,
                "min_parameters": 0.0,
                "constructor_parameters": 0.0,
                "method_count": 0.0,
                "methods_with_many_params": 0.0,
            }

        method_param_counts = []
        constructor_params = 0

        for method in cls.methods:
            # Analizar parámetros del método (excluyendo 'self')
            method_params = [p for p in method.parameters if p.name != "self"]
            method_param_count = len(method_params)
            method_param_counts.append(method_param_count)

            # Identificar constructor
            if method.name == "__init__":
                constructor_params = method_param_count

        # Solo estadísticas útiles, NO suma total
        result = {
            "avg_parameters": sum(method_param_counts)
            / len(method_param_counts),
            "max_parameters": max(method_param_counts),
            "min_parameters": min(method_param_counts),
            "constructor_parameters": float(constructor_params),
            "method_count": float(len(cls.methods)),
            "methods_with_many_params": len(
                [c for c in method_param_counts if c > 5]
            ),
        }

        return result

    def calculate_module(self, module: Module) -> None:
        """El conteo de parámetros no se calcula a nivel de módulo.

        El conteo de parámetros es una métrica específica para evaluar
        la complejidad de interfaces de funciones individuales. No tiene
        sentido agregar esta métrica a nivel de módulo, ya que:

        - Los umbrales están definidos para funciones individuales
        - La suma total no es representativa de la calidad del módulo
        - No hay forma meaningful de interpretar la agregación

        Para análisis a nivel de módulo, use métricas específicas como:
        - Líneas de código
        - Métricas de acoplamiento
        - Análisis de dependencias

        Args:
            module: Módulo a analizar.

        Returns:
            None: Siempre None porque no aplica a módulos.
        """
        logger.debug(
            f"Conteo de parámetros no aplica a módulo: {module.name} - devolviendo None"
        )
        return None

    def calculate_project(self, project: Project) -> None:
        """El conteo de parámetros no se calcula a nivel de proyecto.

        Similar a módulos, el conteo de parámetros es una métrica específica
        para funciones individuales y no debe agregarse a nivel de proyecto.

        Args:
            project: Proyecto a analizar.

        Returns:
            None: Siempre None porque no aplica a proyectos.
        """
        logger.debug(
            f"Conteo de parámetros no aplica a proyecto: {project.name} - devolviendo None"
        )
        return None

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
            return class_result.get("avg_parameters", 0.0)
        elif isinstance(entity, Module):
            module_result = self.calculate_module(entity)
            # module_result is None for non-aggregatable metrics
            return (
                0.0
                if module_result is None
                else module_result.get("avg_parameters", 0.0)
            )
        elif isinstance(entity, Project):
            project_result = self.calculate_project(entity)
            # project_result is None for non-aggregatable metrics
            return (
                0.0
                if project_result is None
                else project_result.get("avg_parameters", 0.0)
            )
        else:
            logger.warning(f"Tipo de entidad no soportado: {type(entity)}")
            return 0.0

    def get_aggregated_value(self, entity: CodeEntity) -> float:
        """Obtiene un valor agregado para usar con umbrales.

        Args:
            entity: Entidad de código a analizar.

        Returns:
            float: Valor agregado de conteo de parámetros.
        """
        result = self.calculate(entity)
        return float(result) if isinstance(result, (int, float)) else 0.0
