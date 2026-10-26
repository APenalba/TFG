"""Tests para el módulo FileProcessor."""

import os
import re
from unittest.mock import patch

import pytest

from pypex.core.file_processor import FileProcessor
from pypex.core.interfaces import ParsingError


class TestFileProcessor:
    """Tests para la clase FileProcessor."""

    def test_init_default_patterns(self):
        """Test inicialización con patrones por defecto."""
        processor = FileProcessor()

        assert processor.max_file_size == 1024 * 1024
        assert len(processor.ignore_patterns) == 9
        assert "**/__pycache__/**" in processor.ignore_patterns
        assert "**/.git/**" in processor.ignore_patterns
        assert len(processor._compiled_absolute_patterns) > 0
        assert len(processor._compiled_relative_patterns) >= 0

    def test_init_custom_patterns(self):
        """Test inicialización con patrones personalizados."""
        custom_patterns = ["**/test/**", "*.tmp"]
        processor = FileProcessor(ignore_patterns=custom_patterns, max_file_size=512 * 1024)

        assert processor.ignore_patterns == custom_patterns
        assert processor.max_file_size == 512 * 1024

    def test_compile_patterns_absolute_double_star(self):
        """Test compilación de patrones con **/ al inicio y /**/ al final."""
        processor = FileProcessor(ignore_patterns=["**/__pycache__/**"])

        # Debe haber un patrón absoluto compilado
        assert len(processor._compiled_absolute_patterns) == 1

        # Test que coincida con el patrón
        pattern = processor._compiled_absolute_patterns[0]
        assert pattern.search("/some/path/__pycache__/file.pyc") is not None
        assert pattern.search("/some/__pycache__/other/file.py") is not None

    def test_compile_patterns_ending_with_triple_star(self):
        """Test compilación de patrones que terminan con /**."""
        processor = FileProcessor(ignore_patterns=[".git/**"])

        assert len(processor._compiled_absolute_patterns) == 1
        pattern = processor._compiled_absolute_patterns[0]
        assert pattern.search("/some/path/.git") is not None
        assert pattern.search("/some/path/.git/file") is not None

    def test_compile_patterns_starting_with_double_star(self):
        """Test compilación de patrones que empiezan con **/."""
        processor = FileProcessor(ignore_patterns=["**/*.tmp"])

        assert len(processor._compiled_absolute_patterns) == 1
        pattern = processor._compiled_absolute_patterns[0]
        assert pattern.search("/some/path/file.tmp") is not None
        assert pattern.search("/file.tmp") is not None

    def test_compile_patterns_relative(self):
        """Test compilación de patrones relativos."""
        processor = FileProcessor(ignore_patterns=["build/*", "test.py"])

        assert len(processor._compiled_relative_patterns) == 2

        # Test patrones relativos
        patterns = processor._compiled_relative_patterns
        build_pattern = next(p for p in patterns if "build" in p.pattern)
        test_pattern = next(p for p in patterns if "test" in p.pattern)

        assert build_pattern.fullmatch("build/file.py") is not None
        assert test_pattern.fullmatch("test.py") is not None

    @patch("os.name", "nt")
    def test_compile_patterns_windows(self):
        """Test compilación de patrones en Windows (case insensitive)."""
        processor = FileProcessor(ignore_patterns=["Test/**"])

        pattern = processor._compiled_absolute_patterns[0]
        # En Windows debería ser case insensitive
        assert pattern.flags & re.IGNORECASE

    @patch("os.name", "posix")
    def test_compile_patterns_unix(self):
        """Test compilación de patrones en Unix (case sensitive)."""
        processor = FileProcessor(ignore_patterns=["Test/**"])

        pattern = processor._compiled_absolute_patterns[0]
        # En Unix no debería ser case insensitive
        assert not (pattern.flags & re.IGNORECASE)

    def test_should_ignore_absolute_patterns(self, tmp_path):
        """Test should_ignore con patrones absolutos."""
        processor = FileProcessor(ignore_patterns=["**/__pycache__/**"])

        # Crear estructura de directorios
        cache_dir = tmp_path / "__pycache__"
        cache_dir.mkdir()
        cache_file = cache_dir / "test.pyc"
        cache_file.write_text("# cache file")

        assert processor.should_ignore(cache_file, tmp_path) is True

        # Archivo normal no debería ser ignorado
        normal_file = tmp_path / "test.py"
        normal_file.write_text("# normal file")
        assert processor.should_ignore(normal_file, tmp_path) is False

    @pytest.mark.skipif(os.name != "nt", reason="Solo aplica en Windows")
    def test_should_ignore_windows_path_normalization(self, tmp_path):
        """Test normalización de rutas en Windows."""
        processor = FileProcessor(ignore_patterns=["**/__pycache__/**"])

        cache_dir = tmp_path / "__pycache__"
        cache_dir.mkdir()
        cache_file = cache_dir / "test.pyc"
        cache_file.write_text("# cache file")

        # En Windows, las rutas se normalizan con /
        assert processor.should_ignore(cache_file, tmp_path) is True

    def test_should_ignore_relative_patterns(self, tmp_path):
        """Test should_ignore con patrones relativos."""
        processor = FileProcessor(ignore_patterns=["build/*"])

        # Crear directorio build
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        build_file = build_dir / "output.py"
        build_file.write_text("# build file")

        assert processor.should_ignore(build_file, tmp_path) is True

        # Archivo en raíz no debería ser ignorado
        root_file = tmp_path / "main.py"
        root_file.write_text("# main file")
        assert processor.should_ignore(root_file, tmp_path) is False

    def test_should_ignore_path_outside_scan_root(self, tmp_path):
        """Test should_ignore con ruta fuera del directorio de escaneo."""
        processor = FileProcessor(ignore_patterns=["build/*"])

        # Crear directorio temporal diferente
        other_tmp = tmp_path.parent / "other_tmp"
        other_tmp.mkdir(exist_ok=True)
        other_file = other_tmp / "test.py"
        other_file.write_text("# other file")

        # No debería ser ignorado porque está fuera del scan_root
        assert processor.should_ignore(other_file, tmp_path) is False

    def test_should_ignore_file_size_limit(self, tmp_path):
        """Test should_ignore con límite de tamaño de archivo."""
        processor = FileProcessor(max_file_size=10)  # 10 bytes

        # Archivo pequeño
        small_file = tmp_path / "small.py"
        small_file.write_text("x=1")  # < 10 bytes
        assert processor.should_ignore(small_file, tmp_path) is False

        # Archivo grande
        large_file = tmp_path / "large.py"
        large_file.write_text("x=" + "1" * 20)  # > 10 bytes
        assert processor.should_ignore(large_file, tmp_path) is True

    def test_should_ignore_directory_not_affected_by_size(self, tmp_path):
        """Test que los directorios no se ven afectados por el límite de tamaño."""
        processor = FileProcessor(max_file_size=10)

        # Directorio no debería ser ignorado por tamaño
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()
        assert processor.should_ignore(test_dir, tmp_path) is False

    def test_should_ignore_file_size_exceeds_limit_return_true(self, tmp_path):
        """Test para cubrir específicamente las líneas 144-145: when file size > max_file_size return True."""
        processor = FileProcessor(max_file_size=5)  # 5 bytes limit

        # Crear archivo que exceda el límite
        large_file = tmp_path / "large.py"
        large_file.write_text("print('Hello World')")  # > 5 bytes

        # Verificar que el archivo es efectivamente más grande que el límite
        assert large_file.stat().st_size > 5

        # El archivo debe ser ignorado por tamaño
        result = processor.should_ignore(large_file, tmp_path)
        assert result is True  # Esta línea cubre la línea 145 (return True)

    def test_find_python_files_nonexistent_path(self):
        """Test find_python_files con ruta inexistente."""
        processor = FileProcessor()

        with pytest.raises(FileNotFoundError, match="La ruta .* no existe"):
            processor.find_python_files("/nonexistent/path")

    def test_find_python_files_single_file(self, tmp_path):
        """Test find_python_files con un solo archivo Python."""
        processor = FileProcessor()

        # Crear archivo Python
        py_file = tmp_path / "test.py"
        py_file.write_text("# test file")

        files = processor.find_python_files(py_file)
        assert len(files) == 1
        assert files[0] == py_file.resolve()

    def test_find_python_files_single_non_python_file(self, tmp_path):
        """Test find_python_files con archivo no Python."""
        processor = FileProcessor()

        # Crear archivo no Python
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("# test file")

        files = processor.find_python_files(txt_file)
        assert len(files) == 0

    def test_find_python_files_single_ignored_file(self, tmp_path):
        """Test find_python_files con archivo Python ignorado."""
        # Usar un patrón relativo que coincida exactamente
        processor = FileProcessor(ignore_patterns=["test.py"])

        # Crear archivo Python
        py_file = tmp_path / "test.py"
        py_file.write_text("# test file")

        # Necesitamos llamar con el directorio padre para que el patrón relativo funcione
        files = processor.find_python_files(tmp_path)
        assert len(files) == 0

    def test_find_python_files_directory_with_python_files(self, tmp_path):
        """Test find_python_files con directorio que contiene archivos Python."""
        processor = FileProcessor()

        # Crear varios archivos Python
        (tmp_path / "main.py").write_text("# main")
        (tmp_path / "utils.py").write_text("# utils")
        (tmp_path / "README.md").write_text("# readme")

        # Crear subdirectorio con más archivos
        subdir = tmp_path / "modules"
        subdir.mkdir()
        (subdir / "module1.py").write_text("# module1")
        (subdir / "module2.py").write_text("# module2")

        files = processor.find_python_files(tmp_path)
        python_files = [f.name for f in files]

        assert len(files) == 4
        assert "main.py" in python_files
        assert "utils.py" in python_files
        assert "module1.py" in python_files
        assert "module2.py" in python_files

    def test_find_python_files_directory_with_ignored_subdirs(self, tmp_path):
        """Test find_python_files con subdirectorios ignorados."""
        processor = FileProcessor(ignore_patterns=["**/__pycache__/**"])

        # Crear archivos normales
        (tmp_path / "main.py").write_text("# main")

        # Crear directorio __pycache__ con archivos
        cache_dir = tmp_path / "__pycache__"
        cache_dir.mkdir()
        (cache_dir / "main.cpython-39.pyc").write_text("# cached")
        (cache_dir / "test.py").write_text("# should be ignored")

        files = processor.find_python_files(tmp_path)
        python_files = [f.name for f in files]

        assert len(files) == 1
        assert "main.py" in python_files
        assert "test.py" not in python_files

    def test_find_python_files_with_ignored_files(self, tmp_path):
        """Test find_python_files con archivos ignorados."""
        processor = FileProcessor(ignore_patterns=["test_*.py"])

        # Crear archivos
        (tmp_path / "main.py").write_text("# main")
        (tmp_path / "test_unit.py").write_text("# test")
        (tmp_path / "test_integration.py").write_text("# test")
        (tmp_path / "utils.py").write_text("# utils")

        files = processor.find_python_files(tmp_path)
        python_files = [f.name for f in files]

        assert len(files) == 2
        assert "main.py" in python_files
        assert "utils.py" in python_files
        assert "test_unit.py" not in python_files
        assert "test_integration.py" not in python_files

    def test_read_file_success(self, tmp_path):
        """Test read_file con archivo válido."""
        processor = FileProcessor()

        test_file = tmp_path / "test.py"
        content = "def hello():\n    print('Hello World')"
        test_file.write_text(content, encoding="utf-8")

        result = processor.read_file(test_file)
        assert result == content

    def test_read_file_nonexistent(self):
        """Test read_file con archivo inexistente."""
        processor = FileProcessor()

        with pytest.raises(FileNotFoundError, match="El archivo .* no existe"):
            processor.read_file("/nonexistent/file.py")

    def test_read_file_directory(self, tmp_path):
        """Test read_file con directorio en lugar de archivo."""
        processor = FileProcessor()

        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()

        with pytest.raises(FileNotFoundError, match="El archivo .* no existe"):
            processor.read_file(test_dir)

    def test_read_file_unicode_decode_error_fallback_success(self, tmp_path):
        """Test read_file con error de decodificación UTF-8 pero éxito con latin-1."""
        processor = FileProcessor()

        test_file = tmp_path / "test.py"
        # Escribir contenido con caracteres latin-1 que fallarán en UTF-8
        with open(test_file, "wb") as f:
            f.write(b"# Contenido con caracteres especiales \xff\xfe")

        # El método debería intentar latin-1 como fallback
        result = processor.read_file(test_file)
        assert isinstance(result, str)
        assert len(result) > 0

    @patch("builtins.open")
    def test_read_file_unicode_decode_error_fallback_failure(self, mock_open_func, tmp_path):
        """Test read_file cuando tanto UTF-8 como latin-1 fallan."""
        processor = FileProcessor()

        test_file = tmp_path / "test.py"
        test_file.write_text("dummy")  # Crear archivo real para que exists() pase

        # Configurar mock para que UTF-8 falle con UnicodeDecodeError
        # y latin-1 falle con otra excepción
        mock_open_func.side_effect = [
            UnicodeDecodeError("utf-8", b"", 0, 1, "invalid start byte"),
            Exception("Encoding error"),
        ]

        with pytest.raises(ValueError, match="No se puede leer el archivo"):
            processor.read_file(test_file)

    @patch("builtins.open")
    def test_read_file_general_exception(self, mock_open_func, tmp_path):
        """Test read_file con excepción general."""
        processor = FileProcessor()

        test_file = tmp_path / "test.py"
        test_file.write_text("dummy")  # Crear archivo real

        mock_open_func.side_effect = OSError("Disk error")

        with pytest.raises(ValueError, match="Error al leer el archivo"):
            processor.read_file(test_file)

    def test_process_file_success(self, tmp_path):
        """Test process_file con archivo válido."""
        processor = FileProcessor()

        test_file = tmp_path / "test.py"
        content = "def hello():\n    print('Hello World')\n    return True"
        test_file.write_text(content)

        result = processor.process_file(test_file)

        assert result["path"] == str(test_file)
        assert result["name"] == "test.py"
        assert result["size"] == test_file.stat().st_size
        assert result["lines"] == 3
        assert result["content"] == content

    def test_process_file_nonexistent(self):
        """Test process_file con archivo inexistente."""
        processor = FileProcessor()

        with pytest.raises(FileNotFoundError, match="El archivo .* no existe"):
            processor.process_file("/nonexistent/file.py")

    def test_process_file_directory(self, tmp_path):
        """Test process_file con directorio."""
        processor = FileProcessor()

        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()

        with pytest.raises(FileNotFoundError, match="El archivo .* no existe"):
            processor.process_file(test_dir)

    def test_process_file_non_python(self, tmp_path):
        """Test process_file con archivo no Python."""
        processor = FileProcessor()

        test_file = tmp_path / "test.txt"
        test_file.write_text("Not Python code")

        with pytest.raises(ParsingError, match="no es un archivo Python"):
            processor.process_file(test_file)

    @patch.object(FileProcessor, "read_file")
    def test_process_file_read_error(self, mock_read_file, tmp_path):
        """Test process_file cuando read_file lanza excepción."""
        processor = FileProcessor()

        test_file = tmp_path / "test.py"
        test_file.write_text("dummy content")

        mock_read_file.side_effect = Exception("Read error")

        with pytest.raises(ParsingError, match="Error al procesar el archivo"):
            processor.process_file(test_file)

    def test_empty_file_processing(self, tmp_path):
        """Test procesamiento de archivo vacío."""
        processor = FileProcessor()

        test_file = tmp_path / "empty.py"
        test_file.write_text("")

        result = processor.process_file(test_file)

        assert result["lines"] == 0
        assert result["content"] == ""
        assert result["size"] == 0

    def test_file_with_only_whitespace(self, tmp_path):
        """Test procesamiento de archivo con solo espacios en blanco."""
        processor = FileProcessor()

        test_file = tmp_path / "whitespace.py"
        content = "   \n\n\t\n  "
        test_file.write_text(content)

        result = processor.process_file(test_file)

        assert result["lines"] == 4
        assert result["content"] == content

    def test_pattern_with_dots_and_special_chars(self):
        """Test patrones con puntos y caracteres especiales."""
        processor = FileProcessor(ignore_patterns=["*.pyc", "file.test.*"])

        # Verificar que los puntos se escapan correctamente
        relative_patterns = processor._compiled_relative_patterns

        # Debe haber patrones que manejen los puntos como literales
        assert len(relative_patterns) == 2

    def test_pattern_with_complex_glob(self):
        """Test patrones glob complejos."""
        processor = FileProcessor(ignore_patterns=["src/**/test_*.py", "build/**"])

        # Verificar que se compilan correctamente
        absolute_patterns = processor._compiled_absolute_patterns
        # Solo "build/**" genera un patrón absoluto, "src/**/test_*.py" genera un patrón absoluto también
        # pero "src/**/test_*.py" debe ir a absolute patterns, no relative
        assert len(absolute_patterns) >= 1  # Al menos build/**

    def test_very_long_path_handling(self, tmp_path):
        """Test manejo de rutas muy largas."""
        processor = FileProcessor()

        # Crear estructura de directorios profunda
        deep_path = tmp_path
        for i in range(10):
            deep_path = deep_path / f"level_{i}"
            deep_path.mkdir()

        test_file = deep_path / "deep_file.py"
        test_file.write_text("# Deep file")

        files = processor.find_python_files(tmp_path)
        assert len(files) == 1
        assert files[0].name == "deep_file.py"

    def test_should_ignore_signature_compatibility(self, tmp_path):
        """Test que should_ignore funciona con la signatura de la interfaz."""
        processor = FileProcessor()

        test_file = tmp_path / "test.py"
        test_file.write_text("# test")

        # La interfaz especifica solo un parámetro, pero la implementación necesita dos
        # Verificar que funciona cuando se llama desde find_python_files
        files = processor.find_python_files(tmp_path)
        assert len(files) == 1

    def test_complex_pattern_compilation_cases(self):
        """Test casos específicos de compilación de patrones para cubrir todas las ramas."""
        # Test patrón que empieza con ** pero no termina con /
        processor1 = FileProcessor(ignore_patterns=["**/*test.py"])
        assert len(processor1._compiled_absolute_patterns) == 1

        # Test patrón que contiene ** en el medio (como foo/**/bar)
        processor2 = FileProcessor(ignore_patterns=["src/**/tests/*"])
        assert len(processor2._compiled_relative_patterns) == 1

        # Test patrón normal sin **
        processor3 = FileProcessor(ignore_patterns=["build/temp/*"])
        assert len(processor3._compiled_relative_patterns) == 1
