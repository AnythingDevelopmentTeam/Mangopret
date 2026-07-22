import time
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout,
)


class LogTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFontFamily("Consolas")
        self.log_text.setFontPointSize(11)
        layout.addWidget(self.log_text, 1)

        btn_row = QHBoxLayout()
        btn_clear = QPushButton("Clear Log")
        btn_clear.setObjectName("secondaryBtn")
        btn_clear.clicked.connect(lambda: self.log_text.clear())
        btn_row.addWidget(btn_clear)

        btn_copy = QPushButton("Copy Log")
        btn_copy.setObjectName("secondaryBtn")
        btn_copy.clicked.connect(self._copy_log)
        btn_row.addWidget(btn_copy)

        btn_row.addStretch()
        layout.addLayout(btn_row)

    def log(self, message: str):
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _copy_log(self):
        text = self.log_text.toPlainText()
        if text:
            from PyQt6.QtWidgets import QApplication
            QApplication.clipboard().setText(text)
