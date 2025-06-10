"""Tests comprehensivos para la métrica de Profundidad de Comprensión Anidada.

Este módulo contiene tests exhaustivos que cubren todos los aspectos
de la métrica de profundidad de comprensión anidada, incluyendo edge cases.
"""

import pytest
from typing import List, Dict

from pypex.metrics.complexity.nested_comprehension_depth import NestedComprehensionDepthMetric
from pypex.parser.code_entities import Function, Class, Module, Project
from tests.unit.metrics.test_utils import (
    TestEntityFactory,
    BaseMetricTestCase,
    AssertionHelpers
)


class TestNestedComprehensionDepthBasic:
    """Tests básicos para la métrica de Profundidad de Comprensión Anidada."""
    
    def setup_method(self):
        """Setup para cada test."""
        self.factory = TestEntityFactory()
        self.assertions = AssertionHelpers()
        self.metric = NestedComprehensionDepthMetric()
    
    def test_metric_properties(self):
        """Verifica las propiedades básicas de la métrica."""
        assert self.metric.name == "nested_comprehension_depth"
        assert "profundidad" in self.metric.description.lower()
        assert "anidamiento" in self.metric.description.lower()
        assert "comprensión" in self.metric.description.lower()
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


class TestNestedComprehensionDepthFunctions:
    """Tests para cálculo de profundidad de comprensión anidada en funciones."""
    
    def setup_method(self):
        """Setup para cada test."""
        self.factory = TestEntityFactory()
        self.metric = NestedComprehensionDepthMetric()
    
    def test_function_no_comprehensions(self):
        """Test función sin comprensiones (profundidad = 0)."""
        code = """
def no_comp_func():
    x = 5
    y = 10
    return x + y
"""
        func = self.factory.create_function_from_code(code, "no_comp_func")
        
        result = self.metric.calculate_function(func)
        
        assert result == 0.0  # Sin comprensiones
    
    def test_function_simple_comprehension(self):
        """Test función con comprensión simple (nivel 1)."""
        code = """
def simple_comp():
    result = [x for x in range(10)]
    return result
"""
        func = self.factory.create_function_from_code(code, "simple_comp")
        
        result = self.metric.calculate_function(func)
        
        assert result == 1.0  # Nivel 1
    
    def test_function_nested_comprehension(self):
        """Test función con comprensión anidada (nivel 2)."""
        code = """
def nested_comp():
    result = [[x for x in row] for row in matrix]
    return result
"""
        func = self.factory.create_function_from_code(code, "nested_comp")
        
        result = self.metric.calculate_function(func)
        
        assert result == 2.0  # Nivel 2
    
    def test_function_deeply_nested_comprehension(self):
        """Test función con comprensión profundamente anidada (nivel 3)."""
        code = """
def deep_nested():
    result = [[[z for z in y] for y in x] for x in data]
    return result
"""
        func = self.factory.create_function_from_code(code, "deep_nested")
        
        result = self.metric.calculate_function(func)
        
        assert result == 3.0  # Nivel 3
    
    def test_function_multiple_comprehensions_different_levels(self):
        """Test función con múltiples comprensiones de diferentes niveles."""
        code = """
def multi_levels():
    simple = [x for x in range(10)]  # Nivel 1
    nested = [[x for x in row] for row in matrix]  # Nivel 2
    single = [y for y in data]  # Nivel 1
    return simple, nested, single
"""
        func = self.factory.create_function_from_code(code, "multi_levels")
        
        result = self.metric.calculate_function(func)
        
        assert result == 2.0  # Máximo nivel = 2
    
    def test_function_multiple_comprehensions_same_level(self):
        """Test función con múltiples comprensiones del mismo nivel."""
        code = """
def same_levels():
    comp1 = [[x for x in row] for row in matrix1]  # Nivel 2
    comp2 = {k: [v for v in values] for k, values in data.items()}  # Nivel 2
    comp3 = ((x for x in row) for row in matrix2)  # Nivel 2
    return comp1, comp2, comp3
"""
        func = self.factory.create_function_from_code(code, "same_levels")
        
        result = self.metric.calculate_function(func)
        
        assert result == 2.0  # Todas nivel 2
    
    def test_function_very_deep_nesting(self):
        """Test función con anidamiento muy profundo."""
        code = """
def very_deep():
    result = [[[[[x for x in a] for a in b] for b in c] for c in d] for d in data]
    return result
"""
        func = self.factory.create_function_from_code(code, "very_deep")
        
        result = self.metric.calculate_function(func)
        
        assert result == 5.0  # Nivel 5
    
    def test_function_mixed_comprehension_types(self):
        """Test función con diferentes tipos de comprensiones anidadas."""
        code = """
def mixed_types():
    list_comp = [x for x in data]  # Nivel 1
    dict_comp = {k: [[v for v in vals] for vals in groups] for k, groups in nested_data.items()}  # Nivel 3
    set_comp = {[x for x in group] for group in grouped_data}  # Nivel 2
    gen_expr = (x for x in simple_data)  # Nivel 1
    return list_comp, dict_comp, set_comp, gen_expr
"""
        func = self.factory.create_function_from_code(code, "mixed_types")
        
        result = self.metric.calculate_function(func)
        
        assert result == 3.0  # Máximo = 3


