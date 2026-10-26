"""Tests unitarios para el procesador de resultados."""

from unittest.mock import Mock, patch

import pytest

from pypex.core.results import (
    AnalysisError,
    EntityAnalysisResult,
    ErrorSeverity,
    FileAnalysisResult,
    MetricsResult,
    ProjectAnalysisResult,
)
from pypex.core.results_processor import ResultsProcessor


@pytest.fixture
def mock_config():
    """Mock del servicio de configuración."""
    config = Mock()
    config.get.return_value = "normal"  # threshold_profile por defecto
    return config


@pytest.fixture
def mock_threshold_config():
    """Mock de la configuración de thresholds."""
    threshold_config = Mock()
    threshold_config.get_thresholds.return_value = {"low": 5, "medium": 10, "high": 20}
    return threshold_config


@pytest.fixture
def mock_registry():
    """Mock del registry de métricas."""
    registry = Mock()
    registry.get_available_metrics.return_value = [
        "cyclomatic_complexity",
        "cognitive_complexity",
        "fan_in_out",
        "lcom4",
        "nesting_depth",
    ]

    mock_metric = Mock()
    mock_metric.interpret.return_value = "High complexity"
    registry.get_metric.return_value = mock_metric

    return registry


@pytest.fixture
def mock_entity():
    """Crea una entidad mock para testing."""
    entity = Mock(spec=EntityAnalysisResult)
    entity.source_info = {}
    entity.name = "test_function"
    entity.entity_type = "function"
    entity.children = []

    # Mock del contenedor de métricas
    metrics = Mock(spec=MetricsResult)
    metrics.get_metric_value.return_value = 15  # valor por defecto
    entity.metrics = metrics

    return entity


@pytest.fixture
def mock_file_result():
    """Crea un resultado de archivo mock."""
    file_result = Mock(spec=FileAnalysisResult)
    file_result.was_successful = True
    file_result.line_count = 100
    file_result.errors = []
    file_result.entities = []
    return file_result


@pytest.fixture
def mock_project_result():
    """Crea un resultado de proyecto mock."""
    project_result = Mock(spec=ProjectAnalysisResult)
    project_result.files = {}
    project_result.successful_files = 1
    project_result.failed_files = 0
    project_result.analysis_time_ms = 1000
    project_result.total_lines_of_code = 100
    project_result.get_all_errors.return_value = []
    return project_result


