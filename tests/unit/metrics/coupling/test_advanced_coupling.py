"""Tests comprehensivos para la métrica de Acoplamiento Avanzado.

Este módulo contiene tests exhaustivos que cubren todos los aspectos
de la métrica de acoplamiento avanzado, incluyendo edge cases.
"""

import pytest
from typing import List, Dict

from pypex.metrics.coupling.advanced_coupling import AdvancedCouplingMetric
from pypex.parser.code_entities import Function, Class, Module, Project, Import
from tests.unit.metrics.test_utils import (
    TestEntityFactory,
    BaseMetricTestCase,
    AssertionHelpers
)


class TestAdvancedCouplingBasic:
    """Tests básicos para la métrica de Acoplamiento Avanzado."""
    
    def setup_method(self):
        """Setup para cada test."""
        self.factory = TestEntityFactory()
        self.assertions = AssertionHelpers()
        self.metric = AdvancedCouplingMetric()
    
    def test_metric_properties(self):
        """Verifica las propiedades básicas de la métrica."""
        assert self.metric.name == "advanced_coupling"
        assert "acoplamiento" in self.metric.description.lower()
        assert "cbo" in self.metric.description.lower()
        assert "rfc" in self.metric.description.lower()
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


class TestAdvancedCouplingFunctions:
    """Tests para funciones (que devuelven None)."""
    
    def setup_method(self):
        """Setup para cada test."""
        self.factory = TestEntityFactory()
        self.metric = AdvancedCouplingMetric()
    
    def test_function_returns_none(self):
        """Test que funciones devuelven None."""
        func = self.factory.create_simple_function("test_func")
        
        result = self.metric.calculate_function(func)
        
        assert result is None  # No aplica a funciones


class TestAdvancedCouplingClasses:
    """Tests para cálculo de acoplamiento avanzado en clases."""
    
    def setup_method(self):
        """Setup para cada test."""
        self.factory = TestEntityFactory()
        self.metric = AdvancedCouplingMetric()
        self.assertions = AssertionHelpers()
    
    def test_empty_class(self):
        """Test clase sin métodos ni herencia."""
        empty_class = Class(name="EmptyClass")
        empty_class.methods = []
        empty_class.base_classes = []
        
        result = self.metric.calculate_class(empty_class)
        
        expected_keys = ["cbo", "rfc", "mpc", "inheritance_coupling", "external_classes_used", "external_methods_called"]
        self.assertions.assert_metric_result_structure(result, expected_keys)
        
        assert result["cbo"] == 0.0  # Sin herencia ni referencias externas
        assert result["rfc"] == 0.0  # Sin métodos
        assert result["mpc"] == 0.0  # Sin llamadas externas
        assert result["inheritance_coupling"] == 0.0  # Sin herencia
        assert result["external_classes_used"] == 0.0  # Sin clases externas
        assert result["external_methods_called"] == 0.0  # Sin métodos externos
    
    def test_class_with_inheritance(self):
        """Test clase con herencia."""
        cls = self.factory.create_class_with_methods(
            class_name="ChildClass",
            method_names=["method1"]
        )
        cls.base_classes = ["BaseClass", "Mixin"]  # Herencia múltiple
        
        result = self.metric.calculate_class(cls)
        
        assert result["cbo"] >= 2.0  # Al menos las 2 clases base
        assert result["rfc"] >= 1.0  # Al menos 1 método propio
        assert result["inheritance_coupling"] == 2.0  # 2 clases base
    
    def test_class_with_external_calls(self):
        """Test clase con llamadas a métodos externos."""
        cls = self.factory.create_class_with_methods(
            class_name="CoupledClass",
            method_names=["method1", "method2"]
        )
        
        # Simular llamadas externas
        cls.methods[0].calls = {"other_obj.method", "external.function", "self.internal"}
        cls.methods[1].calls = {"another.call", "utils.helper"}
        
        result = self.metric.calculate_class(cls)
        
        assert result["cbo"] >= 3.0  # other_obj, external, another, utils
        assert result["rfc"] >= 2.0  # Métodos propios + externos
        assert result["mpc"] >= 4.0  # Llamadas externas (sin self.)
        assert result["external_classes_used"] >= 3.0  # Clases externas referenciadas
        assert result["external_methods_called"] >= 4.0  # Métodos externos llamados
    
    def test_class_with_mixed_coupling(self):
        """Test clase con herencia y llamadas externas."""
        cls = self.factory.create_class_with_methods(
            class_name="HighlyCoupledClass",
            method_names=["method1", "method2", "method3"]
        )
        cls.base_classes = ["BaseClass"]
        
        # Configurar llamadas externas variadas
        cls.methods[0].calls = {"db.query", "logger.info"}
        cls.methods[1].calls = {"validator.check", "self.helper"}  # self. no cuenta
        cls.methods[2].calls = {"api.call", "utils.format"}
        
        result = self.metric.calculate_class(cls)
        
        # CBO = herencia + clases externas únicas
        assert result["cbo"] >= 5.0  # BaseClass + db + logger + validator + api + utils
        assert result["rfc"] >= 8.0  # 3 métodos propios + 5 externos
        assert result["mpc"] >= 5.0  # 5 llamadas externas
        assert result["inheritance_coupling"] == 1.0  # 1 clase base
    
    def test_class_high_coupling_scenario(self):
        """Test clase con acoplamiento muy alto."""
        cls = self.factory.create_class_with_methods(
            class_name="HighCouplingClass",
            method_names=["m1", "m2", "m3", "m4"]
        )
        cls.base_classes = ["Base1", "Base2", "Base3"]  # Herencia múltiple
        
        # Muchas llamadas externas
        cls.methods[0].calls = {"service1.method", "service2.call", "util1.func"}
        cls.methods[1].calls = {"service3.process", "service4.handle"}
        cls.methods[2].calls = {"db.save", "cache.set", "log.write"}
        cls.methods[3].calls = {"api.request", "parser.parse"}
        
        result = self.metric.calculate_class(cls)
        
        assert result["cbo"] >= 10.0  # Alta complejidad de acoplamiento
        assert result["rfc"] >= 14.0  # 4 métodos + 10 externos
        assert result["mpc"] >= 10.0  # 10 llamadas externas
        assert result["inheritance_coupling"] == 3.0  # 3 clases base


