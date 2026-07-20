"""Per-user settings with Windows DPAPI password storage."""

from __future__ import annotations

import base64
import ctypes
import json
import os
from ctypes import wintypes
from dataclasses import dataclass, field

from PySide6.QtCore import QSettings

from .i18n import CHINESE, normalize_language
from .platform_windows import (
    DEFAULT_HOTKEY_KEY,
    DEFAULT_HOTKEY_MODIFIERS,
    HotkeySpec,
    default_hotkey_bundle,
)


@dataclass(frozen=True)
class HotkeyBundle:
    toggle: HotkeySpec = field(default_factory=lambda: HotkeySpec(DEFAULT_HOTKEY_MODIFIERS, DEFAULT_HOTKEY_KEY))
    start: HotkeySpec = field(default_factory=lambda: HotkeySpec(DEFAULT_HOTKEY_MODIFIERS, 0x52))  # R
    pause: HotkeySpec = field(default_factory=lambda: HotkeySpec(DEFAULT_HOTKEY_MODIFIERS, 0x50))  # P
    stop: HotkeySpec = field(default_factory=lambda: HotkeySpec(DEFAULT_HOTKEY_MODIFIERS, 0x53))  # S


@dataclass(frozen=True)
class ConnectionSettings:
    host: str = "127.0.0.1"
    port: int = 4455
    password: str = ""
    configured: bool = False
    language: str = CHINESE
    hotkeys: HotkeyBundle = field(default_factory=HotkeyBundle)
    autostart: bool = False
    auto_rename_on_stop: bool = False
    auto_hide_while_recording: bool = False
    recent_recordings: tuple[str, ...] = ()


@dataclass(frozen=True)
class SettingsUpdate:
    host: str
    port: int
    password: str
    language: str
    hotkeys: HotkeyBundle
    autostart: bool
    auto_rename_on_stop: bool
    auto_hide_while_recording: bool


class _DataBlob(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_byte))]


class DpapiProtector:
    """Encrypt data for the current Windows user using DPAPI."""

    def __init__(self) -> None:
        if os.name != "nt":
            raise OSError("DPAPI 仅在 Windows 上可用")
        self._crypt32 = ctypes.WinDLL("crypt32", use_last_error=True)
        self._crypt32.CryptProtectData.argtypes = (
            ctypes.POINTER(_DataBlob),
            wintypes.LPCWSTR,
            ctypes.POINTER(_DataBlob),
            ctypes.c_void_p,
            ctypes.c_void_p,
            wintypes.DWORD,
            ctypes.POINTER(_DataBlob),
        )
        self._crypt32.CryptProtectData.restype = wintypes.BOOL
        self._crypt32.CryptUnprotectData.argtypes = self._crypt32.CryptProtectData.argtypes
        self._crypt32.CryptUnprotectData.restype = wintypes.BOOL
        self._kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self._kernel32.LocalFree.argtypes = (wintypes.HLOCAL,)
        self._kernel32.LocalFree.restype = wintypes.HLOCAL

    @staticmethod
    def _blob(data: bytes) -> tuple[_DataBlob, ctypes.Array[ctypes.c_char]]:
        buffer = ctypes.create_string_buffer(data)
        return _DataBlob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_byte))), buffer

    def protect(self, value: str) -> str:
        source, source_buffer = self._blob(value.encode("utf-8"))
        target = _DataBlob()
        if not self._crypt32.CryptProtectData(
            ctypes.byref(source), None, None, None, None, 0, ctypes.byref(target)
        ):
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            encrypted = ctypes.string_at(target.pbData, target.cbData)
            return base64.b64encode(encrypted).decode("ascii")
        finally:
            self._kernel32.LocalFree(ctypes.cast(target.pbData, wintypes.HLOCAL))

    def unprotect(self, value: str) -> str:
        encrypted = base64.b64decode(value.encode("ascii"))
        source, source_buffer = self._blob(encrypted)
        target = _DataBlob()
        if not self._crypt32.CryptUnprotectData(
            ctypes.byref(source), None, None, None, None, 0, ctypes.byref(target)
        ):
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            return ctypes.string_at(target.pbData, target.cbData).decode("utf-8")
        finally:
            self._kernel32.LocalFree(ctypes.cast(target.pbData, wintypes.HLOCAL))


def _spec_from_values(modifiers: object, key: object, fallback: HotkeySpec) -> HotkeySpec:
    try:
        return HotkeySpec(int(modifiers), int(key))
    except (TypeError, ValueError):
        return fallback


