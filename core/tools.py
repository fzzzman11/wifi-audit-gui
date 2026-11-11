"""Detección de herramientas, interfaces WiFi y estado de privilegios."""

from __future__ import annotations

import os
import re
import shutil
from pathlib import Path

from .constants import REQUIRED_TOOLS
from .process import run_command


def is_root() -> bool:
    """True si el proceso corre como root (necesario para modo monitor)."""
    return os.geteuid() == 0


def tool_paths() -> dict[str, str | None]:
    """Ruta de cada herramienta requerida, o None si no está instalada."""
    return {tool: shutil.which(tool) for tool in REQUIRED_TOOLS}


def missing_tools(paths: dict[str, str | None] | None = None) -> list[str]:
    paths = paths or tool_paths()
    return [name for name, path in paths.items() if not path]


def list_wifi_interfaces() -> list[dict[str, str]]:
    """Lista interfaces WiFi parseando `iw dev`.

    Formato típico:
        phy#0
            Interface wlan0
                ifindex 3
                type managed

    Si `iw` no devuelve nada (driver raro o sin adaptador), se usa un
    fallback leyendo /sys/class/net para no dejar la UI vacía.
    """
    interfaces: list[dict[str, str]] = []
    code, output = run_command(["iw", "dev"], timeout=6)

    if code == 0 and output:
        for block in output.split("Interface ")[1:]:
            lines = block.splitlines()
            if not lines:
                continue
            name = lines[0].strip()
            if not name:
                continue
            match = re.search(r"type\s+(\w+)", block)
            iface_type = match.group(1) if match else "desconocido"
            interfaces.append({"name": name, "type": iface_type})

    if not interfaces:
        net_dir = Path("/sys/class/net")
        if net_dir.exists():
            for entry in sorted(net_dir.iterdir()):
                # Un adaptador WiFi tiene el atributo "wireless" o "phy80211".
                if (entry / "wireless").exists() or (entry / "phy80211").exists():
                    interfaces.append({"name": entry.name, "type": "managed"})

    return interfaces


def detect_monitor_interface() -> str | None:
    """Devuelve el nombre de la primera interfaz en modo monitor, si existe."""
    code, output = run_command(["iw", "dev"], timeout=6)
    if code != 0 or not output:
        return None
    for block in output.split("Interface ")[1:]:
        lines = block.splitlines()
        if not lines:
            continue
        name = lines[0].strip()
        if re.search(r"type\s+monitor", block):
            return name
    return None


def restart_network_manager() -> tuple[int, str]:
    """Reinicia NetworkManager con systemctl y, si falla, con service."""
    if shutil.which("systemctl"):
        code, output = run_command(
            ["systemctl", "restart", "NetworkManager"], timeout=45
        )
        if code == 0:
            return code, output

    if shutil.which("service"):
        return run_command(["service", "NetworkManager", "restart"], timeout=45)

    return 1, "No se encontró systemctl ni service para reiniciar NetworkManager."


def sudo_relaunch_command() -> str:
    """Comando que el usuario puede copiar para relanzar la app como root."""
    from .constants import MAIN_SCRIPT

    return f"sudo -E python3 {MAIN_SCRIPT}"
