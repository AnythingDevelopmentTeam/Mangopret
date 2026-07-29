import subprocess

from core.strategy import StrategyParser
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMessageBox,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .tabs.lists_tab import ListsTab
from .tabs.log_tab import LogTab
from .tabs.main_tab import MainTab


class MainWindow(QMainWindow):
    def __init__(self, platform_info, config, list_manager, start_minimized=False):
        super().__init__()
        self.platform = platform_info
        self.config = config
        self.list_manager = list_manager
        self._start_minimized = start_minimized

        self.strategies = {}
        self.strategy_list = []
        self.active_strategy_name = ""

        self.setWindowTitle("Mangopret")
        self.setMinimumSize(640, 480)
        self.resize(900, 650)

        self._ensure_zapret()
        self._load_strategies()
        self._build_ui()
        self._setup_tray()
        self._setup_timer()
        self._refresh_status()

        last = self.config.get("last_strategy", "")
        if last:
            idx = self.strategy_combo.findText(last)
            if idx >= 0:
                self.strategy_combo.setCurrentIndex(idx)
                self._on_strategy_changed(idx)

    def _require_root(self, action, payload=None):
        return True  # DEPRECATED: will be removed in 1.3.0 (root elevation removed)

    def _elevate_linux(self, action, payload=None):
        pass  # DEPRECATED: will be removed in 1.3.0

    def _elevate_windows(self, action, payload=None):
        pass  # DEPRECATED: will be removed in 1.3.0

    def _ensure_zapret(self):
        if self.platform.is_windows:
            return
        if self.platform.is_zapret_installed():
            return
        reply = QMessageBox.question(
            None,
            "Zapret not found",
            "zapret is not installed.\nDownload and install it now?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            ok = self.platform.install_zapret(callback=lambda m: print(f"  {m}"))
            if not ok:
                QMessageBox.warning(
                    None, "Error", "Installation failed. Check the log."
                )

    def _load_strategies(self):
        strategies_dir = self.platform.strategies_dir
        if strategies_dir.exists():
            for f in sorted(strategies_dir.glob("*.strategy")):
                s = StrategyParser.from_file(str(f))
                if s and s.rules:
                    self.strategies[s.name] = s
                    self.strategy_list.append((s.name, s.id))

        bat_dir = self.platform.base_dir
        for f in sorted(bat_dir.glob("general*.bat")):
            s = StrategyParser.from_file(str(f))
            if s and s.rules:
                display_name = s.name
                if display_name not in self.strategies:
                    self.strategies[display_name] = s
                    self.strategy_list.append((display_name, s.id))

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.main_tab = MainTab(
            platform=self.platform,
            config=self.config,
            list_manager=self.list_manager,
        )
        self.main_tab.set_strategies([(name, sid) for name, sid in self.strategy_list])
        self.main_tab.set_strategies_dict(self.strategies)
        self.main_tab.start_requested.connect(self._start_strategy)
        self.main_tab.stop_requested.connect(self._stop_strategy)
        self.main_tab.ipset_changed.connect(self._on_ipset)
        self.main_tab.refresh_requested.connect(self._refresh_status)
        self.main_tab.test_requested.connect(self._run_tests)
        self.main_tab.log_signal.connect(self._log)
        self.strategy_combo = self.main_tab.strategy_combo
        self.strategy_combo.currentIndexChanged.connect(self._on_strategy_changed)

        self.lists_tab = ListsTab(self.list_manager)
        self.lists_tab.log_signal.connect(self._log)

        self.log_tab = LogTab()

        self.tabs.addTab(self.main_tab, "  Main  ")
        self.tabs.addTab(self.lists_tab, "  Lists  ")
        self.tabs.addTab(self.log_tab, "  Log  ")

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

        if self.strategy_list:
            self.main_tab.set_description(
                self.strategies[self.strategy_list[0][0]].description
            )
        else:
            self.main_tab.set_description("No strategies found")

    def _setup_tray(self):
        pass  # DEPRECATED: will be removed in 1.3.0 (system tray removed)

    def _setup_timer(self):
        self._status_timer = QTimer(self)
        self._status_timer.timeout.connect(self._refresh_status)
        self._status_timer.start(5000)

    def _on_strategy_changed(self, index):
        if index < 0:
            return
        name = self.strategy_combo.currentText()
        if name in self.strategies:
            s = self.strategies[name]
            self.main_tab.set_description(s.description)
            self.config["last_strategy"] = name

    def _start_strategy(self, name: str = ""):
        if not name:
            name = self.main_tab.get_selected_strategy()

        if not name or name not in self.strategies:
            return

        if not self._require_root("start", {"strategy": name}):
            return

        if self.platform.is_linux:
            svc_status = self.platform.get_service_status()
            if svc_status in ("running", "starting"):
                if self.active_strategy_name == name:
                    self._log(f"Service already running with strategy: {name}")
                    self.status_bar.showMessage(f"Already active: {name}")
                    return
                self._log(f"Switching from {self.active_strategy_name} to {name}...")
                ok, err = self.platform.service_stop()
                if not ok:
                    self._log(f"FAILED to stop old service: {err}")
                    self.status_bar.showMessage("Failed to stop old service")
                    return
                self._pending_start_name = name
                QTimer.singleShot(1500, self._do_deferred_start)
                return

        self._do_start(name)

    def _do_deferred_start(self):
        name = getattr(self, "_pending_start_name", "")
        self._pending_start_name = ""
        if name:
            self._do_start(name)

    def _do_start(self, name: str):
        strategy = self.strategies[name]

        self._log(f"Creating service: {name}")

        if self.platform.is_linux:
            ok = self.platform.create_systemd_service(strategy, name)
            if not ok:
                self._log("FAILED to create service")
                self.status_bar.showMessage("Failed to create service")
                return

            ok, err = self.platform.service_start()
            if ok:
                self.active_strategy_name = name
                self.main_tab.set_active(True, name)
                # self.tray.set_active(True, name)  # DEPRECATED: will be removed in 1.3.0
                self.status_bar.showMessage(f"Active: {name}")
                # self.tray.show_message("Mangopret", f"Service started: {name}")  # DEPRECATED: will be removed in 1.3.0
                self._log(f"Service started: {name}")
            else:
                self._log(f"FAILED to start service: {err}")
                self.status_bar.showMessage("Service start failed")
        else:
            ok, err = self.platform.service_install(strategy, name)
            if ok:
                ok2, err2 = self.platform.service_start()
                if ok2:
                    self.active_strategy_name = name
                    self.main_tab.set_active(True, name)
                    # self.tray.set_active(True, name)  # DEPRECATED: will be removed in 1.3.0
                    self.status_bar.showMessage(f"Active: {name}")
                    # self.tray.show_message("Mangopret", f"Service started: {name}")  # DEPRECATED: will be removed in 1.3.0
                    self._log(f"Service started: {name}")
                else:
                    self._log(f"FAILED to start service: {err2}")
                    self.status_bar.showMessage("Service start failed")
            else:
                self._log(f"FAILED to install service: {err}")
                self.status_bar.showMessage("Service install failed")

        QTimer.singleShot(1500, self._verify_started)

    def _verify_started(self):
        if not self.active_strategy_name:
            return
        running = self.platform.is_process_running()
        if not running:
            self._log("Process crashed after start — cleaning up")
            self.platform.service_stop()
            self.active_strategy_name = ""
            self.main_tab.set_active(False)
            # self.tray.set_active(False)  # DEPRECATED: will be removed in 1.3.0
            self.status_bar.showMessage("Process crashed on startup")
        QTimer.singleShot(500, self._refresh_status)

    def _stop_strategy(self):
        if not self._require_root("stop"):
            return
        self._log("Stopping service...")
        ok, err = self.platform.service_stop()
        if not ok:
            self._log(f"FAILED to stop service: {err}")
            self.status_bar.showMessage("Stop failed")
            QTimer.singleShot(1000, self._refresh_status)
            return
        self.active_strategy_name = ""
        self.main_tab.set_active(False)
        # self.tray.set_active(False)  # DEPRECATED: will be removed in 1.3.0
        self.status_bar.showMessage("Stopped")
        self._log("Service stopped")
        QTimer.singleShot(1000, self._refresh_status)

    def _install_service_from_payload(self, payload):
        name = payload.get("strategy") or self.main_tab.get_selected_strategy()
        if name and name in self.strategies:
            self._create_service_for(name)

    def _remove_service_confirm(self):
        self._remove_service_for(self.main_tab.get_selected_strategy())

    def _set_autostart_force(self, enabled):
        pass  # DEPRECATED: will be removed in 1.3.0 (autostart removed)

    def _install_zapret_root(self):
        pass  # DEPRECATED: will be removed in 1.3.0 (root elevation removed)

    def _update_ipset_root(self):
        pass  # DEPRECATED: will be removed in 1.3.0 (root elevation removed)

    def _update_hosts_root(self):
        pass  # DEPRECATED: will be removed in 1.3.0 (root elevation removed)

    def _refresh_status(self):
        service_status = self.platform.get_service_status()
        ipset = self.config.get_ipset_mode(str(self.platform.lists_dir))

        svc_display = service_status.upper()
        svc_style = (
            "ok"
            if service_status == "running"
            else ("error" if service_status in ("stopped", "not_installed") else "warn")
        )

        self.main_tab.set_status("service", svc_display, svc_style)
        self.main_tab.set_status("ipset", ipset.upper())

        self.main_tab.set_ipset(ipset)
        self.main_tab.refresh_service_status()
        self.main_tab.refresh_startup_status()

        if service_status == "running" and self.active_strategy_name:
            pass
        elif service_status == "running" and not self.active_strategy_name:
            self.main_tab.set_active(True)
            # self.tray.set_active(True)  # DEPRECATED: will be removed in 1.3.0
        elif service_status != "running" and self.active_strategy_name:
            self.active_strategy_name = ""
            self._pending_start_name = ""
            self.main_tab.set_active(False)
            # self.tray.set_active(False)  # DEPRECATED: will be removed in 1.3.0
            self.status_bar.showMessage("Service stopped")

    def _log(self, message: str):
        self.log_tab.log(message)

    def _on_ipset(self, mode: str):
        self.config.set_ipset_mode(mode, str(self.platform.lists_dir))
        self._log(f"IPSet mode: {mode}")
        self._refresh_status()

    def _run_tests(self):
        if self.platform.is_windows:
            test_file = self.platform.utils_dir / "test zapret.ps1"
            if test_file.exists():
                subprocess.Popen(
                    [
                        "powershell",
                        "-NoProfile",
                        "-ExecutionPolicy",
                        "Bypass",
                        "-File",
                        str(test_file),
                    ],
                    creationflags=0x08000000,
                )
                self._log("Tests started in PowerShell")
            else:
                self._log("Test script not found")
        else:
            self._log("Tests not available on Linux yet")

    def _show_window(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _quit(self):
        QApplication.instance().quit()

    def closeEvent(self, event):
        # DEPRECATED: will be removed in 1.3.0 (minimize_to_tray removed)
        self._quit()
        event.accept()
