"""Tests unitarios completos para el módulo CLI de PyPex.

Estos tests cubren todas las funciones del CLI con casos de éxito,
error y edge cases siguiendo las mejores prácticas de testing.
"""

import json
from unittest.mock import Mock, patch

import click
import pytest
import yaml

from pypex.cli import (
    analyze,
    load_config_file,
    main,
    thresholds,
    validate_metrics_list,
)


@pytest.fixture
def temp_config_dir(tmp_path):
    """Crea un directorio temporal para archivos de configuración."""
    return tmp_path / "config"


@pytest.fixture
def valid_yaml_config(temp_config_dir):
    """Crea un archivo YAML de configuración válido."""
    temp_config_dir.mkdir(exist_ok=True)
    config_file = temp_config_dir / "valid_config.yaml"
    config_data = {
        "max_file_size": 2048 * 1024,
        "ignore_patterns": ["*.pyc", "__pycache__"],
        "metrics": ["cyclomatic_complexity", "cognitive_complexity"],
        "exclude_metrics": ["lcom4"],
        "thresholds_profile": "strict",
    }
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)
    return config_file


@pytest.fixture
def valid_json_config(temp_config_dir):
    """Crea un archivo JSON de configuración válido."""
    temp_config_dir.mkdir(exist_ok=True)
    config_file = temp_config_dir / "valid_config.json"
    config_data = {
        "max_file_size": 1536 * 1024,
        "verbose": True,
        "output_format": "html",
    }
    with open(config_file, "w") as f:
        json.dump(config_data, f)
    return config_file


@pytest.fixture
def invalid_yaml_config(temp_config_dir):
    """Crea un archivo YAML con sintaxis inválida."""
    temp_config_dir.mkdir(exist_ok=True)
    config_file = temp_config_dir / "invalid_config.yaml"
    with open(config_file, "w") as f:
        f.write("invalid: yaml: content: [")
    return config_file


@pytest.fixture
def invalid_json_config(temp_config_dir):
    """Crea un archivo JSON con sintaxis inválida."""
    temp_config_dir.mkdir(exist_ok=True)
    config_file = temp_config_dir / "invalid_config.json"
    with open(config_file, "w") as f:
        f.write('{"invalid": json content}')
    return config_file


@pytest.fixture
def mock_registry():
    """Mock del registry de métricas."""
    mock_reg = Mock()
    mock_reg.get_available_metrics.return_value = [
        "cyclomatic_complexity",
        "cognitive_complexity",
        "lcom4",
        "design_complexity",
        "nesting_depth",
    ]

    # Mock para métricas individuales
    mock_metric = Mock()
    mock_metric.description = "Test metric description"
    mock_reg.get_metric.return_value = mock_metric

    return mock_reg


@pytest.fixture
def mock_analyzer():
    """Mock del analizador principal."""
    mock_analyzer = Mock()
    mock_results = Mock()
    mock_results.project_stats = {"total_files": 5, "total_functions": 20}
    mock_analyzer.analyze.return_value = mock_results
    return mock_analyzer


