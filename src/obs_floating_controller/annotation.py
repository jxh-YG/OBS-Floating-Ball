"""Transparent on-screen drawing canvas and capture-excluded tool panel."""

from __future__ import annotations

from dataclasses import dataclass, field

from PySide6.QtCore import QPoint, QRect, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPainterPath, QPen, QPolygon
from PySide6.QtWidgets import (
    QButtonGroup,
    QColorDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QSlider,
    QToolButton,
    QWidget,
)

from .i18n import CHINESE, tr
from .platform_windows import CaptureExclusionResult, exclude_from_capture


@dataclass
class Stroke:
    color: QColor
    width: int
    eraser: bool
    points: list[QPoint] = field(default_factory=list)


class AnnotationCanvas(QWidget):
    """A transparent per-monitor drawing surface. It intentionally is capturable."""

    exited = Signal()

    def __init__(self) -> None:
        super().__init__(None)
        self.setWindowFlags(
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self._language = CHINESE
        self._color = QColor("#e53935")
        self._width = 4
        self._eraser = False
        self._strokes: list[Stroke] = []
        self._current_stroke: Stroke | None = None

    def set_language(self, language: str) -> None:
        self._language = language

    def enter(self, screen_geometry: QRect) -> None:
        self.setGeometry(screen_geometry)
        self.show()
        self.raise_()
        self.activateWindow()

    def exit(self) -> None:
        self.hide()
        self.exited.emit()

    def set_color(self, color: QColor) -> None:
        if color.isValid():
            self._color = color
            self._eraser = False

    def set_width(self, width: int) -> None:
        self._width = max(1, width)

    def set_eraser(self, enabled: bool) -> None:
        self._eraser = enabled

    def undo(self) -> None:
        if self._strokes:
            self._strokes.pop()
            self.update()

    def clear(self) -> None:
        self._strokes.clear()
        self.update()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._current_stroke = Stroke(self._color, self._width, self._eraser, [event.position().toPoint()])
            self._strokes.append(self._current_stroke)
            self.update()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._current_stroke and event.buttons() & Qt.MouseButton.LeftButton:
            point = event.position().toPoint()
            if not self._current_stroke.points or self._current_stroke.points[-1] != point:
                self._current_stroke.points.append(point)
                self.update()
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._current_stroke:
            self._current_stroke = None
            self.update()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def paintEvent(self, _event: object) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        for stroke in self._strokes:
            if stroke.eraser:
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
                pen = QPen(Qt.GlobalColor.transparent, stroke.width)
            else:
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
                pen = QPen(stroke.color, stroke.width)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            if len(stroke.points) == 1:
                painter.drawPoint(stroke.points[0])
            else:
                painter.drawPolyline(QPolygon(stroke.points))


class AnnotationActionButton(QToolButton):
    """Small, self-drawn toolbar glyphs with a consistent visual weight."""

    def __init__(self, kind: str, parent: QWidget, checkable: bool = False) -> None:
        super().__init__(parent)
        self._kind = kind
        self.setCheckable(checkable)
        self.setFixedSize(40, 40)
        self.setIconSize(QSize(0, 0))
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)

    def paintEvent(self, event: object) -> None:
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = QColor("#FFFFFF") if self.isChecked() else QColor("#505055")
        pen = QPen(color, 2.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        center = self.rect().center()

        if self._kind == "brush":
            painter.setPen(QPen(color, 4.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawLine(center.x() - 7, center.y() + 7, center.x() + 7, center.y() - 7)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color)
            tip = QPainterPath()
            tip.moveTo(center.x() - 11, center.y() + 11)
            tip.lineTo(center.x() - 7, center.y() + 2)
            tip.lineTo(center.x() - 2, center.y() + 7)
            tip.closeSubpath()
            painter.drawPath(tip)
        elif self._kind == "eraser":
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            path = QPainterPath()
            path.moveTo(center.x() - 7, center.y() + 7)
            path.lineTo(center.x() + 2, center.y() - 8)
            path.quadTo(center.x() + 4, center.y() - 11, center.x() + 7, center.y() - 8)
            path.lineTo(center.x() + 11, center.y() - 4)
            path.quadTo(center.x() + 13, center.y() - 2, center.x() + 11, center.y() + 1)
            path.lineTo(center.x() + 2, center.y() + 9)
            path.closeSubpath()
            painter.drawPath(path)
            painter.drawLine(center.x() - 8, center.y() + 9, center.x() + 6, center.y() + 9)
        elif self._kind == "color":
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(center.x() - 9, center.y() - 9, 18, 18)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color)
            painter.drawEllipse(center.x() + 2, center.y() + 1, 4, 4)
        elif self._kind == "undo":
            painter.setPen(pen)
            path = QPainterPath()
            path.moveTo(center.x() + 9, center.y() + 6)
            path.cubicTo(center.x() + 7, center.y() - 7, center.x() - 3, center.y() - 10, center.x() - 9, center.y() - 2)
            painter.drawPath(path)
            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)
            arrow = QPainterPath()
            arrow.moveTo(center.x() - 12, center.y() - 2)
            arrow.lineTo(center.x() - 4, center.y() - 7)
            arrow.lineTo(center.x() - 5, center.y() + 1)
            arrow.closeSubpath()
            painter.drawPath(arrow)
        elif self._kind == "clear":
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(center.x() - 7, center.y() - 5, 14, 14, 2, 2)
            painter.drawLine(center.x() - 9, center.y() - 8, center.x() + 9, center.y() - 8)
            painter.drawLine(center.x() - 3, center.y() - 11, center.x() + 3, center.y() - 11)
        else:
            painter.setPen(QPen(color, 2.4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawLine(center.x() - 7, center.y() - 7, center.x() + 7, center.y() + 7)
            painter.drawLine(center.x() + 7, center.y() - 7, center.x() - 7, center.y() + 7)


class AnnotationToolPanel(QFrame):
    """Compact drawing controls kept out of OBS capture with display affinity."""

    capture_exclusion_checked = Signal(object)
    exit_requested = Signal()

    def __init__(self, canvas: AnnotationCanvas) -> None:
        super().__init__(None)
        self._canvas = canvas
        self._language = CHINESE
        self._exclusion_checked = False
        self._tool_buttons: list[QToolButton] = []
        self.setWindowFlags(
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setObjectName("annotationPanel")
        self.setStyleSheet(
            "#annotationPanel { background: #FFFFFF; border: 1px solid #D1D1D6; border-radius: 16px; }"
            "QToolButton { border: 0; border-radius: 12px; background: transparent; }"
            "QToolButton:hover { background: #F2F2F7; }"
            "QToolButton:pressed { background: #E5E5EA; }"
            "QToolButton:checked { background: #0A84FF; }"
            "QToolButton#colorSwatch { border: 2px solid #FFFFFF; border-radius: 12px; }"
            "QToolButton#colorSwatch:checked { border: 3px solid #0A84FF; background: transparent; }"
            "QLabel#widthLabel { color: #6E6E73; font-size: 12px; font-weight: 500; }"
            "QSlider::groove:horizontal { height: 4px; background: #D1D1D6; border-radius: 2px; }"
            "QSlider::sub-page:horizontal { background: #0A84FF; border-radius: 2px; }"
            "QSlider::handle:horizontal { width: 16px; margin: -6px 0; background: #FFFFFF;"
            " border: 1px solid #C7C7CC; border-radius: 8px; }"
        )
        self.setFixedHeight(62)
        self._build_controls()

    def _button(self, kind: str, text_key: str, checkable: bool = False) -> AnnotationActionButton:
        button = AnnotationActionButton(kind, self, checkable)
        button.setToolTip(tr(text_key, self._language))
        button.setProperty("text_key", text_key)
        self._tool_buttons.append(button)
        return button

    def _build_controls(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(11, 11, 11, 11)
        layout.setSpacing(5)
        self._brush = self._button("brush", "brush", True)
        self._brush.setChecked(True)
        self._brush.clicked.connect(lambda: self._canvas.set_eraser(False))
        layout.addWidget(self._brush)
        self._eraser = self._button("eraser", "eraser", True)
        self._eraser.clicked.connect(self._canvas.set_eraser)
        layout.addWidget(self._eraser)
        mode_group = QButtonGroup(self)
        mode_group.setExclusive(True)
        mode_group.addButton(self._brush)
        mode_group.addButton(self._eraser)
        for color in ("#e53935", "#1e88e5", "#fbc02d", "#212121"):
            swatch = QToolButton(self)
            swatch.setToolTip(tr("select_color", self._language))
            swatch.setProperty("text_key", "select_color")
            swatch.setObjectName("colorSwatch")
            swatch.setCheckable(True)
            swatch.setFixedSize(24, 24)
            swatch.setStyleSheet(
                f"QToolButton {{ background: {color}; border: 2px solid #FFFFFF; border-radius: 12px; }}"
                "QToolButton:hover { border: 2px solid #8E8E93; }"
                "QToolButton:checked { border: 3px solid #0A84FF; }"
            )
            swatch.clicked.connect(lambda _checked=False, value=color: self._select_color(QColor(value)))
            self._tool_buttons.append(swatch)
            layout.addWidget(swatch)
            if color == "#e53935":
                swatch.setChecked(True)
        self._colors = QButtonGroup(self)
        self._colors.setExclusive(True)
        for swatch in self._tool_buttons[2:]:
            self._colors.addButton(swatch)
        custom_color = self._button("color", "custom_color")
        custom_color.clicked.connect(self._choose_color)
        layout.addWidget(custom_color)
        self._width_label = QLabel(self)
        self._width_label.setObjectName("widthLabel")
        layout.addWidget(self._width_label)
        width = QSlider(Qt.Orientation.Horizontal, self)
        width.setToolTip(tr("brush_width", self._language))
        width.setProperty("text_key", "brush_width")
        width.setRange(1, 24)
        width.setValue(4)
        width.setFixedWidth(80)
        width.valueChanged.connect(self._canvas.set_width)
        layout.addWidget(width)
        undo = self._button("undo", "undo")
        undo.clicked.connect(self._canvas.undo)
        layout.addWidget(undo)
        clear = self._button("clear", "clear")
        clear.clicked.connect(self._canvas.clear)
        layout.addWidget(clear)
        exit_button = self._button("exit", "exit_annotation")
        exit_button.clicked.connect(self.exit_requested.emit)
        layout.addWidget(exit_button)
        self.adjustSize()

    def set_language(self, language: str) -> None:
        self._language = language
        for button in self._tool_buttons:
            button.setToolTip(tr(button.property("text_key"), language))
        self._width_label.setText(tr("width", language))

    def _select_color(self, color: QColor) -> None:
        self._canvas.set_color(color)
        self._brush.setChecked(True)

    def _choose_color(self) -> None:
        color = QColorDialog.getColor(QColor("#e53935"), self, tr("choose_color_title", self._language))
        if color.isValid():
            self._select_color(color)

    def show_for_screen(self, geometry: QRect) -> None:
        self.move(geometry.x() + (geometry.width() - self.width()) // 2, geometry.y() + 28)
        self.show()
        self.raise_()
        if not self._exclusion_checked:
            self._exclusion_checked = True
            QTimer.singleShot(0, self._verify_capture_exclusion)

    def _verify_capture_exclusion(self) -> None:
        result: CaptureExclusionResult = exclude_from_capture(self)
        self.capture_exclusion_checked.emit(result)
