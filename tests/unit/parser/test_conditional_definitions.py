"""Tests de extracción de funciones y clases definidas dentro de bloques condicionales."""

import textwrap
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import astroid

from pypex.metrics.cohesion.lcom4 import LCOM4
from pypex.metrics.complexity.cyclomatic import CyclomaticComplexity
from pypex.metrics.size.lines_of_code import LinesOfCodeMetric
from pypex.parser.ast_parser import ASTParser
from pypex.parser.astroid_visitor import AstroidNodeVisitor
from pypex.parser.code_entities import Module


def _analyze(source: str) -> Module:
    module_node = astroid.parse(textwrap.dedent(source), module_name="sample")
    return AstroidNodeVisitor(module_node, "").analyze()


def _names(entities: Iterable[Any]) -> list[str]:
    return [e.name for e in entities]


def _names_lines(entities: Iterable[Any]) -> list[tuple[str, int]]:
    return [(e.name, e.line_start) for e in entities]


# --- Nivel módulo -----------------------------------------------------------------------------


def test_function_inside_if_type_checking_is_extracted() -> None:
    module = _analyze(
        """
        if TYPE_CHECKING:
            def tc():
                return 1
        """
    )
    assert _names(module.functions) == ["tc"]


def test_both_branches_of_if_else_are_reported() -> None:
    module = _analyze(
        """
        import sys
        if sys.platform == "win32":
            def plat():
                return 1
        else:
            def plat():
                return 2
        """
    )
    assert _names_lines(module.functions) == [("plat", 4), ("plat", 7)]


def test_elif_chain_reports_every_branch() -> None:
    module = _analyze(
        """
        if A:
            def plat():
                return 1
        elif B:
            def plat():
                return 2
        else:
            def plat():
                return 3
        """
    )
    assert _names_lines(module.functions) == [("plat", 3), ("plat", 6), ("plat", 9)]


def test_try_except_importerror_fallback() -> None:
    module = _analyze(
        """
        try:
            import ujson
        except ImportError:
            def loads(s):
                return s
        else:
            def fast():
                return 1
        finally:
            def fin():
                return 2
        """
    )
    assert _names(module.functions) == ["loads", "fast", "fin"]


def test_try_star_handler_definitions() -> None:
    module = _analyze(
        """
        try:
            pass
        except* ValueError:
            def star():
                return 1
        """
    )
    assert _names(module.functions) == ["star"]


def test_deeply_nested_blocks() -> None:
    module = _analyze(
        """
        if A:
            try:
                import x
            except ImportError:
                if B:
                    def deep():
                        return 1

                    class DeepC:
                        def m(self):
                            return 2
        """
    )
    assert _names(module.functions) == ["deep"]
    assert _names(module.classes) == ["DeepC"]
    assert _names(module.classes[0].methods) == ["m"]


def test_with_match_for_while_blocks() -> None:
    module = _analyze(
        """
        with ctx():
            def in_with():
                return 1

        match cmd:
            case 1 if flag:
                def in_match():
                    return 2

        for i in range(3):
            def in_for():
                return 3
        else:
            def for_else():
                return 4

        while cond():
            def in_while():
                return 5
        """
    )
    assert _names(module.functions) == ["in_with", "in_match", "in_for", "for_else", "in_while"]


def test_async_function_inside_if() -> None:
    module = _analyze(
        """
        if A:
            async def coro():
                return 1
        """
    )
    assert _names(module.functions) == ["coro"]
    assert module.functions[0].is_async is True


def test_lambda_assigned_inside_if_is_named() -> None:
    module = _analyze(
        """
        if X:
            handler = lambda: 1
        """
    )
    assert _names(module.functions) == ["handler"]
    assert module.functions[0].is_lambda is True


def test_source_order_is_preserved() -> None:
    module = _analyze(
        """
        def top1():
            return 1

        if A:
            def cond():
                return 2

        def top2():
            return 3
        """
    )
    assert _names(module.functions) == ["top1", "cond", "top2"]


def test_conditional_function_is_not_a_method() -> None:
    module = _analyze(
        """
        if A:
            def plain():
                return 1
        """
    )
    func = module.functions[0]
    assert func.is_method is False
    assert func.parent_class is None


# --- Funciones anidadas (sin cambios de comportamiento) ----------------------------------------


def test_nested_functions_stay_inside_parent() -> None:
    module = _analyze(
        """
        def outer():
            if True:
                def inner():
                    return 1
            return 2
        """
    )
    assert _names(module.functions) == ["outer"]


def test_nested_function_complexity_still_added_to_parent() -> None:
    module = _analyze(
        """
        def outer(a, b):
            if a:
                def inner():
                    if b:
                        return 1
                    return 0
            return 2
        """
    )
    assert CyclomaticComplexity().calculate_function(module.functions[0]) == 3.0


# --- Nivel clase ------------------------------------------------------------------------------


