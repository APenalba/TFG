# Métricas de referencia (golden)

Este corpus pequeño fija los resultados del pipeline de análisis de PyPex para flujo de control,
comprensiones, clases, funciones anidadas, decoradores, lambdas y código asíncrono. Cada módulo
cuenta con un snapshot y hay otro para las métricas del proyecto. También se comprueba que el
reporte JSON del CLI coincide con `Analyzer` y que una segunda ejecución produce los mismos datos.

Los snapshots contienen métricas y errores por módulo y entidad, líneas, y métricas de proyecto.
Se normalizan las rutas a nombres relativos, los mensajes que incluyen la ruta del corpus, el orden
de claves y archivos, los sets y los floats (seis decimales). Se excluyen timestamps, duración,
tamaño de archivo y rutas absolutas. Los errores del reporter CLI se ordenan al compararlos porque
el reporter ejecuta las métricas en un orden distinto.

Regenera con `PYPEX_UPDATE_GOLDEN=1 uv run pytest tests/golden` o
`uv run python -m tests.golden.regenerate`. Todo diff de snapshots en una PR debe explicarse en su
descripción. Los tests fallan con las métricas cambiadas y un diff unificado.

## Diferencias de complejidad ciclomática con radon

La comparación usa archivo, nombre cualificado y línea de `def`. Las divergencias conocidas se
fijan por caso en `test_radon_crosscheck.py`; una divergencia nueva, una que desaparezca o un valor
que cambie hace fallar el test.

| Ejemplo | Diferencia conocida |
| --- | --- |
| `comprehensions.py`: `evens`, `index_pairs`, `flatten`, `upper_triangle`, `unique_lengths`, `total_positive`; `shapes.py`: `total_area` | PyPex no suma comprensiones ni expresiones generadoras; radon suma decisiones de `for` e `if`. |
| `functional.py`: `logged`, `retry`, `make_counter` | PyPex suma las decisiones de funciones anidadas a la contenedora. |
| `functional.py`: `logged.wrapper`, `retry.decorator`, `retry.decorator.wrapper`, `make_counter.increment` | PyPex no reporta funciones anidadas como entidades; radon sí las reporta como closures. |
| `control_flow.py`: `sum_until` | radon suma el `else` del bucle. |
| `control_flow.py`: `safe_div` | radon suma el `else` de `try`. |
| `control_flow.py`: `sign_of` | radon suma la expresión ternaria; PyPex no, aunque su docstring indica que sí. |
| `control_flow.py`: `require_positive` | radon suma `assert`; PyPex no. |
| `control_flow.py`: `dispatch` | PyPex cuenta todos los `case`; radon no cuenta `case _`. |
| `control_flow.py`: `classify` | PyPex cuenta cada `elif` dos veces (posible bug). |
| `functional.py`: `double` | PyPex reporta la lambda de módulo, pero falla al calcular su CC; radon no la reporta. |

Para mantener las líneas y claves de comparación, no se deben añadir definiciones dentro de `if` o
`try` a nivel de módulo o clase. El corpus está excluido de ruff para preservar su contenido literal;
no se debe reformatear.
