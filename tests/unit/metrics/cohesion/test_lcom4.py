"""Tests comprehensivos para la métrica LCOM4.

Este módulo contiene tests exhaustivos que cubren todos los aspectos
de la métrica LCOM4 (Lack of Cohesion of Methods 4), incluyendo edge cases.
"""

import pytest

from pypex.metrics.cohesion.lcom4 import LCOM4
from pypex.parser.code_entities import Class, Function, Module
from tests.unit.metrics.test_utils import AssertionHelpers, TestEntityFactory


class TestLCOM4Basic:
    """Tests básicos para la métrica LCOM4."""

    def setup_method(self):
        """Setup para cada test."""
        self.factory = TestEntityFactory()
        self.assertions = AssertionHelpers()
        self.metric = LCOM4()

    def test_metric_properties(self):
        """Verifica las propiedades básicas de la métrica."""
        assert self.metric.name == "lcom4"
        assert "cohesión" in self.metric.description.lower()
        assert "métodos" in self.metric.description.lower()
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

    def test_get_default_thresholds(self):
        """Verifica que los umbrales por defecto están bien configurados."""
        thresholds = self.metric.get_default_thresholds()

        assert isinstance(thresholds, dict)
        assert "low" in thresholds
        assert "medium" in thresholds
        assert "high" in thresholds

        # Verificar que los umbrales tienen sentido para LCOM4
        assert thresholds["low"] == 1.0  # Excelente cohesión
        assert thresholds["medium"] == 2.0  # Buena cohesión
        assert thresholds["high"] == 4.0  # Cohesión moderada/pobre

        # Verificar orden lógico
        assert thresholds["low"] <= thresholds["medium"] <= thresholds["high"]


class TestLCOM4Functions:
    """Tests para funciones (que devuelven None)."""

    def setup_method(self):
        """Setup para cada test."""
        self.factory = TestEntityFactory()
        self.metric = LCOM4()

    def test_function_returns_none(self):
        """Test que funciones devuelven None."""
        func = self.factory.create_simple_function("test_func")

        result = self.metric.calculate_function(func)

        assert result is None  # No aplica a funciones

    def test_async_function_returns_none(self):
        """Test que funciones async también devuelven None."""
        func = self.factory.create_simple_function("async_func")
        func.is_async = True

        result = self.metric.calculate_function(func)

        assert result is None

    def test_function_with_complex_attributes(self):
        """Test función con atributos complejos devuelve None."""
        func = self.factory.create_simple_function("complex_func")
        func.accessed_instance_attributes = {"attr1", "attr2", "attr3"}
        func.calls = {"method1", "method2"}

        result = self.metric.calculate_function(func)

        assert result is None


