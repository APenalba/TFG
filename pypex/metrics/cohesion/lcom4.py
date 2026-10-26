"""Módulo para calcular la métrica LCOM4 (Lack of Cohesion of Methods 4)."""

from collections import defaultdict

from pypex.metrics.base import BaseMetric
from pypex.parser.code_entities import Class, Function, Module, Project
from pypex.services.logging_service import get_logger

logger = get_logger(__name__)


class LCOM4(BaseMetric):
    """Calcula la métrica LCOM4 (Lack of Cohesion of Methods 4).

    ## ¿Qué es LCOM4?

    LCOM4 (Lack of Cohesion of Methods 4) es una métrica de cohesión que mide qué tan bien
    están relacionados los métodos de una clase. Fue desarrollada por Martin Hitz y Behzad Montazeri
    como una versión mejorada de las métricas LCOM anteriores.

    ## ¿Cómo se calcula?

    LCOM4 construye un grafo no dirigido donde:
    - **Nodos**: Cada método de la clase
    - **Aristas**: Conectan métodos que están relacionados por:
      * **Compartir atributos de instancia**: Dos métodos que acceden al mismo atributo de instancia
      * **Llamadas directas**: Un método llama directamente a otro método de la misma clase

    Una vez construido el grafo, LCOM4 cuenta el número de **componentes conectados**.

    ### Algoritmo paso a paso:
    1. Crear un nodo para cada método de la clase
    2. Para cada par de métodos (m1, m2):
       - Si ambos acceden al mismo atributo de instancia → crear arista
       - Si m1 llama a m2 o viceversa → crear arista
    3. Aplicar algoritmo de búsqueda (DFS/BFS) para contar componentes conectados
    4. LCOM4 = número de componentes conectados

    ## Interpretación de valores:

    - **LCOM4 = 1**: **Excelente cohesión** - Todos los métodos están interconectados
    - **LCOM4 = 2**: **Buena cohesión** - La clase tiene dos grupos de métodos relacionados
    - **LCOM4 = 3**: **Cohesión moderada** - Tres grupos separados, considerar refactoring
    - **LCOM4 > 3**: **Pobre cohesión** - Muchos grupos no relacionados, refactoring necesario

    ## ¿Cuándo se aplica?

    **✅ CLASES**: Es la aplicación principal y única correcta de LCOM4
    - Analiza las relaciones entre métodos de una clase
    - Ayuda a identificar clases con múltiples responsabilidades
    - Útil para detectar violaciones del principio de responsabilidad única

    **❌ FUNCIONES**: No aplica - devuelve None
    - Las funciones no tienen métodos internos para analizar
    - El concepto de cohesión entre métodos no existe en funciones

    **❌ MÓDULOS**: No aplica - devuelve None
    - LCOM4 es específica para la cohesión interna de clases
    - Los módulos pueden contener múltiples clases independientemente
    - La cohesión a nivel de módulo se mide con otras métricas

    **❌ PROYECTOS**: No aplica - devuelve None
    - LCOM4 es una métrica a nivel de clase únicamente
    - Los proyectos requieren métricas de nivel arquitectónico

    ## Ejemplo de cálculo:

    ```python
    class EjemploClase:
        def __init__(self):
            self.attr1 = 0
            self.attr2 = 0

        def metodo_a(self):  # Accede a attr1
            return self.attr1 * 2

        def metodo_b(self):  # Accede a attr1, llama a metodo_a
            result = self.metodo_a()
            return self.attr1 + result

        def metodo_c(self):  # Accede a attr2
            return self.attr2 + 1
    ```

    **Análisis**:
    - metodo_a y metodo_b están conectados (ambos usan attr1 + llamada directa)
    - metodo_c está aislado (solo usa attr2)
    - **Resultado**: LCOM4 = 2 (dos componentes conectados)

    ## Referencias:
    - Hitz, M., & Montazeri, B. (1995). "Measuring coupling and cohesion in object-oriented systems"
    - ISO/IEC 25023:2016 Systems and software engineering
    """

    def __init__(self):
        """Inicializa el calculador LCOM4."""
        super().__init__(
            name="lcom4",
            description="Mide la cohesión de clases contando componentes conectados entre métodos.",
        )

    def get_default_thresholds(self) -> dict[str, float]:
        """Obtiene los umbrales por defecto para LCOM4.

        Basado en investigación de Hitz & Montazeri y mejores prácticas:
        - LCOM4 = 1: Excelente cohesión (todos los métodos están interconectados)
        - LCOM4 = 2: Buena cohesión (dos grupos de métodos relacionados)
        - LCOM4 = 3: Cohesión moderada (considerar refactoring)
        - LCOM4 > 3: Pobre cohesión (refactoring necesario)

        Returns:
            Dict[str, float]: Umbrales por defecto {low, medium, high}.
        """
        return {
            "low": 1.0,  # LCOM4 = 1: excelente cohesión
            "medium": 2.0,  # LCOM4 = 2: buena cohesión
            "high": 4.0,  # LCOM4 = 3-4: cohesión moderada/pobre
        }

    def calculate_function(self, function: Function) -> float | None:
        """LCOM4 no aplica a funciones individuales.

        LCOM4 está diseñada específicamente para medir la cohesión entre métodos
        de una clase. Las funciones no tienen métodos internos, por lo que el
        concepto de cohesión entre métodos no aplica.

        Args:
            function: Función a analizar.

        Returns:
            None: Siempre None porque LCOM4 no aplica a funciones.
        """
        logger.debug(f"LCOM4 no aplica a función: {function.name} - devolviendo None")
        return None

    def calculate_class(self, cls: Class) -> dict[str, float]:
        """Calcula LCOM4 para una clase.

        Esta es la aplicación principal de LCOM4. Analiza las relaciones entre
        métodos de la clase basándose en atributos compartidos y llamadas directas.

        Args:
            cls: Clase a analizar.

        Returns:
            Dict[str, float]: Diccionario con LCOM4 y métricas relacionadas.
        """
        logger.debug(f"Calculando LCOM4 para clase: {cls.name}")

        # Si no hay métodos, LCOM4 = 0 (sin cohesión porque no hay métodos)
        if len(cls.methods) == 0:
            return {
                "lcom4": 0.0,
                "total_methods": 0,
                "connected_components": 0,
                "method_connections": 0.0,
                "attribute_connections": 0.0,
                "total": 0.0,  # Para compatibilidad con umbrales
            }

        # Si hay un solo método, la cohesión es perfecta
        if len(cls.methods) == 1:
            return {
                "lcom4": 1.0,
                "total_methods": 1,
                "connected_components": 1,
                "method_connections": 0.0,
                "attribute_connections": 0.0,
                "total": 1.0,  # Para compatibilidad con umbrales
            }

        # Construir grafo de conexiones entre métodos
        method_graph = self._build_method_connection_graph(cls)

        # Contar componentes conectados
        components_count = self._count_connected_components(method_graph)

        # Calcular estadísticas adicionales
        total_methods = len(cls.methods)
        method_connections = self._count_method_call_connections(cls)
        attribute_connections = self._count_attribute_connections(cls)

        lcom4_value = float(components_count)

        return {
            "lcom4": lcom4_value,
            "total_methods": total_methods,
            "connected_components": components_count,
            "method_connections": method_connections,
            "attribute_connections": attribute_connections,
            "total": lcom4_value,  # Para compatibilidad con umbrales
        }

    def calculate_module(self, module: Module) -> dict[str, float] | None:
        """LCOM4 no aplica a módulos.

        LCOM4 es una métrica específica para la cohesión interna de clases,
        midiendo las relaciones entre métodos de una misma clase. Los módulos
        pueden contener múltiples clases independientes, por lo que aplicar
        LCOM4 a nivel de módulo no tiene sentido conceptual.

        Para analizar cohesión a nivel de módulo, considere otras métricas como:
        - Análisis de dependencias entre clases
        - Métricas de acoplamiento entre componentes
        - Análisis de responsabilidades funcionales

        Args:
            module: Módulo a analizar.

        Returns:
            None: Siempre None porque LCOM4 no aplica a módulos.
        """
        logger.debug(f"LCOM4 no aplica a módulo: {module.name} - devolviendo None")
        return None

    def calculate_project(self, project: Project) -> dict[str, float] | None:
        """LCOM4 no aplica a proyectos.

        LCOM4 es una métrica a nivel de clase que mide la cohesión entre métodos.
        Los proyectos requieren métricas de nivel arquitectónico que analicen
        la estructura general del sistema, no la cohesión interna de clases.

        Para analizar proyectos, considere métricas como:
        - Métricas de acoplamiento entre módulos
        - Análisis de dependencias del proyecto
        - Métricas de complejidad arquitectónica
        - Análisis de patrones de diseño

        Args:
            project: Proyecto a analizar.

        Returns:
            None: Siempre None porque LCOM4 no aplica a proyectos.
        """
        logger.debug(f"LCOM4 no aplica a proyecto: {project.name} - devolviendo None")
        return None

    def _build_method_connection_graph(self, cls: Class) -> dict[str, set[str]]:
        """Construye un grafo de conexiones entre métodos de una clase.

        Args:
            cls: Clase a analizar.

        Returns:
            Dict[str, Set[str]]: Grafo donde cada método apunta a sus conectados.
        """
        graph: defaultdict[str, set[str]] = defaultdict(set)
        method_names = {method.name for method in cls.methods}

        # Inicializar nodos del grafo
        for method in cls.methods:
            graph[method.name] = set()

        # Crear conexiones basadas en atributos compartidos
        self._add_attribute_connections(cls, graph)

        # Crear conexiones basadas en llamadas entre métodos
        self._add_method_call_connections(cls, graph, method_names)

        return dict(graph)

    def _add_attribute_connections(self, cls: Class, graph: dict[str, set[str]]):
        """Añade conexiones basadas en atributos de instancia compartidos.

        Args:
            cls: Clase a analizar.
            graph: Grafo a modificar.
        """
        # Crear mapa de atributo -> métodos que lo acceden
        attribute_to_methods = defaultdict(set)

        for method in cls.methods:
            accessed_attrs = self._extract_accessed_attributes_from_ast(method)
            for attr in accessed_attrs:
                attribute_to_methods[attr].add(method.name)

        # Conectar métodos que acceden al mismo atributo
        for methods in attribute_to_methods.values():
            if len(methods) > 1:
                method_list = list(methods)
                for i, method1 in enumerate(method_list):
                    for j, method2 in enumerate(method_list):
                        if i != j:
                            graph[method1].add(method2)
                            graph[method2].add(method1)

    def _extract_accessed_attributes_from_ast(self, method: Function) -> set[str]:
        """Extrae atributos de instancia accedidos desde el método.

        Primero intenta usar el atributo accessed_instance_attributes si está disponible
        (útil para testing), y luego recurre al análisis AST.

        Args:
            method: Método a analizar.

        Returns:
            Set[str]: Conjunto de atributos de instancia accedidos.
        """
        # Primero verificar si ya tenemos los atributos accedidos
        # (usado para testing y cuando ya se han calculado)
        if (
            hasattr(method, "accessed_instance_attributes")
            and method.accessed_instance_attributes is not None
        ):
            return set(method.accessed_instance_attributes)

        # Si no hay nodo AST, no podemos extraer atributos
        if method.astroid_node is None:
            return set()

        try:
            from astroid import nodes as astroid_nodes
        except ImportError:
            logger.warning("Astroid no disponible para análisis de atributos")
            return set()

        accessed_attrs = set()

        # Obtener el nombre del primer parámetro (usualmente 'self')
        first_param_name = None
        if (
            hasattr(method.astroid_node, "args")
            and method.astroid_node.args is not None
            and method.astroid_node.args.args
        ):
            first_param_name = method.astroid_node.args.args[0].name

        if first_param_name is None:
            return set()

        def find_attribute_accesses(node):
            nonlocal accessed_attrs

            if isinstance(node, astroid_nodes.Attribute):
                # Verificar si es acceso a self.atributo
                if isinstance(node.expr, astroid_nodes.Name) and node.expr.name == first_param_name:
                    accessed_attrs.add(node.attrname)

            # Recursión sobre hijos
            for child in node.get_children():
                find_attribute_accesses(child)

        # Analizar el cuerpo del método
        if hasattr(method.astroid_node, "body"):
            for stmt in method.astroid_node.body:
                find_attribute_accesses(stmt)

        return accessed_attrs

    def _add_method_call_connections(
        self, cls: Class, graph: dict[str, set[str]], method_names: set[str]
    ):
        """Añade conexiones basadas en llamadas entre métodos.

        Args:
            cls: Clase a analizar.
            graph: Grafo a modificar.
            method_names: Conjunto de nombres de métodos de la clase.
        """
        for method in cls.methods:
            for called in method.calls:
                # Extraer nombre del método de la llamada completa
                called_method = self._extract_method_name(called)

                # Solo conectar si es un método de la misma clase
                if called_method in method_names and called_method != method.name:
                    graph[method.name].add(called_method)
                    graph[called_method].add(method.name)

    def _extract_method_name(self, call: str) -> str:
        """Extrae el nombre del método de una llamada completa.

        Args:
            call: Cadena de llamada (ej: "self.method_name", "method_name").

        Returns:
            str: Nombre del método extraído.
        """
        # Remover prefijos comunes como "self."
        if call.startswith("self."):
            return call[5:]

        # Si contiene punto, tomar la última parte
        if "." in call:
            return call.split(".")[-1]

        return call

    def _count_connected_components(self, graph: dict[str, set[str]]) -> int:
        """Cuenta el número de componentes conectados en el grafo.

        Args:
            graph: Grafo de conexiones entre métodos.

        Returns:
            int: Número de componentes conectados.
        """
        visited: set[str] = set()
        components = 0

        for node in graph:
            if node not in visited:
                self._dfs(graph, node, visited)
                components += 1

        return components

    def _dfs(self, graph: dict[str, set[str]], node: str, visited: set[str]):
        """Búsqueda en profundidad para encontrar componentes conectados.

        Args:
            graph: Grafo de conexiones.
            node: Nodo actual.
            visited: Conjunto de nodos visitados.
        """
        visited.add(node)
        for neighbor in graph[node]:
            if neighbor not in visited:
                self._dfs(graph, neighbor, visited)

    def _count_method_call_connections(self, cls: Class) -> float:
        """Cuenta conexiones por llamadas entre métodos.

        Args:
            cls: Clase a analizar.

        Returns:
            float: Número de conexiones por llamadas de método.
        """
        method_names = {method.name for method in cls.methods}
        connections = 0

        for method in cls.methods:
            for called in method.calls:
                called_method = self._extract_method_name(called)
                if called_method in method_names and called_method != method.name:
                    connections += 1

        return float(connections)

    def _count_attribute_connections(self, cls: Class) -> float:
        """Cuenta conexiones por atributos compartidos.

        Args:
            cls: Clase a analizar.

        Returns:
            float: Número de conexiones por atributos compartidos.
        """
        attribute_to_methods = defaultdict(set)

        for method in cls.methods:
            accessed_attrs = self._extract_accessed_attributes_from_ast(method)
            for attr in accessed_attrs:
                attribute_to_methods[attr].add(method.name)

        connections = 0
        for methods in attribute_to_methods.values():
            if len(methods) > 1:
                # n métodos que comparten un atributo crean n*(n-1)/2 conexiones
                n = len(methods)
                connections += n * (n - 1) // 2

        return float(connections)

    def get_aggregated_value(self, entity) -> float:
        """Obtiene un valor agregado para usar con umbrales.

        Args:
            entity: Entidad de código a analizar.

        Returns:
            float: Valor LCOM4 agregado.
        """
        result = self.calculate(entity)

        if isinstance(result, (int, float)):
            return float(result)

        if isinstance(result, dict):
            # Buscar el valor LCOM4 principal
            for key in [
                "lcom4",
                "total",
                "module_max_lcom4",
                "project_max_lcom4",
            ]:
                if key in result:
                    return float(result[key])

        return 0.0

    def interpret_cohesion_level(self, lcom4: float) -> str:
        """Interpreta el nivel de cohesión basado en LCOM4.

        Args:
            lcom4: Valor LCOM4.

        Returns:
            str: Interpretación del nivel de cohesión.
        """
        if lcom4 <= 1:
            return "Excelente"
        elif lcom4 <= 2:
            return "Buena"
        elif lcom4 <= 3:
            return "Moderada"
        else:
            return "Pobre"

    def get_cohesion_analysis(self, cls: Class) -> dict[str, str | int | float]:
        """Obtiene un análisis detallado de cohesión para una clase.

        Args:
            cls: Clase a analizar.

        Returns:
            Dict: Análisis detallado de cohesión.
        """
        metrics = self.calculate_class(cls)
        lcom4_value = metrics["lcom4"]

        return {
            "lcom4_value": lcom4_value,
            "interpretation": self.interpret_cohesion_level(lcom4_value),
            "total_methods": metrics["total_methods"],
            "connected_groups": metrics["connected_components"],
            "method_calls": int(metrics["method_connections"]),
            "shared_attributes": int(metrics["attribute_connections"]),
            "needs_refactoring": lcom4_value > 3,
            "refactoring_priority": (
                "High" if lcom4_value > 3 else "Medium" if lcom4_value > 1 else "Low"
            ),
        }
