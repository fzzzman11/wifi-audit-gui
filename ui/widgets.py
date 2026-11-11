"""Widgets reutilizables: tarjetas, LEDs de estado, log, barras de señal..."""

from __future__ import annotations

import html
import time

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QColor, QFontDatabase, QPainter
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.parsers import signal_level


def rgba(hex_color: str, alpha: float) -> str:
    """Convierte #RRGGBB a rgba(...) para usarlo en hojas de estilo."""
    color = QColor(hex_color)
    return f"rgba({color.red()}, {color.green()}, {color.blue()}, {alpha})"


class Card(QFrame):
    """Contenedor con el estilo de tarjeta oscura usado en todas las páginas."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("Card")
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(18, 16, 18, 16)
        self.body.setSpacing(12)


class PageHeader(QWidget):
    """Título y subtítulo de una página."""

    def __init__(self, title: str, subtitle: str, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        title_label = QLabel(title)
        title_label.setObjectName("PageTitle")
        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("PageSubtitle")
        subtitle_label.setWordWrap(True)

        layout.addWidget(title_label)
        layout.addWidget(subtitle_label)


class LogView(QPlainTextEdit):
    """Panel de log de solo lectura con marcas de tiempo y colores por nivel."""

    COLORS = {
        "info": "#b9c9d9",
        "ok": "#22c55e",
        "warn": "#f59e0b",
        "error": "#ef4444",
        "cmd": "#22d3ee",
    }

    def __init__(self, placeholder: str = "", parent=None) -> None:
        super().__init__(parent)
        self.setReadOnly(True)
        self.setMaximumBlockCount(3000)
        self.setPlaceholderText(placeholder)
        self.setMinimumHeight(110)

        font = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        font.setPointSize(9)
        self.setFont(font)

    def append(self, text: str, level: str = "info") -> None:
        color = self.COLORS.get(level, self.COLORS["info"])
        stamp = time.strftime("%H:%M:%S")
        safe = html.escape(str(text))
        self.appendHtml(
            f'<span style="color:#4f6275">[{stamp}]</span> '
            f'<span style="color:{color}">{safe}</span>'
        )
        scrollbar = self.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def clear_log(self) -> None:
        self.clear()


class StatusBadge(QFrame):
    """Píldora con un punto luminoso y un texto (ACTIVO / INACTIVO / ...)."""

    COLORS = {
        "ok": "#22c55e",
        "warn": "#f59e0b",
        "error": "#ef4444",
        "idle": "#64748b",
        "busy": "#38bdf8",
    }
    BACKGROUNDS = {
        "ok": "#0d2a1a",
        "warn": "#2a200c",
        "error": "#2a1013",
        "idle": "#16202b",
        "busy": "#0c2330",
    }

    def __init__(self, text: str = "", kind: str = "idle", parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("StatusBadge")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(9, 4, 11, 4)
        layout.setSpacing(7)

        self._dot = QLabel()
        self._dot.setFixedSize(10, 10)
        self._text = QLabel(text)
        self._text.setObjectName("BadgeText")

        layout.addWidget(self._dot)
        layout.addWidget(self._text)

        self._glow = QGraphicsDropShadowEffect(self._dot)
        self._glow.setBlurRadius(12)
        self._glow.setOffset(0, 0)
        self._dot.setGraphicsEffect(self._glow)

        self.set_status(kind, text)

    def set_status(self, kind: str, text: str | None = None) -> None:
        if text is not None:
            self._text.setText(text)
        foreground = self.COLORS.get(kind, self.COLORS["idle"])
        background = self.BACKGROUNDS.get(kind, self.BACKGROUNDS["idle"])

        self.setStyleSheet(
            "QFrame#StatusBadge {"
            f"background: {background};"
            f"border: 1px solid {rgba(foreground, 0.45)};"
            "border-radius: 12px;"
            "}"
            "QLabel#BadgeText {"
            f"color: {foreground};"
            "background: transparent;"
            "font-size: 11px;"
            "font-weight: 700;"
            "}"
        )
        self._dot.setStyleSheet(
            f"background: {foreground}; border-radius: 5px;"
        )
        self._glow.setColor(QColor(foreground))


class NumericItem(QTableWidgetItem):
    """Celda de tabla que ordena numéricamente usando el rol UserRole."""

    def __init__(self, text: str, value: float) -> None:
        super().__init__(text)
        self.setData(Qt.ItemDataRole.UserRole, value)
        self.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

    def __lt__(self, other: QTableWidgetItem) -> bool:
        left = self.data(Qt.ItemDataRole.UserRole)
        right = other.data(Qt.ItemDataRole.UserRole)
        if isinstance(left, (int, float)) and isinstance(right, (int, float)):
            return left < right
        return super().__lt__(other)


class SignalDelegate(QStyledItemDelegate):
    """Pinta la columna Señal como 4 barras + valor en dBm."""

    HEIGHTS = (4, 7, 10, 13)
    BAR_WIDTH = 4
    GAP = 2

    def paint(self, painter: QPainter, option, index) -> None:
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        style = opt.widget.style() if opt.widget else QApplication.style()

        # Dibuja el fondo/selección estándar, pero sin el texto.
        opt.text = ""
        style.drawControl(
            QStyle.ControlElement.CE_ItemViewItem, opt, painter, opt.widget
        )

        try:
            dbm = int(index.data(Qt.ItemDataRole.UserRole))
        except (TypeError, ValueError):
            dbm = -100

        level = signal_level(dbm)
        color = {
            4: "#22c55e",
            3: "#84cc16",
            2: "#f59e0b",
            1: "#f97316",
            0: "#ef4444",
        }[level]

        rect = option.rect.adjusted(10, 0, -6, 0)
        base_y = rect.center().y() + 7

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(Qt.PenStyle.NoPen)

        for i, height in enumerate(self.HEIGHTS):
            x = rect.left() + i * (self.BAR_WIDTH + self.GAP)
            bar = QRectF(x, base_y - height, self.BAR_WIDTH, height)
            painter.setBrush(
                QColor(color) if i < level else QColor("#243444")
            )
            painter.drawRoundedRect(bar, 1.5, 1.5)

        selected = bool(opt.state & QStyle.StateFlag.State_Selected)
        painter.setPen(QColor("#e6fbff") if selected else QColor("#c6d5e4"))
        painter.setFont(opt.font)
        text_rect = rect.adjusted(
            4 * (self.BAR_WIDTH + self.GAP) + 8, 0, 0, 0
        )
        painter.drawText(
            text_rect,
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            f"{dbm} dBm",
        )
        painter.restore()

    def sizeHint(self, option, index):
        size = super().sizeHint(option, index)
        size.setWidth(max(size.width(), 96))
        size.setHeight(max(size.height(), 26))
        return size


class MetricCard(QFrame):
    """Tarjeta pequeña con un título y un valor grande (clientes, paquetes...)."""

    def __init__(self, title: str, value: str = "—", parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("Card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)

        self._title = QLabel(title.upper())
        self._title.setObjectName("MetricTitle")
        self._value = QLabel(value)
        self._value.setObjectName("MetricValue")

        layout.addWidget(self._title)
        layout.addWidget(self._value)

    def set_value(self, text: str, color: str | None = None) -> None:
        self._value.setText(text)
        self._value.setStyleSheet(
            f"color: {color};" if color else "color: #f1f7fd;"
        )


class Banner(QFrame):
    """Aviso destacado para handshake capturado, resultado del crack, etc."""

    COLORS = {
        "success": ("#22c55e", "#0d2a1a", "#1d6b3a"),
        "error": ("#ef4444", "#2a1013", "#7f1d1d"),
        "warning": ("#f59e0b", "#2a200c", "#7c5a12"),
        "info": ("#38bdf8", "#0c2330", "#155e75"),
    }
    ICONS = {
        "success": "✓",
        "error": "✕",
        "warning": "!",
        "info": "i",
    }

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("Banner")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        self._icon = QLabel("✓")
        self._icon.setObjectName("BannerIcon")
        self._icon.setFixedWidth(26)
        self._icon.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter
        )

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        self._title = QLabel()
        self._title.setObjectName("BannerTitle")
        self._text = QLabel()
        self._text.setObjectName("BannerText")
        self._text.setWordWrap(True)
        text_layout.addWidget(self._title)
        text_layout.addWidget(self._text)

        self.action_button = QPushButton("Ir a análisis")
        self.action_button.setObjectName("Primary")
        self.action_button.hide()

        layout.addWidget(self._icon)
        layout.addLayout(text_layout, 1)
        layout.addWidget(
            self.action_button, 0, Qt.AlignmentFlag.AlignVCenter
        )

        self.hide()

    def show_message(
        self,
        kind: str,
        title: str,
        text: str,
        action_text: str | None = None,
    ) -> None:
        foreground, background, border = self.COLORS.get(
            kind, self.COLORS["info"]
        )
        self.setStyleSheet(
            "QFrame#Banner {"
            f"background: {background};"
            f"border: 1px solid {border};"
            "border-radius: 12px;"
            "}"
            "QLabel#BannerTitle {"
            f"color: {foreground};"
            "background: transparent;"
            "font-size: 15px;"
            "font-weight: 700;"
            "}"
            "QLabel#BannerText {"
            "color: #c6d5e4;"
            "background: transparent;"
            "}"
            "QLabel#BannerIcon {"
            f"color: {foreground};"
            "background: transparent;"
            "font-size: 22px;"
            "font-weight: 700;"
            "}"
        )
        self._icon.setText(self.ICONS.get(kind, "i"))
        self._title.setText(title)
        self._text.setText(text)
        if action_text:
            self.action_button.setText(action_text)
            self.action_button.show()
        else:
            self.action_button.hide()
        self.show()


class Divider(QFrame):
    """Línea horizontal fina para separar secciones dentro de una tarjeta."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedHeight(1)
        self.setStyleSheet("background: #1d2b3a; border: none;")