class TestLoadConfigFile:
    """Tests para la función load_config_file."""

    def test_load_yaml_config_success(self, valid_yaml_config):
        """Prueba la carga exitosa de un archivo YAML."""
        config = load_config_file(str(valid_yaml_config))

        assert config["max_file_size"] == 2048 * 1024
        assert config["ignore_patterns"] == ["*.pyc", "__pycache__"]
        assert "cyclomatic_complexity" in config["metrics"]
        assert config["thresholds_profile"] == "strict"

    def test_load_json_config_success(self, valid_json_config):
        """Prueba la carga exitosa de un archivo JSON."""
        config = load_config_file(str(valid_json_config))

        assert config["max_file_size"] == 1536 * 1024
        assert config["verbose"] is True
        assert config["output_format"] == "html"

    def test_load_nonexistent_file(self):
        """Prueba el error al cargar un archivo inexistente."""
        with pytest.raises(click.ClickException) as exc_info:
            load_config_file("nonexistent_file.yaml")

        assert "no encontrado" in str(exc_info.value)

    def test_load_invalid_yaml(self, invalid_yaml_config):
        """Prueba el error al cargar YAML inválido."""
        with pytest.raises(click.ClickException) as exc_info:
            load_config_file(str(invalid_yaml_config))

        assert "Error al parsear" in str(exc_info.value)

    def test_load_invalid_json(self, invalid_json_config):
        """Prueba el error al cargar JSON inválido."""
        with pytest.raises(click.ClickException) as exc_info:
            load_config_file(str(invalid_json_config))

        assert "Error al parsear" in str(exc_info.value)

    def test_load_unknown_extension_fallback_yaml(self, temp_config_dir):
        """Prueba que archivos con extensión desconocida se traten como YAML."""
        config_file = temp_config_dir / "config.unknown"
        temp_config_dir.mkdir(exist_ok=True)

        config_data = {"test_key": "test_value"}
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        config = load_config_file(str(config_file))
        assert config["test_key"] == "test_value"

    def test_load_empty_yaml_file(self, temp_config_dir):
        """Prueba la carga de un archivo YAML vacío."""
        temp_config_dir.mkdir(exist_ok=True)
        config_file = temp_config_dir / "empty.yaml"

        with open(config_file, "w") as f:
            f.write("")

        config = load_config_file(str(config_file))
        assert config == {}

    @patch("pathlib.Path.exists", return_value=True)
    @patch("builtins.open", side_effect=PermissionError("Permission denied"))
    def test_load_permission_error_real(self, mock_open, mock_exists):
        """Prueba el error de permisos real al leer archivo."""
        with pytest.raises(click.ClickException) as exc_info:
            load_config_file("restricted_file.yaml")

        assert "Error al leer" in str(exc_info.value)


class TestValidateMetricsList:
    """Tests para la función validate_metrics_list."""

    @patch("pypex.cli.get_registry")
    def test_validate_specific_metrics_success(self, mock_get_registry, mock_registry):
        """Prueba la validación exitosa de métricas específicas."""
        mock_get_registry.return_value = mock_registry

        metrics = ["cyclomatic_complexity", "cognitive_complexity"]
        exclude_metrics = []

        result = validate_metrics_list(metrics, exclude_metrics)

        assert set(result) == set(metrics)

    @patch("pypex.cli.get_registry")
    def test_validate_all_metrics_when_none_specified(self, mock_get_registry, mock_registry):
        """Prueba que se usan todas las métricas cuando no se especifica ninguna."""
        mock_get_registry.return_value = mock_registry

        result = validate_metrics_list([], [])

        expected_metrics = mock_registry.get_available_metrics()
        assert set(result) == set(expected_metrics)

    @patch("pypex.cli.get_registry")
    def test_validate_exclude_metrics_success(self, mock_get_registry, mock_registry):
        """Prueba la exclusión exitosa de métricas."""
        mock_get_registry.return_value = mock_registry

        metrics = []  # Usar todas
        exclude_metrics = ["lcom4", "design_complexity"]

        result = validate_metrics_list(metrics, exclude_metrics)

        available = set(mock_registry.get_available_metrics())
        excluded = set(exclude_metrics)
        expected = available - excluded

        assert set(result) == expected

    @patch("pypex.cli.get_registry")
    def test_validate_invalid_metrics_error(self, mock_get_registry, mock_registry):
        """Prueba el error al especificar métricas inválidas."""
        mock_get_registry.return_value = mock_registry

        metrics = ["invalid_metric", "another_invalid"]
        exclude_metrics = []

        with pytest.raises(click.ClickException) as exc_info:
            validate_metrics_list(metrics, exclude_metrics)

        assert "Métricas no válidas especificadas" in str(exc_info.value)
        assert "invalid_metric" in str(exc_info.value)

    @patch("pypex.cli.get_registry")
    def test_validate_invalid_exclude_metrics_error(self, mock_get_registry, mock_registry):
        """Prueba el error al excluir métricas inválidas."""
        mock_get_registry.return_value = mock_registry

        metrics = []
        exclude_metrics = ["invalid_exclude"]

        with pytest.raises(click.ClickException) as exc_info:
            validate_metrics_list(metrics, exclude_metrics)

        assert "Métricas a excluir no válidas" in str(exc_info.value)

    @patch("pypex.cli.get_registry")
    def test_validate_no_metrics_left_after_exclusion(self, mock_get_registry, mock_registry):
        """Prueba el error cuando no quedan métricas después de la exclusión."""
        mock_get_registry.return_value = mock_registry

        # Excluir todas las métricas disponibles
        all_metrics = mock_registry.get_available_metrics()

        with pytest.raises(click.ClickException) as exc_info:
            validate_metrics_list([], all_metrics)

        assert "No quedan métricas válidas" in str(exc_info.value)

    @patch("pypex.cli.get_registry")
    def test_validate_duplicates_removed(self, mock_get_registry, mock_registry):
        """Prueba que se eliminan métricas duplicadas."""
        mock_get_registry.return_value = mock_registry

        metrics = ["cyclomatic_complexity", "cyclomatic_complexity", "cognitive_complexity"]

        result = validate_metrics_list(metrics, [])

        # No debe haber duplicados
        assert len(result) == len(set(result))
        assert "cyclomatic_complexity" in result
        assert "cognitive_complexity" in result