class TestLCOM4Classes:
    """Tests para cálculo de LCOM4 en clases."""

    def setup_method(self):
        """Setup para cada test."""
        self.factory = TestEntityFactory()
        self.metric = LCOM4()
        self.assertions = AssertionHelpers()

    def test_empty_class(self):
        """Test clase sin métodos."""
        empty_class = Class(name="EmptyClass")
        empty_class.methods = []

        result = self.metric.calculate_class(empty_class)

        expected_keys = [
            "lcom4",
            "total_methods",
            "connected_components",
            "method_connections",
            "attribute_connections",
            "total",
        ]
        self.assertions.assert_metric_result_structure(result, expected_keys)

        assert result["lcom4"] == 0.0  # Sin métodos
        assert result["total_methods"] == 0
        assert result["connected_components"] == 0
        assert result["method_connections"] == 0.0
        assert result["attribute_connections"] == 0.0
        assert result["total"] == 0.0

    def test_single_method_class(self):
        """Test clase con un solo método."""
        cls = Class(name="SingleMethodClass")
        method = self.factory.create_simple_function("single_method")
        method.accessed_instance_attributes = {"attr1"}
        cls.methods = [method]

        result = self.metric.calculate_class(cls)

        assert result["lcom4"] == 1.0  # Cohesión perfecta
        assert result["total_methods"] == 1
        assert result["connected_components"] == 1
        assert result["method_connections"] == 0.0  # Sin llamadas internas
        assert result["attribute_connections"] == 0.0  # Solo un método

    def test_perfectly_cohesive_class(self):
        """Test clase perfectamente cohesiva (todos los métodos conectados)."""
        cls = self.factory.create_class_with_methods(
            class_name="CohesiveClass", method_names=["method1", "method2", "method3"]
        )

        # Todos los métodos acceden al mismo atributo
        for method in cls.methods:
            method.accessed_instance_attributes = {"shared_attr"}

        result = self.metric.calculate_class(cls)

        assert result["lcom4"] == 1.0  # Un solo componente conectado
        assert result["total_methods"] == 3
        assert result["connected_components"] == 1
        assert result["attribute_connections"] > 0.0  # Conexiones por atributos

    def test_completely_uncohesive_class(self):
        """Test clase completamente no cohesiva (métodos aislados)."""
        cls = self.factory.create_class_with_methods(
            class_name="UncohesiveClass", method_names=["method1", "method2", "method3"]
        )

        # Cada método accede a un atributo diferente
        cls.methods[0].accessed_instance_attributes = {"attr1"}
        cls.methods[1].accessed_instance_attributes = {"attr2"}
        cls.methods[2].accessed_instance_attributes = {"attr3"}

        # Sin llamadas entre métodos
        for method in cls.methods:
            method.calls = set()

        result = self.metric.calculate_class(cls)

        assert result["lcom4"] == 3.0  # Tres componentes separados
        assert result["total_methods"] == 3
        assert result["connected_components"] == 3
        assert result["method_connections"] == 0.0  # Sin llamadas
        assert result["attribute_connections"] == 0.0  # Sin atributos compartidos

    def test_class_with_method_calls(self):
        """Test clase con conexiones por llamadas entre métodos."""
        cls = self.factory.create_class_with_methods(
            class_name="MethodCallClass", method_names=["method1", "method2", "method3"]
        )

        # method1 llama a method2
        cls.methods[0].calls = {"self.method2"}
        cls.methods[1].calls = set()
        cls.methods[2].calls = set()

        # Sin atributos compartidos
        cls.methods[0].accessed_instance_attributes = {"attr1"}
        cls.methods[1].accessed_instance_attributes = {"attr2"}
        cls.methods[2].accessed_instance_attributes = {"attr3"}

        result = self.metric.calculate_class(cls)

        assert result["lcom4"] == 2.0  # method1-method2 conectados, method3 aislado
        assert result["connected_components"] == 2
        assert result["method_connections"] == 1.0  # Una llamada
        assert result["attribute_connections"] == 0.0  # Sin atributos compartidos

    def test_class_with_shared_attributes(self):
        """Test clase con conexiones por atributos compartidos."""
        cls = self.factory.create_class_with_methods(
            class_name="SharedAttrClass", method_names=["method1", "method2", "method3", "method4"]
        )

        # method1 y method2 comparten attr1
        cls.methods[0].accessed_instance_attributes = {"attr1"}
        cls.methods[1].accessed_instance_attributes = {"attr1"}

        # method3 y method4 comparten attr2
        cls.methods[2].accessed_instance_attributes = {"attr2"}
        cls.methods[3].accessed_instance_attributes = {"attr2"}

        # Sin llamadas entre métodos
        for method in cls.methods:
            method.calls = set()

        result = self.metric.calculate_class(cls)

        assert result["lcom4"] == 2.0  # Dos grupos conectados
        assert result["connected_components"] == 2
        assert result["method_connections"] == 0.0  # Sin llamadas
        assert result["attribute_connections"] == 2.0  # Dos pares de conexiones

    def test_class_mixed_connections(self):
        """Test clase con conexiones mixtas (atributos + llamadas)."""
        cls = self.factory.create_class_with_methods(
            class_name="MixedConnectionsClass",
            method_names=["method1", "method2", "method3", "method4"],
        )

        # method1 y method2 comparten atributo
        cls.methods[0].accessed_instance_attributes = {"shared_attr"}
        cls.methods[1].accessed_instance_attributes = {"shared_attr"}

        # method3 llama a method1 (conecta con el primer grupo)
        cls.methods[2].calls = {"self.method1"}
        cls.methods[2].accessed_instance_attributes = {"unique_attr"}

        # method4 está aislado
        cls.methods[3].accessed_instance_attributes = {"isolated_attr"}
        cls.methods[3].calls = set()

        result = self.metric.calculate_class(cls)

        assert result["lcom4"] == 2.0  # method1-2-3 conectados, method4 aislado
        assert result["connected_components"] == 2
        assert result["method_connections"] == 1.0  # Una llamada
        assert result["attribute_connections"] == 1.0  # Un par compartido

    def test_class_complex_connections(self):
        """Test clase con conexiones complejas."""
        cls = self.factory.create_class_with_methods(
            class_name="ComplexClass", method_names=["init", "process", "validate", "save", "log"]
        )

        # Configurar conexiones realistas
        cls.methods[0].accessed_instance_attributes = {"data", "config"}  # init
        cls.methods[1].accessed_instance_attributes = {"data"}  # process
        cls.methods[1].calls = {"self.validate"}

        cls.methods[2].accessed_instance_attributes = {"config"}  # validate
        cls.methods[2].calls = set()

        cls.methods[3].accessed_instance_attributes = {"data"}  # save
        cls.methods[3].calls = {"self.log"}

        cls.methods[4].accessed_instance_attributes = set()  # log (aislado)
        cls.methods[4].calls = set()

        result = self.metric.calculate_class(cls)

        # init-process-validate-save conectados por atributos y llamadas
        # log conectado a save por llamada
        assert result["lcom4"] == 1.0  # Todos conectados
        assert result["connected_components"] == 1
        assert result["method_connections"] == 2.0  # process->validate, save->log
        assert result["attribute_connections"] > 0.0  # Múltiples conexiones por atributos

    def test_class_with_no_attributes_or_calls(self):
        """Test clase donde los métodos no tienen atributos ni llamadas."""
        cls = self.factory.create_class_with_methods(
            class_name="IsolatedClass", method_names=["method1", "method2", "method3"]
        )

        # Métodos completamente aislados
        for method in cls.methods:
            method.accessed_instance_attributes = set()
            method.calls = set()

        result = self.metric.calculate_class(cls)

        assert result["lcom4"] == 3.0  # Completamente desconectados
        assert result["connected_components"] == 3
        assert result["method_connections"] == 0.0
        assert result["attribute_connections"] == 0.0

    def test_class_with_large_number_of_methods(self):
        """Test clase con muchos métodos para verificar escalabilidad."""
        method_names = [f"method_{i}" for i in range(10)]
        cls = self.factory.create_class_with_methods(
            class_name="LargeClass", method_names=method_names
        )

        # Todos comparten el mismo atributo (perfectamente cohesiva)
        for method in cls.methods:
            method.accessed_instance_attributes = {"shared_attr"}
            method.calls = set()

        result = self.metric.calculate_class(cls)

        assert result["lcom4"] == 1.0  # Perfectamente cohesiva
        assert result["total_methods"] == 10
        assert result["connected_components"] == 1


