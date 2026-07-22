import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)

sys.path.insert(0, SCRIPT_DIR)

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont

from core.platform import PlatformInfo
from core.config import Config
from core.lists import ListManager
from ui.main_window import MainWindow
from ui.theme import DARK_THEME


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Mangopret")
    app.setOrganizationName("Mangopret")

    font = QFont("Segoe UI", 10)
    app.setFont(font)

    app.setStyleSheet(DARK_THEME)

    platform = PlatformInfo(BASE_DIR)
    platform.ensure_dirs()

    config = Config(str(platform.config_dir))

    list_manager = ListManager(str(platform.lists_dir), str(platform.utils_dir))

    window = MainWindow(platform, config, list_manager)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
