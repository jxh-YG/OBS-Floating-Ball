import ctypes
import os
from ctypes import wintypes

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import QApplication

from obs_floating_controller.platform_windows import (
    HOTKEY_ID,
    HOTKEY_IDS,
    MOD_ALT,
    MOD_CONTROL,
    WM_HOTKEY,
    GlobalHotkey,
    HotkeySpec,
    format_hotkey,
    hotkey_to_key_sequence,
    key_sequence_to_hotkey,
)


@pytest.fixture(scope="module")
def qt_app() -> QApplication:
    return QApplication.instance() or QApplication([])


@pytest.mark.skipif(os.name != "nt", reason="Windows native message handling only")
def test_global_hotkey_emits_for_its_registered_message() -> None:
    class Msg(ctypes.Structure):
        _fields_ = [
            ("hwnd", wintypes.HWND),
            ("message", wintypes.UINT),
            ("wParam", wintypes.WPARAM),
            ("lParam", wintypes.LPARAM),
            ("time", wintypes.DWORD),
            ("pt", wintypes.POINT),
        ]

    hotkey = GlobalHotkey()
    activated: list[bool] = []
    started: list[bool] = []
    hotkey.activated.connect(lambda: activated.append(True))
    hotkey.start_activated.connect(lambda: started.append(True))
    message = Msg(message=WM_HOTKEY, wParam=HOTKEY_IDS["toggle"])
    assert hotkey.handle_native_message(ctypes.addressof(message))
    assert activated == [True]
    message = Msg(message=WM_HOTKEY, wParam=HOTKEY_IDS["start"])
    assert hotkey.handle_native_message(ctypes.addressof(message))
    assert started == [True]


def test_hotkey_round_trip_through_key_sequence(qt_app: QApplication) -> None:
    original = HotkeySpec(MOD_CONTROL | MOD_ALT, 0x48)
    sequence = hotkey_to_key_sequence(original)
    parsed = key_sequence_to_hotkey(sequence)
    assert parsed is not None
    assert parsed.modifiers == original.modifiers
    assert parsed.key == original.key
    assert format_hotkey(original.modifiers, original.key) == "Ctrl+Alt+H"


def test_key_sequence_without_modifier_is_rejected(qt_app: QApplication) -> None:
    assert key_sequence_to_hotkey(QKeySequence(Qt.Key.Key_H)) is None
