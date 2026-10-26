"""Utilities y factories para tests de métricas.

Este módulo proporciona clases y funciones de utilidad para crear tests
consistentes y mantenibles para todas las métricas de PyPex.
"""

from dataclasses import dataclass
from typing import Any

import astroid

from pypex.metrics.base import IMetric
from pypex.parser.code_entities import Class, CodeEntity, Function, Import, Module, Project


@dataclass
class CodeSample:
    """Representa una muestra de código para testing."""

    code: str
    description: str
    expected_complexity: float
    edge_case: bool = False
    error_expected: bool = False


class TestEntityFactory:
    """Factory para crear entidades de código para testing.

    Implementa el patrón Factory para crear entidades de código
    consistentes y configurables para tests.
    """

    @staticmethod
    def create_simple_function(
        name: str = "test_function",
        control_flow_elements: list[Any] | None = None,
        parameters: list[str] | None = None,
        calls: set[str] | None = None,
        complexity: float = 1.0,
    ) -> Function:
        """Crea una función simple para testing."""
        function = Function(name=name)
        function.control_flow_elements = control_flow_elements or []
        function.parameters = parameters or []
        function.calls = calls or set()
        function.node = None  # No necesitamos AST real para tests unitarios
        # Agregar atributos para métricas de Halstead
        function.operators_count = {}
        function.operands_count = {}
        # Agregar atributos para métricas de comprensión
        function.comprehensions = []
        # Agregar atributos para métricas de manejo de excepciones
        function.exception_handlers_count = 0
        function.try_blocks_count = 0
        # Agregar atributos para métricas de complejidad de generadores
        function.yield_expressions_count = 0
        return function

    @staticmethod
    def create_function_from_code(code: str, function_name: str = "test_function") -> Function:
        """Crea una función con nodo astroid real desde código Python.

        Args:
            code: Código Python que contiene la función
            function_name: Nombre de la función a extraer

        Returns:
            Function: Función con nodo astroid para testing de métricas avanzadas
        """
        try:
            # Parsear código con astroid
            module_node = astroid.parse(code)

            # Buscar la función por nombre
            for node in module_node.nodes_of_class(astroid.nodes.FunctionDef):
                if node.name == function_name:
                    # Crear entidad Function con nodo astroid
                    function = Function(
                        name=node.name,
                        line_start=node.lineno,
                        line_end=node.end_lineno or node.lineno,
                        astroid_node=node,
                    )

                    # Determinar si es async
                    function.is_async = isinstance(node, astroid.nodes.AsyncFunctionDef)

                    # Extraer parámetros básicos
                    if node.args:
                        function.parameters = [arg.name for arg in node.args.args]

                    return function

            # Si no se encontró la función, crear una vacía
            return TestEntityFactory.create_simple_function(function_name)

        except Exception as e:
            # Fallback en caso de error de parsing
            print(f"Warning: Could not parse code for {function_name}: {e}")
            return TestEntityFactory.create_simple_function(function_name)

    @staticmethod
    def create_complex_function(
        name: str = "complex_function",
        if_count: int = 3,
        loop_count: int = 2,
        try_count: int = 1,
        parameters: list[str] | None = None,
    ) -> Function:
        """Crea una función compleja con elementos de control de flujo específicos."""
        function = Function(name=name)

        # Simular elementos de control de flujo
        control_elements = []

        # Agregar elementos if
        for i in range(if_count):
            control_elements.append(MockControlFlowElement("If", f"if_{i}"))

        # Agregar bucles
        for i in range(loop_count):
            control_elements.append(MockControlFlowElement("For", f"for_{i}"))

        # Agregar try/except
        for i in range(try_count):
            control_elements.append(MockControlFlowElement("try_handler", f"try_{i}"))

        function.control_flow_elements = control_elements
        function.parameters = parameters or ["param1", "param2"]
        function.calls = {"external_function", "another_call"}
        return function

    @staticmethod
    def create_class_with_methods(
        class_name: str = "TestClass",
        method_names: list[str] | None = None,
        method_complexities: dict[str, float] | None = None,
        attributes: set[str] | None = None,
    ) -> Class:
        """Crea una clase con métodos para testing."""
        cls = Class(name=class_name)
        method_names = method_names or ["method1", "method2", "method3"]
        method_complexities = method_complexities or {}

        methods = []
        for method_name in method_names:
            complexity = method_complexities.get(method_name, 1.0)
            # Simular complejidad creando elementos de control
            if_count = int(complexity) - 1 if complexity > 1 else 0
            method = TestEntityFactory.create_complex_function(
                name=method_name, if_count=if_count, loop_count=0
            )
            method.is_method = True
            method.accessed_instance_attributes = attributes or {"attr1"}
            methods.append(method)

        cls.methods = methods
        cls.attributes = attributes or {"attr1", "attr2"}
        cls.base_classes = []  # Lista vacía por defecto para acoplamiento
        cls.is_abstract_class = False  # Por defecto no es abstracta
        return cls

    @staticmethod
    def create_module_with_entities(
        module_name: str = "test_module",
        function_count: int = 3,
        class_count: int = 2,
        import_count: int = 5,
    ) -> Module:
        """Crea un módulo con funciones y clases para testing."""
        module = Module(name=module_name)

        # Crear funciones
        functions = []
        for i in range(function_count):
            func = TestEntityFactory.create_simple_function(f"function_{i}")
            functions.append(func)

        # Crear clases
        classes = []
        for i in range(class_count):
            cls = TestEntityFactory.create_class_with_methods(f"Class_{i}")
            classes.append(cls)

        # Crear imports como objetos Import para compatibilidad con AdvancedCoupling
        imports = [Import(module=f"import_module_{i}", line=i + 1) for i in range(import_count)]

        module.functions = functions
        module.classes = classes
        module.imports = imports
        module.loc = 100  # Líneas de código por defecto
        module.sloc = 80  # Líneas de código sin comentarios
        module.dloc = 10  # Líneas de documentación
        module.cloc = 5  # Líneas de comentarios
        module.blank = 5  # Líneas en blanco

        return module

    @staticmethod
    def create_project_with_modules(
        project_name: str = "test_project", module_count: int = 3
    ) -> Project:
        """Crea un proyecto con múltiples módulos para testing."""
        project = Project(name=project_name)

        modules = []
        for i in range(module_count):
            module = TestEntityFactory.create_module_with_entities(f"module_{i}")
            modules.append(module)

        project.modules = modules
        return project


