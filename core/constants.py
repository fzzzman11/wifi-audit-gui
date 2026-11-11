"""Constantes compartidas por el núcleo y la interfaz."""

from pathlib import Path

APP_NAME = "WiFi Audit Lab"
APP_VERSION = "1.0.0"

# Todas las capturas y CSV temporales se guardan aquí para que el alumno
# pueda adjuntarlos fácilmente en el informe de laboratorio.
OUTPUT_DIR = Path.home() / "wifi_audit_capturas"

# Herramientas externas que la aplicación necesita. Se comprueban al arrancar.
REQUIRED_TOOLS = [
    "airmon-ng",
    "airodump-ng",
    "aireplay-ng",
    "aircrack-ng",
    "iw",
]

# Directorio del proyecto (para mensajes de ayuda y relanzar como root).
PROJECT_DIR = Path(__file__).resolve().parent.parent
MAIN_SCRIPT = PROJECT_DIR / "main.py"
