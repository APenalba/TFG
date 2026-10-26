"""Tests comprehensivos para la métrica LinesOfCodeMetric.

Este módulo contiene tests exhaustivos que cubren todos los aspectos
de la métrica de líneas de código, incluyendo edge cases.
"""

import pytest

from pypex.metrics.size.lines_of_code import LinesOfCodeMetric
from pypex.parser.code_entities import Class, Module, Project
from tests.unit.metrics.test_utils import AssertionHelpers, TestEntityFactory


class TestLinesOfCodeBasic:
    """Tests básicos para la métrica LinesOfCodeMetric."""

    def setup_method(self):
        """Setup para cada test."""
        self.factory = TestEntityFactory()
        self.assertions = AssertionHelpers()
        self.metric = LinesOfCodeMetric()

    def test_metric_properties(self):
        """Verifica las propiedades básicas de la métrica."""
        assert self.metric.name == "lines_of_code"
        assert "tamaño" in self.metric.description.lower()
        assert "líneas" in self.metric.description.lower()
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


class TestLinesOfCodeFunctions:
    """Tests para cálculo de LOC en funciones."""

    def setup_method(self):
        """Setup para cada test."""
        self.factory = TestEntityFactory()
        self.metric = LinesOfCodeMetric()

    def test_simple_function(self):
        """Test función simple."""
        func = self.factory.create_simple_function("test_func")
        func.source_lines_of_code = 10

        result = self.metric.calculate_function(func)

        assert result == 10.0
        assert isinstance(result, float)

    def test_function_zero_lines(self):
        """Test función con cero líneas."""
        func = self.factory.create_simple_function("empty_func")
        func.source_lines_of_code = 0

        result = self.metric.calculate_function(func)

        assert result == 0.0

    def test_function_large_lines(self):
        """Test función con muchas líneas."""
        func = self.factory.create_simple_function("large_func")
        func.source_lines_of_code = 500

        result = self.metric.calculate_function(func)

        assert result == 500.0

    def test_function_with_different_sloc_values(self):
        """Test funciones con diferentes valores de SLOC."""
        test_values = [1, 5, 10, 25, 50, 100, 200]

        for sloc_value in test_values:
            func = self.factory.create_simple_function(f"func_{sloc_value}")
            func.source_lines_of_code = sloc_value

            result = self.metric.calculate_function(func)

            assert result == float(sloc_value)
            assert isinstance(result, float)