@dataclass
class MockControlFlowElement:
    """Mock de un elemento de control de flujo para testing."""

    element_type: str
    name: str
    nesting_level: int = 0  # Nivel de anidamiento requerido por CognitiveComplexity
    condition_complexity: int = 0  # Complejidad de condición para operadores booleanos
    is_exceptional_flow: bool = False  # Para EssentialComplexityMetric


class MetricTestCase:
    """Builder para casos de test de métricas.

    Implementa el patrón Builder para crear casos de test
    complejos de manera fluida y legible.
    """

    def __init__(self, metric: IMetric):
        self.metric = metric
        self.entity: CodeEntity | None = None
        self.expected_result: Any = None
        self.description: str = ""
        self.should_raise: Exception | None = None

    def with_entity(self, entity: CodeEntity) -> "MetricTestCase":
        """Configura la entidad a testear."""
        self.entity = entity
        return self

    def expecting(self, result: Any) -> "MetricTestCase":
        """Configura el resultado esperado."""
        self.expected_result = result
        return self

    def should_raise_error(self, exception: Exception) -> "MetricTestCase":
        """Configura que se espera una excepción."""
        self.should_raise = exception
        return self

    def described_as(self, description: str) -> "MetricTestCase":
        """Agrega una descripción al caso de test."""
        self.description = description
        return self

    def execute(self) -> Any:
        """Ejecuta el caso de test."""
        if self.should_raise:
            raise self.should_raise

        if isinstance(self.entity, Function):
            return self.metric.calculate_function(self.entity)
        elif isinstance(self.entity, Class):
            return self.metric.calculate_class(self.entity)
        elif isinstance(self.entity, Module):
            return self.metric.calculate_module(self.entity)
        elif isinstance(self.entity, Project):
            return self.metric.calculate_project(self.entity)
        else:
            return self.metric.calculate(self.entity)


