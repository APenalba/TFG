#!/usr/bin/env python
"""Interfaz de línea de comandos para PyPex.

PyPex es un analizador estático de código Python que calcula métricas de complejidad
y genera reportes detallados sobre la calidad y mantenibilidad del código.

Características principales:
- 14 métricas de complejidad diferentes
- Múltiples formatos de reporte (HTML, JSON y consola)
- Análisis a nivel de función, clase, módulo y proyecto
- Configuración flexible con perfiles de umbrales
- Filtros y exclusiones personalizables
- Salida rica con Rich o fallback a texto plano

Ejemplos de uso:
    # Análisis básico
    pypex analyze .

    # Reporte HTML completo
    pypex analyze --format html --output reporte.html ./src

    # Análisis con configuración personalizada
    pypex analyze --config pypex.yaml --exclude-metrics lcom4 --thresholds-profile strict .

    # Ver umbrales configurados
    pypex thresholds
"""

import json
import logging
from pathlib import Path
from typing import Any

import click
import yaml

from pypex import __version__
from pypex.core.analyzer import Analyzer
from pypex.core.file_processor import FileProcessor
from pypex.core.results import ErrorSeverity
from pypex.metrics import get_registry
from pypex.parser.ast_parser import ASTParser
from pypex.reporters import ReporterRegistry
from pypex.services.config_service import get_config
from pypex.services.logging_service import (
    configure_logging,
    configure_presentation_service,
    get_logger,
    get_presentation_service,
)

logger = get_logger(__name__)


def load_config_file(config_path: str) -> dict:
    """Carga un archivo de configuración YAML o JSON.

    Args:
        config_path: Ruta al archivo de configuración.

    Returns:
        dict: Configuración cargada.

    Raises:
        click.ClickException: Si hay error al cargar el archivo.
    """
    config_file = Path(config_path)

    if not config_file.exists():
        raise click.ClickException(f"Archivo de configuración no encontrado: {config_path}")

    try:
        with open(config_file, encoding="utf-8") as f:
            config: dict[str, Any]
            if config_file.suffix.lower() == ".json":
                config = json.load(f)
            else:
                # YAML (.yaml/.yml) y, por defecto, cualquier otra extensión
                config = yaml.safe_load(f) or {}
            return config
    except (yaml.YAMLError, json.JSONDecodeError) as e:
        raise click.ClickException(
            f"Error al parsear archivo de configuración {config_path}: {e}"
        ) from e
    except Exception as e:
        raise click.ClickException(
            f"Error al leer archivo de configuración {config_path}: {e}"
        ) from e


def validate_metrics_list(metrics: list[str], exclude_metrics: list[str]) -> list[str]:
    """Valida y procesa la lista de métricas a usar.

    Args:
        metrics: Lista de métricas específicas a incluir.
        exclude_metrics: Lista de métricas a excluir.

    Returns:
        List[str]: Lista final de métricas a usar.

    Raises:
        click.ClickException: Si hay métricas inválidas.
    """
    registry = get_registry()
    available_metrics = set(registry.get_available_metrics())

    # Validar métricas especificadas
    if metrics:
        invalid_metrics = set(metrics) - available_metrics
        if invalid_metrics:
            raise click.ClickException(
                f"Métricas no válidas especificadas: {', '.join(invalid_metrics)}\n"
                f"Métricas disponibles: {', '.join(sorted(available_metrics))}"
            )
        final_metrics = list(set(metrics))
    else:
        # Usar todas las métricas disponibles
        final_metrics = list(available_metrics)

    # Excluir métricas especificadas
    if exclude_metrics:
        invalid_exclude = set(exclude_metrics) - available_metrics
        if invalid_exclude:
            raise click.ClickException(
                f"Métricas a excluir no válidas: {', '.join(invalid_exclude)}\n"
                f"Métricas disponibles: {', '.join(sorted(available_metrics))}"
            )
        final_metrics = [m for m in final_metrics if m not in exclude_metrics]

    if not final_metrics:
        raise click.ClickException("No quedan métricas válidas después de aplicar filtros.")

    return final_metrics


