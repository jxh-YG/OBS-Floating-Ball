"""Glossy Apple-style floating recording control.

Default: collapsed glass ball.
Click: expand frosted control pill to the right.
Ball color reflects connection / recording state.
"""

from __future__ import annotations

import math
import time
from collections.abc import Callable

from PySide6.QtCore import QEvent, QPoint, QPointF, QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import (
    QAction,
    QColor,
    QRegion,
    QFont,
    QLinearGradient,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPen,
    QRadialGradient,
)
from PySide6.QtWidgets import QApplication, QFrame, QHBoxLayout, QMenu, QToolButton, QWidget

from .i18n import CHINESE, tr
from .models import RecordStatus, RecordingState, format_elapsed
from . import theme


class TimerBubble(QWidget):
    """Glossy 3D glass sphere with state colors and timer text."""

    # State: idle_connected | recording | paused | disconnected
    def __init__(self) -> None:
        super().__init__()
        self.setFixedSize(theme.FLOAT_BUBBLE, theme.FLOAT_BUBBLE)
        self._text = tr("timer_disconnected")
        self._connected = False
        self._recording = False
        self._paused = False
        self._finished = False
        self._pulse = 0.0

    def set_display(
        self,
        text: str,
        connected: bool,
        *,
        recording: bool = False,
        paused: bool = False,
        finished: bool = False,
        pulse: float = 0.0,
    ) -> None:
        self._text = text
        self._connected = connected
        self._recording = recording
        self._paused = paused
        self._finished = finished
        self._pulse = pulse
        self.update()

    def _core_colors(self) -> tuple[QColor, QColor, QColor, QColor]:
        """Return (highlight, mid, deep, rim_tint)."""
        if self._recording:
            # Matching design reference: vivid recording red
            return (
                QColor("#FF4A4A"),
                QColor("#E02020"),
                QColor("#C01515"),
                QColor("#FF6464"),
            )
        if self._paused:
            return (
                QColor("#FFD60A"),
                QColor("#FF9F0A"),
                QColor("#C77700"),
                QColor("#FFE08A"),
            )
        if self._finished:
            return (
                QColor("#4ADE80"),
                QColor("#22C55E"),
                QColor("#15803D"),
                QColor("#86EFAC"),
            )
        if self._connected:
            return (
                QColor("#64D2FF"),
                QColor("#0A84FF"),
                QColor("#0055C4"),
                QColor("#9ED8FF"),
            )
        return (
            QColor("#D1D1D6"),
            QColor("#8E8E93"),
            QColor("#636366"),
            QColor("#C7C7CC"),
        )

    def paintEvent(self, _event: object) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        size = float(self.width())
        scale = size / 130.0
        # White frosted ring (matches design)
        outer = QRectF(0.5, 0.5, size - 1.0, size - 1.0)
        ring_grad = QRadialGradient(outer.center().x(), outer.center().y() - 2, outer.width() * 0.55)
        ring_grad.setColorAt(0.0, QColor(255, 255, 255, 255))
        ring_grad.setColorAt(0.7, QColor(248, 250, 255, 255))
        ring_grad.setColorAt(1.0, QColor(220, 228, 240, 255))
        painter.setPen(QPen(QColor(200, 210, 225, 200), max(0.5, scale)))
        painter.setBrush(ring_grad)
        painter.drawEllipse(outer)

        # Colored glass core
        hi, mid, deep, rim = self._core_colors()
        core_inset = 5.0 * scale
        core = outer.adjusted(core_inset, core_inset, -core_inset, -core_inset)
        cx = core.center().x()
        cy = core.center().y()
        body = QRadialGradient(cx - core.width() * 0.18, cy - core.height() * 0.22, core.width() * 0.78)
        body.setColorAt(0.0, hi)
        body.setColorAt(0.35, mid)
        body.setColorAt(0.78, deep)
        body.setColorAt(1.0, deep.darker(115))
        painter.setPen(QPen(rim, max(0.5, 0.8 * scale)))
        painter.setBrush(body)
        painter.drawEllipse(core)

        if self._recording and self._pulse > 0:
            ring_alpha = int(40 + 90 * self._pulse)
            painter.setPen(QPen(QColor(255, 80, 80, ring_alpha), max(1.0, 2.0 * scale)))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            grow = 2.0 * scale * self._pulse
            painter.drawEllipse(core.adjusted(-grow, -grow, grow, grow))

        # Soft edge vignette for depth
        edge = QRadialGradient(cx, cy, core.width() * 0.52)
        edge.setColorAt(0.55, QColor(0, 0, 0, 0))
        edge.setColorAt(1.0, QColor(0, 0, 0, 45))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(edge)
        painter.drawEllipse(core)

        # Specular highlight (bright glass blob, top-left)
        spec = QRectF(core.x() + core.width() * 0.16, core.y() + core.height() * 0.10,
                      core.width() * 0.28, core.height() * 0.20)
        spec_grad = QRadialGradient(spec.center(), spec.width() * 0.7)
        spec_grad.setColorAt(0.0, QColor(255, 255, 255, 230))
        spec_grad.setColorAt(0.45, QColor(255, 255, 255, 110))
        spec_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.setBrush(spec_grad)
        painter.drawEllipse(spec)

        # Secondary sheen arc
        sheen = QRectF(
            core.x() + 6 * scale,
            core.y() + 5 * scale,
            core.width() - 12 * scale,
            core.height() * 0.42,
        )
        sheen_grad = QLinearGradient(sheen.topLeft(), sheen.bottomLeft())
        sheen_grad.setColorAt(0.0, QColor(255, 255, 255, 70))
        sheen_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.setBrush(sheen_grad)
        painter.drawEllipse(sheen)

        # Timer label
        painter.setPen(QColor(255, 255, 255, 250))
        font = QFont(theme.FONT_FAMILY_PRIMARY)
        font.setPixelSize(max(9, round(28 * scale)))
        font.setWeight(QFont.Weight.DemiBold)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self._text)


