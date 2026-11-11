#!/usr/bin/env python3
"""WiFi Audit Lab · punto de entrada.

Ejecuta:
    sudo -E python3 main.py

La aplicación es una interfaz gráfica para la suite aircrack-ng, pensada
exclusivamente para prácticas de laboratorio sobre redes propias o con
autorización explícita.
"""

from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication, QDialog

from core.constants import APP_NAME, APP_VERSION
from core.tools import is_root
from ui.legal_dialog import LegalDialog
from ui.main_window import MainWindow
from ui.theme import apply_theme


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName("Laboratorio de Ciberseguridad")
    apply_theme(app)

    # 1) Aviso legal obligatorio: sin aceptar el checkbox no se abre la app.
    legal = LegalDialog(running_as_root=is_root())
    if (
        legal.exec() != QDialog.DialogCode.Accepted
        or not legal.authorization_confirmed()
    ):
        return 0

    # 2) Ventana principal. Ella comprueba root, herramientas e interfaces.
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