class TestLinesOfCodeClasses:
    """Tests para cálculo de LOC en clases."""

    def setup_method(self):
        """Setup para cada test."""
        self.factory = TestEntityFactory()
        self.metric = LinesOfCodeMetric()
        self.assertions = AssertionHelpers()

    def test_empty_class(self):
        """Test clase sin métodos."""
        cls = Class(name="EmptyClass")
        cls.methods = []
        cls.line_start = 1
        cls.line_end = 5  # length será 5
        cls.source_lines_of_code = 2
        cls.docstring_sloc = 1
        cls.comment_sloc = 0
        cls.blank_lines_count = 2

        result = self.metric.calculate_class(cls)

        expected_keys = [
            "total_loc",
            "total_sloc",
            "class_sloc",
            "methods_sloc",
            "avg_method_sloc",
            "max_method_sloc",
            "documentation_lines",
            "comment_lines",
            "blank_lines",
            "documentation_ratio",
            "comment_ratio",
        ]
        self.assertions.assert_metric_result_structure(result, expected_keys)

        assert result["total_loc"] == 5.0
        assert result["total_sloc"] == 2.0  # Solo la clase
        assert result["class_sloc"] == 2.0
        assert result["methods_sloc"] == 0.0
        assert result["avg_method_sloc"] == 0.0
        assert result["max_method_sloc"] == 0.0
        assert result["documentation_lines"] == 1.0
        assert result["comment_lines"] == 0.0
        assert result["blank_lines"] == 2.0
        assert result["documentation_ratio"] == 0.5  # 1/2
        assert result["comment_ratio"] == 0.0

    def test_class_with_methods(self):
        """Test clase con métodos."""
        cls = self.factory.create_class_with_methods(
            class_name="TestClass", method_names=["method1", "method2", "method3"]
        )

        # Configurar métricas de la clase
        cls.line_start = 1
        cls.line_end = 50  # length será 50
        cls.source_lines_of_code = 10
        cls.docstring_sloc = 3
        cls.comment_sloc = 2
        cls.blank_lines_count = 5

        # Configurar métricas de los métodos
        cls.methods[0].source_lines_of_code = 8
        cls.methods[1].source_lines_of_code = 12
        cls.methods[2].source_lines_of_code = 6

        result = self.metric.calculate_class(cls)

        assert result["total_loc"] == 50.0
        assert result["total_sloc"] == 36.0  # 10 (clase) + 26 (métodos)
        assert result["class_sloc"] == 10.0
        assert result["methods_sloc"] == 26.0  # 8 + 12 + 6
        assert result["avg_method_sloc"] == 26.0 / 3  # Promedio
        assert result["max_method_sloc"] == 12.0  # Máximo
        assert result["documentation_lines"] == 3.0
        assert result["comment_lines"] == 2.0
        assert result["blank_lines"] == 5.0
        assert abs(result["documentation_ratio"] - (3.0 / 36.0)) < 0.001
        assert abs(result["comment_ratio"] - (2.0 / 36.0)) < 0.001

    def test_class_with_single_method(self):
        """Test clase con un solo método."""
        cls = self.factory.create_class_with_methods(
            class_name="SingleMethodClass", method_names=["single_method"]
        )

        cls.line_start = 1
        cls.line_end = 20  # length será 20
        cls.source_lines_of_code = 5
        cls.docstring_sloc = 2
        cls.comment_sloc = 1
        cls.blank_lines_count = 3

        cls.methods[0].source_lines_of_code = 10

        result = self.metric.calculate_class(cls)

        assert result["total_sloc"] == 15.0  # 5 + 10
        assert result["methods_sloc"] == 10.0
        assert result["avg_method_sloc"] == 10.0
        assert result["max_method_sloc"] == 10.0

    def test_class_zero_division_protection(self):
        """Test protección contra división por cero."""
        cls = Class(name="ZeroClass")
        cls.methods = []
        cls.line_start = 1
        cls.line_end = 1  # length será 1
        cls.source_lines_of_code = 0
        cls.docstring_sloc = 0
        cls.comment_sloc = 0
        cls.blank_lines_count = 0

        result = self.metric.calculate_class(cls)

        assert result["documentation_ratio"] == 0.0
        assert result["comment_ratio"] == 0.0
        assert result["avg_method_sloc"] == 0.0
        assert result["max_method_sloc"] == 0.0

    def test_class_with_varying_method_sizes(self):
        """Test clase con métodos de diferentes tamaños."""
        cls = self.factory.create_class_with_methods(
            class_name="VaryingSizeClass", method_names=["tiny", "small", "medium", "large", "huge"]
        )

        cls.line_start = 1
        cls.line_end = 200  # length será 200
        cls.source_lines_of_code = 20
        cls.docstring_sloc = 5
        cls.comment_sloc = 3
        cls.blank_lines_count = 10

        # Métodos de diferentes tamaños
        method_sizes = [2, 10, 25, 50, 100]
        for i, size in enumerate(method_sizes):
            cls.methods[i].source_lines_of_code = size

        result = self.metric.calculate_class(cls)

        total_methods_sloc = sum(method_sizes)  # 187
        assert result["methods_sloc"] == float(total_methods_sloc)
        assert result["avg_method_sloc"] == total_methods_sloc / 5
        assert result["max_method_sloc"] == 100.0
        assert result["total_sloc"] == 20.0 + total_methods_sloc


