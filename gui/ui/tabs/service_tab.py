from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QTextEdit, QLabel, QMessageBox,
    QProgressBar,
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
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        header = QLabel("Service & Updates")
        header.setObjectName("headerLabel")
        layout.addWidget(header)

        if self.platform.is_linux:
            linux_group = QGroupBox("Zapret Engine (Linux)")
            lg_layout = QVBoxLayout(linux_group)

            info = QLabel("The zapret engine (bol-van/zapret) will be downloaded from GitHub")
            info.setWordWrap(True)
            lg_layout.addWidget(info)

            btn_row = QHBoxLayout()
            self.btn_download = QPushButton("Download / Update Engine")
            self.btn_download.setMinimumHeight(36)
            self.btn_download.clicked.connect(self._download_zapret)
            btn_row.addWidget(self.btn_download)

            self.btn_nftables = QPushButton("Setup nftables rules")
            self.btn_nftables.setObjectName("secondaryBtn")
            self.btn_nftables.setMinimumHeight(36)
            self.btn_nftables.clicked.connect(self._setup_nftables)
            btn_row.addWidget(self.btn_nftables)
            lg_layout.addLayout(btn_row)

            self.progress_bar = QProgressBar()
            self.progress_bar.setVisible(False)
            lg_layout.addWidget(self.progress_bar)

            self.download_status = QLabel("")
            self.download_status.setObjectName("subHeaderLabel")
            lg_layout.addWidget(self.download_status)

            layout.addWidget(linux_group)

        if self.platform.is_windows:
            service_group = QGroupBox("Windows Service")
            sv_layout = QVBoxLayout(service_group)

            info = QLabel("Manage Windows service (auto-start on boot)")
            sv_layout.addWidget(info)

            btn_row = QHBoxLayout()
            btn_install = QPushButton("Install Service")
            btn_install.clicked.connect(self._install_service)
            btn_row.addWidget(btn_install)

            btn_remove = QPushButton("Remove Service")
            btn_remove.setObjectName("stopBtn")
            btn_remove.clicked.connect(self._remove_service)
            btn_row.addWidget(btn_remove)

            btn_status = QPushButton("Check Status")
            btn_status.setObjectName("secondaryBtn")
            btn_status.clicked.connect(self._check_service)
            btn_row.addWidget(btn_status)
            sv_layout.addLayout(btn_row)

            layout.addWidget(service_group)

        updates_group = QGroupBox("Updates")
        up_layout = QVBoxLayout(updates_group)

        btn_row2 = QHBoxLayout()
        btn_ipset = QPushButton("Update IPSet List")
        btn_ipset.clicked.connect(self._update_ipset)
        btn_row2.addWidget(btn_ipset)

        btn_hosts = QPushButton("Update Hosts File")
        btn_hosts.clicked.connect(self._update_hosts)
        btn_row2.addWidget(btn_hosts)

        btn_updates = QPushButton("Check for Updates")
        btn_updates.setObjectName("secondaryBtn")
        btn_updates.clicked.connect(self._check_updates)
        btn_row2.addWidget(btn_updates)
        up_layout.addLayout(btn_row2)

        layout.addWidget(updates_group)

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
        layout.addStretch()

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
            self.download_status.setText("Zapret engine downloaded successfully!")
            self.log_signal.emit("Zapret engine downloaded successfully")
        else:
            self.download_status.setText("Download failed - check log")
            self.log_signal.emit("zapret engine download failed")

    def _setup_nftables(self):
        if self.platform.is_linux:
            try:
                rules = self.platform.build_iptables_rules(
                    "80,443,2053,2083,2087,2096,8443",
                    "443,19294-19344,50000-50100",
                    self.config.get("nfqueue_num", "200"),
                )
                self.diag_text.append("Setting up iptables rules...")
                for rule in rules:
                    import subprocess
                    r = subprocess.run(rule.split(), capture_output=True, text=True, timeout=10)
                    if r.returncode != 0:
                        self.diag_text.append(f"Warning: {rule} -> {r.stderr.strip()}")
                    else:
                        self.diag_text.append(f"OK: {rule}")
                self.log_signal.emit("nftables/iptables rules applied")
            except Exception as e:
                self.diag_text.append(f"Error setting up rules: {e}")
                self.log_signal.emit(f"iptables error: {e}")

    def _install_service(self):
        if not self.platform.is_windows:
            return
        import subprocess
        try:
            r = subprocess.run(
                ["sc", "create", "zapret", "binPath=", f'"{self.platform.binary}"',
                 "DisplayName=", "zapret", "start=", "auto"],
                capture_output=True, text=True, timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            self.diag_text.append(r.stdout)
            if r.stderr:
                self.diag_text.append(r.stderr)
            self.log_signal.emit("Service installation attempted")
        except Exception as e:
            self.diag_text.append(f"Error: {e}")

    def _remove_service(self):
        reply = QMessageBox.question(
            self, "Confirm", "Remove zapret service?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        if self.platform.is_windows:
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

    def _check_service(self):
        status = self.platform.get_service_status()
        running = self.platform.is_process_running()
        self.diag_text.append(f"Service: {status}")
        self.diag_text.append(f"Process: {'running' if running else 'not running'}")
        self.log_signal.emit(f"Status: service={status}, process={'running' if running else 'stopped'}")

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
            import json
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
