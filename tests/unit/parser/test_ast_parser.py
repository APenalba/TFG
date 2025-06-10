"""Tests unitarios para el módulo ast_parser."""

import ast

import astroid
import pytest

from pypex.parser.ast_parser import ASTParser


@pytest.fixture
def valid_python_file(tmp_path):
    """Crea un archivo Python válido para pruebas."""
    file_path = tmp_path / "valid.py"
    with open(file_path, "w") as f:
        f.write(
            """
def hello(name):
    print(f"Hello, {name}!")

class Person:
    def __init__(self, name):
        self.name = name

    def greet(self):
        print(f"Hi, I'm {self.name}")

import os
from pathlib import Path
        """
        )
    return file_path


@pytest.fixture
def invalid_python_file(tmp_path):
    """Crea un archivo Python con errores de sintaxis."""
    file_path = tmp_path / "invalid.py"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(
            """
def hello(name:
    print(f"Hello, {name}!")  # Error: falta un parentesis
        """
        )
    return file_path


@pytest.fixture
def ast_parser():
    """Crea una instancia de ASTParser para pruebas."""
    return ASTParser()


class TestASTParser:
    """Pruebas para la clase ASTParser."""

    def test_parse_file_valid(self, ast_parser, valid_python_file):
        """Prueba el parseo de un archivo Python válido."""
        ast_tree = ast_parser.parse_file(valid_python_file)

        # Verificar que es un AST válido
        assert isinstance(ast_tree, ast.Module)

        # Verificar que contiene las estructuras esperadas
        functions = [
            node
            for node in ast.walk(ast_tree)
            if isinstance(node, ast.FunctionDef)
        ]
        classes = [
            node
            for node in ast.walk(ast_tree)
            if isinstance(node, ast.ClassDef)
        ]
        imports = [
            node
            for node in ast.walk(ast_tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
        ]

        assert len(functions) == 3  # hello, __init__, greet
        assert len(classes) == 1  # Person
        assert len(imports) == 2  # import os, from pathlib import Path

    def test_parse_file_invalid(self, ast_parser, invalid_python_file):
        """Prueba el parseo de un archivo Python con errores de sintaxis."""
        with pytest.raises(SyntaxError):
            ast_parser.parse_file(invalid_python_file)

    def test_parse_file_nonexistent(self, ast_parser):
        """Prueba el parseo de un archivo que no existe."""
        with pytest.raises(FileNotFoundError):
            ast_parser.parse_file("nonexistent_file.py")

    def test_parse_with_astroid_valid(self, ast_parser, valid_python_file):
        """Prueba el parseo con astroid de un archivo válido."""
        astroid_tree = ast_parser.parse_with_astroid(valid_python_file)

        # Verificar que es un módulo astroid válido
        assert isinstance(astroid_tree, astroid.Module)

        # Verificar que contiene las estructuras esperadas
        functions = list(astroid_tree.nodes_of_class(astroid.FunctionDef))
        classes = list(astroid_tree.nodes_of_class(astroid.ClassDef))
        imports = list(astroid_tree.nodes_of_class(astroid.Import))
        imports_from = list(astroid_tree.nodes_of_class(astroid.ImportFrom))

        assert len(functions) == 3  # hello, __init__, greet
        assert len(classes) == 1  # Person
        assert len(imports) == 1  # import os
        assert len(imports_from) == 1  # from pathlib import Path

    def test_parse_with_astroid_nonexistent(self, ast_parser):
        """Prueba el parseo con astroid de un archivo que no existe."""
        with pytest.raises(FileNotFoundError):
            ast_parser.parse_with_astroid("nonexistent_file.py")

    def test_extract_functions(self, ast_parser, valid_python_file):
        """Prueba la extracción de funciones de un AST."""
        ast_tree = ast_parser.parse_file(valid_python_file)
        functions = ast_parser.extract_functions(ast_tree)

        assert len(functions) == 3
        assert functions[0].name == "hello"
        assert functions[1].name == "__init__"
        assert functions[2].name == "greet"

    def test_extract_classes(self, ast_parser, valid_python_file):
        """Prueba la extracción de clases de un AST."""
        ast_tree = ast_parser.parse_file(valid_python_file)
        classes = ast_parser.extract_classes(ast_tree)

        assert len(classes) == 1
        assert classes[0].name == "Person"

    def test_extract_imports(self, ast_parser, valid_python_file):
        """Prueba la extracción de imports de un AST."""
        ast_tree = ast_parser.parse_file(valid_python_file)
        imports = ast_parser.extract_imports(ast_tree)

        assert len(imports) == 2
        assert "os" in imports
        assert "pathlib" in imports
