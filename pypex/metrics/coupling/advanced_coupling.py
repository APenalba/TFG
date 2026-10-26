"""Módulo para calcular métricas de acoplamiento avanzadas."""

from pypex.metrics.base import BaseMetric
from pypex.parser.code_entities import (
    Class,
    CodeEntity,
    Function,
    Module,
    Project,
)
from pypex.services.logging_service import get_logger

logger = get_logger(__name__)


class AdvancedCouplingMetric(BaseMetric):
    """Calcula métricas de acoplamiento avanzadas para clases y módulos.

    ## ¿Qué son las métricas de acoplamiento avanzadas?

    Las métricas de acoplamiento avanzadas son un conjunto de métricas que evalúan
    las interdependencias entre componentes de software a diferentes niveles de
    granularidad. Fueron desarrolladas por Chidamber & Kemerer (1994) y Martin (1994)
    como parte de las métricas de calidad de software orientado a objetos.

    ## Métricas para CLASES:

    ### 1. Coupling Between Objects (CBO):
    **CBO = Número de clases de las que esta clase depende**
    - Incluye herencia (base_classes)
    - Incluye composición y agregación (referencias a otras clases)
    - Incluye uso de tipos en parámetros y variables
    - **No incluye** clases del sistema/bibliotecas estándar

    ### 2. Response for Class (RFC):
    **RFC = Número de métodos que pueden ser ejecutados en respuesta a un mensaje**
    - RFC = Métodos propios + Métodos llamados externamente
    - Incluye métodos definidos en la clase
    - Incluye métodos externos que la clase puede invocar
    - Mide la complejidad de testing de la clase

    ### 3. Message Passing Coupling (MPC):
    **MPC = Número de llamadas a métodos externos**
    - Cuenta llamadas a métodos de otras clases
    - No incluye llamadas a métodos de la misma clase
    - Mide el acoplamiento dinámico entre objetos

    ## Métricas para MÓDULOS:

    ### 4. Afferent Coupling (Ca):
    **Ca = Número de módulos que dependen de este módulo**
    - Módulos que importan este módulo
    - Mide la responsabilidad del módulo
    - Alto Ca = módulo central, muchos dependientes

    ### 5. Efferent Coupling (Ce):
    **Ce = Número de módulos de los que depende este módulo**
    - Módulos que este módulo importa
    - Mide las dependencias salientes del módulo
    - Alto Ce = módulo con muchas dependencias

    ### 6. Instability (I):
    **I = Ce / (Ca + Ce)**
    - Rango: [0, 1]
    - I = 0: Completamente estable (solo dependientes, sin dependencias)
    - I = 1: Completamente inestable (solo dependencias, sin dependientes)
    - I ≈ 0.5: Equilibrio entre estabilidad e inestabilidad

    ### 7. Abstractness (A):
    **A = Clases abstractas / Total de clases**
    - Rango: [0, 1]
    - A = 0: Completamente concreto
    - A = 1: Completamente abstracto
    - Mide el grado de abstracción del módulo

    ### 8. Distance from Main Sequence (D):
    **D = |A + I - 1|**
    - Rango: [0, 1]
    - D = 0: En la secuencia principal (equilibrio ideal)
    - D → 1: Alejado del equilibrio
    - Basado en principios de Robert C. Martin

    ## Interpretación de valores:

    ### CBO (Coupling Between Objects):
    - **0-5**: Acoplamiento bajo, diseño bien encapsulado
    - **6-10**: Acoplamiento moderado, aceptable
    - **11-20**: Acoplamiento alto, considerar refactoring
    - **>20**: Acoplamiento muy alto, violación de principios OOP

    ### RFC (Response for Class):
    - **0-20**: Complejidad baja, fácil de testear
    - **21-50**: Complejidad moderada
    - **51-100**: Complejidad alta, difícil de testear
    - **>100**: Complejidad muy alta, refactoring urgente

    ### MPC (Message Passing Coupling):
    - **0-5**: Acoplamiento dinámico bajo
    - **6-15**: Acoplamiento dinámico moderado
    - **16-30**: Acoplamiento dinámico alto
    - **>30**: Acoplamiento dinámico excesivo

    ### Ca (Afferent Coupling):
    - **0**: Módulo no utilizado (posible código muerto)
    - **1-3**: Uso moderado
    - **4-10**: Módulo importante, bien utilizado
    - **>10**: Módulo central crítico

    ### Ce (Efferent Coupling):
    - **0-3**: Pocas dependencias, módulo independiente
    - **4-8**: Dependencias moderadas
    - **9-15**: Muchas dependencias, considerar refactoring
    - **>15**: Dependencias excesivas, alto acoplamiento

    ### Instability (I):
    - **0.0-0.2**: Muy estable (ideal para bibliotecas base)
    - **0.2-0.4**: Estable (componentes de bajo nivel)
    - **0.4-0.6**: Equilibrado
    - **0.6-0.8**: Inestable (componentes de alto nivel)
    - **0.8-1.0**: Muy inestable (interfaces/abstracciones)

    ### Abstractness (A):
    - **0.0-0.2**: Muy concreto (implementaciones específicas)
    - **0.2-0.4**: Principalmente concreto
    - **0.4-0.6**: Equilibrado
    - **0.6-0.8**: Principalmente abstracto
    - **0.8-1.0**: Muy abstracto (interfaces/contratos)

    ### Distance from Main Sequence (D):
    - **0.0-0.1**: Excelente, en la secuencia principal
    - **0.1-0.2**: Bueno, cerca del equilibrio ideal
    - **0.2-0.4**: Aceptable, ligero desequilibrio
    - **0.4-0.7**: Problemático, alejado del equilibrio
    - **0.7-1.0**: Crítico, refactoring urgente necesario

    ## Zonas problemáticas en el gráfico A vs I:

    ### Zone of Pain (A≈0, I≈0):
    - **Módulos concretos y estables**
    - Difíciles de cambiar y extender
    - Pueden volverse legacy rápidamente

    ### Zone of Uselessness (A≈1, I≈1):
    - **Módulos abstractos e inestables**
    - Abstracciones sin uso
    - Código muerto potencial

    ### Main Sequence (A + I ≈ 1):
    - **Equilibrio ideal**
    - Estables y abstractos O inestables y concretos
    - Fáciles de mantener y extender

    ## ¿Cuándo se aplica?

    **❌ FUNCIONES**: No aplicable
    - Las métricas de acoplamiento avanzadas no tienen sentido a nivel de función
    - Usar métricas más simples como Fan-In/Fan-Out para funciones

    **✅ CLASES**: Aplicación principal (CBO, RFC, MPC)
    - Evaluación de diseño orientado a objetos
    - Identificación de clases problemáticas
    - Guía para refactoring de clases
    - Medición de testabilidad

    **✅ MÓDULOS**: Aplicación muy importante (Ca, Ce, I, A, D)
    - Análisis de arquitectura de software
    - Evaluación de dependencias entre módulos
    - Identificación de puntos críticos de cambio
    - Planificación de modularización

    **✅ PROYECTOS**: Aplicación agregada valiosa
    - Métricas de calidad arquitectónica general
    - Identificación de patrones problemáticos
    - Comparación entre proyectos
    - Tracking de evolución arquitectónica

    ## Beneficios de usar estas métricas:
    - **Calidad del diseño**: Evaluación objetiva de arquitectura OOP
    - **Mantenibilidad**: Identificación de código difícil de mantener
    - **Testabilidad**: Predicción de dificultad de testing
    - **Estabilidad**: Evaluación de robustez ante cambios
    - **Refactoring**: Guía para mejoras arquitectónicas
    - **Riesgo**: Identificación de componentes de alto riesgo

    ## Principios de diseño relacionados:
    - **SRP**: CBO y RFC altos pueden indicar múltiples responsabilidades
    - **OCP**: Abstractness y estabilidad facilitan extensibilidad
    - **LSP**: CBO ayuda a evaluar jerarquías de herencia
    - **ISP**: RFC alto puede indicar interfaces demasiado grandes
    - **DIP**: Abstractness mide adherencia a este principio

    ## Referencias:
    - Chidamber, S. R., & Kemerer, C. F. (1994). "A metrics suite for object oriented design"
    - Martin, R. C. (1994). "OO Design Quality Metrics: An Analysis of Dependencies"
    - ISO/IEC 25023:2016 Systems and software engineering
    - IEEE Standard 982.1-2005 for Software Engineering Metrics
    """

    def __init__(self):
        """Inicializa el calculador de métricas de acoplamiento avanzadas."""
        super().__init__(
            name="advanced_coupling",
            description="Calcula métricas de acoplamiento avanzadas: CBO, RFC, MPC para clases; Ca, Ce, Instability, Abstractness y Distance from Main Sequence para módulos.",
        )

    def get_default_thresholds(self) -> dict[str, float]:
        """Obtiene los umbrales por defecto para advanced_coupling.

        Basado en CBO (Coupling Between Objects).

        Returns:
            Dict[str, float]: Umbrales por defecto {low, medium, high}.
        """
        return {
            "low": 5.0,
            "medium": 10.0,
            "high": 20.0,
        }

    def calculate_function(self, function: Function) -> float | None:
        """Las métricas de acoplamiento avanzadas no se aplican a funciones individuales.

        Args:
            function: Función a analizar.

        Returns:
            None: Estas métricas no aplican a funciones.
        """
        logger.debug(f"Métricas de acoplamiento avanzadas no aplican a función: {function.name}")
        return None

    def calculate_class(self, cls: Class) -> dict[str, float] | None:
        """Calcula métricas de acoplamiento avanzadas para una clase (CBO, RFC, MPC).

        Args:
            cls: Clase a analizar.

        Returns:
            Optional[Dict[str, float]]: Métricas de acoplamiento de la clase.
        """
        logger.debug(f"Calculando acoplamiento avanzado para clase: {cls.name}")

        # CBO: Coupling Between Objects
        # Incluye herencia y referencias a otras clases
        cbo = len(cls.base_classes)  # Herencia directa

        # Contar referencias a otras clases en métodos
        external_classes = set()
        for method in cls.methods:
            # Análizar llamadas para encontrar referencias a clases externas
            for call in method.calls:
                # Simplificación: asumir que calls con '.' son llamadas a métodos de otras clases
                if "." in call and not call.startswith("self."):
                    class_name = call.split(".")[0]
                    external_classes.add(class_name)

        cbo += len(external_classes)

        # RFC: Response for Class
        # Métodos propios + métodos externos llamados
        own_methods = len(cls.methods)
        external_methods = set()

        for method in cls.methods:
            for call in method.calls:
                # Métodos externos (no de la misma clase)
                if "." in call and not call.startswith("self."):
                    external_methods.add(call)
                elif call not in [m.name for m in cls.methods]:
                    # Funciones globales o métodos no propios
                    external_methods.add(call)

        rfc = own_methods + len(external_methods)

        # MPC: Message Passing Coupling
        # Llamadas a métodos de otras clases/objetos
        mpc = 0
        for method in cls.methods:
            for call in method.calls:
                # Contar solo llamadas a métodos externos
                if "." in call and not call.startswith("self."):
                    mpc += 1

        return {
            "cbo": float(cbo),
            "rfc": float(rfc),
            "mpc": float(mpc),
            "inheritance_coupling": float(len(cls.base_classes)),
            "external_classes_used": float(len(external_classes)),
            "external_methods_called": float(len(external_methods)),
        }

    def calculate_module(self, module: Module) -> dict[str, float] | None:
        """Calcula métricas de acoplamiento avanzadas para un módulo (Ca, Ce, I, A, D).

        Nota: Para Ca (Afferent Coupling) se necesita información de todo el proyecto,
        por lo que esta implementación simplificada no puede calcularlo completamente.

        Args:
            module: Módulo a analizar.

        Returns:
            Optional[Dict[str, float]]: Métricas de acoplamiento del módulo.
        """
        logger.debug(f"Calculando acoplamiento avanzado para módulo: {module.name}")

        # Ce: Efferent Coupling - módulos que este módulo importa
        ce = len(module.imports)

        # Ca: Afferent Coupling - no se puede calcular sin contexto del proyecto
        # Se deja en 0 y se calculará en calculate_project
        ca = 0.0

        # Abstractness: clases abstractas / total de clases
        total_classes = len(module.classes)
        abstract_classes = sum(1 for cls in module.classes if cls.is_abstract_class)
        abstractness = 0.0
        if total_classes > 0:
            abstractness = abstract_classes / total_classes

        # Instability: Ce / (Ca + Ce)
        instability = 0.0
        if ca + ce > 0:
            instability = ce / (ca + ce)
        elif ce > 0:
            instability = 1.0  # Solo dependencias salientes

        # Distance from Main Sequence: |A + I - 1|
        distance = abs(abstractness + instability - 1.0)

        return {
            "ca": ca,  # Se actualizará en calculate_project
            "ce": float(ce),
            "instability": instability,
            "abstractness": abstractness,
            "distance_main_sequence": distance,
            "total_classes": float(total_classes),
            "abstract_classes": float(abstract_classes),
            "imports_count": float(len(module.imports)),
        }

    def calculate_project(self, project: Project) -> dict[str, float] | None:
        """Calcula métricas de acoplamiento avanzadas agregadas para un proyecto.

        Aquí se puede calcular correctamente Ca para cada módulo ya que tenemos
        información de todo el proyecto.

        Args:
            project: Proyecto a analizar.

        Returns:
            Optional[Dict[str, float]]: Métricas de acoplamiento agregadas del proyecto.
        """
        logger.debug(f"Calculando acoplamiento avanzado para proyecto: {project.name}")

        # Crear mapeo de nombres de módulos
        module_names = {module.name for module in project.modules}

        # Calcular Ca (Afferent Coupling) para cada módulo
        ca_counts = {}
        for module in project.modules:
            ca_counts[module.name] = 0

        # Contar dependencias entre módulos del proyecto
        for module in project.modules:
            for import_stmt in module.imports:
                imported_module = import_stmt.module
                # Si el módulo importado está en el proyecto
                if imported_module in module_names:
                    ca_counts[imported_module] += 1

        # Recopilar métricas de todos los módulos
        all_ca = []
        all_ce = []
        all_instability = []
        all_abstractness = []
        all_distance = []
        total_cbo = 0
        total_rfc = 0
        total_mpc = 0

        for module in project.modules:
            module_metrics = self.calculate_module(module)
            if module_metrics:
                ca = ca_counts.get(module.name, 0)
                ce = module_metrics["ce"]

                # Recalcular instability con Ca correcto
                instability = 0.0
                if ca + ce > 0:
                    instability = ce / (ca + ce)
                elif ce > 0:
                    instability = 1.0

                # Recalcular distance con instability correcto
                abstractness = module_metrics["abstractness"]
                distance = abs(abstractness + instability - 1.0)

                all_ca.append(ca)
                all_ce.append(ce)
                all_instability.append(instability)
                all_abstractness.append(abstractness)
                all_distance.append(distance)

            # Agregar métricas de clases
            for cls in module.classes:
                class_metrics = self.calculate_class(cls)
                if class_metrics:
                    total_cbo += class_metrics["cbo"]
                    total_rfc += class_metrics["rfc"]
                    total_mpc += class_metrics["mpc"]

        # Calcular estadísticas agregadas
        module_count = len(project.modules)
        class_count = sum(len(module.classes) for module in project.modules)

        result = {
            # Estadísticas de módulos
            "avg_ca": sum(all_ca) / module_count if module_count > 0 else 0.0,
            "avg_ce": sum(all_ce) / module_count if module_count > 0 else 0.0,
            "avg_instability": sum(all_instability) / module_count if module_count > 0 else 0.0,
            "avg_abstractness": sum(all_abstractness) / module_count if module_count > 0 else 0.0,
            "avg_distance_main_sequence": sum(all_distance) / module_count
            if module_count > 0
            else 0.0,
            # Estadísticas de clases
            "avg_cbo": total_cbo / class_count if class_count > 0 else 0.0,
            "avg_rfc": total_rfc / class_count if class_count > 0 else 0.0,
            "avg_mpc": total_mpc / class_count if class_count > 0 else 0.0,
            # Conteos
            "module_count": float(module_count),
            "class_count": float(class_count),
            "total_dependencies": float(sum(all_ce)),
            # Máximos (para identificar outliers)
            "max_ca": float(max(all_ca)) if all_ca else 0.0,
            "max_ce": float(max(all_ce)) if all_ce else 0.0,
            "max_distance": float(max(all_distance)) if all_distance else 0.0,
        }

        return result

    def calculate(self, entity: CodeEntity) -> dict[str, float] | None:
        """Calcula las métricas de acoplamiento avanzadas para una entidad específica.

        Args:
            entity: Entidad de código a analizar.

        Returns:
            Union[Dict[str, float], None]: Métricas de acoplamiento para la entidad.
        """
        if isinstance(entity, Function):
            return self.calculate_function(entity)
        elif isinstance(entity, Class):
            return self.calculate_class(entity)
        elif isinstance(entity, Module):
            return self.calculate_module(entity)
        elif isinstance(entity, Project):
            return self.calculate_project(entity)
        else:
            logger.warning(f"Tipo de entidad no soportado: {type(entity)}")
            return None

    def get_aggregated_value(self, entity: CodeEntity) -> float:
        """Obtiene un valor agregado para usar con umbrales.

        Para clases usa CBO, para módulos usa Distance from Main Sequence,
        para proyectos usa el promedio de distancia.

        Args:
            entity: Entidad de código a analizar.

        Returns:
            float: Valor agregado de acoplamiento avanzado.
        """
        result = self.calculate(entity)
        if result is None:
            return 0.0

        if isinstance(entity, Class):
            return result.get("cbo", 0.0)
        elif isinstance(entity, Module):
            return result.get("distance_main_sequence", 0.0)
        elif isinstance(entity, Project):
            return result.get("avg_distance_main_sequence", 0.0)
        else:
            return 0.0
