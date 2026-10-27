"""Behavioral tests for the Astroid based parser visitor."""

import textwrap
from types import SimpleNamespace

import astroid
import pytest

from pypex.parser.astroid_visitor import AstroidNodeVisitor
from pypex.parser.code_entities import Class, Function, Module

FUNCS_SRC = '''\
"""Modulo de ejemplo.

Con dos lineas.
"""

COUNTER = 0


def helper(x):
    return x + 1


def documented(a, b=2):
    """Suma dos numeros."""
    # comentario
    total = helper(a)

    return total + b
'''

CLASSES_SRC = '''\
from abc import ABC, abstractmethod
from dataclasses import dataclass


def helper(v):
    return v


class Base(ABC):
    """Doc base."""

    @abstractmethod
    def run(self):
        ...


class Child(Base):
    x = 1
    y: str = "a"

    def __init__(self, v):
        self.v = v
        self.t: int = 0
        other.q = 1

    def __repr__(self):
        return ""

    @staticmethod
    def s():
        pass

    @classmethod
    def c(cls):
        pass

    @property
    def p(self):
        return self.v

    def run(self):
        local = 1
        return local

    def withpos(me, /):
        me.pos = 1


@dataclass
class DC:
    a: int = 0


class MyError(Exception):
    pass


class Unknown(Missing):
    pass
'''


@pytest.fixture
def analyze(tmp_path):
    """Write source to a temporary file and return its analyzed module."""

    def _analyze(source: str, filename: str = "sample.py") -> Module:
        path = tmp_path / filename
        path.write_text(textwrap.dedent(source), encoding="utf-8")
        tree = astroid.parse(path.read_text(encoding="utf-8"), module_name="sample", path=str(path))
        return AstroidNodeVisitor(tree, str(path)).analyze()

    return _analyze


def _func(module: Module, name: str) -> Function:
    return next(f for f in module.functions if f.name == name)


def _cls(module: Module, name: str) -> Class:
    return next(c for c in module.classes if c.name == name)


def _method(cls: Class, name: str) -> Function:
    return next(m for m in cls.methods if m.name == name)


class TestModuleEntity:
    def test_module_lines_and_docstring(self, analyze):
        mod = analyze(FUNCS_SRC)
        assert (mod.name, mod.line_start, mod.line_end) == ("sample", 1, 18)
        assert mod.docstring.startswith("Modulo de ejemplo.")
        assert (mod.docstring_sloc, mod.comment_sloc) == (3, 1)
        assert [f.name for f in mod.functions] == ["helper", "documented"]
        assert mod.classes == []

    def test_module_variables_and_constants(self, analyze):
        mod = analyze("CONST = 42\nNAME: str = 'x'\nANN_ONLY: int\na, b = 1, 2\n")
        assert set(mod.variables) == {"CONST", "NAME", "ANN_ONLY", "a", "b"}
        assert mod.module_level_constants == {"CONST": 42, "NAME": "x"}

    @pytest.mark.xfail(
        strict=True, reason="BUG astroid_visitor.py:740-763: AssignName sobrescribe anotaciones"
    )
    def test_module_annotated_variable_keeps_annotation(self, analyze):
        mod = analyze("NAME: str = 'x'\nANN_ONLY: int\n")
        assert mod.variables["NAME"] == "str"
        assert mod.variables["ANN_ONLY"] == "int"

    def test_future_imports_shebang_and_main_block(self, analyze):
        src = '#!/usr/bin/env python3\nfrom __future__ import annotations\n\n\ndef main():\n    pass\n\n\nif __name__ == "__main__":\n    main()\n'
        mod = analyze(src)
        assert mod.shebang == "#!/usr/bin/env python3"
        assert mod.future_imports == {"annotations"}
        assert mod.has_main_block is True

    @pytest.mark.parametrize(
        ("condition", "expected"),
        [
            ('__name__ != "__main__"', False),
            ('__name__ == "other"', False),
            ('x == "__main__"', False),
            ("x = 1", False),
        ],
    )
    def test_main_block_detection(self, analyze, condition, expected):
        src = (
            f"if {condition}:\n    pass\n"
            if condition.startswith("__name__") or "==" in condition
            else f"{condition}\n"
        )
        assert analyze(src).has_main_block is expected

    def test_package_init_flag(self, analyze):
        assert analyze("x = 1\n", "__init__.py").is_package_init is True
        assert analyze("x = 1\n", "sample.py").is_package_init is False

    def test_single_line_module_line_end(self, analyze):
        mod = analyze("x = 1\n")
        assert (mod.line_start, mod.line_end) == (1, 1)

    def test_non_utf8_file_degrades_gracefully(self, tmp_path):
        path = tmp_path / "latin.py"
        path.write_bytes(b"x = 1\ny = '\xe9'\n")
        tree = astroid.parse("x = 1\ny = 2\n", module_name="latin", path=str(path))
        visitor = AstroidNodeVisitor(tree, str(path))
        mod = visitor.analyze()
        assert visitor.source_lines_cache is None
        assert mod.shebang is None
        assert mod.source_lines_of_code == 0
        assert mod.line_end == 2

    @pytest.mark.xfail(
        strict=True,
        reason="BUG astroid_visitor.py:914-921: analyze solo captura OSError al leer el archivo",
    )
    def test_non_utf8_single_line_file(self, tmp_path):
        path = tmp_path / "latin.py"
        path.write_bytes(b"y = '\xe9'\n")
        tree = astroid.parse("y = 1\n", module_name="latin", path=str(path))
        mod = AstroidNodeVisitor(tree, str(path)).analyze()
        assert mod.line_end == 1

    def test_visitor_without_file_path(self):
        mod = AstroidNodeVisitor(astroid.parse("def f():\n    pass\n"), "").analyze()
        assert mod.path is None and mod.source_file is None
        assert _func(mod, "f").source_lines_of_code == 0


