"""Tests comprehensivos para la métrica de Complejidad de Manejo de Excepciones.

Este módulo contiene tests exhaustivos que cubren todos los aspectos
de la métrica de complejidad de manejo de excepciones, incluyendo edge cases.
"""

import pytest
from typing import List, Dict

from pypex.metrics.complexity.exception_handling_complexity import ExceptionHandlingComplexityMetric
from pypex.parser.code_entities import Function, Class, Module, Project
from tests.unit.metrics.test_utils import (
    TestEntityFactory,
    BaseMetricTestCase,
    AssertionHelpers
)


class TestExceptionHandlingComplexityBasic:
    """Tests básicos para la métrica de Complejidad de Manejo de Excepciones."""
    
    def setup_method(self):
        """Setup para cada test."""
        self.factory = TestEntityFactory()
        self.assertions = AssertionHelpers()
        self.metric = ExceptionHandlingComplexityMetric()
    
    def test_metric_properties(self):
        """Verifica las propiedades básicas de la métrica."""
        assert self.metric.name == "exception_handling_complexity"
        assert "excepciones" in self.metric.description.lower()
        assert "manejo" in self.metric.description.lower()
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


class TestExceptionHandlingComplexityFunctions:
    """Tests para cálculo de complejidad de manejo de excepciones en funciones."""
    
    def setup_method(self):
        """Setup para cada test."""
        self.factory = TestEntityFactory()
        self.metric = ExceptionHandlingComplexityMetric()
    
    def test_function_no_exception_handling(self):
        """Test función sin manejo de excepciones (complejidad = 0)."""
        func = self.factory.create_simple_function("no_exceptions")
        func.exception_handlers_count = 0
        func.try_blocks_count = 0
        
        result = self.metric.calculate_function(func)
        
        assert result == 0.0  # Sin manejo de excepciones
    
    def test_function_simple_try_except(self):
        """Test función con try-except simple."""
        func = self.factory.create_simple_function("simple_try_except")
        func.exception_handlers_count = 1  # Un except
        func.try_blocks_count = 1  # Un try
        
        result = self.metric.calculate_function(func)
        
        assert result == 2.0  # 1 + 1 = 2
    
    def test_function_multiple_except_handlers(self):
        """Test función con múltiples manejadores de excepciones."""
        func = self.factory.create_simple_function("multiple_except")
        func.exception_handlers_count = 3  # ValueError, TypeError, Exception
        func.try_blocks_count = 1  # Un try
        
        result = self.metric.calculate_function(func)
        
        assert result == 4.0  # 3 + 1 = 4
    
    def test_function_nested_try_blocks(self):
        """Test función con bloques try anidados."""
        func = self.factory.create_simple_function("nested_try")
        func.exception_handlers_count = 2  # Dos except (uno en cada try)
        func.try_blocks_count = 2  # Dos try (uno anidado)
        
        result = self.metric.calculate_function(func)
        
        assert result == 4.0  # 2 + 2 = 4
    
    def test_function_complex_exception_handling(self):
        """Test función con manejo complejo de excepciones."""
        func = self.factory.create_simple_function("complex_exceptions")
        func.exception_handlers_count = 5  # Múltiples except
        func.try_blocks_count = 3  # Múltiples try (algunos anidados)
        
        result = self.metric.calculate_function(func)
        
        assert result == 8.0  # 5 + 3 = 8
    
    def test_function_only_try_blocks(self):
        """Test función con solo bloques try (sin except)."""
        func = self.factory.create_simple_function("only_try")
        func.exception_handlers_count = 0  # Sin except
        func.try_blocks_count = 2  # Solo try (posiblemente con finally)
        
        result = self.metric.calculate_function(func)
        
        assert result == 2.0  # 0 + 2 = 2
    
    def test_function_only_except_handlers(self):
        """Test función con solo manejadores (edge case)."""
        func = self.factory.create_simple_function("only_except")
        func.exception_handlers_count = 3  # Múltiples except
        func.try_blocks_count = 0  # Sin try (edge case)
        
        result = self.metric.calculate_function(func)
        
        assert result == 3.0  # 3 + 0 = 3


