DARK_THEME = """
QMainWindow, QDialog {
    background-color: #1a1b26;
    color: #c0caf5;
}

QWidget {
    background-color: #1a1b26;
    color: #c0caf5;
    font-family: "Segoe UI", "Ubuntu", sans-serif;
    font-size: 13px;
}

QTabWidget::pane {
    border: 1px solid #33467c;
    border-radius: 6px;
    background-color: #1a1b26;
}

QTabBar::tab {
    background-color: #24283b;
    color: #565f89;
    padding: 8px 20px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    border: 1px solid #33467c;
    border-bottom: none;
    min-width: 80px;
}

QTabBar::tab:selected {
    background-color: #1a1b26;
    color: #7aa2f7;
    border-bottom: 2px solid #7aa2f7;
}

QTabBar::tab:hover:!selected {
    background-color: #292e42;
    color: #c0caf5;
}

QGroupBox {
    border: 1px solid #33467c;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 16px;
    font-weight: bold;
    color: #7aa2f7;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
}

QPushButton {
    background-color: #7aa2f7;
    color: #1a1b26;
    border: none;
    border-radius: 6px;
    padding: 8px 18px;
    font-weight: bold;
    min-height: 20px;
}

QPushButton:hover {
    background-color: #89b4fa;
}

QPushButton:pressed {
    background-color: #6a8fd8;
}

QPushButton:disabled {
    background-color: #33467c;
    color: #565f89;
}

QPushButton#stopBtn {
    background-color: #f7768e;
}

QPushButton#stopBtn:hover {
    background-color: #ff8fa3;
}

QPushButton#stopBtn:pressed {
    background-color: #d9667a;
}

QPushButton#secondaryBtn {
    background-color: #292e42;
    color: #c0caf5;
    border: 1px solid #33467c;
}

QPushButton#secondaryBtn:hover {
    background-color: #33467c;
}

QComboBox {
    background-color: #292e42;
    color: #c0caf5;
    border: 1px solid #33467c;
    border-radius: 6px;
    padding: 6px 12px;
    min-height: 20px;
}

QComboBox::drop-down {
    border: none;
    width: 30px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #565f89;
    margin-right: 8px;
}

QComboBox:hover {
    border-color: #7aa2f7;
}

QComboBox QAbstractItemView {
    background-color: #292e42;
    color: #c0caf5;
    border: 1px solid #33467c;
    selection-background-color: #7aa2f7;
    selection-color: #1a1b26;
}

QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #24283b;
    color: #c0caf5;
    border: 1px solid #33467c;
    border-radius: 6px;
    padding: 6px;
    selection-background-color: #7aa2f7;
    selection-color: #1a1b26;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border-color: #7aa2f7;
}

QLabel {
    color: #c0caf5;
}

QLabel#statusOk {
    color: #9ece6a;
    font-weight: bold;
}

QLabel#statusErr {
    color: #f7768e;
    font-weight: bold;
}

QLabel#statusWarn {
    color: #e0af68;
    font-weight: bold;
}

QLabel#headerLabel {
    color: #7aa2f7;
    font-size: 16px;
    font-weight: bold;
}

QLabel#subHeaderLabel {
    color: #565f89;
    font-size: 11px;
}

QRadioButton {
    spacing: 6px;
    color: #c0caf5;
}

QRadioButton::indicator {
    width: 14px;
    height: 14px;
    border-radius: 7px;
    border: 2px solid #33467c;
    background-color: #24283b;
}

QRadioButton::indicator:checked {
    border-color: #7aa2f7;
    background-color: #7aa2f7;
}

QRadioButton::indicator:hover {
    border-color: #7aa2f7;
}

QScrollBar:vertical {
    background-color: #1a1b26;
    width: 10px;
    border-radius: 5px;
}

QScrollBar::handle:vertical {
    background-color: #33467c;
    border-radius: 5px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #565f89;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background-color: #1a1b26;
    height: 10px;
    border-radius: 5px;
}

QScrollBar::handle:horizontal {
    background-color: #33467c;
    border-radius: 5px;
    min-width: 30px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #565f89;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

QListWidget {
    background-color: #24283b;
    color: #c0caf5;
    border: 1px solid #33467c;
    border-radius: 6px;
    padding: 4px;
}

QListWidget::item {
    padding: 4px 8px;
    border-radius: 4px;
}

QListWidget::item:selected {
    background-color: #7aa2f7;
    color: #1a1b26;
}

QListWidget::item:hover:!selected {
    background-color: #292e42;
}

QSplitter::handle {
    background-color: #33467c;
}

QSplitter::handle:horizontal {
    width: 3px;
}

QSplitter::handle:vertical {
    height: 3px;
}

QStatusBar {
    background-color: #24283b;
    color: #565f89;
    border-top: 1px solid #33467c;
}

QToolTip {
    background-color: #292e42;
    color: #c0caf5;
    border: 1px solid #33467c;
    border-radius: 4px;
    padding: 4px 8px;
}

QProgressBar {
    background-color: #24283b;
    border: 1px solid #33467c;
    border-radius: 6px;
    text-align: center;
    color: #c0caf5;
}

QProgressBar::chunk {
    background-color: #7aa2f7;
    border-radius: 5px;
}

QCheckBox {
    spacing: 6px;
    color: #c0caf5;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 2px solid #33467c;
    background-color: #24283b;
}

QCheckBox::indicator:checked {
    background-color: #7aa2f7;
    border-color: #7aa2f7;
}

QCheckBox::indicator:hover {
    border-color: #7aa2f7;
}
"""
