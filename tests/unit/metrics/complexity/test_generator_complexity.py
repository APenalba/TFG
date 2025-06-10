"""Tests comprehensivos para la métrica de Complejidad de Generadores.

Este módulo contiene tests exhaustivos que cubren todos los aspectos
de la métrica de complejidad de generadores, incluyendo edge cases.
"""

import pytest
from typing import List, Dict

from pypex.metrics.complexity.generator_complexity import GeneratorComplexityMetric
from pypex.parser.code_entities import Function, Class, Module, Project
from tests.unit.metrics.test_utils import (
    TestEntityFactory,
    BaseMetricTestCase,
    AssertionHelpers
)


class TestGeneratorComplexityBasic:
    """Tests básicos para la métrica de Complejidad de Generadores."""
    
    def setup_method(self):
        """Setup para cada test."""
        self.factory = TestEntityFactory()
        self.assertions = AssertionHelpers()
        self.metric = GeneratorComplexityMetric()
    
    def test_metric_properties(self):
        """Verifica las propiedades básicas de la métrica."""
        assert self.metric.name == "generator_complexity"
        assert "generadores" in self.metric.description.lower()
        assert "yield" in self.metric.description.lower()
        assert "complejidad" in self.metric.description.lower()
        assert len(self.metric.description) > 50  # Descripción detallada
    
    def test_metric_interface_compliance(self):
        """Verifica que la métrica cumple con la interfaz IMetric."""
        # Verificar propiedades básicas
        assert hasattr(self.metric, 'name'), "La métrica debe tener propiedad 'name'"
        assert hasattr(self.metric, 'description'), "La métrica debe tener propiedad 'description'"
        assert isinstance(self.metric.name, str), "El nombre debe ser string"
        assert isinstance(self.metric.description, str), "La descripción debe ser string"
        assert len(self.metric.name) > 0, "El nombre no puede estar vacío"
        assert len(self.metric.description) > 0, "La descripción no puede estar vacía"
        
        # Verificar métodos obligatorios
        assert callable(getattr(self.metric, 'calculate', None)), "Debe implementar calculate()"
        assert callable(getattr(self.metric, 'calculate_function', None)), "Debe implementar calculate_function()"
        assert callable(getattr(self.metric, 'calculate_class', None)), "Debe implementar calculate_class()"
        assert callable(getattr(self.metric, 'calculate_module', None)), "Debe implementar calculate_module()"
        assert callable(getattr(self.metric, 'calculate_project', None)), "Debe implementar calculate_project()"
        assert callable(getattr(self.metric, 'get_thresholds', None)), "Debe implementar get_thresholds()"
        assert callable(getattr(self.metric, 'interpret', None)), "Debe implementar interpret()"


