# 🐍 PyPex: Analizador Integral de Métricas y Calidad de Código Python

<div align="center">

[![Python Version](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Development Status](https://img.shields.io/badge/status-alpha-orange.svg)](https://github.com/APenalba/TFG)
[![Code Quality](https://img.shields.io/badge/code%20quality-A-green.svg)](https://github.com/APenalba/TFG)

**Analizador profesional de métricas de calidad, complejidad, cohesión y mantenibilidad para proyectos Python**

[📊 Ver Reporte PyPex del Proyecto](https://apenalba.github.io/TFG)

[🚀 Instalación](#-instalación) • [📊 Características](#-características) • [🎯 Uso Rápido](#-uso-rápido) • [📖 Documentación](#-documentación) • [🤝 Contribuir](#-contribuir)

</div>

---

## 📋 Tabla de Contenidos

- [🔍 ¿Qué es PyPex?](#-qué-es-pypex)
- [📊 Características Principales](#-características-principales)
- [🚀 Instalación](#-instalación)
- [🎯 Uso Rápido](#-uso-rápido)
- [📈 Métricas Disponibles](#-métricas-disponibles)
- [🖥️ Comandos CLI](#️-comandos-cli)
- [⚙️ Configuración](#️-configuración)
- [📊 Formatos de Salida](#-formatos-de-salida)
- [🎚️ Perfiles de Umbrales](#️-perfiles-de-umbrales)
- [🏗️ Arquitectura](#️-arquitectura)
- [🧪 Testing](#-testing)
- [🤝 Contribuir](#-contribuir)
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
- **Métricas de Proyecto**: Distribución de complejidad, patrones arquitectónicos

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
- **Archivos de configuración** YAML
- **Perfiles de umbrales** (strict/normal/permissive)
- **Filtros avanzados** para archivos y directorios
- **Métricas selectivas** - incluir/excluir específicas

### 🎯 **Fácil Integración**
- **CLI simple** con comandos intuitivos
- **Configuración por argumentos** o archivos
- **Logging detallado** para debugging
- **API programática** para integraciones custom

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
python -m pypex --help

# O usar el script ejecutable
python pypex.py --help
```

---

## 🎯 Uso Rápido

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

| Métrica | Descripción | Valores Típicos |
|---------|-------------|-----------------|
| **Complejidad Ciclomática** | Número de caminos de ejecución linealmente independientes | 1-10 (bueno), >20 (problemático) |
| **Complejidad Cognitiva** | Dificultad mental para entender el código | 1-15 (bueno), >25 (problemático) |
| **Profundidad de Anidamiento** | Niveles máximos de estructuras anidadas | 1-4 (bueno), >6 (problemático) |
| **Complejidad Esencial** | Complejidad irreducible después de transformaciones | <3 (ideal), >5 (problemático) |
| **Complejidad Lógica** | Complejidad de expresiones booleanas | <5 (bueno), >10 (problemático) |

### 🐍 **Específicas de Python**

| Métrica | Descripción | Aplicación |
|---------|-------------|------------|
| **Complejidad de Comprensiones** | Complejidad de list/dict/set comprehensions | Código funcional Python |
| **Profundidad de Comprensiones Anidadas** | Nivel de anidamiento en comprehensions | Expresiones complejas |
| **Complejidad de Manejo de Excepciones** | Análisis de bloques try/except/finally | Robustez del código |
| **Complejidad de Generadores** | Análisis de funciones con yield | Código asíncrono |

### 📏 **Métricas de Tamaño**

| Métrica | Descripción | Componentes |
|---------|-------------|-------------|
| **Líneas de Código** | LOC físicas, lógicas, comentarios, documentación | SLOC, LLOC, CLOC, DLOC |
| **Conteo de Parámetros** | Número de parámetros en funciones/métodos | Parámetros totales, opcionales |

### 🔗 **Acoplamiento y Cohesión**

| Métrica | Descripción | Nivel |
|---------|-------------|-------|
| **Fan-In/Fan-Out** | Dependencias entre componentes | Módulo/Clase |
| **LCOM4** | Falta de cohesión en métodos (Lack of Cohesion) | Clase |
| **Acoplamiento Avanzado** | Análisis profundo de dependencias | Proyecto |

### 🏗️ **Calidad de Diseño**

| Métrica | Descripción | Enfoque |
|---------|-------------|---------|
| **Complejidad de Diseño** | Complejidad de las interacciones entre módulos | Arquitectura |
| **Métricas de Halstead** | Volumen, dificultad, esfuerzo de programación | Análisis léxico |

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
| `--verbose` | Activar modo verboso | Todos los comandos |
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

# Formato de salida por defecto
output_format: "text"

# Tamaño máximo de archivo a procesar (en bytes)
max_file_size: 1048576  # 1MB

# Perfil de umbrales para interpretación de métricas
thresholds_profile: "normal"  # strict, normal, permissive

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

### Perfiles Predefinidos

#### 🔴 **Perfil Estricto** (Código de Alta Calidad)
```yaml
thresholds_profile: "strict"
metrics:
  - "cyclomatic_complexity"
  - "cognitive_complexity"
  - "nesting_depth"
  - "parameter_count"
  - "lines_of_code"
```

#### 🟡 **Perfil Legacy** (Código Existente)
```yaml
thresholds_profile: "permissive"
exclude_metrics:
  - "essential_complexity"
  - "logical_complexity"
  - "design_complexity"
```

#### 🟢 **Perfil Arquitectónico** (Análisis de Diseño)
```yaml
metrics:
  - "fan_in_out"
  - "lcom4"
  - "design_complexity"
  - "lines_of_code"
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
```
✅ Análisis completado: 15 archivos, 42 funciones
📊 Promedio de complejidad: 3.2 (BUENO)
🔴 Hot spots encontrados: 3
```

#### `--verbosity normal` *(por defecto)*
```
🐍 PyPex v0.1.0 - Análisis de Complejidad

📁 Proyecto: ./mi_proyecto (15 archivos Python)
⏱️  Tiempo de análisis: 2.3s

📊 RESUMEN DE MÉTRICAS
┌─────────────────────────┬─────────┬─────────┬─────────┬──────────┐
│ Métrica                 │ Promedio│ Máximo  │ Hot Spots│ Estado   │
├─────────────────────────┼─────────┼─────────┼─────────┼──────────┤
│ Complejidad Ciclomática │ 3.2     │ 15      │ 3       │ 🟡 MEDIO │
│ Complejidad Cognitiva   │ 4.1     │ 18      │ 2       │ 🟢 BUENO │
│ Profundidad Anidamiento │ 2.8     │ 6       │ 1       │ 🟢 BUENO │
└─────────────────────────┴─────────┴─────────┴─────────┴──────────┘

🔥 HOT SPOTS (Complejidad Alta)
• src/analyzer.py:process_complex_data() - CC:15, CN:18
• src/utils.py:validate_config() - CC:12, CN:14
• src/main.py:main() - CC:11, CN:12
```

#### `--verbosity verbose`
```
# Incluye análisis detallado por archivo con:
• Métricas individuales por función/clase
• Recomendaciones específicas de refactoring
• Distribución de complejidad por módulo
• Análisis de tendencias y patrones
```

#### `--verbosity debug`
```
# Incluye información técnica completa:
• Configuración utilizada
• Tiempos de procesamiento por archivo
• Estadísticas de memoria
• Warnings y errores detallados
```

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

Datos estructurados para integración con herramientas externas:

```json
{
  "metadata": {
    "pypex_version": "0.1.0",
    "analysis_date": "2024-01-15T10:30:00Z",
    "project_path": "./mi_proyecto",
    "total_files": 15,
    "total_functions": 42,
    "total_classes": 8,
    "analysis_duration_seconds": 2.3
  },
  "configuration": {
    "thresholds_profile": "normal",
    "metrics_used": ["cyclomatic_complexity", "cognitive_complexity"],
    "ignored_patterns": ["test_*.py"]
  },
  "project_summary": {
    "cyclomatic_complexity": {
      "mean": 3.2,
      "median": 2.5,
      "max": 15,
      "min": 1,
      "std_dev": 2.8,
      "hot_spots_count": 3
    }
  },
  "files": [
    {
      "path": "src/analyzer.py",
      "metrics": {
        "cyclomatic_complexity": 8.5,
        "cognitive_complexity": 12.3
      },
      "functions": [
        {
          "name": "process_data",
          "line_start": 45,
          "metrics": {
            "cyclomatic_complexity": 15,
            "cognitive_complexity": 18
          }
        }
      ]
    }
  ]
}
```

**Casos de uso del formato JSON:**
- **CI/CD**: Integración con pipelines
- **Análisis histórico**: Seguimiento de evolución
- **Dashboards**: Herramientas de monitoring
- **Investigación**: Análisis estadístico

---

## 🎚️ Perfiles de Umbrales

PyPex incluye **3 perfiles predefinidos** para interpretar las métricas según el contexto del proyecto:

### 🔴 **Strict** - Código de Alta Calidad

Para proyectos que requieren **máxima calidad**:
- Bibliotecas públicas
- Código crítico de seguridad
- Sistemas de alta disponibilidad

| Métrica | Bajo | Medio | Alto |
|---------|------|-------|------|
| Complejidad Ciclomática | ≤3 | 4-6 | >6 |
| Complejidad Cognitiva | ≤5 | 6-10 | >10 |
| Profundidad Anidamiento | ≤2 | 3-4 | >4 |
| Parámetros por Función | ≤3 | 4-5 | >5 |

### 🟡 **Normal** - Proyectos Típicos *(por defecto)*

Para la **mayoría de proyectos**:
- Aplicaciones empresariales
- Scripts de automatización
- Proyectos de desarrollo ágil

| Métrica | Bajo | Medio | Alto |
|---------|------|-------|------|
| Complejidad Ciclomática | ≤6 | 7-15 | >15 |
| Complejidad Cognitiva | ≤10 | 11-25 | >25 |
| Profundidad Anidamiento | ≤4 | 5-6 | >6 |
| Parámetros por Función | ≤5 | 6-8 | >8 |

### 🟢 **Permissive** - Código Legacy

Para **código existente** o en transición:
- Sistemas legacy
- Prototipos rápidos
- Migración de código

| Métrica | Bajo | Medio | Alto |
|---------|------|-------|------|
| Complejidad Ciclomática | ≤10 | 11-25 | >25 |
| Complejidad Cognitiva | ≤15 | 16-40 | >40 |
| Profundidad Anidamiento | ≤6 | 7-8 | >8 |
| Parámetros por Función | ≤8 | 9-12 | >12 |

### Usar Perfiles

```bash
# Aplicar perfil estricto
pypex analyze --thresholds-profile strict ./src

# Ver umbrales configurados
pypex thresholds
```

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
│   ├── size/                # Métricas de tamaño
│   └── project/             # Métricas de proyecto
│
├── reporters/               # 📄 Sistema de reportes
│   ├── console_reporter.py  # Salida en consola
│   ├── json_reporter.py     # Exportación JSON
│   └── html/                # Reportes HTML
│       ├── html_reporter.py
│       ├── html_renderer.py
│       ├── html_styles.py
│       └── html_scripts.py
│
├── services/                # 🔧 Servicios transversales
│   ├── config_service.py    # Gestión de configuración
│   └── logging_service.py   # Sistema de logging
│
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

- **Singleton**: Registry de métricas
- **Strategy**: Diferentes formatos de reporte
- **Visitor**: Recorrido de AST
- **Factory**: Creación de métricas
- **Observer**: Sistema de logging

---

## 🧪 Testing

PyPex incluye una **suite completa de tests** para garantizar calidad y robustez:

### Estadísticas Actuales del Proyecto

- **📊 Tests**: 861 tests totales (799 pasados, 62 en desarrollo)
- **📈 Coverage**: 49% de cobertura de código
- **📁 Archivos**: 59 archivos de código fuente
- **📝 Líneas de código**: +21,000 líneas de código fuente
- **🔢 Total proyecto**: +37,000 líneas (código + tests)

### Estructura de Tests

```
tests/
├── unit/                    # Tests unitarios
│   ├── core/                # Tests de componentes core
│   ├── metrics/             # Tests de métricas individuales
│   │   ├── complexity/      # Tests de métricas de complejidad
│   │   ├── coupling/        # Tests de acoplamiento
│   │   ├── cohesion/        # Tests de cohesión
│   │   ├── design/          # Tests de diseño
│   │   └── size/            # Tests de tamaño
│   ├── parser/              # Tests del parser
│   ├── services/            # Tests de servicios
│   ├── test_cli.py          # Tests de CLI
│   └── test_main.py         # Tests principales
│
└── integration/             # Tests de integración
    └── test_full_analysis.py # Tests end-to-end
```

### Ejecutar Tests

```bash
# Ejecutar todos los tests
pytest

# Tests con cobertura
pytest --cov=pypex --cov-report=term-missing --cov-report=html

# Tests específicos
pytest tests/unit/metrics/complexity/

# Tests verbose
pytest -v

# Tests con output detallado
pytest -s
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

- **Cobertura de código**: 49% (en crecimiento constante)
- **Tests totales**: 861 tests implementados
- **Linting y formateo**: Ruff
- **Type hints**: Mypy
- **Líneas de código**: +37,000 líneas totales (código + tests)

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
# pypex/metrics/complexity/mi_metrica.py
from pypex.metrics.base import IMetric
from pypex.parser.code_entities import CodeEntity


class MiMetrica(IMetric):
    @property
    def name(self) -> str:
        return "mi_metrica"

    @property
    def description(self) -> str:
        return "Descripción de mi métrica"

    def calculate(self, entity: CodeEntity) -> float:
        # Implementar cálculo
        return 0.0
```

#### Estructura de Commits

```
feat: añadir métrica de complejidad ABC
fix: corregir cálculo de cohesión LCOM4
docs: actualizar documentación de métricas
test: añadir tests para fan-in/fan-out
refactor: mejorar estructura del registry
```

#### Code Style

- **Python**: PEP 8 + Ruff formatter
- **Docstrings**: Google style
- **Type hints**: Obligatorios
- **Tests**: Para toda nueva funcionalidad
- **Logging**: Para debugging y errores

### Roadmap
#### v1.0.0
- [ ] Plugin system para métricas custom
- [ ] Integración con IDEs (VS Code, PyCharm)
- [ ] Soporte para configuración JSON
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

Copyright (c) 2024 Alejandro Penalba Tarrida

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

[⬆️ Volver al inicio](#-pypex-analizador-avanzado-de-complejidad-de-código-python)

</div>
