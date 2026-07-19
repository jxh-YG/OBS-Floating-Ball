import os

import pytest
import ctypes
from ctypes import wintypes

from PySide6.QtCore import QEvent, QEventLoop, QPoint, QPointF, QRect, Qt, QTimer
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QApplication, QWidget

import obs_floating_controller.platform_windows as platform_windows
from obs_floating_controller.annotation import AnnotationCanvas, AnnotationToolPanel
from obs_floating_controller.floating_bar import FloatingControlBar
from obs_floating_controller import theme
from obs_floating_controller.i18n import tr
from obs_floating_controller.models import RecordStatus, RecordingState
from obs_floating_controller.platform_windows import WDA_EXCLUDEFROMCAPTURE, WDA_NONE, exclude_from_capture


@pytest.fixture(scope="module")
def qt_app() -> QApplication:
    return QApplication.instance() or QApplication([])


def process_events(delay_ms: int = 50) -> None:
    loop = QEventLoop()
    QTimer.singleShot(delay_ms, loop.quit)
    loop.exec()


def test_controls_follow_the_recording_state(qt_app: QApplication) -> None:
    bar = FloatingControlBar()
    bar.set_connection(True, "connected")
    bar.set_record_status(RecordStatus(RecordingState.IDLE, 0))
    assert bar._primary.isEnabled()
    assert not bar._stop.isEnabled()
    assert not bar._secondary.isEnabled()

    bar.set_record_status(RecordStatus(RecordingState.RECORDING, 10))
    assert bar._primary.isEnabled()
    assert bar._stop.isEnabled()
    assert not bar._secondary.isEnabled()

    bar.set_record_status(RecordStatus(RecordingState.PAUSED, 10))
    assert "继续" in bar._primary.toolTip()
    assert not bar._secondary.isEnabled()

    bar.set_record_status(RecordStatus(RecordingState.IDLE, 0))
    bar.set_recording_output_path("C:/recordings/demo.mkv")
    assert bar._secondary.isEnabled()
    assert bar._secondary.toolTip() == tr("rename_recording")


def test_timer_bubble_uses_distinct_colors_for_connection_and_recording_states(
    qt_app: QApplication,
) -> None:
    bar = FloatingControlBar()
    bar.set_connection(True, "connected")

    bar.set_record_status(RecordStatus(RecordingState.IDLE, 0))
    assert bar._bubble._core_colors()[1].name() == "#0a84ff"

    bar.set_record_status(RecordStatus(RecordingState.RECORDING, 10))
    assert bar._bubble._core_colors()[1].name() == "#e02020"

    bar.set_record_status(RecordStatus(RecordingState.PAUSED, 10))
    assert bar._bubble._core_colors()[1].name() == "#ff9f0a"

    bar.set_record_status(RecordStatus(RecordingState.IDLE, 0))
    bar.set_recording_output_path("C:/recordings/demo.mkv")
    assert bar._bubble._core_colors()[1].name() == "#22c55e"


def test_floating_bar_matches_the_reference_at_one_third_scale(qt_app: QApplication) -> None:
    bar = FloatingControlBar()
    assert (theme.FLOAT_BUBBLE, theme.FLOAT_STRIP_HEIGHT, theme.BUTTON_HIT) == (43, 30, 17)
    assert (bar.width(), bar.height()) == (43, 43)
    assert (bar._primary.width(), bar._primary.height()) == (17, 17)


def test_disconnected_status_surfaces_auth_and_offline_causes(qt_app: QApplication) -> None:
    bar = FloatingControlBar()
    bar.set_connection(False, tr("auth_failed"))
    assert bar._bubble._text == tr("timer_auth_failed")
    assert bar._bubble.toolTip() == tr("auth_failed")

    bar.set_connection(False, tr("connection_refused"))
    assert bar._bubble._text == tr("timer_offline")


