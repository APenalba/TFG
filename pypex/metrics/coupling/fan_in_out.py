"""Módulo para calcular métricas de acoplamiento Fan-In y Fan-Out."""

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


class FanInOutMetric(BaseMetric):
    """Calcula las métricas de Fan-In y Fan-Out para evaluar acoplamiento.

    ## ¿Qué son Fan-In y Fan-Out?

    Fan-In y Fan-Out son métricas de acoplamiento que miden las dependencias entre
    componentes de software. Fueron introducidas por Henry y Kafura en 1981 como
    parte de las métricas de complejidad de software.

    ### Fan-In (Acoplamiento Aferente):
    Número de módulos, clases o funciones que **dependen** de esta entidad.
    - **¿Quién me llama?** - Mide la responsabilidad
    - **Alto Fan-In**: Indica que muchas entidades dependen de esta
    - **Ventaja**: Reutilización, componente central importante
    - **Riesgo**: Cambios pueden afectar muchos dependientes

    ### Fan-Out (Acoplamiento Eferente):
    Número de módulos, clases o funciones de las que **depende** esta entidad.
    - **¿A quién llamo?** - Mide las dependencias
    - **Alto Fan-Out**: Indica que esta entidad depende de muchas otras
    - **Riesgo**: Acoplamiento fuerte, difícil de mantener
    - **Problema**: Cambios en dependencias pueden romper esta entidad

    ## ¿Cómo se calcula?

    ### Para Funciones:
    - **Fan-In**: Número de funciones que llaman a esta función
    - **Fan-Out**: Número de funciones que esta función llama

    ### Para Clases:
    - **Fan-In**: Número de clases que usan esta clase (herencia, instanciación, etc.)
    - **Fan-Out**: Número de clases que esta clase usa (herencia, composición, etc.)

    ### Para Módulos:
    - **Fan-In**: Número de módulos que importan este módulo
    - **Fan-Out**: Número de módulos que este módulo importa

    ### Algoritmo paso a paso:
    1. **Construir grafo de dependencias** del proyecto completo
    2. **Para cada entidad**, contar:
       - **Fan-In**: Aristas entrantes (quién depende de mí)
       - **Fan-Out**: Aristas salientes (de quién dependo)
    3. **Calcular métricas derivadas** como estabilidad e inestabilidad

    ## Interpretación de valores:

    ### Fan-In:
    - **0**: No es usado (código muerto o punto de entrada)
    - **1-3**: Uso moderado, buena encapsulación
    - **4-10**: Uso alto, componente importante
    - **10+**: Uso muy alto, posible violación SRP

    ### Fan-Out:
    - **0**: No tiene dependencias (muy raro)
    - **1-5**: Pocas dependencias, bajo acoplamiento
    - **6-15**: Dependencias moderadas
    - **15+**: Alto acoplamiento, considerar refactoring

    ### Métricas Derivadas:
    - **Inestabilidad (I)**: Fan-Out / (Fan-In + Fan-Out)
      - I = 0: Completamente estable (solo Fan-In)
      - I = 1: Completamente inestable (solo Fan-Out)
    - **Abstractness (A)**: Número de abstracciones / Total de entidades
    - **Distancia del Main Sequence**: |A + I - 1|

    ## ¿Cuándo se aplica?

    **✅ FUNCIONES**: Aplicación básica útil
    - Fan-Out fácil de calcular (llamadas directas)
    - Fan-In requiere análisis global del proyecto
    - Útil para identificar funciones muy acopladas
    - Ayuda en decisiones de refactoring

    **✅ CLASES**: Aplicación muy valiosa
    - Mide acoplamiento entre clases
    - Identifica clases con demasiadas dependencias
    - Útil para evaluar arquitectura OOP
    - Ayuda a detectar violaciones de principios SOLID

    **✅ MÓDULOS**: Aplicación principal y más importante
    - Esta es la aplicación más común y útil
    - Analiza dependencias entre módulos/paquetes
    - Crítico para arquitectura de software
    - Útil para decisiones de modularización

    **✅ PROYECTOS**: Aplicación agregada valiosa
    - Estadísticas de acoplamiento general del proyecto
    - Métricas de calidad arquitectónica
    - Útil para comparar proyectos
    - Tracking de métricas a lo largo del tiempo

    ## Ejemplo de cálculo:

    ```python
    # módulo_a.py
    from módulo_b import ClassB  # Fan-Out +1
    from módulo_c import func_c  # Fan-Out +1

    class ClassA:
        def __init__(self):
            self.b = ClassB()    # Fan-Out +1 (composición)

        def method(self):
            func_c()             # Fan-Out +1 (llamada)

    # Para módulo_a:
    # Fan-Out = 2 (importa módulo_b y módulo_c)
    # Fan-In = ? (depende de quién importe módulo_a)
    ```

    ## Principios de Diseño relacionados:

    ### Principios SOLID:
    - **SRP**: Alto Fan-Out puede indicar múltiples responsabilidades
    - **OCP**: Alto Fan-In facilita extensión
    - **LSP**: Fan-In/Out ayuda a evaluar jerarquías
    - **ISP**: Fan-Out alto puede indicar interfaces grandes
    - **DIP**: Fan-Out hacia abstracciones vs. concreciones

    ### Patrones Arquitectónicos:
    - **Layered Architecture**: Fan-Out debe ir hacia capas inferiores
    - **Hexagonal Architecture**: Núcleo debe tener bajo Fan-Out
    - **Microservices**: Minimizar Fan-In/Out entre servicios

    ## Beneficios de usar estas métricas:
    - Identifica componentes críticos (alto Fan-In)
    - Detecta acoplamiento excesivo (alto Fan-Out)
    - Evalúa estabilidad de componentes
    - Ayuda en decisiones de arquitectura
    - Útil para planificación de testing
    - Facilita identificación de puntos de cambio riesgosos

    ## Referencias:
    - Henry, S., & Kafura, D. (1981). "Software Structure Metrics"
    - Martin, R. C. (2003). "Agile Software Development: Principles, Patterns, and Practices"
    - IEEE Standard 982.1-2005 for Software Engineering
    - ISO/IEC 25023:2016 Systems and software engineering
    """

    def __init__(self):
        """Inicializa el calculador de métricas Fan-In/Fan-Out."""
        super().__init__(
            name="fan_in_out",
            description="Mide el acoplamiento aferente (Fan-In) y eferente (Fan-Out) de entidades de código.",
        )

    def get_default_thresholds(self) -> Dict[str, float]:
        """Obtiene los umbrales por defecto para fan_in_out.
        
        Basado en métricas de acoplamiento CK.
        
        Returns:
            Dict[str, float]: Umbrales por defecto {low, medium, high}.
        """
        return {
            "low": 5.0,
            "medium": 10.0,
            "high": 20.0,
        }

        self._call_graph = {}  # Caché de grafo de llamadas

    def _build_call_graph(self, project: Project) -> Dict[str, Set[str]]:
        """Construye un grafo de llamadas para el proyecto completo.

        Args:
            project: Proyecto a analizar.

        Returns:
            Dict[str, Set[str]]: Grafo de llamadas (quién llama a quién).
        """
        # Solo construir el grafo si no está ya en caché
        if not self._call_graph:
            logger.debug("Construyendo grafo de llamadas para el proyecto")
            call_graph = {}

            # Registrar todas las entidades primero
            for module in project.modules:
                module_path = str(module.path) if module.path else module.name

                # Registrar funciones
                for func in module.functions:
                    func_key = f"{module_path}::{func.name}"
                    call_graph[func_key] = set()

                # Registrar métodos
                for cls in module.classes:
                    for method in cls.methods:
                        method_key = f"{module_path}::{cls.name}.{method.name}"
                        call_graph[method_key] = set()

            # Registrar llamadas
            for module in project.modules:
                module_path = str(module.path) if module.path else module.name

                # Registrar llamadas de funciones
                for func in module.functions:
                    func_key = f"{module_path}::{func.name}"
                    for called in func.calls:
                        # Buscar entidad llamada en el grafo
                        for entity_key in call_graph:
                            if entity_key.endswith(
                                f"::{called}"
                            ) or entity_key.endswith(f".{called}"):
                                # Registrar la llamada
                                call_graph[entity_key].add(func_key)

                # Registrar llamadas de métodos
                for cls in module.classes:
                    for method in cls.methods:
                        method_key = f"{module_path}::{cls.name}.{method.name}"
                        for called in method.calls:
                            # Buscar entidad llamada en el grafo
                            for entity_key in call_graph:
                                if entity_key.endswith(
                                    f"::{called}"
                                ) or entity_key.endswith(f".{called}"):
                                    # Registrar la llamada
                                    call_graph[entity_key].add(method_key)

            self._call_graph = call_graph

        return self._call_graph

    def _get_fan_in(
        self, entity_key: str, call_graph: Dict[str, Set[str]]
    ) -> int:
        """Obtiene el Fan-In de una entidad.

        Args:
            entity_key: Clave de la entidad en el grafo.
            call_graph: Grafo de llamadas.

        Returns:
            int: Número de entidades que llaman a esta entidad.
        """
        # Fan-In: cuántas entidades llaman a esta entidad
        if entity_key in call_graph:
            return len(call_graph[entity_key])
        return 0

    def _get_fan_out(
        self,
        entity_key: str,
        entity_calls: Set[str],
        call_graph: Dict[str, Set[str]],
    ) -> int:
        """Obtiene el Fan-Out de una entidad.

        Args:
            entity_key: Clave de la entidad en el grafo.
            entity_calls: Conjunto de llamadas que hace la entidad.
            call_graph: Grafo de llamadas.

        Returns:
            int: Número de entidades a las que llama esta entidad.
        """
        # Fan-Out: cuántas entidades llama esta entidad
        count = 0
        for called in entity_calls:
            for entity in call_graph:
                if entity.endswith(f"::{called}") or entity.endswith(
                    f".{called}"
                ):
                    count += 1
                    break
        return count

    def calculate_function(self, function: Function) -> float:
        """Calcula el acoplamiento Fan-Out para una función.

        Para funciones individuales, el Fan-Out es más fácil de calcular que el Fan-In
        (ya que las llamadas están disponibles directamente). El Fan-In requeriría
        análisis de todo el proyecto.

        Esta implementación simplificada cuenta solo las llamadas directas de la función.

        Args:
            function: Función a analizar.

        Returns:
            float: Fan-Out de la función (número de llamadas que hace).
        """
        logger.debug(f"Calculando Fan-Out para función: {function.name}")
        return len(function.calls)

    def calculate_class(self, cls: Class) -> Dict[str, float]:
        """Calcula estadísticas de acoplamiento Fan-In/Fan-Out para una clase.

        Analiza el acoplamiento de la clase tanto a nivel de métodos como de
        estructura de clase (herencia, composición).

        Args:
            cls: Clase a analizar.

        Returns:
            Dict[str, float]: Estadísticas de acoplamiento de la clase.
        """
        logger.debug(f"Calculando acoplamiento para clase: {cls.name}")

        if not cls.methods:
            return {
                "avg_calls": 0.0,
                "max_calls": 0.0,
                "inheritance_coupling": len(cls.base_classes),
                "method_count": 0.0,
                "highly_coupled_methods": 0.0,
            }

        method_couplings = []

        # Calcular acoplamiento para cada método
        for method in cls.methods:
            method_fan_out = self.calculate_function(method)
            method_couplings.append(method_fan_out)

        # Calcular acoplamiento estructural de la clase
        inheritance_coupling = len(cls.base_classes)

        result = {
            "avg_calls": sum(method_couplings) / len(method_couplings),
            "max_calls": max(method_couplings),
            "inheritance_coupling": inheritance_coupling,
            "method_count": float(len(cls.methods)),
            "highly_coupled_methods": len(
                [c for c in method_couplings if c >= 6]
            ),
        }

        return result

    def calculate_module(self, module: Module) -> Dict[str, float]:
        """Calcula métricas de acoplamiento Fan-In/Fan-Out para un módulo.

        Esta es una aplicación importante de estas métricas.
        Analiza las dependencias entre módulos y la cohesión interna.

        Args:
            module: Módulo a analizar.

        Returns:
            Dict[str, float]: Métricas útiles de acoplamiento del módulo.
        """
        logger.debug(f"Calculando acoplamiento para módulo: {module.name}")

        function_couplings = []
        method_couplings = []
        total_inheritance_coupling = 0

        # Analizar funciones del módulo
        for func in module.functions:
            func_coupling = self.calculate_function(func)
            function_couplings.append(func_coupling)

        # Analizar clases del módulo
        for cls in module.classes:
            # Métodos de la clase
            for method in cls.methods:
                method_coupling = self.calculate_function(method)
                method_couplings.append(method_coupling)

            # Herencia de la clase
            inheritance_coupling = len(cls.base_classes)
            total_inheritance_coupling += inheritance_coupling

        # Acoplamiento por imports
        import_coupling = len(module.imports)

        all_couplings = function_couplings + method_couplings

        result = {
            "avg_coupling": sum(all_couplings) / len(all_couplings)
            if all_couplings
            else 0.0,
            "max_coupling": max(all_couplings) if all_couplings else 0.0,
            "import_coupling": import_coupling,
            "inheritance_coupling": total_inheritance_coupling,
            "entity_count": len(all_couplings),
            "highly_coupled_entities": len(
                [c for c in all_couplings if c >= 6]
            ),
        }

        return result

    def calculate_project(self, project: Project) -> Dict[str, float]:
        """Calcula estadísticas de acoplamiento Fan-In/Fan-Out a nivel de proyecto.

        Proporciona métricas agregadas de acoplamiento para evaluar
        la calidad arquitectónica general del proyecto.

        Args:
            project: Proyecto a analizar.

        Returns:
            Dict[str, float]: Estadísticas útiles de acoplamiento del proyecto.
        """
        logger.debug(f"Calculando acoplamiento para proyecto: {project.name}")

        all_couplings = []
        total_import_coupling = 0
        total_inheritance_coupling = 0
        module_count = len(project.modules)

        # Analizar cada módulo
        for module in project.modules:
            # Funciones del módulo
            for func in module.functions:
                func_coupling = self.calculate_function(func)
                all_couplings.append(func_coupling)

            # Clases del módulo
            for cls in module.classes:
                # Métodos de la clase
                for method in cls.methods:
                    method_coupling = self.calculate_function(method)
                    all_couplings.append(method_coupling)

                # Herencia de la clase
                inheritance_coupling = len(cls.base_classes)
                total_inheritance_coupling += inheritance_coupling

            # Imports del módulo
            import_coupling = len(module.imports)
            total_import_coupling += import_coupling

        result = {
            "avg_coupling": sum(all_couplings) / len(all_couplings)
            if all_couplings
            else 0.0,
            "max_coupling": max(all_couplings) if all_couplings else 0.0,
            "total_import_coupling": total_import_coupling,
            "total_inheritance_coupling": total_inheritance_coupling,
            "module_count": module_count,
            "entity_count": len(all_couplings),
            "highly_coupled_entities": len(
                [c for c in all_couplings if c >= 6]
            ),
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
            return class_result.get("avg_calls", 0.0)
        elif isinstance(entity, Module):
            module_result = self.calculate_module(entity)
            return module_result.get("avg_coupling", 0.0)
        elif isinstance(entity, Project):
            project_result = self.calculate_project(entity)
            return project_result.get("avg_coupling", 0.0)
        else:
            logger.warning(f"Tipo de entidad no soportado: {type(entity)}")
            return 0.0

    def get_aggregated_value(self, entity: CodeEntity) -> float:
        """Obtiene un valor agregado para usar con umbrales.

        Args:
            entity: Entidad de código a analizar.

        Returns:
            float: Valor agregado de acoplamiento.
        """
        result = self.calculate(entity)
        return float(result) if isinstance(result, (int, float)) else 0.0
