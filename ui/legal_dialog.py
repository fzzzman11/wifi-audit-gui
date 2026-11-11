"""Diálogo modal de advertencia legal y confirmación de autorización."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from core.tools import sudo_relaunch_command

from .widgets import Card, rgba


class LegalDialog(QDialog):
    """Obliga a aceptar el aviso legal antes de habilitar la aplicación.

    Si el usuario cierra el diálogo o pulsa "Salir", `exec()` devuelve
    Rejected y main.py termina sin abrir la ventana principal.
    """

    def __init__(self, running_as_root: bool, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Uso responsable · WiFi Audit Lab")
        self.setModal(True)
        self.setMinimumWidth(640)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 24, 26, 22)
        layout.setSpacing(16)

        eyebrow = QLabel("LABORATORIO AUTORIZADO")
        eyebrow.setStyleSheet(
            f"color: {rgba('#22d3ee', 0.9)}; font-size: 11px; "
            "font-weight: 700; letter-spacing: 1px;"
        )
        title = QLabel("Antes de comenzar")
        title.setObjectName("PageTitle")
        subtitle = QLabel(
            "Esta herramienta automatiza la suite aircrack-ng para prácticas "
            "de auditoría WiFi. Debes leer y aceptar las condiciones."
        )
        subtitle.setObjectName("PageSubtitle")
        subtitle.setWordWrap(True)

        warning = Card()
        warning.setStyleSheet(
            "QFrame#Card {"
            "background: #2a200c;"
            "border: 1px solid #7c5a12;"
            "border-radius: 14px;"
            "}"
        )
        warning_title = QLabel("⚠  Uso exclusivamente educativo")
        warning_title.setStyleSheet(
            "color: #fbbf24; font-size: 15px; font-weight: 700;"
        )
        warning_text = QLabel(
            "Usa esta aplicación únicamente contra redes de tu propiedad o "
            "sobre las que tengas autorización explícita y por escrito "
            "(por ejemplo, el router de tu laboratorio de clase).\n\n"
            "Capturar handshakes, enviar paquetes deauth o probar "
            "diccionarios contra redes de terceros puede constituir un "
            "delito en la mayoría de los países. El autor no se hace "
            "responsable del uso indebido de esta herramienta."
        )
        warning_text.setWordWrap(True)
        warning_text.setStyleSheet("color: #e8dcc0;")
        warning.body.addWidget(warning_title)
        warning.body.addWidget(warning_text)

        steps = Card()
        steps_title = QLabel("Qué hará la aplicación")
        steps_title.setObjectName("CardTitle")
        steps_text = QLabel(
            "1. Poner tu adaptador en modo monitor con airmon-ng.\n"
            "2. Escanear redes cercanas con airodump-ng.\n"
            "3. Capturar el handshake WPA/WPA2 de la red que elijas.\n"
            "4. Probar un diccionario con aircrack-ng y restaurar la "
            "interfaz al terminar."
        )
        steps_text.setWordWrap(True)
        steps_text.setStyleSheet("color: #a9bccf;")
        steps.body.addWidget(steps_title)
        steps.body.addWidget(steps_text)

        if running_as_root:
            root_label = QLabel("✓  Privilegios root detectados")
            root_color = "#22c55e"
        else:
            root_label = QLabel(
                "⚠  Sin privilegios root: podrás explorar la interfaz, pero "
                "las operaciones de red estarán deshabilitadas.\n"
                f"Relanza con:  {sudo_relaunch_command()}"
            )
            root_color = "#f59e0b"
        root_label.setWordWrap(True)
        root_label.setStyleSheet(
            f"color: {root_color}; background: #111a24; "
            "border: 1px solid #1d2b3a; border-radius: 10px; padding: 10px;"
        )

        self._checkbox = QCheckBox(
            "Confirmo que tengo autorización para auditar la red objetivo"
        )
        self._checkbox.setStyleSheet("font-weight: 600; color: #eaf4fd;")

        buttons = QHBoxLayout()
        buttons.addStretch(1)

        exit_button = QPushButton("Salir")
        exit_button.setObjectName("Ghost")
        exit_button.clicked.connect(self.reject)

        self._accept_button = QPushButton("Aceptar y continuar")
        self._accept_button.setObjectName("Primary")
        self._accept_button.setEnabled(False)
        self._accept_button.clicked.connect(self.accept)

        buttons.addWidget(exit_button)
        buttons.addWidget(self._accept_button)

        self._checkbox.toggled.connect(self._accept_button.setEnabled)

        layout.addWidget(eyebrow)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(warning)
        layout.addWidget(steps)
        layout.addWidget(root_label)
        layout.addWidget(self._checkbox)
        layout.addLayout(buttons)

    def authorization_confirmed(self) -> bool:
        return self._checkbox.isChecked()