class TestLCOM4ModulesAndProjects:
    """Tests para módulos y proyectos (que devuelven None)."""

    def setup_method(self):
        """Setup para cada test."""
        self.factory = TestEntityFactory()
        self.metric = LCOM4()

    def test_module_returns_none(self):
        """Test que módulos devuelven None."""
        module = self.factory.create_module_with_entities("test_module")

        result = self.metric.calculate_module(module)

        assert result is None  # No aplica a módulos

    def test_project_returns_none(self):
        """Test que proyectos devuelven None."""
        project = self.factory.create_project_with_modules("test_project")

        result = self.metric.calculate_project(project)

        assert result is None  # No aplica a proyectos

    def test_empty_module_returns_none(self):
        """Test que módulos vacíos también devuelven None."""
        module = Module(name="empty_module")
        module.functions = []
        module.classes = []

        result = self.metric.calculate_module(module)

        assert result is None

    def test_complex_module_returns_none(self):
        """Test que módulos complejos devuelven None."""
        module = self.factory.create_module_with_entities(
            "complex_module", function_count=10, class_count=5
        )

        result = self.metric.calculate_module(module)

        assert result is None


class TestLCOM4EdgeCases:
    """Tests para casos extremos y edge cases."""

    def setup_method(self):
        """Setup para cada test."""
        self.factory = TestEntityFactory()
        self.metric = LCOM4()

    def test_methods_without_attributes_or_calls(self):
        """Test métodos sin atributos ni llamadas."""
        cls = self.factory.create_class_with_methods(
            class_name="IsolatedMethodsClass", method_names=["method1", "method2"]
        )

        # Métodos sin atributos ni llamadas
        for method in cls.methods:
            method.accessed_instance_attributes = set()
            method.calls = set()

        result = self.metric.calculate_class(cls)

        assert result["lcom4"] == 2.0  # Completamente desconectados
        assert result["connected_components"] == 2
        assert result["method_connections"] == 0.0
        assert result["attribute_connections"] == 0.0

    def test_self_calling_methods(self):
        """Test métodos que se llaman a sí mismos."""
        cls = self.factory.create_class_with_methods(
            class_name="SelfCallingClass", method_names=["recursive_method", "other_method"]
        )

        # Método que se llama a sí mismo (no debe crear conexión)
        cls.methods[0].calls = {"self.recursive_method"}
        cls.methods[0].accessed_instance_attributes = {"attr1"}

        cls.methods[1].accessed_instance_attributes = {"attr2"}
        cls.methods[1].calls = set()

        result = self.metric.calculate_class(cls)

        assert result["lcom4"] == 2.0  # Sin conexión entre métodos
        assert result["method_connections"] == 0.0  # Llamada a sí mismo no cuenta

    def test_external_method_calls(self):
        """Test llamadas a métodos externos (no deben crear conexiones)."""
        cls = self.factory.create_class_with_methods(
            class_name="ExternalCallsClass", method_names=["method1", "method2"]
        )

        # Llamadas a métodos externos
        cls.methods[0].calls = {"external.method", "utils.helper"}
        cls.methods[1].calls = {"another.function"}

        # Sin atributos compartidos
        cls.methods[0].accessed_instance_attributes = {"attr1"}
        cls.methods[1].accessed_instance_attributes = {"attr2"}

        result = self.metric.calculate_class(cls)

        assert result["lcom4"] == 2.0  # Sin conexiones internas
        assert result["method_connections"] == 0.0  # Llamadas externas no cuentan

    def test_complex_method_call_patterns(self):
        """Test patrones complejos de llamadas de métodos."""
        cls = self.factory.create_class_with_methods(
            class_name="ComplexCallsClass", method_names=["method1", "method2", "method3"]
        )

        # Llamadas con diferentes formatos
        cls.methods[0].calls = {"self.method2", "method3"}  # Diferentes formatos
        cls.methods[1].calls = {"self.method3"}
        cls.methods[2].calls = set()

        # Sin atributos para aislar el efecto de las llamadas
        for method in cls.methods:
            method.accessed_instance_attributes = set()

        result = self.metric.calculate_class(cls)

        assert result["lcom4"] == 1.0  # Todos conectados por llamadas
        assert result["connected_components"] == 1
        assert result["method_connections"] == 3.0  # Tres llamadas internas

    def test_get_aggregated_value_different_entities(self):
        """Test get_aggregated_value para diferentes tipos de entidades."""
        # Función
        func = self.factory.create_simple_function("test_func")
        assert self.metric.get_aggregated_value(func) == 0.0

        # Clase cohesiva
        cls = self.factory.create_class_with_methods()
        for method in cls.methods:
            method.accessed_instance_attributes = {"shared_attr"}
        aggregated_class = self.metric.get_aggregated_value(cls)
        assert aggregated_class == 1.0  # Perfectamente cohesiva

        # Módulo
        module = self.factory.create_module_with_entities("test_module")
        assert self.metric.get_aggregated_value(module) == 0.0

        # Proyecto - usar calculate_project directamente ya que get_aggregated_value
        # no funciona con proyectos debido a la validación en BaseMetric
        project = self.factory.create_project_with_modules("test_project")
        project_result = self.metric.calculate_project(project)
        assert project_result is None  # LCOM4 no aplica a proyectos

    def test_extract_method_name_edge_cases(self):
        """Test extracción de nombres de métodos con casos extremos."""
        # Acceder al método privado para testing
        extract_method = self.metric._extract_method_name

        assert extract_method("self.method_name") == "method_name"
        assert extract_method("method_name") == "method_name"
        assert extract_method("obj.method_name") == "method_name"
        assert extract_method("module.class.method") == "method"
        assert extract_method("") == ""
        assert extract_method("simple") == "simple"

    def test_class_with_none_attributes(self):
        """Test clase donde accessed_instance_attributes es None."""
        cls = self.factory.create_class_with_methods(
            class_name="NoneAttributesClass", method_names=["method1", "method2"]
        )

        # Establecer accessed_instance_attributes como None
        for method in cls.methods:
            method.accessed_instance_attributes = None
            method.calls = set()

        result = self.metric.calculate_class(cls)

        assert result["lcom4"] == 2.0  # Sin conexiones
        assert result["connected_components"] == 2

    def test_circular_method_calls(self):
        """Test métodos que se llaman circularmente."""
        cls = self.factory.create_class_with_methods(
            class_name="CircularCallsClass", method_names=["method1", "method2", "method3"]
        )

        # Crear llamadas circulares
        cls.methods[0].calls = {"self.method2"}
        cls.methods[1].calls = {"self.method3"}
        cls.methods[2].calls = {"self.method1"}

        # Sin atributos compartidos
        for method in cls.methods:
            method.accessed_instance_attributes = set()

        result = self.metric.calculate_class(cls)

        assert result["lcom4"] == 1.0  # Todos conectados en círculo
        assert result["connected_components"] == 1
        assert result["method_connections"] == 3.0

    def test_multiple_shared_attributes(self):
        """Test métodos que comparten múltiples atributos."""
        cls = self.factory.create_class_with_methods(
            class_name="MultipleSharedClass", method_names=["method1", "method2"]
        )

        # Ambos métodos comparten múltiples atributos
        cls.methods[0].accessed_instance_attributes = {"attr1", "attr2", "attr3"}
        cls.methods[1].accessed_instance_attributes = {"attr1", "attr2", "attr4"}

        for method in cls.methods:
            method.calls = set()

        result = self.metric.calculate_class(cls)

        assert result["lcom4"] == 1.0  # Conectados por múltiples atributos
        assert result["connected_components"] == 1