class TestGeneratorComplexityFunctions:
    """Tests para cálculo de complejidad de generadores en funciones."""
    
    def setup_method(self):
        """Setup para cada test."""
        self.factory = TestEntityFactory()
        self.metric = GeneratorComplexityMetric()
    
    def test_function_no_yields(self):
        """Test función sin yields (función regular = 0)."""
        func = self.factory.create_simple_function("regular_func")
        func.yield_expressions_count = 0  # Sin yields
        
        result = self.metric.calculate_function(func)
        
        assert result == 0.0  # Sin yields
    
    def test_function_single_yield(self):
        """Test función con un solo yield."""
        func = self.factory.create_simple_function("single_yield")
        func.yield_expressions_count = 1  # yield value
        
        result = self.metric.calculate_function(func)
        
        assert result == 1.0  # Un yield
    
    def test_function_multiple_yields(self):
        """Test función con múltiples yields."""
        func = self.factory.create_simple_function("multiple_yields")
        func.yield_expressions_count = 3  # yield 1, yield 2, yield 3
        
        result = self.metric.calculate_function(func)
        
        assert result == 3.0  # Tres yields
    
    def test_function_yield_in_loop(self):
        """Test función con yields en bucles."""
        func = self.factory.create_simple_function("yield_in_loop")
        func.yield_expressions_count = 5  # for i in range(5): yield i
        
        result = self.metric.calculate_function(func)
        
        assert result == 5.0  # Cada yield cuenta
    
    def test_function_yield_from(self):
        """Test función con yield from."""
        func = self.factory.create_simple_function("yield_from_func")
        func.yield_expressions_count = 2  # yield from [1, 2] + yield 3
        
        result = self.metric.calculate_function(func)
        
        assert result == 2.0  # yield from cuenta como yield
    
    def test_function_complex_generator(self):
        """Test función generadora compleja."""
        func = self.factory.create_simple_function("complex_generator")
        func.yield_expressions_count = 8  # Múltiples yields, yield from, en bucles y condiciones
        
        result = self.metric.calculate_function(func)
        
        assert result == 8.0  # Alta complejidad de generador
    
    def test_function_conditional_yields(self):
        """Test función con yields condicionales."""
        func = self.factory.create_simple_function("conditional_yields")
        func.yield_expressions_count = 4  # if/else con yields en cada rama
        
        result = self.metric.calculate_function(func)
        
        assert result == 4.0  # Yields condicionales
    
    def test_function_nested_generator(self):
        """Test función con generador anidado."""
        func = self.factory.create_simple_function("nested_generator")
        func.yield_expressions_count = 6  # Generador que llama a otros generadores
        
        result = self.metric.calculate_function(func)
        
        assert result == 6.0  # Complejidad de anidamiento


class TestGeneratorComplexityClasses:
    """Tests para cálculo de complejidad de generadores en clases."""
    
    def setup_method(self):
        """Setup para cada test."""
        self.factory = TestEntityFactory()
        self.metric = GeneratorComplexityMetric()
        self.assertions = AssertionHelpers()
    
    def test_empty_class(self):
        """Test clase sin métodos."""
        empty_class = Class(name="EmptyClass")
        empty_class.methods = []
        
        result = self.metric.calculate_class(empty_class)
        
        expected_keys = ["average", "max", "method_count", "generator_methods"]
        self.assertions.assert_metric_result_structure(result, expected_keys)
        
        assert result["average"] == 0.0
        assert result["max"] == 0.0
        assert result["method_count"] == 0.0
        assert result["generator_methods"] == 0.0
    
    def test_class_with_no_generators(self):
        """Test clase con métodos sin yields."""
        cls = self.factory.create_class_with_methods(
            class_name="NoGeneratorsClass",
            method_names=["method1", "method2", "method3"]
        )
        
        # Todos los métodos sin yields
        for method in cls.methods:
            method.yield_expressions_count = 0
        
        result = self.metric.calculate_class(cls)
        
        assert result["average"] == 0.0  # Todos sin yields
        assert result["max"] == 0.0
        assert result["method_count"] == 3.0
        assert result["generator_methods"] == 0.0  # Ninguno es generador
    
    def test_class_with_generators(self):
        """Test clase con métodos generadores."""
        cls = self.factory.create_class_with_methods(
            class_name="GeneratorsClass",
            method_names=["regular", "simple_gen", "complex_gen"]
        )
        
        # Configurar yields para cada método
        cls.methods[0].yield_expressions_count = 0  # Sin yields = 0
        cls.methods[1].yield_expressions_count = 2  # Generador simple = 2
        cls.methods[2].yield_expressions_count = 5  # Generador complejo = 5
        
        result = self.metric.calculate_class(cls)
        
        assert result["average"] == pytest.approx(2.33, abs=0.01)  # (0+2+5)/3
        assert result["max"] == 5.0
        assert result["method_count"] == 3.0
        assert result["generator_methods"] == 2.0  # Dos métodos con yields > 0
    
    def test_class_all_generators(self):
        """Test clase donde todos los métodos son generadores."""
        cls = self.factory.create_class_with_methods(
            class_name="AllGeneratorsClass",
            method_names=["gen1", "gen2"]
        )
        
        # Todos los métodos con yields
        cls.methods[0].yield_expressions_count = 1  # Generador simple
        cls.methods[1].yield_expressions_count = 4  # Generador moderado
        
        result = self.metric.calculate_class(cls)
        
        assert result["average"] == 2.5  # (1+4)/2
        assert result["max"] == 4.0
        assert result["method_count"] == 2.0
        assert result["generator_methods"] == 2.0  # Todos los métodos
    
    def test_class_high_generator_complexity(self):
        """Test clase con alta complejidad de generadores."""
        cls = self.factory.create_class_with_methods(
            class_name="HighGenClass",
            method_names=["ultra_generator"]
        )
        
        # Método con muchos yields
        cls.methods[0].yield_expressions_count = 12  # Generador muy complejo
        
        result = self.metric.calculate_class(cls)
        
        assert result["average"] == 12.0
        assert result["max"] == 12.0
        assert result["method_count"] == 1.0
        assert result["generator_methods"] == 1.0