class TestImports:
    SRC = """\
from __future__ import annotations
import os
from collections import OrderedDict as OD, deque
from typing import *
from . import sibling
from ..pkg import thing

try:
    import ujson as json
except ImportError:
    import json


def f():
    import re
    return re
"""

    def test_plain_import(self, analyze):
        item = next(i for i in analyze(self.SRC).imports if i.line == 2)
        assert (item.module, item.names, item.is_from, item.level, item.is_conditional) == (
            "os",
            ["os"],
            False,
            0,
            False,
        )

    def test_from_import_with_alias(self, analyze):
        item = next(i for i in analyze(self.SRC).imports if i.line == 3)
        assert item.module == "collections"
        assert item.names == ["OD", "deque"]
        assert item.aliases == {"OrderedDict": "OD"}

    def test_wildcard_import(self, analyze):
        item = next(i for i in analyze(self.SRC).imports if i.module == "typing")
        assert item.is_wildcard_import is True and item.names == ["*"]

    def test_relative_imports(self, analyze):
        imports = analyze(self.SRC).imports
        sibling = next(i for i in imports if i.line == 5)
        thing = next(i for i in imports if i.line == 6)
        assert (sibling.module, sibling.level, sibling.is_relative) == ("", 1, True)
        assert (thing.module, thing.level) == ("pkg", 2)

    def test_conditional_imports_inside_try(self, analyze):
        imports = analyze(self.SRC).imports
        ujson = next(i for i in imports if i.line == 9)
        json = next(i for i in imports if i.line == 11)
        assert ujson.is_conditional and ujson.aliases == {"ujson": "json"}
        assert json.is_conditional

    def test_import_inside_function_is_collected_not_conditional(self, analyze):
        item = next(i for i in analyze(self.SRC).imports if i.module == "re")
        assert item.is_conditional is False

    @pytest.mark.xfail(
        strict=True,
        reason="BUG astroid_visitor.py:792-810: import con varios módulos pierde dependencias",
    )
    def test_multi_name_import_keeps_every_module(self, analyze):
        assert analyze("import os, sys\n").dependencies >= {"os", "sys"}