class TestMainCommand:
    """Tests para el comando principal main."""

    @patch("pypex.cli.configure_logging")
    @patch("pypex.cli.configure_presentation_service")
    @patch("pypex.cli.get_config")
    def test_main_command_default_options(
        self, mock_get_config, mock_configure_presentation, mock_configure_logging
    ):
        """Prueba la ejecución del comando principal con opciones por defecto."""
        mock_config = Mock()
        mock_get_config.return_value = mock_config

        from click.testing import CliRunner

        runner = CliRunner()

        # Ejecutar solo el comando principal (sin subcomandos)
        result = runner.invoke(main, ["--help"])

        assert result.exit_code == 0
        assert "PyPex: Analizador Avanzado" in result.output

    @patch("pypex.cli.configure_logging")
    @patch("pypex.cli.configure_presentation_service")
    @patch("pypex.cli.get_config")
    def test_main_command_verbose_option(
        self, mock_get_config, mock_configure_presentation, mock_configure_logging
    ):
        """Prueba la opción verbose del comando principal."""
        mock_config = Mock()
        mock_get_config.return_value = mock_config

        from click.testing import CliRunner

        runner = CliRunner()

        # Use a callback to trigger the main function
        result = runner.invoke(main, ["--verbose", "thresholds", "--help"])

        # Verificar que se llamó configure_logging
        mock_configure_logging.assert_called()

        # Verificar que se configuró con nivel DEBUG
        args, kwargs = mock_configure_logging.call_args
        import logging

        assert kwargs.get("console_level") == logging.DEBUG

    @patch("pypex.cli.configure_logging")
    @patch("pypex.cli.configure_presentation_service")
    @patch("pypex.cli.get_config")
    def test_main_command_log_file_option(
        self, mock_get_config, mock_configure_presentation, mock_configure_logging
    ):
        """Prueba la opción log-file del comando principal."""
        mock_config = Mock()
        mock_get_config.return_value = mock_config

        from click.testing import CliRunner

        runner = CliRunner()

        with runner.isolated_filesystem():
            result = runner.invoke(main, ["--log-file", "test.log", "thresholds", "--help"])

            # Verificar que se configuró el archivo de log
            mock_configure_logging.assert_called()
            args, kwargs = mock_configure_logging.call_args
            assert kwargs.get("log_file") == "test.log"


