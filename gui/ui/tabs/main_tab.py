from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class MainTab(QWidget):
    start_requested = pyqtSignal(str)
    stop_requested = pyqtSignal()
    ipset_changed = pyqtSignal(str)
    refresh_requested = pyqtSignal()
    test_requested = pyqtSignal()
    log_signal = pyqtSignal(str)
    startup_changed = pyqtSignal(bool)

    def __init__(self, platform=None, config=None, list_manager=None, parent=None):
        super().__init__(parent)
        self.platform = platform
        self.config = config
        self.list_manager = list_manager
        self._active_strategy = ""
        self._strategies = {}
        self._build_ui()

    def set_strategies_dict(self, strategies: dict):
        self._strategies = strategies

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

        header = QLabel("Mangopret")
        header.setObjectName("headerLabel")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        subtitle = QLabel("Cross-platform DPI bypass manager")
        subtitle.setObjectName("subHeaderLabel")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        layout.addSpacing(4)

        self._build_quick_controls(layout)

        self._build_status(layout)

        self._build_strategy(layout)

        self._build_startup_ui(layout)

        self._build_updates_ui(layout)

        self._build_diagnostics_ui(layout)

        layout.addStretch()

        scroll.setWidget(container)

    def _build_quick_controls(self, layout):
        group = QGroupBox("Quick Controls")
        g_layout = QVBoxLayout(group)
        g_layout.setSpacing(6)

        ip_row = QHBoxLayout()
        ip_row.addWidget(QLabel("IPSet mode:"))
        self.ipset_group = QButtonGroup()
        for i, (val, text) in enumerate(
            [
                ("none", "None"),
                ("loaded", "Loaded"),
                ("any", "Any"),
            ]
        ):
            rb = QRadioButton(text)
            self.ipset_group.addButton(rb, i)
            rb.setProperty("ipset_value", val)
            rb.clicked.connect(self._on_ipset)
            ip_row.addWidget(rb)
        ip_row.addStretch()
        g_layout.addLayout(ip_row)

        btn_grid = QGridLayout()
        btn_grid.setSpacing(6)

        btn_refresh = QPushButton("Refresh")
        btn_refresh.setObjectName("secondaryBtn")
        btn_refresh.setMinimumHeight(28)
        btn_refresh.clicked.connect(self.refresh_requested.emit)
        btn_grid.addWidget(btn_refresh, 0, 0)

        btn_test = QPushButton("Test Sites")
        btn_test.setObjectName("secondaryBtn")
        btn_test.setMinimumHeight(28)
        btn_test.clicked.connect(self.test_requested.emit)
        btn_grid.addWidget(btn_test, 0, 1)

        g_layout.addLayout(btn_grid)

        layout.addWidget(group)

    def _build_status(self, layout):
        group = QGroupBox("Status")
        g_layout = QVBoxLayout(group)
        g_layout.setSpacing(4)

        self.status_labels = {}
        for key, label_text in [
            ("service", "Service:"),
            ("ipset", "IPSet filter:"),
        ]:
            row = QHBoxLayout()
            lbl = QLabel(label_text)
            lbl.setFixedWidth(110)
            row.addWidget(lbl)
            val = QLabel("checking...")
            val.setObjectName("statusWarn")
            row.addWidget(val)
            row.addStretch()
            g_layout.addLayout(row)
            self.status_labels[key] = val

        layout.addWidget(group)

    def _build_strategy(self, layout):
        group = QGroupBox("Strategy")
        g_layout = QVBoxLayout(group)

        row = QHBoxLayout()
        row.addWidget(QLabel("Select:"))
        self.strategy_combo = QComboBox()
        self.strategy_combo.setMinimumWidth(200)
        row.addWidget(self.strategy_combo, 1)
        g_layout.addLayout(row)

        self.description_label = QLabel("")
        self.description_label.setWordWrap(True)
        self.description_label.setObjectName("subHeaderLabel")
        g_layout.addWidget(self.description_label)

        btn_row = QHBoxLayout()
        self.btn_start = QPushButton("Start")
        self.btn_start.setMinimumHeight(32)
        self.btn_start.clicked.connect(self._on_start)
        btn_row.addWidget(self.btn_start)

        self.btn_stop = QPushButton("Stop")
        self.btn_stop.setObjectName("stopBtn")
        self.btn_stop.setMinimumHeight(32)
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self._on_stop)
        btn_row.addWidget(self.btn_stop)
        g_layout.addLayout(btn_row)

        if self.platform and self.platform.is_linux:
            sep = QFrame()
            sep.setFrameShape(QFrame.Shape.HLine)
            sep.setStyleSheet("color: #444;")
            g_layout.addWidget(sep)

            svc_row = QHBoxLayout()
            self.btn_create_svc = QPushButton("Install / Update Service")
            self.btn_create_svc.setMinimumHeight(28)
            self.btn_create_svc.clicked.connect(self._create_service)
            svc_row.addWidget(self.btn_create_svc)

            self.btn_remove_svc = QPushButton("Remove Service")
            self.btn_remove_svc.setObjectName("stopBtn")
            self.btn_remove_svc.setMinimumHeight(28)
            self.btn_remove_svc.clicked.connect(self._remove_service)
            svc_row.addWidget(self.btn_remove_svc)
            g_layout.addLayout(svc_row)

            un_row = QHBoxLayout()
            self.btn_uninstall = QPushButton("Remove Zapret")
            self.btn_uninstall.setObjectName("stopBtn")
            self.btn_uninstall.setMinimumHeight(28)
            self.btn_uninstall.clicked.connect(self._uninstall_zapret)
            un_row.addWidget(self.btn_uninstall)
            un_row.addStretch()
            g_layout.addLayout(un_row)

            # DEPRECATED: will be removed in 1.3.0 (autostart checkbox removed)
            # boot_row = QHBoxLayout()
            # self.chk_autostart = QCheckBox("Enable on boot")
            # self.chk_autostart.clicked.connect(self._toggle_autostart)
            # boot_row.addWidget(self.chk_autostart)
            # boot_row.addStretch()
            # g_layout.addLayout(boot_row)

            self.svc_status_label = QLabel("")
            self.svc_status_label.setObjectName("subHeaderLabel")
            g_layout.addWidget(self.svc_status_label)

        layout.addWidget(group)

    def _build_startup_ui(self, layout):
        pass  # DEPRECATED: will be removed in 1.3.0

    def _build_updates_ui(self, layout):
        group = QGroupBox("Updates")
        g_layout = QVBoxLayout(group)

        btn_grid = QGridLayout()
        btn_grid.setSpacing(6)

        btn_ipset = QPushButton("Update IPSet List")
        btn_ipset.setMinimumHeight(28)
        btn_ipset.clicked.connect(self._update_ipset)
        btn_grid.addWidget(btn_ipset, 0, 0)

        btn_hosts = QPushButton("Update Hosts File")
        btn_hosts.setMinimumHeight(28)
        btn_hosts.clicked.connect(self._update_hosts)
        btn_grid.addWidget(btn_hosts, 0, 1)

        btn_updates = QPushButton("Check for Updates")
        btn_updates.setObjectName("secondaryBtn")
        btn_updates.setMinimumHeight(28)
        btn_updates.clicked.connect(self._check_updates)
        btn_grid.addWidget(btn_updates, 0, 2)

        g_layout.addLayout(btn_grid)

        layout.addWidget(group)

    def _build_diagnostics_ui(self, layout):
        group = QGroupBox("Diagnostics")
        g_layout = QVBoxLayout(group)

        btn_diag = QPushButton("Run Diagnostics")
        btn_diag.setMinimumHeight(28)
        btn_diag.clicked.connect(self._run_diagnostics)
        g_layout.addWidget(btn_diag)

        self.diag_text = QTextEdit()
        self.diag_text.setReadOnly(True)
        self.diag_text.setFontFamily("Consolas")
        self.diag_text.setMaximumHeight(180)
        g_layout.addWidget(self.diag_text)

        layout.addWidget(group)

    def set_strategies(self, strategies: list, current: str = ""):
        self.strategy_combo.clear()
        for name, _ in strategies:
            self.strategy_combo.addItem(name)
        if current:
            idx = self.strategy_combo.findText(current)
            if idx >= 0:
                self.strategy_combo.setCurrentIndex(idx)

    def get_selected_strategy(self) -> str:
        return self.strategy_combo.currentText()

    def set_description(self, text: str):
        self.description_label.setText(text)

    def set_active(self, active: bool, strategy_name: str = ""):
        self._active_strategy = strategy_name if active else ""
        self.btn_start.setText("Start" if not active else "Switch")
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(active)

    def set_status(self, key: str, text: str, status: str = "ok"):
        if key in self.status_labels:
            self.status_labels[key].setText(text)
            obj_name = {
                "ok": "statusOk",
                "error": "statusErr",
                "warn": "statusWarn",
                "running": "statusOk",
                "stopped": "statusErr",
            }.get(status, "statusWarn")
            self.status_labels[key].setObjectName(obj_name)
            self.status_labels[key].setStyleSheet("")

    def set_ipset(self, mode: str):
        for btn in self.ipset_group.buttons():
            if btn.property("ipset_value") == mode:
                btn.setChecked(True)
                break

    def refresh_service_status(self):
        if not self.platform or not self.platform.is_linux:
            return
        status = self.platform.get_service_status()
        enabled = self.platform.is_service_enabled()
        parts = [f"Status: {status.upper()}"]
        if enabled:
            parts.append("Auto-start: ON")
        self.svc_status_label.setText(" | ".join(parts))
        # self.chk_autostart.setChecked(enabled)  # DEPRECATED: will be removed in 1.3.0

    def refresh_startup_status(self):
        pass  # DEPRECATED: will be removed in 1.3.0

    def _on_start(self):
        name = self.get_selected_strategy()
        if name:
            self.start_requested.emit(name)

    def _on_stop(self):
        self.stop_requested.emit()

    def _on_ipset(self):
        btn = self.ipset_group.checkedButton()
        if btn:
            self.ipset_changed.emit(btn.property("ipset_value"))

    def _get_active_strategy(self):
        name = self.get_selected_strategy()
        if name and name in self._strategies:
            return name, self._strategies[name]
        return None, None

    def _create_service(self):
        if not self.platform or not self.platform.is_linux:
            return
        name, strategy = self._get_active_strategy()
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
        self.refresh_service_status()

    def _remove_service(self):
        if not self.platform:
            return
        reply = QMessageBox.question(
            self,
            "Confirm",
            "Remove service?",
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
        self.refresh_service_status()

    def _uninstall_zapret(self):
        if not self.platform:
            return
        reply = QMessageBox.question(
            self,
            "Confirm",
            "Remove zapret completely?\n\n"
            "This will:\n"
            "  • Stop nfqws and clean iptables\n"
            "  • Remove systemd service\n"
            "  • Delete /opt/zapret\n\n"
            "Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self.platform.kill_all()
        self.platform.remove_systemd_service()
        import shutil

        zapret_dir = self.platform.zapret_dir
        if zapret_dir.exists():
            shutil.rmtree(zapret_dir)
            msg = "Zapret removed"
            self.diag_text.append(msg)
            self.log_signal.emit(msg)
        else:
            self.diag_text.append("Zapret not found")
        self.refresh_service_status()

    def _toggle_autostart(self):
        pass  # DEPRECATED: will be removed in 1.3.0

    def _toggle_startup(self):
        pass  # DEPRECATED: will be removed in 1.3.0

    def _update_ipset(self):
        if not self.list_manager:
            return

        def callback(msg):
            self.diag_text.append(msg)
            self.log_signal.emit(msg)

        import threading

        t = threading.Thread(
            target=self.list_manager.update_ipset, args=(callback,), daemon=True
        )
        t.start()
        self.log_signal.emit("IPSet update started...")

    def _update_hosts(self):
        if not self.list_manager:
            return

        def callback(msg):
            self.diag_text.append(msg)
            self.log_signal.emit(msg)

        import threading

        t = threading.Thread(
            target=self.list_manager.update_hosts, args=(callback,), daemon=True
        )
        t.start()

    def _check_updates(self):
        self.diag_text.append("Checking for updates...")
        self.log_signal.emit("Checking for updates...")

        from core.update import check_mangopret_update

        result = check_mangopret_update()
        if result:
            current, latest, _ = result
            self.diag_text.append(f"Mangopret: {current} → latest: {latest}")
            self.log_signal.emit(f"Mangopret: {current} → latest: {latest}")
            if latest != current:
                self.diag_text.append("UPDATE AVAILABLE")
                self.log_signal.emit(
                    "UPDATE AVAILABLE — Download at https://github.com/Flowseal/mangopret/releases"
                )
        else:
            self.diag_text.append("Mangopret: update check failed")

        try:
            import urllib.request

            url = "https://raw.githubusercontent.com/Flowseal/zapret-discord-youtube/main/.service/version.txt"
            req = urllib.request.Request(url, headers={"User-Agent": "Mangopret"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                remote_version = resp.read().decode().strip()
            self.diag_text.append(f"Zapret: {remote_version}")
            self.log_signal.emit(f"Zapret: {remote_version}")
        except Exception as e:
            self.diag_text.append(f"Zapret: check failed — {e}")

    def _run_diagnostics(self):
        if not self.list_manager or not self.platform:
            return
        result = self.list_manager.run_diagnostics(self.platform.is_windows)
        self.diag_text.setPlainText(result)
        self.log_signal.emit("Diagnostics completed")