class TestExceptionHandlingComplexityClasses:
    """Tests para cálculo de complejidad de manejo de excepciones en clases."""
    
    def setup_method(self):
        """Setup para cada test."""
        self.factory = TestEntityFactory()
        self.metric = ExceptionHandlingComplexityMetric()
        self.assertions = AssertionHelpers()
    
    def test_empty_class(self):
        """Test clase sin métodos."""
        empty_class = Class(name="EmptyClass")
        empty_class.methods = []
        
        result = self.metric.calculate_class(empty_class)
        
        expected_keys = ["average", "max", "method_count", "methods_with_exceptions"]
        self.assertions.assert_metric_result_structure(result, expected_keys)
        
        assert result["average"] == 0.0
        assert result["max"] == 0.0
        assert result["method_count"] == 0.0
        assert result["methods_with_exceptions"] == 0.0
    
    def test_class_with_no_exception_handling(self):
        """Test clase con métodos sin manejo de excepciones."""
        cls = self.factory.create_class_with_methods(
            class_name="NoExceptionsClass",
            method_names=["method1", "method2", "method3"]
        )
        
        # Todos los métodos sin manejo de excepciones
        for method in cls.methods:
            method.exception_handlers_count = 0
            method.try_blocks_count = 0
        
        result = self.metric.calculate_class(cls)
        
        assert result["average"] == 0.0  # Todos sin excepciones
        assert result["max"] == 0.0
        assert result["method_count"] == 3.0
        assert result["methods_with_exceptions"] == 0.0  # Ninguno con excepciones
    
    def test_class_with_exception_handling(self):
        """Test clase con métodos que manejan excepciones."""
        cls = self.factory.create_class_with_methods(
            class_name="ExceptionsClass",
            method_names=["simple", "moderate", "complex"]
        )
        
        # Configurar manejo de excepciones para cada método
        cls.methods[0].exception_handlers_count = 0
        cls.methods[0].try_blocks_count = 0  # Sin excepciones = 0
        
        cls.methods[1].exception_handlers_count = 1
        cls.methods[1].try_blocks_count = 1  # Simple try-except = 2
        
        cls.methods[2].exception_handlers_count = 3
        cls.methods[2].try_blocks_count = 2  # Complejo = 5
        
        result = self.metric.calculate_class(cls)
        
        assert result["average"] == pytest.approx(2.33, abs=0.01)  # (0+2+5)/3
        assert result["max"] == 5.0
        assert result["method_count"] == 3.0
        assert result["methods_with_exceptions"] == 2.0  # Dos métodos con excepciones
    
    def test_class_all_methods_with_exceptions(self):
        """Test clase donde todos los métodos manejan excepciones."""
        cls = self.factory.create_class_with_methods(
            class_name="AllExceptionsClass",
            method_names=["exc1", "exc2"]
        )
        
        # Todos los métodos con manejo de excepciones
        cls.methods[0].exception_handlers_count = 1
        cls.methods[0].try_blocks_count = 1  # Complejidad = 2
        
        cls.methods[1].exception_handlers_count = 2
        cls.methods[1].try_blocks_count = 2  # Complejidad = 4
        
        result = self.metric.calculate_class(cls)
        
        assert result["average"] == 3.0  # (2+4)/2
        assert result["max"] == 4.0
        assert result["method_count"] == 2.0
        assert result["methods_with_exceptions"] == 2.0  # Todos los métodos
    
    def test_class_high_exception_complexity(self):
        """Test clase con alta complejidad de manejo de excepciones."""
        cls = self.factory.create_class_with_methods(
            class_name="HighExceptionClass",
            method_names=["ultra_complex"]
        )
        
        # Método con manejo muy complejo
        cls.methods[0].exception_handlers_count = 8  # Muchos except
        cls.methods[0].try_blocks_count = 4  # Múltiples try anidados
        
        result = self.metric.calculate_class(cls)
        
        assert result["average"] == 12.0  # 8 + 4 = 12
        assert result["max"] == 12.0
        assert result["method_count"] == 1.0
        assert result["methods_with_exceptions"] == 1.0


class TestExceptionHandlingComplexityModulesAndProjects:
    """Tests para módulos y proyectos (que devuelven None)."""
    
    def setup_method(self):
        """Setup para cada test."""
        self.factory = TestEntityFactory()
        self.metric = ExceptionHandlingComplexityMetric()
    
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


class TestExceptionHandlingComplexityEdgeCases:
    """Tests para casos extremos y edge cases."""
    
    def setup_method(self):
        """Setup para cada test."""
        self.factory = TestEntityFactory()
        self.metric = ExceptionHandlingComplexityMetric()
    
    def test_function_without_exception_attributes(self):
        """Test función sin atributos de excepciones."""
        func = self.factory.create_simple_function("no_exc_attrs")
        # Asegurar que los atributos existen con valores por defecto
        func.exception_handlers_count = 0
        func.try_blocks_count = 0
        
        result = self.metric.calculate_function(func)
        
        assert result == 0.0  # Sin manejo de excepciones
    
    def test_function_with_high_exception_counts(self):
        """Test función con conteos muy altos de excepciones."""
        func = self.factory.create_simple_function("high_exc")
        func.exception_handlers_count = 20  # Muchos except
        func.try_blocks_count = 10  # Muchos try
        
        result = self.metric.calculate_function(func)
        
        assert result == 30.0  # 20 + 10 = 30
    
    def test_function_with_negative_counts(self):
        """Test función con conteos negativos (edge case)."""
        func = self.factory.create_simple_function("negative_exc")
        func.exception_handlers_count = -1  # Edge case
        func.try_blocks_count = -1  # Edge case
        
        result = self.metric.calculate_function(func)
        
        assert result == -2.0  # -1 + (-1) = -2
    
    def test_get_aggregated_value_function(self):
        """Test get_aggregated_value para función."""
        func = self.factory.create_simple_function("test_func")
        func.exception_handlers_count = 2
        func.try_blocks_count = 1
        
        aggregated = self.metric.get_aggregated_value(func)
        
        assert aggregated == 3.0  # 2 + 1 = 3
    
    def test_get_aggregated_value_class(self):
        """Test get_aggregated_value para clase."""
        cls = self.factory.create_class_with_methods()
        
        # Configurar manejo de excepciones en métodos
        cls.methods[0].exception_handlers_count = 1
        cls.methods[0].try_blocks_count = 1  # Complejidad = 2
        
        cls.methods[1].exception_handlers_count = 0
        cls.methods[1].try_blocks_count = 1  # Complejidad = 1
        
        cls.methods[2].exception_handlers_count = 0
        cls.methods[2].try_blocks_count = 0  # Complejidad = 0
        
        aggregated = self.metric.get_aggregated_value(cls)
        
        # Para clases, get_aggregated_value suma todos los valores del diccionario
        # average=1.0, max=2.0, method_count=3.0, methods_with_exceptions=2.0
        # Suma total = 1.0 + 2.0 + 3.0 + 2.0 = 8.0
        assert aggregated == 8.0
    
    def test_get_aggregated_value_module(self):
        """Test get_aggregated_value para módulo."""
        module = self.factory.create_module_with_entities("test_module")
        
        aggregated = self.metric.get_aggregated_value(module)
        
        # Para módulos, debe devolver 0.0 ya que calculate devuelve None
        assert aggregated == 0.0


