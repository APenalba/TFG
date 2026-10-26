"""Visitante para AST estándar de Python con recolección de métricas básicas.

Este módulo implementa un visitante para recorrer el AST estándar de Python
y recolectar métricas básicas de código.

Classes:
    ASTNodeVisitor: Visitante principal para métricas básicas del AST

Functions:
    _calculate_sloc: Función auxiliar para cálculo de líneas de código

Note:
    Este visitante es una alternativa ligera cuando Astroid no está disponible
    o cuando se requiere análisis básico sin dependencias externas complejas.
"""

import ast
from pathlib import Path

from pypex.services.logging_service import get_logger

logger = get_logger(__name__)


def _calculate_sloc(filepath: Path, start_line: int, end_line: int) -> int:
    """Calcula las Source Lines of Code (SLOC) para un rango de líneas."""
    if not filepath or not filepath.exists():
        return 0
    try:
        with open(filepath, encoding="utf-8") as f:
            lines = f.readlines()
        total_lines = len(lines)
        start = start_line if isinstance(start_line, int) and start_line > 0 else 1
        end = end_line if isinstance(end_line, int) and end_line >= start else total_lines

        if end > total_lines:
            end = total_lines
        if start > end:
            logger.warning(
                f"SLOC: start_line ({start}) > end_line ({end}) en {filepath}, ajustando a rango válido."
            )
            start = 1

        sloc = 0
        for i in range(start - 1, end):
            line = lines[i].strip()
            if (
                line
                and not line.startswith("#")
                and not line.startswith('"""')
                and not line.startswith("'''")
            ):
                sloc += 1
        return sloc
    except Exception as e:
        logger.error(f"Error calculating SLOC for {filepath}: {e}")
        return 0


class ASTNodeVisitor(ast.NodeVisitor):
    """Visitante robusto para AST estándar de Python con recolección de métricas.

    Esta clase extiende ast.NodeVisitor para recorrer el AST estándar de Python
    y recolectar métricas básicas de código.

    Attributes:
        function_count: Número de funciones encontradas
        class_count: Número de clases encontradas
        import_count: Número de declaraciones de importación
        conditional_count: Número de estructuras condicionales (if)
        loop_count: Número de bucles (for, while)
        try_except_count: Número de bloques try-except
        complexity_nodes: Lista de nodos que aumentan complejidad
        call_graph: Grafo de llamadas entre funciones
        variables: Conjunto de variables definidas
        current_function: Función actual siendo visitada
    """

    def __init__(self):
        """Inicializa el visitante de nodos."""
        logger.debug("ASTNodeVisitor inicializado")
        self.function_count = 0
        self.class_count = 0
        self.import_count = 0
        self.conditional_count = 0
        self.loop_count = 0
        self.try_except_count = 0

        self.complexity_nodes: list[ast.AST] = []
        self.call_graph: dict[str, set[str]] = {}
        self.variables: set[str] = set()

        self.current_function: str | None = None
        self.function_stack: list[str] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visita una definición de función."""
        self.function_count += 1
        self.call_graph[node.name] = set()

        self.function_stack.append(node.name)
        old_function = self.current_function
        self.current_function = node.name

        self.generic_visit(node)

        self.function_stack.pop()
        self.current_function = old_function

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visita una definición de función asíncrona."""
        self.function_count += 1
        self.call_graph[node.name] = set()

        self.function_stack.append(node.name)
        old_function = self.current_function
        self.current_function = node.name

        self.generic_visit(node)

        self.function_stack.pop()
        self.current_function = old_function

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visita una definición de clase."""
        self.class_count += 1
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        """Visita una declaración de importación."""
        self.import_count += len(node.names)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Visita una declaración de importación desde."""
        self.import_count += len(node.names)
        self.generic_visit(node)

    def visit_If(self, node: ast.If) -> None:
        """Visita una declaración if."""
        self.conditional_count += 1
        self.complexity_nodes.append(node)
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        """Visita una declaración for."""
        self.loop_count += 1
        self.complexity_nodes.append(node)

        if isinstance(node.target, ast.Name):
            self.variables.add(node.target.id)
        elif isinstance(node.target, (ast.Tuple, ast.List)):
            for elt in node.target.elts:
                if isinstance(elt, ast.Name):
                    self.variables.add(elt.id)

        self.generic_visit(node)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        """Visita una declaración for asíncrona."""
        self.loop_count += 1
        self.complexity_nodes.append(node)

        if isinstance(node.target, ast.Name):
            self.variables.add(node.target.id)
        elif isinstance(node.target, (ast.Tuple, ast.List)):
            for elt in node.target.elts:
                if isinstance(elt, ast.Name):
                    self.variables.add(elt.id)

        self.generic_visit(node)

    def visit_While(self, node: ast.While) -> None:
        """Visita una declaración while."""
        self.loop_count += 1
        self.complexity_nodes.append(node)
        self.generic_visit(node)

    def visit_Try(self, node: ast.Try) -> None:
        """Visita una declaración try-except."""
        self.try_except_count += 1
        self.complexity_nodes.append(node)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        """Visita una llamada a función."""
        if self.current_function and self.current_function in self.call_graph:
            called_func_name: str | None = None
            if isinstance(node.func, ast.Name):
                called_func_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                called_func_name = node.func.attr

            if called_func_name:
                self.call_graph[self.current_function].add(called_func_name)

        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        """Visita una asignación."""
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.variables.add(target.id)
            elif isinstance(target, (ast.Tuple, ast.List)):
                for elt in target.elts:
                    if isinstance(elt, ast.Name):
                        self.variables.add(elt.id)

        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        """Visita una asignación anotada."""
        if isinstance(node.target, ast.Name):
            self.variables.add(node.target.id)
        self.generic_visit(node)

    def get_metrics(self) -> dict[str, any]:
        """Obtiene las métricas básicas recolectadas."""
        return {
            "function_count": self.function_count,
            "class_count": self.class_count,
            "import_count": self.import_count,
            "conditional_count": self.conditional_count,
            "loop_count": self.loop_count,
            "try_except_count": self.try_except_count,
            "complexity_node_count": len(self.complexity_nodes),
            "unique_variables_defined": len(self.variables),
            "call_graph": self.call_graph,
        }