class TestNestedComprehensionDepthClasses:
    """Tests para cálculo de profundidad de comprensión anidada en clases."""
    
    def setup_method(self):
        """Setup para cada test."""
        self.factory = TestEntityFactory()
        self.metric = NestedComprehensionDepthMetric()
        self.assertions = AssertionHelpers()
    
    def test_empty_class(self):
        """Test clase sin métodos."""
        empty_class = Class(name="EmptyClass")
        empty_class.methods = []
        
        result = self.metric.calculate_class(empty_class)
        
        expected_keys = ["max_depth", "average_depth", "method_count", "methods_with_nested"]
        self.assertions.assert_metric_result_structure(result, expected_keys)
        
        assert result["max_depth"] == 0.0
        assert result["average_depth"] == 0.0
        assert result["method_count"] == 0.0
        assert result["methods_with_nested"] == 0.0
    
    def test_class_with_no_nested_comprehensions(self):
        """Test clase con métodos sin comprensiones anidadas."""
        code1 = """
def method1(self):
    return [x for x in range(10)]  # Nivel 1
"""
        code2 = """
def method2(self):
    return {x: x*2 for x in data}  # Nivel 1
"""
        code3 = """
def method3(self):
    return (x for x in items)  # Nivel 1
"""
        
        method1 = self.factory.create_function_from_code(code1, "method1")
        method2 = self.factory.create_function_from_code(code2, "method2") 
        method3 = self.factory.create_function_from_code(code3, "method3")
        
        cls = Class(name="NoNestedClass")
        cls.methods = [method1, method2, method3]
        
        result = self.metric.calculate_class(cls)
        
        expected_keys = ["max_depth", "average_depth", "method_count", "methods_with_nested"]
        self.assertions.assert_metric_result_structure(result, expected_keys)
        
        assert result["max_depth"] == 1.0  # Máximo nivel 1
        assert result["average_depth"] == 1.0  # Promedio nivel 1
        assert result["method_count"] == 3.0
        assert result["methods_with_nested"] == 0.0  # Ninguno con anidamiento > 1
    
    def test_class_with_nested_comprehensions(self):
        """Test clase con métodos que tienen comprensiones anidadas."""
        code1 = """
def simple_method(self):
    return [x for x in range(10)]  # Nivel 1
"""
        code2 = """
def nested_method(self):
    return [[x for x in row] for row in matrix]  # Nivel 2
"""
        code3 = """
def deeply_nested_method(self):
    return [[[[x for x in a] for a in b] for b in c] for c in data]  # Nivel 4
"""
        
        method1 = self.factory.create_function_from_code(code1, "simple_method")
        method2 = self.factory.create_function_from_code(code2, "nested_method")
        method3 = self.factory.create_function_from_code(code3, "deeply_nested_method")
        
        cls = Class(name="NestedClass")
        cls.methods = [method1, method2, method3]
        
        result = self.metric.calculate_class(cls)
        
        expected_keys = ["max_depth", "average_depth", "method_count", "methods_with_nested"]
        self.assertions.assert_metric_result_structure(result, expected_keys)
        
        assert result["max_depth"] == 4.0  # Máximo = 4
        assert result["average_depth"] == pytest.approx(2.33, abs=0.01)  # (1+2+4)/3
        assert result["method_count"] == 3.0
        assert result["methods_with_nested"] == 2.0  # Dos métodos > 1
    
    def test_class_all_methods_with_deep_nesting(self):
        """Test clase donde todos los métodos tienen anidamiento profundo."""
        code1 = """
def deep1(self):
    return [[[x for x in z] for z in y] for y in data]  # Nivel 3
"""
        code2 = """
def deep2(self):
    return {k: [v for v in values] for k, values in nested_dict.items()}  # Nivel 2
"""
        
        method1 = self.factory.create_function_from_code(code1, "deep1")
        method2 = self.factory.create_function_from_code(code2, "deep2")
        
        cls = Class(name="DeepNestedClass")
        cls.methods = [method1, method2]
        
        result = self.metric.calculate_class(cls)
        
        expected_keys = ["max_depth", "average_depth", "method_count", "methods_with_nested"]
        self.assertions.assert_metric_result_structure(result, expected_keys)
        
        assert result["max_depth"] == 3.0  # Máximo = 3
        assert result["average_depth"] == 2.5  # (3+2)/2
        assert result["method_count"] == 2.0
        assert result["methods_with_nested"] == 2.0  # Todos > 1
    
    def test_class_mixed_nesting_levels(self):
        """Test clase con métodos de diferentes niveles de anidamiento."""
        code1 = """
def none_method(self):
    return "no comprehensions"  # Nivel 0
"""
        code2 = """
def simple_method(self):
    return [x for x in range(10)]  # Nivel 1
"""
        code3 = """
def nested_method(self):
    list_comp = [[x for x in row] for row in matrix]  # Nivel 2
    set_comp = {x for x in data}  # Nivel 1
    return list_comp, set_comp  # Máximo = 2
"""
        code4 = """
def deep_method(self):
    return [[[[[x for x in a] for a in b] for b in c] for c in d] for d in data]  # Nivel 5
"""
        
        method1 = self.factory.create_function_from_code(code1, "none_method")
        method2 = self.factory.create_function_from_code(code2, "simple_method")
        method3 = self.factory.create_function_from_code(code3, "nested_method")
        method4 = self.factory.create_function_from_code(code4, "deep_method")
        
        cls = Class(name="MixedNestedClass")
        cls.methods = [method1, method2, method3, method4]
        
        result = self.metric.calculate_class(cls)
        
        expected_keys = ["max_depth", "average_depth", "method_count", "methods_with_nested"]
        self.assertions.assert_metric_result_structure(result, expected_keys)
        
        assert result["max_depth"] == 5.0  # Máximo = 5
        assert result["average_depth"] == 2.0  # (0+1+2+5)/4
        assert result["method_count"] == 4.0
        assert result["methods_with_nested"] == 2.0  # Dos métodos > 1 (nested=2, deep=5)


