"""Ejemplo de uso del ConsoleReporter para mostrar reportes en la terminal.

Este archivo demuestra cómo utilizar el ConsoleReporter con diferentes niveles
de verbosidad y opciones de configuración.
"""

import sys

from pypex.core.analyzer import Analyzer
from pypex.core.file_processor import FileProcessor
from pypex.parser.ast_parser import ASTParser
from pypex.reporters.console_reporter import ConsoleReporter


def analyze_and_show_console_reports(
    project_path: str,
    verbosity: str = "normal",
    use_colors: bool | None = None,
) -> None:
    """
    Ejemplo completo de análisis y generación de reportes de consola.

    Args:
        project_path: Ruta al proyecto a analizar
        verbosity: Nivel de verbosidad ("quiet", "normal", "verbose", "debug")
        use_colors: Si usar colores (None = auto-detectar)
    """
    print(f"🔍 Analizando proyecto: {project_path}")
    print("=" * 60)

    # Configurar componentes del analyzer
    file_processor = FileProcessor()
    ast_parser = ASTParser()
    analyzer = Analyzer(file_processor, ast_parser)

    try:
        # Realizar análisis
        results = analyzer.analyze_project(project_path)

        # Crear reporter de consola
        console_reporter = ConsoleReporter(use_colors=use_colors)

        # Generar reporte según el nivel de verbosidad
        if verbosity == "quiet":
            console_reporter.generate_report(results, verbosity="quiet")
        elif verbosity == "normal":
            console_reporter.generate_report(
                results,
                verbosity="normal",
                show_files=True,
                show_entities=False,
            )
        elif verbosity == "verbose":
            console_reporter.generate_report(
                results,
                verbosity="verbose",
                show_files=True,
                show_entities=True,
            )
        elif verbosity == "debug":
            console_reporter.generate_report(
                results,
                verbosity="debug",
                show_files=True,
                show_entities=True,
                show_metrics=True,
            )
        else:
            raise ValueError(f"Verbosity level '{verbosity}' not supported")

    except Exception as e:
        print(f"❌ Error durante el análisis: {e}")
        sys.exit(1)


def demo_different_outputs() -> None:
    """Demuestra diferentes tipos de salida del ConsoleReporter."""

    # Ejemplo de uso con diferentes configuraciones
    sample_project = "./pypex"  # Analizarse a sí mismo

    print("🎨 Demo de diferentes salidas del ConsoleReporter")
    print("=" * 60)

    # 1. Reporte mínimo (quiet)
    print("\n1️⃣ Reporte QUIET (mínimo):")
    print("-" * 40)
    analyze_and_show_console_reports(sample_project, "quiet", use_colors=True)

    print("\n" + "=" * 60)

    # 2. Reporte normal
    print("\n2️⃣ Reporte NORMAL (balanceado):")
    print("-" * 40)
    analyze_and_show_console_reports(sample_project, "normal", use_colors=True)

    print("\n" + "=" * 60)

    # 3. Reporte detallado
    print("\n3️⃣ Reporte VERBOSE (detallado):")
    print("-" * 40)
    analyze_and_show_console_reports(sample_project, "verbose", use_colors=True)


def demo_colors_and_formatting() -> None:
    """Demuestra las capacidades de colores y formateo."""

    # Crear un reporter para mostrar capacidades
    reporter = ConsoleReporter(use_colors=True)

    print("🌈 Demo de colores y formateo")
    print("=" * 60)

    # Mostrar diferentes tipos de mensajes
    reporter.print_success("Este es un mensaje de éxito")
    reporter.print_warning("Este es un mensaje de advertencia")
    reporter.print_error("Este es un mensaje de error")
    reporter.print_info("Este es un mensaje informativo")

    print()
    reporter.print_separator("═")
    reporter.print_section_header("Sección de Ejemplo", "📊")

    # Mostrar colores de calidad
    print("\n🎯 Colores de calidad:")
    scores = [95, 75, 55, 35, 15]
    for score in scores:
        quality_color = reporter._get_quality_color(score)
        quality_level = reporter._get_quality_level(score)
        print(f"   Score {score}: {reporter.colorize(quality_level, quality_color)}")


def demo_without_colors() -> None:
    """Demuestra la salida sin colores (para CI/CD)."""

    sample_project = "./pypex"

    print("\n📄 Demo SIN colores (ideal para CI/CD o redirección):")
    print("-" * 60)

    analyze_and_show_console_reports(sample_project, "normal", use_colors=False)


def main():
    """Función principal para ejecutar las demos."""

    if len(sys.argv) > 1:
        project_path = sys.argv[1]
        verbosity = sys.argv[2] if len(sys.argv) > 2 else "normal"

        print(f"📁 Analizando: {project_path}")
        print(f"🔧 Verbosidad: {verbosity}")

        analyze_and_show_console_reports(project_path, verbosity, use_colors=True)
    else:
        # Ejecutar demos
        print("🚀 Demos del ConsoleReporter")
        print("=" * 80)

        try:
            # Demo de colores y formateo
            demo_colors_and_formatting()

            # Demo de diferentes salidas (comentado para evitar ejecución larga)
            # demo_different_outputs()

            # Demo sin colores
            # demo_without_colors()

            print("\n✅ Demos completadas!")
            print("\n💡 Para analizar un proyecto específico:")
            print("   python example_console_usage.py <ruta_proyecto> [verbosity]")
            print("   Donde verbosity puede ser: quiet, normal, verbose, debug")

        except Exception as e:
            print(f"❌ Error en demos: {e}")


if __name__ == "__main__":
    main()
