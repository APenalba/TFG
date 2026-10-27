"""Carga de los assets estáticos (CSS/JS) del reporter HTML.

Los ficheros viven en ``pypex/reporters/html/static/`` y se leen con
``importlib.resources`` para que funcionen igual desde el árbol de fuentes,
una instalación editable o un wheel.
"""

from functools import cache
from importlib.resources import files

_PACKAGE = "pypex.reporters.html"
_STATIC_DIR = "static"


@cache
def load_static_asset(name: str) -> str:
    """Devuelve el contenido de un asset estático del reporter HTML.

    Args:
        name: Nombre del fichero dentro de ``static/`` (p. ej. ``"styles.css"``).

    Returns:
        Contenido del fichero como texto UTF-8.

    Raises:
        FileNotFoundError: Si el asset no existe.
    """
    return files(_PACKAGE).joinpath(_STATIC_DIR, name).read_text(encoding="utf-8")