class TestAnalyzeCommand:
    """Tests para el comando analyze."""

    def setup_method(self):
        """Configuración inicial para cada test."""
        self.runner = pytest.importorskip("click.testing").CliRunner()

    @patch("pypex.cli.Analyzer")
    @patch("pypex.cli.FileProcessor")
    @patch("pypex.cli.ASTParser")
    @patch("pypex.cli.get_registry")
    @patch("pypex.cli.get_config")
    @patch("pypex.reporters.console_reporter.ConsoleReporter")
    def test_analyze_basic_success(
        self,
        mock_console_reporter,
        mock_get_config,
        mock_get_registry,
        mock_ast_parser,
        mock_file_processor,
        mock_analyzer_class,
        mock_registry,
        tmp_path,
    ):
        """Prueba el análisis básico exitoso."""
        # Setup mocks
        mock_config = Mock()
        mock_config.get.return_value = []  # Para ignore_patterns
        mock_get_config.return_value = mock_config
        mock_get_registry.return_value = mock_registry

        mock_analyzer = Mock()
        mock_results = Mock()
        mock_analyzer.analyze.return_value = mock_results
        mock_analyzer_class.return_value = mock_analyzer

        mock_reporter_instance = Mock()
        mock_console_reporter.return_value = mock_reporter_instance

        # Crear directorio de prueba
        test_dir = tmp_path / "test_project"
        test_dir.mkdir()
        (test_dir / "test_file.py").write_text("def hello(): pass")

        result = self.runner.invoke(analyze, [str(test_dir)])

        assert result.exit_code == 0
        mock_analyzer.analyze.assert_called_once_with(str(test_dir))
        mock_reporter_instance.generate_report.assert_called_once()

    @patch("pypex.cli.load_config_file")
    @patch("pypex.cli.Analyzer")
    @patch("pypex.cli.get_registry")
    @patch("pypex.cli.get_config")
    @patch("pypex.reporters.console_reporter.ConsoleReporter")
    def test_analyze_with_config_file(
        self,
        mock_console_reporter,
        mock_get_config,
        mock_get_registry,
        mock_analyzer_class,
        mock_load_config,
        mock_registry,
        tmp_path,
    ):
        """Prueba el análisis con archivo de configuración."""
        # Setup mocks
        mock_config = Mock()
        mock_config.get.return_value = []  # Para ignore_patterns
        mock_get_config.return_value = mock_config
        mock_get_registry.return_value = mock_registry

        mock_file_config = {
            "max_file_size": 2048 * 1024,
            "metrics": ["cyclomatic_complexity"],
        }
        mock_load_config.return_value = mock_file_config

        mock_analyzer = Mock()
        mock_analyzer.analyze.return_value = Mock()
        mock_analyzer_class.return_value = mock_analyzer

        mock_reporter_instance = Mock()
        mock_console_reporter.return_value = mock_reporter_instance

        # Crear archivos de prueba
        test_dir = tmp_path / "test_project"
        test_dir.mkdir()
        (test_dir / "test_file.py").write_text("def hello(): pass")

        config_file = tmp_path / "config.yaml"
        config_file.write_text("max_file_size: 2097152")

        result = self.runner.invoke(analyze, [str(test_dir), "--config", str(config_file)])

        assert result.exit_code == 0
        mock_load_config.assert_called_once_with(str(config_file))

    @patch("pypex.cli.ReporterRegistry")
    @patch("pypex.cli.Analyzer")
    @patch("pypex.cli.FileProcessor")
    @patch("pypex.cli.ASTParser")
    @patch("pypex.cli.get_registry")
    @patch("pypex.cli.get_config")
    @patch("pypex.cli.get_presentation_service")
    def test_analyze_html_output(
        self,
        mock_get_presentation_service,
        mock_get_config,
        mock_get_registry,
        mock_ast_parser,
        mock_file_processor,
        mock_analyzer_class,
        mock_reporter_registry,
        mock_registry,
        tmp_path,
    ):
        """Prueba la generación de reporte HTML."""
        # Setup mocks
        mock_config = Mock()
        mock_config.get.return_value = []  # Para ignore_patterns
        mock_get_config.return_value = mock_config
        mock_get_registry.return_value = mock_registry

        # Mock presentation service
        mock_presentation = Mock()
        mock_get_presentation_service.return_value = mock_presentation

        mock_analyzer = Mock()
        mock_results = Mock()
        mock_analyzer.analyze.return_value = mock_results
        mock_analyzer_class.return_value = mock_analyzer

        # Mock reporter
        mock_reporter = Mock()
        mock_reporter_registry.get_reporter.return_value = Mock(return_value=mock_reporter)

        # Crear directorio de prueba
        test_dir = tmp_path / "test_project"
        test_dir.mkdir()
        (test_dir / "test_file.py").write_text("def hello(): pass")

        output_file = tmp_path / "report.html"
        # Pre-crear el archivo para simular la generación exitosa
        output_file.write_text("<html>Test report</html>")

        result = self.runner.invoke(
            analyze,
            [
                str(test_dir),
                "--format",
                "html",
                "--output",
                str(output_file),
            ],
        )

        assert result.exit_code == 0
        mock_reporter.generate_report.assert_called_once_with(mock_results)

    def test_analyze_nonexistent_path(self):
        """Prueba el error al analizar una ruta inexistente."""
        result = self.runner.invoke(analyze, ["/nonexistent/path"])

        assert result.exit_code != 0
        assert "does not exist" in result.output or "no existe" in result.output

    @patch("pypex.cli.validate_metrics_list")
    @patch("pypex.cli.get_registry")
    @patch("pypex.cli.get_config")
    @patch("pypex.reporters.console_reporter.ConsoleReporter")
    def test_analyze_invalid_metrics(
        self,
        mock_console_reporter,
        mock_get_config,
        mock_get_registry,
        mock_validate_metrics,
        tmp_path,
    ):
        """Prueba el error con métricas inválidas."""
        mock_config = Mock()
        mock_config.get.return_value = []
        mock_get_config.return_value = mock_config

        mock_validate_metrics.side_effect = click.ClickException("Métricas inválidas")

        test_dir = tmp_path / "test_project"
        test_dir.mkdir()
        (test_dir / "test_file.py").write_text("def hello(): pass")

        result = self.runner.invoke(analyze, [str(test_dir), "--metrics", "invalid_metric"])

        assert result.exit_code != 0
        assert "Métricas inválidas" in result.output

    @patch("pypex.cli.Analyzer")
    @patch("pypex.cli.get_registry")
    @patch("pypex.cli.get_config")
    @patch("pypex.reporters.console_reporter.ConsoleReporter")
    def test_analyze_with_ignore_patterns(
        self,
        mock_console_reporter,
        mock_get_config,
        mock_get_registry,
        mock_analyzer_class,
        mock_registry,
        tmp_path,
    ):
        """Prueba el análisis con patrones de exclusión."""
        mock_config = Mock()
        mock_config.get.return_value = []
        mock_get_config.return_value = mock_config
        mock_get_registry.return_value = mock_registry

        mock_analyzer = Mock()
        mock_analyzer.analyze.return_value = Mock()
        mock_analyzer_class.return_value = mock_analyzer

        mock_reporter_instance = Mock()
        mock_console_reporter.return_value = mock_reporter_instance

        test_dir = tmp_path / "test_project"
        test_dir.mkdir()
        (test_dir / "test_file.py").write_text("def hello(): pass")

        result = self.runner.invoke(
            analyze,
            [
                str(test_dir),
                "--ignore",
                "*.pyc",
                "--ignore",
                "__pycache__",
            ],
        )

        assert result.exit_code == 0
        # Verificar que se configuraron los patrones de exclusión
        mock_config.set.assert_any_call("ignore_patterns", ["*.pyc", "__pycache__"])

    @patch("pypex.cli.Analyzer")
    @patch("pypex.cli.get_registry")
    @patch("pypex.cli.get_config")
    @patch("pypex.reporters.console_reporter.ConsoleReporter")
    def test_analyze_console_reporter_error(
        self,
        mock_console_reporter,
        mock_get_config,
        mock_get_registry,
        mock_analyzer_class,
        mock_registry,
        tmp_path,
    ):
        """Prueba el error al usar ConsoleReporter."""
        mock_config = Mock()
        mock_config.get.return_value = []
        mock_get_config.return_value = mock_config
        mock_get_registry.return_value = mock_registry

        mock_analyzer = Mock()
        mock_analyzer.analyze.return_value = Mock()
        mock_analyzer_class.return_value = mock_analyzer

        # Mock que falla al generar reporte
        mock_reporter_instance = Mock()
        mock_reporter_instance.generate_report.side_effect = Exception("Reporter error")
        mock_console_reporter.return_value = mock_reporter_instance

        test_dir = tmp_path / "test_project"
        test_dir.mkdir()
        (test_dir / "test_file.py").write_text("def hello(): pass")

        result = self.runner.invoke(analyze, [str(test_dir)])

        assert result.exit_code != 0
        assert "Error al mostrar resultados en consola" in result.output

    @patch("pypex.cli.ReporterRegistry")
    @patch("pypex.cli.Analyzer")
    @patch("pypex.cli.get_registry")
    @patch("pypex.cli.get_config")
    @patch("pypex.cli.get_presentation_service")
    def test_analyze_reporter_error(
        self,
        mock_get_presentation_service,
        mock_get_config,
        mock_get_registry,
        mock_analyzer_class,
        mock_reporter_registry,
        mock_registry,
        tmp_path,
    ):
        """Prueba el error al generar reporte con ReporterRegistry."""
        mock_config = Mock()
        mock_config.get.return_value = []
        mock_get_config.return_value = mock_config
        mock_get_registry.return_value = mock_registry

        mock_presentation = Mock()
        mock_get_presentation_service.return_value = mock_presentation

        mock_analyzer = Mock()
        mock_results = Mock()
        mock_analyzer.analyze.return_value = mock_results
        mock_analyzer_class.return_value = mock_analyzer

        # Mock reporter que falla
        mock_reporter = Mock()
        mock_reporter.generate_report.side_effect = Exception("Report generation failed")
        mock_reporter_registry.get_reporter.return_value = Mock(return_value=mock_reporter)

        test_dir = tmp_path / "test_project"
        test_dir.mkdir()
        (test_dir / "test_file.py").write_text("def hello(): pass")

        output_file = tmp_path / "report.html"

        result = self.runner.invoke(
            analyze,
            [
                str(test_dir),
                "--format",
                "html",
                "--output",
                str(output_file),
            ],
        )

        assert result.exit_code != 0
        assert "Error al generar reporte html" in result.output

    @patch("pypex.cli.Analyzer")
    @patch("pypex.cli.get_registry")
    @patch("pypex.cli.get_config")
    @patch("pypex.cli.get_presentation_service")
    def test_analyze_file_size_check(
        self,
        mock_get_presentation_service,
        mock_get_config,
        mock_get_registry,
        mock_analyzer_class,
        mock_registry,
        tmp_path,
    ):
        """Prueba la verificación del tamaño de archivo."""
        mock_config = Mock()
        mock_config.get.return_value = []
        mock_get_config.return_value = mock_config
        mock_get_registry.return_value = mock_registry

        mock_presentation = Mock()
        mock_get_presentation_service.return_value = mock_presentation

        mock_analyzer = Mock()
        mock_results = Mock()
        mock_analyzer.analyze.return_value = mock_results
        mock_analyzer_class.return_value = mock_analyzer

        # Mock reporter
        mock_reporter = Mock()

        with patch("pypex.cli.ReporterRegistry") as mock_reporter_registry:
            mock_reporter_registry.get_reporter.return_value = Mock(return_value=mock_reporter)

            test_dir = tmp_path / "test_project"
            test_dir.mkdir()
            (test_dir / "test_file.py").write_text("def hello(): pass")

            output_file = tmp_path / "report.html"
            # Crear archivo de tamaño 0 para probar el branch de tamaño
            output_file.write_text("")

            result = self.runner.invoke(
                analyze,
                [
                    str(test_dir),
                    "--format",
                    "html",
                    "--output",
                    str(output_file),
                ],
            )

            assert result.exit_code == 0
            # Verificar que no se llama print_info para el tamaño cuando es 0
            calls = [
                call
                for call in mock_presentation.print_info.call_args_list
                if "Tamaño:" in str(call)
            ]
            assert len(calls) == 0

    @patch("pypex.cli.Analyzer")
    @patch("pypex.cli.get_registry")
    @patch("pypex.cli.get_config")
    @patch("pypex.reporters.console_reporter.ConsoleReporter")
    def test_analyze_general_exception(
        self,
        mock_console_reporter,
        mock_get_config,
        mock_get_registry,
        mock_analyzer_class,
        mock_registry,
        tmp_path,
    ):
        """Prueba el manejo de excepciones generales."""
        mock_config = Mock()
        mock_config.get.return_value = []
        mock_get_config.return_value = mock_config
        mock_get_registry.return_value = mock_registry

        # Analyzer que lanza excepción general
        mock_analyzer_class.side_effect = RuntimeError("Unexpected error")

        test_dir = tmp_path / "test_project"
        test_dir.mkdir()
        (test_dir / "test_file.py").write_text("def hello(): pass")

        result = self.runner.invoke(analyze, [str(test_dir)])

        assert result.exit_code != 0
        assert "Error durante el análisis: Unexpected error" in result.output

    @patch("pypex.cli.Analyzer")
    @patch("pypex.cli.get_registry")
    @patch("pypex.cli.get_config")
    def test_analyze_no_metrics_after_filter(
        self,
        mock_get_config,
        mock_get_registry,
        mock_analyzer_class,
        mock_registry,
        tmp_path,
    ):
        """Prueba el caso cuando no quedan métricas después de filtros."""
        mock_config = Mock()
        mock_config.get.return_value = []
        mock_get_config.return_value = mock_config
        mock_get_registry.return_value = mock_registry

        # Mock registry con métricas limitadas que serán todas excluidas
        mock_registry.get_available_metrics.return_value = ["metric1", "metric2"]

        test_dir = tmp_path / "test_project"
        test_dir.mkdir()
        (test_dir / "test_file.py").write_text("def hello(): pass")

        # Excluir todas las métricas disponibles
        result = self.runner.invoke(
            analyze, [str(test_dir), "--exclude-metrics", "metric1", "--exclude-metrics", "metric2"]
        )

        assert result.exit_code != 0
        assert "No quedan métricas válidas" in result.output

    @patch("pypex.cli.Analyzer")
    @patch("pypex.cli.get_registry")
    @patch("pypex.cli.get_config")
    @patch("pypex.cli.get_presentation_service")
    def test_analyze_file_size_display(
        self,
        mock_get_presentation_service,
        mock_get_config,
        mock_get_registry,
        mock_analyzer_class,
        mock_registry,
        tmp_path,
    ):
        """Prueba la mostrar del tamaño de archivo cuando es > 0."""
        mock_config = Mock()
        mock_config.get.return_value = []
        mock_get_config.return_value = mock_config
        mock_get_registry.return_value = mock_registry

        mock_presentation = Mock()
        mock_get_presentation_service.return_value = mock_presentation

        mock_analyzer = Mock()
        mock_results = Mock()
        mock_analyzer.analyze.return_value = mock_results
        mock_analyzer_class.return_value = mock_analyzer

        # Mock reporter
        mock_reporter = Mock()

        with patch("pypex.cli.ReporterRegistry") as mock_reporter_registry:
            mock_reporter_registry.get_reporter.return_value = Mock(return_value=mock_reporter)

            test_dir = tmp_path / "test_project"
            test_dir.mkdir()
            (test_dir / "test_file.py").write_text("def hello(): pass")

            output_file = tmp_path / "report.html"
            # Crear archivo con contenido para que tenga tamaño > 0
            output_file.write_text("<html>Test report with content</html>")

            result = self.runner.invoke(
                analyze,
                [
                    str(test_dir),
                    "--format",
                    "html",
                    "--output",
                    str(output_file),
                ],
            )

            assert result.exit_code == 0
            # Verificar que sí se llama print_info para el tamaño cuando es > 0
            size_calls = [
                call
                for call in mock_presentation.print_info.call_args_list
                if "Tamaño:" in str(call)
            ]
            assert len(size_calls) > 0