class TestResultsProcessor:
    """Tests para la clase ResultsProcessor."""

    @patch("pypex.core.results_processor.get_config")
    def test_init(self, mock_get_config, mock_config):
        """Prueba la inicialización del ResultsProcessor."""
        mock_get_config.return_value = mock_config

        processor = ResultsProcessor()

        assert processor.config == mock_config
        assert "sum" in processor.aggregation_functions
        assert "avg" in processor.aggregation_functions
        assert "max" in processor.aggregation_functions
        assert "min" in processor.aggregation_functions
        assert "count" in processor.aggregation_functions

    @patch("pypex.core.results_processor.get_config")
    def test_aggregation_functions(self, mock_get_config, mock_config):
        """Prueba las funciones de agregación."""
        mock_get_config.return_value = mock_config
        processor = ResultsProcessor()

        values = [1, 2, 3, 4, 5]

        assert processor.aggregation_functions["sum"](values) == 15
        assert processor.aggregation_functions["avg"](values) == 3.0
        assert processor.aggregation_functions["max"](values) == 5
        assert processor.aggregation_functions["min"](values) == 1
        assert processor.aggregation_functions["count"](values) == 5

        # Test con lista vacía
        assert processor.aggregation_functions["avg"]([]) == 0
        assert processor.aggregation_functions["max"]([]) == 0
        assert processor.aggregation_functions["min"]([]) == 0

    @patch("pypex.core.results_processor.get_config")
    def test_aggregate_metrics_success(
        self, mock_get_config, mock_config, mock_project_result, mock_file_result, mock_entity
    ):
        """Prueba la agregación exitosa de métricas."""
        mock_get_config.return_value = mock_config
        processor = ResultsProcessor()

        # Configurar entidad con valor de métrica
        mock_entity.metrics.get_metric_value.return_value = 10
        mock_file_result.entities = [mock_entity]
        mock_project_result.files = {"test.py": mock_file_result}

        result = processor.aggregate_metrics(mock_project_result, "cyclomatic_complexity", "sum")

        assert result["project_total"] == 10
        assert result["files_count"] == 1
        assert result["average_per_file"] == 10
        assert "file_test" in result

    @patch("pypex.core.results_processor.get_config")
    def test_aggregate_metrics_invalid_type(
        self, mock_get_config, mock_config, mock_project_result
    ):
        """Prueba error con tipo de agregación inválido."""
        mock_get_config.return_value = mock_config
        processor = ResultsProcessor()

        with pytest.raises(ValueError) as exc_info:
            processor.aggregate_metrics(
                mock_project_result, "cyclomatic_complexity", "invalid_type"
            )

        assert "Tipo de agregación no soportado" in str(exc_info.value)

    @patch("pypex.core.results_processor.get_config")
    def test_aggregate_metrics_with_children(
        self, mock_get_config, mock_config, mock_project_result, mock_file_result, mock_entity
    ):
        """Prueba agregación incluyendo entidades hijas."""
        mock_get_config.return_value = mock_config
        processor = ResultsProcessor()

        child_entity = Mock(spec=EntityAnalysisResult)

        child_entity.source_info = {}
        child_entity.name = "method_1"
        child_entity.entity_type = "method"
        child_metrics = Mock(spec=MetricsResult)
        child_metrics.get_metric_value.return_value = 5
        child_entity.metrics = child_metrics

        mock_entity.children = [child_entity]
        mock_entity.metrics.get_metric_value.return_value = 10

        mock_file_result.entities = [mock_entity]
        mock_project_result.files = {"test.py": mock_file_result}

        result = processor.aggregate_metrics(mock_project_result, "cyclomatic_complexity", "sum")

        assert result["project_total"] == 15  # 10 + 5

    @patch("pypex.core.results_processor.get_config")
    def test_aggregate_metrics_failed_file(
        self, mock_get_config, mock_config, mock_project_result, mock_file_result, mock_entity
    ):
        """Prueba que archivos fallidos se ignoran."""
        mock_get_config.return_value = mock_config
        processor = ResultsProcessor()

        mock_file_result.was_successful = False
        mock_file_result.entities = [mock_entity]
        mock_project_result.files = {"test.py": mock_file_result}

        result = processor.aggregate_metrics(mock_project_result, "cyclomatic_complexity", "sum")

        assert result["project_total"] == 0
        assert result["files_count"] == 0

    @patch("pypex.core.results_processor.get_config")
    def test_aggregate_metrics_none_values(
        self, mock_get_config, mock_config, mock_project_result, mock_file_result, mock_entity
    ):
        """Prueba manejo de valores None en métricas."""
        mock_get_config.return_value = mock_config
        processor = ResultsProcessor()

        mock_entity.metrics.get_metric_value.return_value = None
        mock_file_result.entities = [mock_entity]
        mock_project_result.files = {"test.py": mock_file_result}

        result = processor.aggregate_metrics(mock_project_result, "cyclomatic_complexity", "sum")

        assert result["project_total"] == 0

    @patch("pypex.core.results_processor.get_config")
    def test_aggregate_metrics_different_types(
        self, mock_get_config, mock_config, mock_project_result, mock_file_result
    ):
        """Prueba agregación con diferentes tipos de agregación."""
        mock_get_config.return_value = mock_config
        processor = ResultsProcessor()

        # Crear múltiples entidades con valores diferentes
        entities = []
        for value in [5, 10, 15, 20]:
            entity = Mock(spec=EntityAnalysisResult)
            entity.source_info = {}
            entity.entity_type = "function"
            entity.children = []
            metrics = Mock(spec=MetricsResult)
            metrics.get_metric_value.return_value = value
            entity.metrics = metrics
            entities.append(entity)

        mock_file_result.entities = entities
        mock_project_result.files = {"test.py": mock_file_result}

        # Test diferentes tipos de agregación
        result_sum = processor.aggregate_metrics(mock_project_result, "metric", "sum")
        result_avg = processor.aggregate_metrics(mock_project_result, "metric", "avg")
        result_max = processor.aggregate_metrics(mock_project_result, "metric", "max")
        result_min = processor.aggregate_metrics(mock_project_result, "metric", "min")
        result_count = processor.aggregate_metrics(mock_project_result, "metric", "count")

        assert result_sum["project_total"] == 50
        assert result_avg["project_total"] == 12.5
        assert result_max["project_total"] == 20
        assert result_min["project_total"] == 5
        assert result_count["project_total"] == 4

    @patch("pypex.core.results_processor.get_config")
    def test_find_problematic_entities_success(
        self, mock_get_config, mock_config, mock_project_result, mock_file_result, mock_entity
    ):
        """Prueba la detección exitosa de entidades problemáticas."""
        mock_get_config.return_value = mock_config

        with patch("pypex.metrics.get_registry") as mock_get_registry:
            mock_registry = Mock()
            mock_registry.get_metric.return_value = Mock()  # Mock de métrica
            mock_get_registry.return_value = mock_registry

            processor = ResultsProcessor()

            # Configurar entidad con valor sobre threshold
            mock_entity.metrics.get_metric_value.return_value = 25
            mock_file_result.entities = [mock_entity]
            mock_project_result.files = {"test.py": mock_file_result}

            thresholds = {"cyclomatic_complexity": 20}

            result = processor.find_problematic_entities(mock_project_result, thresholds)

            assert "cyclomatic_complexity" in result
            assert len(result["cyclomatic_complexity"]) == 1

    @patch("pypex.core.results_processor.get_config")
    def test_find_problematic_entities_below_threshold(
        self, mock_get_config, mock_config, mock_project_result, mock_file_result, mock_entity
    ):
        """Prueba que entidades bajo el threshold no se detectan."""
        mock_get_config.return_value = mock_config

        with patch("pypex.metrics.get_registry") as mock_get_registry:
            mock_registry = Mock()
            mock_registry.get_metric.return_value = Mock()
            mock_get_registry.return_value = mock_registry

            processor = ResultsProcessor()

            # Configurar entidad con valor bajo threshold
            mock_entity.metrics.get_metric_value.return_value = 5
            mock_file_result.entities = [mock_entity]
            mock_project_result.files = {"test.py": mock_file_result}

            thresholds = {"cyclomatic_complexity": 10}

            result = processor.find_problematic_entities(mock_project_result, thresholds)

            assert "cyclomatic_complexity" in result
            assert len(result["cyclomatic_complexity"]) == 0

    @patch("pypex.core.results_processor.get_config")
    def test_check_entity_thresholds_dict_value_with_total(self, mock_get_config, mock_config):
        """Prueba _check_entity_thresholds con valor de diccionario que tiene 'total'."""
        mock_get_config.return_value = mock_config

        with patch("pypex.metrics.get_registry") as mock_get_registry:
            mock_registry = Mock()
            mock_registry.get_metric.return_value = Mock()
            mock_get_registry.return_value = mock_registry

            processor = ResultsProcessor()

            entity = Mock(spec=EntityAnalysisResult)

            entity.source_info = {}
            metrics = Mock(spec=MetricsResult)
            metrics.get_metric_value.return_value = {"total": 25, "other": 5}
            entity.metrics = metrics

            thresholds = {"test_metric": 20}
            problematic = {"test_metric": []}

            processor._check_entity_thresholds(entity, thresholds, problematic)

            assert len(problematic["test_metric"]) == 1

    @patch("pypex.core.results_processor.get_config")
    def test_check_entity_thresholds_dict_value_with_sum(self, mock_get_config, mock_config):
        """Prueba _check_entity_thresholds con valor de diccionario que tiene 'sum'."""
        mock_get_config.return_value = mock_config

        with patch("pypex.metrics.get_registry") as mock_get_registry:
            mock_registry = Mock()
            mock_registry.get_metric.return_value = Mock()
            mock_get_registry.return_value = mock_registry

            processor = ResultsProcessor()

            entity = Mock(spec=EntityAnalysisResult)

            entity.source_info = {}
            metrics = Mock(spec=MetricsResult)
            metrics.get_metric_value.return_value = {"sum": 25, "other": 5}
            entity.metrics = metrics

            thresholds = {"test_metric": 20}
            problematic = {"test_metric": []}

            processor._check_entity_thresholds(entity, thresholds, problematic)

            assert len(problematic["test_metric"]) == 1

    @patch("pypex.core.results_processor.get_config")
    def test_check_entity_thresholds_dict_value_numeric_sum(self, mock_get_config, mock_config):
        """Prueba _check_entity_thresholds con diccionario sin claves especiales."""
        mock_get_config.return_value = mock_config

        with patch("pypex.metrics.get_registry") as mock_get_registry:
            mock_registry = Mock()
            mock_registry.get_metric.return_value = Mock()
            mock_get_registry.return_value = mock_registry

            processor = ResultsProcessor()

            entity = Mock(spec=EntityAnalysisResult)

            entity.source_info = {}
            metrics = Mock(spec=MetricsResult)
            metrics.get_metric_value.return_value = {"val1": 15, "val2": 10, "string": "text"}
            entity.metrics = metrics

            thresholds = {"test_metric": 20}
            problematic = {"test_metric": []}

            processor._check_entity_thresholds(entity, thresholds, problematic)

            assert len(problematic["test_metric"]) == 1  # 15 + 10 = 25 > 20

    @patch("pypex.core.results_processor.get_config")
    def test_check_entity_thresholds_exception_handling(self, mock_get_config, mock_config):
        """Prueba manejo de excepciones en _check_entity_thresholds."""
        mock_get_config.return_value = mock_config

        with patch("pypex.metrics.get_registry") as mock_get_registry:
            mock_registry = Mock()
            mock_registry.get_metric.side_effect = Exception("Registry error")
            mock_get_registry.return_value = mock_registry

            processor = ResultsProcessor()

            entity = Mock(spec=EntityAnalysisResult)

            entity.source_info = {}
            metrics = Mock(spec=MetricsResult)
            metrics.get_metric_value.return_value = None
            entity.metrics = metrics

            thresholds = {"test_metric": 20}
            problematic = {"test_metric": []}

            # No debería lanzar excepción
            processor._check_entity_thresholds(entity, thresholds, problematic)

            assert len(problematic["test_metric"]) == 0

    @patch("pypex.core.results_processor.get_config")
    def test_get_all_registered_metrics_success(self, mock_get_config, mock_config, mock_registry):
        """Prueba obtención exitosa de métricas registradas."""
        mock_get_config.return_value = mock_config

        with patch("pypex.metrics.get_registry") as mock_get_registry:
            mock_get_registry.return_value = mock_registry

            processor = ResultsProcessor()

            result = processor._get_all_registered_metrics()

            assert result == [
                "cyclomatic_complexity",
                "cognitive_complexity",
                "fan_in_out",
                "lcom4",
                "nesting_depth",
            ]
            mock_registry.get_available_metrics.assert_called_once()

    @patch("pypex.core.results_processor.get_config")
    def test_get_all_registered_metrics_fallback(self, mock_get_config, mock_config):
        """Prueba fallback cuando falla obtener métricas del registry."""
        mock_get_config.return_value = mock_config

        with patch("pypex.metrics.get_registry") as mock_get_registry:
            mock_get_registry.side_effect = Exception("Registry error")

            processor = ResultsProcessor()

            result = processor._get_all_registered_metrics()

            # Debe devolver métricas por defecto
            expected = [
                "cyclomatic_complexity",
                "cognitive_complexity",
                "fan_in_out",
                "lcom4",
                "nesting_depth",
            ]
            assert result == expected

    @patch("pypex.core.results_processor.get_config")
    @patch("pypex.core.results_processor.get_threshold_config")
    def test_get_quality_metrics_config_success(
        self,
        mock_get_threshold_config,
        mock_get_config,
        mock_config,
        mock_threshold_config,
        mock_registry,
    ):
        """Prueba obtención exitosa de configuración de métricas de calidad."""
        mock_get_config.return_value = mock_config
        mock_get_threshold_config.return_value = mock_threshold_config

        with patch("pypex.metrics.get_registry") as mock_get_registry:
            mock_get_registry.return_value = mock_registry

            processor = ResultsProcessor()

            result = processor._get_quality_metrics_config("medium")

            assert isinstance(result, dict)
            mock_threshold_config.get_thresholds.assert_called()

    @patch("pypex.core.results_processor.get_config")
    @patch("pypex.core.results_processor.get_threshold_config")
    def test_get_quality_metrics_config_exception_fallback(
        self, mock_get_threshold_config, mock_get_config, mock_config, mock_registry
    ):
        """Prueba fallback cuando falla obtener thresholds."""
        mock_get_config.return_value = mock_config

        threshold_config = Mock()
        threshold_config.get_thresholds.side_effect = Exception("Threshold error")
        mock_get_threshold_config.return_value = threshold_config

        with patch("pypex.metrics.get_registry") as mock_get_registry:
            mock_get_registry.return_value = mock_registry

            processor = ResultsProcessor()

            result = processor._get_quality_metrics_config("medium")

            assert isinstance(result, dict)
            # Debe usar valores por defecto
            for metric_name in mock_registry.get_available_metrics.return_value:
                assert metric_name in result
                assert result[metric_name] == 10  # valor por defecto para "medium"

    @patch("pypex.core.results_processor.get_config")
    def test_generate_quality_report_strict_profile(self, mock_get_config, mock_project_result):
        """Prueba que profile 'strict' retorna None."""
        mock_config = Mock()
        mock_config.get.return_value = "strict"
        mock_get_config.return_value = mock_config

        processor = ResultsProcessor()

        result = processor.generate_quality_report(mock_project_result)

        assert result is None

    @patch("pypex.core.results_processor.get_config")
    @patch("pypex.core.results_processor.get_threshold_config")
    def test_generate_quality_report_permissive_profile(
        self,
        mock_get_threshold_config,
        mock_get_config,
        mock_project_result,
        mock_file_result,
        mock_entity,
        mock_threshold_config,
        mock_registry,
    ):
        """Prueba reporte de calidad con profile 'permissive'."""
        mock_config = Mock()
        mock_config.get.return_value = "permissive"
        mock_get_config.return_value = mock_config
        mock_get_threshold_config.return_value = mock_threshold_config

        with patch("pypex.metrics.get_registry") as mock_get_registry:
            mock_get_registry.return_value = mock_registry

            processor = ResultsProcessor()

            # Configurar datos de prueba
            mock_entity.metrics.get_metric_value.return_value = 3  # Bajo threshold
            mock_file_result.entities = [mock_entity]
            mock_project_result.files = {"test.py": mock_file_result}

            result = processor.generate_quality_report(mock_project_result)

            assert result is not None
            assert result["analysis_type"] == "basic"
            assert result["threshold_profile"] == "permissive"
            assert result["threshold_level"] == "low"
            assert "overall_quality_score" in result

    @patch("pypex.core.results_processor.get_config")
    @patch("pypex.core.results_processor.get_threshold_config")
    def test_generate_quality_report_normal_profile(
        self,
        mock_get_threshold_config,
        mock_get_config,
        mock_project_result,
        mock_file_result,
        mock_entity,
        mock_threshold_config,
        mock_registry,
    ):
        """Prueba reporte de calidad con profile 'normal'."""
        mock_config = Mock()
        mock_config.get.return_value = "normal"
        mock_get_config.return_value = mock_config
        mock_get_threshold_config.return_value = mock_threshold_config

        with patch("pypex.metrics.get_registry") as mock_get_registry:
            mock_get_registry.return_value = mock_registry

            processor = ResultsProcessor()

            # Configurar datos de prueba
            mock_entity.metrics.get_metric_value.return_value = 8  # Medium threshold
            mock_file_result.entities = [mock_entity]
            mock_project_result.files = {"test.py": mock_file_result}

            result = processor.generate_quality_report(mock_project_result)

            assert result is not None
            assert result["analysis_type"] == "basic"
            assert result["threshold_profile"] == "normal"
            assert result["threshold_level"] == "medium"

    @patch("pypex.core.results_processor.get_config")
    def test_calculate_quality_score_no_entities(
        self, mock_get_config, mock_config, mock_project_result
    ):
        """Prueba cálculo de score con 0 entidades."""
        mock_get_config.return_value = mock_config
        processor = ResultsProcessor()

        mock_project_result.files = {}

        score = processor._calculate_quality_score(mock_project_result, {})

        assert score == 100.0

    @patch("pypex.core.results_processor.get_config")
    def test_calculate_quality_score_with_errors(
        self, mock_get_config, mock_config, mock_project_result, mock_file_result, mock_entity
    ):
        """Prueba cálculo de score con errores críticos."""
        mock_get_config.return_value = mock_config
        processor = ResultsProcessor()

        # Configurar entidad
        mock_file_result.entities = [mock_entity]
        mock_project_result.files = {"test.py": mock_file_result}

        # Configurar errores críticos
        critical_error = Mock(spec=AnalysisError)
        critical_error.severity = ErrorSeverity.CRITICAL
        mock_project_result.get_all_errors.return_value = [critical_error, critical_error]

        problematic = {"metric1": [mock_entity]}

        score = processor._calculate_quality_score(mock_project_result, problematic)

        # Score base sería 0 (100% problematic), menos 20 por 2 errores críticos
        assert score == 0  # max(0, 0 - 20)

    @patch("pypex.core.results_processor.get_config")
    def test_generate_dynamic_recommendations_list_input(self, mock_get_config, mock_config):
        """Prueba generación de recomendaciones con lista de entidades."""
        mock_get_config.return_value = mock_config
        processor = ResultsProcessor()

        problematic = {"cyclomatic_complexity": [Mock(), Mock()], "cognitive_complexity": [Mock()]}

        recommendations = processor._generate_dynamic_recommendations(problematic)

        assert len(recommendations) >= 2
        assert any("complejidad ciclomática" in rec.lower() for rec in recommendations)
        assert any("complejidad cognitiva" in rec.lower() for rec in recommendations)

    @patch("pypex.core.results_processor.get_config")
    def test_generate_dynamic_recommendations_int_input(self, mock_get_config, mock_config):
        """Prueba generación de recomendaciones con conteos enteros."""
        mock_get_config.return_value = mock_config
        processor = ResultsProcessor()

        problematic = {
            "cyclomatic_complexity": 5,
            "cognitive_complexity": 3,
            "fan_in_out": 0,  # Debe ignorarse
        }

        recommendations = processor._generate_dynamic_recommendations(problematic)

        assert len(recommendations) >= 2
        assert any("5" in rec for rec in recommendations)
        assert any("3" in rec for rec in recommendations)

    @patch("pypex.core.results_processor.get_config")
    def test_generate_dynamic_recommendations_many_issues(self, mock_get_config, mock_config):
        """Prueba recomendación general cuando hay muchos problemas."""
        mock_get_config.return_value = mock_config
        processor = ResultsProcessor()

        problematic = {"cyclomatic_complexity": 6, "cognitive_complexity": 5}

        recommendations = processor._generate_dynamic_recommendations(problematic)

        # Total issues = 11 > 10, debe incluir recomendación general
        assert any("11" in rec and "proceso de revisión" in rec.lower() for rec in recommendations)

    @patch("pypex.core.results_processor.get_config")
    def test_create_performance_report(
        self, mock_get_config, mock_config, mock_project_result, mock_file_result
    ):
        """Prueba creación de reporte de rendimiento."""
        mock_get_config.return_value = mock_config
        processor = ResultsProcessor()

        # Configurar datos de proyecto
        mock_project_result.files = {"test1.py": mock_file_result, "test2.py": mock_file_result}
        mock_project_result.successful_files = 2
        mock_project_result.failed_files = 0
        mock_project_result.analysis_time_ms = 2000
        mock_project_result.total_lines_of_code = 200

        error_file_result = Mock(spec=FileAnalysisResult)
        error_file_result.errors = [Mock()]
        error_file_result.line_count = 50  # Add missing line_count
        mock_project_result.files["error.py"] = error_file_result

        report = processor.create_performance_report(mock_project_result)

        assert report["analysis_performance"]["total_analysis_time_ms"] == 2000
        assert report["analysis_performance"]["total_files_processed"] == 3
        assert report["analysis_performance"]["successful_files"] == 2
        assert report["analysis_performance"]["failed_files"] == 0
        assert report["analysis_performance"]["success_rate_percent"] == (2 / 3 * 100)
        assert report["file_statistics"]["files_with_errors"] == 1

    @patch("pypex.core.results_processor.get_config")
    def test_create_performance_report_no_files(
        self, mock_get_config, mock_config, mock_project_result
    ):
        """Prueba reporte de rendimiento sin archivos."""
        mock_get_config.return_value = mock_config
        processor = ResultsProcessor()

        mock_project_result.files = {}
        mock_project_result.total_lines_of_code = 0

        report = processor.create_performance_report(mock_project_result)

        assert report["analysis_performance"]["success_rate_percent"] == 0
        assert report["file_statistics"]["average_file_size_lines"] == 0

    @patch("pypex.core.results_processor.get_config")
    def test_get_top_entities_by_metric(
        self, mock_get_config, mock_config, mock_project_result, mock_file_result
    ):
        """Prueba obtención de entidades top por métrica."""
        mock_get_config.return_value = mock_config
        processor = ResultsProcessor()

        # Crear múltiples entidades con valores diferentes
        entities = []
        for i, value in enumerate([30, 10, 20]):
            entity = Mock(spec=EntityAnalysisResult)
            entity.source_info = {}
            entity.name = f"function_{i}"
            entity.entity_type = "function"
            entity.children = []
            metrics = Mock(spec=MetricsResult)
            metrics.get_metric_value.return_value = value
            entity.metrics = metrics
            entities.append(entity)

        mock_file_result.entities = entities
        mock_project_result.files = {"test.py": mock_file_result}

        top_entities = processor.get_top_entities_by_metric(
            mock_project_result, "cyclomatic_complexity", limit=2
        )

        assert len(top_entities) == 2
        assert top_entities[0]["metric_value"] == 30  # Ordenado descendente
        assert top_entities[1]["metric_value"] == 20
        assert top_entities[0]["entity_name"] == "function_0"

    @patch("pypex.core.results_processor.get_config")
    def test_get_top_entities_by_metric_with_children(
        self, mock_get_config, mock_config, mock_project_result, mock_file_result
    ):
        """Prueba obtención de entidades top incluyendo hijos."""
        mock_get_config.return_value = mock_config
        processor = ResultsProcessor()

        # Crear entidad padre con método hijo
        parent_entity = Mock(spec=EntityAnalysisResult)
        parent_entity.source_info = {}
        parent_entity.name = "TestClass"
        parent_entity.entity_type = "class"
        parent_metrics = Mock(spec=MetricsResult)
        parent_metrics.get_metric_value.return_value = 15
        parent_entity.metrics = parent_metrics

        child_entity = Mock(spec=EntityAnalysisResult)

        child_entity.source_info = {}
        child_entity.name = "method_1"
        child_entity.entity_type = "method"
        child_metrics = Mock(spec=MetricsResult)
        child_metrics.get_metric_value.return_value = 25
        child_entity.metrics = child_metrics

        parent_entity.children = [child_entity]

        mock_file_result.entities = [parent_entity]
        mock_project_result.files = {"test.py": mock_file_result}

        top_entities = processor.get_top_entities_by_metric(
            mock_project_result, "cyclomatic_complexity"
        )

        assert len(top_entities) == 2
        assert top_entities[0]["metric_value"] == 25  # Método hijo primero
        assert top_entities[1]["metric_value"] == 15  # Clase padre segundo

    @patch("pypex.core.results_processor.get_config")
    @patch("pypex.core.results_processor.get_threshold_config")
    def test_get_entities_by_threshold_level_success(
        self,
        mock_get_threshold_config,
        mock_get_config,
        mock_config,
        mock_threshold_config,
        mock_project_result,
        mock_file_result,
        mock_entity,
    ):
        """Prueba obtención de entidades por nivel de threshold."""
        mock_get_config.return_value = mock_config
        mock_get_threshold_config.return_value = mock_threshold_config

        processor = ResultsProcessor()

        # Configurar entidad que supera threshold
        mock_entity.metrics.get_metric_value.return_value = 25
        mock_file_result.entities = [mock_entity]
        mock_project_result.files = {"test.py": mock_file_result}

        entities = processor.get_entities_by_threshold_level(
            mock_project_result,
            "cyclomatic_complexity",
            "high",  # threshold = 20
        )

        assert len(entities) == 1
        assert entities[0] == mock_entity

    @patch("pypex.core.results_processor.get_config")
    @patch("pypex.core.results_processor.get_threshold_config")
    def test_get_entities_by_threshold_level_exception_fallback(
        self,
        mock_get_threshold_config,
        mock_get_config,
        mock_config,
        mock_project_result,
        mock_file_result,
        mock_entity,
    ):
        """Prueba fallback cuando falla obtener thresholds."""
        mock_get_config.return_value = mock_config

        threshold_config = Mock()
        threshold_config.get_thresholds.side_effect = Exception("Threshold error")
        mock_get_threshold_config.return_value = threshold_config

        processor = ResultsProcessor()

        # Configurar entidad
        mock_entity.metrics.get_metric_value.return_value = 25
        mock_file_result.entities = [mock_entity]
        mock_project_result.files = {"test.py": mock_file_result}

        entities = processor.get_entities_by_threshold_level(
            mock_project_result,
            "cyclomatic_complexity",
            "high",  # fallback threshold = 20
        )

        assert len(entities) == 1

    @patch("pypex.core.results_processor.get_config")
    @patch("pypex.core.results_processor.get_threshold_config")
    def test_get_entities_with_file_info(
        self,
        mock_get_threshold_config,
        mock_get_config,
        mock_config,
        mock_threshold_config,
        mock_project_result,
        mock_file_result,
        mock_entity,
    ):
        """Prueba obtención de entidades con información de archivo."""
        mock_get_config.return_value = mock_config
        mock_get_threshold_config.return_value = mock_threshold_config

        processor = ResultsProcessor()

        # Configurar entidad
        mock_entity.metrics.get_metric_value.return_value = 25
        mock_file_result.entities = [mock_entity]
        mock_project_result.files = {"test.py": mock_file_result}

        entities_with_file = processor._get_entities_with_file_info(
            mock_project_result, "cyclomatic_complexity", "high"
        )

        assert len(entities_with_file) == 1
        assert entities_with_file[0]["entity"] == mock_entity
        assert entities_with_file[0]["file_path"] == "test.py"
        assert entities_with_file[0]["metric_value"] == 25

    @patch("pypex.core.results_processor.get_config")
    def test_generate_detailed_quality_report_permissive_profile(
        self, mock_get_config, mock_project_result
    ):
        """Prueba que profile 'permissive' retorna None para reporte detallado."""
        mock_config = Mock()
        mock_config.get.return_value = "permissive"
        mock_get_config.return_value = mock_config

        processor = ResultsProcessor()

        result = processor.generate_detailed_quality_report(mock_project_result)

        assert result is None

    @patch("pypex.core.results_processor.get_config")
    @patch("pypex.core.results_processor.get_threshold_config")
    def test_generate_detailed_quality_report_normal_profile(
        self,
        mock_get_threshold_config,
        mock_get_config,
        mock_config,
        mock_threshold_config,
        mock_registry,
        mock_project_result,
        mock_file_result,
        mock_entity,
    ):
        """Prueba reporte detallado con profile 'normal'."""
        mock_config = Mock()
        mock_config.get.return_value = "normal"
        mock_get_config.return_value = mock_config
        mock_get_threshold_config.return_value = mock_threshold_config

        with patch("pypex.metrics.get_registry") as mock_get_registry:
            mock_get_registry.return_value = mock_registry

            processor = ResultsProcessor()

            # Configurar entidad
            mock_entity.metrics.get_metric_value.return_value = 25
            mock_file_result.entities = [mock_entity]
            mock_project_result.files = {"test.py": mock_file_result}

            result = processor.generate_detailed_quality_report(mock_project_result)

            assert result is not None
            assert result["analysis_type"] == "advanced"
            assert result["threshold_profile"] == "normal"
            assert "metrics_analysis" in result

    @patch("pypex.core.results_processor.get_config")
    @patch("pypex.core.results_processor.get_threshold_config")
    def test_generate_detailed_quality_report_with_metric_error(
        self,
        mock_get_threshold_config,
        mock_get_config,
        mock_config,
        mock_threshold_config,
        mock_project_result,
        mock_file_result,
        mock_entity,
    ):
        """Prueba reporte detallado cuando hay error con una métrica."""
        mock_config = Mock()
        mock_config.get.return_value = "strict"
        mock_get_config.return_value = mock_config
        mock_get_threshold_config.return_value = mock_threshold_config

        with patch("pypex.metrics.get_registry") as mock_get_registry:
            mock_registry = Mock()
            mock_registry.get_available_metrics.return_value = ["bad_metric"]
            mock_registry.get_metric.side_effect = Exception("Metric error")
            mock_get_registry.return_value = mock_registry

            processor = ResultsProcessor()

            result = processor.generate_detailed_quality_report(mock_project_result)

            assert result is not None
            assert "bad_metric" in result["metrics_analysis"]
            assert "error" in result["metrics_analysis"]["bad_metric"]

    @patch("pypex.core.results_processor.get_config")
    def test_generate_advanced_recommendations(self, mock_get_config, mock_config):
        """Prueba generación de recomendaciones avanzadas."""
        mock_get_config.return_value = mock_config
        processor = ResultsProcessor()

        detailed_analysis = {
            "cyclomatic_complexity": {"high_complexity_entities": 5, "other_field": "value"},
            "cognitive_complexity": {"high_complexity_entities": 3},
            "invalid_metric": "not_a_dict",
        }

        recommendations = processor._generate_advanced_recommendations(detailed_analysis)

        assert len(recommendations) >= 2
        assert any("5" in rec for rec in recommendations)
        assert any("3" in rec for rec in recommendations)


