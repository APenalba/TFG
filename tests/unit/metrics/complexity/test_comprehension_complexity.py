"""Tests comprehensivos para la métrica de Complejidad de Comprensión.

Este módulo contiene tests exhaustivos que cubren todos los aspectos
de la métrica de complejidad de comprensión, incluyendo edge cases.
"""

import pytest

from pypex.metrics.complexity.comprehension_complexity import ComprehensionComplexityMetric
from pypex.parser.code_entities import Class
from tests.unit.metrics.test_utils import AssertionHelpers, TestEntityFactory


class TestComprehensionComplexityBasic:
    """Tests básicos para la métrica de Complejidad de Comprensión."""

    def setup_method(self):
        """Setup para cada test."""
        self.factory = TestEntityFactory()
        self.assertions = AssertionHelpers()
        self.metric = ComprehensionComplexityMetric()

    def test_metric_properties(self):
        """Verifica las propiedades básicas de la métrica."""
        assert self.metric.name == "comprehension_complexity"
        assert "comprensión" in self.metric.description.lower()
        assert "expresiones" in self.metric.description.lower()
        assert "condiciones" in self.metric.description.lower()
        assert len(self.metric.description) > 50  # Descripción detallada

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


class TestComprehensionComplexityFunctions:
    """Tests para cálculo de complejidad de comprensión en funciones."""

    def setup_method(self):
        """Setup para cada test."""
        self.factory = TestEntityFactory()
        self.metric = ComprehensionComplexityMetric()

    def test_function_no_comprehensions(self):
        """Test función sin comprensiones (complejidad = 0)."""
        code = """
def no_comp_func():
    x = 5
    y = 10
    return x + y
"""
        func = self.factory.create_function_from_code(code, "no_comp_func")

        result = self.metric.calculate_function(func)

        assert result == 0.0  # Sin comprensiones

    def test_function_simple_comprehension_no_conditions(self):
        """Test función con comprensión simple sin condiciones."""
        code = """
def simple_comp():
    result = [x for x in range(10)]
    return result
"""
        func = self.factory.create_function_from_code(code, "simple_comp")

        result = self.metric.calculate_function(func)

        assert result == 0.0  # Sin condiciones if

    def test_function_simple_comprehension_with_condition(self):
        """Test función con comprensión simple con una condición."""
        code = """
def simple_comp():
    result = [x for x in range(10) if x > 5]
    return result
"""
        func = self.factory.create_function_from_code(code, "simple_comp")

        result = self.metric.calculate_function(func)

        assert result == 1.0  # 1 condición

    def test_function_comprehension_multiple_conditions(self):
        """Test función con comprensión con múltiples condiciones."""
        code = """
def multi_cond_comp():
    result = [x for x in range(10) if x > 2 if x < 8 if x % 2 == 0]
    return result
"""
        func = self.factory.create_function_from_code(code, "multi_cond_comp")

        result = self.metric.calculate_function(func)

        assert result == 3.0  # 3 condiciones if

    def test_function_multiple_comprehensions(self):
        """Test función con múltiples comprensiones."""
        code = """
def multiple_comp():
    list_comp = [x for x in range(10) if x > 5]  # 1 condición
    dict_comp = {k: v for k, v in items.items() if k if v}  # 2 condiciones
    set_comp = {x for x in data if x}  # 1 condición
    return list_comp, dict_comp, set_comp
"""
        func = self.factory.create_function_from_code(code, "multiple_comp")

        result = self.metric.calculate_function(func)

        assert result == 4.0  # 1 + 2 + 1 = 4

    def test_function_nested_comprehensions(self):
        """Test función con comprensiones anidadas."""
        code = """
def nested_comp():
    result = [[x for x in row if x > 0] for row in matrix if len(row) > 2]
    return result
"""
        func = self.factory.create_function_from_code(code, "nested_comp")

        result = self.metric.calculate_function(func)

        assert result == 2.0  # 1 condición interna + 1 condición externa

    def test_function_generator_expression(self):
        """Test función con expresión generadora."""
        code = """
def gen_expr():
    result = (x*2 for x in range(10) if x % 2 == 0 if x > 2)
    return list(result)
"""
        func = self.factory.create_function_from_code(code, "gen_expr")

        result = self.metric.calculate_function(func)

        assert result == 2.0  # 2 condiciones if

    def test_function_dict_comprehension(self):
        """Test función con comprensión de diccionario."""
        code = """
def dict_comp():
    result = {k: v*2 for k, v in data.items() if v > 0 if k.startswith('a')}
    return result
"""
        func = self.factory.create_function_from_code(code, "dict_comp")

        result = self.metric.calculate_function(func)

        assert result == 2.0  # 2 condiciones if

    def test_function_set_comprehension(self):
        """Test función con comprensión de conjunto."""
        code = """
def set_comp():
    result = {x.upper() for x in words if len(x) > 3}
    return result
"""
        func = self.factory.create_function_from_code(code, "set_comp")

        result = self.metric.calculate_function(func)

        assert result == 1.0  # 1 condición if


