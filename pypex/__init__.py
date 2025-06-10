"""
PyPex: Analizador de Complejidad de Código para Python.

Este paquete proporciona herramientas para analizar la complejidad de código Python
y generar reportes sobre la calidad y mantenibilidad del código.

Autor: Alejandro Penalba Tarrida
Licencia: MIT
"""

try:
    from importlib.metadata import version, PackageNotFoundError
except ImportError:
    # Python < 3.8 fallback
    from importlib_metadata import version, PackageNotFoundError

try:
    __version__ = version("pypex")
except PackageNotFoundError:
    # Para desarrollo local cuando el paquete no está instalado
    __version__ = "0.1.0-dev"
