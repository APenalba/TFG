"""Tests para el módulo base de métricas.

Este módulo contiene tests para IMetric, BaseMetric, excepciones
y funcionalidad base del sistema de métricas.
"""

import pytest

from pypex.metrics.base import BaseMetric, IMetric, InvalidEntityError, MetricError
from pypex.parser.code_entities import Class, Function, Module, Project
from tests.unit.metrics.test_utils import AssertionHelpers, TestEntityFactory


class TestIMetricInterface:
    """Tests para la interfaz IMetric."""

    def test_imetric_is_abstract(self):
        """Verifica que IMetric es abstracta y no se puede instanciar."""
        with pytest.raises(TypeError):
            IMetric()

    def test_imetric_has_required_methods(self):
        """Verifica que IMetric define todos los métodos abstractos necesarios."""
        required_methods = [
            "name",
            "description",
            "calculate",
            "calculate_function",
            "calculate_class",
            "calculate_module",
            "calculate_project",
            "get_thresholds",
            "interpret",
        ]

        for method_name in required_methods:
            assert hasattr(IMetric, method_name), f"IMetric debe definir {method_name}"


class TestMetricError:
    """Tests para la excepción MetricError."""

    def test_metric_error_creation(self):
        """Verifica que se puede crear MetricError correctamente."""
        error = MetricError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)

    def test_metric_error_inheritance(self):
        """Verifica que MetricError hereda correctamente de Exception."""
        error = MetricError("Test")
        assert isinstance(error, Exception)
        assert isinstance(error, MetricError)


class TestInvalidEntityError:
    """Tests para la excepción InvalidEntityError."""

    def test_invalid_entity_error_creation(self):
        """Verifica que se puede crear InvalidEntityError correctamente."""
        error = InvalidEntityError("Invalid entity type")
        assert str(error) == "Invalid entity type"
        assert isinstance(error, MetricError)
        assert isinstance(error, Exception)


class MockMetric(BaseMetric):
    """Métrica mock para testing de BaseMetric."""

    def __init__(self, name: str = "mock_metric", description: str = "Mock metric for testing"):
        super().__init__(name, description)
        self.function_calls = []
        self.class_calls = []
        self.module_calls = []
        self.project_calls = []

    def calculate_function(self, function: Function) -> float | None:
        """Mock implementation para funciones."""
        self.function_calls.append(function.name)
        # Simular cálculo basado en parámetros
        return float(len(function.parameters)) if function.parameters else 1.0

    def calculate_class(self, cls: Class) -> dict[str, float] | None:
        """Mock implementation para clases."""
        self.class_calls.append(cls.name)
        return {
            "method_count": float(len(cls.methods)),
            "attribute_count": float(len(cls.attributes)),
            "total_complexity": float(len(cls.methods) + len(cls.attributes)),
        }

    def calculate_module(self, module: Module) -> dict[str, float] | None:
        """Mock implementation para módulos."""
        self.module_calls.append(module.name)
        return {
            "function_count": float(len(module.functions)),
            "class_count": float(len(module.classes)),
            "import_count": float(len(module.imports)),
        }

    def calculate_project(self, project: Project) -> dict[str, float] | None:
        """Mock implementation para proyectos."""
        self.project_calls.append(project.name)
        return {
            "module_count": float(len(project.modules)),
            "total_entities": float(
                sum(len(m.functions) + len(m.classes) for m in project.modules)
            ),
        }