# Tests adicionales para mejorar coverage


class TestResultsProcessorAdditionalCoverage:
    """Tests adicionales para alcanzar mayor coverage."""

    @patch("pypex.core.results_processor.get_config")
    def test_aggregate_metrics_custom_entity_types(
        self, mock_get_config, mock_config, mock_project_result, mock_file_result
    ):
        """Prueba agregación con tipos de entidad específicos."""
        mock_get_config.return_value = mock_config
        processor = ResultsProcessor()

        # Crear entidades de diferentes tipos
        class_entity = Mock(spec=EntityAnalysisResult)
        class_entity.source_info = {}
        class_entity.entity_type = "class"
        class_entity.children = []
        class_metrics = Mock(spec=MetricsResult)
        class_metrics.get_metric_value.return_value = 5
        class_entity.metrics = class_metrics

        function_entity = Mock(spec=EntityAnalysisResult)

        function_entity.source_info = {}
        function_entity.entity_type = "function"
        function_entity.children = []
        function_metrics = Mock(spec=MetricsResult)
        function_metrics.get_metric_value.return_value = 10
        function_entity.metrics = function_metrics

        mock_file_result.entities = [class_entity, function_entity]
        mock_project_result.files = {"test.py": mock_file_result}

        # Solo incluir clases
        result = processor.aggregate_metrics(
            mock_project_result, "metric", "sum", entity_types=["class"]
        )

        assert result["project_total"] == 5  # Solo la clase

    @patch("pypex.core.results_processor.get_config")
    def test_aggregate_metrics_empty_project(
        self, mock_get_config, mock_config, mock_project_result
    ):
        """Prueba agregación con proyecto vacío."""
        mock_get_config.return_value = mock_config
        processor = ResultsProcessor()

        mock_project_result.files = {}

        result = processor.aggregate_metrics(mock_project_result, "metric", "sum")

        assert result["project_total"] == 0
        assert result["files_count"] == 0
        assert result["average_per_file"] == 0

    @patch("pypex.core.results_processor.get_config")
    def test_check_entity_thresholds_none_value(self, mock_get_config, mock_config):
        """Prueba _check_entity_thresholds con valor None."""
        mock_get_config.return_value = mock_config

        with patch("pypex.metrics.get_registry") as mock_get_registry:
            mock_get_registry.return_value = Mock()

            processor = ResultsProcessor()

            entity = Mock(spec=EntityAnalysisResult)

            entity.source_info = {}
            metrics = Mock(spec=MetricsResult)
            metrics.get_metric_value.return_value = None
            entity.metrics = metrics

            thresholds = {"test_metric": 20}
            problematic = {"test_metric": []}

            processor._check_entity_thresholds(entity, thresholds, problematic)

            assert len(problematic["test_metric"]) == 0

    @patch("pypex.core.results_processor.get_config")
    def test_check_entity_thresholds_non_numeric_value(self, mock_get_config, mock_config):
        """Prueba _check_entity_thresholds con valor no numérico."""
        mock_get_config.return_value = mock_config

        with patch("pypex.metrics.get_registry") as mock_get_registry:
            mock_get_registry.return_value = Mock()

            processor = ResultsProcessor()

            entity = Mock(spec=EntityAnalysisResult)

            entity.source_info = {}
            metrics = Mock(spec=MetricsResult)
            metrics.get_metric_value.return_value = "not_a_number"
            entity.metrics = metrics

            thresholds = {"test_metric": 20}
            problematic = {"test_metric": []}

            processor._check_entity_thresholds(entity, thresholds, problematic)

            assert len(problematic["test_metric"]) == 0

    @patch("pypex.core.results_processor.get_config")
    @patch("pypex.core.results_processor.get_threshold_config")
    def test_get_quality_metrics_config_all_levels(
        self,
        mock_get_threshold_config,
        mock_get_config,
        mock_config,
        mock_threshold_config,
        mock_registry,
    ):
        """Prueba obtención de configuración para todos los niveles."""
        mock_get_config.return_value = mock_config
        mock_get_threshold_config.return_value = mock_threshold_config

        with patch("pypex.metrics.get_registry") as mock_get_registry:
            mock_get_registry.return_value = mock_registry

            processor = ResultsProcessor()

            # Test todos los niveles
            for level in ["low", "medium", "high"]:
                config = processor._get_quality_metrics_config(level)
                assert "cyclomatic_complexity" in config

    @patch("pypex.core.results_processor.get_config")
    def test_calculate_quality_score_partial_problematic(
        self, mock_get_config, mock_config, mock_project_result, mock_file_result
    ):
        """Prueba cálculo de score con algunas entidades problemáticas."""
        mock_get_config.return_value = mock_config
        processor = ResultsProcessor()

        # Crear múltiples entidades
        entities = []
        for _ in range(10):
            entity = Mock(spec=EntityAnalysisResult)
            entity.source_info = {}
            entity.children = []
            entities.append(entity)

        mock_file_result.entities = entities
        mock_project_result.files = {"test.py": mock_file_result}

        # 3 de 10 son problemáticas (30%)
        problematic = {"metric1": entities[:3]}

        score = processor._calculate_quality_score(mock_project_result, problematic)

        # Score base: 100 - (3/10 * 100) = 70
        assert score == 70.0

    @patch("pypex.core.results_processor.get_config")
    def test_generate_dynamic_recommendations_empty_input(self, mock_get_config, mock_config):
        """Prueba recomendaciones con entrada vacía."""
        mock_get_config.return_value = mock_config
        processor = ResultsProcessor()

        problematic = {}

        recommendations = processor._generate_dynamic_recommendations(problematic)

        # Debe retornar lista vacía pero no fallar
        assert isinstance(recommendations, list)

    @patch("pypex.core.results_processor.get_config")
    def test_generate_dynamic_recommendations_unknown_metric(self, mock_get_config, mock_config):
        """Prueba recomendaciones con métrica desconocida."""
        mock_get_config.return_value = mock_config
        processor = ResultsProcessor()

        problematic = {"unknown_metric": [Mock(), Mock(), Mock()]}

        recommendations = processor._generate_dynamic_recommendations(problematic)

        assert len(recommendations) >= 1
        # Para métricas desconocidas, se reemplaza _ con espacio en la descripción
        assert any("unknown metric" in rec for rec in recommendations)

    @patch("pypex.core.results_processor.get_config")
    def test_get_top_entities_by_metric_none_values(
        self, mock_get_config, mock_config, mock_project_result, mock_file_result
    ):
        """Prueba obtención de top entities con valores None."""
        mock_get_config.return_value = mock_config
        processor = ResultsProcessor()

        # Entidad con valor None (debe ignorarse)
        entity_none = Mock(spec=EntityAnalysisResult)
        entity_none.source_info = {}
        entity_none.entity_type = "function"
        entity_none.children = []
        metrics_none = Mock(spec=MetricsResult)
        metrics_none.get_metric_value.return_value = None
        entity_none.metrics = metrics_none

        # Entidad con valor válido
        entity_valid = Mock(spec=EntityAnalysisResult)
        entity_valid.source_info = {}
        entity_valid.name = "valid_function"
        entity_valid.entity_type = "function"
        entity_valid.children = []
        metrics_valid = Mock(spec=MetricsResult)
        metrics_valid.get_metric_value.return_value = 15
        entity_valid.metrics = metrics_valid

        mock_file_result.entities = [entity_none, entity_valid]
        mock_project_result.files = {"test.py": mock_file_result}

        top_entities = processor.get_top_entities_by_metric(
            mock_project_result, "cyclomatic_complexity"
        )

        # Solo debe incluir la entidad válida
        assert len(top_entities) == 1
        assert top_entities[0]["entity_name"] == "valid_function"

    @patch("pypex.core.results_processor.get_config")
    @patch("pypex.core.results_processor.get_threshold_config")
    def test_get_entities_by_threshold_level_all_levels(
        self,
        mock_get_threshold_config,
        mock_get_config,
        mock_config,
        mock_threshold_config,
        mock_project_result,
        mock_file_result,
    ):
        """Prueba obtención de entidades para todos los niveles de threshold."""
        mock_get_config.return_value = mock_config
        mock_get_threshold_config.return_value = mock_threshold_config

        processor = ResultsProcessor()

        # Crear entidad mock manualmente para este test
        test_entity = Mock(spec=EntityAnalysisResult)
        test_entity.source_info = {}
        test_entity.children = []
        test_metrics = Mock(spec=MetricsResult)
        test_metrics.get_metric_value.return_value = 25
        test_entity.metrics = test_metrics

        mock_file_result.entities = [test_entity]
        mock_project_result.files = {"test.py": mock_file_result}

        # Test todos los niveles
        for level in ["low", "medium", "high", "very_high"]:
            entities = processor.get_entities_by_threshold_level(
                mock_project_result, "cyclomatic_complexity", level
            )
            # Todas deberían incluir la entidad ya que tiene valor 25 > todos los thresholds
            assert len(entities) == 1

    @patch("pypex.core.results_processor.get_config")
    @patch("pypex.core.results_processor.get_threshold_config")
    def test_get_entities_with_file_info_all_levels(
        self,
        mock_get_threshold_config,
        mock_get_config,
        mock_config,
        mock_threshold_config,
        mock_project_result,
        mock_file_result,
        mock_entity,
    ):
        """Prueba obtención de entidades con info de archivo para todos los niveles."""
        mock_get_config.return_value = mock_config
        mock_get_threshold_config.return_value = mock_threshold_config

        processor = ResultsProcessor()

        # Configurar entidad
        mock_entity.metrics.get_metric_value.return_value = 25
        mock_file_result.entities = [mock_entity]
        mock_project_result.files = {"test.py": mock_file_result}

        # Test todos los niveles
        for level in ["low", "medium", "high", "very_high"]:
            entities_with_file = processor._get_entities_with_file_info(
                mock_project_result, "cyclomatic_complexity", level
            )

            assert len(entities_with_file) == 1
            assert entities_with_file[0]["entity"] == mock_entity

    @patch("pypex.core.results_processor.get_config")
    @patch("pypex.core.results_processor.get_threshold_config")
    def test_generate_detailed_quality_report_strict_profile(
        self,
        mock_get_threshold_config,
        mock_get_config,
        mock_config,
        mock_threshold_config,
        mock_registry,
        mock_project_result,
        mock_file_result,
        mock_entity,
    ):
        """Prueba reporte detallado con profile 'strict'."""
        mock_config = Mock()
        mock_config.get.return_value = "strict"
        mock_get_config.return_value = mock_config
        mock_get_threshold_config.return_value = mock_threshold_config

        with patch("pypex.metrics.get_registry") as mock_get_registry:
            mock_get_registry.return_value = mock_registry

            processor = ResultsProcessor()

            # Configurar entidad
            mock_entity.metrics.get_metric_value.return_value = 25
            mock_file_result.entities = [mock_entity]
            mock_project_result.files = {"test.py": mock_file_result}

            result = processor.generate_detailed_quality_report(mock_project_result)

            assert result is not None
            assert result["analysis_type"] == "advanced"
            assert result["threshold_profile"] == "strict"

    @patch("pypex.core.results_processor.get_config")
    def test_create_performance_report_max_file_size(
        self, mock_get_config, mock_config, mock_project_result
    ):
        """Prueba reporte de rendimiento con archivos de diferentes tamaños."""
        mock_get_config.return_value = mock_config
        processor = ResultsProcessor()

        # Crear archivos con diferentes tamaños
        file1 = Mock(spec=FileAnalysisResult)
        file1.line_count = 50
        file1.errors = []

        file2 = Mock(spec=FileAnalysisResult)
        file2.line_count = 200  # Archivo más grande
        file2.errors = []

        file3 = Mock(spec=FileAnalysisResult)
        file3.line_count = 100
        file3.errors = []

        mock_project_result.files = {"file1.py": file1, "file2.py": file2, "file3.py": file3}
        mock_project_result.total_lines_of_code = 350

        report = processor.create_performance_report(mock_project_result)

        assert report["file_statistics"]["largest_file_lines"] == 200
        assert report["file_statistics"]["average_file_size_lines"] == (350 / 3)

    @patch("pypex.core.results_processor.get_config")
    def test_get_top_entities_by_metric_sorted_correctly(
        self, mock_get_config, mock_config, mock_project_result, mock_file_result
    ):
        """Prueba que las entidades se ordenan correctamente por valor de métrica."""
        mock_get_config.return_value = mock_config
        processor = ResultsProcessor()

        # Crear entidades con valores en orden no secuencial
        values = [15, 30, 5, 25, 10]
        entities = []

        for i, value in enumerate(values):
            entity = Mock(spec=EntityAnalysisResult)
            entity.source_info = {}
            entity.name = f"entity_{i}"
            entity.entity_type = "function"
            entity.children = []
            metrics = Mock(spec=MetricsResult)
            metrics.get_metric_value.return_value = value
            entity.metrics = metrics
            entities.append(entity)

        mock_file_result.entities = entities
        mock_project_result.files = {"test.py": mock_file_result}

        top_entities = processor.get_top_entities_by_metric(mock_project_result, "metric", limit=3)

        # Debe estar ordenado descendente: 30, 25, 15
        assert len(top_entities) == 3
        assert top_entities[0]["metric_value"] == 30
        assert top_entities[1]["metric_value"] == 25
        assert top_entities[2]["metric_value"] == 15

    @patch("pypex.core.results_processor.get_config")
    @patch("pypex.core.results_processor.get_threshold_config")
    def test_get_entities_by_threshold_level_sorted(
        self,
        mock_get_threshold_config,
        mock_get_config,
        mock_config,
        mock_threshold_config,
        mock_project_result,
        mock_file_result,
    ):
        """Prueba que las entidades problemáticas se ordenan por valor."""
        mock_get_config.return_value = mock_config
        mock_get_threshold_config.return_value = mock_threshold_config

        processor = ResultsProcessor()

        # Crear entidades con valores diferentes por encima del threshold
        values = [25, 35, 30]  # Todos > 20 (threshold high)
        entities = []

        for value in values:
            entity = Mock(spec=EntityAnalysisResult)
            entity.source_info = {}
            entity.children = []
            metrics = Mock(spec=MetricsResult)
            metrics.get_metric_value.return_value = value
            entity.metrics = metrics
            entities.append(entity)

        mock_file_result.entities = entities
        mock_project_result.files = {"test.py": mock_file_result}

        problematic_entities = processor.get_entities_by_threshold_level(
            mock_project_result, "cyclomatic_complexity", "high"
        )

        # Debe estar ordenado descendente: 35, 30, 25
        assert len(problematic_entities) == 3
        assert problematic_entities[0].metrics.get_metric_value.return_value == 35
        assert problematic_entities[1].metrics.get_metric_value.return_value == 30
        assert problematic_entities[2].metrics.get_metric_value.return_value == 25