class TestLinesOfCodeModules:
    """Tests para cálculo de LOC en módulos."""

    def setup_method(self):
        """Setup para cada test."""
        self.factory = TestEntityFactory()
        self.metric = LinesOfCodeMetric()
        self.assertions = AssertionHelpers()

    def test_empty_module(self):
        """Test módulo vacío."""
        module = Module(name="empty_module")
        module.functions = []
        module.classes = []
        module.imports = []
        module.line_start = 1
        module.line_end = 10  # length será 10
        module.source_lines_of_code = 5
        module.docstring_sloc = 2
        module.comment_sloc = 1
        module.blank_lines_count = 2

        result = self.metric.calculate_module(module)

        expected_keys = [
            "total_loc",
            "total_sloc",
            "functions_sloc",
            "classes_sloc",
            "total_code_sloc",
            "avg_entity_sloc",
            "documentation_lines",
            "comment_lines",
            "blank_lines",
            "import_count",
            "import_density",
            "documentation_ratio",
            "comment_ratio",
            "entity_count",
        ]
        self.assertions.assert_metric_result_structure(result, expected_keys)

        assert result["total_loc"] == 10.0
        assert result["total_sloc"] == 5.0
        assert result["functions_sloc"] == 0.0
        assert result["classes_sloc"] == 0.0
        assert result["total_code_sloc"] == 0.0
        assert result["avg_entity_sloc"] == 0.0
        assert result["entity_count"] == 0.0
        assert result["import_count"] == 0.0
        assert result["import_density"] == 0.0

    def test_module_with_functions_only(self):
        """Test módulo solo con funciones."""
        module = self.factory.create_module_with_entities(
            module_name="func_module", function_count=3, class_count=0, import_count=2
        )

        # Configurar métricas del módulo
        module.line_start = 1
        module.line_end = 100  # length será 100
        module.source_lines_of_code = 80
        module.docstring_sloc = 10
        module.comment_sloc = 5
        module.blank_lines_count = 5

        # Configurar métricas de las funciones
        function_slocs = [15, 20, 25]
        for i, func in enumerate(module.functions):
            func.source_lines_of_code = function_slocs[i]

        result = self.metric.calculate_module(module)

        total_func_sloc = sum(function_slocs)  # 60
        assert result["functions_sloc"] == float(total_func_sloc)
        assert result["classes_sloc"] == 0.0
        assert result["total_code_sloc"] == float(total_func_sloc)
        assert result["avg_entity_sloc"] == total_func_sloc / 3
        assert result["entity_count"] == 3.0
        assert result["import_count"] == 2.0
        assert result["import_density"] == 2.0 / 100.0

    def test_module_with_classes_only(self):
        """Test módulo solo con clases."""
        module = self.factory.create_module_with_entities(
            module_name="class_module", function_count=0, class_count=2, import_count=3
        )

        module.line_start = 1
        module.line_end = 150  # length será 150
        module.source_lines_of_code = 120
        module.docstring_sloc = 15
        module.comment_sloc = 8
        module.blank_lines_count = 7

        # Configurar clases con métodos
        cls1 = module.classes[0]
        cls1.source_lines_of_code = 20
        cls1.methods = [self.factory.create_simple_function("method1")]
        cls1.methods[0].source_lines_of_code = 15

        cls2 = module.classes[1]
        cls2.source_lines_of_code = 25
        cls2.methods = [
            self.factory.create_simple_function("method2"),
            self.factory.create_simple_function("method3"),
        ]
        cls2.methods[0].source_lines_of_code = 10
        cls2.methods[1].source_lines_of_code = 12

        result = self.metric.calculate_module(module)

        total_class_sloc = 20 + 15 + 25 + 10 + 12  # 82
        assert result["functions_sloc"] == 0.0
        assert result["classes_sloc"] == float(total_class_sloc)
        assert result["total_code_sloc"] == float(total_class_sloc)
        assert result["avg_entity_sloc"] == total_class_sloc / 2
        assert result["entity_count"] == 2.0

    def test_module_mixed_entities(self):
        """Test módulo con funciones y clases."""
        module = self.factory.create_module_with_entities(
            module_name="mixed_module", function_count=2, class_count=2, import_count=5
        )

        module.line_start = 1
        module.line_end = 200  # length será 200
        module.source_lines_of_code = 160
        module.docstring_sloc = 20
        module.comment_sloc = 10
        module.blank_lines_count = 10

        # Configurar funciones
        module.functions[0].source_lines_of_code = 30
        module.functions[1].source_lines_of_code = 25

        # Configurar clases
        for i, cls in enumerate(module.classes):
            cls.source_lines_of_code = 15 + i * 5  # 15, 20
            cls.methods = [self.factory.create_simple_function(f"method_{i}")]
            cls.methods[0].source_lines_of_code = 10 + i * 3  # 10, 13

        result = self.metric.calculate_module(module)

        functions_sloc = 30 + 25  # 55
        classes_sloc = 15 + 10 + 20 + 13  # 58
        total_code_sloc = functions_sloc + classes_sloc  # 113

        assert result["functions_sloc"] == float(functions_sloc)
        assert result["classes_sloc"] == float(classes_sloc)
        assert result["total_code_sloc"] == float(total_code_sloc)
        assert result["avg_entity_sloc"] == total_code_sloc / 4
        assert result["entity_count"] == 4.0
        assert result["import_count"] == 5.0

    def test_module_zero_division_protection(self):
        """Test protección contra división por cero en módulos."""
        module = Module(name="zero_module")
        module.functions = []
        module.classes = []
        module.imports = []
        module.line_start = 1
        module.line_end = 1  # length será 1
        module.source_lines_of_code = 0
        module.docstring_sloc = 0
        module.comment_sloc = 0
        module.blank_lines_count = 0

        result = self.metric.calculate_module(module)

        assert result["avg_entity_sloc"] == 0.0
        assert result["import_density"] == 0.0
        assert result["documentation_ratio"] == 0.0
        assert result["comment_ratio"] == 0.0


