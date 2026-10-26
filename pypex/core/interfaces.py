"""Definición de interfaces para los componentes principales del sistema PyPex.

Este módulo define todas las interfaces que deben implementar los componentes
principales del analizador de código Python. Facilita la extensibilidad
y testing mediante inversión de dependencias.

Interfaces:
    IAnalyzer: Coordinador principal del proceso de análisis
    IFileProcessor: Procesamiento de archivos individuales
    IProject: Gestión de proyectos Python completos
    IASTParser: Parseo y análisis de árboles de sintaxis abstracta

Exceptions:
    PypexError: Excepción base del sistema
    InvalidProjectError: Proyecto no válido para análisis
    InvalidPythonFileError: Archivo Python no válido
    ParsingError: Error durante el parseo de código
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

# Importar las estructuras principales
from pypex.core.results import FileAnalysisResult, ProjectAnalysisResult

# Tipos básicos
ProjectPath = str | Path
FilePath = str | Path


# Definición de excepciones personalizadas
class PypexError(Exception):
    """Excepción base para errores de PyPex."""


class InvalidProjectError(PypexError):
    """Excepción lanzada cuando un proyecto no es válido."""


class InvalidPythonFileError(PypexError):
    """Excepción lanzada cuando un archivo Python no es válido."""


class ParsingError(PypexError):
    """Excepción lanzada cuando hay errores al parsear un archivo."""


# Interfaces para los componentes principales
class IAnalyzer(ABC):
    """Interfaz principal que coordina todo el proceso de análisis de código.

    Define el contrato para analizadores que procesan código Python y calculan
    métricas de complejidad. Soporta análisis tanto de archivos individuales
    como de proyectos completos.

    Methods:
        analyze_project: Analiza un proyecto completo
        analyze_file: Analiza un archivo individual
        analyze: Analiza archivo o directorio automáticamente
        set_reporters: Configura generadores de informes
        set_metrics: Configura métricas a calcular
    """

    @abstractmethod
    def analyze_project(
        self, path: ProjectPath, config: dict[str, Any] | None = None
    ) -> ProjectAnalysisResult:
        """
        Analiza un proyecto completo en la ruta especificada.

        Args:
            path: Ruta al directorio del proyecto
            config: Configuración opcional para el análisis

        Returns:
            Resultados completos del análisis

        Raises:
            FileNotFoundError: Si la ruta no existe
            InvalidProjectError: Si la ruta no contiene archivos Python válidos
        """

    @abstractmethod
    def analyze_file(
        self, file_path: FilePath, config: dict[str, Any] | None = None
    ) -> FileAnalysisResult:
        """
        Analiza un único archivo Python.

        Args:
            file_path: Ruta al archivo Python
            config: Configuración opcional para el análisis

        Returns:
            Resultados del análisis del archivo

        Raises:
            FileNotFoundError: Si el archivo no existe
            InvalidPythonFileError: Si el archivo no es Python válido
        """

    @abstractmethod
    def set_reporters(self, reporters: list[Any]) -> None:
        """
        Configura los generadores de informes a utilizar.

        Args:
            reporters: Lista de reporteros a utilizar
        """

    @abstractmethod
    def set_metrics(self, metrics: list[Any]) -> None:
        """
        Configura las métricas a calcular durante el análisis.

        Args:
            metrics: Lista de métricas a utilizar
        """

    @abstractmethod
    def analyze(
        self, path: ProjectPath, config: dict[str, Any] | None = None
    ) -> ProjectAnalysisResult:
        """
        Analiza la ruta especificada, que puede ser un archivo o directorio.

        Args:
            path: Ruta al archivo o directorio a analizar
            config: Configuración opcional para el análisis

        Returns:
            Resultados del análisis

        Raises:
            FileNotFoundError: Si la ruta no existe
        """


class IFileProcessor(ABC):
    """Interfaz para procesamiento de archivos Python individuales.

    Define el contrato para procesadores que manejan descoberta de archivos,
    filtrado de patrones, validación y lectura de contenido de archivos Python.

    Methods:
        find_python_files: Descubre archivos Python en una ruta
        should_ignore: Verifica si un archivo debe ser ignorado
        process_file: Procesa un archivo y extrae información
        read_file: Lee el contenido de un archivo
    """

    @abstractmethod
    def process_file(self, file_path: FilePath) -> dict[str, Any]:
        """
        Procesa un archivo Python y extrae su información estructural.

        Args:
            file_path: Ruta al archivo Python

        Returns:
            Información estructural del archivo

        Raises:
            FileNotFoundError: Si el archivo no existe
            ParsingError: Si hay errores al parsear el archivo
        """

    @abstractmethod
    def should_ignore(self, path: FilePath, scan_root_abs: Path) -> bool:
        """
        Verifica si un archivo debe ser ignorado según los patrones configurados.

        Args:
            path: Ruta al archivo
            scan_root_abs: Raíz absoluta del escaneo, para los patrones relativos

        Returns:
            True si el archivo debe ser ignorado, False en caso contrario
        """

    @abstractmethod
    def find_python_files(self, path: ProjectPath) -> list[Path]:
        """
        Encuentra todos los archivos Python en una ruta.

        Args:
            path: Ruta del archivo o directorio

        Returns:
            Lista de archivos Python encontrados

        Raises:
            FileNotFoundError: Si la ruta no existe
        """

    @abstractmethod
    def read_file(self, file_path: FilePath) -> str:
        """
        Lee el contenido de un archivo.

        Args:
            file_path: Ruta al archivo

        Returns:
            Contenido del archivo como string

        Raises:
            FileNotFoundError: Si el archivo no existe
            IOError: Si hay errores al leer el archivo
        """


class IProject(ABC):
    """Interfaz para gestión de proyectos de código Python.

    Define el contrato para gestores que manejan la estructura completa
    de un proyecto Python, incluyendo descoberta y parseo de archivos.

    Methods:
        parse_file: Parsea un archivo específico del proyecto
        parse_all_files: Parsea todos los archivos del proyecto
        get_summary: Obtiene información resumida del proyecto
    """

    @property
    @abstractmethod
    def path(self) -> Path:
        """Ruta raíz del proyecto."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Nombre del proyecto."""

    @property
    @abstractmethod
    def python_files(self) -> list[Path]:
        """Lista de archivos Python en el proyecto."""

    @abstractmethod
    def parse_file(self, file_path: Path) -> Any | None:
        """
        Parsea un archivo específico del proyecto.

        Args:
            file_path: Ruta al archivo

        Returns:
            Resultado del parsing o None si falla
        """

    @abstractmethod
    def parse_all_files(self) -> None:
        """Parsea todos los archivos del proyecto."""

    @abstractmethod
    def get_summary(self) -> dict[str, Any]:
        """
        Obtiene un resumen del proyecto.

        Returns:
            Diccionario con información resumida del proyecto
        """


class IASTParser(ABC):
    """Interfaz para parseo de archivos Python usando AST.

    Define el contrato para parsers que procesan código Python usando
    tanto AST estándar como Astroid para análisis avanzado.

    Methods:
        parse_file: Parsea usando AST estándar de Python
        parse_with_astroid: Parsea usando Astroid para análisis avanzado
    """

    @abstractmethod
    def parse_file(self, file_path: FilePath) -> Any:
        """
        Parsea un archivo Python usando AST estándar.

        Args:
            file_path: Ruta al archivo Python

        Returns:
            Nodo AST raíz

        Raises:
            FileNotFoundError: Si el archivo no existe
            ParsingError: Si hay errores al parsear
        """

    @abstractmethod
    def parse_with_astroid(self, file_path: FilePath) -> Any:
        """
        Parsea un archivo Python usando Astroid para análisis avanzado.

        Args:
            file_path: Ruta al archivo Python

        Returns:
            Nodo Astroid raíz

        Raises:
            FileNotFoundError: Si el archivo no existe
            ParsingError: Si hay errores al parsear con Astroid
        """