class TestNestedComprehensionDepthModulesAndProjects:
    """Tests para módulos y proyectos (que devuelven None)."""
    
    def setup_method(self):
        """Setup para cada test."""
        self.factory = TestEntityFactory()
        self.metric = NestedComprehensionDepthMetric()
    
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


class TestNestedComprehensionDepthEdgeCases:
    """Tests para casos extremos y edge cases."""
    
    def setup_method(self):
        """Setup para cada test."""
        self.factory = TestEntityFactory()
        self.metric = NestedComprehensionDepthMetric()
    
    def test_function_without_astroid_node(self):
        """Test función sin nodo astroid."""
        func = self.factory.create_simple_function("no_astroid")
        func.astroid_node = None  # Sin nodo astroid
        
        result = self.metric.calculate_function(func)
        
        assert result == 0.0  # Sin nodo AST
    
    def test_function_with_extreme_nesting_level(self):
        """Test función con nivel extremo de anidamiento."""
        code = """
def extreme_level():
    # Anidamiento extremo de 8 niveles
    result = [[[[[[[[x for x in h] for h in g] for g in f] for f in e] for e in d] for d in c] for c in b] for b in data]
    return result
"""
        func = self.factory.create_function_from_code(code, "extreme_level")
        
        result = self.metric.calculate_function(func)
        
        assert result == 8.0  # Nivel extremo
    
    def test_get_aggregated_value_function(self):
        """Test get_aggregated_value para función."""
        code = """
def test_func():
    result = [[[x for x in z] for z in y] for y in data]  # Nivel 3
    return result
"""
        func = self.factory.create_function_from_code(code, "test_func")
        
        aggregated = self.metric.get_aggregated_value(func)
        
        assert aggregated == 3.0
    
    def test_get_aggregated_value_class(self):
        """Test get_aggregated_value para clase."""
        code1 = """
def method1(self):
    return [[x for x in row] for row in matrix]  # Nivel 2
"""
        code2 = """
def method2(self):
    return [x for x in data]  # Nivel 1
"""
        code3 = """
def method3(self):
    return "no comprehensions"  # Nivel 0
"""
        
        method1 = self.factory.create_function_from_code(code1, "method1")
        method2 = self.factory.create_function_from_code(code2, "method2")
        method3 = self.factory.create_function_from_code(code3, "method3")
        
        cls = Class(name="TestClass")
        cls.methods = [method1, method2, method3]
        
        aggregated = self.metric.get_aggregated_value(cls)
        
        # Para clases, get_aggregated_value suma todos los valores del diccionario
        # max_depth=2.0, average_depth=1.0, method_count=3.0, methods_with_nested=1.0
        # Suma total = 2.0 + 1.0 + 3.0 + 1.0 = 7.0
        assert aggregated == 7.0
    
    def test_get_aggregated_value_module(self):
        """Test get_aggregated_value para módulo."""
        module = self.factory.create_module_with_entities("test_module")
        
        aggregated = self.metric.get_aggregated_value(module)
        
        # Para módulos, debe devolver 0.0 ya que calculate devuelve None
        assert aggregated == 0.0


