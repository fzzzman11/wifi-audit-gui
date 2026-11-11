"""Pantalla 1: selección de interfaz y activación del modo monitor."""

from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ui.widgets import Card, LogView, PageHeader, StatusBadge


class InterfacePage(QWidget):
    refresh_requested = pyqtSignal()
    activate_requested = pyqtSignal(str)
    deactivate_requested = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self._interfaces: list[dict[str, str]] = []
        self._monitor_active = False
        self._busy = False
        self._root_ok = True

        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 24, 26, 24)
        layout.setSpacing(16)

        layout.addWidget(
            PageHeader(
                "1 · Interfaz y modo monitor",
                "Elige el adaptador WiFi y actívalo en modo monitor. "
                "airmon-ng detendrá temporalmente NetworkManager.",
            )
        )

        adapter = Card()
        top = QHBoxLayout()
        card_title = QLabel("Adaptador WiFi")
        card_title.setObjectName("CardTitle")
        self.badge = StatusBadge("Modo monitor: INACTIVO", "idle")
        top.addWidget(card_title)
        top.addStretch(1)
        top.addWidget(self.badge)
        adapter.body.addLayout(top)

        form = QHBoxLayout()
        form.setSpacing(10)
        form.addWidget(QLabel("Interfaz"))
        self.interface_combo = QComboBox()
        self.interface_combo.setMinimumWidth(280)
        self.interface_combo.currentIndexChanged.connect(
            self._on_interface_changed
        )
        form.addWidget(self.interface_combo, 1)

        self.refresh_button = QPushButton("Actualizar")
        self.refresh_button.setObjectName("Ghost")
        self.refresh_button.clicked.connect(self.refresh_requested.emit)
        form.addWidget(self.refresh_button)
        adapter.body.addLayout(form)

        self.info_label = QLabel(
            "Selecciona una interfaz para ver su estado."
        )
        self.info_label.setObjectName("Muted")
        self.info_label.setWordWrap(True)
        adapter.body.addWidget(self.info_label)

        actions = QHBoxLayout()
        actions.setSpacing(10)
        self.activate_button = QPushButton("Activar modo monitor")
        self.activate_button.setObjectName("Primary")
        self.activate_button.clicked.connect(self._emit_activate)

        self.deactivate_button = QPushButton("Restaurar modo managed")
        self.deactivate_button.setObjectName("Ghost")
        self.deactivate_button.clicked.connect(
            self.deactivate_requested.emit
        )

        actions.addWidget(self.activate_button)
        actions.addWidget(self.deactivate_button)
        actions.addStretch(1)
        adapter.body.addLayout(actions)

        hint = QLabel(
            "Consejo para el TP-Link TL-WN722N v4 (RTL8188EUS): si airmon-ng "
            "no crea una interfaz terminada en “mon”, revisa que el driver "
            "rtl8188eus esté cargado y que no haya otro proceso usando la "
            "interfaz."
        )
        hint.setObjectName("Muted")
        hint.setWordWrap(True)
        adapter.body.addWidget(hint)

        layout.addWidget(adapter)

        log_card = Card()
        log_title = QLabel("Registro de airmon-ng")
        log_title.setObjectName("CardTitle")
        log_card.body.addWidget(log_title)
        self.log_view = LogView(
            "Aquí aparecerá la salida de airmon-ng check kill y airmon-ng start…"
        )
        log_card.body.addWidget(self.log_view, 1)
        layout.addWidget(log_card, 1)

        self.set_interfaces([])

    # ------------------------------------------------------------------ API
    def current_interface(self) -> str | None:
        return self.interface_combo.currentData()

    def set_interfaces(self, interfaces: list[dict[str, str]]) -> None:
        self._interfaces = interfaces
        self.interface_combo.blockSignals(True)
        self.interface_combo.clear()

        if interfaces:
            for iface in interfaces:
                self.interface_combo.addItem(
                    f"{iface['name']}  ·  {iface['type']}",
                    iface["name"],
                )
        else:
            self.interface_combo.addItem(
                "No se detectó interfaz WiFi", None
            )

        self.interface_combo.blockSignals(False)
        self.interface_combo.setEnabled(
            bool(interfaces) and not self._monitor_active and not self._busy
        )
        self._update_action_state()
        self._on_interface_changed()

    def set_monitor_state(
        self, active: bool, interface: str | None = None
    ) -> None:
        self._monitor_active = active
        if active:
            self.badge.set_status(
                "ok", f"Modo monitor: ACTIVO · {interface or ''}".strip()
            )
        else:
            self.badge.set_status("idle", "Modo monitor: INACTIVO")
        self._update_action_state()

    def set_busy(self, busy: bool, message: str | None = None) -> None:
        self._busy = busy
        if busy:
            self.badge.set_status(
                "busy", message or "Activando modo monitor…"
            )
        elif self._monitor_active:
            self.badge.set_status("ok", "Modo monitor: ACTIVO")
        else:
            self.badge.set_status("idle", "Modo monitor: INACTIVO")
        self._update_action_state()

    def set_root_enabled(self, root_ok: bool) -> None:
        self._root_ok = root_ok
        self._update_action_state()

    def append_log(self, text: str, level: str = "info") -> None:
        self.log_view.append(text, level)

    # ------------------------------------------------------------- internos
    def _on_interface_changed(self) -> None:
        iface = next(
            (
                item
                for item in self._interfaces
                if item["name"] == self.interface_combo.currentData()
            ),
            None,
        )
        if iface is None:
            self.info_label.setText(
                "No se detectó ninguna interfaz WiFi. Conecta el adaptador y "
                "pulsa Actualizar."
            )
        elif iface["type"] == "monitor":
            self.info_label.setText(
                f"{iface['name']} ya está en modo monitor."
            )
        else:
            self.info_label.setText(
                f"{iface['name']} está en modo {iface['type']}. "
                "Pulsa “Activar modo monitor” para comenzar."
            )
        self._update_action_state()

    def _update_action_state(self) -> None:
        has_interface = bool(self._interfaces)
        self.activate_button.setEnabled(
            has_interface
            and not self._monitor_active
            and not self._busy
            and self._root_ok
        )
        self.deactivate_button.setEnabled(
            self._monitor_active and not self._busy
        )
        self.interface_combo.setEnabled(
            has_interface and not self._monitor_active and not self._busy
        )
        self.refresh_button.setEnabled(not self._busy)

    def _emit_activate(self) -> None:
        interface = self.current_interface()
        if interface:
            self.activate_requested.emit(interface)
