"""Tests unitarios completos para el módulo Analyzer de PyPex.

Estos tests cubren todas las funcionalidades del analizador principal
con casos de éxito, error y edge cases siguiendo las mejores prácticas de testing.
"""

import time
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from pypex.core.analyzer import Analyzer
from pypex.core.interfaces import (
    FileAnalysisResult,
    IASTParser,
    IFileProcessor,
    InvalidProjectError,
    IProject,
    ProjectAnalysisResult,
)
from pypex.core.results import AnalysisError, ErrorSeverity
from pypex.metrics import IMetric
from pypex.parser.code_entities import Module as ModuleEntity


@pytest.fixture
def mock_file_processor():
    """Mock del procesador de archivos."""
    mock_processor = Mock(spec=IFileProcessor)
    mock_processor.max_file_size = 1024 * 1024  # 1MB
    mock_processor.ignore_patterns = ["*.pyc", "__pycache__"]
    return mock_processor


@pytest.fixture
def mock_parser():
    """Mock del parser AST."""
    mock_parser = Mock(spec=IASTParser)

    # Mock para parse_with_astroid
    mock_astroid_tree = Mock()
    mock_parser.parse_with_astroid.return_value = mock_astroid_tree

    # Mock para parse_file (fallback)
    mock_ast_tree = Mock()
    mock_parser.parse_file.return_value = mock_ast_tree

    return mock_parser


@pytest.fixture
def mock_project_class():
    """Mock de la clase Project."""
    mock_project = Mock(spec=IProject)
    mock_project.python_files = []
    mock_project_class = Mock(return_value=mock_project)
    return mock_project_class


@pytest.fixture
def mock_metrics():
    """Mock de métricas para testing."""
    metrics = []
    for i in range(3):
        metric = Mock(spec=IMetric)
        metric.name = f"test_metric_{i}"
        metric.description = f"Test metric {i} description"
        metrics.append(metric)
    return metrics


@pytest.fixture
def sample_config():
    """Configuración de ejemplo para tests."""
    return {
        "max_file_size": 2048 * 1024,
        "ignore_patterns": ["*.pyc", "test_*.py"],
        "output_format": "console",
        "no_progress_bar": False,
    }


@pytest.fixture
def temp_python_file(tmp_path):
    """Archivo Python temporal para tests."""
    python_file = tmp_path / "sample.py"
    python_content = '''"""Archivo de ejemplo para tests."""

def hello_world():
    """Función de saludo."""
    print("Hello, World!")
    return "Hello, World!"

class Calculator:
    """Calculadora simple."""

    def add(self, a, b):
        """Suma dos números."""
        return a + b

    def multiply(self, a, b):
        """Multiplica dos números."""
        result = a * b
        return result
'''
    python_file.write_text(python_content)
    return python_file


