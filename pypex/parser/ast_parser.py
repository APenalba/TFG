"""Parser principal para análisis de código Python usando AST estándar y Astroid.

Este módulo implementa la funcionalidad de parsing de archivos Python utilizando
tanto el módulo AST estándar como Astroid para análisis avanzado.

Classes:
    ASTParser: Parser principal con soporte para AST y Astroid
"""

import ast
from pathlib import Path
from typing import List, Set, Union

import astroid

from pypex.core.interfaces import IASTParser
from pypex.services.logging_service import get_logger

logger = get_logger(__name__)


class ASTParser(IASTParser):
    """Parser robusto para análisis de código Python usando AST estándar y Astroid.
    
    Esta clase implementa la interfaz IASTParser y proporciona métodos para parsear
    archivos Python utilizando tanto el módulo AST estándar como Astroid.
    
    Methods:
        parse_file: Parsea usando AST estándar de Python
        parse_with_astroid: Parsea usando Astroid para análisis avanzado
        extract_functions: Extrae definiciones de funciones del AST
        extract_classes: Extrae definiciones de clases del AST
        extract_imports: Extrae declaraciones de importación del AST
    """

    def __init__(self):
        """Inicializa el parser AST."""
        logger.debug("ASTParser inicializado")

    def parse_file(self, file_path: Union[str, Path]) -> ast.Module:
        """Parsea un archivo Python y devuelve su AST.

        Args:
            file_path: Ruta al archivo a parsear.

        Returns:
            ast.Module: El AST del archivo.

        Raises:
            FileNotFoundError: Si el archivo no existe.
            SyntaxError: Si el archivo contiene errores de sintaxis.
        """
        path = Path(file_path)
        logger.debug(f"Parseando archivo con AST estándar: {path}")
        
        if not path.exists() or not path.is_file():
            logger.error(f"El archivo {file_path} no existe o no es un archivo")
            raise FileNotFoundError(f"El archivo {file_path} no existe")

        try:
            with open(path, "r", encoding="utf-8") as file:
                source = file.read()
            
            logger.debug(f"Archivo leído correctamente: {len(source)} caracteres")
            ast_tree = ast.parse(source, filename=str(path))
            logger.debug(f"AST generado correctamente para {path}")
            return ast_tree
        except SyntaxError as e:
            logger.error(f"Error de sintaxis parseando {file_path}: {str(e)}")
            raise SyntaxError(f"Error al parsear {file_path}: {str(e)}")
        except Exception as e:
            logger.error(f"Error inesperado parseando {file_path}: {str(e)}")
            raise

    def parse_with_astroid(self, file_path: Union[str, Path]) -> astroid.nodes.Module:
        """Parsea un archivo Python usando astroid para análisis más avanzados.

        Args:
            file_path: Ruta al archivo a parsear.

        Returns:
            astroid.nodes.Module: El árbol de sintaxis abstracta del archivo.

        Raises:
            FileNotFoundError: Si el archivo no existe.
            Exception: Si hay errores al parsear el archivo.
        """
        path = Path(file_path)
        logger.debug(f"Parseando archivo con Astroid: {path}")
        
        if not path.exists() or not path.is_file():
            logger.error(f"El archivo {file_path} no existe o no es un archivo")
            raise FileNotFoundError(f"El archivo {file_path} no existe")

        try:
            content = path.read_text(encoding="utf-8")
            logger.debug(f"Archivo leído para Astroid: {len(content)} caracteres")
            
            astroid_tree = astroid.parse(content, str(path))
            logger.debug(f"Árbol Astroid generado correctamente para {path}")
            return astroid_tree
        except Exception as e:
            logger.error(f"Error parseando {file_path} con Astroid: {str(e)}")
            raise Exception(f"Error al parsear {file_path} con astroid: {str(e)}")

    def extract_functions(self, tree: ast.Module) -> List[ast.FunctionDef]:
        """Extrae todas las definiciones de funciones del AST.

        Args:
            tree: El AST a analizar.

        Returns:
            List[ast.FunctionDef]: Lista de definiciones de funciones.
        """
        functions = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef)
        ]
        logger.debug(f"Extraídas {len(functions)} definiciones de funciones")
        return functions

    def extract_classes(self, tree: ast.Module) -> List[ast.ClassDef]:
        """Extrae todas las definiciones de clases del AST.

        Args:
            tree: El AST a analizar.

        Returns:
            List[ast.ClassDef]: Lista de definiciones de clases.
        """
        classes = [
            node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
        ]
        logger.debug(f"Extraídas {len(classes)} definiciones de clases")
        return classes

    def extract_imports(self, tree: ast.Module) -> Set[str]:
        """Extrae todos los imports del AST.

        Args:
            tree: El AST a analizar.

        Returns:
            Set[str]: Conjunto de nombres de módulos importados.
        """
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    imports.add(name.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module)
        
        logger.debug(f"Extraídos {len(imports)} imports únicos")
        return imports