class TestLCOM4HelperMethods:
    """Tests para métodos auxiliares de LCOM4."""

    def setup_method(self):
        """Setup para cada test."""
        self.factory = TestEntityFactory()
        self.metric = LCOM4()

    def test_interpret_cohesion_level(self):
        """Test interpretación de niveles de cohesión."""
        assert self.metric.interpret_cohesion_level(1.0) == "Excelente"
        assert self.metric.interpret_cohesion_level(2.0) == "Buena"
        assert self.metric.interpret_cohesion_level(3.0) == "Moderada"
        assert self.metric.interpret_cohesion_level(4.0) == "Pobre"
        assert self.metric.interpret_cohesion_level(5.0) == "Pobre"

    def test_interpret_cohesion_level_edge_values(self):
        """Test interpretación con valores límite."""
        assert self.metric.interpret_cohesion_level(0.0) == "Excelente"
        assert self.metric.interpret_cohesion_level(0.5) == "Excelente"
        assert self.metric.interpret_cohesion_level(1.0) == "Excelente"
        assert self.metric.interpret_cohesion_level(1.5) == "Buena"
        assert self.metric.interpret_cohesion_level(2.5) == "Moderada"
        assert self.metric.interpret_cohesion_level(10.0) == "Pobre"

    def test_get_cohesion_analysis(self):
        """Test análisis detallado de cohesión."""
        cls = self.factory.create_class_with_methods(
            class_name="AnalysisClass", method_names=["method1", "method2", "method3"]
        )

        # Configurar clase moderadamente cohesiva
        cls.methods[0].accessed_instance_attributes = {"attr1"}
        cls.methods[1].accessed_instance_attributes = {"attr1"}
        cls.methods[2].accessed_instance_attributes = {"attr2"}

        analysis = self.metric.get_cohesion_analysis(cls)

        expected_keys = [
            "lcom4_value",
            "interpretation",
            "total_methods",
            "connected_groups",
            "method_calls",
            "shared_attributes",
            "needs_refactoring",
            "refactoring_priority",
        ]

        for key in expected_keys:
            assert key in analysis, f"Falta clave {key} en análisis"

        assert analysis["lcom4_value"] == 2.0
        assert analysis["interpretation"] == "Buena"
        assert analysis["total_methods"] == 3
        assert analysis["connected_groups"] == 2
        assert isinstance(analysis["needs_refactoring"], bool)
        assert analysis["refactoring_priority"] in ["Low", "Medium", "High"]

    def test_get_cohesion_analysis_edge_cases(self):
        """Test análisis de cohesión con casos extremos."""
        # Clase perfectamente cohesiva
        cls_perfect = self.factory.create_class_with_methods(method_names=["m1", "m2"])
        for method in cls_perfect.methods:
            method.accessed_instance_attributes = {"shared"}

        analysis_perfect = self.metric.get_cohesion_analysis(cls_perfect)
        assert analysis_perfect["needs_refactoring"] is False
        assert analysis_perfect["refactoring_priority"] == "Low"

        # Clase con pobre cohesión
        cls_poor = self.factory.create_class_with_methods(
            method_names=["m1", "m2", "m3", "m4", "m5"]
        )
        for i, method in enumerate(cls_poor.methods):
            method.accessed_instance_attributes = {f"attr_{i}"}
            method.calls = set()

        analysis_poor = self.metric.get_cohesion_analysis(cls_poor)
        assert analysis_poor["needs_refactoring"] is True
        assert analysis_poor["refactoring_priority"] == "High"