class TestLinesOfCodeProjects:
    """Tests para cálculo de LOC en proyectos."""

    def setup_method(self):
        """Setup para cada test."""
        self.factory = TestEntityFactory()
        self.metric = LinesOfCodeMetric()
        self.assertions = AssertionHelpers()

    def test_empty_project(self):
        """Test proyecto vacío."""
        project = Project(name="empty_project")
        project.modules = []

        result = self.metric.calculate_project(project)

        expected_keys = [
            "total_loc",
            "total_sloc",
            "total_documentation_lines",
            "total_comment_lines",
            "total_blank_lines",
            "total_imports",
            "module_count",
            "total_entities",
            "avg_module_sloc",
            "avg_entity_sloc",
            "max_module_sloc",
            "documentation_ratio",
            "comment_ratio",
            "import_density",
        ]
        self.assertions.assert_metric_result_structure(result, expected_keys)

        assert result["module_count"] == 0.0
        assert result["total_entities"] == 0.0
        assert result["avg_module_sloc"] == 0.0
        assert result["avg_entity_sloc"] == 0.0
        assert result["max_module_sloc"] == 0.0

    def test_project_single_module(self):
        """Test proyecto con un solo módulo."""
        project = self.factory.create_project_with_modules(
            project_name="single_module_project", module_count=1
        )

        module = project.modules[0]
        module.line_start = 1
        module.line_end = 100  # length será 100
        module.source_lines_of_code = 80
        module.docstring_sloc = 10
        module.comment_sloc = 5
        module.blank_lines_count = 5

        # Agregar funciones al módulo
        func1 = self.factory.create_simple_function("func1")
        func1.source_lines_of_code = 20
        func2 = self.factory.create_simple_function("func2")
        func2.source_lines_of_code = 30
        module.functions = [func1, func2]

        # Agregar clase al módulo
        cls = self.factory.create_class_with_methods("TestClass", ["method1"])
        cls.source_lines_of_code = 15
        cls.methods[0].source_lines_of_code = 10
        module.classes = [cls]

        result = self.metric.calculate_project(project)

        assert result["module_count"] == 1.0
        assert result["total_loc"] == 100.0
        assert result["total_sloc"] == 80.0
        assert result["total_entities"] == 3.0  # 2 funciones + 1 clase
        assert result["avg_module_sloc"] == 80.0
        assert result["max_module_sloc"] == 80.0

        # Verificar agregación de entidades
        total_entity_sloc = 20 + 30 + (15 + 10)  # func1 + func2 + (clase + método)
        assert result["avg_entity_sloc"] == total_entity_sloc / 3

    def test_project_multiple_modules(self):
        """Test proyecto con múltiples módulos."""
        project = self.factory.create_project_with_modules(
            project_name="multi_module_project", module_count=3
        )

        # Configurar módulos con diferentes tamaños
        module_configs = [
            {"loc": 100, "sloc": 80, "dloc": 10, "cloc": 5, "blank": 5},
            {"loc": 150, "sloc": 120, "dloc": 15, "cloc": 8, "blank": 7},
            {"loc": 200, "sloc": 160, "dloc": 20, "cloc": 10, "blank": 10},
        ]

        total_functions = 0
        total_classes = 0

        for i, (module, config) in enumerate(zip(project.modules, module_configs)):
            module.line_start = 1
            module.line_end = config["loc"]  # length será config["loc"]
            module.source_lines_of_code = config["sloc"]
            module.docstring_sloc = config["dloc"]
            module.comment_sloc = config["cloc"]
            module.blank_lines_count = config["blank"]

            # Agregar funciones
            func_count = i + 1  # 1, 2, 3 funciones por módulo
            functions = []
            for j in range(func_count):
                func = self.factory.create_simple_function(f"func_{i}_{j}")
                func.source_lines_of_code = 10 + j * 5
                functions.append(func)
            module.functions = functions
            total_functions += func_count

            # Agregar clases
            if i > 0:  # Solo módulos 1 y 2 tienen clases
                cls = self.factory.create_class_with_methods(f"Class_{i}", [f"method_{i}"])
                cls.source_lines_of_code = 20
                cls.methods[0].source_lines_of_code = 15
                module.classes = [cls]
                total_classes += 1
            else:
                module.classes = []

        result = self.metric.calculate_project(project)

        assert result["module_count"] == 3.0
        assert result["total_loc"] == 450.0  # 100 + 150 + 200
        assert result["total_sloc"] == 360.0  # 80 + 120 + 160
        assert result["total_entities"] == float(total_functions + total_classes)
        assert result["avg_module_sloc"] == 360.0 / 3
        assert result["max_module_sloc"] == 160.0

        # Verificar ratios
        total_dloc = 10 + 15 + 20  # 45
        total_cloc = 5 + 8 + 10  # 23
        assert abs(result["documentation_ratio"] - (total_dloc / 360.0)) < 0.001
        assert abs(result["comment_ratio"] - (total_cloc / 360.0)) < 0.001

    def test_project_zero_division_protection(self):
        """Test protección contra división por cero en proyectos."""
        project = Project(name="zero_project")
        project.modules = []

        result = self.metric.calculate_project(project)

        assert result["avg_module_sloc"] == 0.0
        assert result["avg_entity_sloc"] == 0.0
        assert result["documentation_ratio"] == 0.0
        assert result["comment_ratio"] == 0.0
        assert result["import_density"] == 0.0