class TestNestedComprehensionDepthIntegration:
    """Tests de integración para la métrica de Profundidad de Comprensión Anidada."""
    
    def setup_method(self):
        """Setup para cada test."""
        self.metric = NestedComprehensionDepthMetric()
        self.factory = TestEntityFactory()
    
    def test_thresholds_configuration(self):
        """Verifica que los umbrales están correctamente configurados."""
        thresholds = self.metric.get_thresholds()
        
        assert isinstance(thresholds, dict)
        assert "low" in thresholds
        assert "medium" in thresholds  
        assert "high" in thresholds
        assert thresholds["low"] < thresholds["medium"] < thresholds["high"]
    
    def test_realistic_function_analysis(self):
        """Test análisis de función realista."""
        code = """
def process_nested_data(matrix_data, filters):
    # Procesamiento con comprensiones anidadas nivel 3
    filtered_matrix = [
        [
            [cell for cell in row if cell > threshold]
            for row in submatrix if len(row) > min_length
        ]
        for submatrix in matrix_data if submatrix in filters
    ]
    
    # Comprensión simple nivel 1
    flattened = [item for sublist in filtered_matrix for item in sublist]
    
    return filtered_matrix, flattened
"""
        func = self.factory.create_function_from_code(code, "process_nested_data")
        
        result = self.metric.calculate_function(func)
        
        # Esperamos nivel 3 (máximo entre las comprensiones)
        assert result == 3.0
        
        # Verificar interpretación
        interpretation = self.metric.interpret(result)
        assert "alta" in interpretation.lower() or "elevada" in interpretation.lower()
    
    def test_class_statistics_consistency(self):
        """Test consistencia de estadísticas de clase."""
        code1 = """
def method_with_simple_comp(self):
    return [x for x in range(10)]  # Nivel 1
"""
        code2 = """
def method_with_nested_comp(self):
    return [[[x for x in z] for z in y] for y in data]  # Nivel 3
"""
        code3 = """
def method_without_comp(self):
    return [1, 2, 3, 4, 5]  # Nivel 0
"""
        
        method1 = self.factory.create_function_from_code(code1, "method_with_simple_comp")
        method2 = self.factory.create_function_from_code(code2, "method_with_nested_comp") 
        method3 = self.factory.create_function_from_code(code3, "method_without_comp")
        
        cls = Class(name="TestClass")
        cls.methods = [method1, method2, method3]
        
        result = self.metric.calculate_class(cls)
        
        # Verificar consistencia estadística
        assert result["method_count"] == 3.0
        assert result["methods_with_nested"] == 1.0  # Solo 1 método con nivel > 1
        assert result["max_depth"] == 3.0  # Máximo es del método más profundo
        assert result["average_depth"] == pytest.approx(1.33, abs=0.01)  # (1+3+0)/3