class TestAdvancedCouplingModules:
    """Tests para cálculo de acoplamiento avanzado en módulos."""
    
    def setup_method(self):
        """Setup para cada test."""
        self.factory = TestEntityFactory()
        self.metric = AdvancedCouplingMetric()
        self.assertions = AssertionHelpers()
    
    def test_empty_module(self):
        """Test módulo sin imports ni clases."""
        module = Module(name="empty_module")
        module.imports = []
        module.classes = []
        
        result = self.metric.calculate_module(module)
        
        expected_keys = ["ca", "ce", "instability", "abstractness", "distance_main_sequence", 
                        "total_classes", "abstract_classes", "imports_count"]
        self.assertions.assert_metric_result_structure(result, expected_keys)
        
        assert result["ca"] == 0.0  # Sin dependientes (se calcula en proyecto)
        assert result["ce"] == 0.0  # Sin imports
        assert result["instability"] == 0.0  # Sin dependencias
        assert result["abstractness"] == 0.0  # Sin clases
        assert result["distance_main_sequence"] == 1.0  # |0 + 0 - 1| = 1
        assert result["total_classes"] == 0.0
        assert result["abstract_classes"] == 0.0
        assert result["imports_count"] == 0.0
    
    def test_module_with_imports(self):
        """Test módulo con imports."""
        module = self.factory.create_module_with_entities("test_module")
        
        # Agregar imports específicos
        module.imports = [
            Import(module="os", line=1),
            Import(module="sys", line=2),
            Import(module="json", line=3),
            Import(module="requests", line=4)
        ]
        
        result = self.metric.calculate_module(module)
        
        assert result["ce"] == 4.0  # 4 imports
        assert result["instability"] == 1.0  # Ce/(Ca+Ce) = 4/(0+4) = 1
        assert result["imports_count"] == 4.0
    
    def test_module_with_abstract_classes(self):
        """Test módulo con clases abstractas."""
        module = self.factory.create_module_with_entities("abstract_module")
        
        # Configurar clases abstractas
        module.classes[0].is_abstract_class = True  # 1 abstracta
        module.classes[1].is_abstract_class = False  # 1 concreta
        
        result = self.metric.calculate_module(module)
        
        assert result["total_classes"] == 2.0
        assert result["abstract_classes"] == 1.0
        assert result["abstractness"] == 0.5  # 1/2 = 0.5
    
    def test_module_balanced_metrics(self):
        """Test módulo con métricas equilibradas."""
        module = self.factory.create_module_with_entities("balanced_module")
        
        # Configurar imports moderados
        module.imports = [
            Import(module="utils", line=1),
            Import(module="helpers", line=2)
        ]
        
        # Configurar clases mixtas
        module.classes[0].is_abstract_class = True
        module.classes[1].is_abstract_class = False
        
        result = self.metric.calculate_module(module)
        
        assert result["ce"] == 2.0  # 2 imports
        assert result["abstractness"] == 0.5  # 1/2 abstractas
        assert result["instability"] == 1.0  # 2/(0+2) = 1
        assert result["distance_main_sequence"] == 0.5  # |0.5 + 1.0 - 1| = 0.5
    
    def test_module_high_coupling_scenario(self):
        """Test módulo con alto acoplamiento."""
        module = self.factory.create_module_with_entities("high_coupling_module")
        
        # Muchos imports
        imports = [Import(module=f"lib{i}", line=i) for i in range(1, 11)]  # 10 imports
        module.imports = imports
        
        # Todas las clases concretas
        for cls in module.classes:
            cls.is_abstract_class = False
        
        result = self.metric.calculate_module(module)
        
        assert result["ce"] == 10.0  # 10 imports
        assert result["abstractness"] == 0.0  # Todas concretas
        assert result["instability"] == 1.0  # 10/(0+10) = 1
        assert result["distance_main_sequence"] == 0.0  # |0 + 1 - 1| = 0