class TestBaseMetric:
    """Tests comprehensivos para BaseMetric."""

    def setup_method(self):
        """Setup para cada test."""
        self.factory = TestEntityFactory()
        self.assertions = AssertionHelpers()
        self.metric = MockMetric()

    def test_initialization(self):
        """Verifica la inicialización correcta de BaseMetric."""
        metric = MockMetric("test_metric", "Test description")
        assert metric.name == "test_metric"
        assert metric.description == "Test description"

    def test_property_access(self):
        """Verifica el acceso a propiedades name y description."""
        assert isinstance(self.metric.name, str)
        assert isinstance(self.metric.description, str)
        assert len(self.metric.name) > 0
        assert len(self.metric.description) > 0

    def test_calculate_delegates_to_specific_methods(self):
        """Verifica que calculate() delega correctamente a métodos específicos."""
        # Test con Function
        function = self.factory.create_simple_function("test_func")
        result = self.metric.calculate(function)
        assert isinstance(result, float)
        assert "test_func" in self.metric.function_calls

        # Test con Class
        cls = self.factory.create_class_with_methods("TestClass")
        result = self.metric.calculate(cls)
        assert isinstance(result, dict)
        assert "TestClass" in self.metric.class_calls

        # Test con Module
        module = self.factory.create_module_with_entities("test_module")
        result = self.metric.calculate(module)
        assert isinstance(result, dict)
        assert "test_module" in self.metric.module_calls

    def test_calculate_with_project_raises_error(self):
        """Verifica que calculate() con Project lanza InvalidEntityError."""
        project = self.factory.create_project_with_modules("test_project")

        with pytest.raises(InvalidEntityError) as exc_info:
            self.metric.calculate(project)

        assert "Project" in str(exc_info.value)
        assert "calculate_project" in str(exc_info.value)

    def test_calculate_with_invalid_entity_raises_error(self):
        """Verifica que calculate() con entidad inválida lanza InvalidEntityError."""

        # Crear un objeto mock que no es una entidad válida pero tiene name
        class InvalidEntity:
            def __init__(self):
                self.name = "invalid_entity"

        invalid_entity = InvalidEntity()

        with pytest.raises(InvalidEntityError) as exc_info:
            self.metric.calculate(invalid_entity)

        assert "no está soportado" in str(exc_info.value)

    def test_calculate_function_implementation(self):
        """Verifica la implementación de calculate_function."""
        # Función sin parámetros
        func_no_params = self.factory.create_simple_function("no_params", parameters=[])
        result = self.metric.calculate_function(func_no_params)
        assert result == 1.0

        # Función con parámetros
        func_with_params = self.factory.create_simple_function(
            "with_params", parameters=["a", "b", "c"]
        )
        result = self.metric.calculate_function(func_with_params)
        assert result == 3.0

    def test_calculate_class_implementation(self):
        """Verifica la implementación de calculate_class."""
        cls = self.factory.create_class_with_methods(
            "TestClass", method_names=["method1", "method2"], attributes={"attr1", "attr2", "attr3"}
        )
        result = self.metric.calculate_class(cls)

        expected_keys = ["method_count", "attribute_count", "total_complexity"]
        self.assertions.assert_metric_result_structure(result, expected_keys)
        assert result["method_count"] == 2.0
        assert result["attribute_count"] == 3.0
        assert result["total_complexity"] == 5.0

    def test_calculate_module_implementation(self):
        """Verifica la implementación de calculate_module."""
        module = self.factory.create_module_with_entities(
            "TestModule", function_count=3, class_count=2, import_count=5
        )
        result = self.metric.calculate_module(module)

        expected_keys = ["function_count", "class_count", "import_count"]
        self.assertions.assert_metric_result_structure(result, expected_keys)
        assert result["function_count"] == 3.0
        assert result["class_count"] == 2.0
        assert result["import_count"] == 5.0

    def test_calculate_project_implementation(self):
        """Verifica la implementación de calculate_project."""
        project = self.factory.create_project_with_modules("TestProject", module_count=3)
        result = self.metric.calculate_project(project)

        expected_keys = ["module_count", "total_entities"]
        self.assertions.assert_metric_result_structure(result, expected_keys)
        assert result["module_count"] == 3.0
        assert result["total_entities"] > 0.0

    def test_get_aggregated_value_for_function(self):
        """Verifica get_aggregated_value para función."""
        func = self.factory.create_simple_function(parameters=["a", "b"])
        value = self.metric.get_aggregated_value(func)
        assert value == 2.0  # Número de parámetros

    def test_get_aggregated_value_for_class(self):
        """Verifica get_aggregated_value para clase."""
        cls = self.factory.create_class_with_methods("TestClass")
        value = self.metric.get_aggregated_value(cls)
        assert isinstance(value, float)
        assert value >= 0.0

    def test_get_aggregated_value_with_none_result(self):
        """Verifica get_aggregated_value cuando calculate devuelve None."""

        class MetricThatReturnsNone(BaseMetric):
            def __init__(self):
                super().__init__("none_metric", "Always returns None")

            def calculate_function(self, function: Function) -> None:
                return None

        metric = MetricThatReturnsNone()
        func = self.factory.create_simple_function()
        value = metric.get_aggregated_value(func)
        assert value == 0.0

    def test_get_aggregated_value_with_dict_result(self):
        """Verifica get_aggregated_value con resultado de diccionario."""
        cls = self.factory.create_class_with_methods()
        value = self.metric.get_aggregated_value(cls)
        assert isinstance(value, float)
        assert value >= 0.0

    def test_get_thresholds_default_implementation(self):
        """Verifica la implementación por defecto de get_thresholds."""
        thresholds = self.metric.get_thresholds()
        assert isinstance(thresholds, dict)

    def test_interpret_default_implementation(self):
        """Verifica la implementación por defecto de interpret."""
        interpretation = self.metric.interpret(5.0)
        assert isinstance(interpretation, str)

    def test_metric_interface_compliance(self):
        """Verifica que la métrica cumple con la interfaz IMetric."""
        # Verificar propiedades básicas
        assert hasattr(self.metric, "name"), "La métrica debe tener propiedad 'name'"
        assert hasattr(self.metric, "description"), "La métrica debe tener propiedad 'description'"
        assert isinstance(self.metric.name, str), "El nombre debe ser string"
        assert isinstance(self.metric.description, str), "La descripción debe ser string"
        assert len(self.metric.name) > 0, "El nombre no puede estar vacío"
        assert len(self.metric.description) > 0, "La descripción no puede estar vacía"

        # Verificar métodos obligatorios
        assert callable(getattr(self.metric, "calculate", None)), "Debe implementar calculate()"
        assert callable(getattr(self.metric, "calculate_function", None)), (
            "Debe implementar calculate_function()"
        )
        assert callable(getattr(self.metric, "calculate_class", None)), (
            "Debe implementar calculate_class()"
        )
        assert callable(getattr(self.metric, "calculate_module", None)), (
            "Debe implementar calculate_module()"
        )
        assert callable(getattr(self.metric, "calculate_project", None)), (
            "Debe implementar calculate_project()"
        )
        assert callable(getattr(self.metric, "get_thresholds", None)), (
            "Debe implementar get_thresholds()"
        )
        assert callable(getattr(self.metric, "interpret", None)), "Debe implementar interpret()"