class TestFunctions:
    def test_function_lines_docstring_and_counts(self, analyze):
        f = _func(analyze(FUNCS_SRC), "documented")
        assert (f.line_start, f.line_end, f.length) == (13, 18, 6)
        assert (f.source_lines_of_code, f.docstring_sloc, f.comment_sloc, f.blank_lines_count) == (
            3,
            1,
            1,
            1,
        )
        assert f.docstring == "Suma dos numeros."
        assert f.is_method is False and f.parent_class is None

    def test_function_calls_resolved_by_inference(self, analyze):
        mod = analyze(FUNCS_SRC)
        assert _func(mod, "documented").calls == {"sample.helper"}
        assert _func(mod, "helper").calls == set()

    def test_uninferable_call_falls_back_to_source(self, analyze):
        f = _func(analyze("def g():\n    unknown_func()\n    return range(3)\n"), "g")
        assert f.calls == {"unknown_func", "builtins.range"}

    def test_method_call_through_self(self, analyze):
        mod = analyze(
            "class Svc:\n    def a(self):\n        return self.b() + len([1])\n    def b(self):\n        return 1\n"
        )
        assert _method(_cls(mod, "Svc"), "a").calls == {"sample.Svc.b", "builtins.len"}

    def test_parameters_kinds_and_defaults(self, analyze):
        f = _func(
            analyze("def main(a, /, b, c=3, *args: str, d, e=1.0, **kw: dict) -> int:\n    ...\n"),
            "main",
        )
        actual = [
            (
                p.name,
                p.default_value,
                p.is_positional_only,
                p.is_variadic_positional,
                p.is_keyword_only,
                p.is_variadic_keyword,
            )
            for p in f.parameters
        ]
        assert actual == [
            ("a", None, True, False, False, False),
            ("b", None, False, False, False, False),
            ("c", "3", False, False, False, False),
            ("args", None, False, True, False, False),
            ("d", None, False, False, True, False),
            ("e", "1.0", False, False, True, False),
            ("kw", None, False, False, False, True),
        ]
        assert (
            _func(
                analyze(
                    "def main(a, /, b, c=3, *args: str, d, e=1.0, **kw: dict) -> int:\n    ...\n"
                ),
                "main",
            )
            .parameters[3]
            .annotation
            == "str"
        )
        assert f.parameters[-1].annotation == "dict" and f.returns == "int"
        assert f.local_variables >= {"a", "b", "c", "args", "d", "e", "kw"}

    @pytest.mark.xfail(
        strict=True,
        reason="BUG astroid_visitor.py:146,167,197: las anotaciones de argumentos viven en Arguments",
    )
    def test_parameter_annotations(self, analyze):
        f = _func(analyze("def f(a: int, /, b: str, *, c: float = 1.0):\n    ...\n"), "f")
        assert [p.annotation for p in f.parameters] == ["int", "str", "float"]

    def test_async_function(self, analyze):
        f = _func(
            analyze(
                "async def fetch(url):\n    async with ctx() as c:\n        await c\n    return 1\n"
            ),
            "fetch",
        )
        assert f.is_async and f.with_statements_count == 1 and f.return_points_count == 1
        assert f.local_variables == {"url", "c"} and f.calls == {"ctx"}

    def test_generator_function(self, analyze):
        f = _func(analyze("def gen():\n    yield 1\n    yield from range(3)\n"), "gen")
        assert f.is_generator and f.yield_expressions_count == 2

    def test_control_flow_counters(self, analyze):
        src = """def control(x):
    assert x
    try:
        pass
    except ValueError:
        raise
    except (TypeError, KeyError):
        pass
    finally:
        pass
    for i in range(3):
        pass
    else:
        pass
    while False:
        pass
    else:
        pass
    with x as f:
        pass
    if x:
        return 1
    return 2
"""
        f = _func(analyze(src), "control")
        assert (f.assert_statements_count, f.raise_statements_count, f.with_statements_count) == (
            1,
            1,
            1,
        )
        assert (
            f.return_points_count,
            f.try_blocks_count,
            f.finally_blocks_count,
            f.exception_handlers_count,
        ) == (2, 1, 1, 2)
        assert f.else_blocks_in_loops_count == 2 and f.local_variables == {"x", "i", "f"}

    def test_global_variables(self, analyze):
        f = _func(
            analyze("counter = 0\n\ndef bump():\n    global counter\n    counter += 1\n"), "bump"
        )
        assert f.global_variables_accessed == {"counter"}
        assert f.global_variables_modified == {"counter"}

    def test_global_declared_but_not_assigned(self, analyze):
        f = _func(analyze("def read():\n    global counter\n    return counter\n"), "read")
        assert f.global_variables_accessed == {"counter"} and f.global_variables_modified == set()

    @pytest.mark.xfail(
        strict=True,
        reason="BUG astroid_visitor.py:426-485: nodos de funciones anidadas se atribuyen al contenedor",
    )
    def test_nested_function_not_attributed_to_outer(self, analyze):
        mod = analyze(
            "def outer():\n    v = 0\n    def inner():\n        nonlocal v\n        v = 1\n        yield v\n        return 2\n    return inner\n"
        )
        outer = _func(mod, "outer")
        assert outer.is_generator is False
        assert outer.return_points_count == 1
        assert outer.nonlocal_variables_accessed == set()

    def test_module_level_lambda(self, analyze):
        mod = analyze(
            "square = lambda x: x * x\nf1 = f2 = lambda: 0\n\ndef host():\n    return lambda y: y\n"
        )
        assert [f.name for f in mod.functions] == ["square", "host"]
        square = _func(mod, "square")
        assert square.is_lambda and not square.is_method and square.line_start == 1
        assert (
            [p.name for p in square.parameters] == ["x"]
            and square.calls == set()
            and square.docstring is None
        )

    def test_decorators_name_args_and_lines(self, analyze):
        src = """import functools


def deco(fn):
    return fn


@deco
@functools.lru_cache(maxsize=None)
@functools.partial(print, "x", 1)
def decorated():
    pass


reg = {}


@reg["k"]
def by_subscript():
    pass
"""
        mod = analyze(src)
        decs = _func(mod, "decorated").decorators
        assert [(d.name, d.args, d.line_start) for d in decs] == [
            ("deco", [], 8),
            ("functools.lru_cache", [], 9),
            ("functools.partial", ["print", "'x'", "1"], 10),
        ]
        assert _func(mod, "by_subscript").decorators[0].name == "reg['k']"

    @pytest.mark.xfail(
        strict=True,
        reason="BUG astroid_visitor.py:353-354: se indexa infer() como generador y se traga la excepción",
    )
    def test_decorator_qualified_name(self, analyze):
        f = _func(
            analyze("import functools\n@functools.lru_cache\ndef decorated():\n    pass\n"),
            "decorated",
        )
        assert f.decorators[0].qualified_name is not None
        assert "lru_cache" in f.decorators[0].qualified_name

    @pytest.mark.xfail(
        strict=True,
        reason="BUG astroid_visitor.py:122: llamadas de decoradores se cuentan como llamadas de función",
    )
    def test_decorator_calls_not_counted_as_function_calls(self, analyze):
        src = "import functools\n@functools.lru_cache(maxsize=None)\n@functools.partial(print, 'x', 1)\ndef decorated():\n    pass\n"
        assert _func(analyze(src), "decorated").calls == set()