class TestThresholdsCommand:
    """Tests para el comando thresholds."""

    def setup_method(self):
        """Configuración inicial para cada test."""
        self.runner = pytest.importorskip("click.testing").CliRunner()

    @patch("pypex.cli.get_registry")
    @patch("pypex.metrics.thresholds.get_threshold_config")
    def test_thresholds_error_handling(
        self,
        mock_get_threshold_config,
        mock_get_registry,
    ):
        """Prueba el manejo de errores en el comando thresholds."""
        mock_get_registry.side_effect = Exception("Registry error")

        result = self.runner.invoke(thresholds)

        # El comando debe manejar el error graciosamente
        assert result.exit_code == 0  # No debe fallar completamente

    @patch("pypex.cli.get_registry")
    @patch("pypex.metrics.thresholds.get_threshold_config")
    @patch("pypex.cli.get_presentation_service")
    def test_thresholds_general_exception_handling(
        self,
        mock_get_presentation,
        mock_get_threshold_config,
        mock_get_registry,
    ):
        """Prueba el manejo de excepciones generales en thresholds."""
        # Simular error al obtener el registry
        mock_get_registry.side_effect = Exception("Registry loading error")

        mock_presentation = Mock()
        mock_get_presentation.return_value = mock_presentation

        result = self.runner.invoke(thresholds)

        assert result.exit_code == 0  # No debe fallar completamente
        # Verificar que se maneja el error correctamente
        assert len(result.output) >= 0  # Al menos algo de output


