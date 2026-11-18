"""Pantalla 4: análisis del .cap con un diccionario mediante aircrack-ng."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ui.widgets import Banner, Card, LogView, PageHeader, StatusBadge


class AnalysisPage(QWidget):
    crack_requested = pyqtSignal(dict)
    stop_requested = pyqtSignal()
    wordlists_refresh_requested = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self._running = False
        self._has_result = False

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(
            "QScrollArea { background: transparent; border: none; }"
        )
        scroll.viewport().setStyleSheet("background: transparent;")
        content = QWidget()
        content.setObjectName("AnalysisContent")
        scroll.setWidget(content)
        outer.addWidget(scroll)

        layout = QVBoxLayout(content)
        layout.setContentsMargins(26, 24, 26, 24)
        layout.setSpacing(14)

        layout.addWidget(
            PageHeader(
                "4 · Análisis y recuperación",
                "aircrack-ng probará cada palabra del diccionario contra el "
                "handshake. El progreso y la clave encontrada se muestran en "
                "vivo.",
            )
        )

        files = Card()
        files_title = QLabel("Archivos de entrada")
        files_title.setObjectName("CardTitle")
        files.body.addWidget(files_title)

        self.cap_edit = QLineEdit()
        self.cap_edit.setPlaceholderText(
            "Ruta al archivo .cap capturado (ej. ~/wifi_audit_capturas/…)"
        )
        files.body.addLayout(
            self._file_row("Captura .cap", self.cap_edit, self._browse_cap)
        )

        self.wordlist_edit = QLineEdit()
        self.wordlist_edit.setPlaceholderText(
            "Ruta al diccionario .txt (ej. /usr/share/wordlists/rockyou.txt)"
        )
        files.body.addLayout(
            self._file_row(
                "Diccionario", self.wordlist_edit, self._browse_wordlist
            )
        )

        saved_row = QHBoxLayout()
        saved_row.setSpacing(10)
        saved_label = QLabel("Guardados")
        saved_label.setFixedWidth(120)
        self.saved_combo = QComboBox()
        self.saved_combo.currentIndexChanged.connect(
            self._on_saved_wordlist_selected
        )
        refresh_button = QPushButton("Actualizar")
        refresh_button.setObjectName("Ghost")
        refresh_button.clicked.connect(
            self.wordlists_refresh_requested.emit
        )
        saved_row.addWidget(saved_label)
        saved_row.addWidget(self.saved_combo, 1)
        saved_row.addWidget(refresh_button)
        files.body.addLayout(saved_row)

        bssid_row = QHBoxLayout()
        bssid_row.setSpacing(10)
        bssid_label = QLabel("BSSID")
        bssid_label.setFixedWidth(120)
        self.bssid_edit = QLineEdit()
        self.bssid_edit.setPlaceholderText(
            "Opcional: AA:BB:CC:DD:EE:FF (se rellena al capturar)"
        )
        bssid_row.addWidget(bssid_label)
        bssid_row.addWidget(self.bssid_edit, 1)
        files.body.addLayout(bssid_row)

        actions = QHBoxLayout()
        actions.setSpacing(10)
        self.crack_button = QPushButton("Crackear")
        self.crack_button.setObjectName("Primary")
        self.crack_button.clicked.connect(self._emit_crack)
        self.stop_button = QPushButton("Detener")
        self.stop_button.setObjectName("Danger")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_requested.emit)
        actions.addWidget(self.crack_button)
        actions.addWidget(self.stop_button)
        actions.addStretch(1)
        files.body.addLayout(actions)

        hint = QLabel(
            "Consejo: usa el .cap que acabas de capturar. Si el archivo "
            "contiene varias redes, el BSSID evita que aircrack-ng pregunte "
            "cuál analizar."
        )
        hint.setObjectName("Muted")
        hint.setWordWrap(True)
        files.body.addWidget(hint)

        layout.addWidget(files)

        progress_card = Card()
        progress_top = QHBoxLayout()
        progress_title = QLabel("Progreso del ataque")
        progress_title.setObjectName("CardTitle")
        self.status_badge = StatusBadge("EN ESPERA", "idle")
        progress_top.addWidget(progress_title)
        progress_top.addStretch(1)
        progress_top.addWidget(self.status_badge)
        progress_card.body.addLayout(progress_top)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        progress_card.body.addWidget(self.progress)

        stats = QHBoxLayout()
        stats.setSpacing(24)
        self.keys_label = QLabel("Claves: 0 / 0")
        self.speed_label = QLabel("Velocidad: 0 keys/s")
        for label in (self.keys_label, self.speed_label):
            label.setObjectName("Muted")
            stats.addWidget(label)
        stats.addStretch(1)
        progress_card.body.addLayout(stats)

        layout.addWidget(progress_card)

        self.banner = Banner()
        layout.addWidget(self.banner)

        log_card = Card()
        log_title = QLabel("Registro de aircrack-ng")
        log_title.setObjectName("CardTitle")
        log_card.body.addWidget(log_title)
        self.log_view = LogView(
            "La salida de aircrack-ng y el resultado final aparecerán aquí…"
        )
        self.log_view.setMinimumHeight(120)
        log_card.body.addWidget(self.log_view, 1)
        layout.addWidget(log_card, 1)

    # ------------------------------------------------------------------ API
    def set_cap(self, cap_path: str) -> None:
        self.cap_edit.setText(cap_path)

    def set_bssid(self, bssid: str) -> None:
        self.bssid_edit.setText(bssid)

    def set_saved_wordlists(self, dictionaries: list[dict]) -> None:
        current = self.saved_combo.currentData()
        self.saved_combo.blockSignals(True)
        self.saved_combo.clear()
        self.saved_combo.addItem("— Diccionario guardado —", "")
        for dictionary in dictionaries:
            self.saved_combo.addItem(
                f"{dictionary['name']} ({dictionary['count']:,} palabras)",
                dictionary["path"],
            )
        self.saved_combo.blockSignals(False)
        if current:
            index = self.saved_combo.findData(current)
            if index >= 0:
                self.saved_combo.setCurrentIndex(index)

    def set_wordlist(self, path: str) -> None:
        self.wordlist_edit.setText(path)

    def set_running(self, running: bool) -> None:
        self._running = running
        self.crack_button.setEnabled(not running)
        self.stop_button.setEnabled(running)
        self.cap_edit.setEnabled(not running)
        self.wordlist_edit.setEnabled(not running)
        self.saved_combo.setEnabled(not running)
        self.bssid_edit.setEnabled(not running)
        if running:
            self._has_result = False
            self.banner.hide()
            self.status_badge.set_status("busy", "ANALIZANDO")
            self.progress.setValue(0)
            self.keys_label.setText("Claves: 0 / 0")
            self.speed_label.setText("Velocidad: 0 keys/s")
        elif not self._has_result:
            self.status_badge.set_status("idle", "EN ESPERA")

    def set_progress(self, tested: int, total: int, speed: float) -> None:
        if total > 0:
            percent = min(100, int(tested * 100 / total))
            self.progress.setValue(percent)
        self.keys_label.setText(f"Claves: {tested:,} / {total:,}")
        self.speed_label.setText(f"Velocidad: {speed:,.0f} keys/s")

    def show_result(self, kind: str, key: str = "") -> None:
        self._has_result = True
        if kind == "found":
            self.progress.setValue(100)
            self.status_badge.set_status("ok", "CLAVE ENCONTRADA")
            self.banner.show_message(
                "success",
                "¡Clave encontrada!",
                f"Contraseña: {key}",
            )
        elif kind == "not_found":
            self.progress.setValue(100)
            self.status_badge.set_status("error", "NO ENCONTRADA")
            self.banner.show_message(
                "error",
                "Clave no encontrada",
                "El diccionario no contiene la contraseña de esta red. "
                "Prueba con otro diccionario.",
            )
        elif kind == "stopped":
            self.status_badge.set_status("warn", "DETENIDO")
            self.banner.show_message(
                "warning",
                "Análisis detenido",
                "El proceso se detuvo antes de terminar.",
            )
        elif kind == "timeout":
            self.status_badge.set_status("warn", "TIEMPO AGOTADO")
            self.banner.show_message(
                "warning",
                "Tiempo máximo alcanzado",
                "aircrack-ng se detuvo por seguridad. Puedes volver a "
                "intentarlo con un diccionario más pequeño.",
            )
        else:
            self.status_badge.set_status("error", "ERROR")
            self.banner.show_message(
                "error",
                "No se pudo completar el análisis",
                "Revisa el registro y comprueba que aircrack-ng está "
                "instalado.",
            )

    def append_log(self, text: str, level: str = "info") -> None:
        self.log_view.append(text, level)

    # ------------------------------------------------------------- internos
    def _on_saved_wordlist_selected(self, index: int) -> None:
        path = self.saved_combo.itemData(index)
        if path:
            self.wordlist_edit.setText(str(path))

    @staticmethod
    def _file_row(title: str, line_edit: QLineEdit, callback):
        row = QHBoxLayout()
        row.setSpacing(10)
        label = QLabel(title)
        label.setFixedWidth(120)
        button = QPushButton("Examinar…")
        button.setObjectName("Ghost")
        button.clicked.connect(callback)
        row.addWidget(label)
        row.addWidget(line_edit, 1)
        row.addWidget(button)
        return row

    def _browse_cap(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar captura",
            str(Path.home()),
            "Capturas (*.cap *.pcap *.ivs);;Todos los archivos (*)",
        )
        if path:
            self.cap_edit.setText(path)

    def _browse_wordlist(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar diccionario",
            str(Path.home()),
            "Diccionarios (*.txt *.lst *.dic);;Todos los archivos (*)",
        )
        if path:
            self.wordlist_edit.setText(path)

    def _emit_crack(self) -> None:
        cap = self.cap_edit.text().strip()
        wordlist = self.wordlist_edit.text().strip()

        if not cap or not Path(cap).is_file():
            QMessageBox.warning(
                self,
                "Falta la captura",
                "Selecciona un archivo .cap válido antes de continuar.",
            )
            return
        if not wordlist or not Path(wordlist).is_file():
            QMessageBox.warning(
                self,
                "Falta el diccionario",
                "Selecciona un diccionario .txt válido antes de continuar.",
            )
            return

        self.crack_requested.emit(
            {
                "cap": cap,
                "wordlist": wordlist,
                "bssid": self.bssid_edit.text().strip(),
            }
        )