class TestLCOM4Integration:
    """Tests de integración para la métrica LCOM4."""

    def setup_method(self):
        """Setup para cada test."""
        self.metric = LCOM4()
        self.factory = TestEntityFactory()

    def test_thresholds_configuration(self):
        """Verifica que los umbrales están correctamente configurados."""
        thresholds = self.metric.get_thresholds()

        assert isinstance(thresholds, dict)
        # Verificar que hay umbrales para diferentes niveles

    def test_interpretation_with_known_values(self):
        """Verifica interpretación con valores conocidos."""
        test_values = [1.0, 2.0, 3.0, 4.0, 5.0]

        for value in test_values:
            interpretation = self.metric.interpret(value)
            assert isinstance(interpretation, str), (
                f"Interpretación debe ser string para valor {value}"
            )
            assert len(interpretation) > 0, (
                f"Interpretación no puede estar vacía para valor {value}"
            )

    def test_realistic_class_analysis(self):
        """Test con análisis de clase realista."""
        # Simular clase de servicio típica
        cls = self.factory.create_class_with_methods(
            class_name="UserService",
            method_names=["__init__", "get_user", "update_user", "validate_user", "log_action"],
        )

        # Configurar conexiones realistas
        cls.methods[0].accessed_instance_attributes = {"db", "logger"}  # __init__
        cls.methods[1].accessed_instance_attributes = {"db"}  # get_user
        cls.methods[2].accessed_instance_attributes = {"db"}  # update_user
        cls.methods[2].calls = {"self.validate_user", "self.log_action"}
        cls.methods[3].accessed_instance_attributes = set()  # validate_user
        cls.methods[4].accessed_instance_attributes = {"logger"}  # log_action

        result = self.metric.calculate_class(cls)

        # Verificar que el resultado es razonable
        assert result["lcom4"] >= 1.0
        assert result["total_methods"] == 5
        assert result["connected_components"] >= 1

        # Verificar interpretación
        interpretation = self.metric.interpret(result["lcom4"])
        assert isinstance(interpretation, str)
        assert len(interpretation) > 0

    def test_calculate_polymorphic_dispatch(self):
        """Test que el método calculate hace dispatch correcto."""
        # Para función
        func = self.factory.create_simple_function("test_func")
        func_result = self.metric.calculate(func)
        assert func_result is None

        # Para clase
        cls = self.factory.create_class_with_methods()
        for method in cls.methods:
            method.accessed_instance_attributes = {"shared"}
        cls_result = self.metric.calculate(cls)
        assert isinstance(cls_result, dict)
        assert "lcom4" in cls_result

        # Para módulo
        module = self.factory.create_module_with_entities("test")
        module_result = self.metric.calculate(module)
        assert module_result is None

        # Para proyecto - el método calculate genérico lanza excepción
        # pero calculate_project específico devuelve None
        project = self.factory.create_project_with_modules("test")

        # Verificar que calculate genérico lanza excepción
        from pypex.metrics.base import InvalidEntityError

        with pytest.raises(InvalidEntityError):
            self.metric.calculate(project)

        # Verificar que calculate_project específico funciona
        project_result = self.metric.calculate_project(project)
        assert project_result is None


