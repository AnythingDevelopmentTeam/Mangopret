DARK_THEME = r"""
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

LIGHT_THEME = r"""
QMainWindow, QDialog {
    background-color: #ffffff;
    color: #1a1a2e;
}

QWidget {
    background-color: #ffffff;
    color: #1a1a2e;
    font-family: "Segoe UI", "Ubuntu", sans-serif;
    font-size: 13px;
}

QTabWidget::pane {
    border: 1px solid #d0d5e0;
    border-radius: 6px;
    background-color: #ffffff;
}

QTabBar::tab {
    background-color: #f0f2f5;
    color: #6b7280;
    padding: 8px 20px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    border: 1px solid #d0d5e0;
    border-bottom: none;
    min-width: 80px;
}

QTabBar::tab:selected {
    background-color: #ffffff;
    color: #2563eb;
    border-bottom: 2px solid #2563eb;
}

QTabBar::tab:hover:!selected {
    background-color: #e5e7eb;
    color: #1a1a2e;
}

QGroupBox {
    border: 1px solid #d0d5e0;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 16px;
    font-weight: bold;
    color: #2563eb;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
}

QPushButton {
    background-color: #2563eb;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 8px 18px;
    font-weight: bold;
    min-height: 20px;
}

QPushButton:hover {
    background-color: #3b82f6;
}

QPushButton:pressed {
    background-color: #1d4ed8;
}

QPushButton:disabled {
    background-color: #d0d5e0;
    color: #9ca3af;
}

QPushButton#stopBtn {
    background-color: #ef4444;
}

QPushButton#stopBtn:hover {
    background-color: #f87171;
}

QPushButton#stopBtn:pressed {
    background-color: #dc2626;
}

QPushButton#secondaryBtn {
    background-color: #f0f2f5;
    color: #1a1a2e;
    border: 1px solid #d0d5e0;
}

QPushButton#secondaryBtn:hover {
    background-color: #e5e7eb;
}

QComboBox {
    background-color: #f0f2f5;
    color: #1a1a2e;
    border: 1px solid #d0d5e0;
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
    border-top: 6px solid #6b7280;
    margin-right: 8px;
}

QComboBox:hover {
    border-color: #2563eb;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #1a1a2e;
    border: 1px solid #d0d5e0;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
}

QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #f0f2f5;
    color: #1a1a2e;
    border: 1px solid #d0d5e0;
    border-radius: 6px;
    padding: 6px;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border-color: #2563eb;
}

QLabel {
    color: #1a1a2e;
}

QLabel#statusOk {
    color: #16a34a;
    font-weight: bold;
}

QLabel#statusErr {
    color: #dc2626;
    font-weight: bold;
}

QLabel#statusWarn {
    color: #d97706;
    font-weight: bold;
}

QLabel#headerLabel {
    color: #2563eb;
    font-size: 16px;
    font-weight: bold;
}

QLabel#subHeaderLabel {
    color: #6b7280;
    font-size: 11px;
}

QRadioButton {
    spacing: 6px;
    color: #1a1a2e;
}

QRadioButton::indicator {
    width: 14px;
    height: 14px;
    border-radius: 7px;
    border: 2px solid #d0d5e0;
    background-color: #f0f2f5;
}

QRadioButton::indicator:checked {
    border-color: #2563eb;
    background-color: #2563eb;
}

QRadioButton::indicator:hover {
    border-color: #2563eb;
}

QScrollBar:vertical {
    background-color: #ffffff;
    width: 10px;
    border-radius: 5px;
}

QScrollBar::handle:vertical {
    background-color: #d0d5e0;
    border-radius: 5px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #9ca3af;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background-color: #ffffff;
    height: 10px;
    border-radius: 5px;
}

QScrollBar::handle:horizontal {
    background-color: #d0d5e0;
    border-radius: 5px;
    min-width: 30px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #9ca3af;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

QListWidget {
    background-color: #ffffff;
    color: #1a1a2e;
    border: 1px solid #d0d5e0;
    border-radius: 6px;
    padding: 4px;
}

QListWidget::item {
    padding: 4px 8px;
    border-radius: 4px;
}

QListWidget::item:selected {
    background-color: #2563eb;
    color: #ffffff;
}

QListWidget::item:hover:!selected {
    background-color: #f0f2f5;
}

QSplitter::handle {
    background-color: #d0d5e0;
}

QSplitter::handle:horizontal {
    width: 3px;
}

QSplitter::handle:vertical {
    height: 3px;
}

QStatusBar {
    background-color: #f0f2f5;
    color: #6b7280;
    border-top: 1px solid #d0d5e0;
}

QToolTip {
    background-color: #f0f2f5;
    color: #1a1a2e;
    border: 1px solid #d0d5e0;
    border-radius: 4px;
    padding: 4px 8px;
}

QProgressBar {
    background-color: #f0f2f5;
    border: 1px solid #d0d5e0;
    border-radius: 6px;
    text-align: center;
    color: #1a1a2e;
}

QProgressBar::chunk {
    background-color: #2563eb;
    border-radius: 5px;
}

QCheckBox {
    spacing: 6px;
    color: #1a1a2e;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 2px solid #d0d5e0;
    background-color: #f0f2f5;
}

QCheckBox::indicator:checked {
    background-color: #2563eb;
    border-color: #2563eb;
}

QCheckBox::indicator:hover {
    border-color: #2563eb;
}
"""

CONTRAST_THEME = r"""
QMainWindow, QDialog {
    background-color: #000000;
    color: #ffffff;
}

QWidget {
    background-color: #000000;
    color: #ffffff;
    font-family: "Segoe UI", "Ubuntu", sans-serif;
    font-size: 13px;
}

QTabWidget::pane {
    border: 2px solid #ffffff;
    border-radius: 6px;
    background-color: #000000;
}

QTabBar::tab {
    background-color: #1a1a1a;
    color: #aaaaaa;
    padding: 8px 20px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    border: 1px solid #ffffff;
    border-bottom: none;
    min-width: 80px;
}

QTabBar::tab:selected {
    background-color: #000000;
    color: #00ff00;
    border-bottom: 2px solid #00ff00;
}

QTabBar::tab:hover:!selected {
    background-color: #333333;
    color: #ffffff;
}

QGroupBox {
    border: 2px solid #ffffff;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 16px;
    font-weight: bold;
    color: #00ff00;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
}

QPushButton {
    background-color: #ffffff;
    color: #000000;
    border: 2px solid #ffffff;
    border-radius: 6px;
    padding: 8px 18px;
    font-weight: bold;
    min-height: 20px;
}

QPushButton:hover {
    background-color: #cccccc;
}

QPushButton:pressed {
    background-color: #999999;
}

QPushButton:disabled {
    background-color: #333333;
    color: #666666;
    border: 2px solid #333333;
}

QPushButton#stopBtn {
    background-color: #ff0000;
    color: #ffffff;
}

