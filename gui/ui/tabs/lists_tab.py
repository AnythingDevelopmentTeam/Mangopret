from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class ListsTab(QWidget):
    log_signal = pyqtSignal(str)

    def __init__(self, list_manager, parent=None):
        super().__init__(parent)
        self.list_manager = list_manager
        self._current_file = None
        self._build_ui()
        self._load_file_list()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        header = QLabel("Domain & IP Lists")
        header.setObjectName("headerLabel")
        layout.addWidget(header)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(4)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        left_label = QLabel("Available lists")
        left_label.setObjectName("subHeaderLabel")
        left_layout.addWidget(left_label)

        self.file_list = QListWidget()
        self.file_list.currentItemChanged.connect(self._on_file_selected)
        left_layout.addWidget(self.file_list)

        btn_row = QHBoxLayout()
        btn_save = QPushButton("Save")
        btn_save.setMinimumHeight(28)
        btn_save.clicked.connect(self._save_content)
        btn_row.addWidget(btn_save)

        btn_add = QPushButton("Add Entry")
        btn_add.setObjectName("secondaryBtn")
        btn_add.setMinimumHeight(28)
        btn_add.clicked.connect(self._add_entry)
        btn_row.addWidget(btn_add)

        btn_remove = QPushButton("Remove Line")
        btn_remove.setObjectName("secondaryBtn")
        btn_remove.setMinimumHeight(28)
        btn_remove.clicked.connect(self._remove_line)
        btn_row.addWidget(btn_remove)

        left_layout.addLayout(btn_row)
        splitter.addWidget(left_widget)

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.file_label = QLabel("Select a list to edit")
        self.file_label.setObjectName("subHeaderLabel")
        right_layout.addWidget(self.file_label)

        self.editor = QTextEdit()
        self.editor.setPlaceholderText("Select a list file from the left panel...")
        self.editor.setFontFamily("Consolas")
        right_layout.addWidget(self.editor)

        splitter.addWidget(right_widget)
        splitter.setSizes([200, 400])

        layout.addWidget(splitter, 1)

        btn_validate = QPushButton("Validate Lists")
        btn_validate.setObjectName("secondaryBtn")
        btn_validate.setMinimumHeight(28)
        btn_validate.clicked.connect(self._validate_lists)
        layout.addWidget(btn_validate)

    def _load_file_list(self):
        self.file_list.clear()
        for name in self.list_manager.get_list_files():
            self.file_list.addItem(name)

    def _on_file_selected(self, current, previous):
        if current is None:
            return
        filename = current.text()
        self._current_file = filename
        self.file_label.setText(f"Editing: {filename}")
        content = self.list_manager.read_list(filename)
        self.editor.setPlainText(content)
        self.log_signal.emit(f"Loaded: {filename}")

    def _save_content(self):
        if not self._current_file:
            QMessageBox.warning(self, "Warning", "Select a list first")
            return
        content = self.editor.toPlainText()
        self.list_manager.write_list(self._current_file, content)
        self.log_signal.emit(f"Saved: {self._current_file}")

    def _add_entry(self):
        if not self._current_file:
            QMessageBox.warning(self, "Warning", "Select a list first")
            return
        text, ok = QInputDialog.getText(self, "Add Entry", "Enter domain or IP:")
        if ok and text.strip():
            cursor = self.editor.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            cursor.insertText("\n" + text.strip())
            self.editor.setTextCursor(cursor)
            self._save_content()

    def _remove_line(self):
        if not self._current_file:
            return
        cursor = self.editor.textCursor()
        cursor.select(cursor.SelectionType.BlockUnderCursor)
        cursor.removeSelectedText()
        cursor.deleteChar()
        self.editor.setTextCursor(cursor)

    def _validate_lists(self):
        if not self.list_manager:
            return
        has_errors = False
        for fname in self.list_manager.get_list_files():
            errors = self.list_manager.validate_list_file(fname)
            if errors:
                has_errors = True
                self.log_signal.emit(f"Validation: {fname}")
                for e in errors:
                    self.log_signal.emit(e)
        if not has_errors:
            self.log_signal.emit("All list files validated OK")
        else:
            self.log_signal.emit("Some list files have validation errors")

    def refresh(self):
        self._load_file_list()