class TestComprehensionComplexityClasses:
    """Tests para cálculo de complejidad de comprensión en clases."""

    def setup_method(self):
        """Setup para cada test."""
        self.factory = TestEntityFactory()
        self.metric = ComprehensionComplexityMetric()
        self.assertions = AssertionHelpers()

    def test_empty_class(self):
        """Test clase sin métodos."""
        empty_class = Class(name="EmptyClass")
        empty_class.methods = []

        result = self.metric.calculate_class(empty_class)

        expected_keys = ["average", "max", "method_count", "methods_with_comprehensions"]
        self.assertions.assert_metric_result_structure(result, expected_keys)

        assert result["average"] == 0.0
        assert result["max"] == 0.0
        assert result["method_count"] == 0.0
        assert result["methods_with_comprehensions"] == 0.0

    def test_class_with_no_comprehensions(self):
        """Test clase con métodos sin comprensiones."""
        code1 = """
def method1(self):
    x = 5
    return x + 1
"""
        code2 = """
def method2(self):
    return "hello world"
"""
        code3 = """
def method3(self):
    for i in range(10):
        print(i)
"""

        method1 = self.factory.create_function_from_code(code1, "method1")
        method2 = self.factory.create_function_from_code(code2, "method2")
        method3 = self.factory.create_function_from_code(code3, "method3")

        cls = Class(name="NoCompClass")
        cls.methods = [method1, method2, method3]

        result = self.metric.calculate_class(cls)

        expected_keys = ["average", "max", "method_count", "methods_with_comprehensions"]
        self.assertions.assert_metric_result_structure(result, expected_keys)

        assert result["average"] == 0.0
        assert result["max"] == 0.0
        assert result["method_count"] == 3.0
        assert result["methods_with_comprehensions"] == 0.0

    def test_class_with_comprehensions(self):
        """Test clase con métodos que tienen comprensiones."""
        code1 = """
def simple_method(self):
    return "no comprehensions"
"""
        code2 = """
def moderate_method(self):
    result = [x for x in range(10) if x > 5 if x < 8]  # 2 condiciones
    return result
"""
        code3 = """
def complex_method(self):
    list_comp = [x for x in data if x > 0 if x < 100 if x % 2 == 0]  # 3 condiciones
    dict_comp = {k: v for k, v in items.items() if k if v}  # 2 condiciones
    return list_comp, dict_comp
"""

        method1 = self.factory.create_function_from_code(code1, "simple_method")
        method2 = self.factory.create_function_from_code(code2, "moderate_method")
        method3 = self.factory.create_function_from_code(code3, "complex_method")

        cls = Class(name="CompClass")
        cls.methods = [method1, method2, method3]

        result = self.metric.calculate_class(cls)

        expected_keys = ["average", "max", "method_count", "methods_with_comprehensions"]
        self.assertions.assert_metric_result_structure(result, expected_keys)

        assert result["average"] == pytest.approx(2.33, abs=0.01)  # (0+2+5)/3
        assert result["max"] == 5.0
        assert result["method_count"] == 3.0
        assert result["methods_with_comprehensions"] == 2.0  # Dos métodos con comprensiones

    def test_class_all_methods_with_comprehensions(self):
        """Test clase donde todos los métodos tienen comprensiones."""
        code1 = """
def comp1(self):
    result = [x for x in data if x > 0]  # 1 condición
    return result
"""
        code2 = """
def comp2(self):
    result = {x for x in items if x if len(x) > 2 if x.startswith('a') if x.endswith('z')}  # 4 condiciones
    return result
"""

        method1 = self.factory.create_function_from_code(code1, "comp1")
        method2 = self.factory.create_function_from_code(code2, "comp2")

        cls = Class(name="AllCompClass")
        cls.methods = [method1, method2]

        result = self.metric.calculate_class(cls)

        expected_keys = ["average", "max", "method_count", "methods_with_comprehensions"]
        self.assertions.assert_metric_result_structure(result, expected_keys)

        assert result["average"] == 2.5  # (1+4)/2
        assert result["max"] == 4.0
        assert result["method_count"] == 2.0
        assert result["methods_with_comprehensions"] == 2.0  # Todos los métodos