class TestBaseMetricEdgeCases:
    """Tests para casos extremos de BaseMetric."""

    def setup_method(self):
        """Setup para cada test."""
        self.factory = TestEntityFactory()
        self.metric = MockMetric()

    def test_empty_function(self):
        """Test con función vacía."""
        empty_func = self.factory.create_simple_function("empty", parameters=[])
        result = self.metric.calculate_function(empty_func)
        assert result == 1.0  # Valor por defecto de la implementación mock

    def test_empty_class(self):
        """Test con clase vacía."""
        empty_class = Class(name="EmptyClass")
        empty_class.methods = []
        empty_class.attributes = set()

        result = self.metric.calculate_class(empty_class)
        assert result["method_count"] == 0.0
        assert result["attribute_count"] == 0.0

    def test_empty_module(self):
        """Test con módulo vacío."""
        empty_module = Module(name="EmptyModule")
        empty_module.functions = []
        empty_module.classes = []
        empty_module.imports = []

        result = self.metric.calculate_module(empty_module)
        assert result["function_count"] == 0.0
        assert result["class_count"] == 0.0
        assert result["import_count"] == 0.0

    def test_empty_project(self):
        """Test con proyecto vacío."""
        empty_project = Project(name="EmptyProject")
        empty_project.modules = []

        result = self.metric.calculate_project(empty_project)
        assert result["module_count"] == 0.0
        assert result["total_entities"] == 0.0

    def test_large_function(self):
        """Test con función con muchos parámetros."""
        large_params = [f"param_{i}" for i in range(100)]
        large_func = self.factory.create_simple_function("large_func", parameters=large_params)

        result = self.metric.calculate_function(large_func)
        assert result == 100.0

    def test_get_aggregated_value_with_complex_dict(self):
        """Test get_aggregated_value con diccionario complejo."""

        class ComplexDictMetric(BaseMetric):
            def __init__(self):
                super().__init__("complex_dict", "Returns complex dict")

            def calculate_function(self, function: Function) -> dict[str, float]:
                return {
                    "value1": 10.0,
                    "value2": 20.0,
                    "non_numeric": "string",  # Valor no numérico
                    "total": 30.0,  # Valor total que debería usar
                }

        metric = ComplexDictMetric()
        func = self.factory.create_simple_function()
        value = metric.get_aggregated_value(func)
        assert value == 30.0  # Debe usar la clave 'total'

    def test_get_aggregated_value_with_dict_no_total_key(self):
        """Test get_aggregated_value con diccionario sin clave total."""

        class NoTotalKeyMetric(BaseMetric):
            def __init__(self):
                super().__init__("no_total", "No total key")

            def calculate_function(self, function: Function) -> dict[str, float]:
                return {"metric1": 5.0, "metric2": 3.0}

        metric = NoTotalKeyMetric()
        func = self.factory.create_simple_function()
        value = metric.get_aggregated_value(func)
        assert value == 8.0  # Suma de valores numéricos


