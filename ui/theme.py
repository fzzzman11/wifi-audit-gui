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
MUTED = "#9fb4c8"
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
    color: #9fb4c8;
    font-size: 12px;
}
QLabel#PageTitle {
    font-size: 22px;
    font-weight: 700;
    color: #f1f7fd;
}
QLabel#PageSubtitle {
    color: #b4c6d8;
    font-size: 13px;
}
QLabel#Muted {
    color: #9fb4c8;
}
QLabel#Value {
    font-size: 15px;
    font-weight: 600;
    color: #eaf4fd;
}
QLabel#MetricTitle {
    color: #9fb4c8;
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
    background: #1b2b3a;
    border: 1px solid #3b5a73;
    border-radius: 9px;
    padding: 8px 14px;
    color: #f1f7fd;
    font-weight: 700;
}
QPushButton:hover {
    background: #24405a;
    border-color: #67e8f9;
}
QPushButton:pressed {
    background: #162532;
}
QPushButton:disabled {
    color: #6c8195;
    background: #141e28;
    border-color: #24333f;
}
QPushButton#Primary {
    background: #06b6d4;
    border: 1px solid #a5f3fc;
    color: #03252c;
    font-weight: 800;
}
QPushButton#Primary:hover {
    background: #22d3ee;
    border-color: #e0fdff;
}
QPushButton#Primary:pressed {
    background: #0891b2;
}
QPushButton#Primary:disabled {
    background: #164b58;
    border-color: #24606c;
    color: #8fc4cf;
}
QPushButton#Danger {
    background: #b91c1c;
    border: 1px solid #fca5a5;
    color: #fff7f7;
    font-weight: 800;
}
QPushButton#Danger:hover {
    background: #dc2626;
    border-color: #fecaca;
}
QPushButton#Danger:pressed {
    background: #991b1b;
}
QPushButton#Danger:disabled {
    background: #4a2226;
    border-color: #6d3338;
    color: #bb8b8f;
}
QPushButton#Ghost {
    background: #14232f;
    border: 1px solid #3b5a73;
    color: #dcebf7;
}
QPushButton#Ghost:hover {
    background: #1d3648;
    border-color: #67e8f9;
    color: #ffffff;
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
    background: #0e1925;
    border: 1px solid #33506a;
    border-radius: 8px;
    padding: 7px 10px;
    color: #f1f7fd;
    selection-background-color: #0891b2;
    min-height: 20px;
}
QComboBox:focus, QLineEdit:focus, QSpinBox:focus {
    border-color: #22d3ee;
}
QComboBox:disabled, QLineEdit:disabled, QSpinBox:disabled {
    color: #6c8195;
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
    border: 1px solid #2a4055;
    border-radius: 6px;
    height: 16px;
    text-align: center;
    color: #f8fcff;
    font-size: 11px;
    font-weight: 700;
}
QProgressBar::chunk {
    background: #0e7490;
    border-radius: 5px;
}
QTableWidget {
    background: #101b27;
    alternate-background-color: #142231;
    border: 1px solid #2a4055;
    border-radius: 10px;
    gridline-color: #1d2b3a;
    selection-background-color: #155e75;
    selection-color: #ffffff;
    color: #f1f7fd;
}
QTableWidget::item {
    padding: 7px 8px;
    border-bottom: 1px solid #1b2a39;
    color: #f1f7fd;
}
QTableWidget::item:selected {
    background: #155e75;
    color: #ffffff;
}
QHeaderView::section {
    background: #162635;
    color: #b4c6d8;
    border: none;
    border-bottom: 1px solid #24384a;
    padding: 9px 8px;
    font-weight: 700;
    font-size: 11px;
}
QPlainTextEdit, QTextEdit {
    background: #0b141d;
    border: 1px solid #2a4055;
    border-radius: 10px;
    color: #dbe7f3;
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
    color: #9fb4c8;
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