class GlassControlStrip(QFrame):
    """Frosted white glass pill matching the design reference."""

    def paintEvent(self, _event: object) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        radius = rect.height() / 2.0
        scale = rect.height() / 90.0

        # Soft blue-gray glass body from the reference control bar.
        fill = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        fill.setColorAt(0.0, QColor("#F7F7FC"))
        fill.setColorAt(0.40, QColor("#E7EAF5"))
        fill.setColorAt(1.0, QColor("#D2DCF0"))
        painter.setPen(QPen(QColor(255, 255, 255, 170), max(0.5, 2.5 * scale)))
        painter.setBrush(fill)
        painter.drawRoundedRect(rect, radius, radius)

        # Top gloss band
        gloss = QRectF(
            rect.x() + 15 * scale,
            rect.y() + 4 * scale,
            rect.width() - 30 * scale,
            rect.height() * 0.35,
        )
        gloss_grad = QLinearGradient(gloss.topLeft(), gloss.bottomLeft())
        gloss_grad.setColorAt(0.0, QColor(255, 255, 255, 210))
        gloss_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(gloss_grad)
        painter.drawRoundedRect(gloss, radius - 1.5, radius - 1.5)

        # Right-end soft blue bloom (as in design)
        bloom = QRadialGradient(rect.right() - 28 * scale, rect.center().y(), 62 * scale)
        bloom.setColorAt(0.0, QColor(120, 180, 255, 40))
        bloom.setColorAt(1.0, QColor(120, 180, 255, 0))
        painter.setBrush(bloom)
        painter.drawRoundedRect(rect, radius, radius)


