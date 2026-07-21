from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication, QSystemTrayIcon

from obs_floating_controller.config import ConnectionSettings
from obs_floating_controller.main import ApplicationController
from obs_floating_controller.models import RecordStatus, RecordingState


@pytest.fixture(scope="module")
def qt_app() -> QApplication:
    return QApplication.instance() or QApplication([])


@pytest.fixture
def controller(qt_app: QApplication) -> ApplicationController:
    # Avoid stacking many controllers' native filters across tests by reusing carefully.
    ctrl = ApplicationController(qt_app)
    ctrl._connection_settings = replace(
        ctrl._connection_settings,
        auto_hide_while_recording=True,
        auto_rename_on_stop=False,
    )
    return ctrl


def test_auto_hide_only_on_enter_recording_edge(controller: ApplicationController) -> None:
    controller._visibility.set_visible(True)
    controller._bar.show()
    controller._auto_hidden_for_recording = False
    controller._last_record_state = RecordingState.IDLE

    controller._on_record_status_changed(RecordStatus(RecordingState.RECORDING, 1))
    assert controller._auto_hidden_for_recording is True
    assert controller._visibility.visible is False

    # Repeat RECORDING status (poll) must not re-hide after manual show.
    controller.toggle_floating_bar()
    assert controller._visibility.visible is True
    assert controller._auto_hidden_for_recording is False
    controller._on_record_status_changed(RecordStatus(RecordingState.RECORDING, 2))
    assert controller._visibility.visible is True
    assert controller._auto_hidden_for_recording is False


def test_auto_hide_restores_on_idle_and_disconnect(controller: ApplicationController) -> None:
    controller._auto_hidden_for_recording = True
    controller._visibility.set_visible(False)
    controller._bar.hide()
    controller._last_record_state = RecordingState.RECORDING

    controller._on_record_status_changed(RecordStatus(RecordingState.IDLE, 0))
    assert controller._auto_hidden_for_recording is False
    assert controller._visibility.visible is True

    controller._auto_hidden_for_recording = True
    controller._visibility.set_visible(False)
    controller._bar.hide()
    controller._last_record_state = RecordingState.RECORDING
    controller._on_record_status_changed(RecordStatus(RecordingState.DISCONNECTED, 0))
    assert controller._auto_hidden_for_recording is False
    assert controller._visibility.visible is True


def test_finished_path_clears_only_when_recording_becomes_active(
    controller: ApplicationController,
) -> None:
    controller._last_recording_output_path = Path(r"C:/recordings/demo.mkv")
    controller._bar.set_recording_output_path(r"C:/recordings/demo.mkv")
    controller._last_record_state = RecordingState.IDLE
    controller._bar.set_connection(True, "connected")
    controller._bar.set_record_status(RecordStatus(RecordingState.IDLE, 0))
    assert controller._bar._secondary.isEnabled()

    # Failed start: stay idle, path remains.
    controller._on_record_status_changed(RecordStatus(RecordingState.IDLE, 0))
    assert controller._last_recording_output_path == Path(r"C:/recordings/demo.mkv")

    controller._on_record_status_changed(RecordStatus(RecordingState.RECORDING, 1))
    assert controller._last_recording_output_path is None
    assert controller._bar._last_recording_output_path is None


def test_rename_busy_notifies_once(controller: ApplicationController, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    missing = tmp_path / "not-yet.mkv"
    controller._last_recording_output_path = missing
    notes: list[tuple[str, str]] = []

    def capture(title: str, message: str, *, informational: bool = False) -> None:
        notes.append((title, message))

    monkeypatch.setattr(controller, "_notify", capture)
    monkeypatch.setattr(
        "obs_floating_controller.main.QTimer.singleShot",
        lambda _ms, callback: None,
    )

    controller.rename_last_recording()  # arm wait
    controller.rename_last_recording()  # first retry + notify
    controller.rename_last_recording()  # second retry, no extra notify
    assert len(notes) == 1