@click.group()
@click.version_option(version=__version__)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Activa el modo verboso con información detallada en la consola (nivel DEBUG en logs).",
)
@click.option(
    "--log-file",
    type=click.Path(),
    help="Archivo donde guardar los logs detallados del análisis.",
    metavar="ARCHIVO",
)
def main(verbose: bool, log_file: str | None = None):
    """🐍 PyPex: Analizador Avanzado de Complejidad de Código Python

    PyPex es una herramienta profesional para analizar código Python y calcular
    métricas de complejidad, generando reportes detallados sobre la calidad,
    mantenibilidad y arquitectura del código.

    \b
    🎯 CARACTERÍSTICAS PRINCIPALES:
    • 16 métricas de complejidad diferentes (ciclomática, cognitiva, etc.)
    • Análisis multi-nivel: función, clase, módulo y proyecto
    • Múltiples formatos de salida: HTML, JSON y consola
    • Configuración flexible con archivos YAML/JSON
    • Perfiles de umbrales personalizables (strict/normal/permissive)
    • Filtros y exclusiones avanzadas
    • Interfaz rica con colores y tablas (Rich) o texto plano

    \b
    📊 MÉTRICAS DISPONIBLES:
    • Complejidad Ciclomática        • Complejidad Cognitiva
    • Profundidad de Anidamiento     • Conteo de Parámetros
    • Complejidad Esencial          • Complejidad Lógica
    • Complejidad de Comprensiones  • Manejo de Excepciones
    • Complejidad de Generadores    • Complejidad de Diseño
    • Líneas de Código              • Acoplamiento Fan-In/Out
    • Cohesión LCOM4               • Profundidad de Comprensiones
    • Métricas de Halstead         • Acoplamiento Avanzado

    \b
    🚀 EJEMPLOS RÁPIDOS:
      pypex analyze .                         # Análisis básico en consola
      pypex analyze --format html -o reporte.html ./src  # Reporte HTML
      pypex analyze --verbosity verbose ./src # Análisis detallado en consola
      pypex thresholds                        # Ver umbrales configurados

    \b
    📖 Para más información y documentación completa:
      https://github.com/tu-repo/pypex
    """
    # Configurar nivel de log según verbosidad
    log_level = logging.DEBUG if verbose else logging.INFO
    configure_logging(console_level=log_level, log_file=log_file)

    # Configurar servicio de presentación (prefiere Rich cuando esté disponible)
    configure_presentation_service(prefer_rich=True)

    # Actualizar configuración global
    config = get_config()
    config.set("verbose", verbose)
    if log_file:
        config.set("log_file", log_file)

    logger.info(f"PyPex v{__version__} iniciado")