class TestExceptionHandlingComplexityIntegration:
    """Tests de integración para la métrica de Complejidad de Manejo de Excepciones."""
    
    def setup_method(self):
        """Setup para cada test."""
        self.metric = ExceptionHandlingComplexityMetric()
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
        # Simular función con manejo moderado de excepciones
        func = self.factory.create_simple_function("file_processor")
        func.exception_handlers_count = 2  # FileNotFoundError, PermissionError
        func.try_blocks_count = 1  # Un try principal
        
        result = self.metric.calculate_function(func)
        
        assert result == 3.0  # 2 + 1 = 3
        
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
        cls.methods[0].exception_handlers_count = 0
        cls.methods[0].try_blocks_count = 0  # 0
        
        cls.methods[1].exception_handlers_count = 1
        cls.methods[1].try_blocks_count = 1  # 2
        
        cls.methods[2].exception_handlers_count = 4
        cls.methods[2].try_blocks_count = 2  # 6
        
        result = self.metric.calculate_class(cls)
        
        # Verificar consistencia de estadísticas
        assert result["max"] >= result["average"]
        assert result["method_count"] == 3.0
        assert result["methods_with_exceptions"] == 2.0  # Solo métodos "low" y "high"


@pytest.mark.parametrize("handlers,try_blocks,expected_complexity", [
    (0, 0, 0.0),
    (1, 0, 1.0),
    (0, 1, 1.0),
    (1, 1, 2.0),
    (3, 1, 4.0),
    (2, 3, 5.0),
    (5, 3, 8.0),
])
def test_exception_handling_complexity_calculation(handlers, try_blocks, expected_complexity):
    """Test parametrizado para verificar cálculo de complejidad de manejo de excepciones."""
    factory = TestEntityFactory()
    metric = ExceptionHandlingComplexityMetric()
    
    func = factory.create_simple_function("test_func")
    func.exception_handlers_count = handlers
    func.try_blocks_count = try_blocks
    
    result = metric.calculate_function(func)
    assert result == expected_complexity


@pytest.mark.parametrize("method_exceptions,expected_stats", [
    ([(0, 0), (0, 0), (0, 0)], {"avg": 0.0, "max": 0.0, "with_exc": 0}),
    ([(1, 1), (0, 0), (0, 0)], {"avg": 0.67, "max": 2.0, "with_exc": 1}),
    ([(1, 1), (2, 1), (3, 2)], {"avg": 3.33, "max": 5.0, "with_exc": 3}),
    ([(0, 0), (5, 2), (1, 1)], {"avg": 3.0, "max": 7.0, "with_exc": 2}),
])
def test_class_exception_handling_complexity_aggregation(method_exceptions, expected_stats):
    """Test parametrizado para verificar agregación de complejidad de manejo de excepciones en clases."""
    factory = TestEntityFactory()
    metric = ExceptionHandlingComplexityMetric()
    
    cls = factory.create_class_with_methods(method_names=["m1", "m2", "m3"])
    
    for i, (handlers, try_blocks) in enumerate(method_exceptions):
        cls.methods[i].exception_handlers_count = handlers
        cls.methods[i].try_blocks_count = try_blocks
    
    result = metric.calculate_class(cls)
    
    assert abs(result["average"] - expected_stats["avg"]) < 0.01  # Tolerancia para decimales
    assert result["max"] == expected_stats["max"]
    assert result["methods_with_exceptions"] == expected_stats["with_exc"]


if __name__ == "__main__":
    pytest.main([__file__]) 