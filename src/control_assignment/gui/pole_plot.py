"""A small s-plane plot that marks every pole and shades the right half-plane."""

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPalette, QPen
from PySide6.QtWidgets import QWidget


class PolePlot(QWidget):
    """Draws poles as crosses: green in the left half-plane, red in the right."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._poles: tuple[complex, ...] = ()
        self._tolerance = 1e-8
        self.setMinimumSize(260, 220)

    def set_poles(self, poles: tuple[complex, ...], tolerance: float = 1e-8) -> None:
        self._poles = poles
        self._tolerance = tolerance
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802 (Qt naming)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        palette = self.palette()
        text_color = palette.color(QPalette.ColorRole.Text)
        painter.fillRect(self.rect(), palette.color(QPalette.ColorRole.Base))

        area = QRectF(self.rect()).adjusted(28, 22, -18, -22)
        cx, cy = area.center().x(), area.center().y()
        extent = max(
            [1.0] + [max(abs(p.real), abs(p.imag)) for p in self._poles]
        ) * 1.25
        scale = min(area.width(), area.height()) / (2 * extent)

        def to_screen(point: complex) -> QPointF:
            return QPointF(cx + point.real * scale, cy - point.imag * scale)

        # Right half-plane shading.
        shade = QColor(220, 60, 60, 45)
        painter.fillRect(QRectF(cx, area.top(), area.right() - cx, area.height()), shade)

        painter.setPen(QPen(text_color, 1.2))
        painter.drawRect(area)
        painter.drawLine(QPointF(area.left(), cy), QPointF(area.right(), cy))
        painter.drawLine(QPointF(cx, area.top()), QPointF(cx, area.bottom()))
        painter.drawText(QPointF(area.right() - 22, cy - 5), "Re")
        painter.drawText(QPointF(cx + 5, area.top() + 12), "Im")
        painter.drawText(QPointF(area.left() + 2, area.bottom() + 15), f"±{extent:.3g}")
        painter.drawText(QPointF(cx + 4, area.bottom() - 4), "RHP shaded →")

        for pole in self._poles:
            point = to_screen(pole)
            color = QColor("#c92a2a") if pole.real > self._tolerance else QColor("#2b8a3e")
            painter.setPen(QPen(color, 2.4))
            painter.drawLine(point + QPointF(-5, -5), point + QPointF(5, 5))
            painter.drawLine(point + QPointF(-5, 5), point + QPointF(5, -5))
