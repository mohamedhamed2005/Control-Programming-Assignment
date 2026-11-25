"""Part 2 tab: enter a characteristic equation and see the Routh analysis."""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor, QFont, QFontDatabase
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from control_assignment.analysis.routh import (
    RouthResult,
    RouthSpecialCaseError,
    build_routh_table,
    verify_with_poles,
)
from control_assignment.examples import ROUTH_EXAMPLES
from control_assignment.gui.pole_plot import PolePlot
from control_assignment.parsing.polynomial import (
    PolynomialError,
    parse_characteristic_equation,
)
from control_assignment.reporting.formatting import fmt
from control_assignment.reporting.routh_report import build_routh_report

FIRST_COLUMN_FILL = QColor("#fff3bf")
SIGN_CHANGE_FILL = QColor("#ffc9c9")


class RouthTab(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.example_combo = QComboBox()
        for name, _ in ROUTH_EXAMPLES:
            self.example_combo.addItem(name)
        load_button = QPushButton("Load example")
        load_button.clicked.connect(self._load_example)

        self.equation_edit = QLineEdit(ROUTH_EXAMPLES[0][1])
        self.equation_edit.setPlaceholderText("s^5 + s^4 + 10s^3 + 72s^2 + 152s + 240 = 0")
        self.equation_edit.returnPressed.connect(self.analyze)
        analyze_button = QPushButton("Analyze  ▶")
        analyze_button.setStyleSheet("font-weight: bold; padding: 8px;")
        analyze_button.clicked.connect(self.analyze)

        input_box = QGroupBox("Characteristic equation (or coefficients, highest power first)")
        top = QHBoxLayout()
        top.addWidget(self.equation_edit, 1)
        top.addWidget(analyze_button)
        examples = QHBoxLayout()
        examples.addWidget(QLabel("Examples:"))
        examples.addWidget(self.example_combo, 1)
        examples.addWidget(load_button)
        box_layout = QVBoxLayout(input_box)
        box_layout.addLayout(top)
        box_layout.addLayout(examples)

        self.verdict = QLabel("")
        self.verdict.setAlignment(Qt.AlignmentFlag.AlignCenter)
        verdict_font = QFont(self.font())
        verdict_font.setPointSize(verdict_font.pointSize() + 3)
        verdict_font.setBold(True)
        self.verdict.setFont(verdict_font)

        self.table = QTableWidget()
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table_box = QGroupBox("Routh table (yellow = first column, red = sign change)")
        table_layout = QVBoxLayout(table_box)
        table_layout.addWidget(self.table)

        self.pole_plot = PolePlot()
        plot_box = QGroupBox("Poles in the s-plane")
        plot_layout = QVBoxLayout(plot_box)
        plot_layout.addWidget(self.pole_plot)

        upper = QSplitter(Qt.Orientation.Horizontal)
        upper.addWidget(table_box)
        upper.addWidget(plot_box)
        upper.setStretchFactor(0, 3)
        upper.setStretchFactor(1, 2)

        self.report = QPlainTextEdit()
        self.report.setReadOnly(True)
        self.report.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.report.setFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont))
        save_button = QPushButton("Save report…")
        save_button.clicked.connect(self._save_report)
        report_box = QGroupBox("Step-by-step solution")
        report_layout = QVBoxLayout(report_box)
        save_row = QHBoxLayout()
        save_row.addStretch(1)
        save_row.addWidget(save_button)
        report_layout.addLayout(save_row)
        report_layout.addWidget(self.report)

        lower = QSplitter(Qt.Orientation.Vertical)
        lower.addWidget(upper)
        lower.addWidget(report_box)
        lower.setStretchFactor(0, 2)
        lower.setStretchFactor(1, 3)

        layout = QVBoxLayout(self)
        layout.addWidget(input_box)
        layout.addWidget(self.verdict)
        layout.addWidget(lower, 1)

        self.analyze()

    def _load_example(self) -> None:
        self.equation_edit.setText(ROUTH_EXAMPLES[self.example_combo.currentIndex()][1])
        self.analyze()

    def analyze(self) -> None:
        try:
            coefficients = parse_characteristic_equation(self.equation_edit.text())
            result = build_routh_table(coefficients)
        except (PolynomialError, RouthSpecialCaseError) as error:
            QMessageBox.warning(self, "Cannot analyze the equation", str(error))
            return

        verification = verify_with_poles(result)
        self._fill_table(result)
        self.pole_plot.set_poles(verification.poles, verification.tolerance)
        self.report.setPlainText(build_routh_report(result, verification))

        if result.is_stable:
            text, color = "STABLE - all poles are in the left half-plane", "#2b8a3e"
        else:
            text = f"UNSTABLE - {result.sign_changes} pole(s) in the right half-plane"
            color = "#c92a2a"
        agreement = "numerical poles agree" if verification.agrees else "numerical poles DISAGREE"
        self.verdict.setText(f"{text}   ({agreement})")
        self.verdict.setStyleSheet(f"color: {color};")

    def _fill_table(self, result: RouthResult) -> None:
        columns = len(result.rows[0])
        self.table.clear()
        self.table.setRowCount(len(result.rows))
        self.table.setColumnCount(columns)
        self.table.setVerticalHeaderLabels([f"s^{p}" for p in result.row_powers])
        self.table.setHorizontalHeaderLabels([f"col {i + 1}" for i in range(columns)])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        changes = result.sign_change_positions
        flagged_rows = {i + 1 for i in changes}
        for row_index, row in enumerate(result.rows):
            for column, value in enumerate(row):
                item = QTableWidgetItem(fmt(value, 8))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if column == 0:
                    fill = SIGN_CHANGE_FILL if row_index in flagged_rows else FIRST_COLUMN_FILL
                    item.setBackground(QBrush(fill))
                    item.setForeground(QBrush(QColor("black")))
                    bold = item.font()
                    bold.setBold(True)
                    item.setFont(bold)
                self.table.setItem(row_index, column, item)

    def _save_report(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Save report", "routh_report.txt", "Text files (*.txt)")
        if path:
            Path(path).write_text(self.report.toPlainText(), encoding="utf-8")
