"""Create the Qt application and show the main window."""

import sys

from PySide6.QtWidgets import QApplication

from control_assignment.gui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()