class StatusIndicator(QWidget):
    """Small recording-state dot in the glass control strip."""

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setFixedSize(theme.STATUS_DOT_SIZE, theme.STATUS_DOT_SIZE)
        self._color = QColor("#8E8E93")

    def set_state(self, *, connected: bool, recording: bool, paused: bool, finished: bool) -> None:
        if recording:
            color = QColor("#EF4444")
        elif paused:
            color = QColor("#F59E0B")
        elif finished:
            color = QColor("#22C55E")
        elif connected:
            color = QColor("#22C55E")
        else:
            color = QColor("#8E8E93")
        if self._color != color:
            self._color = color
            self.update()

    def paintEvent(self, _event: object) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self._color)
        painter.drawEllipse(self.rect())


class AppleActionButton(QToolButton):
    """SF-like media glyphs with clear state feedback."""

    def __init__(self, kind: str, parent: QWidget) -> None:
        super().__init__(parent)
        self._kind = kind
        self.setFixedSize(theme.BUTTON_HIT, theme.BUTTON_HIT)
        self.setIconSize(QSize(0, 0))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.setAutoRaise(True)
        self.setStyleSheet(
            "QToolButton { background: transparent; border: 0; border-radius: 10px; }"
            "QToolButton:hover { background: rgba(0, 0, 0, 0.06); }"
            "QToolButton:pressed { background: rgba(0, 0, 0, 0.10); }"
            "QToolButton:disabled { background: transparent; }"
        )

    def set_kind(self, kind: str) -> None:
        self._kind = kind
        self.update()

    def paintEvent(self, event: object) -> None:
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        scale = self.width() / 52.0

        if self._kind == "rename":
            color = QColor("#6B7280")
        elif not self.isEnabled():
            color = QColor("#A0A3AC")
        else:
            color = QColor("#6B7280")

        if self.isDown():
            painter.translate(self.width() / 2, self.height() / 2)
            painter.scale(0.9, 0.9)
            painter.translate(-self.width() / 2, -self.height() / 2)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        center = self.rect().center()

        if self._kind == "stop":
            stop_size = 32.0 * scale
            stop_rect = QRectF(
                center.x() - stop_size / 2,
                center.y() - stop_size / 2,
                stop_size,
                stop_size,
            )
            if self.isEnabled():
                painter.setBrush(QColor(220, 38, 38, 80))
                painter.drawRoundedRect(
                    stop_rect.translated(0, 2.0 * scale),
                    6.0 * scale,
                    6.0 * scale,
                )
                fill = QLinearGradient(stop_rect.topLeft(), stop_rect.bottomLeft())
                fill.setColorAt(0.0, QColor("#EF4444"))
                fill.setColorAt(1.0, QColor("#DC2626"))
                painter.setBrush(fill)
            else:
                painter.setBrush(QColor("#F5C7C4"))
            painter.drawRoundedRect(stop_rect, 6.0 * scale, 6.0 * scale)
        elif self._kind == "play":
            path = QPainterPath()
            path.moveTo(center.x() - 6.5 * scale, center.y() - 11.0 * scale)
            path.lineTo(center.x() - 6.5 * scale, center.y() + 11.0 * scale)
            path.lineTo(center.x() + 11.0 * scale, center.y())
            path.closeSubpath()
            painter.setBrush(QColor(0, 0, 0, 30))
            painter.drawPath(path.translated(0, 1.0 * scale))
            painter.setBrush(color)
            painter.drawPath(path)
        elif self._kind == "pause":
            painter.drawRoundedRect(
                QRectF(
                    center.x() - 8.0 * scale,
                    center.y() - 11.0 * scale,
                    5.0 * scale,
                    22.0 * scale,
                ),
                1.5 * scale,
                1.5 * scale,
            )
            painter.drawRoundedRect(
                QRectF(
                    center.x() + 3.0 * scale,
                    center.y() - 11.0 * scale,
                    5.0 * scale,
                    22.0 * scale,
                ),
                1.5 * scale,
                1.5 * scale,
            )
        else:
            # Exact filled edit glyph from the supplied HTML sample.
            path = QPainterPath()
            path.moveTo(3.0, 17.25)
            path.lineTo(3.0, 21.0)
            path.lineTo(6.75, 21.0)
            path.lineTo(17.81, 9.94)
            path.lineTo(14.06, 6.19)
            path.closeSubpath()
            path.moveTo(20.71, 7.04)
            path.cubicTo(21.10, 6.65, 21.10, 6.02, 20.71, 5.63)
            path.lineTo(18.37, 3.29)
            path.cubicTo(17.98, 2.90, 17.35, 2.90, 16.96, 3.29)
            path.lineTo(15.13, 5.12)
            path.lineTo(18.88, 8.87)
            path.closeSubpath()
            icon_size = 32.0 * scale
            painter.save()
            painter.translate(center.x() - icon_size / 2, center.y() - icon_size / 2)
            painter.scale(icon_size / 24.0, icon_size / 24.0)
            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPath(path)
            painter.restore()


