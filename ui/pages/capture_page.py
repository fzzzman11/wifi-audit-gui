"""Pantalla 3: captura del handshake y estado en vivo."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ui.widgets import Banner, Card, LogView, MetricCard, PageHeader, StatusBadge


class CapturePage(QWidget):
    start_requested = pyqtSignal(dict)
    stop_requested = pyqtSignal()
    analyze_requested = pyqtSignal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self._target: dict | None = None
        self._monitor_ready = False
        self._running = False
        self._cap_path = ""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 24, 26, 24)
        layout.setSpacing(14)

        layout.addWidget(
            PageHeader(
                "3 · Captura de handshake",
                "airodump-ng queda escuchando solo la red objetivo. Si marcas "
                "el deauth, aireplay-ng pedirá a los clientes que se "
                "reconecten.",
            )
        )

        target_card = Card()
        target_top = QHBoxLayout()
        target_title = QLabel("Objetivo seleccionado")
        target_title.setObjectName("CardTitle")
        self.target_badge = StatusBadge("SIN OBJETIVO", "idle")
        target_top.addWidget(target_title)
        target_top.addStretch(1)
        target_top.addWidget(self.target_badge)
        target_card.body.addLayout(target_top)

        target_grid = QHBoxLayout()
        target_grid.setSpacing(26)
        self.ssid_value = self._target_field("SSID")
        self.bssid_value = self._target_field("BSSID")
        self.channel_value = self._target_field("Canal")
        self.privacy_value = self._target_field("Cifrado")
        target_grid.addLayout(self.ssid_value[0])
        target_grid.addLayout(self.bssid_value[0])
        target_grid.addLayout(self.channel_value[0])
        target_grid.addLayout(self.privacy_value[0])
        target_grid.addStretch(1)
        target_card.body.addLayout(target_grid)

        layout.addWidget(target_card)

        controls = Card()
        row = QHBoxLayout()
        row.setSpacing(12)

        self.deauth_checkbox = QCheckBox(
            "Enviar deauth para forzar reconexión (10 paquetes)"
        )
        row.addWidget(self.deauth_checkbox)

        row.addSpacing(10)
        row.addWidget(QLabel("Tiempo máximo"))
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(30, 600)
        self.duration_spin.setValue(120)
        self.duration_spin.setSuffix(" s")
        self.duration_spin.setFixedWidth(95)
        row.addWidget(self.duration_spin)

        row.addStretch(1)

        self.start_button = QPushButton("Iniciar captura")
        self.start_button.setObjectName("Primary")
        self.start_button.setEnabled(False)
        self.start_button.clicked.connect(self._emit_start)
        row.addWidget(self.start_button)

        self.stop_button = QPushButton("Detener captura")
        self.stop_button.setObjectName("Danger")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_requested.emit)
        row.addWidget(self.stop_button)

        controls.body.addLayout(row)

        status_row = QHBoxLayout()
        self.status_badge = StatusBadge("CAPTURA DETENIDA", "idle")
        status_row.addWidget(self.status_badge)
        self.status_hint = QLabel(
            "Selecciona una red en la pantalla de escaneo para comenzar."
        )
        self.status_hint.setObjectName("Muted")
        self.status_hint.setWordWrap(True)
        status_row.addWidget(self.status_hint, 1)
        controls.body.addLayout(status_row)

        layout.addWidget(controls)

        metrics = QHBoxLayout()
        metrics.setSpacing(12)
        self.clients_metric = MetricCard("Clientes conectados", "0")
        self.packets_metric = MetricCard("Paquetes de datos", "0")
        self.time_metric = MetricCard("Tiempo transcurrido", "00:00")
        metrics.addWidget(self.clients_metric)
        metrics.addWidget(self.packets_metric)
        metrics.addWidget(self.time_metric)
        layout.addLayout(metrics)

        self.banner = Banner()
        self.banner.action_button.clicked.connect(self._emit_analyze)
        layout.addWidget(self.banner)

        log_card = Card()
        log_title = QLabel("Registro de la captura")
        log_title.setObjectName("CardTitle")
        log_card.body.addWidget(log_title)
        self.log_view = LogView(
            "Aquí verás los clientes detectados, el deauth y el handshake…"
        )
        log_card.body.addWidget(self.log_view, 1)
        layout.addWidget(log_card, 1)

    # ------------------------------------------------------------------ API
    def set_target(self, network: dict) -> None:
        self._target = network
        self.ssid_value[1].setText(network.get("essid") or "(oculto)")
        self.bssid_value[1].setText(network.get("bssid", "—"))
        self.channel_value[1].setText(str(network.get("channel_text", "?")))
        privacy = network.get("privacy") or "?"
        if privacy.upper() == "OPN":
            privacy = "Abierta"
        self.privacy_value[1].setText(privacy)

        ssid = network.get("essid") or "(oculto)"
        self.target_badge.set_status("ok", f"OBJETIVO · {ssid[:24]}")
        self.status_hint.setText(
            "Pulsa “Iniciar captura”. Puedes activar el deauth si la red "
            "tiene clientes conectados."
        )
        self.banner.hide()
        self._update_buttons()

    def clear_target(self) -> None:
        self._target = None
        for field in (
            self.ssid_value,
            self.bssid_value,
            self.channel_value,
            self.privacy_value,
        ):
            field[1].setText("—")
        self.target_badge.set_status("idle", "SIN OBJETIVO")
        self._update_buttons()

    def set_monitor_ready(self, ready: bool) -> None:
        self._monitor_ready = ready
        self._update_buttons()

    def set_deauth(self, enabled: bool) -> None:
        self.deauth_checkbox.setChecked(enabled)

    def options(self) -> dict:
        return {
            "deauth": self.deauth_checkbox.isChecked(),
            "duration": self.duration_spin.value(),
        }

    def set_running(self, running: bool) -> None:
        self._running = running
        self.start_button.setEnabled(
            not running and self._target is not None and self._monitor_ready
        )
        self.stop_button.setEnabled(running)
        self.deauth_checkbox.setEnabled(not running)
        self.duration_spin.setEnabled(not running)

        if running:
            self.banner.hide()
            self.status_badge.set_status("busy", "CAPTURA EN CURSO")
            self.status_hint.setText(
                "Escuchando la red objetivo. El proceso se detendrá solo al "
                "capturar el handshake o al agotarse el tiempo."
            )
            self.clients_metric.set_value("0")
            self.packets_metric.set_value("0")
            self.time_metric.set_value("00:00")
            self._cap_path = ""
        elif self._cap_path:
            self.status_badge.set_status("ok", "HANDSHAKE CAPTURADO")
        else:
            self.status_badge.set_status("idle", "CAPTURA DETENIDA")
        self._update_buttons()

    def update_status(self, data: dict) -> None:
        self.clients_metric.set_value(str(data.get("clients", 0)))
        self.packets_metric.set_value(str(data.get("packets", 0)))
        elapsed = int(data.get("elapsed", 0))
        self.time_metric.set_value(
            f"{elapsed // 60:02d}:{elapsed % 60:02d}"
        )
        if data.get("handshake"):
            self.status_badge.set_status("ok", "HANDSHAKE DETECTADO")

    def show_handshake(self, cap_path: str) -> None:
        self._cap_path = cap_path
        self.status_badge.set_status("ok", "HANDSHAKE CAPTURADO")
        self.status_hint.setText(
            "Captura completada. Puedes pasar a la pantalla de análisis."
        )
        self.banner.show_message(
            "success",
            "¡Handshake capturado!",
            f"Archivo guardado en: {cap_path}",
            "Ir a análisis",
        )

    def append_log(self, text: str, level: str = "info") -> None:
        self.log_view.append(text, level)

    # ------------------------------------------------------------- internos
    @staticmethod
    def _target_field(title: str):
        layout = QVBoxLayout()
        layout.setSpacing(2)
        label = QLabel(title)
        label.setObjectName("MetricTitle")
        value = QLabel("—")
        value.setObjectName("Value")
        value.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        layout.addWidget(label)
        layout.addWidget(value)
        return layout, value

    def _update_buttons(self) -> None:
        self.start_button.setEnabled(
            not self._running
            and self._target is not None
            and self._monitor_ready
        )

    def _emit_start(self) -> None:
        if self._target is not None:
            self.start_requested.emit(self.options())

    def _emit_analyze(self) -> None:
        if self._cap_path:
            self.analyze_requested.emit(self._cap_path)