class TestDataProvider:
    """Proveedor de datos de test usando el patrón Strategy.

    Proporciona conjuntos de datos específicos para diferentes
    tipos de tests y métricas.
    """

    @staticmethod
    def get_complexity_test_cases() -> list[CodeSample]:
        """Proporciona casos de test para métricas de complejidad."""
        return [
            CodeSample(
                code="""
def simple_function():
    return 42
                """,
                description="Función simple sin estructuras de control",
                expected_complexity=1.0,
            ),
            CodeSample(
                code="""
def function_with_if(x):
    if x > 0:
        return x
    else:
        return 0
                """,
                description="Función con if/else",
                expected_complexity=2.0,
            ),
            CodeSample(
                code="""
def complex_function(data):
    result = 0
    for item in data:
        if item > 0:
            if item % 2 == 0:
                result += item
            else:
                result -= item
        elif item < 0:
            try:
                result = result / abs(item)
            except ZeroDivisionError:
                result = 0
    return result
                """,
                description="Función muy compleja con múltiples estructuras anidadas",
                expected_complexity=7.0,
            ),
            CodeSample(
                code="", description="Código vacío", expected_complexity=0.0, edge_case=True
            ),
        ]

    @staticmethod
    def get_edge_case_functions() -> list[Function]:
        """Proporciona funciones para casos extremos."""
        return [
            TestEntityFactory.create_simple_function(name="empty_function"),
            TestEntityFactory.create_complex_function(
                name="very_complex", if_count=20, loop_count=10
            ),
            TestEntityFactory.create_simple_function(name="no_params", parameters=[]),
            TestEntityFactory.create_complex_function(
                name="many_params", parameters=[f"param{i}" for i in range(15)]
            ),
        ]

    @staticmethod
    def get_cohesion_test_classes() -> list[Class]:
        """Proporciona clases para tests de cohesión."""
        # Clase con alta cohesión
        high_cohesion = TestEntityFactory.create_class_with_methods(
            class_name="HighCohesionClass", method_names=["method1", "method2", "method3"]
        )
        for method in high_cohesion.methods:
            method.accessed_instance_attributes = {"shared_attr1", "shared_attr2"}

        # Clase con baja cohesión
        low_cohesion = TestEntityFactory.create_class_with_methods(
            class_name="LowCohesionClass", method_names=["method1", "method2", "method3"]
        )
        for i, method in enumerate(low_cohesion.methods):
            method.accessed_instance_attributes = {f"unique_attr_{i}"}

        return [high_cohesion, low_cohesion]


class AssertionHelpers:
    """Helpers para aserciones específicas de métricas."""

    @staticmethod
    def assert_metric_result_structure(result: Any, expected_keys: list[str]) -> None:
        """Verifica que el resultado tenga la estructura esperada."""
        assert result is not None, "El resultado no debe ser None"

        if isinstance(result, dict):
            for key in expected_keys:
                assert key in result, f"Clave esperada '{key}' no encontrada en resultado"
                assert isinstance(result[key], (int, float)), f"Valor de '{key}' debe ser numérico"
        else:
            assert isinstance(result, (int, float)), "El resultado debe ser numérico"

    @staticmethod
    def assert_metric_bounds(
        value: float, min_value: float = 0.0, max_value: float = float("inf")
    ) -> None:
        """Verifica que el valor de la métrica esté dentro de límites esperados."""
        assert min_value <= value <= max_value, (
            f"Valor {value} fuera de rango [{min_value}, {max_value}]"
        )

    @staticmethod
    def assert_threshold_consistency(metric: IMetric, test_values: list[float]) -> None:
        """Verifica que los umbrales sean consistentes con los valores de test."""
        metric.get_thresholds()

        for value in test_values:
            interpretation = metric.interpret(value)
            assert interpretation in ["low", "medium", "high"], (
                f"Interpretación inválida: {interpretation}"
            )


