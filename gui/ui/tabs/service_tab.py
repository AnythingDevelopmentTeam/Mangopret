from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QTextEdit, QLabel, QMessageBox,
    QProgressBar, QCheckBox, QScrollArea, QFrame,
    QGridLayout, QComboBox,
)
from PyQt6.QtCore import pyqtSignal, Qt, QThread


class DownloadThread(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool)

    def __init__(self, platform_info, parent=None):
        super().__init__(parent)
        self.platform = platform_info

    def run(self):
        def callback(msg):
            self.progress.emit(msg)

        result = self.platform.install_zapret(callback=callback)
        self.finished.emit(result)


class ServiceTab(QWidget):
    log_signal = pyqtSignal(str)

    def __init__(self, platform_info, config, list_manager, parent=None):
        super().__init__(parent)
        self.platform = platform_info
        self.config = config
        self.list_manager = list_manager
        self._download_thread = None
        self._strategies = {}
        self._build_ui()

    def set_strategies(self, strategies: dict):
        self._strategies = strategies
        self.svc_strategy_combo.clear()
        for name in sorted(strategies.keys()):
            self.svc_strategy_combo.addItem(name)

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        outer.addWidget(scroll)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(10)

        header = QLabel("Service & Updates")
        header.setObjectName("headerLabel")
        layout.addWidget(header)

        if self.platform.is_linux:
            self._build_linux_ui(layout)
        else:
            self._build_windows_ui(layout)

        self._build_updates_ui(layout)
        self._build_diagnostics_ui(layout)
        layout.addStretch()

        scroll.setWidget(container)

    def _build_service_strategy_row(self, layout):
        row = QHBoxLayout()
        row.addWidget(QLabel("Strategy:"))
        self.svc_strategy_combo = QComboBox()
        self.svc_strategy_combo.setMinimumWidth(200)
        row.addWidget(self.svc_strategy_combo, 1)
        layout.addLayout(row)

    def _get_selected_strategy(self):
        name = self.svc_strategy_combo.currentText()
        if name and name in self._strategies:
            return name, self._strategies[name]
        return None, None

    def _build_linux_ui(self, layout):
        engine_group = QGroupBox("Zapret Engine")
        eg_layout = QVBoxLayout(engine_group)

        info = QLabel("Install zapret v72.13 to /opt/zapret from GitHub")
        info.setWordWrap(True)
        eg_layout.addWidget(info)

        btn_row = QHBoxLayout()
        self.btn_download = QPushButton("Install / Update")
        self.btn_download.setMinimumHeight(32)
        self.btn_download.clicked.connect(self._download_zapret)
        btn_row.addWidget(self.btn_download)
        eg_layout.addLayout(btn_row)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        eg_layout.addWidget(self.progress_bar)

        self.download_status = QLabel("")
        self.download_status.setObjectName("subHeaderLabel")
        eg_layout.addWidget(self.download_status)

        layout.addWidget(engine_group)

        service_group = QGroupBox("Systemd Service")
        sv_layout = QVBoxLayout(service_group)

        info2 = QLabel("Install, update or remove a systemd service for auto-start on boot")
        sv_layout.addWidget(info2)

        self._build_service_strategy_row(sv_layout)

        svc_grid = QGridLayout()
        svc_grid.setSpacing(6)

        self.btn_create_svc = QPushButton("Install / Update Service")
        self.btn_create_svc.setMinimumHeight(32)
        self.btn_create_svc.clicked.connect(self._create_service)
        svc_grid.addWidget(self.btn_create_svc, 0, 0)

        self.btn_remove_svc = QPushButton("Remove Service")
        self.btn_remove_svc.setObjectName("stopBtn")
        self.btn_remove_svc.setMinimumHeight(32)
        self.btn_remove_svc.clicked.connect(self._remove_service)
        svc_grid.addWidget(self.btn_remove_svc, 0, 1)

        self.btn_start_svc = QPushButton("Start Service")
        self.btn_start_svc.setMinimumHeight(32)
        self.btn_start_svc.clicked.connect(self._start_service)
        svc_grid.addWidget(self.btn_start_svc, 1, 0)

        self.btn_stop_svc = QPushButton("Stop Service")
        self.btn_stop_svc.setObjectName("stopBtn")
        self.btn_stop_svc.setMinimumHeight(32)
        self.btn_stop_svc.clicked.connect(self._stop_service)
        svc_grid.addWidget(self.btn_stop_svc, 1, 1)

        sv_layout.addLayout(svc_grid)

        btn_row4 = QHBoxLayout()
        self.chk_autostart = QCheckBox("Enable on boot (auto-start)")
        self.chk_autostart.clicked.connect(self._toggle_autostart)
        btn_row4.addWidget(self.chk_autostart)
        btn_row4.addStretch()
        sv_layout.addLayout(btn_row4)

        self.svc_status_label = QLabel("Status: checking...")
        self.svc_status_label.setObjectName("subHeaderLabel")
        sv_layout.addWidget(self.svc_status_label)

        layout.addWidget(service_group)

        desktop_group = QGroupBox("App Menu Entry")
        dt_layout = QVBoxLayout(desktop_group)

        info4 = QLabel("Add/remove Mangopret from your application menu")
        dt_layout.addWidget(info4)

        dt_row = QHBoxLayout()
        self.btn_install_desktop = QPushButton("Install to Menu")
        self.btn_install_desktop.setMinimumHeight(32)
        self.btn_install_desktop.clicked.connect(self._install_desktop_entry)
        dt_row.addWidget(self.btn_install_desktop)

        self.btn_remove_desktop = QPushButton("Remove from Menu")
        self.btn_remove_desktop.setObjectName("stopBtn")
        self.btn_remove_desktop.setMinimumHeight(32)
        self.btn_remove_desktop.clicked.connect(self._remove_desktop_entry)
        dt_row.addWidget(self.btn_remove_desktop)
        dt_row.addStretch()
        dt_layout.addLayout(dt_row)

        layout.addWidget(desktop_group)

    def _build_windows_ui(self, layout):
        service_group = QGroupBox("Windows Service")
        sv_layout = QVBoxLayout(service_group)

        info = QLabel("Install, update or remove the Windows service (auto-start on boot)")
        sv_layout.addWidget(info)

        self._build_service_strategy_row(sv_layout)

        svc_grid = QGridLayout()
        svc_grid.setSpacing(6)

        self.btn_install_svc = QPushButton("Install / Update Service")
        self.btn_install_svc.setMinimumHeight(32)
        self.btn_install_svc.clicked.connect(self._install_service)
        svc_grid.addWidget(self.btn_install_svc, 0, 0)

        self.btn_remove_svc = QPushButton("Remove Service")
        self.btn_remove_svc.setObjectName("stopBtn")
        self.btn_remove_svc.setMinimumHeight(32)
        self.btn_remove_svc.clicked.connect(self._remove_service)
        svc_grid.addWidget(self.btn_remove_svc, 0, 1)

        self.btn_start_svc = QPushButton("Start Service")
        self.btn_start_svc.setMinimumHeight(32)
        self.btn_start_svc.clicked.connect(self._start_service)
        svc_grid.addWidget(self.btn_start_svc, 1, 0)

        self.btn_stop_svc = QPushButton("Stop Service")
        self.btn_stop_svc.setObjectName("stopBtn")
        self.btn_stop_svc.setMinimumHeight(32)
        self.btn_stop_svc.clicked.connect(self._stop_service)
        svc_grid.addWidget(self.btn_stop_svc, 1, 1)

        self.btn_check_svc = QPushButton("Check Status")
        self.btn_check_svc.setObjectName("secondaryBtn")
        self.btn_check_svc.setMinimumHeight(32)
        self.btn_check_svc.clicked.connect(self._check_service)
        svc_grid.addWidget(self.btn_check_svc, 1, 2)

        sv_layout.addLayout(svc_grid)

        self.svc_status_label = QLabel("Status: checking...")
        self.svc_status_label.setObjectName("subHeaderLabel")
        sv_layout.addWidget(self.svc_status_label)

        layout.addWidget(service_group)

    def _build_updates_ui(self, layout):
        updates_group = QGroupBox("Updates")
        up_layout = QVBoxLayout(updates_group)

        up_grid = QGridLayout()
        up_grid.setSpacing(6)

        btn_ipset = QPushButton("Update IPSet List")
        btn_ipset.setMinimumHeight(28)
        btn_ipset.clicked.connect(self._update_ipset)
        up_grid.addWidget(btn_ipset, 0, 0)

        btn_hosts = QPushButton("Update Hosts File")
        btn_hosts.setMinimumHeight(28)
        btn_hosts.clicked.connect(self._update_hosts)
        up_grid.addWidget(btn_hosts, 0, 1)

        btn_updates = QPushButton("Check for Updates")
        btn_updates.setObjectName("secondaryBtn")
        btn_updates.setMinimumHeight(28)
        btn_updates.clicked.connect(self._check_updates)
        up_grid.addWidget(btn_updates, 0, 2)

        up_layout.addLayout(up_grid)

        layout.addWidget(updates_group)

    def _build_diagnostics_ui(self, layout):
        diag_group = QGroupBox("Diagnostics")
        dg_layout = QVBoxLayout(diag_group)

        btn_diag = QPushButton("Run Diagnostics")
        btn_diag.setMinimumHeight(28)
        btn_diag.clicked.connect(self._run_diagnostics)
        dg_layout.addWidget(btn_diag)

        self.diag_text = QTextEdit()
        self.diag_text.setReadOnly(True)
        self.diag_text.setFontFamily("Consolas")
        self.diag_text.setMaximumHeight(180)
        dg_layout.addWidget(self.diag_text)

        layout.addWidget(diag_group)

    def refresh_status(self):
        status = self.platform.get_service_status()
        if self.platform.is_linux:
            enabled = self.platform.is_service_enabled()
            status_text = f"Status: {status.upper()}"
            if enabled:
                status_text += " | Auto-start: ON"
            self.svc_status_label.setText(status_text)
            self.chk_autostart.setChecked(enabled)
        else:
            self.svc_status_label.setText(f"Status: {status.upper()}")

    def _download_zapret(self):
        self.btn_download.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)

        self._download_thread = DownloadThread(self.platform)
        self._download_thread.progress.connect(self._on_download_progress)
        self._download_thread.finished.connect(self._on_download_finished)
        self._download_thread.start()

    def _on_download_progress(self, msg):
        self.download_status.setText(msg)
        self.log_signal.emit(msg)

    def _on_download_finished(self, success):
        self.btn_download.setEnabled(True)
        self.progress_bar.setVisible(False)
        if success:
            self.download_status.setText("Zapret installed / updated successfully!")
            self.log_signal.emit("Zapret installed / updated successfully")
        else:
            self.download_status.setText("Installation failed - check log")
            self.log_signal.emit("Zapret installation failed")

    def _create_service(self):
        if not self.platform.is_linux:
            return

        name, strategy = self._get_selected_strategy()
        if not strategy:
            QMessageBox.warning(self, "Error", "Select a strategy first")
            return

        ok = self.platform.create_systemd_service(strategy, name)
        if ok:
            self.diag_text.append(f"Service installed/updated: {name}")
            self.log_signal.emit(f"Service installed/updated: {name}")

            was_running = self.platform.get_service_status() == "running"
            if was_running:
                self.platform.service_stop()
                self.platform.service_start()
                self.diag_text.append("Service restarted with new config")
                self.log_signal.emit("Service restarted with new config")
        else:
            self.diag_text.append("Failed to create systemd service (need root?)")
            self.log_signal.emit("Failed to create systemd service")
        self.refresh_status()

    def _remove_service(self):
        reply = QMessageBox.question(
            self, "Confirm", "Remove service?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        ok, err = self.platform.service_remove()
        if ok:
            self.diag_text.append("Service removed")
            self.log_signal.emit("Service removed")
            self.platform.kill_all()
        else:
            self.diag_text.append(f"Failed to remove: {err}")
        self.refresh_status()

    def _start_service(self):
        ok, err = self.platform.service_start()

        if ok:
            self.diag_text.append("Service started")
            self.log_signal.emit("Service started")
        else:
            self.diag_text.append(f"Failed to start: {err}")
            self.log_signal.emit(f"Service start failed: {err}")
        self.refresh_status()

    def _stop_service(self):
        ok, err = self.platform.service_stop()

        if ok:
            self.diag_text.append("Service stopped")
            self.log_signal.emit("Service stopped")
        else:
            self.diag_text.append(f"Failed to stop: {err}")
            self.log_signal.emit(f"Service stop failed: {err}")
        self.refresh_status()

    def _install_service(self):
        name, strategy = self._get_selected_strategy()

        ok, err = self.platform.service_install(strategy, name or "")
        if ok:
            self.diag_text.append(f"Service installed/updated: {name}" if name else "Service installed")
            self.log_signal.emit(f"Service installed: {name}")
        else:
            self.diag_text.append(f"Failed: {err}" if err else "Failed to install service")
        self.refresh_status()

    def _check_service(self):
        status = self.platform.get_service_status()
        running = self.platform.is_process_running()
        self.diag_text.append(f"Service: {status}")
        self.diag_text.append(f"Process: {'running' if running else 'not running'}")
        self.log_signal.emit(f"Status: service={status}, process={'running' if running else 'stopped'}")
        self.refresh_status()

    def _toggle_autostart(self):
        if not self.platform.is_linux:
            return
        enabled = self.chk_autostart.isChecked()
        if enabled:
            ok, err = self.platform.enable_systemd_service()
        else:
            ok, err = self.platform.disable_systemd_service()

        if ok:
            state = "enabled" if enabled else "disabled"
            self.diag_text.append(f"Auto-start {state}")
            self.log_signal.emit(f"Auto-start {state}")
        else:
            self.diag_text.append(f"Failed to change auto-start: {err}")
        self.refresh_status()

    def _install_desktop_entry(self):
        ok, msg = self.platform.create_desktop_entry()
        if ok:
            self.diag_text.append(f"Desktop entry installed: {msg}")
            self.log_signal.emit(f"Desktop entry installed: {msg}")
        else:
            self.diag_text.append(f"Failed to install desktop entry: {msg}")
            self.log_signal.emit(f"Failed: {msg}")

    def _remove_desktop_entry(self):
        ok, msg = self.platform.remove_desktop_entry()
        if ok:
            self.diag_text.append("Desktop entry removed")
            self.log_signal.emit("Desktop entry removed")
        else:
            self.diag_text.append(f"Failed: {msg}")

    def _update_ipset(self):
        def callback(msg):
            self.diag_text.append(msg)
            self.log_signal.emit(msg)

        import threading
        t = threading.Thread(
            target=self.list_manager.update_ipset,
            args=(callback,),
            daemon=True,
        )
        t.start()
        self.log_signal.emit("IPSet update started...")

    def _update_hosts(self):
        def callback(msg):
            self.diag_text.append(msg)
            self.log_signal.emit(msg)

        import threading
        t = threading.Thread(
            target=self.list_manager.update_hosts,
            args=(callback,),
            daemon=True,
        )
        t.start()

    def _check_updates(self):
        self.diag_text.append("Checking for updates...")
        self.log_signal.emit("Checking for updates...")
        try:
            import urllib.request
            url = "https://raw.githubusercontent.com/Flowseal/zapret-discord-youtube/main/.service/version.txt"
            req = urllib.request.Request(url, headers={"User-Agent": "Mangopret"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                remote_version = resp.read().decode().strip()
            self.diag_text.append(f"Remote version: {remote_version}")
            self.log_signal.emit(f"Remote version: {remote_version}")
        except Exception as e:
            self.diag_text.append(f"Failed to check: {e}")

    def _run_diagnostics(self):
        result = self.list_manager.run_diagnostics(self.platform.is_windows)
        self.diag_text.setPlainText(result)
        self.log_signal.emit("Diagnostics completed")
