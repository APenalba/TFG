"""Módulo core de PyPex - Núcleo del analizador de complejidad de código Python.

Este módulo contiene las clases y funciones principales que forman el núcleo
del analizador de complejidad de código Python. Proporciona interfaces estándar,
implementaciones concretas y estructuras de datos unificadas.

Classes:
    Analyzer: Coordinador principal del proceso de análisis
    Project: Gestión de proyectos Python completos
    FileProcessor: Procesamiento de archivos individuales
    ResultsProcessor: Análisis y agregación de resultados

Interfaces:
    IAnalyzer: Interfaz principal del analizador
    IFileProcessor: Interfaz para procesamiento de archivos
    IProject: Interfaz para gestión de proyectos
    IASTParser: Interfaz para parseo AST

Structures:
    ProjectAnalysisResult: Resultados completos de análisis de proyecto
    FileAnalysisResult: Resultados de análisis de archivo individual
    MetricsResult: Resultados unificados de métricas

Exceptions:
    PypexError: Excepción base del sistema
    InvalidProjectError: Proyecto no válido para análisis
    ParsingError: Error durante el parseo de código


Autor: Alejandro Penalba Tarrida
Licencia: MIT
"""

from .interfaces import (
    IAnalyzer,
    IFileProcessor, 
    IProject,
    IASTParser,
    PypexError,
    InvalidProjectError,
    InvalidPythonFileError,
    ParsingError,
)

from .analyzer import Analyzer
from .project import Project
from .file_processor import FileProcessor

from .results import (
    ProjectAnalysisResult,
    FileAnalysisResult,
    EntityAnalysisResult,
    MetricsResult,
    AnalysisError,
    ErrorSeverity,
)

from .results_processor import ResultsProcessor

__all__ = [
    "IAnalyzer",
    "IFileProcessor", 
    "IProject",
    "IASTParser",
    "PypexError",
    "InvalidProjectError", 
    "InvalidPythonFileError",
    "ParsingError",
    "Analyzer",
    "Project", 
    "FileProcessor",
    "ProjectAnalysisResult",
    "FileAnalysisResult",
    "EntityAnalysisResult", 
    "MetricsResult",
    "AnalysisError",
    "ErrorSeverity",
    "ResultsProcessor",
]
