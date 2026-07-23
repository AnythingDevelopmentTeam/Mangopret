#!/usr/bin/env python3
"""Mangopret GUI entry point. Requires PyQt6."""
import sys
import os
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)

sys.path.insert(0, SCRIPT_DIR)

from PyQt6.QtWidgets import QApplication, QStyleFactory
from PyQt6.QtGui import QFont

from core.platform import PlatformInfo
from core.config import Config
from core.lists import ListManager
from ui.main_window import MainWindow
from ui.theme import DARK_THEME


# Actions that need root; surfaced as a set for quick lookup
_REQUIRES_ROOT = frozenset({
    "start", "stop", "install_service", "remove_service",
    "enable_autostart", "disable_autostart", "install_desktop",
    "remove_desktop", "install_zapret", "update_ipset", "update_hosts",
})


def _relaunch_elevated(args):
    """Re-launch this script via pkexec, persisting all original args."""
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
    except Exception as e:
        print(f"[mangopret] Failed to relaunch with pkexec: {e}")
        return False
    return True


def _run_pending(window):
    """Execute a root action that was queued before a pkexec relaunch."""
    data = window.config.get("_pending_root_action")
    if not data:
        return
    action = data.get("action")
    payload = data.get("payload", {})
    window.config.set("_pending_root_action", None)
    _dispatch(window, action, payload)


def _dispatch(window, action, payload):
    """Route a named action to the corresponding MainWindow method."""
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


def _apply_theme(app, platform):
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


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Mangopret")
    app.setOrganizationName("Mangopret")

    font = QFont("Segoe UI", 10)
    app.setFont(font)

    platform = PlatformInfo(BASE_DIR)
    platform.ensure_dirs()

    config = Config(str(platform.config_dir))

    theme = config.get("theme", "system")
    if theme == "dark":
        app.setStyleSheet(DARK_THEME)
    else:
        _apply_theme(app, platform)
    list_manager = ListManager(str(platform.lists_dir), str(platform.utils_dir))

    args = sys.argv[1:]
    start_minimized = "--minimized" in args or config.get("start_minimized", False)

    window = MainWindow(platform, config, list_manager, start_minimized=start_minimized)
    if start_minimized:
        window.hide()
    else:
        window.show()

    # If elevated by pkexec, run any queued action then normal GUI loop
    if platform.IS_ROOT:
        _run_pending(window)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