def test_methods_in_both_branches_of_class_if() -> None:
    module = _analyze(
        """
        class K:
            if A:
                def cm(self):
                    return 1
            else:
                def cm(self):
                    return 2
        """
    )
    methods = module.classes[0].methods
    assert _names_lines(methods) == [("cm", 4), ("cm", 7)]
    assert all(m.is_method for m in methods)
    assert all(m.parent_class == "sample.K" for m in methods)


def test_method_inside_try_in_class_body() -> None:
    module = _analyze(
        """
        class K:
            try:
                import x
            except ImportError:
                def tm(self):
                    return 1
        """
    )
    assert _names(module.classes[0].methods) == ["tm"]


def test_inner_class_inside_if_in_class_body() -> None:
    module = _analyze(
        """
        class K:
            if A:
                class Inner:
                    def im(self):
                        return 1
        """
    )
    inner_classes = module.classes[0].inner_classes
    assert _names(inner_classes) == ["Inner"]
    assert _names(inner_classes[0].methods) == ["im"]
    # La clase interna no debe aparecer también como clase de módulo
    assert _names(module.classes) == ["K"]


def test_overloads_are_all_reported() -> None:
    module = _analyze(
        """
        from typing import overload

        class K:
            @overload
            def ov(self, a: int) -> int: ...
            @overload
            def ov(self, a: str) -> str: ...
            def ov(self, a):
                return a
        """
    )
    assert _names(module.classes[0].methods) == ["ov", "ov", "ov"]


def test_property_getter_and_setter_are_both_reported() -> None:
    module = _analyze(
        """
        class K:
            @property
            def x(self):
                return self._x

            @x.setter
            def x(self, value):
                self._x = value
        """
    )
    cls = module.classes[0]
    assert _names(cls.methods) == ["x", "x"]
    assert cls.property_methods_count == 1


def test_enum_synthetic_members_are_not_methods() -> None:
    module = _analyze(
        """
        import enum

        class Color(enum.Enum):
            RED = 1

            def __repr__(self):
                return "c"
        """
    )
    assert _names(module.classes[0].methods) == ["__repr__"]


def test_instance_attributes_from_conditional_method() -> None:
    module = _analyze(
        """
        class K:
            if X:
                def __init__(self):
                    self.a = 1
            else:
                def __init__(self):
                    self.b = 2
        """
    )
    assert module.classes[0].defined_instance_attributes == {"a", "b"}


# --- Métricas de módulo -----------------------------------------------------------------------


def test_module_cyclomatic_still_not_applicable() -> None:
    module = _analyze(
        """
        if A:
            def f():
                return 1
        else:
            def f():
                return 2
        """
    )
    assert CyclomaticComplexity().calculate_module(module) is None


def test_module_loc_entity_count_includes_conditional_definitions(tmp_path: Path) -> None:
    source = textwrap.dedent(
        """\
        import sys

        if sys.platform == "win32":
            def plat():
                return 1
        else:
            def plat():
                return 2
        """
    )
    path = tmp_path / "sample.py"
    path.write_text(source, encoding="utf-8")
    module = AstroidNodeVisitor(ASTParser().parse_with_astroid(path), str(path)).analyze()

    result = LinesOfCodeMetric().calculate_module(module)

    assert result["entity_count"] == 2.0
    assert result["total_sloc"] == float(
        len([line for line in source.splitlines() if line.strip()])
    )


class TestLcom4WithDuplicateDefinitions:
    """Las definiciones homónimas se agrupan como un único método en LCOM4."""

    @staticmethod
    def _class(source: str):
        return _analyze(source).classes[0]

    def test_overloads_are_one_method_and_share_attributes(self) -> None:
        cls = self._class(
            """
            from typing import overload

            class Store:
                @overload
                def get(self, k: str) -> str: ...
                @overload
                def get(self, k: int) -> int: ...
                def get(self, k):
                    return self.data[k]
                def size(self):
                    return len(self.data)
            """
        )

        result = LCOM4().calculate_class(cls)

        assert result["total_methods"] == 2
        assert result["lcom4"] == 1.0

    def test_property_getter_and_setter_group_with_reset(self) -> None:
        cls = self._class(
            """
            class Item:
                @property
                def x(self):
                    return self._x
                @x.setter
                def x(self, value):
                    self._x = value
                def reset(self):
                    return self._x
            """
        )

        result = LCOM4().calculate_class(cls)

        assert result["total_methods"] == 2
        assert result["lcom4"] == 1.0

    def test_conditional_definitions_union_their_attributes(self) -> None:
        cls = self._class(
            """
            class Item:
                if FLAG:
                    def a(self):
                        return self.p
                else:
                    def a(self):
                        return self.q
                def b(self):
                    return self.q
            """
        )

        result = LCOM4().calculate_class(cls)

        assert result["total_methods"] == 2
        assert result["lcom4"] == 1.0

    def test_only_duplicate_definitions_count_as_one_method(self) -> None:
        cls = self._class(
            """
            class Item:
                @property
                def x(self):
                    return self._x
                @x.setter
                def x(self, value):
                    self._x = value
            """
        )

        result = LCOM4().calculate_class(cls)

        assert result["total_methods"] == 1
        assert result["lcom4"] == 1.0