class TestLCOM4ErrorHandling:
    """Tests para manejo de errores y casos especiales."""

    def setup_method(self):
        """Setup para cada test."""
        self.metric = LCOM4()
        self.factory = TestEntityFactory()

    def test_class_with_malformed_calls(self):
        """Test clase con llamadas mal formadas."""
        cls = self.factory.create_class_with_methods(method_names=["m1", "m2"])

        # Llamadas mal formadas
        cls.methods[0].calls = {"", "...", "self.", ".method"}
        cls.methods[1].calls = set()

        # No debería fallar
        result = self.metric.calculate_class(cls)
        assert isinstance(result, dict)
        assert "lcom4" in result

    def test_class_with_empty_method_names(self):
        """Test clase con nombres de métodos vacíos."""
        cls = Class(name="EmptyNamesClass")
        method1 = Function(name="")
        method2 = Function(name="valid_method")

        method1.accessed_instance_attributes = {"attr1"}
        method2.accessed_instance_attributes = {"attr1"}
        method1.calls = set()
        method2.calls = set()

        cls.methods = [method1, method2]

        result = self.metric.calculate_class(cls)
        assert isinstance(result, dict)
        assert result["total_methods"] == 2

    def test_class_with_missing_attributes(self):
        """Test clase donde algunos métodos no tienen accessed_instance_attributes."""
        cls = self.factory.create_class_with_methods(method_names=["m1", "m2"])

        # Remover el atributo de uno de los métodos
        delattr(cls.methods[0], "accessed_instance_attributes")
        cls.methods[1].accessed_instance_attributes = {"attr1"}

        # No debería fallar
        result = self.metric.calculate_class(cls)
        assert isinstance(result, dict)


class TestLCOM4Performance:
    """Tests de rendimiento para LCOM4."""

    def setup_method(self):
        """Setup para cada test."""
        self.metric = LCOM4()
        self.factory = TestEntityFactory()

    def test_large_class_performance(self):
        """Test rendimiento con clase grande."""
        import time

        # Crear clase con muchos métodos
        method_names = [f"method_{i}" for i in range(50)]
        cls = self.factory.create_class_with_methods(
            class_name="LargeClass", method_names=method_names
        )

        # Configurar para máxima conectividad (peor caso para el algoritmo)
        for method in cls.methods:
            method.accessed_instance_attributes = {"shared_attr"}

        start_time = time.time()
        result = self.metric.calculate_class(cls)
        end_time = time.time()

        # El cálculo debe completarse en tiempo razonable (< 1 segundo)
        assert (end_time - start_time) < 1.0
        assert result["lcom4"] == 1.0  # Perfectamente cohesiva
        assert result["total_methods"] == 50


@pytest.mark.parametrize(
    "method_count,shared_attrs,expected_lcom4",
    [
        (0, [], 0.0),  # Sin métodos
        (1, ["attr1"], 1.0),  # Un método
        (2, ["attr1", "attr1"], 1.0),  # Dos métodos, atributo compartido
        (2, ["attr1", "attr2"], 2.0),  # Dos métodos, atributos diferentes
        (3, ["attr1", "attr1", "attr1"], 1.0),  # Tres métodos, todos comparten
        (3, ["attr1", "attr1", "attr2"], 2.0),  # Tres métodos, dos grupos
        (4, ["attr1", "attr1", "attr2", "attr2"], 2.0),  # Cuatro métodos, dos grupos
        (5, ["attr1", "attr1", "attr2", "attr3", "attr3"], 3.0),  # Cinco métodos, tres grupos
    ],
)
def test_lcom4_calculation_parametrized(method_count, shared_attrs, expected_lcom4):
    """Test parametrizado para verificar cálculo de LCOM4."""
    factory = TestEntityFactory()
    metric = LCOM4()

    if method_count == 0:
        cls = Class(name="TestClass")
        cls.methods = []
    else:
        method_names = [f"method{i}" for i in range(method_count)]
        cls = factory.create_class_with_methods(method_names=method_names)

        # Configurar atributos
        for i, method in enumerate(cls.methods):
            if i < len(shared_attrs):
                method.accessed_instance_attributes = {shared_attrs[i]}
            else:
                method.accessed_instance_attributes = set()
            method.calls = set()  # Sin llamadas para aislar efecto de atributos

    result = metric.calculate_class(cls)
    assert result["lcom4"] == expected_lcom4