class TestClasses:
    def test_class_lines_docstring_and_sloc(self, analyze):
        base = _cls(analyze(CLASSES_SRC), "Base")
        assert base.docstring == "Doc base."
        assert base.docstring_sloc == 1
        assert base.line_start == 9

    def test_methods_are_marked_with_parent_class(self, analyze):
        mod = analyze(CLASSES_SRC)
        child = _cls(mod, "Child")
        assert [m.name for m in child.methods] == [
            "__init__",
            "__repr__",
            "s",
            "c",
            "p",
            "run",
            "withpos",
        ]
        assert all(m.parent_class == "sample.Child" and m.is_method for m in child.methods)
        assert [f.name for f in mod.functions] == ["helper"]

    def test_method_kind_counts(self, analyze):
        child = _cls(analyze(CLASSES_SRC), "Child")
        assert (
            child.static_methods_count,
            child.class_methods_count,
            child.property_methods_count,
            child.dunder_methods_count,
        ) == (1, 1, 1, 2)
        assert _method(child, "p").decorators[0].name == "property"

    def test_class_attributes(self, analyze):
        child = _cls(analyze(CLASSES_SRC), "Child")
        assert set(child.attributes) == {"x", "y"}
        assert child.attributes["y"] == "str"

    @pytest.mark.xfail(
        strict=True,
        reason="BUG astroid_visitor.py:609-610: inferencia de valor de atributo falla y usa Any",
    )
    def test_class_attribute_type_inferred_from_value(self, analyze):
        assert _cls(analyze(CLASSES_SRC), "Child").attributes["x"] in {"int", "builtins.int"}

    def test_instance_attributes(self, analyze):
        assert _cls(analyze(CLASSES_SRC), "Child").defined_instance_attributes == {"v", "t", "pos"}

    def test_abstract_class_detection(self, analyze):
        mod = analyze(CLASSES_SRC)
        base, child = _cls(mod, "Base"), _cls(mod, "Child")
        assert base.is_abstract_class and base.abstract_methods_list == ["run"]
        assert child.is_abstract_class is False

    def test_inheritance_and_mro(self, analyze):
        mod = analyze(CLASSES_SRC)
        base, child = _cls(mod, "Base"), _cls(mod, "Child")
        assert base.base_classes == ["abc.ABC"] and child.base_classes == ["sample.Base"]
        assert child.mro_qnames == ["sample.Child", "sample.Base", "abc.ABC", "builtins.object"]
        assert child.inheritance_depth == 3 and child.has_inheritance

    def test_dataclass_detection_by_name(self, analyze):
        dc = _cls(analyze(CLASSES_SRC), "DC")
        assert dc.is_dataclass is True and dc.decorators[0].name == "dataclass"

    def test_exception_class_detection(self, analyze):
        mod = analyze(CLASSES_SRC)
        assert _cls(mod, "MyError").is_exception_class is True
        assert _cls(mod, "MyError").base_classes == ["builtins.Exception"]
        assert _cls(mod, "Child").is_exception_class is False

    def test_uninferable_bases(self, analyze):
        mod = analyze(CLASSES_SRC)
        unknown = _cls(mod, "Unknown")
        assert unknown.base_classes == ["Missing"] and unknown.mro_qnames == ["sample.Unknown"]
        extra = analyze(
            "def make():\n    return undefined\n\nBase = make()\n\nclass A(Base):\n    pass\n\nclass B(make()):\n    pass\n"
        )
        assert _cls(extra, "A").base_classes == ["Base"]
        assert _cls(extra, "B").base_classes == ["make()"]

    def test_inconsistent_mro_is_tolerated(self, analyze):
        mod = analyze("class A:\n    pass\nclass B(A):\n    pass\nclass C(A, B):\n    pass\n")
        c = _cls(mod, "C")
        assert c.mro_qnames == [] and c.inheritance_depth == 0

    @pytest.mark.xfail(
        strict=True,
        reason="BUG astroid_visitor.py:640-642: solo reconoce bases directas terminadas en Exception",
    )
    def test_exception_subclass_detection(self, analyze):
        assert (
            _cls(analyze("class VErr(ValueError):\n    pass\n"), "VErr").is_exception_class is True
        )

    @pytest.mark.xfail(
        strict=True,
        reason="BUG astroid_visitor.py:353-354: qname de decorador calificado no se resuelve",
    )
    @pytest.mark.parametrize(
        ("src", "name"),
        [
            ("import dataclasses\n@dataclasses.dataclass\nclass D:\n    a: int = 0\n", "D"),
            (
                "import abc\nclass A:\n    @abc.abstractmethod\n    def run(self):\n        pass\n",
                "A",
            ),
        ],
    )
    def test_qualified_decorators_detected(self, analyze, src, name):
        cls = _cls(analyze(src), name)
        assert cls.is_dataclass if name == "D" else cls.is_abstract_class


