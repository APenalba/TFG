"""Entidades de código para representación estructural de elementos Python.

Este módulo define las estructuras de datos que representan elementos del código
fuente Python para análisis estático y cálculo de métricas.

Classes:
    CodeEntity: Clase base para todas las entidades analizables
    Function: Representación de funciones y métodos
    Class: Representación de clases con métodos y atributos
    Module: Representación de módulos Python completos
    Project: Representación de proyectos de software completos
    Import: Representación de declaraciones de importación
    Parameter: Representación de parámetros de funciones
    DecoratorEntity: Representación de decoradores aplicados
"""

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import astroid


@dataclass
class CodeEntity:
    """Clase base para todas las entidades de código analizables."""

    name: str
    line_start: int = 0
    line_end: int = 0
    source_file: str | Path | None = None

    source_lines_of_code: int = 0
    docstring_sloc: int = 0
    comment_sloc: int = 0
    blank_lines_count: int = 0

    astroid_node: astroid.nodes.NodeNG | None = field(default=None, repr=False, compare=False)
    ast_node: ast.AST | None = field(default=None, repr=False, compare=False)

    @property
    def length(self) -> int:
        """Calcula la longitud total en líneas de la entidad de código."""
        if self.line_end is None or self.line_start is None or self.line_end < self.line_start:
            return 0
        return self.line_end - self.line_start + 1


@dataclass
class Parameter:
    """Representa un parámetro de una función o método."""

    name: str
    default_value: str | None = None
    annotation: str | None = None
    is_variadic_positional: bool = False
    is_variadic_keyword: bool = False
    is_positional_only: bool = False
    is_keyword_only: bool = False


@dataclass
class DecoratorEntity:
    """Representa un decorador aplicado a una función o clase."""

    name: str
    qualified_name: str | None = None
    args: list[str] = field(default_factory=list)
    line_start: int = 0
    line_end: int = 0


@dataclass
class Function(CodeEntity):
    """Representa una función o método en el código fuente."""

    parameters: list[Parameter] = field(default_factory=list)
    is_method: bool = False
    is_async: bool = False
    is_lambda: bool = False
    is_generator: bool = False
    parent_class: str | None = None
    docstring: str | None = None
    returns: str | None = None
    decorators: list[DecoratorEntity] = field(default_factory=list)

    calls: set[str] = field(default_factory=set)
    local_variables: set[str] = field(default_factory=set)

    yield_expressions_count: int = 0
    assert_statements_count: int = 0
    raise_statements_count: int = 0
    with_statements_count: int = 0
    return_points_count: int = 0
    try_blocks_count: int = 0
    finally_blocks_count: int = 0
    else_blocks_in_loops_count: int = 0
    exception_handlers_count: int = 0

    global_variables_accessed: set[str] = field(default_factory=set)
    global_variables_modified: set[str] = field(default_factory=set)
    nonlocal_variables_accessed: set[str] = field(default_factory=set)
    nonlocal_variables_modified: set[str] = field(default_factory=set)

    @property
    def signature(self) -> str:
        """Genera una representación en cadena de la firma de la función."""
        params_str_list = []
        for p in self.parameters:
            param_str = p.name
            if p.annotation:
                param_str += f": {p.annotation}"
            if p.default_value is not None:
                param_str += f" = {p.default_value}"
            params_str_list.append(param_str)

        signature_str = (
            f"{'async ' if self.is_async else ''}def {self.name}({', '.join(params_str_list)})"
        )
        if self.returns:
            signature_str += f" -> {self.returns}"
        return signature_str