@pytest.mark.parametrize(
    "call_pattern,expected_components",
    [
        ([], 3),  # Sin llamadas = 3 componentes
        ([("method1", "method2")], 2),  # Una llamada = 2 componentes
        ([("method1", "method2"), ("method2", "method3")], 1),  # Cadena = 1 componente
        ([("method1", "method2"), ("method1", "method3")], 1),  # Estrella = 1 componente
        (
            [("method1", "method2"), ("method2", "method1")],
            2,
        ),  # Bidireccional = 2 componentes (method3 aislado)
    ],
)
def test_lcom4_method_calls_parametrized(call_pattern, expected_components):
    """Test parametrizado para verificar conexiones por llamadas de métodos."""
    factory = TestEntityFactory()
    metric = LCOM4()

    cls = factory.create_class_with_methods(method_names=["method1", "method2", "method3"])

    # Sin atributos compartidos
    for method in cls.methods:
        method.accessed_instance_attributes = set()
        method.calls = set()

    # Configurar llamadas según el patrón
    method_map = {method.name: method for method in cls.methods}
    for caller, callee in call_pattern:
        if caller in method_map:
            method_map[caller].calls.add(f"self.{callee}")

    result = metric.calculate_class(cls)
    assert result["connected_components"] == expected_components


@pytest.mark.parametrize(
    "complexity_level,expected_needs_refactoring",
    [
        (1.0, False),  # Excelente
        (2.0, False),  # Buena
        (3.0, False),  # Moderada
        (4.0, True),  # Pobre
        (5.0, True),  # Muy pobre
    ],
)
def test_lcom4_refactoring_analysis_parametrized(complexity_level, expected_needs_refactoring):
    """Test parametrizado para análisis de refactoring."""
    factory = TestEntityFactory()
    metric = LCOM4()

    # Crear clase que produzca el nivel de complejidad deseado
    num_methods = int(complexity_level)
    method_names = [f"method{i}" for i in range(num_methods)]
    cls = factory.create_class_with_methods(method_names=method_names)

    # Configurar para producir el LCOM4 deseado (métodos aislados)
    for i, method in enumerate(cls.methods):
        method.accessed_instance_attributes = {f"attr{i}"}
        method.calls = set()

    analysis = metric.get_cohesion_analysis(cls)
    assert analysis["needs_refactoring"] == expected_needs_refactoring


class TestLCOM4ASTAnalysis:
    """Tests para análisis AST de atributos."""

    def setup_method(self):
        """Setup para cada test."""
        self.metric = LCOM4()
        self.factory = TestEntityFactory()

    def test_extract_attributes_without_astroid_node(self):
        """Test extracción de atributos cuando no hay nodo AST."""
        method = Function(name="test_method")
        method.astroid_node = None
        method.accessed_instance_attributes = None

        result = self.metric._extract_accessed_attributes_from_ast(method)

        assert result == set()

    def test_extract_attributes_astroid_import_error(self):
        """Test extracción cuando astroid no está disponible."""
        from unittest.mock import patch

        method = Function(name="test_method")
        # Crear un mock de nodo AST mínimo
        method.astroid_node = type("MockNode", (), {"args": None})()
        method.accessed_instance_attributes = None

        # Mockear directamente la función de importación en el contexto LCOM4
        with patch("pypex.metrics.cohesion.lcom4.logger.warning") as mock_warning:
            with patch.dict("sys.modules", {"astroid.nodes": None}):
                # Mockear la importación específica
                original_import = __builtins__["__import__"]

                def mock_import(name, *args):
                    if name == "astroid":
                        raise ImportError("No astroid")
                    return original_import(name, *args)

                with patch("builtins.__import__", side_effect=mock_import):
                    result = self.metric._extract_accessed_attributes_from_ast(method)

        assert result == set()
        mock_warning.assert_called_once()

    def test_extract_attributes_no_args(self):
        """Test extracción cuando el método no tiene argumentos."""
        method = Function(name="test_method")
        # Crear mock de nodo sin args correctamente
        method.astroid_node = type("MockNode", (), {"args": None, "body": []})()
        method.accessed_instance_attributes = None

        result = self.metric._extract_accessed_attributes_from_ast(method)

        assert result == set()

    def test_method_with_astroid_node_but_no_accessed_attributes(self):
        """Test método con nodo AST pero sin accessed_instance_attributes definido."""
        method = Function(name="test_method")

        # Crear mock mínimo de nodo AST
        mock_arg = type("MockArg", (), {"name": "self"})()
        args_mock = type("MockArgs", (), {"args": [mock_arg]})()
        method.astroid_node = type("MockNode", (), {"args": args_mock, "body": []})()

        # No establecer accessed_instance_attributes
        if hasattr(method, "accessed_instance_attributes"):
            delattr(method, "accessed_instance_attributes")

        result = self.metric._extract_accessed_attributes_from_ast(method)

        # Debería devolver conjunto vacío ya que no hay body con accesos
        assert result == set()