class TestGeneratorComplexityModulesAndProjects:
    """Tests para módulos y proyectos (que devuelven None)."""
    
    def setup_method(self):
        """Setup para cada test."""
        self.factory = TestEntityFactory()
        self.metric = GeneratorComplexityMetric()
    
    def test_module_returns_none(self):
        """Test que módulos devuelven None."""
        module = self.factory.create_module_with_entities("test_module")
        
        result = self.metric.calculate_module(module)
        
        assert result is None
    
    def test_project_returns_none(self):
        """Test que proyectos devuelven None."""
        project = self.factory.create_project_with_modules("test_project")
        
        result = self.metric.calculate_project(project)
        
        assert result is None


class TestGeneratorComplexityEdgeCases:
    """Tests para casos extremos y edge cases."""
    
    def setup_method(self):
        """Setup para cada test."""
        self.factory = TestEntityFactory()
        self.metric = GeneratorComplexityMetric()
    
    def test_function_without_yield_attribute(self):
        """Test función sin atributo yield_expressions_count."""
        func = self.factory.create_simple_function("no_yield_attr")
        # Asegurar que el atributo existe con valor por defecto
        func.yield_expressions_count = 0
        
        result = self.metric.calculate_function(func)
        
        assert result == 0.0  # Sin yields
    
    def test_function_with_high_yield_count(self):
        """Test función con conteo muy alto de yields."""
        func = self.factory.create_simple_function("high_yield")
        func.yield_expressions_count = 25  # Muchísimos yields
        
        result = self.metric.calculate_function(func)
        
        assert result == 25.0
    
    def test_function_with_negative_yield_count(self):
        """Test función con conteo negativo de yields (edge case)."""
        func = self.factory.create_simple_function("negative_yield")
        func.yield_expressions_count = -1  # Edge case
        
        result = self.metric.calculate_function(func)
        
        assert result == -1.0  # Maneja negativos
    
    def test_get_aggregated_value_function(self):
        """Test get_aggregated_value para función."""
        func = self.factory.create_simple_function("test_func")
        func.yield_expressions_count = 3
        
        aggregated = self.metric.get_aggregated_value(func)
        
        assert aggregated == 3.0
    
    def test_get_aggregated_value_class(self):
        """Test get_aggregated_value para clase."""
        cls = self.factory.create_class_with_methods()
        
        # Configurar yields en métodos
        cls.methods[0].yield_expressions_count = 2  # Complejidad = 2
        cls.methods[1].yield_expressions_count = 1  # Complejidad = 1
        cls.methods[2].yield_expressions_count = 0  # Complejidad = 0
        
        aggregated = self.metric.get_aggregated_value(cls)
        
        # Para clases, get_aggregated_value suma todos los valores del diccionario
        # average=1.0, max=2.0, method_count=3.0, generator_methods=2.0
        # Suma total = 1.0 + 2.0 + 3.0 + 2.0 = 8.0
        assert aggregated == 8.0
    
    def test_get_aggregated_value_module(self):
        """Test get_aggregated_value para módulo."""
        module = self.factory.create_module_with_entities("test_module")
        
        aggregated = self.metric.get_aggregated_value(module)
        
        # Para módulos, debe devolver 0.0 ya que calculate devuelve None
        assert aggregated == 0.0


