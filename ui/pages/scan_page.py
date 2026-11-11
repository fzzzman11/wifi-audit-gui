"""Pantalla 2: escaneo de redes y tabla de resultados."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ui.widgets import (
    Card,
    LogView,
    NumericItem,
    PageHeader,
    SignalDelegate,
)


class ScanPage(QWidget):
    scan_requested = pyqtSignal(int, str)  # duración, banda
    stop_requested = pyqtSignal()
    capture_requested = pyqtSignal(dict)

    COLUMNS = ["SSID", "BSSID", "Canal", "Cifrado", "Señal"]

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self._by_bssid: dict[str, dict] = {}
        self._scanning = False
        self._monitor_ready = False
        self._auto_sorted = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 24, 26, 24)
        layout.setSpacing(16)

        layout.addWidget(
            PageHeader(
                "2 · Escaneo de redes",
                "airodump-ng escucha los canales seleccionados y la tabla se "
                "actualiza en vivo. Al finalizar puedes ordenar por cualquier "
                "columna.",
            )
        )

        controls = Card()
        row = QHBoxLayout()
        row.setSpacing(10)

        row.addWidget(QLabel("Duración"))
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(10, 180)
        self.duration_spin.setValue(30)
        self.duration_spin.setSuffix(" s")
        self.duration_spin.setFixedWidth(90)
        row.addWidget(self.duration_spin)

        row.addSpacing(8)
        row.addWidget(QLabel("Banda"))
        self.band_combo = QComboBox()
        self.band_combo.addItem("2.4 GHz", "bg")
        self.band_combo.addItem("5 GHz", "a")
        self.band_combo.addItem("2.4 + 5 GHz", "abg")
        self.band_combo.setFixedWidth(150)
        row.addWidget(self.band_combo)

        row.addStretch(1)

        self.scan_button = QPushButton("Escanear redes")
        self.scan_button.setObjectName("Primary")
        self.scan_button.clicked.connect(self._emit_scan)
        row.addWidget(self.scan_button)

        self.stop_button = QPushButton("Detener")
        self.stop_button.setObjectName("Danger")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_requested.emit)
        row.addWidget(self.stop_button)

        controls.body.addLayout(row)

        progress_row = QHBoxLayout()
        progress_row.setSpacing(12)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        self.status_label = QLabel("Listo para escanear.")
        self.status_label.setObjectName("Muted")
        self.status_label.setMinimumWidth(220)
        progress_row.addWidget(self.progress, 1)
        progress_row.addWidget(self.status_label)
        controls.body.addLayout(progress_row)

        self.hint_label = QLabel(
            "Activa el modo monitor en la pantalla 1 para habilitar el escaneo."
        )
        self.hint_label.setObjectName("Muted")
        self.hint_label.setWordWrap(True)
        controls.body.addWidget(self.hint_label)

        layout.addWidget(controls)

        table_card = Card()
        table_top = QHBoxLayout()
        table_title = QLabel("Redes detectadas")
        table_title.setObjectName("CardTitle")
        self.count_label = QLabel("0 redes")
        self.count_label.setObjectName("Muted")
        table_top.addWidget(table_title)
        table_top.addSpacing(10)
        table_top.addWidget(self.count_label)
        table_top.addStretch(1)
        table_card.body.addLayout(table_top)

        self.table = QTableWidget(0, len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels(self.COLUMNS)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(False)
        self.table.setShowGrid(False)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for column in range(1, len(self.COLUMNS)):
            header.setSectionResizeMode(
                column, QHeaderView.ResizeMode.ResizeToContents
            )
        self.table.setItemDelegateForColumn(4, SignalDelegate(self.table))
        self.table.itemSelectionChanged.connect(self._update_capture_button)
        self.table.cellDoubleClicked.connect(self._on_double_click)

        table_card.body.addWidget(self.table, 1)

        bottom = QHBoxLayout()
        self.selection_hint = QLabel(
            "Selecciona una fila para capturar su handshake."
        )
        self.selection_hint.setObjectName("Muted")
        bottom.addWidget(self.selection_hint)
        bottom.addStretch(1)

        self.capture_button = QPushButton("Capturar handshake")
        self.capture_button.setObjectName("Primary")
        self.capture_button.setEnabled(False)
        self.capture_button.clicked.connect(self._emit_capture)
        bottom.addWidget(self.capture_button)
        table_card.body.addLayout(bottom)

        layout.addWidget(table_card, 1)

        log_card = Card()
        log_title = QLabel("Registro de airodump-ng")
        log_title.setObjectName("CardTitle")
        log_card.body.addWidget(log_title)
        self.log_view = LogView(
            "La salida del escaneo y los errores aparecerán aquí…"
        )
        self.log_view.setMinimumHeight(90)
        self.log_view.setMaximumHeight(140)
        log_card.body.addWidget(self.log_view)
        layout.addWidget(log_card)

    # ------------------------------------------------------------------ API
    def set_monitor_ready(self, ready: bool) -> None:
        self._monitor_ready = ready
        self.scan_button.setEnabled(ready and not self._scanning)
        if ready:
            self.hint_label.setText(
                "El adaptador está en modo monitor. Elige la duración y pulsa "
                "Escanear redes."
            )
        else:
            self.hint_label.setText(
                "Activa el modo monitor en la pantalla 1 para habilitar el "
                "escaneo."
            )
        self._update_capture_button()

    def set_scanning(self, scanning: bool) -> None:
        self._scanning = scanning
        self.scan_button.setEnabled(self._monitor_ready and not scanning)
        self.stop_button.setEnabled(scanning)
        self.duration_spin.setEnabled(not scanning)
        self.band_combo.setEnabled(not scanning)

        if scanning:
            self.progress.setValue(0)
            self.status_label.setText("Iniciando escaneo…")
            self.table.setSortingEnabled(False)
        else:
            self.progress.setValue(100)
            self.table.setSortingEnabled(True)
            if self.table.rowCount() > 0 and not self._auto_sorted:
                self.table.sortItems(4, Qt.SortOrder.DescendingOrder)
                self._auto_sorted = True
        self._update_capture_button()

    def set_progress(self, elapsed: int, total: int) -> None:
        if total <= 0:
            return
        percent = min(100, int(elapsed * 100 / total))
        self.progress.setValue(percent)
        if self._scanning:
            self.status_label.setText(
                f"Escaneando… {elapsed}s / {total}s"
            )

    def set_status(self, text: str) -> None:
        self.status_label.setText(text)

    def clear_results(self) -> None:
        self.table.setRowCount(0)
        self._by_bssid.clear()
        self.count_label.setText("0 redes")
        self.progress.setValue(0)
        self.status_label.setText("Listo para escanear.")
        self._auto_sorted = False
        self.table.setSortingEnabled(False)
        self._update_capture_button()

    def set_networks(self, networks: list[dict]) -> None:
        self._by_bssid = {network["bssid"]: network for network in networks}
        self.table.setSortingEnabled(False)

        existing: dict[str, int] = {}
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 1)
            if item is not None:
                existing[item.text()] = row

        for network in networks:
            row = existing.get(network["bssid"])
            if row is None:
                row = self.table.rowCount()
                self.table.insertRow(row)
            self._fill_row(row, network)

        self.count_label.setText(f"{len(networks)} redes")
        self._update_capture_button()

    def append_log(self, text: str, level: str = "info") -> None:
        self.log_view.append(text, level)

    def selected_network(self) -> dict | None:
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 1)
        if item is None:
            return None
        return self._by_bssid.get(item.text())

    # ------------------------------------------------------------- internos
    def _fill_row(self, row: int, network: dict) -> None:
        privacy = network.get("privacy") or "?"
        if privacy.upper() == "OPN":
            privacy = "Abierta"

        ssid_item = QTableWidgetItem(network.get("essid") or "(oculto)")
        bssid_item = QTableWidgetItem(network.get("bssid", ""))
        channel_item = NumericItem(
            str(network.get("channel_text", "?")),
            float(network.get("channel", 0)),
        )
        privacy_item = QTableWidgetItem(privacy)
        signal_item = NumericItem("", float(network.get("power", -100)))
        signal_item.setToolTip(f"Señal: {network.get('power', -100)} dBm")

        items = [
            ssid_item,
            bssid_item,
            channel_item,
            privacy_item,
            signal_item,
        ]
        for column, item in enumerate(items):
            self.table.setItem(row, column, item)

    def _emit_scan(self) -> None:
        self.scan_requested.emit(
            self.duration_spin.value(), self.band_combo.currentData()
        )

    def _emit_capture(self) -> None:
        network = self.selected_network()
        if network:
            self.capture_requested.emit(network)

    def _on_double_click(self, row: int, _column: int) -> None:
        self.table.selectRow(row)
        self._emit_capture()

    def _update_capture_button(self) -> None:
        has_selection = self.selected_network() is not None
        self.capture_button.setEnabled(
            has_selection and not self._scanning and self._monitor_ready
        )
