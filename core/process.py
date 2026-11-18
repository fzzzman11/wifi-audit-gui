"""Ejecución controlada de procesos externos.

Las herramientas de aircrack-ng son programas interactivos que escriben en la
terminal con secuencias ANSI y con retornos de carro (\\r). Si las lanzamos con
un pipe normal, su salida puede quedar bloqueada en el buffer y la UI no vería
nada en tiempo real. Para evitarlo usamos un pseudo-terminal (PTY): el proceso
cree que está conectado a una terminal real y va vaciando su salida.

Además, cada proceso se lanza en su propia sesión (os.setsid) para poder
matarlo junto con sus hijos mediante os.killpg.
"""

from __future__ import annotations

import os
import pty
import re
import select
import signal
import subprocess
import time
from collections.abc import Callable, Sequence

# Limpia códigos de escape ANSI (colores, borrado de pantalla, etc.).
ANSI_RE = re.compile(rb"\x1b\[[0-9;?]*[ -/]*[@-~]")


def run_command(
    cmd: Sequence[str],
    timeout: float = 30.0,
) -> tuple[int, str]:
    """Ejecuta un comando corto y devuelve (código de salida, texto).

    Se usa para comprobaciones rápidas (iw dev, systemctl, etc.) donde no
    necesitamos salida en vivo. Nunca lanza excepciones por fallo del comando.
    """
    try:
        result = subprocess.run(
            list(cmd),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return result.returncode, (result.stdout or "") + (result.stderr or "")
    except FileNotFoundError:
        return 127, f"Comando no encontrado: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return 124, f"Tiempo de espera agotado: {' '.join(cmd)}"
    except OSError as exc:  # permisos, binario corrupto, etc.
        return 1, f"No se pudo ejecutar {' '.join(cmd)}: {exc}"


class PtyProcess:
    """Proceso externo con salida en vivo a través de un pseudo-terminal."""

    def __init__(self, cmd: Sequence[str]) -> None:
        self.cmd = list(cmd)
        self.master, slave = pty.openpty()
        self.proc = subprocess.Popen(
            self.cmd,
            stdin=subprocess.DEVNULL,
            stdout=slave,
            stderr=slave,
            preexec_fn=os.setsid,  # sesión propia -> killpg seguro
            close_fds=True,
        )
        os.close(slave)  # el hijo ya tiene su copia
        self._buffer = b""
        self._closed = False
        self.eof = False

    def read_lines(self, timeout: float = 0.25) -> list[str]:
        """Devuelve las líneas completas disponibles en este instante.

        Se separa tanto por \\n como por \\r porque aircrack-ng/airodump-ng
        actualizan sus contadores sobrescribiendo la misma línea.
        """
        if self._closed:
            return []

        try:
            ready, _, _ = select.select([self.master], [], [], timeout)
        except (OSError, ValueError):
            return []
        if not ready:
            return []

        try:
            chunk = os.read(self.master, 8192)
        except OSError:
            # En Linux, leer un PTY cuyo hijo terminó produce EIO.
            self.eof = True
            return []
        if not chunk:
            self.eof = True
            return []

        chunk = ANSI_RE.sub(b"", chunk)
        chunk = chunk.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        self._buffer += chunk
        parts = self._buffer.split(b"\n")
        self._buffer = parts.pop()
        return [p.decode("utf-8", "ignore").rstrip() for p in parts]

    def _signal_group(self, sig: int) -> None:
        try:
            os.killpg(os.getpgid(self.proc.pid), sig)
        except (ProcessLookupError, PermissionError):
            pass

    def stop(self, timeout: float = 6.0) -> None:
        """Detiene el proceso de forma escalonada: SIGINT, SIGTERM, SIGKILL.

        SIGINT es importante en airodump-ng porque le permite cerrar y
        finalizar correctamente los archivos .cap y .csv.
        """
        if self.proc.poll() is None:
            self._signal_group(signal.SIGINT)
            try:
                self.proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                self._signal_group(signal.SIGTERM)
                try:
                    self.proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    self._signal_group(signal.SIGKILL)
                    try:
                        self.proc.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        pass
        self.close()

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        try:
            os.close(self.master)
        except OSError:
            pass


def run_streaming(
    cmd: Sequence[str],
    on_line: Callable[[str], None],
    stop_event=None,
    timeout: float | None = None,
) -> int:
    """Ejecuta un comando emitiendo cada línea y permitiendo cancelarlo.

    Se usa para airmon-ng y aireplay-ng, que pueden tardar unos segundos.
    Devuelve el código de salida (130 si se canceló, 124 si expiró el tiempo).
    """
    process = PtyProcess(cmd)
    started = time.monotonic()
    try:
        while True:
            if stop_event is not None and stop_event.is_set():
                process.stop()
                return 130
            if timeout is not None and time.monotonic() - started > timeout:
                process.stop()
                return 124
            for line in process.read_lines(0.2):
                if line.strip():
                    on_line(line)
            if process.proc.poll() is not None:
                # Drenar lo que quede pendiente antes de salir.
                for line in process.read_lines(0.05):
                    if line.strip():
                        on_line(line)
                return process.proc.returncode or 0
    finally:
        # Si salimos por una excepción, no dejamos el proceso huérfano.
        if process.proc.poll() is None:
            process.stop()
        else:
            process.close()
