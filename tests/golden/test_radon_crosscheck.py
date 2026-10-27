"""Comparación cruzada de la complejidad ciclomática de PyPex con radon.

Las diferencias metodológicas conocidas están en KNOWN_DIFFERENCES; cualquier
divergencia nueva (o una esperada que desaparece) hace fallar el test.
"""

import ast
from pathlib import Path

import pytest
from radon.complexity import cc_visit
from radon.visitors import Function as RadonFunction

from tests.golden.snapshot import CORPUS_DIR

pytestmark = pytest.mark.golden

ABSENT = "ausente"  # la herramienta no reporta esa entidad
NO_VALUE = "sin valor"  # PyPex reporta la entidad pero la métrica falló

COMPREHENSION = "PyPex no suma comprensiones ni expresiones generadoras; radon suma +1 por cada for y +1 por cada if"
NESTED_IN_PARENT = (
    "PyPex suma a la función contenedora las decisiones de sus funciones anidadas; radon no"
)
NESTED_NOT_REPORTED = "PyPex no reporta funciones anidadas como entidades; radon sí (closures)"
LOOP_ELSE = "radon suma +1 por el else de for/while; PyPex no"
TRY_ELSE = "radon suma +1 por el else de try; PyPex no"
TERNARY = "radon suma +1 por la expresión condicional; PyPex no (su docstring dice que sí)"
ASSERT = "radon suma +1 por assert; PyPex no"
MATCH_WILDCARD = "radon no cuenta el 'case _'; PyPex cuenta todos los case"
ELIF_TWICE = "PyPex cuenta cada elif dos veces (sospecha de bug)"
MODULE_LAMBDA = (
    "PyPex reporta la lambda de módulo como función y hoy falla su CC; radon no la reporta"
)

KNOWN_DIFFERENCES: dict[tuple[str, str, int], tuple[int | str, int | str, str]] = {
    ("comprehensions.py", "evens", 4): (1, 3, COMPREHENSION),
    ("comprehensions.py", "index_pairs", 8): (2, 5, COMPREHENSION),
    ("comprehensions.py", "flatten", 12): (1, 3, COMPREHENSION),
    ("comprehensions.py", "upper_triangle", 16): (1, 4, COMPREHENSION),
    ("comprehensions.py", "unique_lengths", 20): (1, 2, COMPREHENSION),
    ("comprehensions.py", "total_positive", 24): (1, 3, COMPREHENSION),
    ("shapes.py", "total_area", 80): (1, 3, COMPREHENSION),
    ("control_flow.py", "classify", 8): (6, 4, ELIF_TWICE),
    ("control_flow.py", "sum_until", 19): (4, 5, LOOP_ELSE),
    ("control_flow.py", "safe_div", 43): (3, 4, TRY_ELSE),
    ("control_flow.py", "sign_of", 71): (1, 2, TERNARY),
    ("control_flow.py", "require_positive", 75): (1, 2, ASSERT),
    ("control_flow.py", "dispatch", 80): (4, 3, MATCH_WILDCARD),
    ("functional.py", "double", 5): (NO_VALUE, ABSENT, MODULE_LAMBDA),
    ("functional.py", "logged", 8): (2, 1, NESTED_IN_PARENT),
    ("functional.py", "logged.wrapper", 10): (ABSENT, 2, NESTED_NOT_REPORTED),
    ("functional.py", "retry", 18): (3, 1, NESTED_IN_PARENT),
    ("functional.py", "retry.decorator", 19): (ABSENT, 1, NESTED_NOT_REPORTED),
    ("functional.py", "retry.decorator.wrapper", 20): (ABSENT, 3, NESTED_NOT_REPORTED),
    ("functional.py", "make_counter", 43): (2, 1, NESTED_IN_PARENT),
    ("functional.py", "make_counter.increment", 46): (ABSENT, 2, NESTED_NOT_REPORTED),
}
MIN_EXACT_MATCHES = 20  # hoy hay 27


def _definition_lines(source: str) -> dict[int, int]:
    """Primera línea (decorador o def) -> línea del def. PyPex usa la primera; radon el def."""
    lines: dict[int, int] = {}
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            first = min([d.lineno for d in node.decorator_list] + [node.lineno])
            lines[first] = node.lineno
    return lines


def _pypex_values(result) -> dict[tuple[str, str, int], int | str]:
    values: dict[tuple[str, str, int], int | str] = {}
    for path_str, file_result in result.files.items():
        path = Path(path_str)
        def_lines = _definition_lines(path.read_text(encoding="utf-8"))

        def add(qualname, entity, file_name=path.name, def_lines=def_lines):
            start = entity.source_info["line_start"]
            cc = entity.metrics.metrics.get("cyclomatic_complexity")
            key = (file_name, qualname, def_lines.get(start, start))
            values[key] = NO_VALUE if cc is None else int(cc)

        for entity in file_result.entities:
            if entity.entity_type == "class":
                for method in entity.children:
                    add(f"{entity.name}.{method.name}", method)
            else:
                add(entity.name, entity)
    return values


def _radon_values() -> dict[tuple[str, str, int], int]:
    values: dict[tuple[str, str, int], int] = {}
    for path in sorted(CORPUS_DIR.glob("*.py")):

        def add(block, qualname, file_name=path.name):
            values[(file_name, qualname, block.lineno)] = block.complexity
            for closure in block.closures:
                add(closure, f"{qualname}.{closure.name}")

        for block in cc_visit(path.read_text(encoding="utf-8")):
            if isinstance(block, RadonFunction):  # los bloques Class no son comparables
                add(block, f"{block.classname}.{block.name}" if block.is_method else block.name)
    return values


def test_cyclomatic_matches_radon_except_known_differences(golden_result):
    pypex, radon = _pypex_values(golden_result), _radon_values()
    divergences = {}
    for key in pypex.keys() | radon.keys():
        pair = (pypex.get(key, ABSENT), radon.get(key, ABSENT))
        if pair[0] != pair[1]:
            divergences[key] = pair
    exact = [k for k, v in pypex.items() if radon.get(k) == v]
    assert len(exact) >= MIN_EXACT_MATCHES, f"Solo {len(exact)} coincidencias exactas"

    problems = []
    for key in sorted(divergences.keys() | KNOWN_DIFFERENCES.keys()):
        where = f"{key[0]}::{key[1]} (línea {key[2]})"
        if key not in KNOWN_DIFFERENCES:
            p, r = divergences[key]
            problems.append(f"+ divergencia nueva en {where}: PyPex={p}, radon={r}")
        elif key not in divergences:
            problems.append(f"- ya no diverge {where} (esperado: {KNOWN_DIFFERENCES[key][2]})")
        elif divergences[key] != KNOWN_DIFFERENCES[key][:2]:
            ep, er, _ = KNOWN_DIFFERENCES[key]
            p, r = divergences[key]
            problems.append(
                f"~ {where}: esperado PyPex={ep}, radon={er}; obtenido PyPex={p}, radon={r}"
            )
    if problems:
        pytest.fail(
            "La CC de PyPex diverge de radon de forma no documentada:\n"
            + "\n".join(problems)
            + "\nSi es intencionado, actualiza KNOWN_DIFFERENCES y tests/golden/README.md.",
            pytrace=False,
        )
