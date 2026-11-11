"""Ventana principal: orquesta páginas, workers y estado global."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from core.capture import CaptureWorker
from core.constants import APP_NAME, APP_VERSION, MAIN_SCRIPT
from core.cracker import CrackWorker
from core.monitor import MonitorWorker, RestoreWorker
from core.scanner import ScanWorker
from core.tools import (
    detect_monitor_interface,
    is_root,
    list_wifi_interfaces,
    missing_tools,
    sudo_relaunch_command,
    tool_paths,
)
from ui.pages.analysis_page import AnalysisPage
from ui.pages.capture_page import CapturePage
from ui.pages.interface_page import InterfacePage
from ui.pages.scan_page import ScanPage
from ui.widgets import StatusBadge


class MainWindow(QMainWindow):
    """Controlador central de la aplicación.

    Las páginas solo se encargan de la presentación. Toda la coordinación
    (arrancar/detener workers, confirmar objetivos, restaurar la interfaz)
    vive aquí para que el flujo sea fácil de seguir en el informe.
    """

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} · Auditoría WPA/WPA2")
        self.resize(1200, 800)
        self.setMinimumSize(1000, 700)

        # --- Estado global -------------------------------------------------
        self.is_root = is_root()
        self.tool_paths = tool_paths()
        self.missing = missing_tools(self.tool_paths)
        self.monitor_interface: str | None = None
        self.selected_network: dict | None = None
        self.last_cap: str | None = None

        self._monitor_worker: MonitorWorker | None = None
        self._scan_worker: ScanWorker | None = None
        self._capture_worker: CaptureWorker | None = None
        self._crack_worker: CrackWorker | None = None
        self._restore_worker: RestoreWorker | None = None

        self._closing = False
        self._stopping = False

        self._build_ui()
        self._connect_signals()
        self._post_start_checks()

    # ================================================================= UI
    def _build_ui(self) -> None:
        root_widget = QWidget()
        root_widget.setObjectName("AppRoot")
        self.setCentralWidget(root_widget)

        root = QVBoxLayout(root_widget)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ------------------------------ cabecera --------------------------
        header = QFrame()
        header.setObjectName("Header")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 12, 24, 12)
        header_layout.setSpacing(14)

        logo = QLabel("◈")
        logo.setStyleSheet(
            "color: #22d3ee; font-size: 28px; font-weight: 700;"
        )

        titles = QVBoxLayout()
        titles.setSpacing(0)
        app_title = QLabel(APP_NAME)
        app_title.setObjectName("AppTitle")
        app_subtitle = QLabel(
            "Laboratorio WPA/WPA2 · airmon-ng · airodump-ng · aireplay-ng · "
            "aircrack-ng"
        )
        app_subtitle.setObjectName("AppSubtitle")
        titles.addWidget(app_title)
        titles.addWidget(app_subtitle)

        self.root_badge = StatusBadge("ROOT", "ok")
        self.monitor_badge = StatusBadge("MONITOR INACTIVO", "idle")

        self.stop_all_button = QPushButton("DETENER TODO")
        self.stop_all_button.setObjectName("Danger")
        self.stop_all_button.setMinimumWidth(150)
        self.stop_all_button.setToolTip(
            "Mata cualquier proceso en ejecución y restaura la interfaz."
        )

        header_layout.addWidget(logo)
        header_layout.addLayout(titles)
        header_layout.addStretch(1)
        header_layout.addWidget(self.root_badge)
        header_layout.addWidget(self.monitor_badge)
        header_layout.addWidget(self.stop_all_button)

        root.addWidget(header)

        # --------------------- banners de advertencia ---------------------
        self.root_banner = self._build_root_banner()
        root.addWidget(self.root_banner)

        self.tool_banner = self._build_tool_banner()
        root.addWidget(self.tool_banner)

        # ------------------------------ cuerpo ----------------------------
        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(235)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(16, 20, 16, 18)
        side_layout.setSpacing(8)

        flow_title = QLabel("FLUJO DE TRABAJO")
        flow_title.setObjectName("MetricTitle")
        side_layout.addWidget(flow_title)
        side_layout.addSpacing(6)

        self.nav_buttons: list[QPushButton] = []
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        steps = [
            ("1", "Interfaz"),
            ("2", "Escaneo"),
            ("3", "Captura"),
            ("4", "Análisis"),
        ]
        for index, (number, title) in enumerate(steps):
            button = QPushButton(f"{number}   {title}")
            button.setObjectName("NavButton")
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(
                lambda _checked=False, idx=index: self._go_to_page(idx)
            )
            self.nav_group.addButton(button, index)
            self.nav_buttons.append(button)
            side_layout.addWidget(button)

        side_layout.addStretch(1)

        side_note = QLabel(
            "Solo redes propias o con autorización explícita.\n"
            "Prácticas de ciberseguridad · uso académico."
        )
        side_note.setObjectName("Muted")
        side_note.setWordWrap(True)
        side_layout.addWidget(side_note)

        body.addWidget(sidebar)

        self.stack = QStackedWidget()
        self.interface_page = InterfacePage()
        self.scan_page = ScanPage()
        self.capture_page = CapturePage()
        self.analysis_page = AnalysisPage()
        self.stack.addWidget(self.interface_page)
        self.stack.addWidget(self.scan_page)
        self.stack.addWidget(self.capture_page)
        self.stack.addWidget(self.analysis_page)
        body.addWidget(self.stack, 1)

        root.addLayout(body, 1)

        status = QStatusBar()
        self.setStatusBar(status)
        self.statusBar().showMessage("Listo.")
        version = QLabel(f"v{APP_VERSION}")
        version.setObjectName("Muted")
        self.statusBar().addPermanentWidget(version)

        self._go_to_page(0)

    def _build_root_banner(self) -> QFrame:
        banner = QFrame()
        banner.setObjectName("RootBanner")
        layout = QHBoxLayout(banner)
        layout.setContentsMargins(18, 9, 18, 9)
        layout.setSpacing(12)

        text = QLabel(
            "Sin privilegios root: podrás explorar la interfaz, pero activar "
            "el modo monitor y capturar tráfico requiere root."
        )
        text.setStyleSheet("color: #f8d98b; background: transparent;")
        text.setWordWrap(True)

        relaunch = QPushButton("Reabrir como root")
        relaunch.setObjectName("Primary")
        relaunch.clicked.connect(self._relaunch_as_root)

        copy_button = QPushButton("Copiar comando")
        copy_button.setObjectName("Ghost")
        copy_button.clicked.connect(self._copy_sudo_command)

        layout.addWidget(text, 1)
        layout.addWidget(relaunch)
        layout.addWidget(copy_button)
        banner.setVisible(False)
        return banner

    def _build_tool_banner(self) -> QFrame:
        banner = QFrame()
        banner.setObjectName("ToolBanner")
        layout = QHBoxLayout(banner)
        layout.setContentsMargins(18, 9, 18, 9)
        layout.setSpacing(12)

        self.tool_banner_label = QLabel("")
        self.tool_banner_label.setStyleSheet(
            "color: #fecaca; background: transparent;"
        )
        self.tool_banner_label.setWordWrap(True)

        copy_button = QPushButton("Copiar instalación")
        copy_button.setObjectName("Ghost")
        copy_button.clicked.connect(self._copy_install_command)

        layout.addWidget(self.tool_banner_label, 1)
        layout.addWidget(copy_button)
        banner.setVisible(False)
        return banner

    # ============================================================ señales
    def _connect_signals(self) -> None:
        self.interface_page.refresh_requested.connect(
            lambda: self._refresh_interfaces(user_initiated=True)
        )
        self.interface_page.activate_requested.connect(
            self._activate_monitor
        )
        self.interface_page.deactivate_requested.connect(
            lambda: self.stop_all(restore=True)
        )

        self.scan_page.scan_requested.connect(self._start_scan)
        self.scan_page.stop_requested.connect(self._stop_scan)
        self.scan_page.capture_requested.connect(self._confirm_capture)

        self.capture_page.start_requested.connect(self._start_capture)
        self.capture_page.stop_requested.connect(self._stop_capture)
        self.capture_page.analyze_requested.connect(self._go_to_analysis)

        self.analysis_page.crack_requested.connect(self._start_crack)
        self.analysis_page.stop_requested.connect(self._stop_crack)

        self.stop_all_button.clicked.connect(
            lambda: self.stop_all(restore=True)
        )

    # ===================================================== estado inicial
    def _post_start_checks(self) -> None:
        if self.is_root:
            self.root_badge.set_status("ok", "ROOT")
            self.root_banner.setVisible(False)
        else:
            self.root_badge.set_status("warn", "SIN ROOT")
            self.root_banner.setVisible(True)

        self.interface_page.set_root_enabled(self.is_root)

        if self.missing:
            names = ", ".join(self.missing)
            self.tool_banner_label.setText(
                f"Faltan herramientas: {names}. Instálalas con "
                "“sudo apt install aircrack-ng iw” y vuelve a abrir la app."
            )
            self.tool_banner.setVisible(True)
        else:
            self.tool_banner.setVisible(False)

        # Si ya había una interfaz en modo monitor, la reflejamos.
        existing_monitor = detect_monitor_interface()
        if existing_monitor:
            self._apply_monitor_state(True, existing_monitor)
            self.statusBar().showMessage(
                f"Interfaz en modo monitor detectada: {existing_monitor}"
            )
        else:
            self._apply_monitor_state(False)

        self._refresh_interfaces()

    def _apply_monitor_state(
        self, active: bool, interface: str | None = None
    ) -> None:
        self.monitor_interface = interface if active else None
        if active:
            self.monitor_badge.set_status(
                "ok", f"MONITOR · {interface or ''}".strip()
            )
        else:
            self.monitor_badge.set_status("idle", "MONITOR INACTIVO")

        self.interface_page.set_monitor_state(active, interface)
        self.scan_page.set_monitor_ready(active)
        self.capture_page.set_monitor_ready(active)

    # ==================================================== interfaz / root
    def _refresh_interfaces(self, user_initiated: bool = False) -> None:
        interfaces = list_wifi_interfaces()
        self.interface_page.set_interfaces(interfaces)

        if interfaces:
            self.statusBar().showMessage(
                f"{len(interfaces)} interfaz(es) WiFi detectada(s).", 5000
            )
        else:
            self.interface_page.append_log(
                "No se detectó interfaz WiFi. Comprueba que el adaptador "
                "está conectado y que el driver está cargado.",
                "warn",
            )
            if user_initiated:
                QMessageBox.warning(
                    self,
                    "No se detectó interfaz WiFi",
                    "No se encontró ningún adaptador inalámbrico.\n\n"
                    "Comprueba que el TP-Link TL-WN722N está conectado y que "
                    "el driver rtl8188eus aparece en `dmesg`.",
                )

    def _activate_monitor(self, interface: str) -> None:
        if not self.is_root:
            QMessageBox.warning(
                self,
                "Permisos insuficientes",
                "Activar el modo monitor requiere root.\n\n"
                f"Ejecuta:\n{sudo_relaunch_command()}",
            )
            return
        if not self.tool_paths.get("airmon-ng"):
            QMessageBox.critical(
                self,
                "airmon-ng no está instalado",
                "Instala la suite aircrack-ng antes de continuar:\n"
                "sudo apt install aircrack-ng iw",
            )
            return
        if self._monitor_worker and self._monitor_worker.isRunning():
            return

        self.interface_page.set_busy(True, "Activando modo monitor…")
        self.monitor_badge.set_status("busy", "MONITOR · ACTIVANDO")
        self.interface_page.append_log(
            f"Activando modo monitor en {interface}…", "cmd"
        )

        worker = MonitorWorker(interface, self)
        worker.log.connect(
            lambda text: self.interface_page.append_log(text)
        )
        worker.activated.connect(self._on_monitor_activated)
        worker.error.connect(self._on_monitor_error)
        worker.finished.connect(self._on_monitor_worker_finished)
        self._monitor_worker = worker
        worker.start()

    def _on_monitor_activated(self, monitor: str) -> None:
        self.interface_page.set_busy(False)
        self._apply_monitor_state(True, monitor)
        self.interface_page.append_log(
            f"Modo monitor activo en {monitor}.", "ok"
        )
        self.statusBar().showMessage(
            f"Modo monitor activo en {monitor}.", 6000
        )
        self._go_to_page(1)

    def _on_monitor_error(self, message: str) -> None:
        self.interface_page.set_busy(False)
        self._apply_monitor_state(False)
        self.interface_page.append_log(message, "error")
        if not self._closing and not self._stopping:
            QMessageBox.critical(
                self, "No se pudo activar el modo monitor", message
            )

    def _on_monitor_worker_finished(self) -> None:
        self._monitor_worker = None

    def _relaunch_as_root(self) -> None:
        command = sudo_relaunch_command()
        if not shutil.which("pkexec"):
            QMessageBox.information(
                self,
                "Ejecutar como root",
                "No se encontró pkexec. Ejecuta manualmente:\n\n"
                f"{command}",
            )
            return

        env = os.environ
        xauthority = env.get(
            "XAUTHORITY", str(Path.home() / ".Xauthority")
        )
        cmd = [
            "pkexec",
            "env",
            f"DISPLAY={env.get('DISPLAY', '')}",
            f"XAUTHORITY={xauthority}",
            sys.executable,
            str(MAIN_SCRIPT),
        ]
        if env.get("WAYLAND_DISPLAY"):
            cmd.insert(3, f"WAYLAND_DISPLAY={env['WAYLAND_DISPLAY']}")

        try:
            subprocess.Popen(cmd, start_new_session=True)
            QApplication.quit()
        except Exception as exc:
            QMessageBox.warning(
                self,
                "No se pudo relanzar como root",
                f"{exc}\n\nEjecuta manualmente:\n{command}",
            )

    def _copy_sudo_command(self) -> None:
        QApplication.clipboard().setText(sudo_relaunch_command())
        self.statusBar().showMessage(
            "Comando copiado al portapapeles.", 4000
        )

    def _copy_install_command(self) -> None:
        QApplication.clipboard().setText(
            "sudo apt install aircrack-ng iw"
        )
        self.statusBar().showMessage(
            "Comando de instalación copiado.", 4000
        )

    # ============================================================= escaneo
    def _start_scan(self, duration: int, band: str) -> None:
        if not self.monitor_interface:
            QMessageBox.warning(
                self,
                "Modo monitor inactivo",
                "Activa el modo monitor en la pantalla 1 antes de escanear.",
            )
            return
        if not self.tool_paths.get("airodump-ng"):
            QMessageBox.critical(
                self,
                "airodump-ng no está instalado",
                "Instala la suite aircrack-ng antes de continuar.",
            )
            return
        if self._scan_worker and self._scan_worker.isRunning():
            return

        self.scan_page.clear_results()
        self.scan_page.set_scanning(True)
        self.scan_page.append_log(
            f"Escaneando durante {duration}s en banda {band}…", "cmd"
        )

        worker = ScanWorker(
            self.monitor_interface, duration, band, self
        )
        worker.networks_updated.connect(self.scan_page.set_networks)
        worker.progress.connect(self.scan_page.set_progress)
        worker.finished_scan.connect(self._on_scan_finished)
        worker.log.connect(
            lambda text: self.scan_page.append_log(
                text, "cmd" if text.startswith("$") else "info"
            )
        )
        worker.error.connect(self._on_scan_error)
        worker.finished.connect(self._on_scan_worker_finished)
        self._scan_worker = worker
        worker.start()

    def _stop_scan(self) -> None:
        if self._scan_worker and self._scan_worker.isRunning():
            self.scan_page.set_status("Deteniendo escaneo…")
            self._scan_worker.request_stop()

    def _on_scan_finished(self, had_networks: bool, cancelled: bool) -> None:
        self.scan_page.set_scanning(False)

        if cancelled:
            self.scan_page.set_status("Escaneo cancelado.")
            self.scan_page.append_log(
                "Escaneo cancelado por el usuario.", "warn"
            )
        elif had_networks:
            count = self.scan_page.table.rowCount()
            self.scan_page.set_status(
                f"Escaneo finalizado · {count} redes detectadas."
            )
            self.scan_page.append_log(
                f"Escaneo finalizado: {count} redes.", "ok"
            )
        else:
            self.scan_page.set_status("Sin resultados.")
            self.scan_page.append_log(
                "No se detectaron redes en este escaneo.", "warn"
            )
            if not self._closing and not self._stopping:
                QMessageBox.information(
                    self,
                    "Sin redes detectadas",
                    "No se encontraron redes. Comprueba que el adaptador "
                    "está en modo monitor y que hay redes en la banda "
                    "seleccionada.",
                )

    def _on_scan_error(self, message: str) -> None:
        self.scan_page.append_log(message, "error")
        if not self._closing and not self._stopping:
            QMessageBox.critical(
                self, "Error de escaneo", message
            )

    def _on_scan_worker_finished(self) -> None:
        self._scan_worker = None

    # ============================================================= captura
    def _confirm_capture(self, network: dict) -> None:
        if not self.monitor_interface:
            QMessageBox.warning(
                self,
                "Modo monitor inactivo",
                "Activa el modo monitor antes de capturar.",
            )
            return

        ssid = network.get("essid") or "(oculto)"
        box = QMessageBox(self)
        box.setWindowTitle("Confirmar red objetivo")
        box.setIcon(QMessageBox.Icon.Warning)
        box.setText("Vas a capturar el handshake de esta red:")
        box.setInformativeText(
            f"SSID: {ssid}\n"
            f"BSSID: {network.get('bssid')}\n"
            f"Canal: {network.get('channel_text')}\n\n"
            "¿Confirmas que es tu red o que tienes autorización explícita "
            "para auditarla?"
        )
        deauth_checkbox = QCheckBox(
            "Enviar deauth para forzar reconexión (10 paquetes)"
        )
        box.setCheckBox(deauth_checkbox)
        confirm_button = box.addButton(
            "Sí, tengo autorización",
            QMessageBox.ButtonRole.AcceptRole,
        )
        cancel_button = box.addButton(
            "Cancelar", QMessageBox.ButtonRole.RejectRole
        )
        box.setDefaultButton(cancel_button)
        box.exec()

        if box.clickedButton() is not confirm_button:
            return

        self.selected_network = network
        self.capture_page.set_target(network)
        self.capture_page.set_deauth(deauth_checkbox.isChecked())
        self.analysis_page.set_bssid(network.get("bssid", ""))
        self._go_to_page(2)
        self.capture_page.append_log(
            f"Objetivo: {ssid} ({network.get('bssid')}) · canal "
            f"{network.get('channel_text')}",
            "ok",
        )
        self._start_capture(self.capture_page.options())

    def _start_capture(self, options: dict) -> None:
        if not self.monitor_interface:
            QMessageBox.warning(
                self,
                "Modo monitor inactivo",
                "Activa el modo monitor antes de capturar.",
            )
            return
        if not self.tool_paths.get("airodump-ng"):
            QMessageBox.critical(
                self,
                "airodump-ng no está instalado",
                "Instala la suite aircrack-ng antes de continuar.",
            )
            return
        if self.selected_network is None:
            QMessageBox.warning(
                self,
                "Sin objetivo",
                "Selecciona una red en la pantalla de escaneo y pulsa "
                "“Capturar handshake”.",
            )
            return
        if self._capture_worker and self._capture_worker.isRunning():
            return

        network = self.selected_network
        try:
            channel = int(network.get("channel", 0))
        except (TypeError, ValueError):
            channel = 0
        if channel <= 0:
            QMessageBox.warning(
                self,
                "Canal desconocido",
                "No se pudo determinar el canal de la red. Vuelve a "
                "escanear y selecciona otra fila.",
            )
            return

        self.capture_page.set_running(True)
        self.capture_page.append_log("Iniciando captura dirigida…", "cmd")

        worker = CaptureWorker(
            interface=self.monitor_interface,
            bssid=network.get("bssid", ""),
            channel=channel,
            essid=network.get("essid", ""),
            deauth=bool(options.get("deauth")),
            duration=int(options.get("duration", 120)),
            parent=self,
        )
        worker.log.connect(
            lambda text: self.capture_page.append_log(
                text, "cmd" if text.startswith("$") else "info"
            )
        )
        worker.status.connect(self.capture_page.update_status)
        worker.handshake_found.connect(self._on_handshake_found)
        worker.finished_capture.connect(self._on_capture_finished)
        worker.error.connect(self._on_capture_error)
        worker.finished.connect(self._on_capture_worker_finished)
        self._capture_worker = worker
        worker.start()

    def _stop_capture(self) -> None:
        if self._capture_worker and self._capture_worker.isRunning():
            self.capture_page.append_log(
                "Deteniendo captura…", "warn"
            )
            self._capture_worker.request_stop()

    def _on_handshake_found(self, cap_path: str) -> None:
        self.last_cap = cap_path
        self.capture_page.show_handshake(cap_path)
        self.analysis_page.set_cap(cap_path)
        if self.selected_network:
            self.analysis_page.set_bssid(
                self.selected_network.get("bssid", "")
            )
        QApplication.beep()
        self.statusBar().showMessage(
            f"Handshake capturado: {cap_path}", 10000
        )

    def _on_capture_finished(self, cap_path: str, reason: str) -> None:
        self.capture_page.set_running(False)
        if cap_path:
            self.last_cap = cap_path
            self.analysis_page.set_cap(cap_path)

        if reason == "handshake":
            self.capture_page.append_log(
                "Captura finalizada con éxito.", "ok"
            )
        elif reason == "timeout":
            self.capture_page.append_log(
                "Tiempo máximo agotado sin capturar el handshake.", "warn"
            )
            if not self._closing and not self._stopping:
                QMessageBox.information(
                    self,
                    "Sin handshake",
                    "Se agotó el tiempo de captura sin detectar el "
                    "handshake. Acércate al router, asegúrate de que hay "
                    "clientes conectados y prueba con el deauth activado.",
                )
        elif reason == "stopped":
            self.capture_page.append_log(
                "Captura detenida por el usuario.", "warn"
            )
        else:
            self.capture_page.append_log(
                "La captura terminó con un error.", "error"
            )

    def _on_capture_error(self, message: str) -> None:
        self.capture_page.append_log(message, "error")
        if not self._closing and not self._stopping:
            QMessageBox.critical(self, "Error de captura", message)

    def _on_capture_worker_finished(self) -> None:
        self._capture_worker = None

    def _go_to_analysis(self, cap_path: str) -> None:
        self.analysis_page.set_cap(cap_path)
        if self.selected_network:
            self.analysis_page.set_bssid(
                self.selected_network.get("bssid", "")
            )
        self._go_to_page(3)

    # ============================================================= análisis
    def _start_crack(self, options: dict) -> None:
        if not self.tool_paths.get("aircrack-ng"):
            QMessageBox.critical(
                self,
                "aircrack-ng no está instalado",
                "Instala la suite aircrack-ng antes de continuar:\n"
                "sudo apt install aircrack-ng",
            )
            return
        if self._crack_worker and self._crack_worker.isRunning():
            return

        self.analysis_page.set_running(True)
        self.analysis_page.append_log(
            "Iniciando aircrack-ng…", "cmd"
        )

        worker = CrackWorker(
            cap_path=options["cap"],
            wordlist=options["wordlist"],
            bssid=options.get("bssid", ""),
            parent=self,
        )
        worker.log.connect(
            lambda text: self.analysis_page.append_log(
                text, "cmd" if text.startswith("$") else "info"
            )
        )
        worker.progress.connect(self.analysis_page.set_progress)
        worker.result.connect(self._on_crack_result)
        worker.error.connect(self._on_crack_error)
        worker.finished_crack.connect(self._on_crack_finished)
        worker.finished.connect(self._on_crack_worker_finished)
        self._crack_worker = worker
        worker.start()

    def _stop_crack(self) -> None:
        if self._crack_worker and self._crack_worker.isRunning():
            self.analysis_page.append_log(
                "Deteniendo aircrack-ng…", "warn"
            )
            self._crack_worker.request_stop()

    def _on_crack_result(self, kind: str, key: str) -> None:
        self.analysis_page.show_result(kind, key)
        if kind == "found":
            QApplication.beep()
            self.statusBar().showMessage(
                f"Clave encontrada: {key}", 15000
            )

    def _on_crack_error(self, message: str) -> None:
        self.analysis_page.append_log(message, "error")
        if not self._closing and not self._stopping:
            QMessageBox.critical(
                self, "Error de aircrack-ng", message
            )

    def _on_crack_finished(self) -> None:
        self.analysis_page.set_running(False)

    def _on_crack_worker_finished(self) -> None:
        self._crack_worker = None

    # ==================================================== restauración
    def _restore_monitor(self, show_confirmation: bool = True) -> bool:
        """Restaura la interfaz en un hilo y muestra un diálogo modal."""
        if not self.monitor_interface:
            if show_confirmation:
                QMessageBox.information(
                    self,
                    "Modo monitor",
                    "La interfaz ya está en modo managed.",
                )
            return True
        if self._restore_worker and self._restore_worker.isRunning():
            return False

        monitor = self.monitor_interface
        result = {"ok": False, "message": ""}

        dialog = QProgressDialog(
            "Restaurando la interfaz y reiniciando NetworkManager…",
            None,
            0,
            0,
            self,
        )
        dialog.setWindowTitle("Restaurando interfaz")
        dialog.setWindowModality(Qt.WindowModality.WindowModal)
        dialog.setCancelButton(None)
        dialog.setMinimumDuration(0)
        dialog.setAutoClose(False)

        worker = RestoreWorker(monitor, self)
        self._restore_worker = worker
        worker.log.connect(
            lambda text: self.interface_page.append_log(text)
        )
        worker.finished_ok.connect(
            lambda message: result.update(ok=True, message=message)
        )
        worker.error.connect(
            lambda message: result.update(ok=False, message=message)
        )
        worker.finished.connect(dialog.accept)
        worker.start()
        dialog.exec()
        worker.wait(30000)

        self._restore_worker = None
        self._apply_monitor_state(False)
        self.interface_page.set_busy(False)
        self.statusBar().showMessage(
            "Interfaz restaurada a modo managed.", 6000
        )

        if show_confirmation:
            if result["ok"]:
                QMessageBox.information(
                    self,
                    "Interfaz restaurada",
                    result["message"]
                    or "La interfaz volvió a modo managed.",
                )
            elif result["message"]:
                QMessageBox.warning(
                    self,
                    "No se pudo restaurar la interfaz",
                    result["message"],
                )
        return bool(result["ok"])

    def stop_all(
        self, restore: bool = True, show_message: bool = True
    ) -> bool:
        """Detiene todos los workers y, opcionalmente, restaura la interfaz.

        Es el manejador del botón global "DETENER TODO" y también se usa al
        cerrar la aplicación.
        """
        if self._stopping:
            return False
        self._stopping = True
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)

        workers = [
            self._scan_worker,
            self._capture_worker,
            self._crack_worker,
            self._monitor_worker,
        ]
        for worker in workers:
            if worker and worker.isRunning() and hasattr(
                worker, "request_stop"
            ):
                worker.request_stop()
        for worker in workers:
            if worker and worker.isRunning():
                worker.wait(8000)

        self.scan_page.set_scanning(False)
        self.capture_page.set_running(False)
        self.analysis_page.set_running(False)

        QApplication.restoreOverrideCursor()

        ok = True
        if restore and self.monitor_interface:
            ok = self._restore_monitor(show_confirmation=show_message)
        elif show_message:
            QMessageBox.information(
                self,
                "Procesos detenidos",
                "No hay ningún proceso en ejecución.",
            )

        self._stopping = False
        return ok

    # ======================================================== navegación
    def _go_to_page(self, index: int) -> None:
        if index < 0 or index >= self.stack.count():
            return
        self.stack.setCurrentIndex(index)
        if index < len(self.nav_buttons):
            self.nav_buttons[index].setChecked(True)

    # ============================================================= cierre
    def closeEvent(self, event: QCloseEvent) -> None:
        if self._closing:
            event.accept()
            return

        running = any(
            worker and worker.isRunning()
            for worker in (
                self._monitor_worker,
                self._scan_worker,
                self._capture_worker,
                self._crack_worker,
            )
        )

        if running or self.monitor_interface:
            reply = QMessageBox.question(
                self,
                "Salir de WiFi Audit Lab",
                "Se detendrán los procesos en ejecución y la interfaz se "
                "restaurará a modo managed.\n\n¿Deseas continuar?",
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Cancel,
            )
            if reply != QMessageBox.StandardButton.Yes:
                event.ignore()
                return

            self._closing = True
            ok = self.stop_all(restore=True, show_message=False)
            if ok:
                QMessageBox.information(
                    self,
                    "Sesión finalizada",
                    "Los procesos se detuvieron y la interfaz volvió a modo "
                    "managed.",
                )
            else:
                QMessageBox.warning(
                    self,
                    "Revisa la interfaz",
                    "Los procesos se detuvieron, pero no se pudo confirmar "
                    "la restauración. Reinicia NetworkManager manualmente:\n"
                    "sudo systemctl restart NetworkManager",
                )

        event.accept()