class TestLCOM4AdvancedEdgeCases:
    """Tests adicionales para casos edge avanzados."""

    def setup_method(self):
        """Setup para cada test."""
        self.metric = LCOM4()
        self.factory = TestEntityFactory()

    def test_dfs_with_complex_graph(self):
        """Test DFS con grafo complejo."""
        # Crear un grafo manualmente para probar DFS
        graph = {
            "a": {"b", "c"},
            "b": {"a", "d"},
            "c": {"a"},
            "d": {"b"},
            "e": {"f"},
            "f": {"e"},
            "g": set(),  # Nodo aislado
        }

        components = self.metric._count_connected_components(graph)

        # Debe tener 3 componentes: {a,b,c,d}, {e,f}, {g}
        assert components == 3

    def test_get_aggregated_value_with_complex_dict(self):
        """Test get_aggregated_value con diccionario complejo."""
        # Crear resultado simulado complejo
        mock_result = {"module_max_lcom4": 5.0, "other_value": 2.0, "lcom4": 3.0}

        # Crear mock de método calculate que devuelve este dict
        original_calculate = self.metric.calculate
        self.metric.calculate = lambda entity: mock_result

        try:
            value = self.metric.get_aggregated_value("dummy_entity")
            # El orden de búsqueda es: lcom4, total, module_max_lcom4, project_max_lcom4
            # Por lo tanto debe devolver 'lcom4' que es 3.0
            assert value == 3.0
        finally:
            self.metric.calculate = original_calculate

    def test_get_aggregated_value_with_project_dict(self):
        """Test get_aggregated_value con resultado de proyecto."""
        # Crear resultado simulado de proyecto sin 'lcom4' ni 'total'
        mock_result = {"project_max_lcom4": 7.0, "other_value": 4.0}

        # Crear mock de método calculate que devuelve este dict
        original_calculate = self.metric.calculate
        self.metric.calculate = lambda entity: mock_result

        try:
            value = self.metric.get_aggregated_value("dummy_entity")
            # Debe devolver project_max_lcom4 ya que no hay lcom4 ni total
            assert value == 7.0
        finally:
            self.metric.calculate = original_calculate

    def test_get_aggregated_value_fallback(self):
        """Test get_aggregated_value cuando no encuentra claves conocidas."""
        # Crear resultado sin claves conocidas
        mock_result = {"unknown_key": 5.0, "another_unknown": 3.0}

        # Crear mock de método calculate
        original_calculate = self.metric.calculate
        self.metric.calculate = lambda entity: mock_result

        try:
            value = self.metric.get_aggregated_value("dummy_entity")
            # Debe devolver 0.0 como fallback
            assert value == 0.0
        finally:
            self.metric.calculate = original_calculate

    def test_class_with_methods_having_mixed_attribute_types(self):
        """Test clase con métodos que tienen tipos mixtos de atributos."""
        cls = self.factory.create_class_with_methods(
            class_name="MixedAttrTypesClass", method_names=["method1", "method2", "method3"]
        )

        # Mezcla de tipos de atributos
        cls.methods[0].accessed_instance_attributes = {"attr1"}  # set normal
        cls.methods[1].accessed_instance_attributes = None  # None
        cls.methods[2].accessed_instance_attributes = set()  # set vacío

        # Sin llamadas
        for method in cls.methods:
            method.calls = set()

        result = self.metric.calculate_class(cls)

        # Solo method1 tiene atributos, por lo que todos están desconectados
        assert result["lcom4"] == 3.0
        assert result["connected_components"] == 3

    def test_attribute_connections_calculation_edge_case(self):
        """Test cálculo de conexiones por atributos en caso edge."""
        cls = self.factory.create_class_with_methods(
            class_name="AttrConnectionsEdgeCase", method_names=["m1", "m2", "m3", "m4"]
        )

        # Un atributo compartido por 3 métodos
        cls.methods[0].accessed_instance_attributes = {"shared_attr"}
        cls.methods[1].accessed_instance_attributes = {"shared_attr"}
        cls.methods[2].accessed_instance_attributes = {"shared_attr"}
        cls.methods[3].accessed_instance_attributes = {"isolated_attr"}

        for method in cls.methods:
            method.calls = set()

        # Calcular conexiones manualmente: 3 métodos compartiendo 1 atributo = 3*(3-1)/2 = 3 conexiones
        expected_attr_connections = 3.0

        result = self.metric.calculate_class(cls)

        assert result["attribute_connections"] == expected_attr_connections
        assert result["lcom4"] == 2.0  # {m1,m2,m3} y {m4}

    def test_method_calls_with_various_formats(self):
        """Test llamadas de método con diferentes formatos de nombrado."""
        cls = self.factory.create_class_with_methods(
            class_name="VariousCallFormatsClass",
            method_names=["caller", "target1", "target2", "target3"],
        )

        # Diferentes formatos de llamadas
        cls.methods[0].calls = {
            "self.target1",  # Formato estándar
            "target2",  # Sin self
            "module.target3",  # Con módulo (debería contar como interno)
            "self.external",  # Método externo (no debería contar)
        }

        # Sin atributos para aislar efecto de llamadas
        for method in cls.methods:
            method.accessed_instance_attributes = set()
            if method.name != "caller":
                method.calls = set()

        result = self.metric.calculate_class(cls)

        # Deben contar las llamadas a target1, target2 y target3 (3 conexiones)
        # porque _extract_method_name("module.target3") devuelve "target3"
        assert result["method_connections"] == 3.0
        assert result["lcom4"] == 1.0  # {caller,target1,target2,target3} todos conectados


if __name__ == "__main__":
    pytest.main([__file__])