class TestAdvancedCouplingProjects:
    """Tests para cálculo de acoplamiento avanzado en proyectos."""
    
    def setup_method(self):
        """Setup para cada test."""
        self.factory = TestEntityFactory()
        self.metric = AdvancedCouplingMetric()
        self.assertions = AssertionHelpers()
    
    def test_empty_project(self):
        """Test proyecto sin módulos."""
        project = Project(name="empty_project")
        project.modules = []
        
        result = self.metric.calculate_project(project)
        
        expected_keys = ["avg_ca", "avg_ce", "avg_instability", "avg_abstractness", 
                        "avg_distance_main_sequence", "avg_cbo", "avg_rfc", "avg_mpc",
                        "module_count", "class_count", "total_dependencies", 
                        "max_ca", "max_ce", "max_distance"]
        self.assertions.assert_metric_result_structure(result, expected_keys)
        
        assert result["module_count"] == 0.0
        assert result["class_count"] == 0.0
        assert result["total_dependencies"] == 0.0
    
    def test_project_with_internal_dependencies(self):
        """Test proyecto con dependencias internas entre módulos."""
        project = self.factory.create_project_with_modules("test_project", module_count=3)
        
        # Configurar dependencias internas
        project.modules[0].name = "module_a"
        project.modules[1].name = "module_b"
        project.modules[2].name = "module_c"
        
        # module_a importa module_b
        project.modules[0].imports = [Import(module="module_b", line=1)]
        # module_b importa module_c
        project.modules[1].imports = [Import(module="module_c", line=1)]
        # module_c no importa nada interno
        project.modules[2].imports = []
        
        result = self.metric.calculate_project(project)
        
        assert result["module_count"] == 3.0
        assert result["total_dependencies"] >= 2.0  # Al menos las dependencias internas
        assert result["max_ca"] >= 1.0  # module_b y module_c tienen dependientes
    
    def test_project_complex_dependencies(self):
        """Test proyecto con dependencias complejas."""
        project = self.factory.create_project_with_modules("complex_project", module_count=4)
        
        # Configurar nombres y dependencias
        project.modules[0].name = "core"
        project.modules[1].name = "utils"
        project.modules[2].name = "services"
        project.modules[3].name = "api"
        
        # Configurar imports internos y externos
        project.modules[0].imports = []  # core no depende de nada
        project.modules[1].imports = [Import(module="core", line=1)]  # utils -> core
        project.modules[2].imports = [
            Import(module="core", line=1),
            Import(module="utils", line=2),
            Import(module="requests", line=3)  # Externa
        ]
        project.modules[3].imports = [
            Import(module="services", line=1),
            Import(module="flask", line=2)  # Externa
        ]
        
        # Configurar clases abstractas
        project.modules[0].classes[0].is_abstract_class = True  # core tiene abstracta
        
        result = self.metric.calculate_project(project)
        
        assert result["module_count"] == 4.0
        assert result["avg_ca"] > 0.0  # Algunos módulos tienen dependientes
        assert result["avg_ce"] > 0.0  # Algunos módulos tienen dependencias
        assert result["max_ca"] >= 2.0  # core es usado por utils y services
    
    def test_project_statistics_consistency(self):
        """Test que las estadísticas del proyecto son consistentes."""
        project = self.factory.create_project_with_modules("consistency_project", module_count=2)
        
        # Configurar escenario conocido
        project.modules[0].name = "mod_a"
        project.modules[1].name = "mod_b"
        
        project.modules[0].imports = [Import(module="mod_b", line=1)]
        project.modules[1].imports = []
        
        # Configurar clases con acoplamiento conocido
        project.modules[0].classes[0].base_classes = ["BaseClass"]
        project.modules[0].classes[0].methods[0].calls = {"external.method"}
        
        result = self.metric.calculate_project(project)
        
        # Verificar consistencia
        assert result["module_count"] == 2.0
        assert result["class_count"] >= 2.0  # Al menos 2 clases
        assert result["avg_cbo"] > 0.0  # Hay acoplamiento en clases
        assert result["max_ca"] <= result["module_count"]  # Ca no puede exceder módulos


