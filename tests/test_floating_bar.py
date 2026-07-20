import os

import pytest
import ctypes
from ctypes import wintypes

from PySide6.QtCore import QEvent, QEventLoop, QPoint, QPointF, QRect, Qt, QTimer
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QApplication, QWidget

import obs_floating_controller.platform_windows as platform_windows
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
    assert bar._primary._kind == "pause"
    assert bar._stop.isEnabled()
    assert not bar._secondary.isEnabled()
    assert bar._display_timer.isActive()

    bar.set_record_status(RecordStatus(RecordingState.PAUSED, 10))
    assert bar._primary._kind == "play"
    assert "继续" in bar._primary.toolTip()
    assert not bar._secondary.isEnabled()
    assert not bar._display_timer.isActive()

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
    assert (theme.FLOAT_BUBBLE, theme.FLOAT_STRIP_HEIGHT, theme.BUTTON_HIT) == (49, 34, 20)
    assert theme.FLOAT_EXPANDED_WIDTH == 157
    assert (bar.width(), bar.height()) == (49, 49)
    assert (bar._primary.width(), bar._primary.height()) == (20, 20)


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
    hidden: list[bool] = []
    bar.hide_requested.connect(lambda: hidden.append(True))
    bar._show_context_menu(QPointF(100, 120).toPoint())
    assert hidden == []
    assert bar._context_menu is not None
    actions = bar._context_menu.actions()
    assert actions[-1].text() == tr("hide_floating_ball")
    actions[-1].trigger()
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

def test_context_menu_exposes_open_folder_when_recording_path_exists(qt_app: QApplication) -> None:
    bar = FloatingControlBar()
    bar.set_connection(True, "connected")
    bar.set_recording_output_path(r"C:/recordings/demo.mkv")
    opened: list[bool] = []
    bar.open_folder_requested.connect(lambda: opened.append(True))
    bar._show_context_menu(QPointF(10, 10).toPoint())
    assert bar._context_menu is not None
    labels = [action.text() for action in bar._context_menu.actions() if action.text()]
    assert tr("open_recording_folder") in labels
    for action in bar._context_menu.actions():
        if action.text() == tr("open_recording_folder"):
            action.trigger()
            break
    assert opened == [True]


def test_context_menu_uses_rounded_menu(qt_app: QApplication) -> None:
    from obs_floating_controller.floating_bar import RoundedMenu

    bar = FloatingControlBar()
    bar._show_context_menu(QPointF(10, 10).toPoint())
    assert isinstance(bar._context_menu, RoundedMenu)


def test_display_timer_only_runs_while_recording(qt_app: QApplication) -> None:
    bar = FloatingControlBar()
    assert not bar._display_timer.isActive()
    bar.set_connection(True, "connected")
    bar.set_record_status(RecordStatus(RecordingState.IDLE, 0))
    assert not bar._display_timer.isActive()
    bar.set_record_status(RecordStatus(RecordingState.RECORDING, 1))
    assert bar._display_timer.isActive()
    bar.set_connection(False, "offline")
    assert not bar._display_timer.isActive()