class SettingsStore:
    MAX_RECENT = 8

    def __init__(self) -> None:
        self._settings = QSettings("OBS Floating Ball", "OBS Floating Ball")
        self._legacy_settings = QSettings("OBS中文悬浮控制器", "OBS中文悬浮控制器")
        self._protector: DpapiProtector | None = None

    def _dpapi(self) -> DpapiProtector:
        if self._protector is None:
            self._protector = DpapiProtector()
        return self._protector

    def _migrate_legacy_settings(self) -> None:
        if self._settings.contains("connection/configured") or not self._legacy_settings.contains(
            "connection/configured"
        ):
            return
        for key in ("connection/configured", "connection/password", "interface/language"):
            self._settings.setValue(key, self._legacy_settings.value(key))
        self._settings.sync()

    def _load_hotkeys(self) -> HotkeyBundle:
        defaults = default_hotkey_bundle()
        # Legacy single hotkey → toggle
        legacy_mod = self._settings.value("hotkey/modifiers", None)
        legacy_key = self._settings.value("hotkey/key", None)
        toggle_fallback = defaults.toggle
        if legacy_mod is not None and legacy_key is not None:
            toggle_fallback = _spec_from_values(legacy_mod, legacy_key, defaults.toggle)
        return HotkeyBundle(
            toggle=_spec_from_values(
                self._settings.value("hotkey/toggle/modifiers", toggle_fallback.modifiers),
                self._settings.value("hotkey/toggle/key", toggle_fallback.key),
                toggle_fallback,
            ),
            start=_spec_from_values(
                self._settings.value("hotkey/start/modifiers", defaults.start.modifiers),
                self._settings.value("hotkey/start/key", defaults.start.key),
                defaults.start,
            ),
            pause=_spec_from_values(
                self._settings.value("hotkey/pause/modifiers", defaults.pause.modifiers),
                self._settings.value("hotkey/pause/key", defaults.pause.key),
                defaults.pause,
            ),
            stop=_spec_from_values(
                self._settings.value("hotkey/stop/modifiers", defaults.stop.modifiers),
                self._settings.value("hotkey/stop/key", defaults.stop.key),
                defaults.stop,
            ),
        )

    def _load_recent(self) -> tuple[str, ...]:
        raw = self._settings.value("recordings/recent", "[]")
        try:
            data = json.loads(str(raw))
            if isinstance(data, list):
                return tuple(str(item) for item in data if item)[: self.MAX_RECENT]
        except json.JSONDecodeError:
            pass
        return ()

    def load(self) -> ConnectionSettings:
        self._migrate_legacy_settings()
        configured = self._settings.value("connection/configured", False, type=bool)
        language = normalize_language(self._settings.value("interface/language", CHINESE, type=str))
        host = str(self._settings.value("connection/host", "127.0.0.1") or "127.0.0.1").strip() or "127.0.0.1"
        try:
            port = int(self._settings.value("connection/port", 4455))
        except (TypeError, ValueError):
            port = 4455
        port = max(1, min(port, 65535))
        encrypted = self._settings.value("connection/password", "", type=str)
        password = ""
        if encrypted:
            try:
                password = self._dpapi().unprotect(encrypted)
            except (OSError, ValueError, ctypes.ArgumentError):
                configured = False
        return ConnectionSettings(
            host=host,
            port=port,
            password=password,
            configured=configured,
            language=language,
            hotkeys=self._load_hotkeys(),
            autostart=self._settings.value("interface/autostart", False, type=bool),
            auto_rename_on_stop=self._settings.value("interface/auto_rename_on_stop", False, type=bool),
            auto_hide_while_recording=self._settings.value(
                "interface/auto_hide_while_recording", False, type=bool
            ),
            recent_recordings=self._load_recent(),
        )

    def save(self, update: SettingsUpdate) -> ConnectionSettings:
        encrypted = self._dpapi().protect(update.password)
        language = normalize_language(update.language)
        host = (update.host or "127.0.0.1").strip() or "127.0.0.1"
        port = max(1, min(int(update.port), 65535))
        self._settings.setValue("connection/password", encrypted)
        self._settings.setValue("connection/configured", True)
        self._settings.setValue("connection/host", host)
        self._settings.setValue("connection/port", port)
        self._settings.setValue("interface/language", language)
        for name, spec in (
            ("toggle", update.hotkeys.toggle),
            ("start", update.hotkeys.start),
            ("pause", update.hotkeys.pause),
            ("stop", update.hotkeys.stop),
        ):
            self._settings.setValue(f"hotkey/{name}/modifiers", int(spec.modifiers))
            self._settings.setValue(f"hotkey/{name}/key", int(spec.key))
        # Keep legacy keys in sync with toggle for older builds.
        self._settings.setValue("hotkey/modifiers", int(update.hotkeys.toggle.modifiers))
        self._settings.setValue("hotkey/key", int(update.hotkeys.toggle.key))
        self._settings.setValue("interface/autostart", bool(update.autostart))
        self._settings.setValue("interface/auto_rename_on_stop", bool(update.auto_rename_on_stop))
        self._settings.setValue(
            "interface/auto_hide_while_recording", bool(update.auto_hide_while_recording)
        )
        self._settings.sync()
        current_recent = self._load_recent()
        return ConnectionSettings(
            host=host,
            port=port,
            password=update.password,
            configured=True,
            language=language,
            hotkeys=update.hotkeys,
            autostart=update.autostart,
            auto_rename_on_stop=update.auto_rename_on_stop,
            auto_hide_while_recording=update.auto_hide_while_recording,
            recent_recordings=current_recent,
        )

    def remember_recording(self, path: str) -> tuple[str, ...]:
        items = [path, *[item for item in self._load_recent() if item != path]]
        trimmed = tuple(items[: self.MAX_RECENT])
        self._settings.setValue("recordings/recent", json.dumps(list(trimmed)))
        self._settings.sync()
        return trimmed

    def save_password(self, password: str, language: str) -> ConnectionSettings:
        current = self.load()
        return self.save(
            SettingsUpdate(
                host=current.host,
                port=current.port,
                password=password,
                language=language,
                hotkeys=current.hotkeys,
                autostart=current.autostart,
                auto_rename_on_stop=current.auto_rename_on_stop,
                auto_hide_while_recording=current.auto_hide_while_recording,
            )
        )

    def load_window_position(self) -> tuple[int, int] | None:
        if not self._settings.contains("window/x") or not self._settings.contains("window/y"):
            return None
        try:
            return (
                int(self._settings.value("window/x")),
                int(self._settings.value("window/y")),
            )
        except (TypeError, ValueError):
            return None

    def save_window_position(self, x: int, y: int) -> None:
        self._settings.setValue("window/x", int(x))
        self._settings.setValue("window/y", int(y))
        self._settings.sync()
