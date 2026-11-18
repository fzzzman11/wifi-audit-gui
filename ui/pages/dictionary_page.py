"""Pantalla 5: creación y gestión de diccionarios personalizados."""

from __future__ import annotations

import itertools
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.wordlist import (
    RULE_LABELS,
    clean_words,
    delete_wordlist,
    list_wordlists,
    wordlist_path,
)
from ui.widgets import Banner, Card, LogView, PageHeader, StatusBadge

RULE_DEFAULTS = {
    "original": True,
    "capitalize": True,
    "upper": False,
    "leet": False,
    "years": True,
    "numbers": True,
    "symbols": False,
}


class DictionaryPage(QWidget):
    generation_requested = pyqtSignal(str, str, dict, int)
    stop_requested = pyqtSignal()
    use_in_analysis = pyqtSignal(str)
    dictionaries_changed = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self._generating = False
        self._result_reported = False
        self._rule_boxes: dict[str, QCheckBox] = {}

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
        content.setObjectName("DictionaryContent")
        scroll.setWidget(content)
        outer.addWidget(scroll)

        layout = QVBoxLayout(content)
        layout.setContentsMargins(26, 24, 26, 24)
        layout.setSpacing(12)

        layout.addWidget(
            PageHeader(
                "5 · Diccionarios personalizados",
                "Escribe palabras propias (nombres, fechas, palabras del "
                "laboratorio…) y genera un diccionario con las variaciones "
                "que elijas. El límite controla cuántas palabras se guardan.",
            )
        )

        builder = Card()
        title = QLabel("Nuevo diccionario")
        title.setObjectName("CardTitle")
        builder.body.addWidget(title)

        name_row = QHBoxLayout()
        name_row.setSpacing(10)
        name_label = QLabel("Nombre")
        name_label.setFixedWidth(70)
        name_row.addWidget(name_label)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("ej. diccionario_laboratorio")
        name_row.addWidget(self.name_edit, 1)
        name_row.addSpacing(10)
        limit_label = QLabel("Límite")
        limit_label.setFixedWidth(50)
        name_row.addWidget(limit_label)
        self.limit_spin = QSpinBox()
        self.limit_spin.setRange(1, 500000)
        self.limit_spin.setValue(2000)
        self.limit_spin.setSuffix(" palabras")
        self.limit_spin.setFixedWidth(150)
        name_row.addWidget(self.limit_spin)
        builder.body.addLayout(name_row)

        builder.body.addWidget(
            QLabel("Palabras base (una por línea)")
        )
        self.words_edit = QPlainTextEdit()
        self.words_edit.setPlaceholderText(
            "gato\nrouter\n2024\nmiRed\n..."
        )
        self.words_edit.setMinimumHeight(80)
        builder.body.addWidget(self.words_edit)

        rules_title = QLabel("Variaciones a generar")
        rules_title.setObjectName("Muted")
        builder.body.addWidget(rules_title)
        rules_grid = QGridLayout()
        rules_grid.setHorizontalSpacing(14)
        rules_grid.setVerticalSpacing(8)
        for index, (key, label) in enumerate(RULE_LABELS.items()):
            checkbox = QCheckBox(label)
            checkbox.setChecked(RULE_DEFAULTS.get(key, False))
            self._rule_boxes[key] = checkbox
            rules_grid.addWidget(checkbox, index // 3, index % 3)
        builder.body.addLayout(rules_grid)

        actions = QHBoxLayout()
        actions.setSpacing(10)
        self.generate_button = QPushButton("Generar y guardar")
        self.generate_button.setObjectName("Primary")
        self.generate_button.clicked.connect(self._emit_generate)
        self.stop_button = QPushButton("Detener")
        self.stop_button.setObjectName("Danger")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_requested.emit)
        self.status_badge = StatusBadge("EN ESPERA", "idle")
        actions.addWidget(self.generate_button)
        actions.addWidget(self.stop_button)
        actions.addStretch(1)
        actions.addWidget(self.status_badge)
        builder.body.addLayout(actions)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        builder.body.addWidget(self.progress)

        self.banner = Banner()
        self._banner_path: str | None = None
        self.banner.action_button.clicked.connect(
            self._use_banner_dictionary
        )
        builder.body.addWidget(self.banner)

        self.log_view = LogView(
            "El resultado de la generación aparecerá aquí…"
        )
        self.log_view.setMinimumHeight(80)
        builder.body.addWidget(self.log_view)
        layout.addWidget(builder)

        saved = Card()
        saved_top = QHBoxLayout()
        saved_title = QLabel("Diccionarios guardados")
        saved_title.setObjectName("CardTitle")
        self.count_label = QLabel("0 diccionarios")
        self.count_label.setObjectName("Muted")
        saved_top.addWidget(saved_title)
        saved_top.addStretch(1)
        saved_top.addWidget(self.count_label)
        saved.body.addLayout(saved_top)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            ["Nombre", "Palabras", "Creado", "Archivo"]
        )
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.table.setAlternatingRowColors(True)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.setMinimumHeight(140)
        saved.body.addWidget(self.table)

        saved_actions = QHBoxLayout()
        saved_actions.setSpacing(10)
        self.use_button = QPushButton("Usar en análisis")
        self.use_button.setObjectName("Primary")
        self.use_button.clicked.connect(self._use_selected)
        self.preview_button = QPushButton("Ver palabras")
        self.preview_button.setObjectName("Ghost")
        self.preview_button.clicked.connect(self._preview_selected)
        self.refresh_button = QPushButton("Actualizar")
        self.refresh_button.setObjectName("Ghost")
        self.refresh_button.clicked.connect(self.refresh_dictionaries)
        self.delete_button = QPushButton("Eliminar")
        self.delete_button.setObjectName("Danger")
        self.delete_button.clicked.connect(self._delete_selected)
        saved_actions.addWidget(self.use_button)
        saved_actions.addWidget(self.preview_button)
        saved_actions.addWidget(self.refresh_button)
        saved_actions.addWidget(self.delete_button)
        saved_actions.addStretch(1)
        saved.body.addLayout(saved_actions)

        hint = QLabel(
            "Los diccionarios se guardan en ~/wifi_audit_capturas/diccionarios "
            "y aparecen también en la pantalla de análisis."
        )
        hint.setObjectName("Muted")
        hint.setWordWrap(True)
        saved.body.addWidget(hint)
        layout.addWidget(saved, 1)

        self.refresh_dictionaries()

    # ------------------------------------------------------------------ API
    def set_generating(self, generating: bool) -> None:
        self._generating = generating
        self.generate_button.setEnabled(not generating)
        self.stop_button.setEnabled(generating)
        self.name_edit.setEnabled(not generating)
        self.words_edit.setEnabled(not generating)
        self.limit_spin.setEnabled(not generating)
        for checkbox in self._rule_boxes.values():
            checkbox.setEnabled(not generating)
        if generating:
            self._result_reported = False
            self.banner.hide()
            self.progress.setValue(0)
            self.status_badge.set_status("busy", "GENERANDO")
        elif not self._result_reported:
            self.status_badge.set_status("idle", "EN ESPERA")

    def set_progress(self, done: int, total: int) -> None:
        if total > 0:
            self.progress.setValue(min(100, int(done * 100 / total)))

    def show_result(self, path: str, count: int) -> None:
        self._result_reported = True
        self.progress.setValue(100)
        self.status_badge.set_status("ok", "GUARDADO")
        self._banner_path = path
        self.banner.show_message(
            "success",
            "Diccionario creado",
            f"{Path(path).name} · {count:,} palabras. Ya está disponible "
            "en la pantalla de análisis.",
            action_text="Usar en análisis",
        )
        self.refresh_dictionaries()
        self.dictionaries_changed.emit()

    def show_error(self, message: str) -> None:
        self._result_reported = True
        self.status_badge.set_status("error", "ERROR")
        self.banner.show_message("error", "No se pudo generar", message)

    def append_log(self, text: str) -> None:
        self.log_view.append(text)

    def is_generating(self) -> bool:
        return self._generating

    def refresh_dictionaries(self) -> None:
        dictionaries = list_wordlists()
        self.table.setRowCount(0)
        for dictionary in dictionaries:
            row = self.table.rowCount()
            self.table.insertRow(row)

            name_item = QTableWidgetItem(dictionary["name"])
            name_item.setData(
                Qt.ItemDataRole.UserRole, dictionary["path"]
            )
            self.table.setItem(row, 0, name_item)
            self.table.setItem(
                row, 1, QTableWidgetItem(f"{dictionary['count']:,}")
            )
            created = dictionary["created"].replace("T", " ")
            self.table.setItem(row, 2, QTableWidgetItem(created))
            self.table.setItem(
                row, 3, QTableWidgetItem(dictionary["path"])
            )

        self.count_label.setText(
            f"{len(dictionaries)} diccionario(s)"
        )
        has_rows = self.table.rowCount() > 0
        for button in (
            self.use_button,
            self.preview_button,
            self.delete_button,
        ):
            button.setEnabled(has_rows)

    # ------------------------------------------------------------- internos
    def _use_banner_dictionary(self) -> None:
        if self._banner_path:
            self.use_in_analysis.emit(self._banner_path)

    def _selected_path(self) -> str | None:
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(
                self,
                "Sin selección",
                "Selecciona un diccionario de la tabla.",
            )
            return None
        item = self.table.item(row, 0)
        if item is None:
            return None
        return str(item.data(Qt.ItemDataRole.UserRole))

    def _emit_generate(self) -> None:
        raw_words = self.words_edit.toPlainText()
        words = clean_words(raw_words)
        if not words:
            QMessageBox.warning(
                self,
                "Faltan palabras",
                "Escribe al menos una palabra base, una por línea.",
            )
            return

        path = wordlist_path(self.name_edit.text())
        if path.exists():
            reply = QMessageBox.question(
                self,
                "Sobrescribir diccionario",
                f"Ya existe un diccionario con ese nombre:\n{path.name}\n\n"
                "¿Quieres reemplazarlo?",
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        rules = {
            key: checkbox.isChecked()
            for key, checkbox in self._rule_boxes.items()
        }
        self.append_log(
            f"Generando desde {len(words)} palabras base · límite "
            f"{self.limit_spin.value():,}…"
        )
        self.generation_requested.emit(
            self.name_edit.text().strip(),
            raw_words,
            rules,
            self.limit_spin.value(),
        )

    def _use_selected(self) -> None:
        path = self._selected_path()
        if path:
            self.use_in_analysis.emit(path)

    def _preview_selected(self) -> None:
        path = self._selected_path()
        if not path:
            return
        try:
            with Path(path).open(encoding="utf-8", errors="replace") as handle:
                sample = list(itertools.islice(handle, 25))
        except OSError as exc:
            QMessageBox.warning(
                self, "No se pudo leer", str(exc)
            )
            return
        words = "".join(sample).strip() or "(vacío)"
        QMessageBox.information(
            self,
            "Primeras palabras",
            f"{Path(path).name}\n\n{words}\n\n…",
        )

    def _delete_selected(self) -> None:
        path = self._selected_path()
        if not path:
            return
        reply = QMessageBox.question(
            self,
            "Eliminar diccionario",
            f"¿Eliminar {Path(path).name}? Esta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            delete_wordlist(path)
        except (OSError, ValueError) as exc:
            QMessageBox.warning(self, "No se pudo eliminar", str(exc))
            return
        self.append_log(f"Diccionario eliminado: {Path(path).name}")
        self.refresh_dictionaries()
        self.dictionaries_changed.emit()
