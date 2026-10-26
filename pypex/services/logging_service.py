"""Servicio de logging y presentación para la aplicación."""

import logging
import sys
import time
from contextlib import AbstractContextManager, contextmanager
from pathlib import Path
from typing import Any, Protocol

# Import RichHandler and Progress
try:
    from rich import print as rich_print
    from rich.console import Console
    from rich.logging import RichHandler
    from rich.panel import Panel
    from rich.progress import (
        BarColumn,
        Progress,
        TextColumn,
        TimeElapsedColumn,
        TimeRemainingColumn,
    )
    from rich.table import Table

    _RICH_AVAILABLE = True
except ImportError:
    RichHandler = None  # type: ignore
    Console = None  # type: ignore
    Panel = None  # type: ignore
    Table = None  # type: ignore
    rich_print = None  # type: ignore
    _RICH_AVAILABLE = False

# Import tqdm as fallback
try:
    from tqdm import tqdm

    _TQDM_AVAILABLE = True
except ImportError:
    _TQDM_AVAILABLE = False


def _get_logging_config() -> dict[str, Any]:
    """Obtiene configuración de logging desde ConfigService o valores por defecto."""
    try:
        # Importar aquí para evitar import circular
        from pypex.services.config_service import get_config

        config = get_config()

        return {
            "console_level": config.get("logging.console_level", logging.INFO),
            "file_level": config.get("logging.file_level", logging.DEBUG),
            "format": config.get(
                "logging.format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            ),
            "date_format": config.get("logging.date_format", "%Y-%m-%d %H:%M:%S"),
        }
    except ImportError:
        # Fallback si ConfigService no está disponible
        return {
            "console_level": logging.INFO,
            "file_level": logging.DEBUG,
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "date_format": "%Y-%m-%d %H:%M:%S",
        }


# Cacheo de loggers para reutilización
_loggers: dict[str, logging.Logger] = {}


class IProgressBar(Protocol):
    """Interfaz para barras de progreso."""

    def update(self, advance: int = 1, description: str | None = None) -> None:
        """Actualiza la barra de progreso."""
        ...

    def close(self) -> None:
        """Cierra la barra de progreso."""
        ...


class RichProgressBar:
    """Implementación de progress bar usando Rich."""

    def __init__(self, progress: Any, task_id: Any):
        self.progress = progress
        self.task_id = task_id

    def update(self, advance: int = 1, description: str | None = None) -> None:
        """Actualiza la barra de progreso."""
        kwargs = {"advance": advance}
        if description:
            kwargs["description"] = description
        self.progress.update(self.task_id, **kwargs)

    def close(self) -> None:
        """Rich progress se cierra automáticamente con el context manager."""
        pass


class TqdmProgressBar:
    """Implementación de progress bar usando tqdm."""

    def __init__(self, tqdm_instance: Any):
        self.tqdm_instance = tqdm_instance

    def update(self, advance: int = 1, description: str | None = None) -> None:
        """Actualiza la barra de progreso."""
        if description:
            self.tqdm_instance.set_description(description)
        self.tqdm_instance.update(advance)

    def close(self) -> None:
        """Cierra la barra de progreso."""
        self.tqdm_instance.close()


class SimpleProgressBar:
    """Implementación simple de progress bar usando prints."""

    def __init__(self, total: int, description: str = "Progress"):
        self.total = total
        self.current = 0
        self.description = description
        self.start_time = time.time()
        self.last_print_time = 0
        self._print_progress()

    def update(self, advance: int = 1, description: str | None = None) -> None:
        """Actualiza la barra de progreso."""
        self.current += advance
        if description:
            self.description = description

        # Solo imprimir cada segundo o al completar
        current_time = time.time()
        if current_time - self.last_print_time >= 1.0 or self.current >= self.total:
            self._print_progress()
            self.last_print_time = current_time

    def _print_progress(self) -> None:
        """Imprime el progreso actual."""
        if self.total > 0:
            percentage = (self.current / self.total) * 100
            elapsed = time.time() - self.start_time

            if self.current > 0 and elapsed > 0:
                rate = self.current / elapsed
                eta = (self.total - self.current) / rate if rate > 0 else 0
                print(
                    f"\r{self.description}: {self.current}/{self.total} ({percentage:.1f}%) "
                    f"- ETA: {eta:.0f}s",
                    end="",
                    flush=True,
                )
            else:
                print(
                    f"\r{self.description}: {self.current}/{self.total} ({percentage:.1f}%)",
                    end="",
                    flush=True,
                )

        if self.current >= self.total:
            print()  # Nueva línea al completar

    def close(self) -> None:
        """Finaliza la barra de progreso."""
        if self.current < self.total:
            self.current = self.total
            self._print_progress()


class ProgressBarManager:
    """Gestor de barras de progreso que selecciona la mejor implementación disponible."""

    def __init__(self, prefer_rich: bool = True, prefer_tqdm: bool = True):
        self.prefer_rich = prefer_rich
        self.prefer_tqdm = prefer_tqdm

    @contextmanager
    def create_progress_bar(
        self, total: int, description: str = "Progress", disable: bool = False
    ) -> AbstractContextManager[IProgressBar]:
        """Crea una barra de progreso usando la mejor implementación disponible.

        Args:
            total: Número total de elementos a procesar
            description: Descripción de la tarea
            disable: Si True, desactiva la barra de progreso

        Yields:
            IProgressBar: Instancia de barra de progreso
        """
        if disable:
            # Progress bar deshabilitada - usar implementación dummy
            class DummyProgressBar:
                def update(self, advance: int = 1, description: str | None = None) -> None:
                    pass

                def close(self) -> None:
                    pass

            yield DummyProgressBar()
            return

        # Intentar usar Rich si está disponible y preferido
        if self.prefer_rich and _RICH_AVAILABLE:
            try:
                progress = Progress(
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                    TimeRemainingColumn(),
                    TimeElapsedColumn(),
                    transient=True,
                )
                with progress:
                    task_id = progress.add_task(description, total=total)
                    yield RichProgressBar(progress, task_id)
                return
            except Exception:
                pass  # Fallback a la siguiente opción

        # Intentar usar tqdm si está disponible y preferido
        if self.prefer_tqdm and _TQDM_AVAILABLE:
            try:
                tqdm_instance = tqdm(total=total, desc=description)
                try:
                    yield TqdmProgressBar(tqdm_instance)
                finally:
                    tqdm_instance.close()
                return
            except Exception:
                pass  # Fallback a la implementación simple

        # Fallback a implementación simple
        simple_bar = SimpleProgressBar(total, description)
        try:
            yield simple_bar
        finally:
            simple_bar.close()


# Instancia global del gestor de progress bars
_progress_manager = ProgressBarManager()


class IPresentationService(Protocol):
    """Interfaz para servicios de presentación."""

    def print_success(self, message: str, **kwargs) -> None:
        """Imprime un mensaje de éxito."""
        ...

    def print_info(self, message: str, **kwargs) -> None:
        """Imprime un mensaje informativo."""
        ...

    def print_warning(self, message: str, **kwargs) -> None:
        """Imprime un mensaje de advertencia."""
        ...

    def print_error(self, message: str, **kwargs) -> None:
        """Imprime un mensaje de error."""
        ...

    def create_table(self, title: str = "", **kwargs) -> Any:
        """Crea una tabla para mostrar datos."""
        ...

    def create_panel(self, content: str, title: str = "", **kwargs) -> Any:
        """Crea un panel informativo."""
        ...

    def print_table(self, table: Any) -> None:
        """Imprime una tabla."""
        ...

    def print_panel(self, panel: Any) -> None:
        """Imprime un panel."""
        ...


class RichPresentationService:
    """Servicio de presentación usando Rich."""

    def __init__(self, console: Console | None = None):
        self.console = console or Console()

    def print_success(self, message: str, **kwargs) -> None:
        """Imprime un mensaje de éxito."""
        self.console.print(f"✅ [bold green]{message}[/bold green]", **kwargs)

    def print_info(self, message: str, **kwargs) -> None:
        """Imprime un mensaje informativo."""
        self.console.print(f"ℹ️ [cyan]{message}[/cyan]", **kwargs)

    def print_warning(self, message: str, **kwargs) -> None:
        """Imprime un mensaje de advertencia."""
        self.console.print(f"⚠️ [yellow]{message}[/yellow]", **kwargs)

    def print_error(self, message: str, **kwargs) -> None:
        """Imprime un mensaje de error."""
        self.console.print(f"❌ [bold red]{message}[/bold red]", **kwargs)

    def create_table(self, title: str = "", **kwargs) -> Table:
        """Crea una tabla para mostrar datos."""
        return Table(title=title, **kwargs)

    def create_panel(self, content: str, title: str = "", **kwargs) -> Panel:
        """Crea un panel informativo."""
        return Panel(content, title=title, **kwargs)

    def print_table(self, table: Table) -> None:
        """Imprime una tabla."""
        self.console.print(table)

    def print_panel(self, panel: Panel) -> None:
        """Imprime un panel."""
        self.console.print(panel)

    def print(self, *args, **kwargs) -> None:
        """Imprime usando Rich console."""
        self.console.print(*args, **kwargs)


class FallbackPresentationService:
    """Servicio de presentación usando print estándar."""

    def print_success(self, message: str, **kwargs) -> None:
        """Imprime un mensaje de éxito."""
        print(f"✅ {message}")

    def print_info(self, message: str, **kwargs) -> None:
        """Imprime un mensaje informativo."""
        print(f"ℹ️ {message}")

    def print_warning(self, message: str, **kwargs) -> None:
        """Imprime un mensaje de advertencia."""
        print(f"⚠️ {message}")

    def print_error(self, message: str, **kwargs) -> None:
        """Imprime un mensaje de error."""
        print(f"❌ {message}")

    def create_table(self, title: str = "", **kwargs) -> dict:
        """Crea una representación de tabla como diccionario."""
        return {"title": title, "columns": [], "rows": [], **kwargs}

    def create_panel(self, content: str, title: str = "", **kwargs) -> dict:
        """Crea una representación de panel como diccionario."""
        return {"content": content, "title": title, **kwargs}

    def print_table(self, table: dict) -> None:
        """Imprime una tabla usando formato texto plano."""
        if table["title"]:
            print(f"\n{table['title']}")
            print("=" * len(table["title"]))

        # Imprimir headers si existen
        if "columns" in table and table["columns"]:
            headers = " | ".join(col.get("header", "") for col in table["columns"])
            print(headers)
            print("-" * len(headers))

        # Imprimir filas si existen
        if "rows" in table and table["rows"]:
            for row in table["rows"]:
                print(" | ".join(str(cell) for cell in row))

    def print_panel(self, panel: dict) -> None:
        """Imprime un panel usando formato texto plano."""
        title = panel.get("title", "")
        content = panel.get("content", "")

        if title:
            print(f"\n{title}")
            print("=" * len(title))

        print(content)

    def print(self, *args, **kwargs) -> None:
        """Imprime usando print estándar."""
        print(*args, **kwargs)


# Instancia global del servicio de presentación
_presentation_service: IPresentationService | None = None


def configure_presentation_service(prefer_rich: bool = True) -> IPresentationService:
    """Configura y retorna el servicio de presentación.

    Args:
        prefer_rich: Si preferir Rich cuando esté disponible

    Returns:
        IPresentationService: Servicio de presentación configurado
    """
    global _presentation_service

    if prefer_rich and _RICH_AVAILABLE:
        _presentation_service = RichPresentationService()
    else:
        _presentation_service = FallbackPresentationService()

    return _presentation_service


def get_presentation_service() -> IPresentationService:
    """Obtiene el servicio de presentación.

    Returns:
        IPresentationService: Servicio de presentación activo
    """
    global _presentation_service

    if _presentation_service is None:
        _presentation_service = configure_presentation_service()

    return _presentation_service


def configure_logging(
    console_level: int | None = None,
    file_level: int | None = None,
    log_file: str | Path | None = None,
    log_format: str | None = None,
) -> None:
    """Configura el sistema de logging global con niveles y archivo.

    Args:
        console_level: Nivel de logging para consola
        file_level: Nivel de logging para archivo
        log_file: Archivo de log opcional
        log_format: Formato de log opcional
    """
    global LOGGING_CONFIG

    # Obtener configuración actual
    logging_config = _get_logging_config()

    # Actualizar configuración con parámetros
    if console_level is not None:
        logging_config["console_level"] = console_level
    if file_level is not None:
        logging_config["file_level"] = file_level
    if log_format is not None:
        logging_config["format"] = log_format

    # Configurar logging básico
    logging.basicConfig(
        level=logging_config["console_level"],
        format=logging_config["format"],
        datefmt=logging_config["date_format"],
    )

    # Aplicar a loggers existentes
    for logger in _loggers.values():
        _configure_logger_handlers(logger, log_file)


def configure_progress_bars(prefer_rich: bool = True, prefer_tqdm: bool = True) -> None:
    """Configura las preferencias para las barras de progreso.

    Args:
        prefer_rich: Si preferir Rich para las barras de progreso
        prefer_tqdm: Si preferir tqdm como fallback
    """
    global _progress_manager
    _progress_manager = ProgressBarManager(prefer_rich=prefer_rich, prefer_tqdm=prefer_tqdm)


def get_progress_manager() -> ProgressBarManager:
    """Obtiene el gestor de barras de progreso.

    Returns:
        ProgressBarManager: Gestor de barras de progreso
    """
    return _progress_manager


def get_logger(name: str, log_file: str | Path | None = None) -> logging.Logger:
    """
    Obtiene un logger configurado con el nombre especificado.

    Args:
        name: Nombre del logger (típicamente __name__)
        log_file: Archivo de log opcional

    Returns:
        Logger configurado
    """
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)
    _configure_logger_handlers(logger, log_file)
    _loggers[name] = logger

    return logger


def _configure_logger_handlers(logger: logging.Logger, log_file: str | Path | None = None) -> None:
    """Configura los handlers de un logger específico."""
    # Obtener configuración actual
    logging_config = _get_logging_config()

    # Limpiar handlers existentes
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Los loggers de PyPex tienen sus propios handlers; sin esto el mensaje
    # se emitiría también por el handler raíz que añade logging.basicConfig()
    logger.propagate = False

    # Handler de consola
    if _RICH_AVAILABLE:
        console_handler = RichHandler(
            console=Console(stderr=True), show_time=False, show_path=False
        )
    else:
        console_handler = logging.StreamHandler(sys.stderr)

    console_handler.setLevel(logging_config["console_level"])

    # Usar formato simplificado para Rich, completo para StreamHandler
    if _RICH_AVAILABLE:
        console_formatter = logging.Formatter("%(message)s")
    else:
        console_formatter = logging.Formatter(
            fmt=logging_config["format"], datefmt=logging_config["date_format"]
        )

    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # Handler de archivo si se especifica
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging_config["file_level"])
        file_formatter = logging.Formatter(
            fmt=logging_config["format"], datefmt=logging_config["date_format"]
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    logger.setLevel(min(logging_config["console_level"], logging_config["file_level"]))
