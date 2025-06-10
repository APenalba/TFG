"""Visitante avanzado para Astroid con análisis detallado de código Python.

Este módulo implementa un visitante especializado para recorrer el AST de Astroid
y extraer información detallada de código Python.

Classes:
    AstroidNodeVisitor: Visitante principal para análisis avanzado con Astroid

Functions:
    _calculate_sloc: Función auxiliar para cálculo de líneas de código
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import astroid
from astroid import nodes as astroid_nodes

from pypex.parser.code_entities import (
    Class,
    DecoratorEntity,
    Function,
    Import,
    Module,
    Parameter,
)
from pypex.services.logging_service import get_logger

logger = get_logger(__name__)

class AstroidNodeVisitor:
    """Visitante especializado para análisis avanzado de código Python con Astroid.
    
    Esta clase proporciona análisis detallado de código Python utilizando Astroid
    para extraer información completa de entidades, métricas de complejidad,
    relaciones entre clases y métodos, y análisis de flujo de control.
    
    Attributes:
        module_node: Nodo raíz del módulo Astroid
        file_path: Ruta al archivo siendo analizado
        source_lines_cache: Cache de líneas de código fuente
        all_functions_in_module: Lista de todas las funciones encontradas
        all_classes_in_module: Lista de todas las clases encontradas
        all_imports_in_module: Lista de todas las importaciones encontradas
        module_call_graph: Grafo de llamadas a nivel de módulo
    """

    def __init__(self, module_node: astroid_nodes.Module, file_path_str: str):
        logger.debug(f"AstroidNodeVisitor inicializado para {file_path_str}")
        self.module_node: astroid_nodes.Module = module_node
        self.file_path: Optional[Path] = Path(file_path_str) if file_path_str else None
        self.source_lines_cache: Optional[List[str]] = None
        
        if self.file_path and self.file_path.exists():
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    self.source_lines_cache = f.readlines()
                logger.debug(f"Cache de líneas de código creado: {len(self.source_lines_cache)} líneas")
            except Exception as e:
                logger.error(f"Failed to cache source lines for {self.file_path}: {e}")
                self.source_lines_cache = None

        self.all_functions_in_module: List[Union[
            astroid_nodes.FunctionDef,
            astroid_nodes.AsyncFunctionDef,
            astroid_nodes.Lambda,
        ]] = []
        self.all_classes_in_module: List[astroid_nodes.ClassDef] = []
        self.all_imports_in_module: List[Union[
            astroid_nodes.Import, 
            astroid_nodes.ImportFrom
        ]] = []
        self.module_call_graph: Dict[str, Set[str]] = {}

    def _read_lines_from_cache(self, start_line: int, end_line: int) -> List[str]:
        if not self.source_lines_cache:
            return []
        s_idx = max(0, start_line - 1)
        e_idx = min(len(self.source_lines_cache), end_line)
        if s_idx >= e_idx:
            return []
        return self.source_lines_cache[s_idx:e_idx]

    def analyze(self) -> Module:
        """Analiza el módulo Astroid y crea la entidad Module completa."""
        logger.debug("Iniciando análisis completo del módulo con Astroid")
        
        self.all_functions_in_module = list(
            self.module_node.nodes_of_class((
                astroid_nodes.FunctionDef,
                astroid_nodes.AsyncFunctionDef,
                astroid_nodes.Lambda,
            ))
        )
        logger.debug(f"Encontradas {len(self.all_functions_in_module)} funciones en el módulo")
        
        self.all_classes_in_module = list(
            self.module_node.nodes_of_class(astroid_nodes.ClassDef)
        )
        logger.debug(f"Encontradas {len(self.all_classes_in_module)} clases en el módulo")
        
        self.all_imports_in_module = list(
            self.module_node.nodes_of_class((
                astroid_nodes.Import, 
                astroid_nodes.ImportFrom
            ))
        )
        logger.debug(f"Encontradas {len(self.all_imports_in_module)} declaraciones de importación")
        
        logger.debug("Construyendo grafo de llamadas del módulo")
        self._build_module_call_graph()
        
        logger.debug("Creando entidad Module final")
        module_entity = self._create_module_entity()
        logger.debug(f"Análisis Astroid completado: {len(module_entity.functions)} funciones, {len(module_entity.classes)} clases")
        
        return module_entity

    def _build_module_call_graph(self) -> None:
        for func_node in self.module_node.nodes_of_class(
            (astroid_nodes.FunctionDef, astroid_nodes.AsyncFunctionDef)
        ):
            q_name = func_node.qname()
            self.module_call_graph.setdefault(q_name, set())
            for call_node in func_node.nodes_of_class(astroid_nodes.Call):
                try:
                    inferred_called_list = call_node.func.infer()
                    for inferred_called in inferred_called_list:
                        if (
                            inferred_called is not astroid.Uninferable
                            and hasattr(inferred_called, "qname")
                        ):
                            self.module_call_graph[q_name].add(inferred_called.qname())
                except astroid.InferenceError:
                    func_str = call_node.func.as_string()
                    if func_str:
                        self.module_call_graph[q_name].add(func_str)
                except Exception as e:
                    logger.debug(
                        f"Could not process call in {q_name}: {call_node.func.as_string()} due to {e}"
                    )

    def _extract_parameters(
        self, args_node: astroid_nodes.Arguments
    ) -> List[Parameter]:
        params = []
        if not args_node:
            return params

        for i, arg in enumerate(args_node.posonlyargs):
            default_val_str = None
            annotation_str = getattr(arg, "annotation", None)
            if annotation_str:
                annotation_str = annotation_str.as_string()
            else:
                annotation_str = None
            params.append(
                Parameter(
                    name=arg.name,
                    annotation=annotation_str,
                    default_value=default_val_str,
                    is_positional_only=True,
                )
            )

        num_regular_args = len(args_node.args)
        num_defaults = len(args_node.defaults)
        for i, arg in enumerate(args_node.args):
            default_val_str = None
            default_idx = i - (num_regular_args - num_defaults)
            if default_idx >= 0:
                default_val_str = args_node.defaults[default_idx].as_string()
            annotation_str = getattr(arg, "annotation", None)
            if annotation_str:
                annotation_str = annotation_str.as_string()
            else:
                annotation_str = None
            params.append(
                Parameter(
                    name=arg.name,
                    annotation=annotation_str,
                    default_value=default_val_str,
                )
            )

        if args_node.vararg:
            vararg_annotation_node = getattr(
                args_node, "varargannotation", None
            )
            vararg_annotation = (
                vararg_annotation_node.as_string()
                if vararg_annotation_node
                else None
            )
            params.append(
                Parameter(
                    name=args_node.vararg,
                    annotation=vararg_annotation,
                    is_variadic_positional=True,
                )
            )

        for i, arg in enumerate(args_node.kwonlyargs):
            default_val_str = None
            if args_node.kw_defaults[i] is not None:
                default_val_str = args_node.kw_defaults[i].as_string()
            annotation_str = getattr(arg, "annotation", None)
            if annotation_str:
                annotation_str = annotation_str.as_string()
            else:
                annotation_str = None
            params.append(
                Parameter(
                    name=arg.name,
                    annotation=annotation_str,
                    default_value=default_val_str,
                    is_keyword_only=True,
                )
            )

        if args_node.kwarg:
            kwarg_annotation_node = getattr(args_node, "kwargannotation", None)
            kwarg_annotation = (
                kwarg_annotation_node.as_string()
                if kwarg_annotation_node
                else None
            )
            params.append(
                Parameter(
                    name=args_node.kwarg,
                    annotation=kwarg_annotation,
                    is_variadic_keyword=True,
                )
            )
        return params

    def _get_line_number(
        self,
        node: Optional[astroid_nodes.NodeNG],
        attribute: str = "lineno",
        default: int = 0,
    ) -> int:
        if node is None:
            return default
        val = getattr(node, attribute, None)
        if isinstance(val, int) and val >= 0:
            return (
                val
                if val > 0
                else (1 if attribute in ("lineno", "fromlineno") else 0)
            )

        if (
            isinstance(node, astroid_nodes.Module)
            and attribute == "tolineno"
            and val is None
        ):
            if self.file_path and self.file_path.exists():
                try:
                    with open(self.file_path, "r", encoding="utf-8") as f:
                        return len(f.readlines())
                except Exception:
                    return default
            return default

        if not hasattr(node, "parent"):
            return default

        if node.parent and attribute not in [
            "tolineno",
            "end_lineno",
            "end_col_offset",
            "col_offset",
        ]:
            parent_val = getattr(node.parent, attribute, None)
            if isinstance(parent_val, int) and parent_val > 0:
                return parent_val

        return default

    def _analyze_code_block_lines(
        self,
        entity_node: astroid_nodes.NodeNG,
        entity_docstring_node: Optional[astroid_nodes.Const],
    ) -> Dict[str, int]:
        counts = {
            "source_lines_of_code": 0,
            "docstring_sloc": 0,
            "comment_sloc": 0,
            "blank_lines_count": 0,
        }

        start_line = self._get_line_number(entity_node, "fromlineno", 1)
        end_line = self._get_line_number(entity_node, "tolineno", start_line)

        docstring_actual_sloc = 0
        doc_start_src_line, doc_end_src_line = -1, -1

        if entity_docstring_node and isinstance(
            entity_docstring_node.value, str
        ):
            docstring_content = entity_docstring_node.value
            docstring_actual_sloc = len(docstring_content.splitlines())
            counts["docstring_sloc"] = docstring_actual_sloc
            doc_start_src_line = self._get_line_number(
                entity_docstring_node, "lineno", -1
            )
            doc_end_src_line = self._get_line_number(
                entity_docstring_node, "end_lineno", -1
            )

        entity_lines: List[str] = []
        node_source_attr = getattr(entity_node, "source", None)

        if isinstance(node_source_attr, str):
            entity_lines = node_source_attr.splitlines()
        elif self.file_path and self.file_path.exists():
            node_start_line_for_read = self._get_line_number(
                entity_node, "fromlineno", 1
            )
            node_end_line_for_read = self._get_line_number(
                entity_node, "tolineno", node_start_line_for_read
            )
            entity_lines = self._read_lines_from_cache(
                node_start_line_for_read, node_end_line_for_read
            )

        effective_sloc = 0
        comment_sloc = 0
        blank_lines = 0

        for idx, line_content_full in enumerate(entity_lines):
            current_line_no = start_line + idx
            line_content_stripped = line_content_full.strip()

            if not line_content_stripped:
                blank_lines += 1
                continue

            is_part_of_docstring_node = False
            if doc_start_src_line <= current_line_no <= doc_end_src_line:
                is_part_of_docstring_node = True

            if is_part_of_docstring_node:
                continue

            if line_content_stripped.startswith("#"):
                comment_sloc += 1
            else:
                effective_sloc += 1

        counts["source_lines_of_code"] = effective_sloc
        counts["comment_sloc"] = comment_sloc
        counts["blank_lines_count"] = blank_lines
        return counts

    def _create_decorator_entity(
        self, actual_decorator_expr_node: astroid_nodes.NodeNG
    ) -> DecoratorEntity:
        name_str = ""
        q_name = None
        args_list = []

        node_to_infer = actual_decorator_expr_node
        if isinstance(actual_decorator_expr_node, astroid_nodes.Call):
            if hasattr(actual_decorator_expr_node, "func"):
                name_str = actual_decorator_expr_node.func.as_string()
                node_to_infer = actual_decorator_expr_node.func
            else:
                name_str = actual_decorator_expr_node.as_string()

            if hasattr(actual_decorator_expr_node, "args"):
                for arg_node in actual_decorator_expr_node.args:
                    args_list.append(arg_node.as_string())
        elif isinstance(
            actual_decorator_expr_node,
            (astroid_nodes.Name, astroid_nodes.Attribute),
        ):
            name_str = actual_decorator_expr_node.as_string()
        else:
            name_str = actual_decorator_expr_node.as_string()

        try:
            inferred_list = node_to_infer.infer()
            if inferred_list and inferred_list[0] is not astroid.Uninferable:
                inferred_obj = inferred_list[0]
                if hasattr(inferred_obj, "qname"):
                    q_name = inferred_obj.qname()
        except astroid.InferenceError:
            logger.debug(
                f"InferenceError for decorator {name_str} in {self.file_path}, qname will be None."
            )
        except Exception as e:
            logger.debug(
                f"Exception during inference for decorator {name_str} in {self.file_path}: {e}, qname will be None."
            )

        return DecoratorEntity(
            name=name_str,
            qualified_name=q_name,
            args=args_list,
            line_start=self._get_line_number(
                actual_decorator_expr_node, "lineno"
            ),
            line_end=self._get_line_number(
                actual_decorator_expr_node,
                "end_lineno",
                self._get_line_number(actual_decorator_expr_node, "lineno"),
            ),
        )

    def _create_function_entity(
        self,
        func_node: Union[
            astroid_nodes.FunctionDef,
            astroid_nodes.AsyncFunctionDef,
            astroid_nodes.Lambda,
        ],
        parent_class_qname: Optional[str] = None,
    ) -> Function:
        is_lambda = isinstance(func_node, astroid_nodes.Lambda)
        func_name = "lambda" if is_lambda else func_node.name

        start_line = self._get_line_number(
            func_node, "lineno", 0 if is_lambda else 1
        )
        end_line = self._get_line_number(func_node, "end_lineno", start_line)

        docstring_node = (
            getattr(func_node, "doc_node", None) if not is_lambda else None
        )
        line_counts = self._analyze_code_block_lines(func_node, docstring_node)

        decorators_list = []
        if hasattr(func_node, "decorators") and func_node.decorators:
            for dec_node in func_node.decorators.nodes:
                decorators_list.append(self._create_decorator_entity(dec_node))

        # Counts
        yield_expressions_count = 0
        assert_statements_count = 0
        raise_statements_count = 0
        with_statements_count = 0
        return_points_count = 0
        try_blocks_count = 0
        finally_blocks_count = 0
        else_blocks_in_loops_count = 0
        exception_handlers_count = 0
        local_vars_set = set()
        is_generator = False

        # Populate local_vars from arguments
        if hasattr(func_node, "args") and func_node.args:
            for arg in func_node.args.args:
                local_vars_set.add(arg.name)
            if func_node.args.vararg:
                local_vars_set.add(func_node.args.vararg)
            if func_node.args.kwarg:
                local_vars_set.add(func_node.args.kwarg)
            for arg in func_node.args.kwonlyargs:
                local_vars_set.add(arg.name)
            for arg in func_node.args.posonlyargs:
                local_vars_set.add(arg.name)

        for sub_node in func_node.nodes_of_class(
            (astroid_nodes.Yield, astroid_nodes.YieldFrom)
        ):
            yield_expressions_count += 1
            is_generator = True
        for sub_node in func_node.nodes_of_class(astroid_nodes.Assert):
            assert_statements_count += 1
        for sub_node in func_node.nodes_of_class(astroid_nodes.Raise):
            raise_statements_count += 1
        for sub_node in func_node.nodes_of_class(
            astroid_nodes.With
        ):  # also AsyncWith
            with_statements_count += 1
        for sub_node in func_node.nodes_of_class(astroid_nodes.Return):
            return_points_count += 1
        for sub_node in func_node.nodes_of_class(
            astroid_nodes.Try
        ):  # TryStar should be included if supported
            try_blocks_count += 1
            if sub_node.finalbody:
                finally_blocks_count += 1
            exception_handlers_count += len(sub_node.handlers)
        for sub_node in func_node.nodes_of_class(
            (astroid_nodes.For, astroid_nodes.While)
        ):  # AsyncFor
            if sub_node.orelse:
                else_blocks_in_loops_count += 1

        # Local variables from assignments, comprehensions etc.
        for assign_node in func_node.nodes_of_class(
            (astroid_nodes.AssignName, astroid_nodes.AssignAttr)
        ):  # Assign, AnnAssign targets
            if (
                isinstance(assign_node, astroid_nodes.AssignName)
                and assign_node.scope() == func_node
            ):
                local_vars_set.add(assign_node.name)

        # Global/Nonlocal
        global_vars_accessed = set()
        global_vars_modified = set()
        nonlocal_vars_accessed = set()
        nonlocal_vars_modified = set()

        for global_stmt_node in func_node.nodes_of_class(astroid_nodes.Global):
            for name in global_stmt_node.names:
                global_vars_accessed.add(name)  # Initially assume accessed

        for nonlocal_stmt_node in func_node.nodes_of_class(
            astroid_nodes.Nonlocal
        ):
            for name in nonlocal_stmt_node.names:
                nonlocal_vars_accessed.add(name)  # Initially assume accessed

        # Correctly identify modified global/nonlocal variables
        declared_globals = set(global_vars_accessed)
        declared_nonlocals = set(nonlocal_vars_accessed)

        # Iterate over all AssignName nodes within the function to find modifications
        for assign_name_node in func_node.nodes_of_class(
            astroid_nodes.AssignName
        ):
            # Ensure assignment is directly within the current function's scope
            if assign_name_node.scope() == func_node:
                if assign_name_node.name in declared_globals:
                    global_vars_modified.add(assign_name_node.name)
                if assign_name_node.name in declared_nonlocals:
                    nonlocal_vars_modified.add(assign_name_node.name)

        # Note: This handles direct assignments. Modifications via attribute access
        # or item assignment (e.g., global_obj.attr = 5, global_list[0] = 5) are not covered here.

        parameters = (
            self._extract_parameters(func_node.args)
            if hasattr(func_node, "args")
            else []
        )

        return Function(
            name=func_name,
            line_start=start_line,
            line_end=end_line,
            source_file=self.file_path,
            source_lines_of_code=line_counts["source_lines_of_code"],
            docstring_sloc=line_counts["docstring_sloc"],
            comment_sloc=line_counts["comment_sloc"],
            blank_lines_count=line_counts["blank_lines_count"],
            parameters=parameters,
            is_method=(not is_lambda) and func_node.is_method(),
            is_async=isinstance(func_node, astroid_nodes.AsyncFunctionDef),
            is_lambda=is_lambda,
            is_generator=is_generator,
            parent_class=parent_class_qname,
            docstring=(
                docstring_node.value
                if docstring_node and isinstance(docstring_node.value, str)
                else None
            ),
            returns=(
                func_node.returns.as_string()
                if hasattr(func_node, "returns") and func_node.returns
                else None
            ),
            decorators=decorators_list,
            calls=(
                self.module_call_graph.get(func_node.qname(), set())
                if not is_lambda and hasattr(func_node, "qname")
                else set()
            ),
            local_variables=local_vars_set,
            yield_expressions_count=yield_expressions_count,
            assert_statements_count=assert_statements_count,
            raise_statements_count=raise_statements_count,
            with_statements_count=with_statements_count,
            return_points_count=return_points_count,
            try_blocks_count=try_blocks_count,
            finally_blocks_count=finally_blocks_count,
            else_blocks_in_loops_count=else_blocks_in_loops_count,
            exception_handlers_count=exception_handlers_count,
            global_variables_accessed=global_vars_accessed,
            global_variables_modified=global_vars_modified,
            nonlocal_variables_accessed=nonlocal_vars_accessed,
            nonlocal_variables_modified=nonlocal_vars_modified,
            astroid_node=func_node,
        )

    def _create_class_entity(
        self, cls_node: astroid_nodes.ClassDef, is_inner: bool = False
    ) -> Class:
        start_line = self._get_line_number(cls_node, "lineno")
        end_line = self._get_line_number(cls_node, "end_lineno", start_line)

        docstring_node = getattr(cls_node, "doc_node", None)
        line_counts = self._analyze_code_block_lines(cls_node, docstring_node)

        methods_list: List[Function] = []
        # Direct methods (not from base classes)
        for method_node in cls_node.mymethods():  # type: ignore
            if isinstance(
                method_node,
                (astroid_nodes.FunctionDef, astroid_nodes.AsyncFunctionDef),
            ):
                methods_list.append(
                    self._create_function_entity(
                        method_node, parent_class_qname=cls_node.qname()
                    )
                )
            elif isinstance(
                method_node, astroid_nodes.Lambda
            ):  # Lambdas assigned to class attributes?
                # Typically lambdas aren't methods in the traditional sense for these metrics.
                # If they need to be captured, it would be as attributes.
                pass

        inner_classes_list: List[Class] = []
        for inner_cls_node in cls_node.nodes_of_class(
            astroid_nodes.ClassDef, skip_klass=astroid_nodes.ClassDef
        ):
            # Ensure it's a direct inner class, not a grandchild
            if inner_cls_node.parent == cls_node:
                inner_classes_list.append(
                    self._create_class_entity(inner_cls_node, is_inner=True)
                )

        base_class_qnames = []
        for base_expr_node in cls_node.bases:
            try:
                inferred_bases = base_expr_node.infer()
                for inf_base in inferred_bases:
                    if inf_base is not astroid.Uninferable and hasattr(
                        inf_base, "qname"
                    ):
                        base_class_qnames.append(inf_base.qname())
                    elif hasattr(
                        base_expr_node, "name"
                    ):  # Fallback for uninferable bases like "object"
                        base_class_qnames.append(base_expr_node.name)
                    else:
                        base_class_qnames.append(base_expr_node.as_string())
            except astroid.InferenceError:
                base_class_qnames.append(
                    base_expr_node.as_string()
                )  # Store as string if not inferable

        decorators_list = []
        if cls_node.decorators:
            for dec_node in cls_node.decorators.nodes:
                decorators_list.append(self._create_decorator_entity(dec_node))

        # Attributes (class-level)
        class_attributes: Dict[str, str] = {}
        for assign_node in cls_node.nodes_of_class(
            astroid_nodes.AssignName
        ):  # AnnAssign too
            if (
                assign_node.scope() == cls_node
            ):  # Direct assignment in class body
                # Try to get annotation string
                annotation_str = "Any"
                parent_assign = assign_node.parent
                if (
                    isinstance(parent_assign, astroid_nodes.AnnAssign)
                    and parent_assign.annotation
                ):
                    annotation_str = parent_assign.annotation.as_string()
                elif isinstance(parent_assign, astroid_nodes.Assign):
                    # Try to infer type from assigned value if no AnnAssign
                    try:
                        inferred_value = parent_assign.value.infer()
                        if (
                            inferred_value
                            and inferred_value[0] is not astroid.Uninferable
                        ):
                            # Get a displayable type name
                            # qname might be too long, name might be better
                            annotation_str = getattr(
                                inferred_value[0], "pytype", lambda: "Any"
                            )()
                        else:  # Fallback if inference fails or value is complex
                            annotation_str = type(parent_assign.value).__name__
                    except astroid.InferenceError:
                        annotation_str = (
                            "Any"  # Or type(parent_assign.value).__name__
                        )
                    except Exception:
                        annotation_str = "Any"

                class_attributes[assign_node.name] = annotation_str

        # MRO
        mro_qnames_list = []
        try:
            for mro_cls in cls_node.mro():
                if hasattr(mro_cls, "qname"):
                    mro_qnames_list.append(mro_cls.qname())
        except Exception as e:  # MROError or others
            logger.debug(f"Could not compute MRO for {cls_node.name}: {e}")

        # Characteristics
        is_abstract = False
        abstract_methods = []
        is_dataclass_flag = any(
            dec.name == "dataclass"
            or (
                dec.qualified_name
                and "dataclasses.dataclass" in dec.qualified_name
            )
            for dec in decorators_list
        )
        is_exception = any(
            base_qname.endswith("Exception")
            for base_qname in base_class_qnames
        )  # Simple check

        if (
            "abc.ABC" in base_class_qnames or "ABCMeta" in base_class_qnames
        ):  # Needs more robust check for ABCMeta in metaclass
            is_abstract = True  # Potential abstract class
        for method_func in methods_list:
            if any(
                dec.name == "abstractmethod"
                or (
                    dec.qualified_name
                    and "abc.abstractmethod" in dec.qualified_name
                )
                for dec in method_func.decorators
            ):
                is_abstract = True
                abstract_methods.append(method_func.name)
            # Could also check for NotImplementedError directly in body, but decorator is more explicit

        # Method counts
        static_methods_count = 0
        class_methods_count = 0
        property_methods_count = 0
        dunder_methods_count = 0
        for m in methods_list:
            if m.name.startswith("__") and m.name.endswith("__"):
                dunder_methods_count += 1
            is_static = False
            is_class = False
            for dec in m.decorators:
                if dec.name == "staticmethod" or (
                    dec.qualified_name
                    and dec.qualified_name.endswith("staticmethod")
                ):
                    static_methods_count += 1
                    is_static = True
                    break
                if dec.name == "classmethod" or (
                    dec.qualified_name
                    and dec.qualified_name.endswith("classmethod")
                ):
                    class_methods_count += 1
                    is_class = True
                    break
                if dec.name == "property" or (
                    dec.qualified_name
                    and dec.qualified_name.endswith("property")
                ):
                    property_methods_count += 1
                    break
            # A method can't be both static and class, but loop handles first match.

        try:
            return Class(
                name=cls_node.name,
                line_start=start_line,
                line_end=end_line,
                source_file=self.file_path,
                source_lines_of_code=line_counts["source_lines_of_code"],
                docstring_sloc=line_counts["docstring_sloc"],
                comment_sloc=line_counts["comment_sloc"],
                blank_lines_count=line_counts["blank_lines_count"],
                docstring=(
                    docstring_node.value
                    if docstring_node and isinstance(docstring_node.value, str)
                    else None
                ),
                base_classes=base_class_qnames,
                decorators=decorators_list,
                methods=methods_list,
                attributes=class_attributes,
                inner_classes=inner_classes_list,
                defined_instance_attributes=self._extract_defined_instance_attributes(
                    cls_node
                ),  # Already implemented
                is_abstract_class=is_abstract,
                abstract_methods_list=abstract_methods,
                is_dataclass=is_dataclass_flag,
                is_exception_class=is_exception,
                inheritance_depth=(
                    len(mro_qnames_list) - 1 if mro_qnames_list else 0
                ),  # -1 for self
                mro_qnames=mro_qnames_list,
                static_methods_count=static_methods_count,
                class_methods_count=class_methods_count,
                property_methods_count=property_methods_count,
                dunder_methods_count=dunder_methods_count,
                astroid_node=cls_node,
            )
        except Exception as e:
            logger.warning(
                f"Error creating Class entity for {cls_node.name} at {self.file_path}:{start_line}: {e}",
                exc_info=True,
            )
            return Class(
                name=cls_node.name,
                line_start=start_line if start_line > 0 else 1,
                line_end=end_line if end_line >= start_line else start_line,
                source_file=self.file_path,
            )

    def _create_module_entity(self) -> Module:
        docstring_node = getattr(self.module_node, "doc_node", None)
        line_counts = self._analyze_code_block_lines(
            self.module_node, docstring_node
        )

        # Module-level variables and constants
        module_vars: Dict[str, str] = {}
        module_consts: Dict[str, Any] = {}
        for assign_node in self.module_node.nodes_of_class(
            (astroid_nodes.AssignName, astroid_nodes.AnnAssign)
        ):
            # Ensure it's a module-level assignment
            if assign_node.scope() == self.module_node:
                name_to_assign = None
                value_node_for_const = None
                annotation_str = "Any"  # Default

                if isinstance(assign_node, astroid_nodes.AssignName):
                    name_to_assign = assign_node.name
                    # Parent is Assign, its value is for const check
                    if isinstance(assign_node.parent, astroid_nodes.Assign):
                        value_node_for_const = assign_node.parent.value
                elif isinstance(
                    assign_node, astroid_nodes.AnnAssign
                ):  # astroid_nodes.AnnAssign
                    if isinstance(
                        assign_node.target, astroid_nodes.AssignName
                    ):
                        name_to_assign = assign_node.target.name
                    if assign_node.annotation:
                        annotation_str = assign_node.annotation.as_string()
                    if (
                        assign_node.value
                    ):  # Value might be None for annotated declarations
                        value_node_for_const = assign_node.value

                if name_to_assign:
                    module_vars[
                        name_to_assign
                    ] = annotation_str  # Store with annotation or "Any"
                    if value_node_for_const and isinstance(
                        value_node_for_const, astroid_nodes.Const
                    ):
                        module_consts[
                            name_to_assign
                        ] = value_node_for_const.value

        imports_list: List[Import] = []
        for imp_node in self.all_imports_in_module:
            try:
                is_conditional_import = False
                parent = imp_node.parent
                while parent and not isinstance(
                    parent,
                    (
                        astroid_nodes.Module,
                        astroid_nodes.FunctionDef,
                        astroid_nodes.ClassDef,
                    ),
                ):
                    if isinstance(
                        parent, (astroid_nodes.If, astroid_nodes.Try)
                    ):  # TryExcept, TryFinally
                        is_conditional_import = True
                        break
                    parent = parent.parent

                aliases_dict: Dict[str, str] = {}
                is_wildcard = False

                if isinstance(imp_node, astroid_nodes.Import):
                    current_names = []
                    for name, alias in imp_node.names:
                        actual_name = alias or name
                        current_names.append(actual_name)
                        if alias:
                            aliases_dict[name] = alias  # original -> alias
                    imports_list.append(
                        Import(
                            module=name,  # First name in list for "module" field
                            line=self._get_line_number(imp_node, "lineno"),
                            names=current_names,  # list of effective names (aliases or original)
                            is_from=False,
                            level=0,  # astroid_nodes.Import has no level
                            is_wildcard_import=False,
                            is_conditional=is_conditional_import,
                            aliases=aliases_dict,
                        )
                    )
                elif isinstance(imp_node, astroid_nodes.ImportFrom):
                    current_names = []
                    for name, alias in imp_node.names:
                        if name == "*":
                            is_wildcard = True
                            current_names.append("*")
                            # No alias for wildcard generally
                            break  # Wildcard usually stands alone in names list
                        actual_name = alias or name
                        current_names.append(actual_name)
                        if alias:
                            aliases_dict[name] = alias  # original -> alias
                    imports_list.append(
                        Import(
                            module=imp_node.modname,
                            line=self._get_line_number(imp_node, "lineno"),
                            names=current_names,
                            is_from=True,
                            level=imp_node.level or 0,
                            is_wildcard_import=is_wildcard,
                            is_conditional=is_conditional_import,
                            aliases=aliases_dict,
                        )
                    )
            except Exception as e:
                logger.warning(
                    f"Error extrayendo import en {self.file_path}: {e}",
                    exc_info=True,
                )

        functions_list: List[Function] = []
        classes_list: List[Class] = []

        for (
            item
        ) in (
            self.module_node.body
        ):  # Iterate over module body to maintain order and catch lambdas assigned at module level
            if isinstance(
                item,
                (astroid_nodes.FunctionDef, astroid_nodes.AsyncFunctionDef),
            ):
                # Ensure it's not a method (already handled by Class)
                if not item.is_method():
                    functions_list.append(self._create_function_entity(item))
            elif isinstance(item, astroid_nodes.ClassDef):
                # Ensure it's not an inner class (already handled by outer Class)
                if isinstance(item.parent, astroid_nodes.Module):
                    classes_list.append(self._create_class_entity(item))
            elif isinstance(
                item,
                astroid_nodes.Assign
            ):  # Check for lambdas assigned to module-level variables
                if isinstance(item.value, astroid_nodes.Lambda):
                    # How to name this lambda? Use the assignment target.
                    if len(item.targets) == 1 and isinstance(
                        item.targets[0], astroid_nodes.AssignName
                    ):
                        lambda_func_entity = self._create_function_entity(
                            item.value
                        )
                        lambda_func_entity.name = item.targets[
                            0
                        ].name  # Override default "lambda" name
                        functions_list.append(lambda_func_entity)

        # Future imports
        future_imports_set = set()
        for imp_from_node in self.module_node.nodes_of_class(
            astroid_nodes.ImportFrom
        ):
            if imp_from_node.modname == "__future__":
                for name, _ in imp_from_node.names:
                    future_imports_set.add(name)

        # Shebang
        shebang_line: Optional[str] = None
        if self.file_path and self.file_path.exists():
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    first_line = f.readline()
                    if first_line.startswith("#!"):
                        shebang_line = first_line.strip()
            except Exception as e:
                logger.debug(
                    f"Could not read shebang from {self.file_path}: {e}"
                )

        # is_package_init
        is_pkg_init = (
            self.file_path.name == "__init__.py" if self.file_path else False
        )

        # has_main_block
        has_main = False
        for if_node in self.module_node.nodes_of_class(astroid_nodes.If):
            # Check for `if __name__ == "__main__":`
            test = if_node.test
            if (
                isinstance(test, astroid_nodes.Compare)
                and isinstance(test.left, astroid_nodes.Name)
                and test.left.name == "__name__"
            ):
                if len(test.ops) == 1 and test.ops[0][0] == "==":
                    if (
                        isinstance(test.ops[0][1], astroid_nodes.Const)
                        and test.ops[0][1].value == "__main__"
                    ):
                        has_main = True
                        break

        start_line = self._get_line_number(self.module_node, "fromlineno", 1)
        # For module, tolineno might be more reliable than end_lineno for full file length
        end_line = self._get_line_number(
            self.module_node, "tolineno", start_line
        )
        if (
            self.file_path and self.file_path.exists() and end_line <= 1
        ):  # If tolineno is weird for module
            try:
                with open(self.file_path, "r", encoding="utf-8") as f_len:
                    end_line = len(f_len.readlines())
            except:
                pass

        try:
            return Module(
                name=self.module_node.name,
                line_start=start_line,
                line_end=end_line,
                source_file=self.file_path,
                source_lines_of_code=line_counts["source_lines_of_code"],
                docstring_sloc=line_counts["docstring_sloc"],
                comment_sloc=line_counts["comment_sloc"],
                blank_lines_count=line_counts["blank_lines_count"],
                path=self.file_path,
                docstring=(
                    docstring_node.value
                    if docstring_node and isinstance(docstring_node.value, str)
                    else None
                ),
                functions=functions_list,
                classes=classes_list,
                imports=imports_list,
                variables=module_vars,
                module_level_constants=module_consts,
                future_imports=future_imports_set,
                shebang=shebang_line,
                is_package_init=is_pkg_init,
                has_main_block=has_main,
                astroid_node=self.module_node,
            )
        except Exception as e:
            logger.warning(
                f"Error creating Module entity for {self.file_path}: {e}",
                exc_info=True,
            )
            return Module(
                name=(
                    self.module_node.name
                    if hasattr(self.module_node, "name")
                    else "unknown_module"
                ),
                line_start=1,
                line_end=1,
                source_file=self.file_path,
                path=self.file_path,
            )

    def _extract_defined_instance_attributes(
        self, cls_node: astroid_nodes.ClassDef
    ) -> Set[str]:
        """Extrae los atributos definidos vía self.atributo en la clase (en métodos, typically __init__)."""
        attrs = set()
        for method_node in cls_node.mymethods():  # type: ignore
            if not isinstance(
                method_node,
                (astroid_nodes.FunctionDef, astroid_nodes.AsyncFunctionDef),
            ):
                continue

            first_param_name = None
            if method_node.args and method_node.args.args:
                first_param_name = method_node.args.args[0].name
            elif method_node.args and method_node.args.posonlyargs:
                first_param_name = method_node.args.posonlyargs[0].name

            if not first_param_name:
                continue

            for assign_node in method_node.nodes_of_class(
                astroid_nodes.Assign
            ):
                for target in assign_node.targets:
                    if isinstance(target, astroid_nodes.AssignAttr):
                        if (
                            isinstance(target.expr, astroid_nodes.Name)
                            and target.expr.name == first_param_name
                        ):
                            attrs.add(target.attrname)
            for ann_assign_node in method_node.nodes_of_class(
                astroid_nodes.AnnAssign
            ):
                if isinstance(
                    ann_assign_node.target, astroid_nodes.AssignAttr
                ):
                    if (
                        isinstance(
                            ann_assign_node.target.expr, astroid_nodes.Name
                        )
                        and ann_assign_node.target.expr.name
                        == first_param_name
                    ):
                        attrs.add(ann_assign_node.target.attrname)
        return attrs
