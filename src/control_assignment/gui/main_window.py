"""The application window: one tab per assignment part."""

from PySide6.QtWidgets import QMainWindow, QTabWidget

from control_assignment.gui.routh_tab import RouthTab
from control_assignment.gui.signal_graph_tab import SignalGraphTab


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Control Systems - Signal Flow Graphs & Routh Stability")
        self.resize(1400, 860)

        self.signal_graph_tab = SignalGraphTab()
        self.routh_tab = RouthTab()

        tabs = QTabWidget()
        tabs.addTab(self.signal_graph_tab, "Part 1 - Signal Flow Graph (Mason)")
        tabs.addTab(self.routh_tab, "Part 2 - Routh Stability")
        self.setCentralWidget(tabs)