def _entity(name, entity_type, value, line_start=1, children=None):
    """Crea una entidad real con un único valor de complejidad ciclomática."""
    return EntityAnalysisResult(
        name=name,
        entity_type=entity_type,
        metrics=MetricsResult(
            entity_name=name,
            entity_type=entity_type,
            metrics={"cyclomatic_complexity": value},
        ),
        children=children or [],
        source_info={"line_start": line_start, "line_end": line_start + 5},
    )


def _project_with_entities():
    """Proyecto con un fichero vacío y una clase que no es la última entidad."""
    empty = FileAnalysisResult(
        file_path="pkg/__init__.py", module_name="pkg", file_size=0, line_count=0
    )
    module = FileAnalysisResult(
        file_path="pkg/module.py",
        module_name="pkg.module",
        file_size=100,
        line_count=40,
        entities=[
            _entity("Service", "class", 3, 1, [_entity("run", "method", 9, 3)]),
            _entity("helper", "function", 4, 30),
        ],
    )
    return ProjectAnalysisResult(
        project_name="pkg",
        root_path="pkg",
        analysis_timestamp="2026-01-01T00:00:00",
        files={"pkg/__init__.py": empty, "pkg/module.py": module},
    )


class TestGetTopEntitiesByMetricRegression:
    """Regresión: entidades vacías y métodos de clases que no son la última entidad."""

    def test_includes_methods_of_every_class_and_skips_empty_files(self):
        top = ResultsProcessor().get_top_entities_by_metric(
            _project_with_entities(), "cyclomatic_complexity"
        )

        assert [e["entity_name"] for e in top] == ["Service.run", "helper", "Service"]
        assert top[0] == {
            "entity_name": "Service.run",
            "entity_type": "method",
            "file_path": "pkg/module.py",
            "line_start": 3,
            "metric_value": 9,
        }

    def test_filters_by_entity_type(self):
        top = ResultsProcessor().get_top_entities_by_metric(
            _project_with_entities(),
            "cyclomatic_complexity",
            entity_types=["function", "method"],
        )

        assert [e["entity_name"] for e in top] == ["Service.run", "helper"]


class TestCreateProjectReport:
    """Distribuciones y totales usados por el reporter de consola."""

    def test_distributions_and_totals(self):
        project = _project_with_entities()
        project.files["pkg/big.py"] = FileAnalysisResult(
            file_path="pkg/big.py",
            module_name="pkg.big",
            file_size=0,
            line_count=600,
            entities=[_entity("tangled", "function", 25)],
        )
        project.total_lines_of_code = 640

        report = ResultsProcessor().create_project_report(project)

        assert report["file_size_distribution"] == {"small": 2, "medium": 0, "large": 1}
        # Umbrales por defecto de complejidad ciclomática: low=10, medium=20
        assert report["complexity_distribution"] == {"low": 2, "medium": 0, "high": 1}
        assert report["totals"] == {
            "cyclomatic_complexity": 9 + 4 + 25,
            "cognitive_complexity": 0,
            "lines_of_code": 640,
        }