def test_control_bar_can_be_dragged_and_right_clicked_to_show_hide_menu(qt_app: QApplication) -> None:
    bar = FloatingControlBar()
    bar.move(30, 40)
    press = QMouseEvent(
        QEvent.Type.MouseButtonPress,
        QPointF(5, 5),
        QPointF(35, 45),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    move = QMouseEvent(
        QEvent.Type.MouseMove,
        QPointF(70, 80),
        QPointF(100, 120),
        Qt.MouseButton.NoButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    release = QMouseEvent(
        QEvent.Type.MouseButtonRelease,
        QPointF(70, 80),
        QPointF(100, 120),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
    )
    bar.mousePressEvent(press)
    bar.mouseMoveEvent(move)
    bar.mouseReleaseEvent(release)
    assert bar.pos() == QPointF(95, 115).toPoint()

    hidden: list[bool] = []
    bar.hide_requested.connect(lambda: hidden.append(True))
    bar._show_context_menu(QPointF(100, 120).toPoint())
    assert hidden == []
    assert bar._context_menu is not None
    bar._context_menu.actions()[0].trigger()
    assert hidden == [True]


def test_timer_bubble_click_collapses_and_expands_the_action_strip(qt_app: QApplication) -> None:
    bar = FloatingControlBar()
    bar.show()
    process_events()
    # Default is ball-only; click expands the glass control strip.
    assert bar.is_collapsed
    assert bar.width() == theme.FLOAT_COLLAPSED_WIDTH
    assert not bar._strip.isVisible()

    click_position = QPointF(theme.FLOAT_BUBBLE / 2, theme.FLOAT_BUBBLE / 2)
    global_position = QPointF(bar.x() + theme.FLOAT_BUBBLE / 2, bar.y() + theme.FLOAT_BUBBLE / 2)
    press = QMouseEvent(
        QEvent.Type.MouseButtonPress,
        click_position,
        global_position,
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    release = QMouseEvent(
        QEvent.Type.MouseButtonRelease,
        click_position,
        global_position,
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
    )

    assert bar.eventFilter(bar._bubble, press)
    assert bar.eventFilter(bar._bubble, release)
    assert not bar.is_collapsed
    assert bar.width() == theme.FLOAT_EXPANDED_WIDTH
    assert bar._strip.isVisible()

    assert bar.eventFilter(bar._bubble, press)
    assert bar.eventFilter(bar._bubble, release)
    assert bar.is_collapsed
    assert bar.width() == theme.FLOAT_COLLAPSED_WIDTH
    assert not bar._strip.isVisible()
    bar.hide()


def test_dragging_timer_bubble_does_not_toggle_the_action_strip(qt_app: QApplication) -> None:
    bar = FloatingControlBar()
    bar.move(30, 40)
    half = theme.FLOAT_BUBBLE / 2
    press = QMouseEvent(
        QEvent.Type.MouseButtonPress,
        QPointF(half, half),
        QPointF(30 + half, 40 + half),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    move = QMouseEvent(
        QEvent.Type.MouseMove,
        QPointF(80, 80),
        QPointF(110, 120),
        Qt.MouseButton.NoButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    release = QMouseEvent(
        QEvent.Type.MouseButtonRelease,
        QPointF(80, 80),
        QPointF(110, 120),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
    )

    assert bar.eventFilter(bar._bubble, press)
    assert bar.eventFilter(bar._bubble, move)
    assert bar.eventFilter(bar._bubble, release)
    # Dragging must not expand/collapse the ball.
    assert bar.is_collapsed
    offset = QPointF(half, half)
    expected = QPointF(110, 120).toPoint() - offset.toPoint()
    assert bar.pos() == expected



def test_translucent_floating_bar_reports_capture_exclusion_as_unavailable(
    qt_app: QApplication,
) -> None:
    bar = FloatingControlBar()
    assert bar.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    assert bar.mask().isEmpty()
    bar.show()
    process_events()
    result = exclude_from_capture(bar)
    bar.hide()
    assert not result.available
    assert "透明悬浮窗" in result.message


@pytest.mark.skipif(os.name != "nt", reason="WDA_EXCLUDEFROMCAPTURE is Windows-only")
def test_unsupported_exclusion_is_cleared_instead_of_leaving_a_black_mask(
    qt_app: QApplication, monkeypatch: pytest.MonkeyPatch
) -> None:
    class Call:
        def __init__(self, callback: object) -> None:
            self.callback = callback

        def __call__(self, *args: object) -> object:
            return self.callback(*args)

    calls: list[int] = []

    def set_affinity(_hwnd: object, value: object) -> bool:
        calls.append(int(value))
        return True

    def get_affinity(_hwnd: object, affinity: object) -> bool:
        affinity._obj.value = 0x00000001
        return True

    class User32:
        def __init__(self) -> None:
            self.SetWindowDisplayAffinity = Call(set_affinity)
            self.GetWindowDisplayAffinity = Call(get_affinity)

    monkeypatch.setattr(platform_windows.ctypes, "WinDLL", lambda *_args, **_kwargs: User32())

    result = exclude_from_capture(QWidget())

    assert not result.available
    assert calls == [WDA_EXCLUDEFROMCAPTURE, WDA_NONE]


@pytest.mark.skipif(os.name != "nt", reason="WDA_EXCLUDEFROMCAPTURE is Windows-only")
def test_annotation_panel_is_excluded_but_canvas_is_capturable(qt_app: QApplication) -> None:
    canvas = AnnotationCanvas()
    panel = AnnotationToolPanel(canvas)
    canvas.setGeometry(QRect(0, 0, 320, 180))
    canvas.show()
    panel.show_for_screen(QRect(0, 0, 800, 600))
    process_events()

    panel_result = exclude_from_capture(panel)
    affinity = wintypes.DWORD()
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.GetWindowDisplayAffinity.argtypes = (wintypes.HWND, ctypes.POINTER(wintypes.DWORD))
    user32.GetWindowDisplayAffinity.restype = wintypes.BOOL
    assert user32.GetWindowDisplayAffinity(
        wintypes.HWND(int(canvas.winId())), ctypes.byref(affinity)
    )
    panel.hide()
    canvas.hide()
    assert panel_result.available, panel_result.message
    assert affinity.value == 0
