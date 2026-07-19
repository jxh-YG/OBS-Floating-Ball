"""Per-user settings with Windows DPAPI password storage."""

from __future__ import annotations

import base64
import ctypes
import os
from ctypes import wintypes
from dataclasses import dataclass

from PySide6.QtCore import QSettings

from .i18n import CHINESE, normalize_language


@dataclass(frozen=True)
class ConnectionSettings:
    host: str = "127.0.0.1"
    port: int = 4455
    password: str = ""
    configured: bool = False
    language: str = CHINESE


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


class SettingsStore:
    def __init__(self) -> None:
        self._settings = QSettings("OBS Floating Ball", "OBS Floating Ball")
        self._legacy_settings = QSettings("OBS中文悬浮控制器", "OBS中文悬浮控制器")

    def _migrate_legacy_settings(self) -> None:
        if self._settings.contains("connection/configured") or not self._legacy_settings.contains(
            "connection/configured"
        ):
            return
        for key in ("connection/configured", "connection/password", "interface/language"):
            self._settings.setValue(key, self._legacy_settings.value(key))
        self._settings.sync()

    def load(self) -> ConnectionSettings:
        self._migrate_legacy_settings()
        configured = self._settings.value("connection/configured", False, type=bool)
        language = normalize_language(self._settings.value("interface/language", CHINESE, type=str))
        encrypted = self._settings.value("connection/password", "", type=str)
        password = ""
        if encrypted:
            try:
                password = DpapiProtector().unprotect(encrypted)
            except (OSError, ValueError, ctypes.ArgumentError):
                configured = False
        return ConnectionSettings(password=password, configured=configured, language=language)

    def save_password(self, password: str, language: str) -> ConnectionSettings:
        encrypted = DpapiProtector().protect(password)
        self._settings.setValue("connection/password", encrypted)
        self._settings.setValue("connection/configured", True)
        self._settings.setValue("interface/language", normalize_language(language))
        self._settings.sync()
        return ConnectionSettings(password=password, configured=True, language=normalize_language(language))