@dataclass
class Class(CodeEntity):
    """Representa una clase en el código fuente."""

    docstring: str | None = None
    base_classes: list[str] = field(default_factory=list)
    decorators: list[DecoratorEntity] = field(default_factory=list)

    methods: list[Function] = field(default_factory=list)
    attributes: dict[str, str] = field(default_factory=dict)
    inner_classes: list["Class"] = field(default_factory=list)

    defined_instance_attributes: set[str] = field(default_factory=set)

    is_abstract_class: bool = False
    abstract_methods_list: list[str] = field(default_factory=list)
    is_dataclass: bool = False
    is_exception_class: bool = False
    inheritance_depth: int = 0
    mro_qnames: list[str] = field(default_factory=list)

    static_methods_count: int = 0
    class_methods_count: int = 0
    property_methods_count: int = 0
    dunder_methods_count: int = 0

    @property
    def method_count(self) -> int:
        """Calcula el número total de métodos en la clase."""
        return len(self.methods)

    @property
    def total_method_count(self) -> int:
        """Calcula el número total de métodos incluyendo clases anidadas."""
        total = len(self.methods)
        for inner_class in self.inner_classes:
            total += inner_class.total_method_count
        return total

    @property
    def depth_of_inheritance_tree(self) -> int:
        """Retorna la profundidad en el árbol de herencia."""
        return self.inheritance_depth

    @property
    def has_inheritance(self) -> bool:
        """Determina si la clase tiene herencia."""
        return len(self.base_classes) > 0


@dataclass
class Import:
    """Representa una sentencia de importación en el código."""

    module: str
    line: int
    names: list[str] = field(default_factory=list)
    is_from: bool = False
    level: int = 0
    is_wildcard_import: bool = False
    is_conditional: bool = False
    aliases: dict[str, str] = field(default_factory=dict)

    @property
    def is_relative(self) -> bool:
        """Determina si la importación es relativa."""
        return self.level > 0


@dataclass
class Module(CodeEntity):
    """Representa un archivo de código Python (módulo)."""

    path: Path | None = None
    docstring: str | None = None
    functions: list[Function] = field(default_factory=list)
    classes: list[Class] = field(default_factory=list)
    imports: list[Import] = field(default_factory=list)
    variables: dict[str, str] = field(default_factory=dict)
    module_level_constants: dict[str, Any] = field(default_factory=dict)

    future_imports: set[str] = field(default_factory=set)
    shebang: str | None = None
    is_package_init: bool = False
    has_main_block: bool = False

    @property
    def package(self) -> str:
        """Obtiene el nombre del paquete al que pertenece el módulo."""
        if self.path:
            return self.path.parent.name
        return ""

    @property
    def dependencies(self) -> set[str]:
        """Obtiene un conjunto de nombres de módulos de los que este módulo depende."""
        deps = set()
        for imp in self.imports:
            deps.add(imp.module)
        return deps

    @property
    def code_entities_count(self) -> int:
        """Calcula el número total de funciones y clases definidas a nivel de módulo."""
        return len(self.functions) + len(self.classes)


@dataclass
class Project(CodeEntity):
    """Representa un proyecto de software completo, compuesto por múltiples módulos."""

    name: str
    root_path: Path | None = None
    modules: list[Module] = field(default_factory=list)

    total_sloc_code: int = 0
    total_sloc_docstrings: int = 0
    total_sloc_comments: int = 0
    total_blank_lines: int = 0
    external_dependencies: set[str] = field(default_factory=set)

    @property
    def module_count(self) -> int:
        """Obtiene el número total de módulos analizados en el proyecto."""
        return len(self.modules)

    @property
    def function_count(self) -> int:
        """Obtiene el número total de funciones definidas en todos los módulos del proyecto."""
        return sum(len(module.functions) for module in self.modules)

    @property
    def class_count(self) -> int:
        """Obtiene el número total de clases definidas en todos los módulos del proyecto."""
        return sum(len(module.classes) for module in self.modules)

    def get_dependency_graph(self) -> dict[str, set[str]]:
        """Genera un grafo de dependencias entre los módulos del proyecto."""
        graph: dict[str, set[str]] = {}
        for module in self.modules:
            graph[module.name] = module.dependencies
        return graph
