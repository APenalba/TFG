"""Paquete parser de PyPex - Análisis y parseo de código Python.

Este módulo contiene las clases y funciones para analizar y parsear código Python
utilizando AST (Abstract Syntax Tree) estándar y Astroid para análisis avanzado.
Proporciona visitantes especializados y entidades de código estructuradas.

Classes:
    ASTNodeVisitor: Visitante para AST estándar de Python
    AstroidNodeVisitor: Visitante para análisis avanzado con Astroid
    ASTParser: Parser con soporte para AST y Astroid

Entities:
    Module: Representación de un módulo Python completo
    Class: Representación de una clase con métodos y atributos
    Function: Representación de una función o método
    Import: Representación de declaraciones de importación

Note:
    El paquete utiliza estrategia de fallback: Astroid para análisis detallado,
    AST estándar como alternativa robusta.

Autor: Alejandro Penalba Tarrida
Licencia: MIT
"""

from .ast_parser import ASTParser
from .astroid_visitor import AstroidNodeVisitor
from .node_visitor import ASTNodeVisitor

__all__ = [
    "ASTNodeVisitor",
    "AstroidNodeVisitor",
    "ASTParser",
]