class TestComprehensionComplexityModulesAndProjects:
    """Tests para módulos y proyectos (que devuelven None)."""

    def setup_method(self):
        """Setup para cada test."""
        self.factory = TestEntityFactory()
        self.metric = ComprehensionComplexityMetric()

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


class TestComprehensionComplexityEdgeCases:
    """Tests para casos extremos y edge cases."""

    def setup_method(self):
        """Setup para cada test."""
        self.factory = TestEntityFactory()
        self.metric = ComprehensionComplexityMetric()

    def test_function_without_astroid_node(self):
        """Test función sin nodo astroid."""
        func = self.factory.create_simple_function("no_astroid")
        # Función sin nodo astroid
        func.astroid_node = None

        result = self.metric.calculate_function(func)

        assert result == 0.0  # Sin nodo AST

    def test_function_with_high_condition_count(self):
        """Test función con comprensión de muchas condiciones."""
        code = """
def high_cond():
    result = [x for x in range(100)
              if x > 0 if x < 90 if x % 2 == 0 if x % 3 == 0 if x % 5 == 0
              if x not in excluded if x > min_val if x < max_val
              if check_validity(x) if x in allowed_set]  # 10 condiciones
    return result
"""
        func = self.factory.create_function_from_code(code, "high_cond")

        result = self.metric.calculate_function(func)

        assert result == 10.0  # 10 condiciones

    def test_get_aggregated_value_function(self):
        """Test get_aggregated_value para función."""
        code = """
def test_func():
    result = [x for x in data if x > 0 if x < 100 if x % 2 == 0]  # 3 condiciones
    return result
"""
        func = self.factory.create_function_from_code(code, "test_func")

        aggregated = self.metric.get_aggregated_value(func)

        assert aggregated == 3.0

    def test_get_aggregated_value_class(self):
        """Test get_aggregated_value para clase."""
        code1 = """
def method1(self):
    result = [x for x in data if x > 0 if x < 50]  # 2 condiciones
    return result
"""
        code2 = """
def method2(self):
    result = [x for x in items if x]  # 1 condición
    return result
"""
        code3 = """
def method3(self):
    return "no comprehensions"  # 0 condiciones
"""

        method1 = self.factory.create_function_from_code(code1, "method1")
        method2 = self.factory.create_function_from_code(code2, "method2")
        method3 = self.factory.create_function_from_code(code3, "method3")

        cls = Class(name="TestClass")
        cls.methods = [method1, method2, method3]

        aggregated = self.metric.get_aggregated_value(cls)

        # Para clases, get_aggregated_value suma todos los valores del diccionario
        # average=1.0, max=2.0, method_count=3.0, methods_with_comprehensions=2.0
        # Suma total = 1.0 + 2.0 + 3.0 + 2.0 = 8.0
        assert aggregated == 8.0

    def test_get_aggregated_value_module(self):
        """Test get_aggregated_value para módulo."""
        module = self.factory.create_module_with_entities("test_module")

        aggregated = self.metric.get_aggregated_value(module)

        # Para módulos, debe devolver 0.0 ya que calculate devuelve None
        assert aggregated == 0.0


