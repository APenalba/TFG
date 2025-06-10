"""Servicio de configuración centralizado para PyPex."""

import json
from pathlib import Path
from typing import Any, Dict, Union


# Singleton para el servicio de configuración
class ConfigService:
    """Servicio de configuración centralizado con patrón Singleton."""

    _instance = None

    def __new__(cls):
        """Implementación del patrón Singleton."""
        if cls._instance is None:
            cls._instance = super(ConfigService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Inicializa el servicio de configuración si no está inicializado."""
        if getattr(self, "_initialized", False):
            return

        # Configuración por defecto
        self._config = {
            # Configuración general
            "verbose": False,
            "log_file": None,
            "output_format": "text",
            # Configuración de análisis
            "max_file_size": 1024 * 1024,  # 1MB exactamente
            "ignore_patterns": [
                "**/__pycache__/**",
                "**/.git/**",
                "**/.venv/**",
                "**/venv/**",
                "**/.tox/**",
                "**/.mypy_cache/**",
                "**/.pytest_cache/**",
                "**/node_modules/**",
                "**/.ipynb_checkpoints/**",
            ],
            # Configuración de logging
            "logging": {
                "console_level": "INFO",
                "file_level": "INFO", 
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "date_format": "%Y-%m-%d %H:%M:%S",
            },
            # Umbrales de métricas - Se obtienen dinámicamente de cada métrica
            # Los usuarios pueden personalizar estos valores via configuración
            "thresholds": {},
        }

        self._initialized = True

    def load_from_file(self, file_path: Union[str, Path]) -> None:
        """Carga la configuración desde un archivo JSON.

        Args:
            file_path: Ruta al archivo de configuración.

        Raises:
            FileNotFoundError: Si el archivo no existe.
            json.JSONDecodeError: Si el archivo no es un JSON válido.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(
                f"El archivo de configuración {file_path} no existe"
            )

        with open(path, "r", encoding="utf-8") as f:
            config_data = json.load(f)

        # Actualizar configuración con los valores del archivo
        self._update_config(config_data)

    def update_from_dict(self, config_dict: Dict[str, Any]) -> None:
        """Actualiza la configuración desde un diccionario.

        Args:
            config_dict: Diccionario con valores de configuración.
        """
        self._update_config(config_dict)

    def _update_config(self, new_config: Dict[str, Any]) -> None:
        """Actualización recursiva de la configuración.

        Args:
            new_config: Nuevos valores de configuración.
        """
        for key, value in new_config.items():
            if (
                isinstance(value, dict)
                and key in self._config
                and isinstance(self._config[key], dict)
            ):
                # Si es un diccionario y ya existe, actualizar recursivamente
                self._update_config_dict(self._config[key], value)
            else:
                # Si no es un diccionario o no existe, asignar directamente
                self._config[key] = value

    def _update_config_dict(
        self, target: Dict[str, Any], source: Dict[str, Any]
    ) -> None:
        """Actualiza un diccionario de configuración de forma recursiva.

        Args:
            target: Diccionario destino.
            source: Diccionario origen.
        """
        for key, value in source.items():
            if (
                isinstance(value, dict)
                and key in target
                and isinstance(target[key], dict)
            ):
                self._update_config_dict(target[key], value)
            else:
                target[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Obtiene un valor de configuración.

        Args:
            key: Clave de configuración (puede usar notación con puntos).
            default: Valor por defecto si la clave no existe.

        Returns:
            Any: Valor de configuración o default si no existe.
        """
        # Soporte para notación con puntos (ej: "thresholds.cyclomatic_complexity.high")
        if "." in key:
            parts = key.split(".")
            value = self._config
            for part in parts:
                if not isinstance(value, dict) or part not in value:
                    return default
                value = value[part]
            return value

        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Establece un valor de configuración.

        Args:
            key: Clave de configuración (puede usar notación con puntos).
            value: Valor a establecer.
        """
        # Soporte para notación con puntos
        if "." in key:
            parts = key.split(".")
            config = self._config

            # Navegar hasta el último nivel
            for part in parts[:-1]:
                if part not in config or not isinstance(config[part], dict):
                    config[part] = {}
                config = config[part]

            # Establecer el valor en el último nivel
            config[parts[-1]] = value
        else:
            self._config[key] = value

    def get_all(self) -> Dict[str, Any]:
        """Obtiene toda la configuración.

        Returns:
            Dict[str, Any]: Diccionario con toda la configuración.
        """
        return self._config.copy()

    def reset_for_testing(self) -> None:
        """Reinicia la configuración a sus valores predeterminados.

        Este método solo debe utilizarse durante las pruebas para
        asegurarse de que cada test tenga un estado limpio.
        """
        self.__init__()


# Función para obtener la instancia del servicio
def get_config() -> ConfigService:
    """Obtiene la instancia del servicio de configuración.

    Returns:
        ConfigService: Instancia del servicio de configuración.
    """
    return ConfigService()
