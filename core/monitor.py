"""Workers encargados de activar y restaurar el modo monitor."""

from __future__ import annotations

import threading

from PyQt6.QtCore import QThread, pyqtSignal

from .process import run_streaming
from .tools import detect_monitor_interface, restart_network_manager


class MonitorWorker(QThread):
    """Ejecuta `airmon-ng check kill` y `airmon-ng start <interfaz>`.

    Se hace en un hilo porque `check kill` puede tardar varios segundos
    (detiene NetworkManager y wpa_supplicant) y no queremos congelar la UI.
    """

    log = pyqtSignal(str)
    activated = pyqtSignal(str)  # nombre real de la interfaz en modo monitor
    error = pyqtSignal(str)

    def __init__(self, interface: str, parent=None) -> None:
        super().__init__(parent)
        self.interface = interface
        self._stop_event = threading.Event()

    def request_stop(self) -> None:
        self._stop_event.set()

    def run(self) -> None:  # noqa: D401 - método de QThread
        try:
            self.log.emit("$ airmon-ng check kill")
            run_streaming(
                ["airmon-ng", "check", "kill"],
                self.log.emit,
                self._stop_event,
                timeout=60,
            )
            if self._stop_event.is_set():
                self.error.emit("Activación del modo monitor cancelada.")
                return

            self.log.emit(f"$ airmon-ng start {self.interface}")
            code = run_streaming(
                ["airmon-ng", "start", self.interface],
                self.log.emit,
                self._stop_event,
                timeout=120,
            )
            if self._stop_event.is_set():
                self.error.emit("Activación del modo monitor cancelada.")
                return
            if code != 0:
                self.error.emit(
                    "airmon-ng no pudo activar el modo monitor. "
                    "Revisa el log y comprueba el driver del adaptador."
                )
                return

            # airmon-ng puede renombrar la interfaz a <nombre>mon o dejarla
            # igual. Preguntamos a `iw dev` cuál es realmente la monitor.
            monitor = detect_monitor_interface() or self.interface
            self.activated.emit(monitor)
        except Exception as exc:  # red de seguridad para no matar el hilo
            self.error.emit(f"Error inesperado al activar el monitor: {exc}")


class RestoreWorker(QThread):
    """Devuelve la interfaz a modo managed y reinicia NetworkManager."""

    log = pyqtSignal(str)
    finished_ok = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, monitor_interface: str | None, parent=None) -> None:
        super().__init__(parent)
        self.monitor_interface = monitor_interface

    def run(self) -> None:
        try:
            if self.monitor_interface:
                self.log.emit(f"$ airmon-ng stop {self.monitor_interface}")
                run_streaming(
                    ["airmon-ng", "stop", self.monitor_interface],
                    self.log.emit,
                    timeout=60,
                )

            self.log.emit("$ systemctl restart NetworkManager")
            code, output = restart_network_manager()
            for line in output.splitlines():
                if line.strip():
                    self.log.emit(line)

            if code != 0:
                self.error.emit(
                    "No se pudo reiniciar NetworkManager. "
                    "Revisa el log y reinícialo manualmente."
                )
                return

            self.finished_ok.emit(
                "Interfaz restaurada a modo managed y NetworkManager reiniciado."
            )
        except Exception as exc:
            self.error.emit(f"Error al restaurar la interfaz: {exc}")