class TestComprehensionComplexityIntegration:
    """Tests de integración para la métrica de Complejidad de Comprensión."""

    def setup_method(self):
        """Setup para cada test."""
        self.metric = ComprehensionComplexityMetric()
        self.factory = TestEntityFactory()

    def test_thresholds_configuration(self):
        """Verifica que los umbrales están correctamente configurados."""
        thresholds = self.metric.get_thresholds()

        assert isinstance(thresholds, dict)
        assert "low" in thresholds
        assert "medium" in thresholds
        assert "high" in thresholds
        assert thresholds["low"] < thresholds["medium"] < thresholds["high"]

    def test_interpretation_with_known_values(self):
        """Test interpretación con valores conocidos."""
        # Test diferentes niveles de complejidad
        assert "baja" in self.metric.interpret(1.0).lower()
        assert "media" in self.metric.interpret(3.0).lower()
        assert "alta" in self.metric.interpret(10.0).lower()

    def test_realistic_function_analysis(self):
        """Test análisis de función realista."""
        code = """
def process_data(data_list, filters):
    # Comprensión con múltiples condiciones
    filtered_data = [
        item for item in data_list
        if item['status'] == 'active'
        if item['value'] > 0
        if item['category'] in filters
    ]  # 3 condiciones

    # Comprensión de diccionario con condiciones
    result_dict = {
        item['id']: item['value']
        for item in filtered_data
        if item['id'] not in excluded_ids
        if item['value'] < max_value
    }  # 2 condiciones

    return result_dict
"""
        func = self.factory.create_function_from_code(code, "process_data")

        result = self.metric.calculate_function(func)

        # Esperamos 5 condiciones total (3 + 2)
        assert result == 5.0

        # Verificar interpretación - 5.0 cae en "Alta" según umbrales {low: 2.0, medium: 5.0, high: 8.0}
        interpretation = self.metric.interpret(result)
        assert "alta" in interpretation.lower()

    def test_class_statistics_consistency(self):
        """Test consistencia de estadísticas de clase."""
        code1 = """
def method_with_simple_comp(self):
    return [x for x in range(10) if x > 5]  # 1 condición
"""
        code2 = """
def method_with_complex_comp(self):
    return [x for x in data if x if len(x) > 2 if x.startswith('test')]  # 3 condiciones
"""
        code3 = """
def method_without_comp(self):
    return [1, 2, 3, 4, 5]  # 0 condiciones
"""

        method1 = self.factory.create_function_from_code(code1, "method_with_simple_comp")
        method2 = self.factory.create_function_from_code(code2, "method_with_complex_comp")
        method3 = self.factory.create_function_from_code(code3, "method_without_comp")

        cls = Class(name="TestClass")
        cls.methods = [method1, method2, method3]

        result = self.metric.calculate_class(cls)

        # Verificar consistencia estadística
        assert result["method_count"] == 3.0
        assert (
            result["methods_with_comprehensions"] == 2.0
        )  # Solo 2 métodos tienen comprensiones con condiciones
        assert result["max"] == 3.0  # Máximo es del método más complejo
        assert result["average"] == pytest.approx(1.33, abs=0.01)  # (1+3+0)/3


@pytest.mark.parametrize(
    "code,expected_complexity",
    [
        ("def f(): return [x for x in range(10)]", 0.0),  # Sin condiciones
        ("def f(): return [x for x in range(10) if x > 5]", 1.0),  # 1 condición
        ("def f(): return [x for x in range(10) if x > 5 if x < 8]", 2.0),  # 2 condiciones
        (
            "def f(): return [x for x in range(10) if x > 2 if x < 8 if x % 2 == 0]",
            3.0,
        ),  # 3 condiciones
        (
            "def f(): return [[x for x in row if x > 0] for row in matrix if len(row) > 2]",
            2.0,
        ),  # Anidada: 1+1
    ],
)
def test_comprehension_complexity_calculation(code, expected_complexity):
    """Test parametrizado para cálculo de complejidad de comprensión."""
    factory = TestEntityFactory()
    metric = ComprehensionComplexityMetric()

    func = factory.create_function_from_code(code, "f")
    result = metric.calculate_function(func)

    assert result == expected_complexity


@pytest.mark.parametrize(
    "method_codes,expected_stats",
    [
        # Caso 1: Métodos sin comprensiones
        (
            ["def m1(self): return 1", "def m2(self): return 2", "def m3(self): return 3"],
            {"avg": 0.0, "max": 0.0, "with_comp": 0},
        ),
        # Caso 2: Un método con comprensión simple
        (
            [
                "def m1(self): return [x for x in range(10) if x > 5]",  # 1 condición
                "def m2(self): return 2",  # 0 condiciones
                "def m3(self): return 3",  # 0 condiciones
            ],
            {"avg": 0.33, "max": 1.0, "with_comp": 1},
        ),
        # Caso 3: Todos los métodos con comprensiones
        (
            [
                "def m1(self): return [x for x in range(10) if x > 5 if x < 8]",  # 2 condiciones
                "def m2(self): return [x for x in data if x]",  # 1 condición
                "def m3(self): return [x for x in items if x > 0 if x < 100 if x % 2 == 0]",  # 3 condiciones
            ],
            {"avg": 2.0, "max": 3.0, "with_comp": 3},
        ),
    ],
)
def test_class_comprehension_complexity_aggregation(method_codes, expected_stats):
    """Test parametrizado para agregación de complejidad de comprensión en clases."""
    factory = TestEntityFactory()
    metric = ComprehensionComplexityMetric()

    methods = []
    for i, code in enumerate(method_codes):
        method = factory.create_function_from_code(code, f"m{i + 1}")
        methods.append(method)

    cls = Class(name="TestClass")
    cls.methods = methods

    result = metric.calculate_class(cls)

    assert result["average"] == pytest.approx(expected_stats["avg"], abs=0.01)
    assert result["max"] == expected_stats["max"]
    assert result["methods_with_comprehensions"] == expected_stats["with_comp"]


if __name__ == "__main__":
    pytest.main([__file__])
