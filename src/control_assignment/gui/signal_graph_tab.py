"""Part 1 tab: enter a signal flow graph, draw it, and see Mason's formula worked out."""

from pathlib import Path

from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import (
    QAbstractItemView,
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
from PySide6.QtCore import Qt

from control_assignment.analysis.mason import calculate_mason_gain
from control_assignment.examples import GRAPH_EXAMPLES, GraphExample
from control_assignment.gui.graph_view import GraphView
from control_assignment.parsing.graph_input import (
    InputError,
    build_graph,
    parse_node_names,
)
from control_assignment.reporting.mason_report import build_mason_report


class SignalGraphTab(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.example_combo = QComboBox()
        for example in GRAPH_EXAMPLES:
            self.example_combo.addItem(example.name)
        load_button = QPushButton("Load example")
        load_button.clicked.connect(self._load_selected_example)

        self.nodes_edit = QLineEdit()
        self.nodes_edit.setPlaceholderText("e.g. R, x1, x2, C  (commas or spaces)")
        self.nodes_edit.textChanged.connect(self._refresh_endpoint_choices)
        self.input_combo = QComboBox()
        self.output_combo = QComboBox()

        self.branch_table = QTableWidget(0, 3)
        self.branch_table.setHorizontalHeaderLabels(["From", "To", "Gain"])
        self.branch_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.branch_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

        add_button = QPushButton("Add branch")
        add_button.clicked.connect(lambda: self.branch_table.insertRow(self.branch_table.rowCount()))
        remove_button = QPushButton("Remove selected")
        remove_button.clicked.connect(self._remove_selected_rows)
        clear_button = QPushButton("Clear all")
        clear_button.clicked.connect(self._clear_all)

        analyze_button = QPushButton("Analyze  ▶")
        analyze_button.setStyleSheet("font-weight: bold; padding: 8px;")
        analyze_button.clicked.connect(self.analyze)

        save_report = QPushButton("Save report…")
        save_report.clicked.connect(self._save_report)
        save_image = QPushButton("Save graph image…")
        save_image.clicked.connect(self._save_image)

        # -- left panel ------------------------------------------------------
        examples_row = QHBoxLayout()
        examples_row.addWidget(self.example_combo, 1)
        examples_row.addWidget(load_button)

        endpoints = QHBoxLayout()
        endpoints.addWidget(QLabel("Input node:"))
        endpoints.addWidget(self.input_combo, 1)
        endpoints.addWidget(QLabel("Output node:"))
        endpoints.addWidget(self.output_combo, 1)

        table_buttons = QHBoxLayout()
        for button in (add_button, remove_button, clear_button):
            table_buttons.addWidget(button)

        form = QGroupBox("Graph input")
        form_layout = QVBoxLayout(form)
        form_layout.addLayout(examples_row)
        form_layout.addWidget(QLabel("Nodes:"))
        form_layout.addWidget(self.nodes_edit)
        form_layout.addLayout(endpoints)
        form_layout.addWidget(QLabel("Branches (directed, numerical gain):"))
        form_layout.addWidget(self.branch_table, 1)
        form_layout.addLayout(table_buttons)
        form_layout.addWidget(analyze_button)

        # -- right panel -----------------------------------------------------
        self.graph_view = GraphView()
        graph_box = QGroupBox("Signal flow graph (green = input, orange = output)")
        graph_layout = QVBoxLayout(graph_box)
        graph_layout.addWidget(self.graph_view)

        self.report = QPlainTextEdit()
        self.report.setReadOnly(True)
        self.report.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.report.setFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont))
        report_box = QGroupBox("Step-by-step solution")
        report_layout = QVBoxLayout(report_box)
        save_row = QHBoxLayout()
        save_row.addStretch(1)
        save_row.addWidget(save_image)
        save_row.addWidget(save_report)
        report_layout.addLayout(save_row)
        report_layout.addWidget(self.report)

        right = QSplitter(Qt.Orientation.Vertical)
        right.addWidget(graph_box)
        right.addWidget(report_box)
        right.setStretchFactor(0, 2)
        right.setStretchFactor(1, 3)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(form)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)

        layout = QVBoxLayout(self)
        layout.addWidget(splitter)

        self._load_example(GRAPH_EXAMPLES[0])
        self.analyze()

    # -- input handling ------------------------------------------------------
    def _refresh_endpoint_choices(self) -> None:
        names = parse_node_names(self.nodes_edit.text())
        for combo, default_index in ((self.input_combo, 0), (self.output_combo, -1)):
            previous = combo.currentText()
            combo.blockSignals(True)
            combo.clear()
            combo.addItems(names)
            if previous in names:
                combo.setCurrentText(previous)
            elif names:
                combo.setCurrentIndex(default_index % len(names))
            combo.blockSignals(False)

    def _read_rows(self) -> list[tuple[str, str, str]]:
        def text(row: int, column: int) -> str:
            item = self.branch_table.item(row, column)
            return item.text() if item else ""

        return [(text(r, 0), text(r, 1), text(r, 2)) for r in range(self.branch_table.rowCount())]

    def _remove_selected_rows(self) -> None:
        rows = sorted({index.row() for index in self.branch_table.selectedIndexes()}, reverse=True)
        for row in rows:
            self.branch_table.removeRow(row)

    def _clear_all(self) -> None:
        self.nodes_edit.clear()
        self.branch_table.setRowCount(0)
        self.report.clear()
        self.graph_view.show_graph(None)

    def _load_selected_example(self) -> None:
        self._load_example(GRAPH_EXAMPLES[self.example_combo.currentIndex()])
        self.analyze()

    def _load_example(self, example: GraphExample) -> None:
        self.nodes_edit.setText(example.nodes)
        self.input_combo.setCurrentText(example.input_node)
        self.output_combo.setCurrentText(example.output_node)
        self.branch_table.setRowCount(len(example.branches))
        for row, values in enumerate(example.branches):
            for column, value in enumerate(values):
                self.branch_table.setItem(row, column, QTableWidgetItem(value))

    # -- analysis ------------------------------------------------------------
    def analyze(self) -> None:
        try:
            graph = build_graph(
                parse_node_names(self.nodes_edit.text()),
                self._read_rows(),
                self.input_combo.currentText(),
                self.output_combo.currentText(),
            )
            result = calculate_mason_gain(graph)
        except (InputError, ZeroDivisionError) as error:
            QMessageBox.warning(self, "Cannot analyze the graph", str(error))
            return

        self.graph_view.show_graph(graph)
        self.report.setPlainText(build_mason_report(graph, result))
        self.report.moveCursor(self.report.textCursor().MoveOperation.Start)

    # -- saving --------------------------------------------------------------
    def _save_report(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Save report", "mason_report.txt", "Text files (*.txt)")
        if path:
            Path(path).write_text(self.report.toPlainText(), encoding="utf-8")

    def _save_image(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Save graph image", "signal_flow_graph.png", "PNG images (*.png)")
        if path and not self.graph_view.save_image(path):
            QMessageBox.warning(self, "Save failed", "The image could not be written.")