class TestBaseMetricIntegration:
    """Tests de integración para BaseMetric."""

    def setup_method(self):
        """Setup para cada test."""
        self.factory = TestEntityFactory()
        self.metric = MockMetric()

    def test_basic_functionality_integration(self):
        """Verifica funcionalidad básica de integración."""
        # Test con función simple
        simple_func = self.factory.create_simple_function()
        result = self.metric.calculate_function(simple_func)

        if result is not None:
            assert isinstance(result, (int, float)), "El resultado de función debe ser numérico"
            assert result >= 0.0, "El resultado debe ser no negativo"

        # Test con clase simple
        simple_class = self.factory.create_class_with_methods()
        class_result = self.metric.calculate_class(simple_class)

        if class_result is not None:
            assert isinstance(class_result, dict), "El resultado de clase debe ser diccionario"


@pytest.mark.parametrize(
    "entity_type,expected_result_type",
    [
        ("function", float),
        ("class", dict),
        ("module", dict),
        ("project", dict),
    ],
)
def test_calculate_return_types(entity_type, expected_result_type):
    """Test parametrizado para verificar tipos de retorno."""
    factory = TestEntityFactory()
    metric = MockMetric()

    if entity_type == "function":
        entity = factory.create_simple_function()
        result = metric.calculate_function(entity)
    elif entity_type == "class":
        entity = factory.create_class_with_methods()
        result = metric.calculate_class(entity)
    elif entity_type == "module":
        entity = factory.create_module_with_entities()
        result = metric.calculate_module(entity)
    elif entity_type == "project":
        entity = factory.create_project_with_modules()
        result = metric.calculate_project(entity)

    assert isinstance(result, expected_result_type), (
        f"{entity_type} debe retornar {expected_result_type.__name__}"
    )


if __name__ == "__main__":
    pytest.main([__file__])
