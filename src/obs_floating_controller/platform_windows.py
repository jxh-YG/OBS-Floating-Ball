"""Windows-only integrations: capture exclusion, hotkeys, autostart, single-instance."""

from __future__ import annotations

import ctypes
import os
import sys
import winreg
from ctypes import wintypes
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QKeyCombination, QObject, Qt, Signal
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import QWidget


WDA_NONE = 0x00000000
WDA_EXCLUDEFROMCAPTURE = 0x00000011
WM_HOTKEY = 0x0312
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
VK_H = 0x48
DEFAULT_HOTKEY_MODIFIERS = MOD_CONTROL | MOD_ALT
DEFAULT_HOTKEY_KEY = VK_H
HOTKEY_ID = 0x4F425348  # legacy single-id alias for toggle
HOTKEY_IDS = {
    "toggle": 0x4F425348,
    "start": 0x4F425349,
    "pause": 0x4F42534A,
    "stop": 0x4F42534B,
}
AUTOSTART_VALUE_NAME = "OBS Floating Ball"
AUTOSTART_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
SINGLE_INSTANCE_MUTEX = "Local\\OBSFloatingBallSingleton"
ERROR_ALREADY_EXISTS = 183


@dataclass(frozen=True)
class CaptureExclusionResult:
    available: bool
    message: str = ""


@dataclass(frozen=True)
class HotkeySpec:
    modifiers: int = DEFAULT_HOTKEY_MODIFIERS
    key: int = DEFAULT_HOTKEY_KEY

    def display(self) -> str:
        return format_hotkey(self.modifiers, self.key)


def default_hotkey_bundle() -> object:
    # Imported lazily-shaped bundle via simple namespace-like object for config defaults.
    from types import SimpleNamespace

    return SimpleNamespace(
        toggle=HotkeySpec(DEFAULT_HOTKEY_MODIFIERS, DEFAULT_HOTKEY_KEY),
        start=HotkeySpec(DEFAULT_HOTKEY_MODIFIERS, 0x52),
        pause=HotkeySpec(DEFAULT_HOTKEY_MODIFIERS, 0x50),
        stop=HotkeySpec(DEFAULT_HOTKEY_MODIFIERS, 0x53),
    )


def format_hotkey(modifiers: int, key: int) -> str:
    parts: list[str] = []
    if modifiers & MOD_CONTROL:
        parts.append("Ctrl")
    if modifiers & MOD_ALT:
        parts.append("Alt")
    if modifiers & MOD_SHIFT:
        parts.append("Shift")
    if modifiers & MOD_WIN:
        parts.append("Win")
    parts.append(_vk_name(key))
    return "+".join(parts)


def _vk_name(key: int) -> str:
    if 0x30 <= key <= 0x39 or 0x41 <= key <= 0x5A:
        return chr(key)
    if 0x70 <= key <= 0x87:
        return f"F{key - 0x6F}"
    return f"0x{key:02X}"


def qt_key_to_vk(key: Qt.Key) -> int | None:
    value = int(key)
    if Qt.Key.Key_A <= key <= Qt.Key.Key_Z:
        return value
    if Qt.Key.Key_0 <= key <= Qt.Key.Key_9:
        return value
    if Qt.Key.Key_F1 <= key <= Qt.Key.Key_F24:
        return 0x70 + (value - int(Qt.Key.Key_F1))
    return None


def key_sequence_to_hotkey(sequence: QKeySequence) -> HotkeySpec | None:
    if sequence.isEmpty():
        return None
    combination = sequence[0]
    qt_key = combination.key()
    qt_mods = combination.keyboardModifiers()
    vk = qt_key_to_vk(qt_key)
    if vk is None:
        return None
    modifiers = 0
    if qt_mods & Qt.KeyboardModifier.ControlModifier:
        modifiers |= MOD_CONTROL
    if qt_mods & Qt.KeyboardModifier.AltModifier:
        modifiers |= MOD_ALT
    if qt_mods & Qt.KeyboardModifier.ShiftModifier:
        modifiers |= MOD_SHIFT
    if qt_mods & Qt.KeyboardModifier.MetaModifier:
        modifiers |= MOD_WIN
    if modifiers == 0:
        return None
    return HotkeySpec(modifiers=modifiers, key=vk)


def hotkey_to_key_sequence(spec: HotkeySpec) -> QKeySequence:
    qt_mods = Qt.KeyboardModifier.NoModifier
    if spec.modifiers & MOD_CONTROL:
        qt_mods |= Qt.KeyboardModifier.ControlModifier
    if spec.modifiers & MOD_ALT:
        qt_mods |= Qt.KeyboardModifier.AltModifier
    if spec.modifiers & MOD_SHIFT:
        qt_mods |= Qt.KeyboardModifier.ShiftModifier
    if spec.modifiers & MOD_WIN:
        qt_mods |= Qt.KeyboardModifier.MetaModifier
    return QKeySequence(QKeyCombination(qt_mods, Qt.Key(spec.key)))


