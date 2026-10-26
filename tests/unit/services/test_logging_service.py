"""Tests para el servicio de logging."""

import subprocess
import sys

from pypex.services.logging_service import get_logger


def test_pypex_loggers_do_not_propagate_to_root():
    assert get_logger("pypex.tests.logging").propagate is False


def test_cli_log_messages_are_not_duplicated():
    # En un proceso aparte: dentro de pytest el logger raíz ya tiene handlers
    # y logging.basicConfig() no añade el suyo, así que no se reproduciría.
    result = subprocess.run(
        [sys.executable, "-m", "pypex", "--verbose", "thresholds", "--help"],
        capture_output=True,
        text=True,
        check=True,
    )

    assert result.stderr.count("iniciado") == 1