@pytest.mark.parametrize("code,expected_max_depth", [
    ("def f(): return [x for x in range(10)]", 1.0),  # Nivel 1
    ("def f(): return [[x for x in row] for row in matrix]", 2.0),  # Nivel 2
    ("def f(): return [[[x for x in z] for z in y] for y in data]", 3.0),  # Nivel 3
    ("def f(): return {k: [v for v in values] for k, values in data.items()}", 2.0),  # Nivel 2
    ("def f(): return [(x for x in row) for row in matrix]", 2.0),  # Nivel 2
    ("def f(): return x + y", 0.0),  # Sin comprensiones
])
def test_nested_comprehension_depth_calculation(code, expected_max_depth):
    """Test parametrizado para cálculo de profundidad de comprensión anidada."""
    factory = TestEntityFactory()
    metric = NestedComprehensionDepthMetric()
    
    func = factory.create_function_from_code(code, "f")
    result = metric.calculate_function(func)
    
    assert result == expected_max_depth


@pytest.mark.parametrize("method_codes,expected_stats", [
    # Caso 1: Métodos sin comprensiones anidadas
    ([
        "def m1(self): return 1",
        "def m2(self): return 2", 
        "def m3(self): return 3"
    ], {"max": 0.0, "avg": 0.0, "nested": 0}),
    
    # Caso 2: Un método con comprensión simple (nivel 1)
    ([
        "def m1(self): return [x for x in range(10)]",  # Nivel 1
        "def m2(self): return 2",  # Nivel 0
        "def m3(self): return 3"   # Nivel 0
    ], {"max": 1.0, "avg": 0.33, "nested": 0}),
    
    # Caso 3: Un método con anidamiento
    ([
        "def m1(self): return [x for x in range(10)]",  # Nivel 1
        "def m2(self): return [[x for x in row] for row in matrix]",  # Nivel 2
        "def m3(self): return [y for y in data]"  # Nivel 1
    ], {"max": 2.0, "avg": 1.33, "nested": 1}),
    
    # Caso 4: Todos los métodos con anidamiento profundo
    ([
        "def m1(self): return [[x for x in row] for row in matrix]",  # Nivel 2
        "def m2(self): return [[[x for x in z] for z in y] for y in data]",  # Nivel 3
        "def m3(self): return [[[[x for x in a] for a in b] for b in c] for c in d]"  # Nivel 4
    ], {"max": 4.0, "avg": 3.0, "nested": 3}),
])
def test_class_nested_comprehension_depth_aggregation(method_codes, expected_stats):
    """Test parametrizado para agregación de profundidad de comprensión anidada en clases."""
    factory = TestEntityFactory()
    metric = NestedComprehensionDepthMetric()
    
    methods = []
    for i, code in enumerate(method_codes):
        method = factory.create_function_from_code(code, f"m{i+1}")
        methods.append(method)
    
    cls = Class(name="TestClass")
    cls.methods = methods
    
    result = metric.calculate_class(cls)
    
    assert result["max_depth"] == expected_stats["max"]
    assert result["average_depth"] == pytest.approx(expected_stats["avg"], abs=0.01)
    assert result["methods_with_nested"] == expected_stats["nested"]


if __name__ == "__main__":
    pytest.main([__file__]) 