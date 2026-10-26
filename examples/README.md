# Ejemplos

Scripts que muestran cómo usar PyPex como librería, sin pasar por la CLI.

```bash
# Reporte de consola de un proyecto, con el nivel de verbosidad indicado
uv run python examples/console_report.py ./pypex verbose

# Reportes JSON (resumen, detallado, completo, solo métricas y personalizado)
uv run python examples/json_report.py
```

Los reportes JSON se escriben en el directorio actual.
