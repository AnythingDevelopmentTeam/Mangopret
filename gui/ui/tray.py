from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont
from PyQt6.QtCore import pyqtSignal, QObject


def create_tray_icon(color: str = "#7aa2f7") -> QIcon:
    pixmap = QPixmap(64, 64)
    pixmap.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    painter.setBrush(QColor(color))
    painter.setPen(QColor(color))
    painter.drawRoundedRect(8, 8, 48, 48, 8, 8)

    font = QFont("Arial", 28, QFont.Weight.Bold)
    painter.setFont(font)
    painter.setPen(QColor("#1a1b26"))
    painter.drawText(pixmap.rect(), 0x0084, "M")

    painter.end()
    return QIcon(pixmap)


def create_status_icon(active: bool) -> QIcon:
    color = "#9ece6a" if active else "#f7768e"
    pixmap = QPixmap(64, 64)
    pixmap.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    painter.setBrush(QColor(color))
    painter.setPen(QColor(color))
    painter.drawRoundedRect(8, 8, 48, 48, 8, 8)

    font = QFont("Arial", 28, QFont.Weight.Bold)
    painter.setFont(font)
    painter.setPen(QColor("#1a1b26"))
    painter.drawText(pixmap.rect(), 0x0084, "M")

    painter.end()
    return QIcon(pixmap)


class SystemTray(QObject):
    show_requested = pyqtSignal()
    start_requested = pyqtSignal(str)
    stop_requested = pyqtSignal()
    quit_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tray = QSystemTrayIcon(create_tray_icon(), parent)
        self.tray.setToolTip("Mangopret")
        self._menu = QMenu()
        self._strategies_menu = self._menu.addMenu("Strategies")
        self._menu.addSeparator()

        self._show_action = self._menu.addAction("Show")
        self._show_action.triggered.connect(self.show_requested.emit)

        self._start_action = self._menu.addAction("Start")
        self._start_action.triggered.connect(self._on_start)

        self._stop_action = self._menu.addAction("Stop")
        self._stop_action.triggered.connect(self.stop_requested.emit)
        self._stop_action.setEnabled(False)

        self._menu.addSeparator()

        self._quit_action = self._menu.addAction("Quit")
        self._quit_action.triggered.connect(self.quit_requested.emit)

        self.tray.setContextMenu(self._menu)
        self.tray.activated.connect(self._on_activated)

        self._current_strategy = ""
        self._strategy_callbacks = []

    def set_strategies(self, strategies: list, callback):
        self._strategies_menu.clear()
        self._strategy_callbacks = []
        for name, sid in strategies:
            action = self._strategies_menu.addAction(name)
            self._strategy_callbacks.append((sid, callback))
            action.triggered.connect(lambda checked, s=sid: self._on_strategy_selected(s))

    def _on_strategy_selected(self, strategy_id: str):
        self._current_strategy = strategy_id
        self.start_requested.emit(strategy_id)

    def _on_start(self):
        if self._current_strategy:
            self.start_requested.emit(self._current_strategy)

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_requested.emit()

    def set_active(self, active: bool, strategy_name: str = ""):
        self._start_action.setEnabled(not active)
        self._stop_action.setEnabled(active)
        if active:
            self.tray.setIcon(create_status_icon(True))
            self.tray.setToolTip(f"Mangopret - Active ({strategy_name})")
        else:
            self.tray.setIcon(create_status_icon(False))
            self.tray.setToolTip("Mangopret - Inactive")

    def show_message(self, title: str, message: str, duration: int = 3000):
        self.tray.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, duration)

    def show(self):
        self.tray.show()

    def hide(self):
        self.tray.hide()
