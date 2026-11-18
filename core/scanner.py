"""Worker de escaneo de redes con airodump-ng."""

from __future__ import annotations

import os
import shutil
import signal
import subprocess
import tempfile
import threading
import time
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

from .parsers import parse_airodump_csv


class ScanWorker(QThread):
    """Ejecuta airodump-ng y publica las redes detectadas en tiempo real.

    Estrategia:
      - airodump-ng se lanza con salida CSV y `--write-interval 1`.
      - Cada ~1.5 s se relee el CSV y se emite la lista de APs.
      - Al terminar (tiempo agotado o botón Detener) se envía SIGINT para
        que airodump-ng cierre el CSV correctamente.
    """

    networks_updated = pyqtSignal(list)
    progress = pyqtSignal(int, int)  # segundos transcurridos, total
    finished_scan = pyqtSignal(bool, bool)  # ¿hubo redes?, ¿cancelado?
    log = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(
        self,
        interface: str,
        duration: int = 30,
        band: str = "bg",
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.interface = interface
        self.duration = max(5, int(duration))
        self.band = band
        self._stop_event = threading.Event()
        self._process: subprocess.Popen | None = None

    def request_stop(self) -> None:
        self._stop_event.set()

    def _terminate_process(self) -> None:
        process = self._process
        if process is None:
            return
        try:
            if process.poll() is None:
                os.killpg(os.getpgid(process.pid), signal.SIGINT)
                try:
                    process.wait(timeout=4)
                except subprocess.TimeoutExpired:
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                    try:
                        process.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                        process.wait()
        except (ProcessLookupError, PermissionError):
            pass

    def run(self) -> None:
        temp_dir = Path(tempfile.mkdtemp(prefix="wifiaudit_scan_"))
        prefix = temp_dir / "scan"
        csv_path = Path(f"{prefix}-01.csv")

        cmd = [
            "airodump-ng",
            "--write",
            str(prefix),
            "--output-format",
            "csv",
            "--write-interval",
            "1",
        ]
        if self.band:
            cmd += ["--band", self.band]
        cmd.append(self.interface)

        started = time.monotonic()
        networks: list[dict] = []
        cancelled = False

        try:
            self.log.emit("$ " + " ".join(cmd))
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                preexec_fn=os.setsid,
            )

            last_publish = 0.0
            while True:
                elapsed = time.monotonic() - started
                if self._stop_event.is_set():
                    cancelled = True
                    break
                if elapsed >= self.duration:
                    break

                self.progress.emit(int(elapsed), self.duration)

                if time.monotonic() - last_publish >= 1.5:
                    networks = parse_airodump_csv(csv_path)
                    if networks:
                        self.networks_updated.emit(networks)
                    last_publish = time.monotonic()

                time.sleep(0.25)

        except FileNotFoundError:
            self.error.emit("airodump-ng no está instalado o no está en el PATH.")
        except Exception as exc:
            self.error.emit(f"Error durante el escaneo: {exc}")
        finally:
            self._terminate_process()
            # Última lectura tras cerrar airodump-ng para no perder redes.
            networks = parse_airodump_csv(csv_path)
            self.networks_updated.emit(networks)
            self.progress.emit(
                int(time.monotonic() - started),
                self.duration,
            )
            self.log.emit(
                f"Escaneo finalizado: {len(networks)} redes detectadas."
            )
            self.finished_scan.emit(bool(networks), cancelled)
            shutil.rmtree(temp_dir, ignore_errors=True)
