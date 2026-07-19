"""Windows-only integrations: capture exclusion and a global hotkey."""

from __future__ import annotations

import ctypes
import os
from ctypes import wintypes
from dataclasses import dataclass

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtWidgets import QWidget


WDA_NONE = 0x00000000
WDA_EXCLUDEFROMCAPTURE = 0x00000011
WM_HOTKEY = 0x0312
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
VK_H = 0x48
HOTKEY_ID = 0x4F425348


@dataclass(frozen=True)
class CaptureExclusionResult:
    available: bool
    message: str = ""


def exclude_from_capture(widget: QWidget) -> CaptureExclusionResult:
    """Apply and verify WDA_EXCLUDEFROMCAPTURE for an already-created window.

    Windows versions without exclusion support can fall back to WDA_MONITOR,
    which renders the window as a black patch in a capture. Clear that fallback
    rather than leaving a partially supported affinity active.
    """
    if os.name != "nt":
        return CaptureExclusionResult(False, "当前系统不是 Windows")
    if widget.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground):
        return CaptureExclusionResult(False, "透明悬浮窗模式不支持 Windows 采集排除")
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.SetWindowDisplayAffinity.argtypes = (wintypes.HWND, wintypes.DWORD)
    user32.SetWindowDisplayAffinity.restype = wintypes.BOOL
    user32.GetWindowDisplayAffinity.argtypes = (wintypes.HWND, ctypes.POINTER(wintypes.DWORD))
    user32.GetWindowDisplayAffinity.restype = wintypes.BOOL
    hwnd = wintypes.HWND(int(widget.winId()))
    if not user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE):
        error = ctypes.get_last_error()
        return CaptureExclusionResult(False, f"SetWindowDisplayAffinity 失败（{error}）")
    affinity = wintypes.DWORD()
    if not user32.GetWindowDisplayAffinity(hwnd, ctypes.byref(affinity)):
        error = ctypes.get_last_error()
        user32.SetWindowDisplayAffinity(hwnd, WDA_NONE)
        return CaptureExclusionResult(False, f"无法验证采集排除（{error}）；已取消黑色遮罩回退")
    if affinity.value != WDA_EXCLUDEFROMCAPTURE:
        # Windows 10 builds before 2004 treat 0x11 as WDA_MONITOR (0x1), which
        # masks the control as black instead of excluding it. Do not retain it.
        user32.SetWindowDisplayAffinity(hwnd, WDA_NONE)
        return CaptureExclusionResult(False, "系统未启用 WDA_EXCLUDEFROMCAPTURE；已取消黑色遮罩回退")
    return CaptureExclusionResult(True)


class GlobalHotkey(QObject):
    """Registers Ctrl+Alt+H with the Windows message queue."""

    activated = Signal()
    registration_failed = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._registered = False

    def register(self) -> bool:
        if os.name != "nt":
            self.registration_failed.emit("全局快捷键仅支持 Windows")
            return False
        if self._registered:
            return True
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        user32.RegisterHotKey.argtypes = (wintypes.HWND, ctypes.c_int, wintypes.UINT, wintypes.UINT)
        user32.RegisterHotKey.restype = wintypes.BOOL
        if not user32.RegisterHotKey(None, HOTKEY_ID, MOD_CONTROL | MOD_ALT, VK_H):
            self.registration_failed.emit("Ctrl+Alt+H 已被其他程序占用")
            return False
        self._registered = True
        return True

    def unregister(self) -> None:
        if self._registered and os.name == "nt":
            user32 = ctypes.WinDLL("user32", use_last_error=True)
            user32.UnregisterHotKey.argtypes = (wintypes.HWND, ctypes.c_int)
            user32.UnregisterHotKey.restype = wintypes.BOOL
            user32.UnregisterHotKey(None, HOTKEY_ID)
        self._registered = False

    def handle_native_message(self, message_pointer: int) -> bool:
        """Process a native MSG pointer; called by the application's event filter."""
        if os.name != "nt":
            return False

        class _Msg(ctypes.Structure):
            _fields_ = [
                ("hwnd", wintypes.HWND),
                ("message", wintypes.UINT),
                ("wParam", wintypes.WPARAM),
                ("lParam", wintypes.LPARAM),
                ("time", wintypes.DWORD),
                ("pt", wintypes.POINT),
            ]

        message = _Msg.from_address(message_pointer)
        if message.message == WM_HOTKEY and message.wParam == HOTKEY_ID:
            self.activated.emit()
            return True
        return False