class TestHelpers:
    def test_get_line_number_edge_cases(self):
        visitor = AstroidNodeVisitor(astroid.parse("x = 1\n"), "")
        assert visitor._get_line_number(None, default=7) == 7
        assert visitor._get_line_number(SimpleNamespace(lineno=0)) == 1
        assert visitor._get_line_number(SimpleNamespace(col_offset=0), "col_offset") == 0
        assert (
            visitor._get_line_number(
                SimpleNamespace(lineno=None, parent=SimpleNamespace(lineno=12))
            )
            == 12
        )
        assert (
            visitor._get_line_number(
                SimpleNamespace(end_lineno=None, parent=SimpleNamespace(end_lineno=9)),
                "end_lineno",
                4,
            )
            == 4
        )

    def test_read_lines_from_cache_bounds(self):
        visitor = AstroidNodeVisitor(astroid.parse("x = 1\n"), "")
        assert visitor._read_lines_from_cache(1, 2) == []
        visitor.source_lines_cache = ["a\n", "b\n"]
        assert visitor._read_lines_from_cache(5, 3) == []
        assert visitor._read_lines_from_cache(1, 99) == ["a\n", "b\n"]

    def test_extract_parameters_none(self):
        visitor = AstroidNodeVisitor(astroid.parse("x = 1\n"), "")
        assert visitor._extract_parameters(None) == []
