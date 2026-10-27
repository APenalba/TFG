# 🐍 PyPex: Analizador Integral de Métricas y Calidad de Código Python

<div align="center">

[![Python Version](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Development Status](https://img.shields.io/badge/status-alpha-orange.svg)](https://github.com/APenalba/TFG)
[![CI](https://github.com/APenalba/TFG/actions/workflows/ci.yml/badge.svg)](https://github.com/APenalba/TFG/actions/workflows/ci.yml)

**Analizador profesional de métricas de calidad, complejidad, cohesión y mantenibilidad para proyectos Python**

[📊 Ver Reporte PyPex del Proyecto](https://apenalba.github.io/TFG)

[🚀 Instalación](#-instalación) • [📊 Características](#-características-principales) • [🎯 Uso Rápido](#-uso-rápido) • [📖 Metodología](#metodología-de-las-métricas) • [🤝 Contribuir](#-contribuir)

</div>

---

## 📋 Tabla de Contenidos

- [🔍 ¿Qué es PyPex?](#-qué-es-pypex)
- [📊 Características Principales](#-características-principales)
- [🚀 Instalación](#-instalación)
- [🎯 Uso Rápido](#-uso-rápido)
- [📈 Métricas Disponibles](#-métricas-disponibles)
- [Metodología de las métricas](#metodología-de-las-métricas)
- [🖥️ Comandos CLI](#️-comandos-cli)
- [⚙️ Configuración](#️-configuración)
- [📊 Formatos de Salida](#-formatos-de-salida)
- [🎚️ Perfiles de Umbrales](#️-perfiles-de-umbrales)
- [🏗️ Arquitectura](#️-arquitectura)
- [🧪 Testing](#-testing)
- [🤝 Contribuir](#-contribuir)
- [📞 Soporte y Contacto](#-soporte-y-contacto)
- [📄 Licencia](#-licencia)

---

## 🔍 ¿Qué es PyPex?

**PyPex** es una herramienta profesional de análisis estático de código diseñada para evaluar **métricas integrales de calidad de software** en proyectos Python. Desarrollada como proyecto de **Trabajo de Fin de Grado (TFG)**, combina métricas tradicionales de ingeniería de software con análisis específicos para Python.

### 🎯 Objetivo Principal

Proporcionar a desarrolladores, equipos de desarrollo y auditores de código una herramienta completa para:

- **Medir** métricas de calidad de código de forma objetiva y comprehensiva
- **Evaluar** complejidad, cohesión, acoplamiento y mantenibilidad del software
- **Identificar** puntos problemáticos que requieren refactoring
- **Generar** reportes profesionales para stakeholders
- **Monitorear** la evolución de la calidad del código

---

## 📊 Características Principales

### 🔢 **16 Métricas de Calidad Integral**
- **Complejidad**: Ciclomática, cognitiva, esencial, anidamiento
- **Cohesión y Acoplamiento**: LCOM4, Fan-In/Fan-Out, CBO
- **Calidad de Diseño**: Métricas de Halstead, complejidad de diseño
- **Tamaño y Documentación**: LOC, SLOC, ratio documentación/código
- **Específicas Python**: Comprehensions, generadores, manejo excepciones
- **Métricas de Proyecto**: LOC, Halstead, Fan-Out e indicadores de acoplamiento agregados

### 📊 **Análisis Multi-Nivel**
- **Función**: Análisis detallado de métodos y funciones
- **Clase**: Métricas de cohesión y diseño orientado a objetos
- **Módulo**: Análisis de archivos individuales y documentación
- **Proyecto**: Métricas agregadas y panorama arquitectónico general

### 🎨 **Múltiples Formatos de Salida**
- **HTML**: Reportes web interactivos con gráficos y navegación
- **JSON**: Datos estructurados para integración con CI/CD
- **Consola**: Salida rica con colores, tablas e iconos

### ⚙️ **Configuración Flexible**
- **Archivos de configuración** YAML o JSON
- **Perfiles de umbrales** (strict/normal/permissive)
- **Filtros avanzados** para archivos y directorios
- **Métricas selectivas** - incluir/excluir específicas

### 🎯 **Fácil Integración**
- **CLI simple** con comandos intuitivos
- **Configuración por argumentos** o archivos
- **Logging detallado** para debugging
- **API programática** para integraciones custom ([ejemplos](examples/README.md))

---

## 🚀 Instalación

### Requisitos Previos

- **Python 3.12+**
- **[uv](https://docs.astral.sh/uv/)** (gestor de dependencias y entornos)

### Instalación desde Código Fuente

```bash
# Clonar el repositorio
git clone https://github.com/APenalba/TFG.git
cd TFG

# Crear el entorno e instalar dependencias
uv sync

# Verificar instalación
uv run pypex --help
```

### Instalación en Modo Desarrollo

```bash
# uv sync instala también el grupo de desarrollo (pytest, ruff, mypy...)
uv sync

# Instalar pre-commit hooks
uv run pre-commit install

# Ejecutar tests
uv run pytest
```

### Uso con Python directo

```bash
# Si no se puede usar como comando
uv run python -m pypex --help
```

---

## 🎯 Uso Rápido

Los ejemplos usan `pypex` directamente. Con `uv`, antepón `uv run` o activa el entorno virtual del proyecto.

### Análisis Básico

```bash
# Análisis completo del directorio actual
pypex analyze .

# Análisis de un archivo específico
pypex analyze mi_script.py

# Análisis de un proyecto con salida detallada
pypex analyze --verbosity verbose ./mi_proyecto
```

### Reportes Avanzados

```bash
# Generar reporte HTML interactivo
pypex analyze --format html --output reporte.html ./src

# Exportar datos a JSON
pypex analyze --format json --output datos.json ./proyecto

# Análisis con métricas específicas
pypex analyze -m cyclomatic_complexity -m cognitive_complexity ./src
```

### Configuración Avanzada

```bash
# Usar archivo de configuración
pypex analyze --config pypex.yaml ./proyecto

# Análisis estricto para código de alta calidad
pypex analyze --thresholds-profile strict ./src

# Excluir archivos de test y configuración
pypex analyze --ignore "test_*.py" --ignore "setup.py" ./proyecto
```

### Ver Configuración

```bash
# Mostrar todas las métricas y umbrales configurados
pypex thresholds
```

---

## 📈 Métricas Disponibles

PyPex implementa **16 métricas** organizadas en **5 categorías**:

### 🔄 **Complejidad Estructural**

| Métrica (`nombre`) | Qué mide | Niveles |
|--------------------|----------|---------|
| Complejidad Ciclomática (`cyclomatic_complexity`) | 1 + puntos de decisión (McCabe) | Función (estadísticas en clase) |
| Complejidad Cognitiva (`cognitive_complexity`) | Estructuras de control penalizadas por su anidamiento | Función (estadísticas en clase) |
| Profundidad de Anidamiento (`nesting_depth`) | Máximo de bloques anidados | Función (estadísticas en clase) |
| Complejidad Esencial (`essential_complexity`) | 1 + salidas no estructuradas (`break`, `continue`, `raise`, `yield`, `return` anticipado) | Función (estadísticas en clase) |
| Complejidad Lógica (`logical_complexity`) | 1 + operadores `and`/`or` | Función (estadísticas en clase) |

### 🐍 **Específicas de Python**

| Métrica (`nombre`) | Qué mide | Niveles |
|--------------------|----------|---------|
| Complejidad de Comprensiones (`comprehension_complexity`) | Nº de cláusulas `if` en comprensiones y expresiones generadoras | Función (estadísticas en clase) |
| Profundidad de Comprensiones Anidadas (`nested_comprehension_depth`) | Máximo anidamiento de comprensiones | Función (estadísticas en clase) |
| Manejo de Excepciones (`exception_handling_complexity`) | Bloques `try` + cláusulas `except` | Función (estadísticas en clase) |
| Complejidad de Generadores (`generator_complexity`) | Nº de `yield` / `yield from` | Función (estadísticas en clase) |

### 📏 **Métricas de Tamaño**

| Métrica (`nombre`) | Qué mide | Niveles |
|--------------------|----------|---------|
| Líneas de Código (`lines_of_code`) | SLOC: líneas que no están en blanco, no son solo comentario y no son docstring | Función, clase, módulo, proyecto |
| Conteo de Parámetros (`parameter_count`) | Nº de parámetros (incluye `self`, `*args`, `**kwargs`) | Función (media sin `self` en clase) |

### 🔗 **Acoplamiento y Cohesión**

| Métrica (`nombre`) | Qué mide | Niveles |
|--------------------|----------|---------|
| Fan-In/Fan-Out (`fan_in_out`) | Fan-out: nº de destinos de llamada distintos. Fan-in aún no se calcula | Función, clase, módulo, proyecto |
| LCOM4 (`lcom4`) | Componentes conexos del grafo de métodos | Clase |
| Acoplamiento Avanzado (`advanced_coupling`) | CBO, RFC, MPC (clase); Ce, Ca, inestabilidad, abstracción, distancia a la secuencia principal (módulo y proyecto) | Clase, módulo, proyecto |

### 🏗️ **Calidad de Diseño**

| Métrica (`nombre`) | Qué mide | Niveles |
|--------------------|----------|---------|
| Complejidad de Diseño (`design_complexity`) | Nº de destinos de llamada distintos de la función | Función (estadísticas en clase) |
| Halstead (`halstead`) | η1, η2, N1, N2, vocabulario, longitud, volumen, dificultad, esfuerzo, tiempo, bugs | Función, clase, módulo, proyecto |

Detalles de cálculo en [Metodología de las métricas](#metodología-de-las-métricas).

## Metodología de las métricas

PyPex calcula las métricas sobre el AST de [astroid](https://github.com/pylint-dev/astroid). Esta sección
describe exactamente qué cuenta cada métrica y en qué se diferencia de otras herramientas como
[radon](https://radon.readthedocs.io/).

### Entidades analizadas

- **Funciones**: funciones y funciones asíncronas, incluidas las lambdas asignadas a una variable.
- **Métodos**: funciones definidas dentro de clases.
- **Clases**: clases detectadas en el código.
- **Funciones anidadas** (closures y funciones internas) **no** son entidades propias: su código forma parte
  de la función que las contiene y suma a sus métricas.

Las métricas de función se calculan sobre todo el cuerpo de la función, incluidas sus funciones anidadas.
El código suelto a nivel de módulo (fuera de funciones y clases) no se mide con métricas de función.

### Niveles de cálculo

- **Función / método**: valor numérico de cada métrica (Halstead devuelve un diccionario).
- **Clase**: estadísticas sobre sus métodos (media, máximo, mínimo, nº de métodos y nº de métodos por
  encima de un límite), además de LCOM4 y CBO/RFC/MPC. Para la complejidad no se suma el total de la clase.
- **Módulo**: solo líneas de código, Halstead, Fan-Out (media) y acoplamiento avanzado (Ce, inestabilidad,
  abstracción, distancia).
- **Proyecto**: agregados de líneas de código, Halstead, Fan-Out y acoplamiento avanzado (incluido Ca).
- La complejidad ciclomática, la cognitiva y el resto de métricas de función **no** se agregan a nivel de
  módulo ni de proyecto.

### Complejidad ciclomática (`cyclomatic_complexity`)

`CC = 1 + puntos de decisión`. Suman:

| Construcción | Incremento |
|---|---|
| `if` | +1 |
| `elif` | +2 (ver [Limitaciones conocidas](#limitaciones-conocidas)) |
| `for`, `async for`, `while` | +1 |
| cada `except` de un `try` | +1 |
| cada `case` de un `match` (incluido `case _`) | +1 |
| expresión booleana con *n* operandos (`a and b and c`) | +(n − 1) |

No suman: `else` (de `if`, bucles o `try`), `finally`, `with`, `assert`, expresiones condicionales
(`x if c else y`), las cláusulas `for`/`if` de comprensiones y expresiones generadoras, ni `except*`.
Los operadores `and`/`or` dentro de una comprensión o de una lambda sí suman.

**Decisiones que difieren de radon:**

1. **Comprensiones fuera de la CC.** Los `for` e `if` de comprensiones y expresiones generadoras no suman.
   Se miden aparte con `comprehension_complexity`, `nested_comprehension_depth` y `nesting_depth`.
2. **Funciones anidadas sumadas a la contenedora.** radon reporta los closures por separado y no los suma;
   PyPex los integra en la función que los define.
3. **Ternarios, `else` de bucles y `try`, `assert` y `case _`** no suman en PyPex; en radon sí. En
   particular, ambas herramientas suman cada `except`; la diferencia de `try / except / else` es que radon
   suma +1 por el `else` de `try` y PyPex no.

Ejemplo (verificado con PyPex y radon 6.0.1):

| Función | PyPex | radon |
|---|---:|---:|
| `return [x for x in xs if x > 0]` | 1 | 3 |
| función con un closure que contiene un `if` | 2 | 1 (closure aparte con 2) |
| `if / elif / else` | 4 | 3 |
| `return 1 if x else 0` | 1 | 2 |
| `match` con `case 1` y `case _` | 3 | 2 |
| `for … if … break … else` | 3 | 4 |
| `try / except / else` | 2 | 3 |
| `assert x` | 1 | 2 |

Sobre el código de click 8.5, el 79 % de las funciones obtiene la misma CC en ambas herramientas;
el resto de diferencias se explica por las reglas anteriores.

### Complejidad cognitiva (`cognitive_complexity`)

Inspirada en la métrica de SonarSource, con estas reglas:

- `if` (y cada `elif`, que se trata como un `if` anidado), `for`, `async for`, `while` y `match`:
  +1 más el nivel de anidamiento actual; su contenido queda un nivel más anidado.
- Cada `case` y cada `except`: +1 (sin penalización por anidamiento); su cuerpo queda un nivel más anidado.
- Expresión booleana con *n* operandos: +(n − 1).
- Una función anidada aumenta en 1 el nivel de anidamiento de su cuerpo.
- El recorrido parte de la propia definición, de modo que el cuerpo de la función ya está en el nivel 1:
  un `if` en el cuerpo principal suma 2.
- No suman: `else`, `try`, `finally`, `with`, ternarios, comprensiones, `break`/`continue` ni recursión.

### Profundidad de anidamiento (`nesting_depth`)

Máximo de bloques anidados dentro del cuerpo. Cada uno de estos nodos añade un nivel: `if` (un `elif`
añade otro), `for`, `while`, `try`, `except`, `with`, `match`, `case` y cada comprensión o expresión
generadora. Por ejemplo, un `try/except` tiene profundidad 2. Las funciones anidadas no añaden nivel,
pero su contenido se tiene en cuenta.

### Complejidad esencial (`essential_complexity`)

No es la complejidad esencial de McCabe (reducibilidad del grafo), sino una aproximación:
`1 + nº de break + continue + raise + yield/yield from + return anticipados`. Un `return` no cuenta si
es la última sentencia del cuerpo o está dentro de ella (por ejemplo, en el `if` final).

### Métricas específicas de Python

- `logical_complexity`: `1 + Σ(n − 1)` sobre todas las expresiones `and`/`or`.
- `comprehension_complexity`: nº total de cláusulas `if` en comprensiones (`list`, `set`, `dict`) y
  expresiones generadoras.
- `nested_comprehension_depth`: máxima profundidad de comprensiones dentro de comprensiones (1 = sin anidar).
- `exception_handling_complexity`: nº de bloques `try` + nº de cláusulas `except`.
- `generator_complexity`: nº de expresiones `yield` y `yield from` (las expresiones generadoras no cuentan).

### Tamaño

- `lines_of_code`: SLOC = líneas que no están en blanco, no son solo un comentario y no forman parte del
  docstring. En clases, módulos y proyecto el resultado incluye además líneas de documentación, comentarios,
  ratios de documentación y comentarios, y nº de imports.
- `parameter_count`: todos los parámetros de la firma (posicionales, solo-posicionales, solo-keyword,
  `*args`, `**kwargs`, incluido `self`). En una clase se informa la media por método sin contar `self`.

### Acoplamiento, cohesión y diseño

- **Llamadas de una función**: destinos distintos que astroid consigue inferir (por ejemplo `builtins.len`).
  Si la inferencia falla con error se usa el texto de la llamada; las llamadas no inferibles se descartan.
  Incluye las llamadas hechas en funciones anidadas.
- `design_complexity` y `fan_in_out` (en función) = nº de llamadas distintas (fan-out). El fan-in todavía
  no se calcula. En clase, módulo y proyecto `fan_in_out` da la media de llamadas y añade acoplamiento por
  herencia e imports.
- `lcom4`: grafo cuyos nodos son los métodos de la clase. Hay arista si dos métodos acceden al mismo
  atributo a través de su primer parámetro (`self.x`) o si uno llama al otro. El valor es el nº de
  componentes conexos (1 = clase cohesionada).
- `advanced_coupling`: en clase, CBO = clases base + clases externas usadas; RFC = métodos propios +
  métodos externos llamados; MPC = nº de llamadas externas. En módulo, Ce = nº de imports, inestabilidad
  I = Ce/(Ca+Ce), abstracción A = clases abstractas/clases y distancia D = |A + I − 1|. Ca solo se estima
  a nivel de proyecto, contando cuántos módulos del proyecto importan a cada uno.

### Halstead (`halstead`)

Aproximación sobre el AST. Operadores: operadores binarios, unarios, booleanos y de comparación,
asignaciones, llamadas y acceso a atributos. Operandos: nombres, constantes, expresión llamada y objeto
base de un atributo. Con η1/η2 (únicos) y N1/N2 (totales):
vocabulario η = η1 + η2, longitud N = N1 + N2, volumen V = N·log2 η, dificultad D = (η1/2)·(N2/η2),
esfuerzo E = D·V, tiempo T = E/18 s y bugs B = V/3000. Los valores no son comparables con los de otras
herramientas, porque cada una clasifica operadores y operandos de forma distinta.

### Limitaciones conocidas

- Cada `elif` suma 2 a la complejidad ciclomática (se cuenta como rama del `if` anterior y como `if` propio).
- `try/except*` no se cuenta en la complejidad ciclomática ni en el manejo de excepciones.

---

## 🖥️ Comandos CLI

PyPex proporciona **2 comandos principales** con múltiples opciones:

### `pypex analyze` - Análisis de Código

**Sintaxis**: `pypex analyze [OPCIONES] RUTA`

#### Opciones Principales

| Opción | Descripción | Ejemplo |
|--------|-------------|---------|
| `--output`, `-o` | Archivo de salida del reporte | `-o reporte.html` |
| `--format`, `-f` | Formato de salida (html/json/console) | `-f html` |
| `--config`, `-c` | Archivo de configuración | `-c pypex.yaml` |
| `--verbosity` | Nivel de detalle (quiet/normal/verbose/debug) | `--verbosity verbose` |

#### Selección de Métricas

| Opción | Descripción | Ejemplo |
|--------|-------------|---------|
| `--metrics`, `-m` | Métricas específicas a calcular | `-m cyclomatic_complexity` |
| `--exclude-metrics`, `-x` | Métricas a excluir | `-x lcom4 -x design_complexity` |

#### Filtros y Configuración

| Opción | Descripción | Ejemplo |
|--------|-------------|---------|
| `--ignore`, `-i` | Patrones glob para ignorar | `-i "test_*.py" -i "__pycache__"` |
| `--max-file-size`, `-s` | Tamaño máximo de archivo (bytes) | `-s 2097152` |
| `--thresholds-profile`, `-t` | Perfil de umbrales | `-t strict` |

#### Ejemplos de Uso

```bash
# Análisis básico con salida normal
pypex analyze ./proyecto

# Reporte HTML completo con métricas específicas
pypex analyze \
  --format html \
  --output reporte_completo.html \
  --metrics cyclomatic_complexity \
  --metrics cognitive_complexity \
  --metrics nesting_depth \
  --verbosity verbose \
  ./src

# Análisis estricto excluyendo tests
pypex analyze \
  --thresholds-profile strict \
  --ignore "test_*.py" \
  --ignore "*_test.py" \
  --format json \
  --output calidad_codigo.json \
  ./mi_proyecto

# Análisis de proyecto grande con configuración
pypex analyze \
  --config pypex.yaml \
  --max-file-size 5242880 \
  --verbosity debug \
  ./proyecto_grande
```

### `pypex thresholds` - Ver Configuración

**Sintaxis**: `pypex thresholds`

Muestra una tabla detallada con:
- **Todas las métricas** disponibles numeradas
- **Umbrales configurados** (Bajo/Medio/Alto)
- **Descripciones** completas de cada métrica
- **Perfil activo** y consejos de uso

```bash
# Ver todos los umbrales configurados
pypex thresholds
```

### Opciones Globales

| Opción | Descripción | Aplicación |
|--------|-------------|------------|
| `-v`, `--verbose` | Activar modo verboso | Todos los comandos |
| `--version` | Mostrar la versión | Comando principal |
| `--log-file` | Archivo para logs detallados | Debugging |
| `--help` | Mostrar ayuda | Cada comando |

---

## ⚙️ Configuración

PyPex admite configuración a través de **archivos YAML/JSON** y **argumentos CLI**, con precedencia para los argumentos de línea de comandos.

### Archivo de Configuración de Ejemplo

```yaml
# pypex.yaml - Configuración completa de ejemplo

# ═══════════════════════════════════════════════════════════════════════════════
# 🔧 CONFIGURACIÓN GENERAL
# ═══════════════════════════════════════════════════════════════════════════════

# Tamaño máximo de archivo a procesar (en bytes)
max_file_size: 1048576  # 1MB

# ═══════════════════════════════════════════════════════════════════════════════
# 📊 CONFIGURACIÓN DE MÉTRICAS
# ═══════════════════════════════════════════════════════════════════════════════

# Métricas específicas a calcular (omitir para usar todas)
metrics:
  - "cyclomatic_complexity"
  - "cognitive_complexity"
  - "nesting_depth"
  - "lines_of_code"
  - "parameter_count"
  - "fan_in_out"

# Métricas a excluir del análisis
exclude_metrics:
  - "lcom4"  # Solo para clases
  - "halstead"  # Métricas muy técnicas

# ═══════════════════════════════════════════════════════════════════════════════
# 🗂️ FILTROS DE ARCHIVOS
# ═══════════════════════════════════════════════════════════════════════════════

ignore_patterns:
  # Directorios comunes
  - "__pycache__"
  - ".git"
  - ".pytest_cache"
  - ".mypy_cache"
  - "venv"
  - "env"

  # Archivos de prueba
  - "test_*.py"
  - "*_test.py"
  - "tests.py"

  # Configuración
  - "setup.py"
  - "conftest.py"

  # Temporales
  - "*.tmp"
  - "*.bak"
  - "*.pyc"

# ═══════════════════════════════════════════════════════════════════════════════
# 📝 CONFIGURACIÓN DE LOGGING
# ═══════════════════════════════════════════════════════════════════════════════

verbose: false
log_file: null
```

### Umbrales personalizados

Se pueden definir los tres niveles para una métrica en la configuración:

```yaml
thresholds:
  cyclomatic_complexity:
    low: 5
    medium: 10
    high: 20
```

### Usar Configuración

```bash
# Usar archivo de configuración
pypex analyze --config pypex.yaml ./proyecto

# Sobrescribir configuración desde CLI
pypex analyze --config pypex.yaml -m cyclomatic_complexity ./src
```

---

## 📊 Formatos de Salida

PyPex admite **3 formatos principales** de salida, cada uno optimizado para casos de uso específicos:

### 🖥️ **Consola (console)** - *Por defecto*

Salida rica en la terminal con **4 niveles de verbosidad**:

#### `--verbosity quiet`

```text
✅ pypex: 56/56 files, 20375 LOC, Quality: 53.7/100
```

#### `--verbosity normal` *(por defecto)*

Muestra el resumen del análisis, las métricas agregadas y los puntos de mayor complejidad.

#### `--verbosity verbose`

Añade detalles por archivo y entidad, además de recomendaciones.

#### `--verbosity debug`

Incluye información de configuración, procesamiento, tiempos y errores para depuración.

### 🌐 **HTML (html)** - *Reportes Interactivos*

Genera reportes web profesionales con:

- **Dashboard principal** con resumen ejecutivo
- **Navegación por módulos** y funciones
- **Gráficos interactivos** (histogramas, heatmaps)
- **Tablas ordenables** y filtros
- **Detalles drill-down** por métrica
- **Recomendaciones** contextuales
- **Exportación** de datos

```bash
pypex analyze --format html --output reporte_completo.html ./proyecto
```

**Características del reporte HTML:**
- 📊 **Dashboard**: Resumen ejecutivo con KPIs
- 🗂️ **Navegación**: Árbol de archivos interactivo
- 📈 **Gráficos**: Distribuciones y tendencias
- 🔍 **Detalles**: Análisis función por función
- 💡 **Recomendaciones**: Sugerencias de mejora
- 🎨 **Responsive**: Funciona en móviles y desktop

### 📄 **JSON (json)** - *Integración y Análisis*

Datos estructurados para integración con herramientas externas. Este extracto real se generó al analizar
`pypex/metrics/thresholds.py`; se muestran las claves de primer nivel y una entidad completa:

```json
{
  "pypex_report": "...",
  "project": "...",
  "quality_reports": "...",
  "metrics_aggregation": "...",
  "performance_analysis": "...",
  "files": {
    "pypex/metrics/thresholds.py": {
      "file_info": "...",
      "module_metrics": "...",
      "entities": [
        {
          "name": "get_threshold_config",
          "type": "function",
          "metrics": {
            "entity_name": "get_threshold_config",
            "entity_type": "function",
            "metrics": {
              "nesting_depth": 1.0,
              "comprehension_complexity": 0.0,
              "design_complexity": 1.0,
              "exception_handling_complexity": 0.0,
              "fan_in_out": 1,
              "essential_complexity": 1.0,
              "nested_comprehension_depth": 0.0,
              "logical_complexity": 1.0,
              "cyclomatic_complexity": 2.0,
              "halstead": {
                "eta1": 3.0,
                "eta2": 3.0,
                "N1": 3.0,
                "N2": 5.0,
                "vocabulary": 6,
                "length": 8,
                "volume": 20.67970000576925,
                "difficulty": 2.5,
                "effort": 51.69925001442312,
                "time": 2.87218055635684,
                "bugs": 0.006893233335256416
              },
              "cognitive_complexity": 2.0,
              "generator_complexity": 0.0,
              "parameter_count": 0.0,
              "lines_of_code": 5.0
            },
            "metadata": {},
            "errors": []
          },
          "source_info": {"line_start": 248, "line_end": 257}
        }
      ]
    }
  },
  "hot_spots": "...",
  "error_analysis": "...",
  "recommendations": "..."
}
```

**Casos de uso del formato JSON:**
- **CI/CD**: Integración con pipelines
- **Análisis histórico**: Seguimiento de evolución
- **Dashboards**: Herramientas de monitoring
- **Investigación**: Análisis estadístico

---

## 🎚️ Perfiles de Umbrales

Cada métrica define tres umbrales (`low`, `medium`, `high`) que clasifican un valor en cuatro niveles:
**Baja** (< low), **Media** (< medium), **Alta** (< high) y **Muy Alta** (≥ high).

Umbrales por defecto (`pypex thresholds`):

| Métrica | low | medium | high |
|---|---:|---:|---:|
| advanced_coupling | 5 | 10 | 20 |
| cognitive_complexity | 15 | 25 | 50 |
| comprehension_complexity | 2 | 5 | 8 |
| cyclomatic_complexity | 10 | 20 | 50 |
| design_complexity | 2 | 5 | 10 |
| essential_complexity | 1 | 3 | 6 |
| exception_handling_complexity | 1 | 3 | 6 |
| fan_in_out | 5 | 10 | 20 |
| generator_complexity | 1 | 3 | 6 |
| halstead | 500 | 2000 | 8000 |
| lcom4 | 1 | 2 | 4 |
| lines_of_code | 30 | 75 | 150 |
| logical_complexity | 2 | 5 | 10 |
| nested_comprehension_depth | 1 | 2 | 3 |
| nesting_depth | 3 | 6 | 9 |
| parameter_count | 3 | 5 | 7 |

Los umbrales se pueden personalizar en el archivo de configuración indicando los tres valores en `thresholds:`.

### Perfil (`--thresholds-profile`)

El perfil no modifica los valores de las métricas ni los umbrales. Decide qué informes de calidad
(`quality_reports` en JSON) se generan y con qué umbral se considera problemática una entidad:

| Perfil | Informe básico | Informe avanzado |
|---|---|---|
| `normal` (por defecto) | sí, umbral `medium` | sí, umbral `high` |
| `strict` | no | sí, umbral `high` |
| `permissive` | sí, umbral `low` | no |

El perfil se indica en la línea de comandos (`--thresholds-profile`).

---

## 🏗️ Arquitectura

PyPex sigue una **arquitectura modular** diseñada para extensibilidad y mantenimiento:

### Componentes Principales

```
pypex/
├── core/                    # 🏗️ Núcleo del sistema
│   ├── analyzer.py          # Coordinador principal
│   ├── project.py           # Modelo de proyecto
│   ├── file_processor.py    # Procesamiento de archivos
│   ├── results.py           # Gestión de resultados
│   ├── results_processor.py # Procesamiento de resultados
│   └── interfaces.py        # Interfaces y contratos
│
├── parser/                  # 🔍 Análisis de código
│   ├── ast_parser.py        # Parser de AST
│   ├── astroid_visitor.py   # Visitante de nodos
│   ├── code_entities.py     # Entidades de código
│   └── node_visitor.py      # Patrón visitor
│
├── metrics/                 # 📊 Sistema de métricas
│   ├── base.py              # Interfaz base
│   ├── registry.py          # Registro de métricas
│   ├── engine.py            # Motor de cálculo
│   ├── thresholds.py        # Configuración de umbrales
│   │
│   ├── complexity/          # Métricas de complejidad
│   ├── coupling/            # Métricas de acoplamiento
│   ├── cohesion/            # Métricas de cohesión
│   ├── design/              # Métricas de diseño
│   └── size/                # Métricas de tamaño
│
├── reporters/               # 📄 Sistema de reportes
│   ├── console_reporter.py  # Salida en consola
│   ├── json_reporter.py     # Exportación JSON
│   └── html/                # Reporte HTML
│
├── assets/                  # Recursos estáticos
├── services/                # 🔧 Servicios transversales
│   ├── config_service.py    # Gestión de configuración
│   └── logging_service.py   # Sistema de logging
│
├── __main__.py              # Entrada para python -m pypex
└── cli.py                   # 🖥️ Interfaz de línea de comandos
```

### Flujo de Ejecución

1. **CLI** → Procesa argumentos y configuración
2. **Analyzer** → Coordina el análisis completo
3. **FileProcessor** → Procesa archivos individuales
4. **Parser** → Genera AST de código Python
5. **Metrics** → Calcula métricas sobre entidades
6. **Reporter** → Genera salida en formato deseado

### Patrones de Diseño

- **Singleton**: `MetricsRegistry`, `ThresholdConfig` y `ConfigService`

---

## 🧪 Testing

PyPex incluye una **suite completa de tests** para garantizar calidad y robustez:

La CI (`.github/workflows/ci.yml`) ejecuta lint (`ruff check` y `ruff format --check`), tests en Python 3.12, 3.13 y 3.14, y mypy (obligatorio). `pyproject.toml` configura `--cov=pypex --cov-report=term-missing` por defecto.

### Estructura de Tests

```
tests/
├── conftest.py             # Restaura el MetricsRegistry global
└── unit/
    ├── core/
    ├── metrics/<categoría>/
    ├── parser/
    ├── reporters/
    └── services/
```

### Ejecutar Tests

```bash
# Ejecutar todos los tests
uv run pytest

# Tests con cobertura
uv run pytest --cov-report=html

# Tests específicos
uv run pytest tests/unit/metrics/complexity/

# Tests verbose
uv run pytest -v

# Tests con output detallado
uv run pytest -s
```

### Herramientas de Calidad

```bash
# Linting (incluye orden de imports)
uv run ruff check .

# Formateo
uv run ruff format .

# Type checking con mypy
uv run mypy pypex/

# Ejecutar todas las validaciones
uv run pre-commit run --all-files
```

### Métricas de Calidad del Código

- **Linting y formateo**: Ruff
- **Tipos**: mypy debe pasar (check obligatorio en CI y hook de pre-commit)
- **Líneas de código**: ~36 500 líneas de Python (código + tests)

---

## 🤝 Contribuir

¡Las contribuciones son bienvenidas! PyPex es un proyecto de **código abierto** desarrollado como TFG.

### Cómo Contribuir

1. **Fork** el repositorio
2. **Crear** una rama para tu feature (`git checkout -b feature/nueva-metrica`)
3. **Desarrollar** siguiendo las convenciones del proyecto
4. **Añadir tests** para tu código
5. **Ejecutar** la suite de tests y validaciones
6. **Commit** con mensajes descriptivos
7. **Push** a tu rama (`git push origin feature/nueva-metrica`)
8. **Crear** un Pull Request

### Guías de Desarrollo

#### Añadir Nueva Métrica

```python
from pypex.metrics.base import BaseMetric
from pypex.metrics.registry import get_registry
from pypex.parser.code_entities import Function


class MiMetrica(BaseMetric):
    def __init__(self) -> None:
        super().__init__("mi_metrica", "Descripción de mi métrica")

    def calculate_function(self, function: Function) -> float:
        return float(len(function.parameters))

    def get_default_thresholds(self) -> dict[str, float]:
        return {"low": 3.0, "medium": 5.0, "high": 7.0}


get_registry().register_metric(MiMetrica())
```

#### Estructura de Commits

```
Add complexity metric ABC
Fix LCOM4 cohesion calculation
Update metric documentation
Add tests for fan-in/fan-out
Refactor the registry
```

#### Code Style

- **Python**: PEP 8 + Ruff formatter
- **Docstrings**: Google style
- **Tipos**: mypy debe pasar (check obligatorio en CI y hook de pre-commit)
- **Tests**: Para toda nueva funcionalidad
- **Logging**: Para debugging y errores

### Roadmap
#### v1.0.0
- [ ] Plugin system para métricas custom
- [ ] Integración con IDEs (VS Code, PyCharm)
- [ ] Cobertura de tests >85%

---

## 📞 Soporte y Contacto

### Desarrollador Principal

**Alejandro Penalba Tarrida**
- 🎓 TFG - Universidad de Barcelona
- 💼 LinkedIn: [linkedin.com/in/apentar](https://www.linkedin.com/in/apentar/)

### Reportar Bugs

Al reportar bugs, incluye:
- Versión de PyPex y Python
- Comando ejecutado completo
- Salida de error completa
- Código de ejemplo (si aplica)
- Sistema operativo

---

## 📄 Licencia

Este proyecto está licenciado bajo la **Licencia MIT** - ver el archivo [LICENSE](LICENSE) para detalles.

```
MIT License

Copyright (c) 2025 Alejandro Penalba Tarrida

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
```

<div align="center">

[⬆️ Volver al inicio](#-pypex-analizador-integral-de-métricas-y-calidad-de-código-python)

</div>