class TestAdvancedCouplingEdgeCases:
    """Tests para casos extremos y edge cases."""
    
    def setup_method(self):
        """Setup para cada test."""
        self.factory = TestEntityFactory()
        self.metric = AdvancedCouplingMetric()
    
    def test_class_with_self_calls_only(self):
        """Test clase que solo llama a sus propios métodos."""
        cls = self.factory.create_class_with_methods(
            class_name="SelfContainedClass",
            method_names=["method1", "method2"]
        )
        
        # Solo llamadas internas
        cls.methods[0].calls = {"self.method2", "self.helper"}
        cls.methods[1].calls = {"self.method1"}
        
        result = self.metric.calculate_class(cls)
        
        assert result["cbo"] == 0.0  # Sin clases externas
        assert result["mpc"] == 0.0  # Sin llamadas externas
        assert result["external_classes_used"] == 0.0
    
    def test_module_with_zero_division_protection(self):
        """Test módulo que protege contra división por cero."""
        module = Module(name="zero_div_module")
        module.imports = []  # Sin imports
        module.classes = []  # Sin clases
        
        result = self.metric.calculate_module(module)
        
        # Verificar que no hay división por cero
        assert result["instability"] == 0.0  # Ca=0, Ce=0
        assert result["abstractness"] == 0.0  # Sin clases
        assert result["distance_main_sequence"] == 1.0  # |0 + 0 - 1|
    
    def test_get_aggregated_value_different_entities(self):
        """Test get_aggregated_value para diferentes tipos de entidades."""
        # Función
        func = self.factory.create_simple_function("test_func")
        assert self.metric.get_aggregated_value(func) == 0.0
        
        # Clase
        cls = self.factory.create_class_with_methods()
        cls.base_classes = ["BaseClass"]
        aggregated_class = self.metric.get_aggregated_value(cls)
        assert aggregated_class >= 1.0  # Al menos CBO de herencia
        
        # Módulo
        module = self.factory.create_module_with_entities("test_module")
        module.imports = [Import(module="os", line=1)]
        aggregated_module = self.metric.get_aggregated_value(module)
        assert aggregated_module >= 0.0  # Distance from main sequence
        
        # Proyecto
        project = self.factory.create_project_with_modules("test_project")
        aggregated_project = self.metric.get_aggregated_value(project)
        assert aggregated_project >= 0.0  # Promedio de distancia


