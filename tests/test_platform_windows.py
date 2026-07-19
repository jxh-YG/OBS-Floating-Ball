import ctypes
import os
from ctypes import wintypes

import pytest

from obs_floating_controller.platform_windows import HOTKEY_ID, WM_HOTKEY, GlobalHotkey


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
    hotkey.activated.connect(lambda: activated.append(True))
    message = Msg(message=WM_HOTKEY, wParam=HOTKEY_ID)
    assert hotkey.handle_native_message(ctypes.addressof(message))
    assert activated == [True]