def exclude_from_capture(widget: QWidget) -> CaptureExclusionResult:
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
        user32.SetWindowDisplayAffinity(hwnd, WDA_NONE)
        return CaptureExclusionResult(False, "系统未启用 WDA_EXCLUDEFROMCAPTURE；已取消黑色遮罩回退")
    return CaptureExclusionResult(True)


def application_launch_command() -> str:
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'
    main_path = Path(sys.argv[0]).resolve()
    return f'"{sys.executable}" "{main_path}"'


def set_autostart_enabled(enabled: bool, command: str | None = None) -> None:
    if os.name != "nt":
        return
    launch = command or application_launch_command()
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, AUTOSTART_RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
        if enabled:
            winreg.SetValueEx(key, AUTOSTART_VALUE_NAME, 0, winreg.REG_SZ, launch)
            return
        try:
            winreg.DeleteValue(key, AUTOSTART_VALUE_NAME)
        except FileNotFoundError:
            pass


def is_autostart_enabled() -> bool:
    if os.name != "nt":
        return False
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, AUTOSTART_RUN_KEY, 0, winreg.KEY_READ) as key:
            winreg.QueryValueEx(key, AUTOSTART_VALUE_NAME)
            return True
    except FileNotFoundError:
        return False
    except OSError:
        return False


def acquire_single_instance() -> ctypes.c_void_p | None:
    """Return a mutex handle when this is the first instance, else None."""
    if os.name != "nt":
        return ctypes.c_void_p(1)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateMutexW.argtypes = (wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR)
    kernel32.CreateMutexW.restype = wintypes.HANDLE
    handle = kernel32.CreateMutexW(None, False, SINGLE_INSTANCE_MUTEX)
    if not handle:
        return None
    if ctypes.get_last_error() == ERROR_ALREADY_EXISTS:
        kernel32.CloseHandle(handle)
        return None
    return handle


class GlobalHotkey(QObject):
    """Registers one or more hotkeys with the Windows message queue."""

    activated = Signal()  # toggle (backward compatible)
    start_activated = Signal()
    pause_activated = Signal()
    stop_activated = Signal()
    registration_failed = Signal(str)

    def __init__(self, toggle: HotkeySpec | None = None) -> None:
        super().__init__()
        defaults = default_hotkey_bundle()
        self._specs = {
            "toggle": toggle or defaults.toggle,
            "start": defaults.start,
            "pause": defaults.pause,
            "stop": defaults.stop,
        }
        self._registered: set[str] = set()

    @property
    def spec(self) -> HotkeySpec:
        return self._specs["toggle"]

    def configure_all(
        self,
        *,
        toggle: HotkeySpec,
        start: HotkeySpec,
        pause: HotkeySpec,
        stop: HotkeySpec,
    ) -> bool:
        self.unregister()
        self._specs = {"toggle": toggle, "start": start, "pause": pause, "stop": stop}
        return self.register()

    def configure(self, modifiers: int, key: int) -> bool:
        return self.configure_all(
            toggle=HotkeySpec(modifiers, key),
            start=self._specs["start"],
            pause=self._specs["pause"],
            stop=self._specs["stop"],
        )

    def register(self) -> bool:
        if os.name != "nt":
            self.registration_failed.emit("全局快捷键仅支持 Windows")
            return False
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        user32.RegisterHotKey.argtypes = (wintypes.HWND, ctypes.c_int, wintypes.UINT, wintypes.UINT)
        user32.RegisterHotKey.restype = wintypes.BOOL
        ok = True
        failures: list[str] = []
        for name, hotkey_id in HOTKEY_IDS.items():
            spec = self._specs[name]
            if not user32.RegisterHotKey(None, hotkey_id, spec.modifiers, spec.key):
                ok = False
                failures.append(f"{name}: {spec.display()}")
            else:
                self._registered.add(name)
        if failures:
            self.registration_failed.emit("快捷键不可用: " + ", ".join(failures))
        return ok and len(self._registered) == len(HOTKEY_IDS)

    def unregister(self) -> None:
        if os.name == "nt" and self._registered:
            user32 = ctypes.WinDLL("user32", use_last_error=True)
            user32.UnregisterHotKey.argtypes = (wintypes.HWND, ctypes.c_int)
            user32.UnregisterHotKey.restype = wintypes.BOOL
            for name in list(self._registered):
                user32.UnregisterHotKey(None, HOTKEY_IDS[name])
        self._registered.clear()

    def handle_native_message(self, message_pointer: int) -> bool:
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
        if message.message != WM_HOTKEY:
            return False
        hotkey_id = int(message.wParam)
        if hotkey_id == HOTKEY_IDS["toggle"]:
            self.activated.emit()
            return True
        if hotkey_id == HOTKEY_IDS["start"]:
            self.start_activated.emit()
            return True
        if hotkey_id == HOTKEY_IDS["pause"]:
            self.pause_activated.emit()
            return True
        if hotkey_id == HOTKEY_IDS["stop"]:
            self.stop_activated.emit()
            return True
        return False