class TestGeneratorComplexityIntegration:
    """Tests de integración para la métrica de Complejidad de Generadores."""
    
    def setup_method(self):
        """Setup para cada test."""
        self.metric = GeneratorComplexityMetric()
        self.factory = TestEntityFactory()
    
    def test_thresholds_configuration(self):
        """Verifica que los umbrales están correctamente configurados."""
        thresholds = self.metric.get_thresholds()
        
        assert isinstance(thresholds, dict)
        # Verificar que hay umbrales para diferentes niveles
    
    def test_interpretation_with_known_values(self):
        """Verifica interpretación con valores conocidos."""
        test_values = [0.0, 1.0, 2.0, 3.0, 5.0, 6.0, 10.0]
        
        for value in test_values:
            interpretation = self.metric.interpret(value)
            assert isinstance(interpretation, str), f"Interpretación debe ser string para valor {value}"
            assert len(interpretation) > 0, f"Interpretación no puede estar vacía para valor {value}"
    
    def test_realistic_function_analysis(self):
        """Test con análisis de función realista."""
        # Simular función generadora moderadamente compleja
        func = self.factory.create_simple_function("data_generator")
        func.yield_expressions_count = 4  # Generador que produce varios valores
        
        result = self.metric.calculate_function(func)
        
        assert result == 4.0
        
        # Verificar interpretación
        interpretation = self.metric.interpret(result)
        assert isinstance(interpretation, str)
        assert len(interpretation) > 0
    
    def test_class_statistics_consistency(self):
        """Test que las estadísticas de clase son consistentes."""
        cls = self.factory.create_class_with_methods(
            class_name="ConsistencyTest",
            method_names=["none", "low", "high"]
        )
        
        # Configurar complejidades conocidas
        cls.methods[0].yield_expressions_count = 0  # 0
        cls.methods[1].yield_expressions_count = 1  # 1
        cls.methods[2].yield_expressions_count = 6  # 6
        
        result = self.metric.calculate_class(cls)
        
        # Verificar consistencia de estadísticas
        assert result["max"] >= result["average"]
        assert result["method_count"] == 3.0
        assert result["generator_methods"] == 2.0  # Solo métodos "low" y "high"


@pytest.mark.parametrize("yield_count,expected_complexity", [
    (0, 0.0),
    (1, 1.0),
    (2, 2.0),
    (3, 3.0),
    (5, 5.0),
    (10, 10.0),
    (15, 15.0),
])
def test_generator_complexity_calculation(yield_count, expected_complexity):
    """Test parametrizado para verificar cálculo de complejidad de generadores."""
    factory = TestEntityFactory()
    metric = GeneratorComplexityMetric()
    
    func = factory.create_simple_function("test_func")
    func.yield_expressions_count = yield_count
    
    result = metric.calculate_function(func)
    assert result == expected_complexity


@pytest.mark.parametrize("method_yields,expected_stats", [
    ([0, 0, 0], {"avg": 0.0, "max": 0.0, "generators": 0}),
    ([1, 0, 0], {"avg": 0.33, "max": 1.0, "generators": 1}),
    ([1, 2, 3], {"avg": 2.0, "max": 3.0, "generators": 3}),
    ([0, 5, 2], {"avg": 2.33, "max": 5.0, "generators": 2}),
    ([10, 8, 12], {"avg": 10.0, "max": 12.0, "generators": 3}),
])
def test_class_generator_complexity_aggregation(method_yields, expected_stats):
    """Test parametrizado para verificar agregación de complejidad de generadores en clases."""
    factory = TestEntityFactory()
    metric = GeneratorComplexityMetric()
    
    cls = factory.create_class_with_methods(method_names=["m1", "m2", "m3"])
    
    for i, yield_count in enumerate(method_yields):
        cls.methods[i].yield_expressions_count = yield_count
    
    result = metric.calculate_class(cls)
    
    assert abs(result["average"] - expected_stats["avg"]) < 0.01  # Tolerancia para decimales
    assert result["max"] == expected_stats["max"]
    assert result["generator_methods"] == expected_stats["generators"]


if __name__ == "__main__":
    pytest.main([__file__]) 