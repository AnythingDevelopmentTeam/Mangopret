from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QComboBox, QPushButton, QRadioButton,
    QButtonGroup, QFrame, QScrollArea, QGridLayout,
)
from PyQt6.QtCore import pyqtSignal, Qt


class MainTab(QWidget):
    start_requested = pyqtSignal(str)
    stop_requested = pyqtSignal()
    game_filter_changed = pyqtSignal(str)
    ipset_changed = pyqtSignal(str)
    refresh_requested = pyqtSignal()
    diagnostics_requested = pyqtSignal()
    test_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._active_strategy = ""
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        outer.addWidget(scroll)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(10)

        header = QLabel("Mangopret")
        header.setObjectName("headerLabel")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        subtitle = QLabel("Cross-platform DPI bypass manager")
        subtitle.setObjectName("subHeaderLabel")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        layout.addSpacing(4)

        strategy_group = QGroupBox("Strategy")
        sg_layout = QVBoxLayout(strategy_group)

        row = QHBoxLayout()
        row.addWidget(QLabel("Select:"))
        self.strategy_combo = QComboBox()
        self.strategy_combo.setMinimumWidth(200)
        row.addWidget(self.strategy_combo, 1)
        sg_layout.addLayout(row)

        self.description_label = QLabel("")
        self.description_label.setWordWrap(True)
        self.description_label.setObjectName("subHeaderLabel")
        sg_layout.addWidget(self.description_label)

        btn_row = QHBoxLayout()
        self.btn_start = QPushButton("Start")
        self.btn_start.setMinimumHeight(32)
        self.btn_start.clicked.connect(self._on_start)
        btn_row.addWidget(self.btn_start)

        self.btn_stop = QPushButton("Stop")
        self.btn_stop.setObjectName("stopBtn")
        self.btn_stop.setMinimumHeight(32)
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self._on_stop)
        btn_row.addWidget(self.btn_stop)
        sg_layout.addLayout(btn_row)

        layout.addWidget(strategy_group)

        status_group = QGroupBox("Status")
        st_layout = QVBoxLayout(status_group)
        st_layout.setSpacing(4)

        self.status_labels = {}
        for key, label_text in [
            ("process", "Bypass process:"),
            ("service", "Service:"),
            ("game_filter", "Game filter:"),
            ("ipset", "IPSet filter:"),
        ]:
            row = QHBoxLayout()
            lbl = QLabel(label_text)
            lbl.setFixedWidth(110)
            row.addWidget(lbl)
            val = QLabel("checking...")
            val.setObjectName("statusWarn")
            row.addWidget(val)
            row.addStretch()
            st_layout.addLayout(row)
            self.status_labels[key] = val

        layout.addWidget(status_group)

        ctrl_group = QGroupBox("Quick Controls")
        ct_layout = QVBoxLayout(ctrl_group)
        ct_layout.setSpacing(6)

        gf_row = QHBoxLayout()
        gf_row.addWidget(QLabel("Game filter:"))
        self.game_filter_group = QButtonGroup()
        for i, (val, text) in enumerate([
            ("disabled", "Off"),
            ("all", "TCP+UDP"),
            ("tcp", "TCP"),
            ("udp", "UDP"),
        ]):
            rb = QRadioButton(text)
            self.game_filter_group.addButton(rb, i)
            rb.setProperty("filter_value", val)
            rb.clicked.connect(self._on_game_filter)
            gf_row.addWidget(rb)
        gf_row.addStretch()
        ct_layout.addLayout(gf_row)

        ip_row = QHBoxLayout()
        ip_row.addWidget(QLabel("IPSet mode:"))
        self.ipset_group = QButtonGroup()
        for i, (val, text) in enumerate([
            ("none", "None"),
            ("loaded", "Loaded"),
            ("any", "Any"),
        ]):
            rb = QRadioButton(text)
            self.ipset_group.addButton(rb, i)
            rb.setProperty("ipset_value", val)
            rb.clicked.connect(self._on_ipset)
            ip_row.addWidget(rb)
        ip_row.addStretch()
        ct_layout.addLayout(ip_row)

        btn_grid = QGridLayout()
        btn_grid.setSpacing(6)

        btn_refresh = QPushButton("Refresh")
        btn_refresh.setObjectName("secondaryBtn")
        btn_refresh.setMinimumHeight(28)
        btn_refresh.clicked.connect(self.refresh_requested.emit)
        btn_grid.addWidget(btn_refresh, 0, 0)

        btn_diag = QPushButton("Diagnostics")
        btn_diag.setObjectName("secondaryBtn")
        btn_diag.setMinimumHeight(28)
        btn_diag.clicked.connect(self.diagnostics_requested.emit)
        btn_grid.addWidget(btn_diag, 0, 1)

        btn_test = QPushButton("Test Sites")
        btn_test.setObjectName("secondaryBtn")
        btn_test.setMinimumHeight(28)
        btn_test.clicked.connect(self.test_requested.emit)
        btn_grid.addWidget(btn_test, 0, 2)

        ct_layout.addLayout(btn_grid)

        layout.addWidget(ctrl_group)
        layout.addStretch()

        scroll.setWidget(container)

    def set_strategies(self, strategies: list, current: str = ""):
        self.strategy_combo.clear()
        for name, _ in strategies:
            self.strategy_combo.addItem(name)
        if current:
            idx = self.strategy_combo.findText(current)
            if idx >= 0:
                self.strategy_combo.setCurrentIndex(idx)

    def get_selected_strategy(self) -> str:
        return self.strategy_combo.currentText()

    def set_description(self, text: str):
        self.description_label.setText(text)

    def set_active(self, active: bool, strategy_name: str = ""):
        self._active_strategy = strategy_name if active else ""
        self.btn_start.setEnabled(not active)
        self.btn_stop.setEnabled(active)
        self.btn_start.setText("Start" if not active else "Switch")
        self.btn_start.setEnabled(True)

    def set_status(self, key: str, text: str, status: str = "ok"):
        if key in self.status_labels:
            self.status_labels[key].setText(text)
            obj_name = {
                "ok": "statusOk",
                "error": "statusErr",
                "warn": "statusWarn",
                "running": "statusOk",
                "stopped": "statusErr",
            }.get(status, "statusWarn")
            self.status_labels[key].setObjectName(obj_name)
            self.status_labels[key].setStyleSheet("")

    def set_game_filter(self, mode: str):
        for btn in self.game_filter_group.buttons():
            if btn.property("filter_value") == mode:
                btn.setChecked(True)
                break

    def set_ipset(self, mode: str):
        for btn in self.ipset_group.buttons():
            if btn.property("ipset_value") == mode:
                btn.setChecked(True)
                break

    def _on_start(self):
        name = self.get_selected_strategy()
        if name:
            self.start_requested.emit(name)

    def _on_stop(self):
        self.stop_requested.emit()

    def _on_game_filter(self):
        btn = self.game_filter_group.checkedButton()
        if btn:
            self.game_filter_changed.emit(btn.property("filter_value"))

    def _on_ipset(self):
        btn = self.ipset_group.checkedButton()
        if btn:
            self.ipset_changed.emit(btn.property("ipset_value"))
