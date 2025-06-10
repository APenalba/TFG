"""Módulo para calcular la métrica de complejidad de diseño."""

from typing import Dict

from pypex.metrics.base import BaseMetric
from pypex.parser.code_entities import Class, Function, Module, Project
from pypex.services.logging_service import get_logger

logger = get_logger(__name__)


class DesignComplexityMetric(BaseMetric):
    """Calcula la complejidad de diseño basada en llamadas inter-módulos.

    ## ¿Qué es la Complejidad de Diseño?

    La complejidad de diseño mide la complejidad arquitectónica del software
    evaluando las interacciones entre diferentes módulos y componentes.
    Esta métrica se enfoca en el acoplamiento y las dependencias que
    trascienden las fronteras de los módulos individuales.

    ### Fundamentos Teóricos:

    **Principios de Diseño**:
    - **Bajo acoplamiento**: Los módulos deben tener pocas dependencias
    - **Alta cohesión**: Los elementos relacionados deben estar juntos
    - **Separación de responsabilidades**: Cada módulo debe tener un propósito claro
    - **Principio DRY**: Don't Repeat Yourself

    **Tipos de Acoplamiento**:
    - **Acoplamiento de datos**: Pasar datos simples entre módulos
    - **Acoplamiento de control**: Un módulo controla el flujo de otro
    - **Acoplamiento común**: Módulos comparten datos globales
    - **Acoplamiento de contenido**: Un módulo modifica datos internos de otro

    ### Elementos que Contribuyen:
    - **Llamadas a funciones/métodos**: function.calls
    - **Dependencias externas**: Calls a funciones de otros módulos
    - **Invocaciones de métodos**: Calls a métodos de otras clases
    - **Uso de APIs**: Calls a interfaces externas

    ## ¿Cómo se calcula?

    ### Fórmula:
    Design Complexity = len(function.calls)

    ### Algoritmo:
    1. **Contar llamadas directas** en function.calls
    2. **Para implementación completa** filtrar llamadas externas vs internas
    3. **En esta implementación simplificada** contar todas las llamadas
    4. **Futuras mejoras** pueden distinguir tipos de llamadas

    ## Interpretación de valores:

    - **0-2**: Bajo acoplamiento, diseño bien modularizado ✅
    - **3-5**: Acoplamiento moderado, aceptable 🟨
    - **6-10**: Acoplamiento alto, revisar diseño 🟧
    - **10+**: Acoplamiento muy alto, refactoring urgente ❌

    ## ¿Cuándo se aplica?

    **✅ FUNCIONES**: Aplicación directa útil
    - Medir dependencias de funciones individuales
    - Identificar funciones que hacen demasiadas llamadas
    - Evaluar responsabilidades de funciones
    - Detectar violaciones del principio de responsabilidad única

    **✅ CLASES**: Aplicación valiosa
    - Evaluar acoplamiento a nivel de clase
    - Identificar clases que dependen de muchas otras
    - Detectar patrones de diseño problemáticos
    - Guiar decisiones de refactoring de clases

    **✅ MÓDULOS**: Aplicación arquitectónica importante
    - Analizar dependencias entre módulos
    - Evaluar arquitectura de software
    - Identificar módulos centrales vs periféricos
    - Planificar modularización y estructura de paquetes

    ## Ejemplo de cálculo:

    ```python
    def funcion_simple():  # Design = 0
        return "hello world"
    # Sin llamadas externas

    def funcion_moderada():  # Design = 3
        result1 = helper_function()     # +1
        result2 = another_function()    # +1
        return process_results(result1, result2)  # +1
    # 3 llamadas a otras funciones

    def funcion_acoplada():  # Design = 8
        db.connect()           # +1
        user = User.find(id)   # +1
        user.validate()        # +1
        logger.info("msg")     # +1
        cache.set(key, val)    # +1
        email.send(user)       # +1
        metrics.track("event") # +1
        db.close()             # +1
    # 8 llamadas a diferentes módulos/servicios
    ```

    ## Patrones Problemáticos:
    - **God functions**: Funciones que llaman a muchos servicios
    - **Tight coupling**: Dependencias circulares entre módulos
    - **Shotgun surgery**: Cambios requieren modificar muchos lugares
    - **Feature envy**: Funciones que usan más de otras clases que de la propia

    ## Beneficios de la Métrica:
    - **Evalúa arquitectura**: Mide calidad del diseño
    - **Identifica puntos calientes**: Encuentra componentes muy acoplados
    - **Guía refactoring**: Prioriza qué refactorizar primero
    - **Facilita testing**: Bajo acoplamiento = más fácil de testear
    - **Mejora mantenibilidad**: Diseño limpio es más mantenible

    ## Estrategias de Mejora:
    - **Dependency Injection**: Inyectar dependencias en lugar de crearlas
    - **Facade Pattern**: Simplificar interfaces complejas
    - **Observer Pattern**: Reducir acoplamiento directo
    - **Service Layer**: Concentrar lógica de negocio
    - **Extract Method**: Dividir funciones grandes en más pequeñas

    ## Referencias:
    - Martin, R. C. (2003). "Agile Software Development: Principles, Patterns, and Practices"
    - Fowler, M. (2018). "Refactoring: Improving the Design of Existing Code"
    - IEEE Standard 982.1-2005 for Software Engineering
    - ISO/IEC 25023:2016 Systems and software engineering
    - "Clean Architecture" by Robert Martin - Dependency Rules
    """

    def __init__(self):
        """Inicializa el calculador de complejidad de diseño."""
        super().__init__(
            name="design_complexity",
            description="Mide la complejidad de diseño basada en llamadas inter-módulos.",
        )

    def get_default_thresholds(self) -> Dict[str, float]:
        """Obtiene los umbrales por defecto para design_complexity.
        
        Basado en patrones de diseño y estructura.
        
        Returns:
            Dict[str, float]: Umbrales por defecto {low, medium, high}.
        """
        return {
            "low": 2.0,
            "medium": 5.0,
            "high": 10.0,
        }


    def calculate_function(self, function: Function) -> float:
        """Calcula la complejidad de diseño de una función.

        Args:
            function: Función a analizar.

        Returns:
            float: Complejidad de diseño de la función.
        """
        logger.debug(
            f"Calculando complejidad de diseño para función: {function.name}"
        )

        # Para esta implementación simplificada, usamos el número de llamadas
        # En una implementación más sofisticada, filtrarías por llamadas externas
        design_complexity = len(function.calls)

        return float(design_complexity)

    def calculate_class(self, cls: Class) -> Dict[str, float]:
        """Calcula estadísticas de complejidad de diseño para una clase."""
        logger.debug(
            f"Calculando complejidad de diseño para clase: {cls.name}"
        )

        if not cls.methods:
            return {
                "average": 0.0,
                "max": 0.0,
                "method_count": 0.0,
                "methods_with_calls": 0.0,
            }

        method_designs = []

        for method in cls.methods:
            method_design = self.calculate_function(method)
            method_designs.append(method_design)

        result = {
            "average": sum(method_designs) / len(method_designs),
            "max": max(method_designs),
            "method_count": float(len(cls.methods)),
            "methods_with_calls": len([d for d in method_designs if d > 0]),
        }

        return result

    def calculate_module(self, module: Module) -> None:
        """La complejidad de diseño no se calcula a nivel de módulo.

        Aunque el diseño puede ser relevante a nivel de módulo,
        la suma de llamadas individuales no es representativa
        de la calidad arquitectónica del módulo.

        Args:
            module: Módulo a analizar.

        Returns:
            None: Siempre None porque no aplica a módulos.
        """
        logger.debug(
            f"Complejidad de diseño no aplica a módulo: {module.name} - devolviendo None"
        )
        return None

    def calculate_project(self, project: Project) -> None:
        """La complejidad de diseño no se calcula a nivel de proyecto.

        Args:
            project: Proyecto a analizar.

        Returns:
            None: Siempre None porque no aplica a proyectos.
        """
        logger.debug(
            f"Complejidad de diseño no aplica a proyecto: {project.name} - devolviendo None"
        )
        return None