class RoundedMenu(QMenu):
    """Context menu with clipped outer rounded corners (Apple-like panel)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("floatingContextMenu")
        self.setWindowFlags(
            self.windowFlags()
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setStyleSheet(theme.floating_menu_stylesheet())

    def _apply_round_mask(self) -> None:
        if self.width() <= 0 or self.height() <= 0:
            return
        radius = float(theme.RADIUS_MENU)
        path = QPainterPath()
        # Inset slightly so the 1px border stays inside the mask.
        path.addRoundedRect(QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5), radius, radius)
        self.setMask(QRegion(path.toFillPolygon().toPolygon()))

    def resizeEvent(self, event: object) -> None:
        super().resizeEvent(event)
        self._apply_round_mask()

    def showEvent(self, event: object) -> None:
        super().showEvent(event)
        self._apply_round_mask()

    def paintEvent(self, event: object) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        radius = float(theme.RADIUS_MENU)
        colors = theme.palette()
        painter.setPen(QPen(QColor(colors.separator), 1.0))
        painter.setBrush(QColor(colors.fill_primary))
        painter.drawRoundedRect(rect, radius, radius)
        painter.end()
        # Draw items without the default rectangular panel fill.
        opt = event  # keep signature; use QStyle painting via base with no panel
        # Manually invoke item rendering: QMenu.paintEvent draws panel+items.
        # Temporarily rely on stylesheet transparent panel + our fill above.
        super().paintEvent(event)


class FloatingControlBar(QWidget):
    start_requested = Signal()
    pause_requested = Signal()
    resume_requested = Signal()
    stop_requested = Signal()
    rename_requested = Signal()
    open_folder_requested = Signal()
    open_recent_requested = Signal(str)
    close_requested = Signal()
    hide_requested = Signal()
    position_changed = Signal()

    def __init__(self) -> None:
        super().__init__(None)
        self.setWindowFlags(
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self._language = CHINESE
        self._connection_message = tr("not_connected", self._language)
        self._allow_close = False
        self._connected = False
        self._drag_offset: QPoint | None = None
        self._drag_press_position: QPoint | None = None
        self._drag_started = False
        self._bubble_click_pending = False
        self._expanded = False
        self._last_recording_output_path: str | None = None
        self._recent_recordings: list[str] = []
        self._pulse_phase = 0.0
        self._context_menu: QMenu | None = None
        self._record_status = RecordStatus(RecordingState.DISCONNECTED, 0)
        self._status_provider: Callable[[], RecordStatus] | None = None
        self._build_ui()
        self._display_timer = QTimer(self)
        self._display_timer.setInterval(250)
        self._display_timer.timeout.connect(self._refresh_timer)

    def _build_ui(self) -> None:
        self.setFixedSize(theme.FLOAT_COLLAPSED_WIDTH, theme.FLOAT_HEIGHT)
        self._bubble = TimerBubble()
        self._bubble.setParent(self)
        bubble_y = (theme.FLOAT_HEIGHT - theme.FLOAT_BUBBLE) // 2
        self._bubble.setGeometry(0, bubble_y, theme.FLOAT_BUBBLE, theme.FLOAT_BUBBLE)
        self._bubble.setCursor(Qt.CursorShape.PointingHandCursor)

        self._strip = GlassControlStrip(self)
        self._strip.setObjectName("controlStrip")
        strip_y = (theme.FLOAT_HEIGHT - theme.FLOAT_STRIP_HEIGHT) // 2
        self._strip.setGeometry(
            theme.FLOAT_STRIP_LEFT,
            strip_y,
            theme.FLOAT_STRIP_WIDTH,
            theme.FLOAT_STRIP_HEIGHT,
        )
        self._strip.setVisible(False)

        controls = QHBoxLayout(self._strip)
        controls.setContentsMargins(23, 6, 9, 6)
        controls.setSpacing(7)
        self._primary = self._control_button("play", "start_recording", "primaryButton")
        self._primary.clicked.connect(self._trigger_primary_action)
        controls.addWidget(self._primary)
        controls.addWidget(self._control_divider())
        self._stop = self._control_button("stop", "stop_recording", "stopButton")
        self._stop.clicked.connect(self.stop_requested.emit)
        controls.addWidget(self._stop)
        controls.addWidget(self._control_divider())
        self._secondary = self._control_button("rename", "rename_recording", "secondaryButton")
        self._secondary.clicked.connect(self._trigger_secondary_action)
        controls.addWidget(self._secondary)

        self._status_indicator = StatusIndicator(self._strip)
        self._status_indicator.move(
            theme.FLOAT_STRIP_WIDTH - theme.STATUS_DOT_SIZE - theme.STATUS_DOT_MARGIN,
            theme.STATUS_DOT_MARGIN,
        )
        self._status_indicator.raise_()

        self._drag_sources = (self._bubble, self._strip)
        self._action_buttons = (self._primary, self._stop, self._secondary)
        for widget in (*self._drag_sources, *self._action_buttons):
            widget.installEventFilter(self)
        self._strip.setCursor(Qt.CursorShape.SizeAllCursor)
        self._bubble.raise_()
        self._set_actions_enabled()

    @property
    def is_collapsed(self) -> bool:
        return not self._expanded

    def set_collapsed(self, collapsed: bool) -> None:
        expanded = not collapsed
        if self._expanded == expanded:
            return
        self._expanded = expanded
        self._strip.setVisible(expanded)
        self.setFixedSize(
            theme.FLOAT_EXPANDED_WIDTH if expanded else theme.FLOAT_COLLAPSED_WIDTH,
            theme.FLOAT_HEIGHT,
        )
        self._bubble.setCursor(
            Qt.CursorShape.PointingHandCursor if not expanded else Qt.CursorShape.SizeAllCursor
        )

    def toggle_collapsed(self) -> None:
        self.set_collapsed(self._expanded)


    def _control_button(self, kind: str, text_key: str, object_name: str) -> AppleActionButton:
        button = AppleActionButton(kind, self._strip)
        button.setObjectName(object_name)
        button.setProperty("text_key", text_key)
        button.setToolTip(tr(text_key, self._language))
        return button

    def _control_divider(self) -> QFrame:
        divider = QFrame(self._strip)
        divider.setFixedSize(theme.CONTROL_DIVIDER_WIDTH, theme.CONTROL_DIVIDER_HEIGHT)
        divider.setStyleSheet("background: rgba(0, 0, 0, 0.10); border: 0;")
        return divider

    def _set_button_state(self, button: QToolButton, name: str, value: bool) -> None:
        button.setProperty(name, value)
        style = button.style()
        style.unpolish(button)
        style.polish(button)
        button.update()

    def set_language(self, language: str) -> None:
        self._language = language
        for button in self._action_buttons:
            button.setToolTip(tr(button.property("text_key"), self._language))
        self._bubble.setToolTip(self._connection_message or tr("show_hide", self._language))
        self._refresh_timer()
        self._set_actions_enabled()

    def set_status_provider(self, provider: Callable[[], RecordStatus]) -> None:
        self._status_provider = provider

    def set_connection(self, connected: bool, message: str) -> None:
        self._connected = connected
        self._connection_message = message
        self._bubble.setToolTip(message)
        self._refresh_timer()
        self._set_actions_enabled()
        self._sync_display_timer()

    def set_record_status(self, status: RecordStatus) -> None:
        self._record_status = status
        self._refresh_timer()
        self._set_actions_enabled()
        self._sync_display_timer()

    def set_recent_recordings(self, paths: list[str] | tuple[str, ...]) -> None:
        self._recent_recordings = list(paths)

    def set_recording_output_path(self, output_path: str | None) -> None:
        self._last_recording_output_path = output_path
        self._refresh_timer()
        self._set_actions_enabled()

    def _refresh_timer(self) -> None:
        if self._status_provider is not None:
            self._record_status = self._status_provider()
        recording = self._record_status.state is RecordingState.RECORDING
        paused = self._record_status.state is RecordingState.PAUSED
        if not self._connected:
            if self._connection_message == tr("connecting", self._language):
                text = tr("timer_connecting", self._language)
            elif tr("auth_failed", self._language) in self._connection_message:
                text = tr("timer_auth_failed", self._language)
            elif tr("connection_refused", self._language) in self._connection_message:
                text = tr("timer_offline", self._language)
            else:
                text = tr("timer_disconnected", self._language)
            self._bubble.set_display(text, False)
        elif self._record_status.state is RecordingState.IDLE:
            self._bubble.set_display(
                "00:00",
                True,
                finished=self._last_recording_output_path is not None,
            )
        else:
            pulse = 0.0
            if recording:
                pulse = 0.5 + 0.5 * math.sin(time.monotonic() * 6.0)
            self._bubble.set_display(
                format_elapsed(self._record_status.elapsed_seconds),
                True,
                recording=recording,
                paused=paused,
                pulse=pulse,
            )

    def _sync_display_timer(self) -> None:
        should_run = self._connected and self._record_status.state is RecordingState.RECORDING
        if should_run:
            if not self._display_timer.isActive():
                self._display_timer.start()
        elif self._display_timer.isActive():
            self._display_timer.stop()

    def _set_actions_enabled(self) -> None:
        state = self._record_status.state
        active = self._record_status.is_active
        recording = state is RecordingState.RECORDING
        paused = state is RecordingState.PAUSED
        finished = self._last_recording_output_path is not None and state is RecordingState.IDLE

        self._primary.setEnabled(self._connected)
        self._stop.setEnabled(self._connected and active)

        if paused:
            self._primary.set_kind("play")
            self._primary.setToolTip(tr("resume_recording", self._language))
        elif recording:
            self._primary.set_kind("pause")
            self._primary.setToolTip(tr("pause_recording", self._language))
        else:
            self._primary.set_kind("play")
            self._primary.setToolTip(tr("start_recording", self._language))

        self._set_button_state(self._primary, "recording", recording)
        self._set_button_state(self._primary, "paused", paused)

        self._secondary.set_kind("rename")
        self._secondary.setToolTip(tr("rename_recording", self._language))
        self._secondary.setEnabled(
            self._connected and (not active) and self._last_recording_output_path is not None
        )
        self._status_indicator.set_state(
            connected=self._connected,
            recording=recording,
            paused=paused,
            finished=finished,
        )

    def _trigger_primary_action(self) -> None:
        if self._record_status.state is RecordingState.IDLE:
            self.set_recording_output_path(None)
            self.start_requested.emit()
        elif self._record_status.state is RecordingState.PAUSED:
            self.resume_requested.emit()
        else:
            self.pause_requested.emit()

    def _trigger_secondary_action(self) -> None:
        if self._record_status.is_active:
            return
        self.rename_requested.emit()

    def eventFilter(self, watched: object, event: QEvent) -> bool:
        if isinstance(event, QMouseEvent):
            if event.type() == QEvent.Type.MouseButtonPress:
                if watched in self._drag_sources and event.button() == Qt.MouseButton.RightButton:
                    self._show_context_menu(event.globalPosition().toPoint())
                    return True
                if watched in self._drag_sources and event.button() == Qt.MouseButton.LeftButton:
                    self._begin_drag(event, watched is self._bubble)
                    return True
            elif event.type() == QEvent.Type.MouseMove and self._drag_offset is not None:
                if event.buttons() & Qt.MouseButton.LeftButton:
                    position = event.globalPosition().toPoint()
                    if self._drag_press_position is not None and not self._drag_started:
                        self._drag_started = (
                            position - self._drag_press_position
                        ).manhattanLength() >= QApplication.startDragDistance()
                    if self._drag_started:
                        self.move(position - self._drag_offset)
                    return True
            elif event.type() == QEvent.Type.MouseButtonRelease and self._drag_offset is not None:
                if event.button() == Qt.MouseButton.LeftButton:
                    should_toggle = self._bubble_click_pending and not self._drag_started
                    self._end_drag()
                    if should_toggle:
                        self.toggle_collapsed()
                    return True
        return super().eventFilter(watched, event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.RightButton:
            self._show_context_menu(event.globalPosition().toPoint())
            event.accept()
            return
        if event.button() == Qt.MouseButton.LeftButton:
            self._begin_drag(event)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._drag_offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            position = event.globalPosition().toPoint()
            if self._drag_press_position is not None and not self._drag_started:
                self._drag_started = (
                    position - self._drag_press_position
                ).manhattanLength() >= QApplication.startDragDistance()
            if self._drag_started:
                self.move(position - self._drag_offset)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if self._drag_offset is not None and event.button() == Qt.MouseButton.LeftButton:
            self._end_drag()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def _begin_drag(self, event: QMouseEvent, bubble_click_pending: bool = False) -> None:
        position = event.globalPosition().toPoint()
        self._drag_offset = position - self.frameGeometry().topLeft()
        self._drag_press_position = position
        self._drag_started = False
        self._bubble_click_pending = bubble_click_pending

    def _end_drag(self) -> None:
        moved = self._drag_started
        self._drag_offset = None
        self._drag_press_position = None
        self._drag_started = False
        self._bubble_click_pending = False
        if moved:
            self.position_changed.emit()

    def _show_context_menu(self, position: QPoint) -> None:
        menu = RoundedMenu(self)
        open_folder_action = QAction(tr("open_recording_folder", self._language), menu)
        open_folder_action.setEnabled(self._last_recording_output_path is not None)
        open_folder_action.triggered.connect(self.open_folder_requested.emit)
        menu.addAction(open_folder_action)
        menu.addSeparator()
        hide_action = QAction(tr("hide_floating_ball", self._language), menu)
        hide_action.triggered.connect(self.hide_requested.emit)
        menu.addAction(hide_action)
        self._context_menu = menu
        # Open below the floating control so the menu does not cover the ball.
        menu.adjustSize()
        gap = 12
        below = self.mapToGlobal(QPoint(0, self.height() + gap))
        # Keep horizontal position near the click, but never above the control bottom.
        x = position.x()
        y = max(position.y() + gap, below.y())
        # Prefer aligning under the ball/control left edge when click is on-widget.
        bar_rect = self.frameGeometry()
        if bar_rect.contains(position):
            x = bar_rect.left()
            y = bar_rect.bottom() + gap
        menu.popup(QPoint(x, y))

    def closeEvent(self, event: object) -> None:
        if self._allow_close:
            event.accept()
            return
        self.hide()
        self.close_requested.emit()
        event.ignore()

    def allow_application_exit(self) -> None:
        self._allow_close = True
