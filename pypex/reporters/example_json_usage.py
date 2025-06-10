"""Ejemplo de uso del JSONReporter para generar reportes en formato JSON.

Este archivo demuestra cómo utilizar el JSONReporter con diferentes niveles
de detalle y configuraciones.
"""

from pathlib import Path
from typing import Any, Dict

from pypex.core.analyzer import Analyzer
from pypex.core.file_processor import FileProcessor
from pypex.parser.ast_parser import ASTParser
from pypex.reporters.json_reporter import JSONReporter


def analyze_and_generate_json_reports(project_path: str) -> None:
    """
    Ejemplo completo de análisis y generación de reportes JSON.

    Args:
        project_path: Ruta al proyecto a analizar
    """
    # Configurar componentes del analyzer
    file_processor = FileProcessor()
    ast_parser = ASTParser()
    analyzer = Analyzer(file_processor, ast_parser)

    # Analizar el proyecto
    print(f"Analizando proyecto: {project_path}")
    results = analyzer.analyze_project(project_path)

    # Generar diferentes tipos de reportes JSON

    # 1. Reporte de resumen (básico)
    print("\n📊 Generando reporte de resumen...")
    summary_reporter = JSONReporter("pypex_summary.json")
    summary_reporter.generate_report(results, detail_level="summary")

    # 2. Reporte detallado
    print("📋 Generando reporte detallado...")
    detailed_reporter = JSONReporter("pypex_detailed.json")
    detailed_reporter.generate_report(results, detail_level="detailed")

    # 3. Reporte completo
    print("📖 Generando reporte completo...")
    full_reporter = JSONReporter("pypex_full.json")
    full_reporter.generate_report(
        results,
        detail_level="full",
        include_source_code=False,
        include_ast_data=True,
    )

    # 4. Reporte solo de métricas
    print("🔢 Generando reporte de métricas...")
    metrics_reporter = JSONReporter("pypex_metrics.json")
    metrics_data = metrics_reporter.generate_metrics_only(results)

    # Mostrar estadísticas básicas
    print(f"\n✅ Análisis completado:")
    print(f"   - Archivos analizados: {results.total_files}")
    print(f"   - Archivos exitosos: {results.successful_files}")
    print(f"   - Líneas de código: {results.total_lines_of_code}")
    print(f"   - Tiempo de análisis: {results.analysis_time_ms/1000:.2f}s")

    if results.project_metrics:
        print(
            f"   - Métricas de proyecto calculadas: {len(results.project_metrics.metrics)}"
        )


def generate_custom_json_report(
    project_path: str, output_config: Dict[str, Any]
) -> None:
    """
    Ejemplo de generación de reporte JSON personalizado.

    Args:
        project_path: Ruta al proyecto a analizar
        output_config: Configuración del reporte de salida
    """
    # Configurar analyzer
    file_processor = FileProcessor()
    ast_parser = ASTParser()
    analyzer = Analyzer(file_processor, ast_parser)

    # Analizar
    results = analyzer.analyze_project(project_path)

    # Crear reporter personalizado
    reporter = JSONReporter(
        output_config.get("output_path", "custom_report.json")
    )

    # Generar reporte con configuración personalizada
    reporter.generate_report(
        results,
        detail_level=output_config.get("detail_level", "detailed"),
        include_source_code=output_config.get("include_source", False),
        include_ast_data=output_config.get("include_ast", False),
        pretty_print=output_config.get("pretty_print", True),
    )

    print(
        f"✅ Reporte personalizado generado: {output_config.get('output_path')}"
    )


def analyze_single_file_to_json(file_path: str) -> Dict[str, Any]:
    """
    Ejemplo de análisis de un solo archivo y generación de JSON.

    Args:
        file_path: Ruta al archivo a analizar

    Returns:
        Dict con los datos del reporte de resumen
    """
    # Configurar analyzer
    file_processor = FileProcessor()
    ast_parser = ASTParser()
    analyzer = Analyzer(file_processor, ast_parser)

    # Analizar archivo único
    results = analyzer.analyze(file_path)

    # Generar reporte de resumen en memoria
    reporter = JSONReporter()
    summary_data = reporter.generate_summary(results)

    print(f"✅ Archivo analizado: {file_path}")
    print(f"   - Exitoso: {list(results.files.values())[0].was_successful}")
    print(f"   - Líneas: {list(results.files.values())[0].line_count}")

    return summary_data


def main():
    """Función principal para demostrar el uso del JSONReporter."""

    # Ejemplo 1: Análisis completo de proyecto
    project_path = input(
        "Ingresa la ruta del proyecto a analizar (o presiona Enter para ejemplo): "
    ).strip()

    if not project_path:
        # Usar el propio proyecto PyPex como ejemplo
        project_path = str(Path(__file__).parent.parent)
        print(f"Usando proyecto PyPex como ejemplo: {project_path}")

    try:
        analyze_and_generate_json_reports(project_path)

        # Ejemplo 2: Reporte personalizado
        print(f"\n🔧 Generando reporte personalizado...")
        custom_config = {
            "output_path": "pypex_custom.json",
            "detail_level": "detailed",
            "include_source": False,
            "include_ast": False,
            "pretty_print": True,
        }
        generate_custom_json_report(project_path, custom_config)

        # Ejemplo 3: Análisis de un solo archivo
        example_file = Path(project_path) / "core" / "analyzer.py"
        if example_file.exists():
            print(f"\n📄 Analizando archivo individual...")
            file_summary = analyze_single_file_to_json(str(example_file))
            print(
                f"   - Score de calidad: {file_summary['quality_assessment']['overall_score']}"
            )

        print(f"\n🎉 ¡Todos los reportes JSON generados exitosamente!")
        print(f"Archivos generados:")
        print(f"   - pypex_summary.json (resumen)")
        print(f"   - pypex_detailed.json (detallado)")
        print(f"   - pypex_full.json (completo)")
        print(f"   - pypex_metrics.json (solo métricas)")
        print(f"   - pypex_custom.json (personalizado)")

    except Exception as e:
        print(f"❌ Error durante el análisis: {e}")


if __name__ == "__main__":
    main()
