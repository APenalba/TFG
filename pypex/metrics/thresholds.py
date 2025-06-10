"""Sistema de umbrales configurables para interpretación de métricas PyPex.

Este módulo implementa un sistema flexible de umbrales que permite interpretar
valores de métricas en diferentes niveles de complejidad. Soporta múltiples perfiles
de calidad y personalización de umbrales por métrica específica.

Classes:
    ComplexityLevel: Enum de niveles de complejidad
    ThresholdConfig: Configurador principal de umbrales

Functions:
    get_threshold_config: Obtiene la instancia singleton de configuración

Note:
    El sistema soporta perfiles de calidad (strict, normal, permissive) que ajustan
    automáticamente los umbrales según el nivel de rigor deseado.
    
    Cada métrica define sus propios umbrales por defecto. El ConfigService
    puede sobreescribir estos valores por configuración.
"""

from enum import Enum
from typing import Dict, Optional

from pypex.services.logging_service import get_logger

logger = get_logger(__name__)


class ComplexityLevel(Enum):
    """Niveles de complejidad para interpretación de métricas."""

    LOW = "Baja"
    MEDIUM = "Media"
    HIGH = "Alta"
    VERY_HIGH = "Muy Alta"


class ThresholdConfig:
    """Configurador de umbrales para interpretación de métricas de complejidad.

    Esta clase gestiona los umbrales utilizados para interpretar valores de métricas
    y clasificarlos en niveles de complejidad. Soporta perfiles de calidad predefinidos
    y personalización de umbrales específicos por métrica.

    Se integra con ConfigService y obtiene umbrales por defecto de cada métrica.

    Attributes:
        _config_service: Servicio de configuración para obtener umbrales personalizados
        _metric_registry: Registro de métricas para obtener umbrales por defecto
        _active_profile: Perfil de calidad activo
        _profiles: Configuraciones de perfiles disponibles

    Example:
        >>> config = get_threshold_config()
        >>> config.set_active_profile("strict")
        >>> umbrales = config.get_thresholds("cyclomatic_complexity")
        >>> nivel = config.interpret_value("cyclomatic_complexity", 15)

    Note:
        Los perfiles ajustan automáticamente todos los umbrales:
        - strict: Umbrales más bajos (mayor rigor)
        - normal: Umbrales estándar
        - permissive: Umbrales más altos (menor rigor)
    """

    def __init__(self):
        """Inicializa la configuración de umbrales con integración a ConfigService."""
        # Lazy import para evitar ciclos de dependencia
        self._config_service = None
        self._metric_registry = None
        
        # Perfiles predefinidos (modificadores para los umbrales base)
        self._profiles = {
            "strict": {
                "multiplier": 0.7,  # Reduce los umbrales (más estricto)
            },
            "normal": {
                "multiplier": 1.0,  # Sin modificación
            },
            "permissive": {
                "multiplier": 1.5,  # Aumenta los umbrales (más permisivo)
            },
        }

        self._active_profile = "normal"

    def _get_config_service(self):
        """Obtiene el servicio de configuración de forma lazy."""
        if self._config_service is None:
            try:
                from pypex.services.config_service import get_config
                self._config_service = get_config()
            except ImportError:
                logger.warning("ConfigService no disponible")
                self._config_service = None
        return self._config_service

    def _get_metric_registry(self):
        """Obtiene el registro de métricas de forma lazy."""
        if self._metric_registry is None:
            try:
                # Lazy import para evitar ciclos de dependencia
                from pypex.metrics.registry import get_registry
                self._metric_registry = get_registry()
            except ImportError:
                logger.warning("MetricsRegistry no disponible")
                self._metric_registry = None
        return self._metric_registry

    def get_default_thresholds(self, metric_name: str) -> Dict[str, float]:
        """Obtiene los umbrales por defecto de una métrica específica.
        
        Args:
            metric_name: Nombre de la métrica.
            
        Returns:
            Dict[str, float]: Umbrales por defecto de la métrica.
        """
        registry = self._get_metric_registry()
        if registry:
            try:
                metric = registry.get_metric(metric_name)
                return metric.get_default_thresholds()
            except Exception as e:
                logger.warning(f"No se pudo obtener umbrales por defecto para {metric_name}: {e}")
        
        # Fallback a umbrales genéricos
        return self._get_generic_thresholds(metric_name)

    def _get_generic_thresholds(self, metric_name: str) -> Dict[str, float]:
        """Obtiene umbrales genéricos como fallback final.
        
        Args:
            metric_name: Nombre de la métrica.
            
        Returns:
            Dict[str, float]: Umbrales genéricos.
        """
        logger.warning(f"Usando umbrales genéricos para métrica desconocida: {metric_name}")
        return {"low": 5.0, "medium": 10.0, "high": 15.0}

    def get_thresholds(
        self, metric_name: str, profile: str = None
    ) -> Dict[str, float]:
        """Obtiene los umbrales para una métrica específica.

        Args:
            metric_name: Nombre de la métrica.
            profile: Perfil a usar (None para usar el activo).

        Returns:
            Dict[str, float]: Diccionario con umbrales (bajo, medio, alto).
        """
        # 1. Intentar obtener desde ConfigService (PRIORIDAD MÁXIMA - NO aplicar perfiles)
        config_service = self._get_config_service()
        if config_service:
            config_thresholds = config_service.get(f"thresholds.{metric_name}")
            if config_thresholds and isinstance(config_thresholds, dict):
                # Los umbrales personalizados NO se ven afectados por perfiles
                return config_thresholds

        # 2. Si no hay configuración personalizada, obtener umbrales por defecto de la métrica
        base_thresholds = self.get_default_thresholds(metric_name)

        # 3. Aplicar perfiles SOLO a umbrales por defecto (no personalizados)
        profile_to_use = profile if profile is not None else self._active_profile

        # Aplicar modificadores según el perfil especificado
        if profile_to_use != "normal":
            if profile_to_use in self._profiles:
                profile_config = self._profiles[profile_to_use]
                multiplier = profile_config["multiplier"]

                return {
                    level: value * multiplier
                    for level, value in base_thresholds.items()
                }
            else:
                logger.warning(
                    f"Perfil '{profile_to_use}' no válido. Usando perfil normal."
                )

        return base_thresholds

    def set_thresholds(
        self, metric_name: str, thresholds: Dict[str, float]
    ) -> None:
        """Establece umbrales personalizados para una métrica en ConfigService.

        Args:
            metric_name: Nombre de la métrica.
            thresholds: Diccionario con umbrales (bajo, medio, alto).

        Raises:
            ValueError: Si el diccionario de umbrales no es válido.
        """
        if not all(key in thresholds for key in ["low", "medium", "high"]):
            raise ValueError(
                "El diccionario de umbrales debe contener las claves 'low', 'medium' y 'high'"
            )

        config_service = self._get_config_service()
        if config_service:
            config_service.set(f"thresholds.{metric_name}", thresholds)
            logger.debug(f"Umbrales actualizados en ConfigService para la métrica '{metric_name}'")
        else:
            logger.warning(f"ConfigService no disponible. No se pudieron guardar umbrales para '{metric_name}'")

    def set_active_profile(self, profile_name: str) -> None:
        """Establece el perfil activo para los umbrales.

        Args:
            profile_name: Nombre del perfil ('strict', 'normal', 'permissive').

        Raises:
            ValueError: Si el perfil no es válido.
        """
        if profile_name not in self._profiles:
            raise ValueError(
                f"Perfil '{profile_name}' no válido. Perfiles disponibles: {list(self._profiles.keys())}"
            )

        self._active_profile = profile_name
        logger.debug(f"Perfil de umbrales cambiado a '{profile_name}'")

    def interpret_value(
        self, metric_name: str, value: float
    ) -> ComplexityLevel:
        """Interpreta un valor según los umbrales de una métrica.

        Args:
            metric_name: Nombre de la métrica.
            value: Valor a interpretar.

        Returns:
            ComplexityLevel: Nivel de complejidad interpretado.
        """
        thresholds = self.get_thresholds(metric_name)

        if value < thresholds["low"]:
            return ComplexityLevel.LOW
        elif value < thresholds["medium"]:
            return ComplexityLevel.MEDIUM
        elif value < thresholds["high"]:
            return ComplexityLevel.HIGH
        else:
            return ComplexityLevel.VERY_HIGH


# Singleton para acceso global
_config_instance = None


def get_threshold_config() -> ThresholdConfig:
    """Obtiene la instancia global de configuración de umbrales.

    Returns:
        ThresholdConfig: Instancia de configuración.
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = ThresholdConfig()
    return _config_instance