@main.command()
@click.argument("path", type=click.Path(exists=True), metavar="RUTA")
@click.option(
    "--output",
    "-o",
    default=None,
    help="Ruta del archivo de salida del reporte. Si no se especifica, se muestra resumen en consola.",
    metavar="ARCHIVO",
)
@click.option(
    "--format",
    "-f",
    default="console",
    type=click.Choice(["html", "json", "console"], case_sensitive=False),
    help="Formato del reporte de salida.",
    show_default=True,
)
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="Archivo de configuración YAML o JSON con opciones personalizadas.",
    metavar="ARCHIVO",
)
@click.option(
    "--max-file-size",
    "-s",
    default=1024 * 1024,  # 1MB por defecto
    help="Tamaño máximo de archivo a analizar en bytes.",
    metavar="BYTES",
    show_default=True,
)
@click.option(
    "--ignore",
    "-i",
    multiple=True,
    help="Patrones glob para ignorar archivos o directorios. Se puede usar múltiples veces.",
    metavar="PATRÓN",
)
@click.option(
    "--metrics",
    "-m",
    multiple=True,
    help="Métricas específicas a calcular. Si no se especifican, se usan todas. Se puede usar múltiples veces.",
    metavar="MÉTRICA",
)
@click.option(
    "--exclude-metrics",
    "-x",
    multiple=True,
    help="Métricas a excluir del análisis. Útil para omitir métricas específicas. Se puede usar múltiples veces.",
    metavar="MÉTRICA",
)
@click.option(
    "--thresholds-profile",
    "-t",
    default="normal",
    type=click.Choice(["strict", "normal", "permissive"], case_sensitive=False),
    help="Perfil de umbrales para la interpretación de métricas.",
    show_default=True,
)
@click.option(
    "--verbosity",
    default="normal",
    type=click.Choice(["quiet", "normal", "verbose", "debug"], case_sensitive=False),
    help="Nivel de detalle para la salida en consola (solo aplica con formato 'console').",
    show_default=True,
)
def analyze(
    path: str,
    output: str | None,
    format: str,
    config: str | None,
    max_file_size: int,
    ignore: tuple,
    metrics: tuple,
    exclude_metrics: tuple,
    thresholds_profile: str,
    verbosity: str,
):
    """📊 Analiza código Python y genera reportes de complejidad.

    Analiza el código Python en la RUTA especificada (archivo o directorio)
    y calcula métricas de complejidad para evaluar la calidad y mantenibilidad.

    \b
    RUTA: Archivo .py o directorio con código Python a analizar

    \b
    🎯 EJEMPLOS DE USO:

    \b
    Análisis básico:
      pypex analyze .
      pypex analyze mi_script.py

    \b
    Reporte HTML completo:
      pypex analyze --format html --output reporte.html ./src

    \b
    Análisis con métricas específicas:
      pypex analyze -m cyclomatic_complexity -m cognitive_complexity ./proyecto

    \b
    Excluir métricas específicas:
      pypex analyze --exclude-metrics lcom4 --exclude-metrics design_complexity .

    \b
    Configuración avanzada:
      pypex analyze --config pypex.yaml --thresholds-profile strict ./src

    \b
    Filtrar archivos:
      pypex analyze --ignore "test_*.py" --ignore "__pycache__" ./proyecto

    \b
    📁 FORMATOS DE SALIDA:
    • html: Reporte web interactivo con gráficos y navegación (requiere --output)
    • json: Datos estructurados para procesamiento automático (requiere --output)
    • console: Reporte formateado en la terminal con colores e iconos (por defecto)

    \b
    🔊 NIVELES DE VERBOSIDAD (para formato console):
    • quiet: Resumen mínimo en una línea
    • normal: Información balanceada con estadísticas y hot spots (por defecto)
    • verbose: Análisis detallado con métricas y recomendaciones
    • debug: Información completa incluyendo configuración y tiempos

    \b
    ⚙️ CONFIGURACIÓN:
    Las opciones de línea de comandos tienen precedencia sobre el archivo de configuración.
    El archivo de configuración puede ser YAML (.yaml/.yml) o JSON (.json).

    \b
    🎚️ PERFILES DE UMBRALES:
    • strict:     Umbrales estrictos para código de alta calidad
    • normal:     Umbrales balanceados para proyectos típicos (por defecto)
    • permissive: Umbrales relajados para código legacy o prototipado
    """
    try:
        logger.info(f"Analizando ruta: {path}")

        path_obj = Path(path)
        if path_obj.is_file() and path_obj.suffix != ".py":
            raise click.ClickException(f"La ruta '{path}' no es un archivo Python (.py).")

        # Cargar configuración del archivo si se especifica
        file_config = {}
        if config:
            logger.info(f"Cargando configuración desde: {config}")
            file_config = load_config_file(config)
            logger.debug(f"Configuración cargada: {file_config}")

        # Actualizar configuración global con los parámetros del CLI y archivo
        config_obj = get_config()

        # Aplicar configuración del archivo primero (menor precedencia)
        for key, value in file_config.items():
            config_obj.set(key, value)

        # Aplicar configuración de CLI (mayor precedencia)
        config_obj.set("output_format", format)
        config_obj.set("max_file_size", max_file_size)
        config_obj.set("thresholds_profile", thresholds_profile)
        config_obj.set("verbosity", verbosity)

        if ignore:
            config_obj.set("ignore_patterns", list(ignore))
        elif "ignore_patterns" not in file_config:
            config_obj.set("ignore_patterns", [])

        if output:
            config_obj.set("output_path", output)

        logger.info(f"Usando perfil de umbrales: {thresholds_profile} (para selección de análisis)")

        # Configurar el analizador
        config_dict = {
            "max_file_size": max_file_size,
            "ignore_patterns": config_obj.get("ignore_patterns", []),
            "output_format": format,
        }

        # Crear las dependencias
        file_processor = FileProcessor(
            ignore_patterns=config_dict.get("ignore_patterns"),
            max_file_size=config_dict.get("max_file_size", 1024 * 1024),
        )
        ast_parser = ASTParser()

        # Procesar métricas a utilizar ANTES de crear el analizador
        registry = get_registry()

        # Obtener métricas de configuración del archivo si no se especificaron en CLI
        cli_metrics = list(metrics) if metrics else file_config.get("metrics", [])
        cli_exclude = (
            list(exclude_metrics) if exclude_metrics else file_config.get("exclude_metrics", [])
        )

        # Validar y procesar métricas
        final_metrics_names = validate_metrics_list(cli_metrics, cli_exclude)

        # Configurar métricas específicas si se especificaron
        specific_metrics = None
        if final_metrics_names:
            configured_metrics = []
            for metric_name in final_metrics_names:
                try:
                    metric = registry.get_metric(metric_name)
                    configured_metrics.append(metric)
                    logger.debug(f"Métrica configurada: {metric_name}")
                except Exception as e:
                    logger.warning(f"Error al cargar métrica {metric_name}: {str(e)}")

            if configured_metrics:
                specific_metrics = configured_metrics
                logger.info(f"Configuradas {len(configured_metrics)} métricas específicas")
                logger.info(f"Métricas activas: {', '.join(final_metrics_names)}")
                if cli_exclude:
                    logger.info(f"Métricas excluidas: {', '.join(cli_exclude)}")
            else:
                logger.warning(
                    "No se pudieron cargar métricas válidas. Usando todas las disponibles."
                )
        else:
            logger.info("Usando todas las métricas disponibles")

        # Crear y ejecutar el analizador (dependency injection)
        analyzer = Analyzer(
            parser=ast_parser,
            file_processor=file_processor,
            specific_metrics=specific_metrics,
        )

        # Ejecutar el análisis
        results = analyzer.analyze(path)

        if not results.files:
            critical = [
                e.message for e in results.global_errors if e.severity == ErrorSeverity.CRITICAL
            ]
            detail = f" Detalle: {critical[0]}" if critical else ""
            raise click.ClickException(
                f"No se encontraron archivos Python que analizar en '{path}'. Revisa la ruta y "
                f"los patrones de exclusión (--ignore / ignore_patterns).{detail}"
            )

        # Generar el reporte
        if output:
            # Si se especifica un archivo de salida, usar el reporter correspondiente
            output_path = Path(output)
            try:
                reporter_cls = ReporterRegistry.get_reporter(format)
                reporter = reporter_cls(output_path)
                reporter.generate_report(results)
                logger.info(f"Reporte {format} generado en {output_path}")

                presentation_service = get_presentation_service()
                presentation_service.print_success(f"Reporte generado exitosamente: {output_path}")
                presentation_service.print_info(f"Formato: {format.upper()}")
                if output_path.stat().st_size > 0:
                    size_mb = output_path.stat().st_size / (1024 * 1024)
                    presentation_service.print_info(f"Tamaño: {size_mb:.2f} MB")

            except Exception as e:
                logger.error(f"Error al generar reporte: {e}")
                raise click.ClickException(f"Error al generar reporte {format}: {e}") from e
        else:
            # Sin archivo de salida: usar ConsoleReporter o fallback
            if format == "console":
                # Usar ConsoleReporter directamente
                try:
                    from pypex.reporters.console_reporter import (
                        ConsoleReporter,
                    )

                    console_reporter = ConsoleReporter(use_colors=True)
                    console_reporter.generate_report(results, verbosity=verbosity, show_files=True)
                except Exception as e:
                    logger.error(f"Error usando ConsoleReporter: {e}")
                    raise click.ClickException(
                        f"Error al mostrar resultados en consola: {e}"
                    ) from e
            else:
                # Para formatos html/json sin output, mostrar error
                raise click.ClickException(
                    f"Formato '{format}' requiere especificar --output/-o para el archivo de destino"
                )

    except click.ClickException:
        raise  # Re-lanzar excepciones de Click sin modificar
    except Exception as e:
        logger.error(f"Error durante el análisis: {str(e)}", exc_info=True)
        raise click.ClickException(f"Error durante el análisis: {str(e)}") from e


