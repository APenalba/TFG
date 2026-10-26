"""Tests unitarios para la métrica de Complejidad de Diseño.

Tests básicos pero robustos que verifican la funcionalidad core de la métrica.
"""

import pytest

from pypex.metrics.design.design_complexity import DesignComplexityMetric
from pypex.parser.code_entities import Class
from tests.unit.metrics.test_utils import TestEntityFactory


class TestDesignComplexityBasic:
    """Tests básicos para DesignComplexityMetric."""

    def setup_method(self):
        """Setup para cada test."""
        self.metric = DesignComplexityMetric()
        self.factory = TestEntityFactory()

    def test_metric_properties(self):
        """Verifica propiedades básicas de la métrica."""
        assert self.metric.name == "design_complexity"
        assert isinstance(self.metric.description, str)
        assert len(self.metric.description) > 10

    def test_get_default_thresholds(self):
        """Verifica umbrales por defecto."""
        thresholds = self.metric.get_default_thresholds()

        assert isinstance(thresholds, dict)
        assert "low" in thresholds
        assert "medium" in thresholds
        assert "high" in thresholds
        assert thresholds["low"] == 2.0
        assert thresholds["medium"] == 5.0
        assert thresholds["high"] == 10.0


class TestDesignComplexityFunctions:
    """Tests para funciones."""

    def setup_method(self):
        """Setup para cada test."""
        self.metric = DesignComplexityMetric()
        self.factory = TestEntityFactory()

    def test_function_without_calls(self):
        """Test función sin llamadas."""
        func = self.factory.create_simple_function("test_func")
        func.calls = []  # Sin llamadas

        result = self.metric.calculate_function(func)

        assert result == 0.0  # Sin complejidad

    def test_function_with_calls(self):
        """Test función con llamadas."""
        func = self.factory.create_simple_function("test_func")
        func.calls = ["func1", "func2", "func3"]  # 3 llamadas

        result = self.metric.calculate_function(func)

        assert result == 3.0  # Complejidad igual al número de llamadas


class TestDesignComplexityClasses:
    """Tests para clases."""

    def setup_method(self):
        """Setup para cada test."""
        self.metric = DesignComplexityMetric()
        self.factory = TestEntityFactory()

    def test_empty_class(self):
        """Test clase vacía."""
        cls = Class(name="EmptyClass")
        cls.methods = []

        result = self.metric.calculate_class(cls)

        assert isinstance(result, dict)
        assert "average" in result
        assert "max" in result
        assert "method_count" in result
        assert "methods_with_calls" in result

        assert result["average"] == 0.0
        assert result["max"] == 0.0
        assert result["method_count"] == 0.0
        assert result["methods_with_calls"] == 0.0

    def test_class_with_simple_methods(self):
        """Test clase con métodos básicos."""
        method1 = self.factory.create_simple_function("method1")
        method1.calls = ["call1"]
        method2 = self.factory.create_simple_function("method2")
        method2.calls = []

        cls = Class(name="TestClass")
        cls.methods = [method1, method2]

        result = self.metric.calculate_class(cls)

        assert isinstance(result, dict)
        assert result["method_count"] == 2.0
        assert result["average"] == 0.5  # (1+0)/2
        assert result["max"] == 1.0
        assert result["methods_with_calls"] == 1.0


class TestDesignComplexityModulesAndProjects:
    """Tests para módulos y proyectos."""

    def setup_method(self):
        """Setup para cada test."""
        self.metric = DesignComplexityMetric()
        self.factory = TestEntityFactory()

    def test_module_returns_none(self):
        """Test que módulos devuelven None."""
        module = self.factory.create_module_with_entities()

        result = self.metric.calculate_module(module)

        assert result is None

    def test_project_returns_none(self):
        """Test que proyectos devuelven None."""
        project = self.factory.create_project_with_modules()

        result = self.metric.calculate_project(project)

        assert result is None


class TestDesignComplexityEdgeCases:
    """Tests para casos especiales."""

    def setup_method(self):
        """Setup para cada test."""
        self.metric = DesignComplexityMetric()
        self.factory = TestEntityFactory()

    def test_get_aggregated_value_function(self):
        """Test get_aggregated_value para función."""
        func = self.factory.create_simple_function("test_func")
        func.calls = ["call1", "call2"]

        aggregated = self.metric.get_aggregated_value(func)
        expected = self.metric.calculate_function(func)

        assert aggregated == expected

    def test_get_aggregated_value_class(self):
        """Test get_aggregated_value para clase."""
        method = self.factory.create_simple_function("method")
        method.calls = ["call1"]
        cls = Class(name="TestClass")
        cls.methods = [method]

        aggregated = self.metric.get_aggregated_value(cls)

        assert isinstance(aggregated, float)
        assert aggregated >= 0.0

    def test_get_aggregated_value_module(self):
        """Test get_aggregated_value para módulo."""
        module = self.factory.create_module_with_entities()

        aggregated = self.metric.get_aggregated_value(module)

        assert aggregated == 0.0  # Módulos devuelven None, agregado es 0.0

    def test_interpret_design_complexity(self):
        """Test función de interpretación."""
        interpretation = self.metric.interpret(10.0)

        assert isinstance(interpretation, str)
        assert len(interpretation) > 0


if __name__ == "__main__":
    pytest.main([__file__])