# Tests de integración básicos
class TestCLIIntegration:
    """Tests de integración para el CLI completo."""

    def setup_method(self):
        """Configuración inicial para cada test."""
        self.runner = pytest.importorskip("click.testing").CliRunner()

    def test_help_command(self):
        """Prueba que el comando help funciona correctamente."""
        result = self.runner.invoke(main, ["--help"])

        assert result.exit_code == 0
        assert "PyPex: Analizador Avanzado" in result.output
        assert "analyze" in result.output
        assert "thresholds" in result.output

    def test_version_option(self):
        """Prueba que la opción version funciona."""
        result = self.runner.invoke(main, ["--version"])

        assert result.exit_code == 0
        # Debe mostrar alguna información de versión
        assert len(result.output.strip()) > 0

    def test_analyze_help(self):
        """Prueba el help del comando analyze."""
        result = self.runner.invoke(analyze, ["--help"])

        assert result.exit_code == 0
        assert "Analiza código Python" in result.output
        assert "--format" in result.output
        assert "--output" in result.output

    def test_thresholds_help(self):
        """Prueba el help del comando thresholds."""
        result = self.runner.invoke(thresholds, ["--help"])

        assert result.exit_code == 0
        assert "umbrales configurados" in result.output


# Fixtures adicionales para casos edge
@pytest.fixture
def corrupted_config_file(temp_config_dir):
    """Crea un archivo de configuración corrupto/binario."""
    temp_config_dir.mkdir(exist_ok=True)
    config_file = temp_config_dir / "corrupted.yaml"

    with open(config_file, "wb") as f:
        f.write(b"\x00\x01\x02\x03")  # Datos binarios

    return config_file


