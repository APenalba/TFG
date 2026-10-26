"""Generador de documentación para métricas implementadas en PyPex."""

from typing import Any

from pypex.metrics import get_registry


class MetricsDocumentationGenerator:
    """Genera documentación HTML para todas las métricas implementadas."""

    def __init__(self):
        self.registry = get_registry()

    def generate_metrics_documentation(self) -> str:
        """Genera la documentación completa de métricas."""
        # Organizar métricas por categorías
        metrics_by_category = self._organize_metrics_by_category()

        # Generar tabla de contenidos
        toc = self._generate_table_of_contents(metrics_by_category)

        # Generar contenido de cada categoría
        content_sections = []
        for category, metrics in metrics_by_category.items():
            content_sections.append(self._generate_category_section(category, metrics))

        return f"""
        <div class='card metrics-documentation' id='metrics-docs'>
            <h2>📚 Documentación de Métricas</h2>
            <div class='metrics-intro'>
                <p>PyPex implementa <strong>{len(self.registry.get_all_metrics_instances())} métricas</strong> organizadas en {len(metrics_by_category)} categorías principales.
                Cada métrica incluye fundamentación teórica, interpretación de valores y ejemplos prácticos.</p>
            </div>

            <div class='metrics-toc'>
                <h3>📋 Índice de Métricas</h3>
                {toc}
            </div>

            <div class='metrics-content'>
                {"".join(content_sections)}
            </div>
        </div>
        """

    def _organize_metrics_by_category(self) -> dict[str, list[Any]]:
        """Organiza las métricas por categorías."""
        categories = {
            "🧮 Complejidad": [],
            "📏 Tamaño": [],
            "🔗 Acoplamiento": [],
            "🎯 Cohesión": [],
            "🏗️ Diseño": [],
        }

        metrics = self.registry.get_all_metrics_instances()

        for metric in metrics:
            # Determinar categoría basada en el nombre de la métrica
            if any(
                word in metric.name
                for word in [
                    "complexity",
                    "cyclomatic",
                    "cognitive",
                    "halstead",
                    "logical",
                    "essential",
                    "nesting",
                    "generator",
                    "exception",
                    "comprehension",
                ]
            ):
                categories["🧮 Complejidad"].append(metric)
            elif any(word in metric.name for word in ["lines_of_code", "parameter_count"]):
                categories["📏 Tamaño"].append(metric)
            elif any(
                word in metric.name for word in ["coupling", "fan_in_out", "advanced_coupling"]
            ):
                categories["🔗 Acoplamiento"].append(metric)
            elif any(word in metric.name for word in ["cohesion", "lcom"]):
                categories["🎯 Cohesión"].append(metric)
            elif any(word in metric.name for word in ["design"]):
                categories["🏗️ Diseño"].append(metric)

        # Filtrar categorías vacías
        return {k: v for k, v in categories.items() if v}

    def _generate_table_of_contents(self, metrics_by_category: dict[str, list[Any]]) -> str:
        """Genera tabla de contenidos."""
        toc_items = []

        for category, metrics in metrics_by_category.items():
            category_id = self._sanitize_id(category)
            toc_items.append(f"""
                <div class='toc-category'>
                    <h4><a href="#category-{category_id}">{category} ({len(metrics)})</a></h4>
                    <ul class='toc-metrics'>
                        {"".join(f'<li><a href="#metric-{metric.name}">{self._get_metric_display_name(metric)}</a></li>' for metric in metrics)}
                    </ul>
                </div>
            """)

        return f"<div class='metrics-toc-content'>{''.join(toc_items)}</div>"

    def _generate_category_section(self, category: str, metrics: list[Any]) -> str:
        """Genera sección de una categoría."""
        category_id = self._sanitize_id(category)
        metrics_html = []

        for metric in metrics:
            metrics_html.append(self._generate_metric_documentation(metric))

        return f"""
        <details class='metrics-category' id='category-{category_id}' open>
            <summary class='category-title'>
                <span class='category-title-content'>{category}</span>
                <span class='category-toggle-icon'>▼</span>
            </summary>
            <div class='category-content'>
                <div class='category-description'>
                    {self._get_category_description(category)}
                </div>
                <div class='category-metrics'>
                    {"".join(metrics_html)}
                </div>
            </div>
        </details>
        """

    def _generate_metric_documentation(self, metric) -> str:
        """Genera documentación completa de una métrica."""
        # Extraer información de la métrica
        display_name = self._get_metric_display_name(metric)
        description = getattr(metric, "description", "Sin descripción disponible")

        # Obtener docstring del método calculate_function para extraer documentación
        doc_content = self._extract_metric_documentation(metric)

        # Generar ejemplos
        examples = self._generate_metric_examples(metric)

        # Obtener umbrales
        thresholds = self._get_metric_thresholds(metric)

        return f"""
        <details class='metric-card' id='metric-{metric.name}'>
            <summary class='metric-header'>
                <span class='metric-title'>{display_name}</span>
                <span class='metric-id'>({metric.name})</span>
                <span class='metric-toggle-icon'>▼</span>
            </summary>

            <div class='metric-content'>
                <div class='metric-description'>
                    <p><strong>Descripción:</strong> {description}</p>
                </div>

                {doc_content}

                <div class='metric-thresholds'>
                    <h5>🎯 Umbrales de Interpretación</h5>
                    {thresholds}
                </div>

                <div class='metric-examples'>
                    <h5>💡 Ejemplos</h5>
                    {examples}
                </div>
            </div>
        </details>
        """

    def _extract_metric_documentation(self, metric) -> str:
        """Extrae documentación del docstring de la métrica."""
        # Intentar obtener docstring de la clase
        doc = getattr(metric.__class__, "__doc__", "")

        if not doc:
            return "<p><em>Documentación no disponible</em></p>"

        # Procesar el docstring para extraer secciones relevantes
        sections = self._parse_docstring_sections(doc)

        html_sections = []

        # Renderizar secciones importantes
        if "¿Qué es" in sections or "¿Qué son" in sections:
            key = "¿Qué es" if "¿Qué es" in sections else "¿Qué son"
            html_sections.append(f"""
                <div class='doc-section'>
                    <h5>❓ {key}</h5>
                    <div class='doc-content'>{self._format_doc_text(sections[key])}</div>
                </div>
            """)

        if "¿Cómo se calcula?" in sections:
            html_sections.append(f"""
                <div class='doc-section'>
                    <h5>🔢 Cálculo</h5>
                    <div class='doc-content'>{self._format_doc_text(sections["¿Cómo se calcula?"])}</div>
                </div>
            """)

        if "¿Cuándo se aplica?" in sections:
            html_sections.append(f"""
                <div class='doc-section'>
                    <h5>🎯 Aplicabilidad</h5>
                    <div class='doc-content'>{self._format_doc_text(sections["¿Cuándo se aplica?"])}</div>
                </div>
            """)

        return (
            "".join(html_sections)
            if html_sections
            else "<p><em>Documentación estructurada no disponible</em></p>"
        )

    def _parse_docstring_sections(self, doc: str) -> dict[str, str]:
        """Parsea un docstring en secciones."""
        sections = {}
        current_section = None
        current_content = []

        lines = doc.split("\n")

        for line in lines:
            stripped = line.strip()

            # Detectar nuevas secciones
            if stripped.startswith("##") and stripped.endswith("?"):
                # Guardar sección anterior
                if current_section and current_content:
                    sections[current_section] = "\n".join(current_content).strip()

                # Iniciar nueva sección
                current_section = stripped.replace("##", "").strip()
                current_content = []
            elif current_section:
                # Si estamos en una sección y encontramos otra que empieza con ##
                if stripped.startswith("##") and not stripped.endswith("?"):
                    # Terminar sección actual
                    if current_content:
                        sections[current_section] = "\n".join(current_content).strip()
                    current_section = None
                    current_content = []
                else:
                    current_content.append(line)

        # Guardar última sección
        if current_section and current_content:
            sections[current_section] = "\n".join(current_content).strip()

        return sections

    def _format_doc_text(self, text: str) -> str:
        """Formatea texto de documentación a HTML."""
        if not text:
            return ""

        # Reemplazar markdown básico
        formatted = text

        # Listas con **
        formatted = formatted.replace("**", "<strong>").replace("**", "</strong>")

        # Código inline con `
        import re

        formatted = re.sub(r"`([^`]+)`", r"<code>\1</code>", formatted)

        # Convertir líneas a párrafos
        paragraphs = []
        current_para = []

        for line in formatted.split("\n"):
            stripped = line.strip()
            if not stripped:
                if current_para:
                    paragraphs.append("<p>" + " ".join(current_para) + "</p>")
                    current_para = []
            elif stripped.startswith("-") or stripped.startswith("*"):
                # Lista
                if current_para:
                    paragraphs.append("<p>" + " ".join(current_para) + "</p>")
                    current_para = []
                paragraphs.append("<li>" + stripped[1:].strip() + "</li>")
            else:
                current_para.append(stripped)

        if current_para:
            paragraphs.append("<p>" + " ".join(current_para) + "</p>")

        # Envolver listas
        html = "".join(paragraphs)
        html = re.sub(r"(<li>.*?</li>)", r"<ul>\1</ul>", html, flags=re.DOTALL)

        return html

    def _generate_metric_examples(self, metric) -> str:
        """Genera ejemplos específicos para cada métrica."""
        examples = {
            "cyclomatic_complexity": {
                "simple": {
                    "code": """def simple_function(x):
    if x > 0:
        return x * 2
    return 0""",
                    "score": 2,
                    "explanation": "Una decisión (if) = complejidad 2",
                },
                "complex": {
                    "code": """def complex_function(x, y, z):
    if x > 0 and y > 0:  # +2 (if + and)
        for i in range(z):  # +1 (for)
            if i % 2 == 0:  # +1 (if)
                try:        # +0 (try)
                    result = x / i
                except ZeroDivisionError:  # +1 (except)
                    continue
        return result
    elif x < 0:  # +1 (elif)
        return -1
    return 0""",
                    "score": 6,
                    "explanation": "Múltiples decisiones y estructuras de control",
                },
            },
            "cognitive_complexity": {
                "simple": {
                    "code": """def calculate_discount(price, is_member):
    if is_member:  # +1
        return price * 0.9
    return price""",
                    "score": 1,
                    "explanation": "Una estructura de decisión simple",
                },
                "complex": {
                    "code": """def process_data(items):
    for item in items:  # +1
        if item.is_valid:  # +2 (nested)
            if item.category == 'special':  # +3 (nested)
                for attr in item.attributes:  # +4 (nested)
                    if attr.needs_processing:  # +5 (nested)
                        process_attribute(attr)""",
                    "score": 15,
                    "explanation": "Anidamiento profundo aumenta exponencialmente la complejidad cognitiva",
                },
            },
            "lines_of_code": {
                "small": {
                    "code": '''def add(a, b):
    """Suma dos números."""
    return a + b''',
                    "score": 1,
                    "explanation": "Función pequeña: 1 SLOC",
                },
                "medium": {
                    "code": '''def validate_user(user_data):
    """Valida datos de usuario."""
    if not user_data:
        raise ValueError("Datos requeridos")

    if len(user_data.get('name', '')) < 2:
        raise ValueError("Nombre muy corto")

    if '@' not in user_data.get('email', ''):
        raise ValueError("Email inválido")

    return True''',
                    "score": 8,
                    "explanation": "Función mediana: 8 SLOC",
                },
            },
            "halstead": {
                "simple": {
                    "code": """def multiply(a, b):
    return a * b""",
                    "score": "V=15.5, D=1.5, E=23.3",
                    "explanation": "Pocos operadores y operandos = bajo volumen y dificultad",
                },
                "complex": {
                    "code": """def fibonacci(n):
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    else:
        return fibonacci(n-1) + fibonacci(n-2)""",
                    "score": "V=78.2, D=4.5, E=351.9",
                    "explanation": "Más operadores/operandos y recursión = mayor volumen y dificultad",
                },
            },
        }

        metric_examples = examples.get(metric.name, {})

        if not metric_examples:
            return "<p><em>Ejemplos no disponibles para esta métrica</em></p>"

        html_examples = []
        for example_type, example_data in metric_examples.items():
            html_examples.append(f"""
                <div class='example-item'>
                    <h6>📝 Ejemplo {example_type.title()}</h6>
                    <pre><code class='python'>{example_data["code"]}</code></pre>
                    <div class='example-result'>
                        <strong>Resultado:</strong> {example_data["score"]}<br>
                        <strong>Explicación:</strong> {example_data["explanation"]}
                    </div>
                </div>
            """)

        return "".join(html_examples)

    def _get_metric_thresholds(self, metric) -> str:
        """Obtiene y formatea los umbrales de una métrica."""
        try:
            thresholds = metric.get_default_thresholds()

            threshold_items = []

            # Determinar rangos basados en umbrales
            low = thresholds.get("low", 0)
            medium = thresholds.get("medium", 0)
            high = thresholds.get("high", 0)

            threshold_items.append(f"""
                <div class='threshold-item excellent'>
                    <span class='threshold-range'>≤ {low}</span>
                    <span class='threshold-label'>Excelente</span>
                </div>
            """)

            threshold_items.append(f"""
                <div class='threshold-item good'>
                    <span class='threshold-range'>{low + 0.1:.1f} - {medium}</span>
                    <span class='threshold-label'>Bueno</span>
                </div>
            """)

            threshold_items.append(f"""
                <div class='threshold-item warning'>
                    <span class='threshold-range'>{medium + 0.1:.1f} - {high}</span>
                    <span class='threshold-label'>Precaución</span>
                </div>
            """)

            threshold_items.append(f"""
                <div class='threshold-item critical'>
                    <span class='threshold-range'>&gt; {high}</span>
                    <span class='threshold-label'>Crítico</span>
                </div>
            """)

            return f"<div class='thresholds-grid'>{''.join(threshold_items)}</div>"

        except Exception:
            return "<p><em>Umbrales no disponibles</em></p>"

    def _get_category_description(self, category: str) -> str:
        """Obtiene descripción de una categoría."""
        descriptions = {
            "🧮 Complejidad": "Las métricas de complejidad miden qué tan difícil es entender, mantener y probar el código. Incluyen análisis de estructuras de control, anidamiento y patrones algorítmicos.",
            "📏 Tamaño": "Las métricas de tamaño evalúan la magnitud del código en términos de líneas, parámetros y elementos estructurales. Son indicadores básicos pero fundamentales de la escala del software.",
            "🔗 Acoplamiento": "Las métricas de acoplamiento miden las dependencias entre componentes. Alto acoplamiento dificulta el mantenimiento y testing, mientras que bajo acoplamiento mejora la modularidad.",
            "🎯 Cohesión": "Las métricas de cohesión evalúan qué tan bien relacionados están los elementos dentro de un módulo o clase. Alta cohesión indica responsabilidades bien definidas.",
            "🏗️ Diseño": "Las métricas de diseño analizan la calidad arquitectónica y los patrones de diseño orientado a objetos utilizados en el código.",
        }

        return f"<p>{descriptions.get(category, 'Descripción no disponible')}</p>"

    def _get_metric_display_name(self, metric) -> str:
        """Convierte el nombre técnico a un nombre legible."""
        display_names = {
            "cyclomatic_complexity": "Complejidad Ciclomática",
            "cognitive_complexity": "Complejidad Cognitiva",
            "halstead": "Métricas de Halstead",
            "logical_complexity": "Complejidad Lógica",
            "essential_complexity": "Complejidad Esencial",
            "nesting_depth": "Profundidad de Anidamiento",
            "generator_complexity": "Complejidad de Generadores",
            "exception_handling_complexity": "Complejidad de Manejo de Excepciones",
            "comprehension_complexity": "Complejidad de Comprensiones",
            "nested_comprehension_depth": "Profundidad de Comprensiones Anidadas",
            "lines_of_code": "Líneas de Código",
            "parameter_count": "Conteo de Parámetros",
            "fan_in_out": "Fan-In/Fan-Out",
            "advanced_coupling": "Acoplamiento Avanzado",
            "lcom4": "LCOM4 (Cohesión)",
            "design_complexity": "Complejidad de Diseño",
        }

        return display_names.get(metric.name, metric.name.replace("_", " ").title())

    def _sanitize_id(self, text: str) -> str:
        """Convierte texto a ID válido para HTML."""
        import re

        # Remover emojis y caracteres especiales
        sanitized = re.sub(r"[^\w\s-]", "", text)
        # Reemplazar espacios con guiones
        sanitized = re.sub(r"\s+", "-", sanitized.strip())
        return sanitized.lower()