@main.command()
def thresholds():
    """🎯 Muestra los umbrales configurados para todas las métricas.

    Presenta una tabla detallada con los umbrales de complejidad configurados
    para cada métrica disponible, incluyendo descripciones completas y el
    perfil de umbrales actualmente activo.

    \b
    🎚️ INFORMACIÓN MOSTRADA:
    • Número de métrica para referencia
    • Nombre de la métrica
    • Umbrales: Bajo, Medio, Alto
    • Descripción detallada de cada métrica

    \b
    💡 INTERPRETACIÓN DE UMBRALES:
    • Bajo:  Valores aceptables, código de calidad
    • Medio: Valores moderados, revisar si es necesario
    • Alto:  Valores problemáticos, refactoring recomendado

    \b
    📋 PERFILES DISPONIBLES:
    • strict:     Umbrales estrictos para código de alta calidad
    • normal:     Umbrales balanceados (activo por defecto)
    • permissive: Umbrales relajados para código legacy

    \b
    🔧 CAMBIAR PERFIL:
    Use --thresholds-profile en el comando analyze:
      pypex analyze --thresholds-profile strict ./src
    """
    try:
        from pypex.metrics import get_registry
        from pypex.metrics.thresholds import get_threshold_config

        threshold_config = get_threshold_config()
        registry = get_registry()
        available_metrics = sorted(registry.get_available_metrics())

        presentation_service = get_presentation_service()

        # Header con información del perfil
        header_panel = presentation_service.create_panel(
            f"🎯 [bold cyan]Configuración de Umbrales PyPex[/bold cyan]\n\n"
            f"📋 [yellow]Perfil activo:[/yellow] [bold magenta]{threshold_config._active_profile}[/bold magenta]\n"
            f"📊 [yellow]Métricas disponibles:[/yellow] [bold]{len(available_metrics)}[/bold]\n"
            f"💡 [dim]Los umbrales determinan cuándo una métrica indica código problemático[/dim]",
            title="📈 Sistema de Umbrales",
            border_style="blue",
        )
        presentation_service.print_panel(header_panel)

        # Crear tabla de thresholds más amplia
        thresholds_table = presentation_service.create_table(
            title="🎯 Umbrales Detallados por Métrica",
            show_header=True,
            header_style="bold magenta",
            title_style="bold cyan",
            border_style="bright_blue",
            width=120,
        )

        # Agregar columnas a la tabla
        if hasattr(thresholds_table, "add_column"):
            thresholds_table.add_column("#", style="bold dim", width=3, justify="right")
            thresholds_table.add_column("Métrica", style="bold cyan", width=25, no_wrap=False)
            thresholds_table.add_column("🟢 Bajo", style="bold green", justify="center", width=8)
            thresholds_table.add_column("🟡 Medio", style="bold yellow", justify="center", width=8)
            thresholds_table.add_column("🔴 Alto", style="bold red", justify="center", width=8)
            thresholds_table.add_column("📖 Descripción", style="dim", width=65, no_wrap=False)

            # Mostrar thresholds para métricas disponibles con numeración
            for idx, metric_name in enumerate(available_metrics, 1):
                try:
                    metric = registry.get_metric(metric_name)
                    thresholds = threshold_config.get_thresholds(metric_name)

                    # Formatear descripción para mejor visualización
                    description = metric.description
                    if len(description) > 180:
                        # Encontrar un punto de corte natural
                        cut_point = description.find(". ", 150)
                        if cut_point > 0 and cut_point < 200:
                            description = description[: cut_point + 1] + "..."
                        else:
                            description = description[:180] + "..."

                    # Formatear nombre de métrica
                    display_name = metric_name.replace("_", " ").title()

                    thresholds_table.add_row(
                        str(idx),
                        display_name,
                        str(thresholds.get("low", "N/A")),
                        str(thresholds.get("medium", "N/A")),
                        str(thresholds.get("high", "N/A")),
                        description,
                    )
                except Exception as e:
                    logger.warning(f"Error obteniendo thresholds para {metric_name}: {e}")
                    thresholds_table.add_row(
                        str(idx),
                        metric_name.replace("_", " ").title(),
                        "❌",
                        "❌",
                        "❌",
                        f"[red]Error: {str(e)}[/red]",
                    )

            presentation_service.print_table(thresholds_table)

            # Footer con información adicional
            footer_panel = presentation_service.create_panel(
                "💡 [bold]Consejos de Uso:[/bold]\n\n"
                "• [cyan]Valores por debajo del umbral bajo:[/cyan] Código excelente ✨\n"
                "• [yellow]Valores entre bajo y medio:[/yellow] Código aceptable, revisar ocasionalmente 👀\n"
                "• [red]Valores por encima del umbral alto:[/red] Código problemático, refactoring urgente 🚨\n\n"
                "🔧 [bold]Cambiar perfil:[/bold] Use [code]--thresholds-profile strict|normal|permissive[/code]\n"
                "📚 [bold]Más info:[/bold] [link]https://github.com/APenalba/TFG/docs/thresholds[/link]",
                title="ℹ️  Información Adicional",
                border_style="green",
            )
            presentation_service.print_panel(footer_panel)

        else:
            # Fallback mejorado para cuando Rich no está disponible
            click.echo("🎯 UMBRALES CONFIGURADOS PARA PYPEX")
            click.echo("=" * 80)
            click.echo(f"📋 Perfil activo: {threshold_config._active_profile}")
            click.echo(f"📊 Métricas disponibles: {len(available_metrics)}")
            click.echo("=" * 80)

            for idx, metric_name in enumerate(available_metrics, 1):
                try:
                    metric = registry.get_metric(metric_name)
                    thresholds = threshold_config.get_thresholds(metric_name)

                    click.echo(f"\n{idx:2d}. 📊 {metric_name.replace('_', ' ').title()}")
                    click.echo(
                        f"     🟢 Bajo: {thresholds.get('low', 'N/A'):<8} "
                        f"🟡 Medio: {thresholds.get('medium', 'N/A'):<8} "
                        f"🔴 Alto: {thresholds.get('high', 'N/A')}"
                    )

                    # Descripción con wrapping manual
                    desc = metric.description
                    if len(desc) > 70:
                        words = desc.split()
                        lines = []
                        current_line = ""
                        for word in words:
                            if len(current_line + word) < 70:
                                current_line += word + " "
                            else:
                                lines.append(current_line.strip())
                                current_line = word + " "
                        if current_line:
                            lines.append(current_line.strip())

                        for i, line in enumerate(lines[:3]):  # Máximo 3 líneas
                            prefix = "     📖 " if i == 0 else "        "
                            click.echo(f"{prefix}{line}")
                        if len(lines) > 3:
                            click.echo("        ...")
                    else:
                        click.echo(f"     📖 {desc}")

                except Exception as e:
                    logger.warning(f"Error obteniendo thresholds para {metric_name}: {e}")
                    click.echo(f"\n{idx:2d}. ❌ {metric_name} - Error: {e}")

            click.echo("\n" + "=" * 80)
            click.echo("💡 Cambiar perfil: Use --thresholds-profile strict|normal|permissive")
            click.echo("📚 Más información: https://github.com/APenalba/TFG")

    except Exception as e:
        logger.error(f"Error al mostrar thresholds: {e}")
        presentation_service = get_presentation_service()
        presentation_service.print_error(f"Error al cargar umbrales: {e}")


if __name__ == "__main__":
    main()
