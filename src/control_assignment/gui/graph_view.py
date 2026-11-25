"""Draw a signal flow graph: nodes on a line, curved arrows, gains as labels."""

import math
from collections import Counter

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QPainter,
    QPainterPath,
    QPalette,
    QPen,
    QPolygonF,
)
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView

from control_assignment.models.signal_graph import SignalFlowGraph
from control_assignment.reporting.formatting import fmt

NODE_SPACING = 120.0
ARROW_SIZE = 10.0

INPUT_FILL = QColor("#b7e4c7")
OUTPUT_FILL = QColor("#ffd6a5")
NODE_FILL = QColor("#dbe4ff")


class GraphView(QGraphicsView):
    """A read-only canvas that renders one ``SignalFlowGraph``."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setMinimumHeight(260)
        self._graph: SignalFlowGraph | None = None

    # -- public API --------------------------------------------------------
    def show_graph(self, graph: SignalFlowGraph | None) -> None:
        self._graph = graph
        self._scene.clear()
        if graph is None:
            return

        palette = self.palette()
        line_color = palette.color(QPalette.ColorRole.Text)
        background = palette.color(QPalette.ColorRole.Base)
        pen = QPen(line_color, 1.6)

        font = QFont(self.font())
        font.setBold(True)
        radius = 20.0
        for node in graph.nodes:
            radius = max(radius, len(node.node_id) * 4.5 + 10)

        index = {node.node_id: i for i, node in enumerate(graph.nodes)}
        centers = [QPointF(i * (NODE_SPACING + radius), 0.0) for i in range(len(index))]

        # Branches first, so the nodes are drawn on top of the arrow ends.
        pair_count: Counter[tuple[int, int]] = Counter()
        for branch in graph.branches:
            src, dst = index[branch.source_node_id], index[branch.target_node_id]
            parallel = pair_count[(src, dst)]
            pair_count[(src, dst)] += 1
            self._draw_branch(
                centers, src, dst, parallel, radius, fmt(branch.gain), pen, background
            )

        for node in graph.nodes:
            center = centers[index[node.node_id]]
            if node.node_id == graph.input_node_id:
                fill = INPUT_FILL
            elif node.node_id == graph.output_node_id:
                fill = OUTPUT_FILL
            else:
                fill = NODE_FILL
            self._scene.addEllipse(
                QRectF(center.x() - radius, center.y() - radius, 2 * radius, 2 * radius),
                QPen(line_color, 2.0),
                QBrush(fill),
            )
            label = self._scene.addSimpleText(node.node_id, font)
            label.setBrush(QBrush(QColor("black")))
            box = label.boundingRect()
            label.setPos(center.x() - box.width() / 2, center.y() - box.height() / 2)

        self._fit()

    def save_image(self, path: str) -> bool:
        return self.grab().save(path)

    # -- drawing helpers ---------------------------------------------------
    def _draw_branch(
        self,
        centers: list[QPointF],
        src: int,
        dst: int,
        parallel: int,
        radius: float,
        gain_text: str,
        pen: QPen,
        background: QColor,
    ) -> None:
        if src == dst:
            path, tip, tail = self._self_loop(centers[src], radius, parallel)
            label_offset = QPointF(0.0, -6.0)
        else:
            path, tip, tail = self._curve(centers, src, dst, parallel, radius)
            label_offset = QPointF(0.0, -9.0 if dst > src else 9.0)

        self._scene.addPath(path, pen)
        self._add_arrow_head(tip, tail, pen)

        text = self._scene.addSimpleText(gain_text)
        text.setBrush(QBrush(pen.color()))
        box = text.boundingRect()
        anchor = path.pointAtPercent(0.5) + label_offset
        backdrop = self._scene.addRect(
            QRectF(anchor.x() - box.width() / 2 - 2, anchor.y() - box.height() / 2,
                   box.width() + 4, box.height()),
            QPen(Qt.PenStyle.NoPen),
            QBrush(background),
        )
        text.setPos(anchor.x() - box.width() / 2, anchor.y() - box.height() / 2)
        text.setZValue(2)
        backdrop.setZValue(1)

    @staticmethod
    def _unit(dx: float, dy: float) -> QPointF:
        length = math.hypot(dx, dy) or 1.0
        return QPointF(dx / length, dy / length)

    def _curve(self, centers, src, dst, parallel, radius):
        a, b = centers[src], centers[dst]
        distance = abs(dst - src)
        forward = dst > src
        height = 0.0
        if forward:
            if distance > 1:
                height = 40.0 + 25.0 * (distance - 1)
            height += 28.0 * parallel
        else:
            height = 38.0 + 25.0 * (distance - 1) + 28.0 * parallel
        direction = -1.0 if forward else 1.0
        control = QPointF((a.x() + b.x()) / 2, (a.y() + b.y()) / 2 + direction * 2 * height)

        ua = self._unit(control.x() - a.x(), control.y() - a.y())
        ub = self._unit(control.x() - b.x(), control.y() - b.y())
        start = QPointF(a.x() + ua.x() * radius, a.y() + ua.y() * radius)
        end = QPointF(b.x() + ub.x() * radius, b.y() + ub.y() * radius)

        path = QPainterPath(start)
        path.quadTo(control, end)
        return path, end, control

    def _self_loop(self, center: QPointF, radius: float, parallel: int):
        lift = 1.0 + 0.6 * parallel
        start = QPointF(center.x() - radius * 0.5, center.y() - radius * 0.86)
        end = QPointF(center.x() + radius * 0.5, center.y() - radius * 0.86)
        c1 = QPointF(center.x() - radius * 1.8, center.y() - radius * (2.8 * lift + 0.6))
        c2 = QPointF(center.x() + radius * 1.8, center.y() - radius * (2.8 * lift + 0.6))
        path = QPainterPath(start)
        path.cubicTo(c1, c2, end)
        return path, end, c2

    def _add_arrow_head(self, tip: QPointF, tail: QPointF, pen: QPen) -> None:
        angle = math.atan2(tip.y() - tail.y(), tip.x() - tail.x())
        points = [tip]
        for side in (-0.4, 0.4):
            points.append(
                QPointF(
                    tip.x() - ARROW_SIZE * math.cos(angle + side),
                    tip.y() - ARROW_SIZE * math.sin(angle + side),
                )
            )
        self._scene.addPolygon(QPolygonF(points), pen, QBrush(pen.color()))

    # -- sizing ------------------------------------------------------------
    def _fit(self) -> None:
        rect = self._scene.itemsBoundingRect().adjusted(-30, -30, 30, 30)
        self._scene.setSceneRect(rect)
        self.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)

    def resizeEvent(self, event) -> None:  # noqa: N802 (Qt naming)
        super().resizeEvent(event)
        if self._graph is not None:
            self.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