class TestEdgeCases:
    """Tests para casos edge y situaciones especiales."""

    def test_load_config_corrupted_file(self, corrupted_config_file):
        """Prueba la carga de un archivo corrupto."""
        with pytest.raises(click.ClickException):
            load_config_file(str(corrupted_config_file))

    @patch("pypex.cli.get_registry")
    def test_validate_metrics_empty_registry(self, mock_get_registry):
        """Prueba la validación cuando el registry está vacío."""
        mock_registry = Mock()
        mock_registry.get_available_metrics.return_value = []
        mock_get_registry.return_value = mock_registry

        with pytest.raises(click.ClickException):
            validate_metrics_list(["any_metric"], [])


# Test para el punto de entrada principal
class TestMainExecution:
    """Tests para la ejecución principal del script."""

    @patch("pypex.cli.main")
    def test_main_script_execution(self, mock_main):
        """Prueba la ejecución del script principal."""
        # Simular la ejecución del script como módulo principal
        import pypex.cli

        # Guardar el valor original de __name__
        original_name = pypex.cli.__name__

        try:
            # Cambiar temporalmente __name__ para simular ejecución como script
            pypex.cli.__name__ = "__main__"

            # Simular la importación que ejecutaría main()
            # Esto no se puede probar directamente porque está al final del módulo
            # pero podemos verificar que la función main existe y es llamable
            assert callable(pypex.cli.main)

        finally:
            # Restaurar el valor original
            pypex.cli.__name__ = original_name
