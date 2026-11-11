"""Tema oscuro propio (QSS) para toda la aplicación.

Se evita depender de qdarkstyle para que el proyecto sea autocontenido y el
alumno pueda explicar en el informe exactamente qué estilos se aplicaron.
"""

from __future__ import annotations

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplication

# Paleta usada también por algunos widgets personalizados.
BG = "#0b1118"
SURFACE = "#111a24"
SURFACE_ALT = "#0d151e"
BORDER = "#1d2b3a"
TEXT = "#dbe7f3"
MUTED = "#8398ad"
ACCENT = "#22d3ee"
ACCENT_DARK = "#0891b2"
GREEN = "#22c55e"
RED = "#ef4444"
AMBER = "#f59e0b"

DARK_QSS = """
* {
    font-family: "Inter", "Segoe UI", "DejaVu Sans", sans-serif;
    font-size: 13px;
}
QMainWindow, QWidget#AppRoot {
    background: #0b1118;
    color: #dbe7f3;
}
QWidget {
    color: #dbe7f3;
}
QFrame#Header {
    background: #0e1621;
    border-bottom: 1px solid #1e2b3a;
}
QFrame#Sidebar {
    background: #0d141d;
    border-right: 1px solid #1e2b3a;
}
QFrame#Card {
    background: #111a24;
    border: 1px solid #1d2b3a;
    border-radius: 14px;
}
QFrame#RootBanner {
    background: #2a200c;
    border: 1px solid #7c5a12;
    border-radius: 10px;
}
QFrame#ToolBanner {
    background: #2a1013;
    border: 1px solid #7f1d1d;
    border-radius: 10px;
}
QLabel#AppTitle {
    font-size: 20px;
    font-weight: 700;
    color: #f1f7fd;
}
QLabel#AppSubtitle {
    color: #7f93a8;
    font-size: 12px;
}
QLabel#PageTitle {
    font-size: 22px;
    font-weight: 700;
    color: #f1f7fd;
}
QLabel#PageSubtitle {
    color: #8398ad;
    font-size: 13px;
}
QLabel#Muted {
    color: #8398ad;
}
QLabel#Value {
    font-size: 15px;
    font-weight: 600;
    color: #eaf4fd;
}
QLabel#MetricTitle {
    color: #7f93a8;
    font-size: 11px;
    font-weight: 700;
}
QLabel#MetricValue {
    font-size: 24px;
    font-weight: 700;
    color: #f1f7fd;
}
QLabel#CardTitle {
    font-size: 14px;
    font-weight: 700;
    color: #eaf4fd;
}
QLabel#BadgeText {
    background: transparent;
    font-size: 11px;
    font-weight: 700;
}
QLabel#BannerTitle {
    font-size: 15px;
    font-weight: 700;
    background: transparent;
}
QLabel#BannerText {
    color: #c6d5e4;
    background: transparent;
}
QLabel#BannerIcon {
    font-size: 22px;
    font-weight: 700;
    background: transparent;
}
QLabel#StepNumber {
    color: #22d3ee;
    font-weight: 700;
    background: transparent;
}
QPushButton {
    background: #17222e;
    border: 1px solid #26384a;
    border-radius: 9px;
    padding: 8px 14px;
    color: #dbe7f3;
    font-weight: 600;
}
QPushButton:hover {
    background: #1d2b39;
    border-color: #33506a;
}
QPushButton:pressed {
    background: #14202b;
}
QPushButton:disabled {
    color: #526577;
    background: #121a23;
    border-color: #1b2733;
}
QPushButton#Primary {
    background: #0891b2;
    border: 1px solid #22d3ee;
    color: #04141a;
}
QPushButton#Primary:hover {
    background: #06b6d4;
}
QPushButton#Primary:pressed {
    background: #0e7490;
}
QPushButton#Primary:disabled {
    background: #16323a;
    border-color: #1e3a44;
    color: #4e7a85;
}
QPushButton#Danger {
    background: #7f1d1d;
    border: 1px solid #ef4444;
    color: #fee2e2;
}
QPushButton#Danger:hover {
    background: #991b1b;
}
QPushButton#Danger:disabled {
    background: #2a1518;
    border-color: #4a2024;
    color: #7c4b4f;
}
QPushButton#Ghost {
    background: transparent;
    border: 1px solid #2a3b4d;
    color: #a9bccf;
}
QPushButton#Ghost:hover {
    background: #16212c;
    border-color: #3a556d;
}
QPushButton#NavButton {
    text-align: left;
    padding: 11px 14px;
    border-radius: 10px;
    border: 1px solid transparent;
    background: transparent;
    color: #8fa3b7;
    font-weight: 600;
}
QPushButton#NavButton:hover {
    background: #121c26;
    color: #dbe7f3;
}
QPushButton#NavButton:checked {
    background: #0e2a33;
    border-color: #164e5b;
    color: #67e8f9;
}
QComboBox, QLineEdit, QSpinBox {
    background: #0c141d;
    border: 1px solid #253647;
    border-radius: 8px;
    padding: 7px 10px;
    color: #dbe7f3;
    selection-background-color: #0891b2;
    min-height: 20px;
}
QComboBox:focus, QLineEdit:focus, QSpinBox:focus {
    border-color: #22d3ee;
}
QComboBox:disabled, QLineEdit:disabled, QSpinBox:disabled {
    color: #526577;
    background: #0a1118;
}
QComboBox::drop-down {
    border: none;
    width: 26px;
}
QComboBox QAbstractItemView {
    background: #0f1922;
    border: 1px solid #253647;
    selection-background-color: #0e3a46;
    selection-color: #a5f3fc;
    outline: none;
}
QSpinBox::up-button, QSpinBox::down-button {
    background: #17222e;
    border: none;
    width: 18px;
}
QCheckBox {
    color: #c6d5e4;
    spacing: 9px;
}
QCheckBox::indicator {
    width: 17px;
    height: 17px;
    border-radius: 5px;
    border: 1px solid #345069;
    background: #0c141d;
}
QCheckBox::indicator:hover {
    border-color: #22d3ee;
}
QCheckBox::indicator:checked {
    background: #0891b2;
    border-color: #22d3ee;
}
QProgressBar {
    background: #0c141d;
    border: 1px solid #1e2d3c;
    border-radius: 6px;
    height: 10px;
    text-align: center;
    color: #7f93a8;
    font-size: 10px;
}
QProgressBar::chunk {
    background: #22d3ee;
    border-radius: 5px;
}
QTableWidget {
    background: #0d151e;
    alternate-background-color: #0f1922;
    border: 1px solid #1d2b3a;
    border-radius: 10px;
    gridline-color: #172430;
    selection-background-color: #0d3a45;
    selection-color: #e6fbff;
}
QTableWidget::item {
    padding: 6px;
    border-bottom: 1px solid #14202b;
}
QTableWidget::item:selected {
    background: #0d3a45;
}
QHeaderView::section {
    background: #111c27;
    color: #7f93a8;
    border: none;
    border-bottom: 1px solid #24384a;
    padding: 9px 8px;
    font-weight: 700;
    font-size: 11px;
}
QPlainTextEdit, QTextEdit {
    background: #0a1118;
    border: 1px solid #1d2b3a;
    border-radius: 10px;
    color: #b9c9d9;
    selection-background-color: #0e3a46;
}
QScrollBar:vertical {
    background: #0a1118;
    width: 10px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #25384a;
    min-height: 24px;
    border-radius: 5px;
}
QScrollBar::handle:vertical:hover {
    background: #33506a;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar:horizontal {
    background: #0a1118;
    height: 10px;
}
QScrollBar::handle:horizontal {
    background: #25384a;
    min-width: 24px;
    border-radius: 5px;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}
QToolTip {
    background: #14202b;
    color: #dbe7f3;
    border: 1px solid #2a3b4d;
    padding: 6px;
    border-radius: 6px;
}
QDialog, QMessageBox, QProgressDialog {
    background: #0b1118;
    color: #dbe7f3;
}
QStatusBar {
    background: #0d141d;
    color: #7f93a8;
    border-top: 1px solid #1e2b3a;
}
QSplitter::handle {
    background: #16212c;
    height: 4px;
}
"""


def apply_theme(app: QApplication) -> None:
    """Aplica Fusion + hoja de estilos oscura a toda la aplicación."""
    app.setStyle("Fusion")
    font = QFont("DejaVu Sans", 10)
    app.setFont(font)
    app.setStyleSheet(DARK_QSS)
