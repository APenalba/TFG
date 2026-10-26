"""Tests para el módulo __main__ de PyPex.

Estos tests verifican que el punto de entrada principal funcione correctamente
cuando PyPex se ejecuta como un módulo.
"""

import importlib.util
from pathlib import Path
from unittest.mock import patch

import pytest


class TestMainModule:
    """Tests para el módulo __main__ de PyPex."""

    def test_main_module_imports_successfully(self):
        """Prueba que el módulo __main__ se puede importar sin errores."""
        # Obtener la ruta al archivo __main__.py
        main_module_path = Path(__file__).parent.parent.parent / "pypex" / "__main__.py"

        # Cargar el módulo dinámicamente
        spec = importlib.util.spec_from_file_location("pypex.__main__", main_module_path)
        main_module = importlib.util.module_from_spec(spec)

        # Esto no debería lanzar ninguna excepción
        with patch("pypex.cli.main") as mock_main:
            spec.loader.exec_module(main_module)
            # Verificar que main no se llamó durante la importación
            mock_main.assert_not_called()

    @patch("pypex.cli.main")
    def test_main_module_calls_cli_main_when_executed_directly(self, mock_main):
        """Prueba que main() se llama cuando el módulo se ejecuta directamente."""
        # Obtener la ruta al archivo __main__.py
        main_module_path = Path(__file__).parent.parent.parent / "pypex" / "__main__.py"

        # Simular que el módulo se ejecuta directamente
        spec = importlib.util.spec_from_file_location("__main__", main_module_path)
        main_module = importlib.util.module_from_spec(spec)
        main_module.__name__ = "__main__"

        # Ejecutar el módulo
        spec.loader.exec_module(main_module)

        # Verificar que main() fue llamada
        mock_main.assert_called_once()

    @patch("pypex.cli.main")
    def test_main_module_does_not_call_main_when_imported(self, mock_main):
        """Prueba que main() NO se llama cuando el módulo se importa."""
        # Obtener la ruta al archivo __main__.py
        main_module_path = Path(__file__).parent.parent.parent / "pypex" / "__main__.py"

        # Simular que el módulo se importa (no se ejecuta directamente)
        spec = importlib.util.spec_from_file_location("pypex.__main__", main_module_path)
        main_module = importlib.util.module_from_spec(spec)
        main_module.__name__ = "pypex.__main__"  # No es "__main__"

        # Ejecutar el módulo
        spec.loader.exec_module(main_module)

        # Verificar que main() NO fue llamada
        mock_main.assert_not_called()

    def test_main_module_has_correct_docstring(self):
        """Prueba que el módulo __main__ tiene la documentación correcta."""
        # Obtener la ruta al archivo __main__.py
        main_module_path = Path(__file__).parent.parent.parent / "pypex" / "__main__.py"

        # Leer el contenido del archivo
        content = main_module_path.read_text(encoding="utf-8")

        # Verificar que contiene el docstring esperado
        assert '"""Punto de entrada para ejecutar PyPex como módulo."""' in content

    def test_main_module_imports_from_correct_module(self):
        """Prueba que el módulo __main__ importa desde pypex.cli."""
        # Obtener la ruta al archivo __main__.py
        main_module_path = Path(__file__).parent.parent.parent / "pypex" / "__main__.py"

        # Leer el contenido del archivo
        content = main_module_path.read_text(encoding="utf-8")

        # Verificar que contiene la importación correcta
        assert "from pypex.cli import main" in content

    @patch("pypex.cli.main", side_effect=Exception("Test exception"))
    def test_main_module_propagates_exceptions_from_cli_main(self, mock_main):
        """Prueba que las excepciones de cli.main() se propagan correctamente."""
        # Obtener la ruta al archivo __main__.py
        main_module_path = Path(__file__).parent.parent.parent / "pypex" / "__main__.py"

        # Simular que el módulo se ejecuta directamente
        spec = importlib.util.spec_from_file_location("__main__", main_module_path)
        main_module = importlib.util.module_from_spec(spec)
        main_module.__name__ = "__main__"

        # Ejecutar el módulo y verificar que la excepción se propaga
        with pytest.raises(Exception, match="Test exception"):
            spec.loader.exec_module(main_module)

    def test_main_module_file_exists(self):
        """Prueba que el archivo __main__.py existe en la ubicación correcta."""
        main_module_path = Path(__file__).parent.parent.parent / "pypex" / "__main__.py"
        assert main_module_path.exists(), f"El archivo {main_module_path} no existe"
        assert main_module_path.is_file(), f"La ruta {main_module_path} no es un archivo"

    def test_main_module_has_shebang(self):
        """Prueba que el módulo __main__ tiene el shebang correcto."""
        main_module_path = Path(__file__).parent.parent.parent / "pypex" / "__main__.py"

        # Leer las primeras líneas del archivo
        with open(main_module_path, encoding="utf-8") as f:
            first_line = f.readline().strip()

        # Verificar que tiene el shebang correcto
        assert first_line == "#!/usr/bin/env python"


class TestMainModuleIntegration:
    """Tests de integración para el módulo __main__."""

    @patch("sys.argv", ["python", "-m", "pypex"])
    @patch("pypex.cli.main")
    def test_module_execution_simulation(self, mock_main):
        """Simula la ejecución del módulo como si fuera llamado con python -m pypex."""
        # Esto simula lo que pasaría cuando se ejecuta: python -m pypex

        # Obtener la ruta al archivo __main__.py
        main_module_path = Path(__file__).parent.parent.parent / "pypex" / "__main__.py"

        # Ejecutar como si fuera el módulo principal
        spec = importlib.util.spec_from_file_location("__main__", main_module_path)
        main_module = importlib.util.module_from_spec(spec)
        main_module.__name__ = "__main__"

        # Ejecutar
        spec.loader.exec_module(main_module)

        # Verificar que main fue llamada
        mock_main.assert_called_once()

    def test_main_module_can_be_imported_multiple_times(self):
        """Prueba que el módulo se puede importar múltiples veces sin problemas."""
        main_module_path = Path(__file__).parent.parent.parent / "pypex" / "__main__.py"

        with patch("pypex.cli.main") as mock_main:
            # Importar múltiples veces
            for i in range(3):
                spec = importlib.util.spec_from_file_location(
                    f"pypex.__main__{i}", main_module_path
                )
                main_module = importlib.util.module_from_spec(spec)
                main_module.__name__ = f"pypex.__main__{i}"  # No es "__main__"

                spec.loader.exec_module(main_module)

            # main() no debería haberse llamado nunca
            mock_main.assert_not_called()
