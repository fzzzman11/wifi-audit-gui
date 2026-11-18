"""Parseo de las salidas de airodump-ng y aircrack-ng.

Se mantiene separado de los workers para poder probar las funciones con
archivos de ejemplo sin lanzar procesos reales.
"""

from __future__ import annotations

import re
from pathlib import Path

# Dirección MAC: 6 pares hexadecimales separados por ':' o '-'.
MAC_RE = re.compile(r"^(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}$")

# airodump-ng escribe "WPA handshake: AA:BB:CC:DD:EE:FF" en la cabecera.
HANDSHAKE_RE = re.compile(r"WPA handshake:\s*([0-9A-Fa-f:]{17})", re.IGNORECASE)

# Progreso de aircrack-ng: "12345/1000000 keys tested (1234.56 k/s)".
KEYS_RE = re.compile(r"(\d+)\s*/\s*(\d+)\s+keys tested", re.IGNORECASE)
SPEED_RE = re.compile(r"([\d.]+)\s*k/s", re.IGNORECASE)
KEY_FOUND_RE = re.compile(r"KEY FOUND!\s*\[\s*(.*?)\s*\]", re.IGNORECASE)


def signal_level(dbm: int) -> int:
    """Convierte dBm a una intensidad de 0 a 4 barras.

    Valores orientativos: -50 excelente, -60 bueno, -70 aceptable,
    -80 débil y por debajo de -80 muy débil.
    """
    if dbm >= -50:
        return 4
    if dbm >= -60:
        return 3
    if dbm >= -70:
        return 2
    if dbm >= -80:
        return 1
    return 0


def parse_airodump_csv(csv_path: str | Path) -> list[dict]:
    """Extrae los access points del CSV que genera airodump-ng.

    El CSV contiene dos tablas: la primera de APs y la segunda de clientes.
    Solo nos interesa la primera, que termina en la primera línea vacía.

    Columnas del CSV de airodump-ng:
      0 BSSID | 1 First seen | 2 Last seen | 3 channel | 4 Speed |
      5 Privacy | 6 Cipher | 7 Authentication | 8 Power | 9 Beacons |
      10 #IV | 11 LAN IP | 12 ID-length | 13 ESSID | 14 Key
    """
    path = Path(csv_path)
    if not path.exists():
        return []

    try:
        raw = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []

    networks: list[dict] = []
    seen: set[str] = set()
    in_ap_table = False

    for line in raw.replace("\x00", "").splitlines():
        stripped = line.strip()
        if not stripped:
            if in_ap_table:
                break
            continue

        if stripped.upper().startswith("BSSID"):
            in_ap_table = True
            continue
        if not in_ap_table:
            continue

        # split(..., 13) conserva las comas internas del ESSID en la parte 13.
        parts = line.split(",", 13)
        if len(parts) < 14:
            continue

        # La última columna del CSV es "Key" (casi siempre vacía) y va justo
        # después del ESSID. Solo se descarta si está vacía, para no romper
        # ESSIDs con coma ni CSVs antiguos sin esa columna.
        essid_field = parts[13]
        if "," in essid_field:
            head, tail = essid_field.rsplit(",", 1)
            if not tail.strip():
                essid_field = head

        bssid = parts[0].strip()
        if not MAC_RE.match(bssid) or bssid.upper() in seen:
            continue

        channel = parts[3].strip()
        privacy = parts[5].strip()
        auth = parts[7].strip()
        power_raw = parts[8].strip()

        try:
            power = int(power_raw)
        except ValueError:
            power = -100

        try:
            channel_num = int(channel)
        except ValueError:
            channel_num = 0

        seen.add(bssid.upper())
        networks.append(
            {
                "bssid": bssid,
                "channel": channel_num,
                "channel_text": channel or "?",
                "privacy": privacy or "?",
                "auth": auth,
                "cipher": parts[6].strip(),
                "power": power,
                "essid": essid_field.strip().strip("\x00") or "(oculto)",
                "hidden": not bool(essid_field.strip()),
            }
        )

    return networks


def parse_capture_line(
    line: str,
    bssid: str,
    clients: set[str],
) -> tuple[int | None, str | None]:
    """Interpreta una línea de la salida de airodump-ng durante la captura.

    Devuelve (paquetes_de_datos, mac_del_handshake). `clients` se modifica
    in-place con los clientes detectados para esa BSSID.
    """
    text = line.strip()
    if not text:
        return None, None

    handshake_match = HANDSHAKE_RE.search(text)
    handshake_mac = handshake_match.group(1) if handshake_match else None

    packets: int | None = None
    upper_bssid = bssid.upper()

    # Línea de la tabla de APs: BSSID PWR RXQ Beacons #Data #/s CH ...
    if text.upper().startswith(upper_bssid):
        fields = text.split()
        # En versiones recientes #Data es el campo 4; en otras el 3.
        for index in (4, 3):
            if len(fields) > index and fields[index].isdigit():
                packets = int(fields[index])
                break

    # Línea de la tabla de estaciones: contiene MACs. Si aparece la BSSID
    # objetivo, cualquier otra MAC de la línea es un cliente conectado.
    macs = re.findall(r"(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}", text)
    if macs:
        upper_macs = [m.upper() for m in macs]
        if upper_bssid in upper_macs:
            for mac in upper_macs:
                if mac != upper_bssid:
                    clients.add(mac)

    return packets, handshake_mac


def parse_aircrack_progress(line: str) -> tuple[int, int, float] | None:
    """Devuelve (probadas, total, velocidad) si la línea es de progreso."""
    match = KEYS_RE.search(line)
    if not match:
        return None
    tested = int(match.group(1))
    total = int(match.group(2))
    speed_match = SPEED_RE.search(line)
    speed = float(speed_match.group(1)) if speed_match else 0.0
    return tested, total, speed


def extract_found_key(line: str) -> str | None:
    match = KEY_FOUND_RE.search(line)
    return match.group(1) if match else None


def count_lines(path: str | Path) -> int:
    """Cuenta líneas de un diccionario para poder mostrar el progreso."""
    total = 0
    try:
        with open(path, "rb") as handle:
            while True:
                chunk = handle.read(1024 * 1024)
                if not chunk:
                    break
                total += chunk.count(b"\n")
    except OSError:
        return 0
    return max(total, 1)