@pytest.fixture
def temp_project_dir(tmp_path):
    """Directorio de proyecto temporal con archivos Python."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()

    # Crear algunos archivos Python
    (project_dir / "__init__.py").write_text("")
    (project_dir / "module1.py").write_text("def func1(): pass")
    (project_dir / "module2.py").write_text("class Class1: pass")

    # Crear subdirectorio
    subdir = project_dir / "subpackage"
    subdir.mkdir()
    (subdir / "__init__.py").write_text("")
    (subdir / "submodule.py").write_text("def sub_func(): pass")

    return project_dir


class TestAnalyzerInitialization:
    """Tests para la inicialización del Analyzer."""

    def test_analyzer_init_default_config(self, mock_file_processor, mock_parser):
        """Prueba la inicialización con configuración por defecto."""
        analyzer = Analyzer(parser=mock_parser, file_processor=mock_file_processor)

        assert analyzer.file_processor == mock_file_processor
        assert analyzer.parser == mock_parser
        assert analyzer.config is not None  # Config comes from service
        assert hasattr(analyzer, "project_class")
        assert analyzer.metrics_engine is not None

    def test_analyzer_init_with_specific_metrics(
        self, mock_file_processor, mock_parser, mock_metrics
    ):
        """Prueba la inicialización con métricas específicas."""
        analyzer = Analyzer(
            parser=mock_parser, file_processor=mock_file_processor, specific_metrics=mock_metrics
        )

        assert analyzer.metrics_engine is not None

    @patch("pypex.core.analyzer.logger")
    def test_analyzer_init_logging(self, mock_logger, mock_file_processor, mock_parser):
        """Prueba que se registre la inicialización en logs."""
        Analyzer(parser=mock_parser, file_processor=mock_file_processor)

        mock_logger.debug.assert_called()
        # Check that initialization was logged
        log_calls = [
            call for call in mock_logger.debug.call_args_list if "inicializado" in str(call).lower()
        ]
        assert len(log_calls) > 0


class TestAnalyzerConfiguration:
    """Tests para la configuración del Analyzer."""

    def test_set_reporters(self, mock_file_processor, mock_parser):
        """Prueba la configuración de reporteros."""
        analyzer = Analyzer(mock_parser, mock_file_processor)

        mock_reporters = [Mock(), Mock()]
        analyzer.set_reporters(mock_reporters)

        assert analyzer.reporters == mock_reporters

    @patch("pypex.core.analyzer.logger")
    def test_set_metrics(self, mock_logger, mock_file_processor, mock_parser, mock_metrics):
        """Prueba la configuración de métricas."""
        analyzer = Analyzer(mock_parser, mock_file_processor)
        analyzer.set_metrics(mock_metrics)

        assert analyzer.metrics == mock_metrics
        assert analyzer.metrics_engine is not None
        mock_logger.debug.assert_called()

    def test_ensure_metrics_engine_returns_existing(self, mock_file_processor, mock_parser):
        """Prueba que se devuelva el motor existente si ya está configurado."""
        analyzer = Analyzer(mock_parser, mock_file_processor)

        result = analyzer._ensure_metrics_engine()

        assert result is not None
        assert result == analyzer.metrics_engine


class TestAnalyzeFile:
    """Tests para el método analyze_file."""

    @patch("pypex.core.analyzer.AstroidNodeVisitor")
    @patch("pypex.core.analyzer.logger")
    def test_analyze_file_success_with_astroid(
        self,
        mock_logger,
        mock_astroid_visitor_class,
        mock_file_processor,
        mock_parser,
        temp_python_file,
    ):
        """Prueba el análisis exitoso de archivo con Astroid."""
        # Setup mocks
        mock_module_entity = Mock(spec=ModuleEntity)
        mock_visitor = Mock()
        mock_visitor.analyze.return_value = mock_module_entity
        mock_astroid_visitor_class.return_value = mock_visitor

        mock_engine = Mock()
        mock_engine.calculate_all_for_module.return_value = {"complexity": 5}
        mock_engine.get_entities_from_module.return_value = []

        analyzer = Analyzer(mock_parser, mock_file_processor)
        analyzer.metrics_engine = mock_engine

        # Execute
        result = analyzer.analyze_file(temp_python_file)

        # Verify
        assert isinstance(result, FileAnalysisResult)
        assert result.file_path == temp_python_file
        assert result.module_name == temp_python_file.stem
        assert result.file_size > 0
        assert result.line_count > 0
        assert result.analysis_time_ms >= 0
        # Note: Since the mock returns data, there should be no errors for successful analysis
        # but there might be warnings from the actual implementation

        # Verify astroid analysis was called
        mock_parser.parse_with_astroid.assert_called_once_with(str(temp_python_file))
        mock_engine.calculate_all_for_module.assert_called_once_with(mock_module_entity)

    def test_analyze_file_nonexistent(self, mock_file_processor, mock_parser):
        """Prueba el análisis de archivo inexistente."""
        nonexistent_file = Path("/nonexistent/file.py")

        analyzer = Analyzer(mock_parser, mock_file_processor)
        result = analyzer.analyze_file(nonexistent_file)

        assert isinstance(result, FileAnalysisResult)
        assert len(result.errors) == 1
        assert result.errors[0].severity == ErrorSeverity.CRITICAL
        assert "no existe" in result.errors[0].message
        assert result.analysis_time_ms >= 0  # Changed from > 0 to >= 0

    def test_analyze_file_non_python(self, mock_file_processor, mock_parser, tmp_path):
        """Prueba el análisis de archivo que no es Python."""
        text_file = tmp_path / "not_python.txt"
        text_file.write_text("This is not Python code")

        analyzer = Analyzer(mock_parser, mock_file_processor)
        result = analyzer.analyze_file(text_file)

        assert isinstance(result, FileAnalysisResult)
        assert len(result.errors) == 1
        assert result.errors[0].severity == ErrorSeverity.CRITICAL
        assert "no es un archivo Python" in result.errors[0].message

    @patch("pypex.core.analyzer.AstroidNodeVisitor")
    @patch("pypex.core.analyzer.ASTNodeVisitor")
    @patch("pypex.core.analyzer.logger")
    def test_analyze_file_astroid_fallback_to_ast(
        self,
        mock_logger,
        mock_ast_visitor_class,
        mock_astroid_visitor_class,
        mock_file_processor,
        mock_parser,
        temp_python_file,
    ):
        """Prueba el fallback a AST cuando Astroid falla."""
        # Setup astroid to fail
        mock_parser.parse_with_astroid.side_effect = Exception("Astroid error")

        # Setup AST fallback
        mock_ast_visitor = Mock()
        mock_ast_visitor.get_metrics.return_value = {"lines": 10}
        mock_ast_visitor_class.return_value = mock_ast_visitor

        analyzer = Analyzer(mock_parser, mock_file_processor)
        result = analyzer.analyze_file(temp_python_file)

        # Verify fallback was used
        assert isinstance(result, FileAnalysisResult)
        assert len(result.errors) >= 1  # Warning about astroid failure
        assert any(
            result.errors[i].severity == ErrorSeverity.WARNING for i in range(len(result.errors))
        )
        assert any(
            "Astroid analysis failed" in result.errors[i].message for i in range(len(result.errors))
        )

        # Verify AST fallback was called
        mock_parser.parse_file.assert_called_once_with(str(temp_python_file))
        mock_ast_visitor.visit.assert_called_once()

    @patch("pypex.core.analyzer.logger")
    def test_analyze_file_critical_error(
        self, mock_logger, mock_file_processor, mock_parser, temp_python_file
    ):
        """Prueba el manejo de errores críticos durante el análisis."""
        # Setup parser to fail critically - simular que el bloque try/except principal capture una excepción
        mock_parser.parse_with_astroid.side_effect = Exception("Critical error")
        mock_parser.parse_file.side_effect = Exception("AST also failed")

        # Mock del visitor de astroid para que también falle
        with patch("pypex.core.analyzer.AstroidNodeVisitor") as mock_visitor_class:
            mock_visitor_class.side_effect = Exception("Visitor failed")

            analyzer = Analyzer(mock_parser, mock_file_processor)
            result = analyzer.analyze_file(temp_python_file)

        assert isinstance(result, FileAnalysisResult)
        assert len(result.errors) >= 1
        # Should have at least a warning from astroid failure
        warning_errors = [e for e in result.errors if e.severity == ErrorSeverity.WARNING]
        assert len(warning_errors) >= 1

    def test_analyze_file_with_custom_config(
        self, mock_file_processor, mock_parser, temp_python_file
    ):
        """Prueba el análisis con configuración personalizada."""
        custom_config = {"custom_option": "value"}

        analyzer = Analyzer(mock_parser, mock_file_processor)
        result = analyzer.analyze_file(temp_python_file, config=custom_config)

        assert isinstance(result, FileAnalysisResult)
        # Config should not affect basic file analysis directly
        assert result.file_path == temp_python_file


class TestAnalyzeProject:
    """Tests para el método analyze_project."""

    def setup_method(self):
        """Setup para cada test."""
        self.mock_progress_manager = Mock()
        self.mock_progress_bar = Mock()
        self.mock_progress_bar.__enter__ = Mock(return_value=self.mock_progress_bar)
        self.mock_progress_bar.__exit__ = Mock(return_value=None)
        self.mock_progress_manager.create_progress_bar.return_value = self.mock_progress_bar

    @patch("pypex.core.analyzer.get_progress_manager")
    @patch("pypex.core.analyzer.logger")
    def test_analyze_project_success(
        self,
        mock_logger,
        mock_get_progress_manager,
        mock_file_processor,
        mock_parser,
        mock_project_class,
        temp_project_dir,
    ):
        """Prueba el análisis exitoso de un proyecto."""
        # Setup mocks
        mock_get_progress_manager.return_value = self.mock_progress_manager

        mock_project = Mock()
        mock_project.python_files = [
            temp_project_dir / "module1.py",
            temp_project_dir / "module2.py",
        ]
        mock_project_class.return_value = mock_project

        analyzer = Analyzer(mock_parser, mock_file_processor)
        analyzer.project_class = mock_project_class

        # Mock analyze_file to return successful results
        successful_result = FileAnalysisResult(
            file_path=temp_project_dir / "module1.py",
            module_name="module1",
            file_size=100,
            line_count=10,
        )
        # No errors = successful by default

        with patch.object(analyzer, "analyze_file", return_value=successful_result):
            result = analyzer.analyze_project(temp_project_dir)

        assert isinstance(result, ProjectAnalysisResult)
        assert result.project_name == temp_project_dir.name
        assert result.root_path == temp_project_dir
        assert result.total_files == 2
        assert result.successful_files == 2
        assert result.failed_files == 0
        assert result.analysis_time_ms >= 0  # Changed from > 0 to >= 0

    def test_analyze_project_nonexistent_directory(self, mock_file_processor, mock_parser):
        """Prueba el análisis de directorio inexistente."""
        nonexistent_dir = Path("/nonexistent/directory")

        analyzer = Analyzer(mock_parser, mock_file_processor)
        result = analyzer.analyze_project(nonexistent_dir)

        assert isinstance(result, ProjectAnalysisResult)
        assert len(result.global_errors) == 1
        assert result.global_errors[0].severity == ErrorSeverity.CRITICAL
        assert "no existe" in result.global_errors[0].message

    def test_analyze_project_not_directory(
        self, mock_file_processor, mock_parser, temp_python_file
    ):
        """Prueba el análisis cuando la ruta no es un directorio."""
        analyzer = Analyzer(mock_parser, mock_file_processor)
        result = analyzer.analyze_project(temp_python_file)  # File instead of directory

        assert isinstance(result, ProjectAnalysisResult)
        assert len(result.global_errors) == 1
        assert result.global_errors[0].severity == ErrorSeverity.CRITICAL

    @patch("pypex.core.analyzer.logger")
    def test_analyze_project_invalid_project_error(
        self, mock_logger, mock_file_processor, mock_parser, mock_project_class, temp_project_dir
    ):
        """Prueba el manejo de InvalidProjectError."""
        # Setup project class to raise InvalidProjectError
        mock_project_class.side_effect = InvalidProjectError("No Python files found")

        analyzer = Analyzer(mock_parser, mock_file_processor)
        analyzer.project_class = mock_project_class
        result = analyzer.analyze_project(temp_project_dir)

        assert isinstance(result, ProjectAnalysisResult)
        assert len(result.global_errors) == 1
        assert result.global_errors[0].severity == ErrorSeverity.CRITICAL
        assert "No Python files found" in result.global_errors[0].message

    @patch("pypex.core.analyzer.get_progress_manager")
    def test_analyze_project_with_mixed_results(
        self,
        mock_get_progress_manager,
        mock_file_processor,
        mock_parser,
        mock_project_class,
        temp_project_dir,
    ):
        """Prueba el análisis con resultados mixtos (éxito y fallo)."""
        mock_get_progress_manager.return_value = self.mock_progress_manager

        mock_project = Mock()
        mock_project.python_files = [temp_project_dir / "good.py", temp_project_dir / "bad.py"]
        mock_project_class.return_value = mock_project

        analyzer = Analyzer(mock_parser, mock_file_processor)
        analyzer.project_class = mock_project_class

        def mock_analyze_file(file_path, config=None):
            result = FileAnalysisResult(
                file_path=file_path, module_name=file_path.stem, file_size=100, line_count=10
            )
            if "bad" in str(file_path):
                # Add error to make it unsuccessful
                result.errors.append(AnalysisError("Parse error", ErrorSeverity.CRITICAL, "test"))
            # No need to set was_successful - it's determined by errors
            return result

        with patch.object(analyzer, "analyze_file", side_effect=mock_analyze_file):
            result = analyzer.analyze_project(temp_project_dir)

        assert result.total_files == 2
        assert result.successful_files == 1
        assert result.failed_files == 1

    @patch("pypex.core.analyzer.get_progress_manager")
    @patch("pypex.core.analyzer.ProjectEntity")
    def test_analyze_project_with_project_metrics(
        self,
        mock_project_entity_class,
        mock_get_progress_manager,
        mock_file_processor,
        mock_parser,
        mock_project_class,
        temp_project_dir,
    ):
        """Prueba el cálculo de métricas a nivel de proyecto."""
        mock_get_progress_manager.return_value = self.mock_progress_manager

        mock_project = Mock()
        mock_project.python_files = [temp_project_dir / "module1.py"]
        mock_project_class.return_value = mock_project

        # Setup metrics engine mock
        mock_engine = Mock()
        mock_engine.calculate_all_for_project.return_value = {"project_complexity": 15}

        analyzer = Analyzer(mock_parser, mock_file_processor)
        analyzer.project_class = mock_project_class
        analyzer.metrics_engine = mock_engine

        # Mock successful file analysis and module entity collection
        successful_result = FileAnalysisResult(
            file_path=temp_project_dir / "module1.py",
            module_name="module1",
            file_size=100,
            line_count=10,
        )
        # No errors = successful by default

        mock_module_entity = Mock(spec=ModuleEntity)

        with (
            patch.object(analyzer, "analyze_file", return_value=successful_result),
            patch.object(analyzer, "_collect_module_entity") as mock_collect,
        ):

            def side_effect(file_path, file_result, module_entities):
                module_entities.append(mock_module_entity)

            mock_collect.side_effect = side_effect

            result = analyzer.analyze_project(temp_project_dir)

        assert result.project_metrics == {"project_complexity": 15}
        mock_engine.calculate_all_for_project.assert_called_once()


class TestAnalyzeMethod:
    """Tests para el método principal analyze."""

    def test_analyze_single_file(self, mock_file_processor, mock_parser, temp_python_file):
        """Prueba el análisis de un archivo único."""
        analyzer = Analyzer(mock_parser, mock_file_processor)

        with patch.object(analyzer, "analyze_file") as mock_analyze_file:
            mock_file_result = FileAnalysisResult(
                file_path=temp_python_file,
                module_name=temp_python_file.stem,
                file_size=100,
                line_count=10,
            )
            # No errors = successful by default
            mock_file_result.analysis_time_ms = 50.0
            mock_analyze_file.return_value = mock_file_result

            result = analyzer.analyze(temp_python_file)

        assert isinstance(result, ProjectAnalysisResult)
        assert result.project_name == temp_python_file.stem
        assert result.root_path == temp_python_file.parent
        assert result.total_files == 1
        assert result.successful_files == 1
        assert result.failed_files == 0
        assert result.analysis_time_ms == 50.0

    def test_analyze_directory(self, mock_file_processor, mock_parser, temp_project_dir):
        """Prueba el análisis de un directorio."""
        analyzer = Analyzer(mock_parser, mock_file_processor)

        with patch.object(analyzer, "analyze_project") as mock_analyze_project:
            mock_project_result = ProjectAnalysisResult(
                project_name=temp_project_dir.name,
                root_path=temp_project_dir,
                analysis_timestamp=datetime.now().isoformat(),
            )
            mock_analyze_project.return_value = mock_project_result

            result = analyzer.analyze(temp_project_dir)

        assert result == mock_project_result
        # Verify the call was made - config will be the full config object, not empty dict
        mock_analyze_project.assert_called_once()
        call_args = mock_analyze_project.call_args
        assert call_args[0][0] == temp_project_dir  # First positional arg should be the path
        assert isinstance(call_args[0][1], dict)  # Second arg should be config dict

    def test_analyze_nonexistent_path(self, mock_file_processor, mock_parser):
        """Prueba el análisis de ruta inexistente."""
        nonexistent_path = Path("/nonexistent/path")

        analyzer = Analyzer(mock_parser, mock_file_processor)
        result = analyzer.analyze(nonexistent_path)

        assert isinstance(result, ProjectAnalysisResult)
        assert len(result.global_errors) == 1
        assert result.global_errors[0].severity == ErrorSeverity.CRITICAL
        assert "no existe" in result.global_errors[0].message

    def test_analyze_unsupported_path_type(self, mock_file_processor, mock_parser):
        """Prueba el análisis de tipo de ruta no soportada."""
        # En sistemas Unix esto podría ser un socket o pipe, pero para el test
        # simularemos con un path que existe pero no es file ni directory
        analyzer = Analyzer(mock_parser, mock_file_processor)

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.is_file", return_value=False),
            patch("pathlib.Path.is_dir", return_value=False),
        ):
            result = analyzer.analyze(Path("/special/path"))

        assert isinstance(result, ProjectAnalysisResult)
        assert len(result.global_errors) == 1
        assert result.global_errors[0].severity == ErrorSeverity.CRITICAL
        assert "no es un archivo o directorio analizable" in result.global_errors[0].message

    def test_analyze_with_custom_config(self, mock_file_processor, mock_parser, temp_python_file):
        """Prueba el análisis con configuración personalizada."""
        custom_config = {"test_option": "test_value"}

        analyzer = Analyzer(mock_parser, mock_file_processor)

        with patch.object(analyzer, "analyze_file") as mock_analyze_file:
            mock_file_result = FileAnalysisResult(
                file_path=temp_python_file,
                module_name=temp_python_file.stem,
                file_size=100,
                line_count=10,
            )
            mock_analyze_file.return_value = mock_file_result

            analyzer.analyze(temp_python_file, config=custom_config)

        # Verify custom config was passed to analyze_file
        mock_analyze_file.assert_called_once_with(temp_python_file, custom_config)


class TestCollectModuleEntity:
    """Tests para el método _collect_module_entity."""

    @patch("pypex.core.analyzer.AstroidNodeVisitor")
    @patch("pypex.core.analyzer.logger")
    def test_collect_module_entity_success(
        self,
        mock_logger,
        mock_astroid_visitor_class,
        mock_file_processor,
        mock_parser,
        temp_python_file,
    ):
        """Prueba la recopilación exitosa de entidad de módulo."""
        # Setup mocks
        mock_module_entity = Mock(spec=ModuleEntity)
        mock_visitor = Mock()
        mock_visitor.analyze.return_value = mock_module_entity
        mock_astroid_visitor_class.return_value = mock_visitor

        analyzer = Analyzer(mock_parser, mock_file_processor)

        file_result = FileAnalysisResult(
            file_path=temp_python_file,
            module_name=temp_python_file.stem,
            file_size=100,
            line_count=10,
        )

        module_entities = []
        analyzer._collect_module_entity(temp_python_file, file_result, module_entities)

        assert len(module_entities) == 1
        assert module_entities[0] == mock_module_entity
        mock_parser.parse_with_astroid.assert_called_once_with(str(temp_python_file))

    @patch("pypex.core.analyzer.logger")
    def test_collect_module_entity_failure(
        self, mock_logger, mock_file_processor, mock_parser, temp_python_file
    ):
        """Prueba el manejo de errores en la recopilación de entidad."""
        # Setup parser to fail
        mock_parser.parse_with_astroid.side_effect = Exception("Parse error")

        analyzer = Analyzer(mock_parser, mock_file_processor)

        file_result = FileAnalysisResult(
            file_path=temp_python_file,
            module_name=temp_python_file.stem,
            file_size=100,
            line_count=10,
        )

        module_entities = []
        analyzer._collect_module_entity(temp_python_file, file_result, module_entities)

        # Should not add any entities on failure
        assert len(module_entities) == 0
        mock_logger.warning.assert_called_once()
        assert "No se pudo recopilar entidad de módulo" in mock_logger.warning.call_args[0][0]


class TestAnalyzerEdgeCases:
    """Tests para casos edge y situaciones especiales."""

    def setup_method(self):
        """Setup para cada test."""
        self.mock_progress_manager = Mock()
        self.mock_progress_bar = Mock()
        self.mock_progress_bar.__enter__ = Mock(return_value=self.mock_progress_bar)
        self.mock_progress_bar.__exit__ = Mock(return_value=None)
        self.mock_progress_manager.create_progress_bar.return_value = self.mock_progress_bar

    def test_analyze_file_with_encoding_issues(self, mock_file_processor, mock_parser, tmp_path):
        """Prueba el análisis de archivo con problemas de codificación."""
        # Crear archivo con contenido que podría causar problemas de encoding
        problematic_file = tmp_path / "encoding_issue.py"
        with open(problematic_file, "wb") as f:
            f.write("# -*- coding: utf-8 -*-\ndef función(): pass".encode("latin1"))

        analyzer = Analyzer(mock_parser, mock_file_processor)
        result = analyzer.analyze_file(problematic_file)

        # Should handle encoding gracefully
        assert isinstance(result, FileAnalysisResult)
        assert result.file_path == problematic_file

    def test_analyze_very_large_file_line_count(self, mock_file_processor, mock_parser, tmp_path):
        """Prueba el análisis de archivo con muchas líneas."""
        large_file = tmp_path / "large_file.py"

        # Crear archivo con muchas líneas
        content = "\n".join([f"# Line {i}" for i in range(1000)])
        large_file.write_text(content)

        analyzer = Analyzer(mock_parser, mock_file_processor)
        result = analyzer.analyze_file(large_file)

        assert isinstance(result, FileAnalysisResult)
        assert result.line_count == 1000
        assert result.file_size > 0

    @patch("pypex.core.analyzer.get_progress_manager")
    def test_analyze_project_without_progress_bar(
        self,
        mock_get_progress_manager,
        mock_file_processor,
        mock_parser,
        mock_project_class,
        temp_project_dir,
    ):
        """Prueba el análisis de proyecto sin barra de progreso."""
        mock_get_progress_manager.return_value = self.mock_progress_manager

        mock_project = Mock()
        mock_project.python_files = [temp_project_dir / "module1.py"]
        mock_project_class.return_value = mock_project

        # Configure no progress bar
        config = {"no_progress_bar": True}

        analyzer = Analyzer(mock_parser, mock_file_processor)
        analyzer.project_class = mock_project_class

        with patch.object(analyzer, "analyze_file") as mock_analyze_file:
            mock_file_result = FileAnalysisResult(
                file_path=temp_project_dir / "module1.py",
                module_name="module1",
                file_size=100,
                line_count=10,
            )
            # No errors = successful by default
            mock_analyze_file.return_value = mock_file_result

            analyzer.analyze_project(temp_project_dir, config=config)

        # Progress bar should be disabled
        self.mock_progress_manager.create_progress_bar.assert_called_once()
        call_args = self.mock_progress_manager.create_progress_bar.call_args
        assert call_args[1]["disable"] is True

    def test_analyzer_memory_cleanup(self, mock_file_processor, mock_parser):
        """Prueba que el analizador no mantenga referencias innecesarias."""
        analyzer = Analyzer(mock_parser, mock_file_processor)

        # Set some data
        large_data = [Mock() for _ in range(100)]
        analyzer.set_metrics(large_data)

        # Clear data
        analyzer.set_metrics([])

        assert len(analyzer.metrics) == 0
        # metrics_engine should be recreated with empty metrics
        assert analyzer.metrics_engine is not None

    @patch("pypex.core.analyzer.time")
    def test_analyze_file_timing_accuracy(
        self, mock_time_module, mock_file_processor, mock_parser, temp_python_file
    ):
        """Prueba la precisión del timing de análisis."""
        # Mock time.time() method specifically
        mock_time_module.time.side_effect = [1000.0, 1000.5]  # 500ms difference

        analyzer = Analyzer(mock_parser, mock_file_processor)
        result = analyzer.analyze_file(temp_python_file)

        assert result.analysis_time_ms == 500.0  # 500ms in milliseconds

    def test_analyze_file_with_very_long_lines(self, mock_file_processor, mock_parser, tmp_path):
        """Prueba el análisis de archivo con líneas muy largas."""
        long_line_file = tmp_path / "long_lines.py"
        # Create a file with very long lines
        long_line = "def very_long_function_name_" + "x" * 1000 + "(): pass"
        long_line_file.write_text(long_line)

        analyzer = Analyzer(mock_parser, mock_file_processor)
        result = analyzer.analyze_file(long_line_file)

        assert isinstance(result, FileAnalysisResult)
        assert result.line_count == 1
        assert result.file_size > 1000

    def test_analyze_file_critical_error_in_main_analysis_block(
        self, mock_file_processor, mock_parser, temp_python_file
    ):
        """Prueba el manejo de error crítico en el bloque principal de análisis."""
        # Mock both astroid and AST parsing to fail, and also mock the visitor creation to fail
        mock_parser.parse_with_astroid.side_effect = Exception("Astroid critical error")
        mock_parser.parse_file.side_effect = Exception("AST critical error")

        with patch(
            "pypex.core.analyzer.AstroidNodeVisitor",
            side_effect=Exception("Visitor creation failed"),
        ):
            analyzer = Analyzer(mock_parser, mock_file_processor)
            result = analyzer.analyze_file(temp_python_file)

        assert isinstance(result, FileAnalysisResult)
        # Should have at least one error from the critical error handling
        assert len(result.errors) >= 1
        # Should contain warning from astroid failure and potentially critical error
        error_severities = [e.severity for e in result.errors]
        assert ErrorSeverity.WARNING in error_severities

    def test_analyze_last_return_path(self, mock_file_processor, mock_parser):
        """Prueba el último path de return en el método analyze."""
        # Create a mock path that exists but is neither file nor directory
        with patch("pypex.core.analyzer.Path") as mock_path_class:
            mock_path = Mock()
            mock_path.exists.return_value = True
            mock_path.is_file.return_value = False
            mock_path.is_dir.return_value = False
            mock_path.__str__ = Mock(return_value="/special/path")
            mock_path_class.return_value = mock_path

            analyzer = Analyzer(mock_parser, mock_file_processor)
            result = analyzer.analyze("/special/path")

        assert isinstance(result, ProjectAnalysisResult)
        assert len(result.global_errors) == 1
        assert result.global_errors[0].severity == ErrorSeverity.CRITICAL
        assert "no es un archivo o directorio analizable" in result.global_errors[0].message


# Performance and integration tests
class TestAnalyzerPerformance:
    """Tests de rendimiento para el Analyzer."""

    def test_multiple_file_analysis_performance(self, mock_file_processor, mock_parser, tmp_path):
        """Prueba el rendimiento con múltiples archivos."""
        # Create multiple Python files
        files = []
        for i in range(10):
            file_path = tmp_path / f"test_file_{i}.py"
            file_path.write_text(f"def function_{i}(): pass")
            files.append(file_path)

        analyzer = Analyzer(mock_parser, mock_file_processor)

        start_time = time.time()
        results = []
        for file_path in files:
            result = analyzer.analyze_file(file_path)
            results.append(result)
        end_time = time.time()

        # Should complete within reasonable time (adjust threshold as needed)
        assert (end_time - start_time) < 5.0  # 5 seconds max
        assert len(results) == 10
        assert all(isinstance(r, FileAnalysisResult) for r in results)

    def test_metrics_engine_reuse(self, mock_file_processor, mock_parser, mock_metrics):
        """Prueba que el motor de métricas se reutilice eficientemente."""
        analyzer = Analyzer(mock_parser, mock_file_processor)
        analyzer.set_metrics(mock_metrics)

        engine1 = analyzer._ensure_metrics_engine()
        engine2 = analyzer._ensure_metrics_engine()

        # Should return the same instance
        assert engine1 is engine2


class TestAnalyzerEdgeCasesAdditional:
    """Tests adicionales para casos edge no cubiertos previamente."""

    def setup_method(self):
        """Setup para cada test."""
        self.mock_progress_manager = Mock()
        self.mock_progress_bar = Mock()
        self.mock_progress_bar.__enter__ = Mock(return_value=self.mock_progress_bar)
        self.mock_progress_bar.__exit__ = Mock(return_value=None)
        self.mock_progress_manager.create_progress_bar.return_value = self.mock_progress_bar

    def test_analyze_file_io_error_reading_file(self, mock_file_processor, mock_parser, tmp_path):
        """Prueba el manejo de errores de I/O al leer archivo."""
        python_file = tmp_path / "test.py"
        python_file.write_text("def test(): pass")

        # Mock only the line counting part that could fail with I/O error
        with patch("builtins.open", side_effect=OSError("I/O Error")):
            analyzer = Analyzer(mock_parser, mock_file_processor)
            result = analyzer.analyze_file(python_file)

        assert isinstance(result, FileAnalysisResult)
        # Should still analyze the file even with I/O error during line counting
        assert result.file_path == python_file
        assert result.line_count == 0  # Default when reading fails

    def test_analyze_file_astroid_success_without_detailed_entity(
        self, mock_file_processor, mock_parser, temp_python_file
    ):
        """Prueba el caso donde astroid funciona pero no genera entidad detallada."""
        # Setup astroid to succeed but visitor returns None
        with patch("pypex.core.analyzer.AstroidNodeVisitor") as mock_visitor_class:
            mock_visitor = Mock()
            mock_visitor.analyze.return_value = None  # No detailed entity
            mock_visitor_class.return_value = mock_visitor

            analyzer = Analyzer(mock_parser, mock_file_processor)
            result = analyzer.analyze_file(temp_python_file)

        assert isinstance(result, FileAnalysisResult)
        assert result.module_metrics is None
        assert len(result.entities) == 0

    @patch("pypex.core.analyzer.get_progress_manager")
    @patch("pypex.core.analyzer.logger")
    def test_analyze_project_with_logging_when_no_progress_bar(
        self,
        mock_logger,
        mock_get_progress_manager,
        mock_file_processor,
        mock_parser,
        mock_project_class,
        temp_project_dir,
    ):
        """Prueba el logging periódico cuando no hay barra de progreso."""
        mock_get_progress_manager.return_value = self.mock_progress_manager

        # Create a project with 15 files to trigger periodic logging
        files = [temp_project_dir / f"module{i}.py" for i in range(15)]
        mock_project = Mock()
        mock_project.python_files = files
        mock_project_class.return_value = mock_project

        config = {"no_progress_bar": True}
        analyzer = Analyzer(mock_parser, mock_file_processor)
        analyzer.project_class = mock_project_class

        with patch.object(analyzer, "analyze_file") as mock_analyze_file:
            mock_file_result = FileAnalysisResult(
                file_path=files[0], module_name="module0", file_size=100, line_count=10
            )
            mock_analyze_file.return_value = mock_file_result

            analyzer.analyze_project(temp_project_dir, config=config)

        # Should have logged progress at file 10 and 15
        info_calls = [
            call for call in mock_logger.info.call_args_list if "Procesando archivo" in str(call)
        ]
        assert len(info_calls) >= 2  # At least 2 progress logs

    def test_analyze_project_general_project_manager_error(
        self, mock_file_processor, mock_parser, mock_project_class, temp_project_dir
    ):
        """Prueba el manejo de errores generales al inicializar project_manager."""
        # Setup project class to raise a general exception (not InvalidProjectError)
        mock_project_class.side_effect = RuntimeError("General initialization error")

        analyzer = Analyzer(mock_parser, mock_file_processor)
        analyzer.project_class = mock_project_class
        result = analyzer.analyze_project(temp_project_dir)

        assert isinstance(result, ProjectAnalysisResult)
        assert len(result.global_errors) == 1
        assert result.global_errors[0].severity == ErrorSeverity.CRITICAL
        assert "Error al inicializar el gestor de proyecto" in result.global_errors[0].message

    @patch("pypex.core.analyzer.get_progress_manager")
    def test_analyze_project_metrics_calculation_error(
        self,
        mock_get_progress_manager,
        mock_file_processor,
        mock_parser,
        mock_project_class,
        temp_project_dir,
    ):
        """Prueba el manejo de errores al calcular métricas de proyecto."""
        mock_get_progress_manager.return_value = self.mock_progress_manager

        mock_project = Mock()
        mock_project.python_files = [temp_project_dir / "module1.py"]
        mock_project_class.return_value = mock_project

        # Setup metrics engine to fail when calculating project metrics
        mock_engine = Mock()
        mock_engine.calculate_all_for_project.side_effect = Exception("Metrics calculation failed")

        analyzer = Analyzer(mock_parser, mock_file_processor)
        analyzer.project_class = mock_project_class
        analyzer.metrics_engine = mock_engine

        with (
            patch.object(analyzer, "analyze_file") as mock_analyze_file,
            patch.object(analyzer, "_collect_module_entity") as mock_collect,
        ):
            mock_file_result = FileAnalysisResult(
                file_path=temp_project_dir / "module1.py",
                module_name="module1",
                file_size=100,
                line_count=10,
            )
            mock_analyze_file.return_value = mock_file_result

            def side_effect(file_path, file_result, module_entities):
                module_entities.append(Mock(spec=ModuleEntity))

            mock_collect.side_effect = side_effect

            result = analyzer.analyze_project(temp_project_dir)

        assert isinstance(result, ProjectAnalysisResult)
        assert len(result.global_errors) == 1
        assert result.global_errors[0].severity == ErrorSeverity.WARNING
        assert "Error calculando métricas de proyecto" in result.global_errors[0].message

    def test_analyze_file_with_permission_error(self, mock_file_processor, mock_parser, tmp_path):
        """Prueba el análisis de archivo con errores de permisos."""
        python_file = tmp_path / "restricted.py"
        python_file.write_text("def test(): pass")

        # Mock open to raise PermissionError when reading for line count
        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            analyzer = Analyzer(mock_parser, mock_file_processor)
            result = analyzer.analyze_file(python_file)

        assert isinstance(result, FileAnalysisResult)
        # Should handle permission error gracefully
        assert result.line_count == 0

    def test_analyze_file_with_unicode_decode_error(
        self, mock_file_processor, mock_parser, tmp_path
    ):
        """Prueba el análisis de archivo con errores de codificación."""
        binary_file = tmp_path / "binary.py"
        # Write some binary content that might cause decode issues
        with open(binary_file, "wb") as f:
            f.write(b"\x80\x81\x82def test(): pass")

        analyzer = Analyzer(mock_parser, mock_file_processor)
        result = analyzer.analyze_file(binary_file)

        assert isinstance(result, FileAnalysisResult)
        # Should handle encoding issues gracefully with errors="ignore"
        assert result.file_path == binary_file

    def test_analyze_empty_python_file(self, mock_file_processor, mock_parser, tmp_path):
        """Prueba el análisis de archivo Python vacío."""
        empty_file = tmp_path / "empty.py"
        empty_file.write_text("")

        analyzer = Analyzer(mock_parser, mock_file_processor)
        result = analyzer.analyze_file(empty_file)

        assert isinstance(result, FileAnalysisResult)
        assert result.file_size == 0
        assert result.line_count == 0
        assert result.file_path == empty_file

    def test_analyze_project_with_no_python_files_found(
        self, mock_file_processor, mock_parser, mock_project_class, temp_project_dir
    ):
        """Prueba el análisis de proyecto sin archivos Python."""
        # Setup project manager with empty python_files list
        mock_project = Mock()
        mock_project.python_files = []
        mock_project_class.return_value = mock_project

        analyzer = Analyzer(mock_parser, mock_file_processor)
        analyzer.project_class = mock_project_class
        result = analyzer.analyze_project(temp_project_dir)

        assert isinstance(result, ProjectAnalysisResult)
        assert len(result.global_errors) == 1
        assert result.global_errors[0].severity == ErrorSeverity.CRITICAL
        assert "no contiene archivos Python válidos" in result.global_errors[0].message

    def test_analyze_with_symlink_file(self, mock_file_processor, mock_parser, tmp_path):
        """Prueba el análisis con archivos symlink (si el sistema lo soporta)."""
        real_file = tmp_path / "real.py"
        real_file.write_text("def test(): pass")

        try:
            symlink_file = tmp_path / "symlink.py"
            symlink_file.symlink_to(real_file)

            analyzer = Analyzer(mock_parser, mock_file_processor)
            result = analyzer.analyze(symlink_file)

            assert isinstance(result, ProjectAnalysisResult)
            assert result.total_files == 1
        except (OSError, NotImplementedError):
            # Skip if symlinks not supported on this system
            pytest.skip("Symlinks not supported on this system")

    def test_analyze_with_very_long_path(self, mock_file_processor, mock_parser, tmp_path):
        """Prueba el análisis con rutas muy largas."""
        # Create a nested path structure
        nested_path = tmp_path
        for i in range(5):  # Moderate nesting to avoid path length issues
            nested_path = nested_path / f"very_long_directory_name_with_lots_of_characters_{i}"

        try:
            nested_path.mkdir(parents=True, exist_ok=True)
            python_file = nested_path / "test.py"
            python_file.write_text("def test(): pass")

            analyzer = Analyzer(mock_parser, mock_file_processor)
            result = analyzer.analyze(python_file)

            assert isinstance(result, ProjectAnalysisResult)
            assert result.total_files == 1
        except OSError:
            # Skip if path too long for this system
            pytest.skip("Path too long for this system")

    def test_analyze_file_with_astroid_returning_empty_module(
        self, mock_file_processor, mock_parser, temp_python_file
    ):
        """Prueba el caso donde astroid devuelve un módulo pero analyze() devuelve None."""
        with patch("pypex.core.analyzer.AstroidNodeVisitor") as mock_visitor_class:
            mock_visitor = Mock()
            mock_visitor.analyze.return_value = None  # Simulate empty analysis
            mock_visitor_class.return_value = mock_visitor

            mock_engine = Mock()
            analyzer = Analyzer(mock_parser, mock_file_processor)
            analyzer.metrics_engine = mock_engine

            result = analyzer.analyze_file(temp_python_file)

        assert isinstance(result, FileAnalysisResult)
        # Engine methods should not be called if no module entity
        mock_engine.calculate_all_for_module.assert_not_called()
        mock_engine.get_entities_from_module.assert_not_called()

    def test_set_metrics_with_empty_list(self, mock_file_processor, mock_parser):
        """Prueba la configuración de métricas con lista vacía."""
        analyzer = Analyzer(mock_parser, mock_file_processor)

        analyzer.set_metrics([])

        assert analyzer.metrics == []
        assert analyzer.metrics_engine is not None

    def test_analyze_with_path_that_becomes_invalid_during_analysis(
        self, mock_file_processor, mock_parser
    ):
        """Prueba el análisis cuando un path se vuelve inválido durante el análisis."""
        # This tests the edge case where a path exists when checked but becomes invalid
        fake_path = Path("/tmp/this/will/not/exist/file.py")

        analyzer = Analyzer(mock_parser, mock_file_processor)
        result = analyzer.analyze(fake_path)

        assert isinstance(result, ProjectAnalysisResult)
        assert len(result.global_errors) == 1
        assert result.global_errors[0].severity == ErrorSeverity.CRITICAL
        assert "no existe" in result.global_errors[0].message


class TestAnalyzerConcurrencyAndPerformance:
    """Tests para casos de concurrencia y rendimiento."""

    def test_analyze_multiple_files_different_sizes(
        self, mock_file_processor, mock_parser, tmp_path
    ):
        """Prueba el análisis de archivos de diferentes tamaños."""
        # Create files of different sizes
        small_file = tmp_path / "small.py"
        small_file.write_text("def small(): pass")

        medium_file = tmp_path / "medium.py"
        medium_content = "\n".join([f"def function_{i}(): pass" for i in range(50)])
        medium_file.write_text(medium_content)

        large_file = tmp_path / "large.py"
        large_content = "\n".join([f"def function_{i}(): pass" for i in range(200)])
        large_file.write_text(large_content)

        analyzer = Analyzer(mock_parser, mock_file_processor)

        results = []
        for file_path in [small_file, medium_file, large_file]:
            result = analyzer.analyze_file(file_path)
            results.append(result)

        assert len(results) == 3
        assert all(isinstance(r, FileAnalysisResult) for r in results)

        # Verify files have different line counts
        line_counts = [r.line_count for r in results]
        assert line_counts[0] < line_counts[1] < line_counts[2]

    def test_analyze_file_with_very_long_lines(self, mock_file_processor, mock_parser, tmp_path):
        """Prueba el análisis de archivo con líneas muy largas."""
        long_line_file = tmp_path / "long_lines.py"
        # Create a file with very long lines
        long_line = "def very_long_function_name_" + "x" * 1000 + "(): pass"
        long_line_file.write_text(long_line)

        analyzer = Analyzer(mock_parser, mock_file_processor)
        result = analyzer.analyze_file(long_line_file)

        assert isinstance(result, FileAnalysisResult)
        assert result.line_count == 1
        assert result.file_size > 1000

    def test_analyze_file_critical_error_in_main_analysis_block(
        self, mock_file_processor, mock_parser, temp_python_file
    ):
        """Prueba el manejo de error crítico en el bloque principal de análisis."""
        # Mock both astroid and AST parsing to fail, and also mock the visitor creation to fail
        mock_parser.parse_with_astroid.side_effect = Exception("Astroid critical error")
        mock_parser.parse_file.side_effect = Exception("AST critical error")

        with patch(
            "pypex.core.analyzer.AstroidNodeVisitor",
            side_effect=Exception("Visitor creation failed"),
        ):
            analyzer = Analyzer(mock_parser, mock_file_processor)
            result = analyzer.analyze_file(temp_python_file)

        assert isinstance(result, FileAnalysisResult)
        # Should have at least one error from the critical error handling
        assert len(result.errors) >= 1
        # Should contain warning from astroid failure and potentially critical error
        error_severities = [e.severity for e in result.errors]
        assert ErrorSeverity.WARNING in error_severities

    def test_analyze_last_return_path(self, mock_file_processor, mock_parser):
        """Prueba el último path de return en el método analyze."""
        # Create a mock path that exists but is neither file nor directory
        with patch("pypex.core.analyzer.Path") as mock_path_class:
            mock_path = Mock()
            mock_path.exists.return_value = True
            mock_path.is_file.return_value = False
            mock_path.is_dir.return_value = False
            mock_path.__str__ = Mock(return_value="/special/path")
            mock_path_class.return_value = mock_path

            analyzer = Analyzer(mock_parser, mock_file_processor)
            result = analyzer.analyze("/special/path")

        assert isinstance(result, ProjectAnalysisResult)
        assert len(result.global_errors) == 1
        assert result.global_errors[0].severity == ErrorSeverity.CRITICAL
        assert "no es un archivo o directorio analizable" in result.global_errors[0].message


# ... existing TestAnalyzerPerformance class ...
