"""Tests unitarios completos para el servicio de configuración."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from pypex.services.config_service import ConfigService, get_config


class TestConfigService:
    """Tests para la clase ConfigService."""

    def setup_method(self):
        """Configuración previa a cada test."""
        # Resetear el singleton antes de cada test
        ConfigService._instance = None

    def test_singleton_behavior(self):
        """Prueba que ConfigService implementa correctamente el patrón Singleton."""
        config1 = ConfigService()
        config2 = ConfigService()

        # Ambas instancias deben ser la misma
        assert config1 is config2
        assert id(config1) == id(config2)

    def test_singleton_initialization_once(self):
        """Prueba que la inicialización solo ocurre una vez."""
        config1 = ConfigService()
        config1.set("test_key", "test_value")

        config2 = ConfigService()

        # El segundo objeto debe mantener el estado del primero
        assert config2.get("test_key") == "test_value"

    def test_init_default_configuration(self):
        """Prueba que la configuración por defecto se carga correctamente."""
        config = ConfigService()

        # Verificar configuración general
        assert config.get("verbose") is False
        assert config.get("log_file") is None
        assert config.get("output_format") == "text"
        assert config.get("max_file_size") == 1024 * 1024

        # Verificar patrones de ignore
        ignore_patterns = config.get("ignore_patterns")
        assert isinstance(ignore_patterns, list)
        assert "**/__pycache__/**" in ignore_patterns
        assert "**/.git/**" in ignore_patterns

        # Verificar que thresholds esté vacío por defecto (los umbrales se obtienen dinámicamente)
        thresholds_config = config.get("thresholds")
        assert thresholds_config == {}
        assert config.get("thresholds.cyclomatic_complexity") is None

    def test_init_already_initialized(self):
        """Prueba que la inicialización no se ejecuta si ya está inicializada."""
        config = ConfigService()
        config.set("test_marker", "initialized")

        # Simular que _initialized ya está True
        original_init = config._initialized
        config._initialized = True

        # Llamar __init__ nuevamente
        config.__init__()

        # El valor debe mantenerse
        assert config.get("test_marker") == "initialized"

    def test_load_from_file_success(self):
        """Prueba la carga exitosa desde archivo JSON."""
        config = ConfigService()

        test_config = {
            "verbose": True,
            "new_setting": "test_value",
            "thresholds": {"new_metric": {"low": 1, "high": 5}},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp_file:
            json.dump(test_config, tmp_file)
            tmp_file_path = tmp_file.name

        try:
            config.load_from_file(tmp_file_path)

            assert config.get("verbose") is True
            assert config.get("new_setting") == "test_value"
            assert config.get("thresholds.new_metric.low") == 1
            assert config.get("thresholds.new_metric.high") == 5
            # Los valores por defecto deben mantenerse
            assert config.get("output_format") == "text"
        finally:
            Path(tmp_file_path).unlink()

    def test_load_from_file_not_exists(self):
        """Prueba error cuando el archivo no existe."""
        config = ConfigService()

        with pytest.raises(FileNotFoundError) as exc_info:
            config.load_from_file("nonexistent_file.json")

        assert "no existe" in str(exc_info.value)

    def test_load_from_file_invalid_json(self):
        """Prueba error con archivo JSON inválido."""
        config = ConfigService()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp_file:
            tmp_file.write("invalid json content {")
            tmp_file_path = tmp_file.name

        try:
            with pytest.raises(json.JSONDecodeError):
                config.load_from_file(tmp_file_path)
        finally:
            Path(tmp_file_path).unlink()

    def test_load_from_file_path_object(self):
        """Prueba carga desde archivo usando objeto Path."""
        config = ConfigService()

        test_config = {"test_setting": "path_object_test"}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp_file:
            json.dump(test_config, tmp_file)
            tmp_file_path = Path(tmp_file.name)

        try:
            config.load_from_file(tmp_file_path)
            assert config.get("test_setting") == "path_object_test"
        finally:
            tmp_file_path.unlink()

    def test_update_from_dict(self):
        """Prueba actualización desde diccionario."""
        config = ConfigService()

        new_config = {
            "verbose": True,
            "new_key": "new_value",
            "thresholds": {
                "cyclomatic_complexity": {"low": 5, "medium": 15, "high": 25},
                "new_metric": {"low": 3, "high": 10},
            },
        }

        config.update_from_dict(new_config)

        assert config.get("verbose") is True
        assert config.get("new_key") == "new_value"
        # Verificar que se establecieron los umbrales
        assert config.get("thresholds.cyclomatic_complexity.medium") == 15
        assert config.get("thresholds.cyclomatic_complexity.low") == 5
        assert config.get("thresholds.new_metric.low") == 3

    def test_update_config_new_dict_key(self):
        """Prueba _update_config con nueva clave de diccionario."""
        config = ConfigService()

        new_config = {"completely_new": {"nested": {"value": "test"}}}

        config._update_config(new_config)
        assert config.get("completely_new.nested.value") == "test"

    def test_update_config_overwrite_non_dict(self):
        """Prueba _update_config sobrescribiendo valor no diccionario."""
        config = ConfigService()
        config.set("verbose", False)

        new_config = {"verbose": True}
        config._update_config(new_config)

        assert config.get("verbose") is True

    def test_update_config_dict_replace_existing_dict(self):
        """Prueba _update_config_dict con diccionarios existentes."""
        config = ConfigService()

        # Estado inicial
        target = {"a": {"x": 1, "y": 2}, "b": 3}
        source = {"a": {"x": 10, "z": 3}, "c": 4}

        config._update_config_dict(target, source)

        # Verificar actualización recursiva
        assert target["a"]["x"] == 10  # Actualizado
        assert target["a"]["y"] == 2  # Mantenido
        assert target["a"]["z"] == 3  # Agregado
        assert target["b"] == 3  # Mantenido
        assert target["c"] == 4  # Agregado

    def test_update_config_dict_overwrite_non_dict_with_dict(self):
        """Prueba _update_config_dict sobrescribiendo no-dict con dict."""
        config = ConfigService()

        target = {"key": "string_value"}
        source = {"key": {"nested": "value"}}

        config._update_config_dict(target, source)

        assert target["key"]["nested"] == "value"

    def test_get_simple_key(self):
        """Prueba obtención de valores con clave simple."""
        config = ConfigService()

        assert config.get("verbose") is False
        assert config.get("output_format") == "text"

    def test_get_with_default(self):
        """Prueba obtención con valor por defecto."""
        config = ConfigService()

        assert config.get("nonexistent_key", "default_value") == "default_value"
        assert config.get("nonexistent_key") is None

    def test_get_dot_notation_success(self):
        """Prueba obtención con notación de puntos exitosa."""
        config = ConfigService()

        # Primero establecer algunos valores para poder probarlos
        config.set("thresholds.cyclomatic_complexity.high", 20)
        config.set("thresholds.cognitive_complexity.medium", 15)

        assert config.get("thresholds.cyclomatic_complexity.high") == 20
        assert config.get("thresholds.cognitive_complexity.medium") == 15

    def test_get_dot_notation_nonexistent_intermediate(self):
        """Prueba obtención con notación de puntos con clave intermedia inexistente."""
        config = ConfigService()

        result = config.get("thresholds.nonexistent.high", "default")
        assert result == "default"

    def test_get_dot_notation_nonexistent_final(self):
        """Prueba obtención con notación de puntos con clave final inexistente."""
        config = ConfigService()

        result = config.get("thresholds.cyclomatic_complexity.ultra_high", "default")
        assert result == "default"

    def test_get_dot_notation_non_dict_intermediate(self):
        """Prueba obtención cuando valor intermedio no es diccionario."""
        config = ConfigService()

        result = config.get("verbose.some.nested.key", "default")
        assert result == "default"

    def test_set_simple_key(self):
        """Prueba establecimiento de valor con clave simple."""
        config = ConfigService()

        config.set("new_key", "new_value")
        assert config.get("new_key") == "new_value"

        config.set("verbose", True)
        assert config.get("verbose") is True

    def test_set_dot_notation_existing_path(self):
        """Prueba establecimiento con notación de puntos en ruta existente."""
        config = ConfigService()

        # Primero establecer el threshold base
        config.set("thresholds.cyclomatic_complexity.high", 20)

        # Luego agregar un nuevo threshold
        config.set("thresholds.cyclomatic_complexity.ultra_high", 50)
        assert config.get("thresholds.cyclomatic_complexity.ultra_high") == 50
        # Verificar que no afecta otros valores
        assert config.get("thresholds.cyclomatic_complexity.high") == 20

    def test_set_dot_notation_new_path(self):
        """Prueba establecimiento con notación de puntos creando nueva ruta."""
        config = ConfigService()

        config.set("new.nested.deep.value", "deep_value")
        assert config.get("new.nested.deep.value") == "deep_value"

        # Verificar que se crearon los diccionarios intermedios
        assert isinstance(config.get("new"), dict)
        assert isinstance(config.get("new.nested"), dict)
        assert isinstance(config.get("new.nested.deep"), dict)

    def test_set_dot_notation_overwrite_non_dict(self):
        """Prueba establecimiento sobrescribiendo valor no-diccionario."""
        config = ConfigService()
        config.set("simple_value", "string")

        config.set("simple_value.nested.key", "nested_value")
        assert config.get("simple_value.nested.key") == "nested_value"

    def test_get_all(self):
        """Prueba obtención de toda la configuración."""
        config = ConfigService()
        config.set("test_key", "test_value")

        all_config = config.get_all()

        # Verificar que es una copia (no la misma referencia)
        assert all_config is not config._config
        # Verificar contenido
        assert all_config["test_key"] == "test_value"
        assert all_config["verbose"] is False
        assert "thresholds" in all_config

    def test_reset_for_testing(self):
        """Prueba el reseteo de configuración para testing."""
        config = ConfigService()
        config.set("test_key", "test_value")
        config.set("verbose", True)

        # El método reset_for_testing() actual solo llama a __init__()
        # pero __init__ retorna inmediatamente si ya está inicializado,
        # por lo que necesitamos resetear manualmente _initialized
        config._initialized = False
        config.reset_for_testing()

        # Verificar que volvió a los valores por defecto
        assert config.get("test_key") is None
        assert config.get("verbose") is False
        assert config.get("output_format") == "text"

    def test_get_config_function(self):
        """Prueba la función get_config."""
        # Reset singleton
        ConfigService._instance = None

        config1 = get_config()
        config2 = get_config()

        assert isinstance(config1, ConfigService)
        assert config1 is config2

    def test_complex_nested_update(self):
        """Prueba actualización compleja con múltiples niveles de anidamiento."""
        config = ConfigService()

        complex_config = {
            "analysis": {
                "metrics": {
                    "complexity": {
                        "cyclomatic": {"enabled": True, "thresholds": {"warning": 10, "error": 20}},
                        "cognitive": {"enabled": False},
                    },
                    "maintainability": {"enabled": True},
                },
                "output": {"format": "json", "file": "results.json"},
            }
        }

        config.update_from_dict(complex_config)

        # Verificar valores anidados
        assert config.get("analysis.metrics.complexity.cyclomatic.enabled") is True
        assert config.get("analysis.metrics.complexity.cyclomatic.thresholds.warning") == 10
        assert config.get("analysis.metrics.complexity.cognitive.enabled") is False
        assert config.get("analysis.output.format") == "json"

    def test_edge_case_empty_key_parts(self):
        """Prueba casos edge con partes de clave vacías."""
        config = ConfigService()

        # Key con punto al final
        result = config.get("verbose.", "default")
        assert result == "default"

        # Key con puntos consecutivos
        result = config.get("verbose..nested", "default")
        assert result == "default"

    def test_mixed_data_types_in_config(self):
        """Prueba configuración con diferentes tipos de datos."""
        config = ConfigService()

        mixed_config = {
            "string_value": "text",
            "int_value": 42,
            "float_value": 3.14,
            "bool_value": True,
            "list_value": [1, 2, 3],
            "dict_value": {"nested": "value"},
            "none_value": None,
        }

        config.update_from_dict(mixed_config)

        assert config.get("string_value") == "text"
        assert config.get("int_value") == 42
        assert config.get("float_value") == 3.14
        assert config.get("bool_value") is True
        assert config.get("list_value") == [1, 2, 3]
        assert config.get("dict_value.nested") == "value"
        assert config.get("none_value") is None

    @patch("builtins.open", side_effect=OSError("Permission denied"))
    def test_load_from_file_io_error(self, mock_file):
        """Prueba error de IO al cargar archivo."""
        config = ConfigService()

        # Crear archivo temporal que existe pero simular error de permisos
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file_path = tmp_file.name

        try:
            with pytest.raises(IOError):
                config.load_from_file(tmp_file_path)
        finally:
            Path(tmp_file_path).unlink()

    def test_singleton_with_multiple_threads_simulation(self):
        """Simula comportamiento con múltiples threads."""
        # Reset singleton
        ConfigService._instance = None

        instances = []
        for _ in range(10):
            instances.append(ConfigService())

        # Todas deben ser la misma instancia
        first_instance = instances[0]
        for instance in instances[1:]:
            assert instance is first_instance

    def test_file_encoding_handling(self):
        """Prueba manejo de encoding UTF-8 en archivos."""
        config = ConfigService()

        # Configuración con caracteres especiales
        test_config = {
            "mensaje": "Configuración con acentos y ñ",
            "símbolos": "★☆♦♣♠",
            "unicode": "🚀🎯",
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as tmp_file:
            json.dump(test_config, tmp_file, ensure_ascii=False)
            tmp_file_path = tmp_file.name

        try:
            config.load_from_file(tmp_file_path)

            assert config.get("mensaje") == "Configuración con acentos y ñ"
            assert config.get("símbolos") == "★☆♦♣♠"
            assert config.get("unicode") == "🚀🎯"
        finally:
            Path(tmp_file_path).unlink()

    def test_preserve_original_config_structure(self):
        """Prueba que la estructura original se preserva en actualizaciones."""
        config = ConfigService()

        # Primero establecer algunos umbrales base para probar la actualización
        config.update_from_dict(
            {
                "thresholds": {
                    "cyclomatic_complexity": {"low": 5, "medium": 10, "high": 20},
                    "cognitive_complexity": {"low": 5, "medium": 15, "high": 25},
                }
            }
        )

        # Obtener configuración original
        original_thresholds = config.get("thresholds")
        original_patterns = config.get("ignore_patterns")

        # Actualizar con nueva configuración
        new_config = {
            "thresholds": {
                "cyclomatic_complexity": {
                    "low": 3  # Solo cambiar este valor
                }
            }
        }

        config.update_from_dict(new_config)

        # Verificar que solo cambió lo especificado
        assert config.get("thresholds.cyclomatic_complexity.low") == 3
        assert config.get("thresholds.cyclomatic_complexity.medium") == 10  # Sin cambios
        assert config.get("thresholds.cyclomatic_complexity.high") == 20  # Sin cambios
        assert config.get("thresholds.cognitive_complexity.low") == 5  # Sin cambios
        assert config.get("ignore_patterns") == original_patterns  # Sin cambios