class TestLinesOfCodeEdgeCases:
    """Tests para casos extremos y edge cases."""

    def setup_method(self):
        """Setup para cada test."""
        self.factory = TestEntityFactory()
        self.metric = LinesOfCodeMetric()

    def test_calculate_method_delegation(self):
        """Test que el método calculate delega correctamente."""
        # Función
        func = self.factory.create_simple_function("test_func")
        func.source_lines_of_code = 25
        assert self.metric.calculate(func) == 25.0

        # Clase
        cls = self.factory.create_class_with_methods()
        cls.source_lines_of_code = 10
        for method in cls.methods:
            method.source_lines_of_code = 5
        result = self.metric.calculate(cls)
        assert result == 25.0  # 10 + 3*5

        # Módulo
        module = self.factory.create_module_with_entities("test_module")
        module.source_lines_of_code = 50
        result = self.metric.calculate(module)
        assert result == 50.0

        # Proyecto
        project = self.factory.create_project_with_modules("test_project")
        project.modules[0].source_lines_of_code = 100
        result = self.metric.calculate(project)
        assert result == 100.0

    def test_get_aggregated_value(self):
        """Test get_aggregated_value para diferentes entidades."""
        # Función
        func = self.factory.create_simple_function("test_func")
        func.source_lines_of_code = 30
        assert self.metric.get_aggregated_value(func) == 30.0

        # Clase
        cls = self.factory.create_class_with_methods()
        cls.source_lines_of_code = 15
        for method in cls.methods:
            method.source_lines_of_code = 8
        aggregated = self.metric.get_aggregated_value(cls)
        assert aggregated == 39.0  # 15 + 3*8

    def test_unsupported_entity_type(self):
        """Test con tipo de entidad no soportado."""

        # Crear un objeto mock que no es ningún tipo conocido
        class UnsupportedEntity:
            pass

        unsupported = UnsupportedEntity()
        result = self.metric.calculate(unsupported)
        assert result == 0.0

    def test_extreme_values(self):
        """Test con valores extremos."""
        # Función con muchas líneas
        func = self.factory.create_simple_function("huge_func")
        func.source_lines_of_code = 10000
        assert self.metric.calculate_function(func) == 10000.0

        # Clase con muchos métodos
        cls = self.factory.create_class_with_methods(
            method_names=[f"method_{i}" for i in range(100)]
        )
        cls.source_lines_of_code = 50
        for method in cls.methods:
            method.source_lines_of_code = 10

        result = self.metric.calculate_class(cls)
        assert result["methods_sloc"] == 1000.0  # 100 * 10
        assert result["total_sloc"] == 1050.0  # 50 + 1000
        assert result["avg_method_sloc"] == 10.0
        assert result["max_method_sloc"] == 10.0