class TestAdvancedCouplingIntegration:
    """Tests de integración para la métrica de Acoplamiento Avanzado."""
    
    def setup_method(self):
        """Setup para cada test."""
        self.metric = AdvancedCouplingMetric()
        self.factory = TestEntityFactory()
    
    def test_thresholds_configuration(self):
        """Verifica que los umbrales están correctamente configurados."""
        thresholds = self.metric.get_thresholds()
        
        assert isinstance(thresholds, dict)
        # Verificar que hay umbrales para diferentes niveles
    
    def test_interpretation_with_known_values(self):
        """Verifica interpretación con valores conocidos."""
        test_values = [0.0, 0.1, 0.3, 0.5, 0.7, 1.0]
        
        for value in test_values:
            interpretation = self.metric.interpret(value)
            assert isinstance(interpretation, str), f"Interpretación debe ser string para valor {value}"
            assert len(interpretation) > 0, f"Interpretación no puede estar vacía para valor {value}"
    
    def test_realistic_class_analysis(self):
        """Test con análisis de clase realista."""
        # Simular clase con acoplamiento moderado
        cls = self.factory.create_class_with_methods(
            class_name="ServiceClass",
            method_names=["process", "validate", "save"]
        )
        cls.base_classes = ["BaseService"]
        cls.methods[0].calls = {"db.query", "validator.check"}
        cls.methods[1].calls = {"utils.format"}
        cls.methods[2].calls = {"db.save", "logger.info"}
        
        result = self.metric.calculate_class(cls)
        
        assert result["cbo"] >= 4.0  # BaseService + db + validator + utils + logger
        assert result["rfc"] >= 8.0  # 3 métodos + 5 externos
        assert result["mpc"] >= 5.0  # 5 llamadas externas
        
        # Verificar interpretación
        interpretation = self.metric.interpret(result["cbo"])
        assert isinstance(interpretation, str)
        assert len(interpretation) > 0


@pytest.mark.parametrize("base_classes,external_calls,expected_min_cbo", [
    ([], [], 0),
    (["Base"], [], 1),
    (["Base1", "Base2"], [], 2),
    ([], ["obj.method"], 1),
    (["Base"], ["obj.method", "util.func"], 3),
])
def test_class_cbo_calculation(base_classes, external_calls, expected_min_cbo):
    """Test parametrizado para verificar cálculo de CBO en clases."""
    factory = TestEntityFactory()
    metric = AdvancedCouplingMetric()
    
    cls = factory.create_class_with_methods(method_names=["method1"])
    cls.base_classes = base_classes
    cls.methods[0].calls = set(external_calls)
    
    result = metric.calculate_class(cls)
    assert result["cbo"] >= expected_min_cbo


@pytest.mark.parametrize("imports_count,abstract_ratio,expected_instability", [
    (0, 0.0, 0.0),  # Sin imports ni clases
    (3, 0.0, 1.0),  # Solo dependencias salientes
    (5, 1.0, 1.0),  # Dependencias salientes con clases abstractas
])
def test_module_instability_calculation(imports_count, abstract_ratio, expected_instability):
    """Test parametrizado para verificar cálculo de inestabilidad en módulos."""
    factory = TestEntityFactory()
    metric = AdvancedCouplingMetric()
    
    module = factory.create_module_with_entities("test_module")
    
    # Configurar imports
    module.imports = [Import(module=f"lib{i}", line=i) for i in range(imports_count)]
    
    # Configurar clases abstractas
    total_classes = len(module.classes)
    abstract_count = int(total_classes * abstract_ratio)
    for i in range(abstract_count):
        if i < len(module.classes):
            module.classes[i].is_abstract_class = True
    
    result = metric.calculate_module(module)
    assert result["instability"] == expected_instability


if __name__ == "__main__":
    pytest.main([__file__]) 