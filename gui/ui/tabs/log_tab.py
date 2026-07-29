import time
from pathlib import Path

from PyQt6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

_MAX_LOG_LINES = 2000


class LogTab(QWidget):
    def __init__(self, log_file: str = "", parent=None):
        super().__init__(parent)
        self._log_file = Path(log_file) if log_file else None
        self._build_ui()
        self._load_persisted()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFontFamily("Consolas")
        self.log_text.setFontPointSize(10)
        layout.addWidget(self.log_text, 1)

        btn_row = QHBoxLayout()
        btn_clear = QPushButton("Clear Log")
        btn_clear.setObjectName("secondaryBtn")
        btn_clear.setMinimumHeight(28)
        btn_clear.clicked.connect(self._clear_log)
        btn_row.addWidget(btn_clear)

        btn_copy = QPushButton("Copy Log")
        btn_copy.setObjectName("secondaryBtn")
        btn_copy.setMinimumHeight(28)
        btn_copy.clicked.connect(self._copy_log)
        btn_row.addWidget(btn_copy)

        btn_row.addStretch()
        layout.addLayout(btn_row)

    def _load_persisted(self):
        if not self._log_file or not self._log_file.exists():
            return
        try:
            lines = self._log_file.read_text(
                encoding="utf-8", errors="replace"
            ).splitlines()
            for line in lines[-_MAX_LOG_LINES:]:
                self.log_text.append(line)
            if lines:
                self.log_text.append("--- log resumed ---")
        except Exception:
            pass

    def log(self, message: str):
        timestamp = time.strftime("%H:%M:%S")
        line = f"[{timestamp}] {message}"
        self.log_text.append(line)
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        self._persist(line)

    def _persist(self, line: str):
        if not self._log_file:
            return
        try:
            self._log_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._log_file, "a", encoding="utf-8") as f:
                f.write(line + "\n")
            if self._log_file.stat().st_size > 1024 * 1024:
                self._rotate_log()
        except Exception:
            pass

    def _rotate_log(self):
        if not self._log_file:
            return
        try:
            lines = self._log_file.read_text(
                encoding="utf-8", errors="replace"
            ).splitlines()
            with open(self._log_file, "w", encoding="utf-8") as f:
                f.writelines(line + "\n" for line in lines[-_MAX_LOG_LINES:])
        except Exception:
            pass

    def _clear_log(self):
        self.log_text.clear()
        if self._log_file:
            try:
                self._log_file.write_text("")
            except Exception:
                pass

    def _copy_log(self):
        text = self.log_text.toPlainText()
        if text:
            from PyQt6.QtWidgets import QApplication

            QApplication.clipboard().setText(text)
