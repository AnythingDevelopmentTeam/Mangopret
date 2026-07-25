#!/usr/bin/env python3
import sys
import os
import signal
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)

# qt platform plugin path for portable python builds
_qt_plugin_path = os.path.join(
    os.path.dirname(sys.executable), "Lib", "site-packages", "Qt6", "plugins"
)
if os.path.isdir(_qt_plugin_path):
    os.environ.setdefault("QT_QPA_PLATFORM_PLUGIN_PATH", _qt_plugin_path)

sys.path.insert(0, SCRIPT_DIR)

from PyQt6.QtWidgets import QApplication, QStyleFactory
from PyQt6.QtGui import QFont
from PyQt6.QtNetwork import QLocalServer, QLocalSocket

from core.platform import PlatformInfo
from core.config import Config
from core.lists import ListManager
from ui.main_window import MainWindow
from ui.theme import THEMES
from core.log import get_logger

logger = get_logger(__name__)

_SOCKET_NAME = "mangopret-gui"


def _try_activate_existing() -> bool:
    socket = QLocalSocket()
    socket.connectToServer(_SOCKET_NAME)
    if socket.waitForConnected(500):
        socket.write(b"activate")
        socket.waitForBytesWritten(1000)
        socket.disconnectFromServer()
        return True
    return False


def _start_server(parent_window) -> QLocalServer | None:
    server = QLocalServer()
    QLocalServer.removeServer(_SOCKET_NAME)
    if not server.listen(_SOCKET_NAME):
        return None

    def on_new_connection() -> None:
        sock = server.nextPendingConnection()
        if sock:
            sock.waitForReadyRead(1000)
            data = sock.readAll().data()
            if data == b"activate" and parent_window is not None:
                parent_window._show_window()
            sock.disconnectFromServer()

    server.newConnection.connect(on_new_connection)
    return server


_REQUIRES_ROOT = frozenset({
    "start", "stop", "install_service", "remove_service",
    "enable_autostart", "disable_autostart", "install_desktop",
    "remove_desktop", "install_zapret", "update_ipset", "update_hosts",
})


def _relaunch_elevated(args: list[str]) -> bool:
    script = sys.argv[0]
    pkexec_args = [script] + args
    try:
        subprocess.Popen(
            ["pkexec", "--disable-internal-agent"] + pkexec_args,
            env={
                **os.environ,
                "DISPLAY": os.environ.get("DISPLAY", ""),
                "XAUTHORITY": os.environ.get("XAUTHORITY", ""),
            },
        )
    except Exception as exc:
        logger.error("Failed to relaunch with pkexec: %s", exc)
        return False
    return True


def _run_pending(window) -> None:
    data = window.config.get("_pending_root_action")
    if not data:
        return
    action = data.get("action")
    payload = data.get("payload", {})
    window.config.set("_pending_root_action", None)
    _dispatch(window, action, payload)


def _dispatch(window, action: str, payload: dict) -> None:
    if action == "start":
        window._start_strategy(payload.get("strategy", ""))
    elif action == "stop":
        window._stop_strategy()
    elif action == "install_service":
        window._install_service_from_payload(payload)
    elif action == "remove_service":
        window._remove_service_confirm()
    elif action == "enable_autostart":
        window._set_autostart_force(True)
    elif action == "disable_autostart":
        window._set_autostart_force(False)
    elif action == "install_zapret":
        window._install_zapret_root()
    elif action == "update_ipset":
        window._update_ipset_root()
    elif action == "update_hosts":
        window._update_hosts_root()


def _handle_sigint(sig, frame) -> None:
    from PyQt6.QtCore import QTimer
    QTimer.singleShot(0, QApplication.quit)


def _apply_theme(app, platform: PlatformInfo) -> None:
    if platform.is_windows:
        available = QStyleFactory.keys()
        for name in ("windows11", "windowsvista"):
            if name in available:
                app.setStyle(name)
                break
        else:
            app.setStyle("fusion")
    else:
        app.setStyleSheet("")


def main() -> None:
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QApplication(sys.argv)
    signal.signal(signal.SIGINT, _handle_sigint)
    app.setApplicationName("Mangopret")
    app.setOrganizationName("Mangopret")

    font = QFont("Segoe UI", 10)
    app.setFont(font)

    platform = PlatformInfo(BASE_DIR)
    platform.ensure_dirs()

    config = Config(str(platform.config_dir))

    theme = config.get("theme", "system")
    if theme in THEMES:
        app.setStyleSheet(THEMES[theme])
    else:
        _apply_theme(app, platform)
    list_manager = ListManager(str(platform.lists_dir), str(platform.utils_dir))

    args = sys.argv[1:]
    start_minimized = "--minimized" in args or config.get("start_minimized", False)

    if not _try_activate_existing():
        window = MainWindow(platform, config, list_manager, start_minimized=start_minimized)
        _server = _start_server(window)
        if start_minimized:
            window.hide()
        else:
            window.show()

        if platform.IS_ROOT:
            _run_pending(window)

        sys.exit(app.exec())


if __name__ == "__main__":
    main()
