"""Worker de cracking con aircrack-ng."""

from __future__ import annotations

import threading
import time

from PyQt6.QtCore import QThread, pyqtSignal

from .parsers import (
    count_lines,
    extract_found_key,
    parse_aircrack_progress,
)
from .process import PtyProcess


class CrackWorker(QThread):
    """Ejecuta aircrack-ng contra un .cap y un diccionario.

    Publica el progreso (keys/s probadas) y el resultado final. Se usa PTY
    para recibir las actualizaciones que aircrack-ng escribe con \\r.
    """

    log = pyqtSignal(str)
    progress = pyqtSignal(int, int, float)  # probadas, total, keys/s
    result = pyqtSignal(str, str)  # estado, clave
    finished_crack = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(
        self,
        cap_path: str,
        wordlist: str,
        bssid: str = "",
        max_runtime: int = 1800,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.cap_path = cap_path
        self.wordlist = wordlist
        self.bssid = bssid.strip()
        self.max_runtime = max_runtime
        self._stop_event = threading.Event()
        self._found_key: str | None = None
        self._not_found = False

    def request_stop(self) -> None:
        self._stop_event.set()

    def _handle_line(self, line: str) -> None:
        text = line.strip()
        if not text:
            return

        progress = parse_aircrack_progress(text)
        if progress:
            self.progress.emit(*progress)

        key = extract_found_key(text)
        if key is not None:
            self._found_key = key
            self.log.emit(f"CLAVE ENCONTRADA: {key}")

        upper = text.upper()
        if "KEY NOT FOUND" in upper or "PASSPHRASE NOT IN DICTIONARY" in upper:
            self._not_found = True

        interesting = (
            "Aircrack-ng",
            "Opening",
            "Read ",
            "BSSID",
            "ESSID",
            "KEY FOUND",
            "KEY NOT FOUND",
            "Passphrase",
            "Warning",
            "Quitting",
        )
        if any(token in text for token in interesting):
            self.log.emit(text)

    def run(self) -> None:
        reason = "stopped"
        started = time.monotonic()
        total = count_lines(self.wordlist)
        self.progress.emit(0, total, 0.0)

        cmd = ["aircrack-ng", "-w", self.wordlist]
        if self.bssid:
            cmd += ["-b", self.bssid]
        cmd.append(self.cap_path)
        self.log.emit("$ " + " ".join(cmd))

        try:
            process = PtyProcess(cmd)
        except FileNotFoundError:
            self.error.emit(
                "aircrack-ng no está instalado o no está en el PATH."
            )
            self.result.emit("error", "")
            self.finished_crack.emit()
            return
        except Exception as exc:
            self.error.emit(f"No se pudo iniciar aircrack-ng: {exc}")
            self.result.emit("error", "")
            self.finished_crack.emit()
            return

        try:
            while True:
                if self._stop_event.is_set():
                    reason = "stopped"
                    break
                if time.monotonic() - started > self.max_runtime:
                    reason = "timeout"
                    self.log.emit("Se alcanzó el tiempo máximo de análisis.")
                    break

                if process.proc.poll() is not None:
                    for line in process.read_lines(0.05):
                        self._handle_line(line)
                    break

                for line in process.read_lines(0.2):
                    self._handle_line(line)
        except Exception as exc:
            reason = "error"
            self.error.emit(f"Error durante el cracking: {exc}")
        finally:
            process.stop()

        if self._found_key is not None:
            self.result.emit("found", self._found_key)
        elif reason == "stopped":
            self.result.emit("stopped", "")
        elif reason == "timeout":
            self.result.emit("timeout", "")
        elif reason == "error":
            self.result.emit("error", "")
        elif self._not_found:
            self.result.emit("not_found", "")
        else:
            self.result.emit("not_found", "")

        self.finished_crack.emit()
