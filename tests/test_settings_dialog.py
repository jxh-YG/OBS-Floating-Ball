import os

import pytest
from PySide6.QtCore import QPoint, QSize
from PySide6.QtGui import QColor, QKeySequence
from PySide6.QtWidgets import QApplication, QDialog

from obs_floating_controller.config import ConnectionSettings, HotkeyBundle, SettingsUpdate
from obs_floating_controller.i18n import CHINESE, ENGLISH, tr
from obs_floating_controller.platform_windows import (
    DEFAULT_HOTKEY_KEY,
    DEFAULT_HOTKEY_MODIFIERS,
    HotkeySpec,
    default_hotkey_bundle,
    format_hotkey,
    hotkey_to_key_sequence,
    key_sequence_to_hotkey,
)
from obs_floating_controller.settings_dialog import SettingsDialog


@pytest.fixture(scope="module")
def qt_app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_cancel_button_matches_primary_button_size_and_rejects(qt_app: QApplication) -> None:
    dialog = SettingsDialog(ConnectionSettings(), lambda _language: "")
    assert dialog._save.size() == QSize(132, 42)
    assert dialog._cancel.size() == dialog._save.size()
    dialog._cancel.click()
    assert dialog.result() == QDialog.DialogCode.Rejected


def test_save_emits_settings_update_with_host_port_and_options(qt_app: QApplication) -> None:
    defaults = default_hotkey_bundle()
    settings = ConnectionSettings(
        password="secret",
        language=CHINESE,
        hotkeys=HotkeyBundle(
            toggle=defaults.toggle,
            start=defaults.start,
            pause=defaults.pause,
            stop=defaults.stop,
        ),
        autostart=True,
        auto_rename_on_stop=True,
    )
    dialog = SettingsDialog(settings, lambda _language: "status")
    captured: list[SettingsUpdate] = []
    dialog.settings_saved.connect(captured.append)
    dialog._host.setText("127.0.0.1")
    dialog._port.setValue(4455)
    dialog._password.setText("new-pass")
    dialog._autostart.setChecked(False)
    dialog._auto_rename.setChecked(True)
    dialog._save.click()
    assert dialog.result() == QDialog.DialogCode.Accepted
    assert len(captured) == 1
    assert captured[0].password == "new-pass"
    assert captured[0].host == "127.0.0.1"
    assert captured[0].port == 4455
    assert captured[0].autostart is False
    assert captured[0].auto_rename_on_stop is True