QPushButton#stopBtn:hover {
    background-color: #cc0000;
}

QPushButton#stopBtn:pressed {
    background-color: #990000;
}

QPushButton#secondaryBtn {
    background-color: #1a1a1a;
    color: #ffffff;
    border: 1px solid #ffffff;
}

QPushButton#secondaryBtn:hover {
    background-color: #333333;
}

QComboBox {
    background-color: #1a1a1a;
    color: #ffffff;
    border: 2px solid #ffffff;
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
    border-top: 6px solid #ffffff;
    margin-right: 8px;
}

QComboBox:hover {
    border-color: #00ff00;
}

QComboBox QAbstractItemView {
    background-color: #000000;
    color: #ffffff;
    border: 2px solid #ffffff;
    selection-background-color: #00ff00;
    selection-color: #000000;
}

QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #1a1a1a;
    color: #ffffff;
    border: 2px solid #ffffff;
    border-radius: 6px;
    padding: 6px;
    selection-background-color: #00ff00;
    selection-color: #000000;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border-color: #00ff00;
}

QLabel {
    color: #ffffff;
}

QLabel#statusOk {
    color: #00ff00;
    font-weight: bold;
}

QLabel#statusErr {
    color: #ff0000;
    font-weight: bold;
}

QLabel#statusWarn {
    color: #ffff00;
    font-weight: bold;
}

QLabel#headerLabel {
    color: #00ff00;
    font-size: 16px;
    font-weight: bold;
}

QLabel#subHeaderLabel {
    color: #aaaaaa;
    font-size: 11px;
}

QRadioButton {
    spacing: 6px;
    color: #ffffff;
}

QRadioButton::indicator {
    width: 14px;
    height: 14px;
    border-radius: 7px;
    border: 2px solid #ffffff;
    background-color: #1a1a1a;
}

QRadioButton::indicator:checked {
    border-color: #00ff00;
    background-color: #00ff00;
}

QRadioButton::indicator:hover {
    border-color: #00ff00;
}

QScrollBar:vertical {
    background-color: #000000;
    width: 12px;
    border-radius: 0px;
}

QScrollBar::handle:vertical {
    background-color: #ffffff;
    border-radius: 0px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #cccccc;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background-color: #000000;
    height: 12px;
    border-radius: 0px;
}

QScrollBar::handle:horizontal {
    background-color: #ffffff;
    border-radius: 0px;
    min-width: 30px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #cccccc;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

QListWidget {
    background-color: #000000;
    color: #ffffff;
    border: 2px solid #ffffff;
    border-radius: 6px;
    padding: 4px;
}

QListWidget::item {
    padding: 4px 8px;
    border-radius: 4px;
}

QListWidget::item:selected {
    background-color: #00ff00;
    color: #000000;
}

QListWidget::item:hover:!selected {
    background-color: #333333;
}

QSplitter::handle {
    background-color: #ffffff;
}

QSplitter::handle:horizontal {
    width: 3px;
}

QSplitter::handle:vertical {
    height: 3px;
}

QStatusBar {
    background-color: #1a1a1a;
    color: #aaaaaa;
    border-top: 2px solid #ffffff;
}

QToolTip {
    background-color: #1a1a1a;
    color: #ffffff;
    border: 2px solid #ffffff;
    border-radius: 4px;
    padding: 4px 8px;
}

QProgressBar {
    background-color: #1a1a1a;
    border: 2px solid #ffffff;
    border-radius: 6px;
    text-align: center;
    color: #ffffff;
}

QProgressBar::chunk {
    background-color: #00ff00;
    border-radius: 5px;
}

QCheckBox {
    spacing: 6px;
    color: #ffffff;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 2px solid #ffffff;
    background-color: #1a1a1a;
}

QCheckBox::indicator:checked {
    background-color: #00ff00;
    border-color: #00ff00;
}

QCheckBox::indicator:hover {
    border-color: #00ff00;
}
"""

THEMES: dict[str, str] = {
    "dark": DARK_THEME,
    "light": LIGHT_THEME,
    "contrast": CONTRAST_THEME,
}

THEME_LABELS: dict[str, str] = {
    "dark": "Dark (Tokyo Night)",
    "light": "Light",
    "contrast": "High Contrast",
}