class TestLinesOfCodeIntegration:
    """Tests de integración para la métrica LinesOfCodeMetric."""

    def setup_method(self):
        """Setup para cada test."""
        self.metric = LinesOfCodeMetric()
        self.factory = TestEntityFactory()

    def test_thresholds_configuration(self):
        """Verifica que los umbrales están correctamente configurados."""
        thresholds = self.metric.get_thresholds()

        assert isinstance(thresholds, dict)
        # Verificar que hay umbrales para diferentes niveles

    def test_interpretation_with_known_values(self):
        """Verifica interpretación con valores conocidos."""
        test_values = [10.0, 50.0, 100.0, 500.0, 1000.0]

        for value in test_values:
            interpretation = self.metric.interpret(value)
            assert isinstance(interpretation, str), (
                f"Interpretación debe ser string para valor {value}"
            )
            assert len(interpretation) > 0, (
                f"Interpretación no puede estar vacía para valor {value}"
            )

    def test_realistic_project_analysis(self):
        """Test con análisis de proyecto realista."""
        # Simular proyecto típico
        project = self.factory.create_project_with_modules(
            project_name="RealProject", module_count=5
        )

        # Configurar módulos con tamaños realistas
        realistic_sizes = [150, 300, 250, 400, 200]

        for i, (module, size) in enumerate(zip(project.modules, realistic_sizes)):
            module.line_start = 1
            module.line_end = size + 50  # Incluir espacios y comentarios
            module.source_lines_of_code = size
            module.docstring_sloc = size // 10  # 10% documentación
            module.comment_sloc = size // 20  # 5% comentarios
            module.blank_lines_count = size // 15  # ~7% líneas en blanco

            # Agregar funciones y clases realistas
            func_count = 2 + i
            for j in range(func_count):
                func = self.factory.create_simple_function(f"func_{i}_{j}")
                func.source_lines_of_code = 15 + j * 5
                module.functions.append(func)

            if i % 2 == 0:  # Algunos módulos tienen clases
                cls = self.factory.create_class_with_methods(
                    f"Service_{i}", [f"method_{k}" for k in range(3)]
                )
                cls.source_lines_of_code = 20
                for method in cls.methods:
                    method.source_lines_of_code = 12
                module.classes = [cls]

        result = self.metric.calculate_project(project)

        # Verificar que el resultado es razonable
        assert result["total_sloc"] == sum(realistic_sizes)
        assert result["module_count"] == 5.0
        assert result["total_entities"] > 0
        assert result["avg_module_sloc"] > 0
        assert 0 <= result["documentation_ratio"] <= 1
        assert 0 <= result["comment_ratio"] <= 1

        # Verificar interpretación
        interpretation = self.metric.interpret(result["total_sloc"])
        assert isinstance(interpretation, str)
        assert len(interpretation) > 0


@pytest.mark.parametrize(
    "sloc_value,expected_type",
    [
        (0, float),
        (1, float),
        (10, float),
        (100, float),
        (1000, float),
    ],
)
def test_function_sloc_parametrized(sloc_value, expected_type):
    """Test parametrizado para verificar cálculo de SLOC en funciones."""
    factory = TestEntityFactory()
    metric = LinesOfCodeMetric()

    func = factory.create_simple_function("test_func")
    func.source_lines_of_code = sloc_value

    result = metric.calculate_function(func)

    assert result == float(sloc_value)
    assert isinstance(result, expected_type)


@pytest.mark.parametrize(
    "class_sloc,method_slocs,expected_total",
    [
        (10, [5, 5, 5], 25),  # Clase + 3 métodos
        (0, [], 0),  # Clase vacía
        (20, [10], 30),  # Clase + 1 método
        (15, [8, 12, 6, 14], 55),  # Clase + 4 métodos
    ],
)
def test_class_sloc_aggregation_parametrized(class_sloc, method_slocs, expected_total):
    """Test parametrizado para verificar agregación de SLOC en clases."""
    factory = TestEntityFactory()
    metric = LinesOfCodeMetric()

    if method_slocs:
        method_names = [f"method_{i}" for i in range(len(method_slocs))]
        cls = factory.create_class_with_methods(method_names=method_names)
        for i, method in enumerate(cls.methods):
            method.source_lines_of_code = method_slocs[i]
    else:
        cls = Class(name="TestClass")
        cls.methods = []

    cls.line_start = 1
    cls.line_end = expected_total + 10  # Agregar overhead
    cls.source_lines_of_code = class_sloc
    cls.docstring_sloc = 0
    cls.comment_sloc = 0
    cls.blank_lines_count = 0

    result = metric.calculate_class(cls)

    assert result["total_sloc"] == float(expected_total)
    assert result["class_sloc"] == float(class_sloc)
    assert result["methods_sloc"] == float(sum(method_slocs))


if __name__ == "__main__":
    pytest.main([__file__])
