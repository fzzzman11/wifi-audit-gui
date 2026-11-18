"""Núcleo de la aplicación: llamadas a las herramientas y parseo de salidas.

Este paquete no contiene código de interfaz gráfica. Su única responsabilidad
es ejecutar airmon-ng, airodump-ng, aireplay-ng y aircrack-ng de forma segura
y convertir sus salidas en estructuras de datos fáciles de pintar en la UI.
"""

__all__ = [
    "capture",
    "constants",
    "cracker",
    "monitor",
    "parsers",
    "process",
    "scanner",
    "tools",
]
