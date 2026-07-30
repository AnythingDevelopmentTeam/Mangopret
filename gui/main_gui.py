#!/usr/bin/env python3
import os
import signal
import sys
from pathlib import Path

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)

# qt platform plugin path for portable python builds
_qt_plugin_path = os.path.join(
    os.path.dirname(sys.executable), "Lib", "site-packages", "Qt6", "plugins"
)
if os.path.isdir(_qt_plugin_path):
    os.environ.setdefault("QT_QPA_PLATFORM_PLUGIN_PATH", _qt_plugin_path)

sys.path.insert(0, SCRIPT_DIR)

from core.config import Config
from core.lists import ListManager
from core.log import get_logger
from core.platform import PlatformInfo
from PyQt6.QtGui import QFont
from PyQt6.QtNetwork import QLocalServer, QLocalSocket
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow
from ui.theme import THEMES

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


def _handle_sigint(sig, frame) -> None:
    from PyQt6.QtCore import QTimer

    QTimer.singleShot(0, QApplication.quit)


def main() -> None:
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QApplication(sys.argv)
    signal.signal(signal.SIGINT, _handle_sigint)
    app.setApplicationName("Mangopret")
    app.setOrganizationName("Mangopret")

    font = QFont("Segoe UI", 10)
    app.setFont(font)

    if sys.platform != "win32":
        app.setStyle("fusion")

    from core.log import set_log_dir

    if sys.platform == "win32":
        base = os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming"))
    else:
        base = os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
    config_dir = Path(base) / "mangopret"
    config = Config(str(config_dir))
    set_log_dir(str(config_dir))

    platform = PlatformInfo(BASE_DIR)
    platform.ensure_dirs()

    theme = config.get("theme", "dark")
    if theme in THEMES:
        app.setStyleSheet(THEMES[theme])
    else:
        app.setStyleSheet(THEMES["dark"])
    list_manager = ListManager(str(platform.lists_dir), str(platform.utils_dir))

    args = sys.argv[1:]
    start_minimized = "--minimized" in args or config.get("start_minimized", False)

    if not _try_activate_existing():
        window = MainWindow(
            platform, config, list_manager, start_minimized=start_minimized
        )
        _server = _start_server(window)
        if start_minimized:
            window.hide()
        else:
            window.show()

        sys.exit(app.exec())


if __name__ == "__main__":
    main()
