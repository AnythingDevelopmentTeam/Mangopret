from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QTextEdit, QLabel, QMessageBox,
    QProgressBar, QCheckBox,
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

        result = self.platform.download_zapret(callback=callback)
        self.finished.emit(result)


class ServiceTab(QWidget):
    log_signal = pyqtSignal(str)

    def __init__(self, platform_info, config, list_manager, parent=None):
        super().__init__(parent)
        self.platform = platform_info
        self.config = config
        self.list_manager = list_manager
        self._download_thread = None
        self._strategy_provider = None
        self._build_ui()

    def set_strategy_provider(self, provider):
        self._strategy_provider = provider

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

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

    def _build_linux_ui(self, layout):
        engine_group = QGroupBox("Zapret Engine")
        eg_layout = QVBoxLayout(engine_group)

        info = QLabel("Download the zapret engine (nfqws) from GitHub")
        info.setWordWrap(True)
        eg_layout.addWidget(info)

        btn_row = QHBoxLayout()
        self.btn_download = QPushButton("Download / Update")
        self.btn_download.setMinimumHeight(36)
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

        info2 = QLabel("Create and manage a systemd service for auto-start on boot")
        sv_layout.addWidget(info2)

        btn_row2 = QHBoxLayout()
        self.btn_create_svc = QPushButton("Create Service")
        self.btn_create_svc.setMinimumHeight(36)
        self.btn_create_svc.clicked.connect(self._create_service)
        btn_row2.addWidget(self.btn_create_svc)

        self.btn_remove_svc = QPushButton("Remove Service")
        self.btn_remove_svc.setObjectName("stopBtn")
        self.btn_remove_svc.setMinimumHeight(36)
        self.btn_remove_svc.clicked.connect(self._remove_service)
        btn_row2.addWidget(self.btn_remove_svc)
        sv_layout.addLayout(btn_row2)

        btn_row3 = QHBoxLayout()
        self.btn_start_svc = QPushButton("Start Service")
        self.btn_start_svc.setMinimumHeight(36)
        self.btn_start_svc.clicked.connect(self._start_service)
        btn_row3.addWidget(self.btn_start_svc)

        self.btn_stop_svc = QPushButton("Stop Service")
        self.btn_stop_svc.setObjectName("stopBtn")
        self.btn_stop_svc.setMinimumHeight(36)
        self.btn_stop_svc.clicked.connect(self._stop_service)
        btn_row3.addWidget(self.btn_stop_svc)
        sv_layout.addLayout(btn_row3)

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

        nftables_group = QGroupBox("iptables / nftables")
        nf_layout = QVBoxLayout(nftables_group)

        info3 = QLabel("Apply firewall rules to redirect traffic through nfqws")
        nf_layout.addWidget(info3)

        btn_row5 = QHBoxLayout()
        self.btn_apply_rules = QPushButton("Apply Rules")
        self.btn_apply_rules.setMinimumHeight(36)
        self.btn_apply_rules.clicked.connect(self._apply_rules)
        btn_row5.addWidget(self.btn_apply_rules)

        self.btn_remove_rules = QPushButton("Remove Rules")
        self.btn_remove_rules.setObjectName("stopBtn")
        self.btn_remove_rules.setMinimumHeight(36)
        self.btn_remove_rules.clicked.connect(self._remove_rules)
        btn_row5.addWidget(self.btn_remove_rules)
        nf_layout.addLayout(btn_row5)

        layout.addWidget(nftables_group)

    def _build_windows_ui(self, layout):
        service_group = QGroupBox("Windows Service")
        sv_layout = QVBoxLayout(service_group)

        info = QLabel("Manage the Windows service (auto-start on boot)")
        sv_layout.addWidget(info)

        btn_row = QHBoxLayout()
        self.btn_install_svc = QPushButton("Install Service")
        self.btn_install_svc.setMinimumHeight(36)
        self.btn_install_svc.clicked.connect(self._install_service)
        btn_row.addWidget(self.btn_install_svc)

        self.btn_remove_svc = QPushButton("Remove Service")
        self.btn_remove_svc.setObjectName("stopBtn")
        self.btn_remove_svc.setMinimumHeight(36)
        self.btn_remove_svc.clicked.connect(self._remove_service)
        btn_row.addWidget(self.btn_remove_svc)
        sv_layout.addLayout(btn_row)

        btn_row2 = QHBoxLayout()
        self.btn_start_svc = QPushButton("Start Service")
        self.btn_start_svc.setMinimumHeight(36)
        self.btn_start_svc.clicked.connect(self._start_service)
        btn_row2.addWidget(self.btn_start_svc)

        self.btn_stop_svc = QPushButton("Stop Service")
        self.btn_stop_svc.setObjectName("stopBtn")
        self.btn_stop_svc.setMinimumHeight(36)
        self.btn_stop_svc.clicked.connect(self._stop_service)
        btn_row2.addWidget(self.btn_stop_svc)

        self.btn_check_svc = QPushButton("Check Status")
        self.btn_check_svc.setObjectName("secondaryBtn")
        self.btn_check_svc.setMinimumHeight(36)
        self.btn_check_svc.clicked.connect(self._check_service)
        btn_row2.addWidget(self.btn_check_svc)
        sv_layout.addLayout(btn_row2)

        self.svc_status_label = QLabel("Status: checking...")
        self.svc_status_label.setObjectName("subHeaderLabel")
        sv_layout.addWidget(self.svc_status_label)

        layout.addWidget(service_group)

    def _build_updates_ui(self, layout):
        updates_group = QGroupBox("Updates")
        up_layout = QVBoxLayout(updates_group)

        btn_row = QHBoxLayout()
        btn_ipset = QPushButton("Update IPSet List")
        btn_ipset.clicked.connect(self._update_ipset)
        btn_row.addWidget(btn_ipset)

        btn_hosts = QPushButton("Update Hosts File")
        btn_hosts.clicked.connect(self._update_hosts)
        btn_row.addWidget(btn_hosts)

        btn_updates = QPushButton("Check for Updates")
        btn_updates.setObjectName("secondaryBtn")
        btn_updates.clicked.connect(self._check_updates)
        btn_row.addWidget(btn_updates)
        up_layout.addLayout(btn_row)

        layout.addWidget(updates_group)

    def _build_diagnostics_ui(self, layout):
        diag_group = QGroupBox("Diagnostics")
        dg_layout = QVBoxLayout(diag_group)

        btn_diag = QPushButton("Run Diagnostics")
        btn_diag.clicked.connect(self._run_diagnostics)
        dg_layout.addWidget(btn_diag)

        self.diag_text = QTextEdit()
        self.diag_text.setReadOnly(True)
        self.diag_text.setFontFamily("Consolas")
        self.diag_text.setMaximumHeight(200)
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
            self.download_status.setText("Engine downloaded successfully!")
            self.log_signal.emit("Engine downloaded successfully")
        else:
            self.download_status.setText("Download failed - check log")
            self.log_signal.emit("Engine download failed")

    def _create_service(self):
        if not self.platform.is_linux:
            return
        if not self._strategy_provider:
            QMessageBox.warning(self, "Error", "No strategy selected")
            return

        result = self._strategy_provider()
        if not result:
            QMessageBox.warning(self, "Error", "No strategy selected")
            return

        strategy_name, strategy_cmd = result
        ok = self.platform.create_systemd_service(strategy_cmd, strategy_name)
        if ok:
            self.diag_text.append(f"Systemd service created for: {strategy_name}")
            self.log_signal.emit(f"Systemd service created for: {strategy_name}")
            self.refresh_status()
        else:
            self.diag_text.append("Failed to create systemd service (need root?)")
            self.log_signal.emit("Failed to create systemd service")

    def _remove_service(self):
        reply = QMessageBox.question(
            self, "Confirm", "Remove service?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        if self.platform.is_windows:
            self._remove_windows_service()
        else:
            self._remove_linux_service()

    def _remove_windows_service(self):
        import subprocess
        for svc in ["zapret", "WinDivert"]:
            subprocess.run(
                ["net", "stop", svc], capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            subprocess.run(
                ["sc", "delete", svc], capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        self.platform.kill_all()
        self.log_signal.emit("Windows services removed")
        self.refresh_status()

    def _remove_linux_service(self):
        ok, err = self.platform.remove_systemd_service()
        if ok:
            self.diag_text.append("Systemd service removed")
            self.log_signal.emit("Systemd service removed")
        else:
            self.diag_text.append(f"Failed to remove: {err}")
        self.refresh_status()

    def _start_service(self):
        if self.platform.is_windows:
            ok, err = self.platform.start_windows_service()
        else:
            ok, err = self.platform.start_systemd_service()

        if ok:
            self.diag_text.append("Service started")
            self.log_signal.emit("Service started")
        else:
            self.diag_text.append(f"Failed to start: {err}")
            self.log_signal.emit(f"Service start failed: {err}")
        self.refresh_status()

    def _stop_service(self):
        if self.platform.is_windows:
            ok, err = self.platform.stop_windows_service()
        else:
            ok, err = self.platform.stop_systemd_service()

        if ok:
            self.diag_text.append("Service stopped")
            self.log_signal.emit("Service stopped")
        else:
            self.diag_text.append(f"Failed to stop: {err}")
            self.log_signal.emit(f"Service stop failed: {err}")
        self.refresh_status()

    def _install_service(self):
        if not self.platform.is_windows:
            return
        import subprocess

        bin_path = str(self.platform.binary)
        cmd_args = ""

        if self._strategy_provider:
            result = self._strategy_provider()
            if result:
                strategy_name, strategy_cmd = result
                cmd_args = " ".join(str(x) for x in strategy_cmd[1:])
                self.log_signal.emit(f"Installing service with strategy: {strategy_name}")

        try:
            if cmd_args:
                sc_cmd = f'"{bin_path}" {cmd_args}'
                r = subprocess.run(
                    ["sc", "create", "zapret", "binPath=", sc_cmd,
                     "DisplayName=", "zapret", "start=", "auto"],
                    capture_output=True, text=True, timeout=10,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
            else:
                r = subprocess.run(
                    ["sc", "create", "zapret", "binPath=", f'"{bin_path}"',
                     "DisplayName=", "zapret", "start=", "auto"],
                    capture_output=True, text=True, timeout=10,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
            self.diag_text.append(r.stdout)
            if r.stderr:
                self.diag_text.append(r.stderr)
            self.log_signal.emit("Service installation attempted")
            self.refresh_status()
        except Exception as e:
            self.diag_text.append(f"Error: {e}")

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

    def _apply_rules(self):
        if not self.platform.is_linux:
            return

        wf_tcp = self.config.get("wf_tcp", "80,443,2053,2083,2087,2096,8443")
        wf_udp = self.config.get("wf_udp", "443,19294-19344,50000-50100")
        queue_num = self.config.get("nfqueue_num", "200")

        results = self.platform.install_iptables_rules(wf_tcp, wf_udp, queue_num)
        for rule, ok, err in results:
            if ok:
                self.diag_text.append(f"OK: {rule}")
            else:
                self.diag_text.append(f"FAIL: {rule} -> {err}")
        self.log_signal.emit(f"Applied {len(results)} iptables rules")

    def _remove_rules(self):
        if not self.platform.is_linux:
            return
        ok = self.platform.remove_iptables_rules()
        if ok:
            self.diag_text.append("iptables rules removed")
            self.log_signal.emit("iptables rules removed")
        else:
            self.diag_text.append("Failed to remove iptables rules")

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
