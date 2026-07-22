from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QStatusBar, QVBoxLayout, QWidget,
    QSystemTrayIcon, QApplication, QMessageBox,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon

from .tabs.main_tab import MainTab
from .tabs.lists_tab import ListsTab
from .tabs.service_tab import ServiceTab
from .tabs.log_tab import LogTab
from .tray import SystemTray
from ..core.strategy import Strategy, StrategyParser


class MainWindow(QMainWindow):
    def __init__(self, platform_info, config, list_manager):
        super().__init__()
        self.platform = platform_info
        self.config = config
        self.list_manager = list_manager

        self.strategies = {}
        self.strategy_list = []
        self.active_process = None
        self.active_strategy_name = ""

        self.setWindowTitle("Mangopret")
        self.setMinimumSize(850, 600)
        self.resize(950, 700)

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

        self.main_tab = MainTab()
        self.main_tab.set_strategies(
            [(name, sid) for name, sid in self.strategy_list]
        )
        self.main_tab.start_requested.connect(self._start_strategy)
        self.main_tab.stop_requested.connect(self._stop_strategy)
        self.main_tab.game_filter_changed.connect(self._on_game_filter)
        self.main_tab.ipset_changed.connect(self._on_ipset)
        self.main_tab.refresh_requested.connect(self._refresh_status)
        self.main_tab.diagnostics_requested.connect(self._run_diagnostics)
        self.main_tab.test_requested.connect(self._run_tests)
        self.strategy_combo = self.main_tab.strategy_combo
        self.strategy_combo.currentIndexChanged.connect(self._on_strategy_changed)

        self.lists_tab = ListsTab(self.list_manager)
        self.lists_tab.log_signal.connect(self._log)

        self.service_tab = ServiceTab(self.platform, self.config, self.list_manager)
        self.service_tab.log_signal.connect(self._log)

        self.log_tab = LogTab()

        self.tabs.addTab(self.main_tab, "  Main  ")
        self.tabs.addTab(self.lists_tab, "  Lists  ")
        self.tabs.addTab(self.service_tab, "  Service  ")
        self.tabs.addTab(self.log_tab, "  Log  ")

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

        if self.strategy_list:
            self.main_tab.set_description(self.strategies[self.strategy_list[0][0]].description)

    def _setup_tray(self):
        self.tray = SystemTray(self)
        self.tray.set_strategies(
            [(name, sid) for name, sid in self.strategy_list],
            self._start_strategy,
        )
        self.tray.show_requested.connect(self._show_window)
        self.tray.start_requested.connect(self._start_strategy)
        self.tray.stop_requested.connect(self._stop_strategy)
        self.tray.quit_requested.connect(self._quit)

        self.tray.show()

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

        self._stop_strategy()

        strategy = self.strategies[name]
        args = strategy.build_command(
            binary_path=str(self.platform.binary),
            bin_dir=str(self.platform.bin_dir),
            lists_dir=str(self.platform.lists_dir),
            game_filter_tcp=self.config.game_filter_tcp,
            game_filter_udp=self.config.game_filter_udp,
            is_windows=self.platform.is_windows,
        )

        self._log(f"Starting: {name}")
        self._log(f"Command: {' '.join(args)}")

        self.active_process = self.platform.start_service(name, args)
        self.active_strategy_name = name
        self.main_tab.set_active(True, name)
        self.tray.set_active(True, name)
        self.status_bar.showMessage(f"Active: {name}")

        QTimer.singleShot(2000, self._refresh_status)
        self.tray.show_message("Mangopret", f"Strategy started: {name}")

    def _stop_strategy(self):
        self.platform.stop_process(self.active_process)
        self.active_process = None
        self.active_strategy_name = ""
        self.main_tab.set_active(False)
        self.tray.set_active(False)
        self.status_bar.showMessage("Stopped")
        self._log("Strategy stopped")
        QTimer.singleShot(1000, self._refresh_status)

    def _refresh_status(self):
        running = self.platform.is_process_running()
        service_status = self.platform.get_service_status()
        gf = self.config.get("game_filter", "disabled")
        ipset = self.config.get_ipset_mode(str(self.platform.lists_dir))

        if running:
            self.main_tab.set_status("process", "RUNNING", "running")
        else:
            self.main_tab.set_status("process", "STOPPED", "stopped")

        svc_display = service_status.upper()
        svc_style = "ok" if service_status == "running" else (
            "error" if service_status == "stopped" else "warn"
        )
        self.main_tab.set_status("service", svc_display, svc_style)
        self.main_tab.set_status("game_filter", gf.upper())
        self.main_tab.set_status("ipset", ipset.upper())

        self.main_tab.set_game_filter(gf)
        self.main_tab.set_ipset(ipset)

        if not running and self.active_strategy_name:
            self.active_strategy_name = ""
            self.main_tab.set_active(False)
            self.tray.set_active(False)

    def _on_game_filter(self, mode: str):
        self.config.set_game_filter(mode)
        self._log(f"Game filter: {mode}")
        self._refresh_status()

    def _on_ipset(self, mode: str):
        self.config.set_ipset_mode(mode, str(self.platform.lists_dir))
        self._log(f"IPSet mode: {mode}")
        self._refresh_status()

    def _run_diagnostics(self):
        result = self.list_manager.run_diagnostics(self.platform.is_windows)
        self._log(f"Diagnostics:\n{result}")
        self.tabs.setCurrentIndex(3)

    def _run_tests(self):
        if self.platform.is_windows:
            test_file = self.platform.utils_dir / "test zapret.ps1"
            if test_file.exists():
                import subprocess
                subprocess.Popen(
                    ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                     "-File", str(test_file)],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
                self._log("Tests started in PowerShell")
            else:
                self._log("Test script not found")
        else:
            self._log("Tests not available on Linux yet")

    def _log(self, message: str):
        self.log_tab.log(message)

    def _show_window(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _quit(self):
        self._stop_strategy()
        self.tray.hide()
        QApplication.instance().quit()

    def closeEvent(self, event):
        if self.config.get("minimize_to_tray", True) and self.tray.tray.isVisible():
            event.ignore()
            self.hide()
            self.tray.show_message(
                "Mangopret",
                "Minimized to tray. Double-click to restore.",
            )
        else:
            self._quit()
            event.accept()