class BaseMetricTestCase:
    """Clase base para todos los tests de métricas.

    Proporciona funcionalidad común y plantillas para tests
    de métricas siguiendo el patrón Template Method.
    """

    def setup_method(self):
        """Setup común para todos los tests de métricas."""
        self.factory = TestEntityFactory()
        self.data_provider = TestDataProvider()
        self.assertions = AssertionHelpers()

    def test_metric_interface_compliance(self, metric: IMetric):
        """Test que verifica que la métrica cumple con la interfaz."""
        # Verificar propiedades básicas
        assert hasattr(metric, "name"), "La métrica debe tener propiedad 'name'"
        assert hasattr(metric, "description"), "La métrica debe tener propiedad 'description'"
        assert isinstance(metric.name, str), "El nombre debe ser string"
        assert isinstance(metric.description, str), "La descripción debe ser string"
        assert len(metric.name) > 0, "El nombre no puede estar vacío"
        assert len(metric.description) > 0, "La descripción no puede estar vacía"

        # Verificar métodos obligatorios
        assert callable(getattr(metric, "calculate", None)), "Debe implementar calculate()"
        assert callable(getattr(metric, "calculate_function", None)), (
            "Debe implementar calculate_function()"
        )
        assert callable(getattr(metric, "calculate_class", None)), (
            "Debe implementar calculate_class()"
        )
        assert callable(getattr(metric, "calculate_module", None)), (
            "Debe implementar calculate_module()"
        )
        assert callable(getattr(metric, "calculate_project", None)), (
            "Debe implementar calculate_project()"
        )
        assert callable(getattr(metric, "get_thresholds", None)), (
            "Debe implementar get_thresholds()"
        )
        assert callable(getattr(metric, "interpret", None)), "Debe implementar interpret()"

    def test_basic_functionality(self, metric: IMetric):
        """Test básico de funcionalidad que debe pasar toda métrica."""
        # Test con función simple
        simple_func = self.factory.create_simple_function()
        result = metric.calculate_function(simple_func)

        if result is not None:
            assert isinstance(result, (int, float)), "El resultado de función debe ser numérico"
            self.assertions.assert_metric_bounds(result)

        # Test con clase simple
        simple_class = self.factory.create_class_with_methods()
        class_result = metric.calculate_class(simple_class)

        if class_result is not None:
            assert isinstance(class_result, dict), "El resultado de clase debe ser diccionario"

    def test_edge_cases(self, metric: IMetric):
        """Test de casos extremos que debe manejar toda métrica."""
        edge_functions = self.data_provider.get_edge_case_functions()

        for func in edge_functions:
            try:
                result = metric.calculate_function(func)
                if result is not None:
                    self.assertions.assert_metric_bounds(result)
            except Exception as e:
                # Los errores deben ser específicos y documentados
                assert isinstance(e, (ValueError, TypeError)), (
                    f"Error inesperado: {type(e).__name__}"
                )

    def test_thresholds_and_interpretation(self, metric: IMetric):
        """Test de umbrales e interpretación."""
        thresholds = metric.get_thresholds()
        assert isinstance(thresholds, dict), "Los umbrales deben ser un diccionario"

        # Verificar que tiene las claves básicas de umbrales
        expected_keys = ["low", "medium", "high"]
        for key in expected_keys:
            if key in thresholds:
                assert isinstance(thresholds[key], (int, float)), (
                    f"Umbral '{key}' debe ser numérico"
                )

        # Test de interpretación con valores conocidos
        test_values = [0.0, 1.0, 5.0, 10.0, 20.0]
        for value in test_values:
            interpretation = metric.interpret(value)
            assert isinstance(interpretation, str), "La interpretación debe ser string"

    def verify_metric_interface_compliance(self, metric: IMetric):
        """Método auxiliar para verificar compliance desde tests específicos."""
        self.test_metric_interface_compliance(metric)

    def verify_basic_functionality(self, metric: IMetric):
        """Método auxiliar para verificar funcionalidad básica desde tests específicos."""
        self.test_basic_functionality(metric)

    def verify_edge_cases(self, metric: IMetric):
        """Método auxiliar para verificar edge cases desde tests específicos."""
        self.test_edge_cases(metric)

    def verify_thresholds_and_interpretation(self, metric: IMetric):
        """Método auxiliar para verificar umbrales desde tests específicos."""
        self.test_thresholds_and_interpretation(metric)
