"""Tests unitarios para la métrica de Profundidad de Anidamiento.

Tests básicos pero robustos que verifican la funcionalidad core de la métrica.
"""

import pytest

from pypex.metrics.complexity.nesting_depth import NestingDepth
from pypex.parser.code_entities import Function, Class, Module, Project
from tests.unit.metrics.test_utils import TestEntityFactory


class TestNestingDepthBasic:
    """Tests básicos para NestingDepth."""
    
    def setup_method(self):
        """Setup para cada test."""
        self.metric = NestingDepth()
        self.factory = TestEntityFactory()
    
    def test_metric_properties(self):
        """Verifica propiedades básicas de la métrica."""
        assert self.metric.name == "nesting_depth"
        assert isinstance(self.metric.description, str)
        assert len(self.metric.description) > 10
    
    def test_get_default_thresholds(self):
        """Verifica umbrales por defecto."""
        thresholds = self.metric.get_default_thresholds()
        
        assert isinstance(thresholds, dict)
        assert "low" in thresholds
        assert "medium" in thresholds
        assert "high" in thresholds
        assert thresholds["low"] == 3.0
        assert thresholds["medium"] == 6.0
        assert thresholds["high"] == 9.0


class TestNestingDepthFunctions:
    """Tests para funciones."""
    
    def setup_method(self):
        """Setup para cada test."""
        self.metric = NestingDepth()
        self.factory = TestEntityFactory()
    
    def test_function_without_astroid_node(self):
        """Test función sin nodo astroid - fallback básico."""
        func = self.factory.create_simple_function("test_func")
        func.astroid_node = None
        
        result = self.metric.calculate_function(func)
        
        assert result == 0.0  # Sin anidamiento detectable
    
    def test_function_with_astroid_node_simple(self):
        """Test función con código simple."""
        code = """
def simple_function():
    x = 5
    return x
"""
        func = self.factory.create_function_from_code(code, "simple_function")
        
        result = self.metric.calculate_function(func)
        
        assert isinstance(result, float)
        assert result >= 0.0  # Profundidad no negativa


class TestNestingDepthClasses:
    """Tests para clases."""
    
    def setup_method(self):
        """Setup para cada test."""
        self.metric = NestingDepth()
        self.factory = TestEntityFactory()
    
    def test_empty_class(self):
        """Test clase vacía."""
        cls = Class(name="EmptyClass")
        cls.methods = []
        
        result = self.metric.calculate_class(cls)
        
        assert isinstance(result, dict)
        assert "avg_depth" in result
        assert "max_depth" in result
        assert "min_depth" in result
        assert "method_count" in result
        assert "high_nesting_methods" in result
        
        assert result["avg_depth"] == 0.0
        assert result["max_depth"] == 0.0
        assert result["min_depth"] == 0.0
        assert result["method_count"] == 0.0
        assert result["high_nesting_methods"] == 0.0
    
    def test_class_with_simple_methods(self):
        """Test clase con métodos básicos."""
        method1 = self.factory.create_simple_function("method1")
        method2 = self.factory.create_simple_function("method2")
        
        cls = Class(name="TestClass")
        cls.methods = [method1, method2]
        
        result = self.metric.calculate_class(cls)
        
        assert isinstance(result, dict)
        assert result["method_count"] == 2.0
        assert result["avg_depth"] >= 0.0
        assert result["max_depth"] >= result["min_depth"]


class TestNestingDepthModulesAndProjects:
    """Tests para módulos y proyectos."""
    
    def setup_method(self):
        """Setup para cada test."""
        self.metric = NestingDepth()
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


class TestNestingDepthEdgeCases:
    """Tests para casos especiales."""
    
    def setup_method(self):
        """Setup para cada test."""
        self.metric = NestingDepth()
        self.factory = TestEntityFactory()
    
    def test_get_aggregated_value_function(self):
        """Test get_aggregated_value para función."""
        func = self.factory.create_simple_function("test_func")
        
        aggregated = self.metric.get_aggregated_value(func)
        expected = self.metric.calculate_function(func)
        
        assert aggregated == expected
    
    def test_get_aggregated_value_class(self):
        """Test get_aggregated_value para clase."""
        method = self.factory.create_simple_function("method")
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
    
    def test_interpret_nesting_level(self):
        """Test función de interpretación."""
        interpretation = self.metric.interpret(5.0)
        
        assert isinstance(interpretation, str)
        assert len(interpretation) > 0


if __name__ == "__main__":
    pytest.main([__file__]) 