"""Application composition and process entry point."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from PySide6.QtCore import QAbstractNativeEventFilter, QObject, Qt, QTimer, QUrl
from PySide6.QtGui import QAction, QColor, QDesktopServices, QFont, QGuiApplication, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from . import __version__
from .config import ConnectionSettings, SettingsStore, SettingsUpdate
from .dialogs import prompt_text, show_alert
from .floating_bar import FloatingControlBar
from .i18n import normalize_language, tr
from .logging_util import configure_logging
from .models import RecordStatus, RecordingState
from .obs_websocket import ObsWebSocketClient
from .platform_windows import (
    CaptureExclusionResult,
    GlobalHotkey,
    acquire_single_instance,
    application_launch_command,
    exclude_from_capture,
    format_hotkey,
    set_autostart_enabled,
)
from .settings_dialog import SettingsDialog
from .visibility import VisibilityState


def build_tray_icon(*, connected: bool, recording: bool, paused: bool, finished: bool) -> QIcon:
    if recording:
        fill = QColor("#E02020")
    elif paused:
        fill = QColor("#FF9F0A")
    elif not connected:
        fill = QColor("#8E8E93")
    elif finished:
        fill = QColor("#22C55E")
    else:
        fill = QColor("#0A84FF")

    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(255, 255, 255, 230))
    painter.drawEllipse(4, 4, 56, 56)
    painter.setBrush(fill)
    painter.drawEllipse(10, 10, 44, 44)
    painter.setBrush(QColor(255, 255, 255, 160))
    painter.drawEllipse(18, 16, 14, 10)
    painter.end()
    return QIcon(pixmap)


class NativeEventFilter(QAbstractNativeEventFilter):
    def __init__(self, hotkey: GlobalHotkey) -> None:
        super().__init__()
        self._hotkey = hotkey

    def nativeEventFilter(self, _event_type: object, message: object) -> tuple[bool, int]:
        return self._hotkey.handle_native_message(int(message)), 0


class ApplicationController(QObject):
    def __init__(self, app: QApplication) -> None:
        super().__init__(app)
        self._app = app
        self._settings_store = SettingsStore()
        self._connection_settings = self._settings_store.load()
        self._language = normalize_language(self._connection_settings.language)
        self._floating_bar_capture_result: CaptureExclusionResult | None = None
        self._visibility = VisibilityState()
        self._auto_hidden_for_recording = False
        self._client = ObsWebSocketClient(self)
        self._bar = FloatingControlBar()
        self._bar.set_status_provider(lambda: self._client.current_status)
        self._bar.set_recent_recordings(self._connection_settings.recent_recordings)
        self._last_recording_output_path: Path | None = None
        self._hotkey = GlobalHotkey(self._connection_settings.hotkeys.toggle)
        self._native_filter = NativeEventFilter(self._hotkey)
        self._app.installNativeEventFilter(self._native_filter)
        self._settings_dialog: SettingsDialog | None = None
        self._auth_prompted = False
        self._rename_retry_remaining = 0
        self._rename_dialog_open = False
        self._status_poll = QTimer(self)
        self._status_poll.setInterval(15_000)
        self._status_poll.timeout.connect(self._poll_record_status)
        self._build_tray()
        self._wire_events()
        self._apply_language(self._language)
        self._refresh_tray_icon()

    def _build_tray(self) -> None:
        self._tray = QSystemTrayIcon(self)
        menu = QMenu()
        self._toggle_action = QAction(menu)
        self._toggle_action.triggered.connect(self.toggle_floating_bar)
        self._settings_action = QAction(menu)
        self._settings_action.triggered.connect(self.show_settings)
        self._quit_action = QAction(menu)
        self._quit_action.triggered.connect(self.quit)
        menu.addAction(self._toggle_action)
        menu.addAction(self._settings_action)
        menu.addSeparator()
        menu.addAction(self._quit_action)
        self._tray.setContextMenu(menu)
        self._tray.activated.connect(self._on_tray_activated)
        self._tray.show()

    def _wire_events(self) -> None:
        self._client.connection_changed.connect(self._on_connection_changed)
        self._client.record_status_changed.connect(self._on_record_status_changed)
        self._client.recording_output_ready.connect(self._set_recording_output_path)
        self._client.request_failed.connect(
            lambda message: self._notify(tr("obs_action_failed", self._language), message)
        )
        self._bar.start_requested.connect(self._client.start_record)
        self._bar.pause_requested.connect(self._client.pause_record)
        self._bar.resume_requested.connect(self._client.resume_record)
        self._bar.stop_requested.connect(self._client.stop_record)
        self._bar.rename_requested.connect(self.rename_last_recording)
        self._bar.open_folder_requested.connect(self.open_last_recording_folder)
        self._bar.open_recent_requested.connect(self.open_recent_recording)
        self._bar.close_requested.connect(self._hide_floating_bar)
        self._bar.hide_requested.connect(self._hide_floating_bar)
        self._bar.position_changed.connect(self._save_bar_position)
        self._hotkey.activated.connect(self.toggle_floating_bar)
        self._hotkey.start_activated.connect(self._hotkey_start_record)
        self._hotkey.pause_activated.connect(self._hotkey_pause_resume)
        self._hotkey.stop_activated.connect(self._client.stop_record)
        self._hotkey.registration_failed.connect(
            lambda message: self._notify(tr("shortcut_unavailable", self._language), message)
        )
        self._app.aboutToQuit.connect(self._cleanup)
        for screen in QGuiApplication.screens():
            screen.geometryChanged.connect(lambda *_args: self._reclamp_bar_position())
        QGuiApplication.instance().screenAdded.connect(lambda *_args: self._reclamp_bar_position())  # type: ignore[union-attr]
        QGuiApplication.instance().screenRemoved.connect(lambda *_args: self._reclamp_bar_position())  # type: ignore[union-attr]

    def _apply_language(self, language: str) -> None:
        self._language = normalize_language(language)
        self._app.setApplicationDisplayName(tr("app_name", self._language))
        self._client.set_language(self._language)
        self._bar.set_language(self._language)
        self._toggle_action.setText(tr("show_hide", self._language))
        self._settings_action.setText(tr("connection_settings", self._language))
        self._quit_action.setText(tr("quit", self._language))
        toggle = self._connection_settings.hotkeys.toggle
        self._tray.setToolTip(
            f"{tr('app_name', self._language)} ({format_hotkey(toggle.modifiers, toggle.key)})"
        )
        if not self._client.is_connected:
            self._bar.set_connection(False, tr("not_connected", self._language))
        if self._settings_dialog:
            self._settings_dialog.set_language(self._language)

    def start(self) -> None:
        self._position_floating_bar()
        self._bar.show()
        QTimer.singleShot(0, self._verify_floating_bar_capture_exclusion)
        self._register_hotkeys()
        set_autostart_enabled(
            self._connection_settings.autostart,
            application_launch_command(),
        )
        if self._connection_settings.configured:
            self._client.connect_to_server(
                self._connection_settings.password,
                host=self._connection_settings.host,
                port=self._connection_settings.port,
            )
        else:
            QTimer.singleShot(0, self.show_settings)

    def _register_hotkeys(self) -> None:
        hotkeys = self._connection_settings.hotkeys
        if not self._hotkey.configure_all(
            toggle=hotkeys.toggle,
            start=hotkeys.start,
            pause=hotkeys.pause,
            stop=hotkeys.stop,
        ):
            logging.warning("one or more hotkeys failed to register")

    def _verify_floating_bar_capture_exclusion(self) -> None:
        self._floating_bar_capture_result = exclude_from_capture(self._bar)
        if self._settings_dialog:
            self._settings_dialog.set_language(self._language)

    def _position_floating_bar(self) -> None:
        saved = self._settings_store.load_window_position()
        width = self._bar.width()
        height = self._bar.height()
        if saved is not None:
            x, y = self._clamp_position(saved[0], saved[1], width, height)
            self._bar.move(x, y)
            return
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            return
        geometry = screen.availableGeometry()
        self._bar.move(geometry.right() - width - 32, geometry.top() + 32)

    def _reclamp_bar_position(self) -> None:
        pos = self._bar.pos()
        x, y = self._clamp_position(pos.x(), pos.y(), self._bar.width(), self._bar.height())
        self._bar.move(x, y)
        self._save_bar_position()

    def _clamp_position(self, x: int, y: int, width: int, height: int) -> tuple[int, int]:
        screens = QGuiApplication.screens()
        if not screens:
            return x, y
        center_x = x + width // 2
        center_y = y + height // 2
        target = None
        for screen in screens:
            if screen.availableGeometry().contains(center_x, center_y):
                target = screen.availableGeometry()
                break
        if target is None:
            primary = QGuiApplication.primaryScreen()
            if primary is None:
                return x, y
            target = primary.availableGeometry()
        clamped_x = max(target.left(), min(x, target.right() - width + 1))
        clamped_y = max(target.top(), min(y, target.bottom() - height + 1))
        return clamped_x, clamped_y

    def _save_bar_position(self) -> None:
        pos = self._bar.pos()
        self._settings_store.save_window_position(pos.x(), pos.y())

    def _capture_status_text(self, language: str | None = None) -> str:
        active_language = language or self._language
        return tr("capture_bar_in_display", active_language)

    def show_settings(self) -> None:
        if self._settings_dialog and self._settings_dialog.isVisible():
            self._settings_dialog.raise_()
            self._settings_dialog.activateWindow()
            return
        dialog = SettingsDialog(
            self._connection_settings,
            self._capture_status_text,
            self._bar,
        )
        dialog.settings_saved.connect(self._save_settings)
        dialog.finished.connect(lambda: setattr(self, "_settings_dialog", None))
        self._settings_dialog = dialog
        dialog.show()

    def _save_settings(self, update: object) -> None:
        if not isinstance(update, SettingsUpdate):
            return
        try:
            self._connection_settings = self._settings_store.save(update)
        except OSError as error:
            self._notify(tr("password_save_failed", self._language), str(error))
            return
        self._auth_prompted = False
        self._apply_language(update.language)
        self._register_hotkeys()
        try:
            set_autostart_enabled(update.autostart, application_launch_command())
        except OSError as error:
            logging.warning("autostart update failed: %s", error)
        logging.info(
            "settings saved host=%s port=%s language=%s autostart=%s",
            update.host,
            update.port,
            update.language,
            update.autostart,
        )
        self._client.connect_to_server(update.password, host=update.host, port=update.port)

    def _on_connection_changed(self, connected: bool, message: str) -> None:
        self._bar.set_connection(connected, message)
        self._refresh_tray_icon()
        if connected:
            self._auth_prompted = False
            self._status_poll.start()
            logging.info("connected to OBS")
            return
        self._status_poll.stop()
        logging.info("OBS disconnected: %s", message)
        if tr("auth_failed", self._language) in message and not self._auth_prompted:
            self._auth_prompted = True
            self._notify(tr("auth_failed", self._language), message)
            QTimer.singleShot(0, self.show_settings)

    def _poll_record_status(self) -> None:
        if self._client.is_connected:
            self._client.refresh_status()

    def _on_record_status_changed(self, status: RecordStatus) -> None:
        self._bar.set_record_status(status)
        self._refresh_tray_icon()
        if (
            self._connection_settings.auto_hide_while_recording
            and status.state is RecordingState.RECORDING
            and self._visibility.visible
        ):
            self._auto_hidden_for_recording = True
            self._hide_floating_bar()
        elif self._auto_hidden_for_recording and status.state is RecordingState.IDLE:
            self._auto_hidden_for_recording = False
            self._visibility.set_visible(True)
            self._bar.show()
            self._bar.raise_()

    def _refresh_tray_icon(self) -> None:
        status = self._client.current_status
        finished = (
            self._last_recording_output_path is not None
            and status.state is RecordingState.IDLE
        )
        self._tray.setIcon(
            build_tray_icon(
                connected=self._client.is_connected,
                recording=status.state is RecordingState.RECORDING,
                paused=status.state is RecordingState.PAUSED,
                finished=finished,
            )
        )

    def _hotkey_start_record(self) -> None:
        if self._client.current_status.state is RecordingState.IDLE and self._client.is_connected:
            self._client.start_record()

    def _hotkey_pause_resume(self) -> None:
        status = self._client.current_status
        if status.state is RecordingState.RECORDING:
            self._client.pause_record()
        elif status.state is RecordingState.PAUSED:
            self._client.resume_record()

    def toggle_floating_bar(self) -> None:
        if self._visibility.toggle():
            self._auto_hidden_for_recording = False
            self._bar.show()
            self._bar.raise_()
        else:
            self._bar.hide()

    def _hide_floating_bar(self) -> None:
        self._visibility.set_visible(False)
        self._bar.hide()

    def _set_recording_output_path(self, output_path: str) -> None:
        path = Path(output_path)
        if self._last_recording_output_path == path:
            return
        self._last_recording_output_path = path
        self._bar.set_recording_output_path(output_path)
        recent = self._settings_store.remember_recording(output_path)
        self._connection_settings = ConnectionSettings(
            host=self._connection_settings.host,
            port=self._connection_settings.port,
            password=self._connection_settings.password,
            configured=self._connection_settings.configured,
            language=self._connection_settings.language,
            hotkeys=self._connection_settings.hotkeys,
            autostart=self._connection_settings.autostart,
            auto_rename_on_stop=self._connection_settings.auto_rename_on_stop,
            auto_hide_while_recording=self._connection_settings.auto_hide_while_recording,
            recent_recordings=recent,
        )
        self._bar.set_recent_recordings(recent)
        self._refresh_tray_icon()
        if self._connection_settings.auto_rename_on_stop:
            QTimer.singleShot(400, self.rename_last_recording)

    def open_recent_recording(self, path: str) -> None:
        target = Path(path)
        if target.is_file():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(target)))
            return
        if target.parent.is_dir():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(target.parent)))
            return
        self._notify(tr("rename_video_title", self._language), tr("rename_video_missing", self._language))

    def open_last_recording_folder(self) -> None:
        source = self._last_recording_output_path
        if source is None:
            self._notify(tr("rename_video_title", self._language), tr("rename_video_unavailable", self._language))
            return
        folder = source if source.is_dir() else source.parent
        if not folder.is_dir():
            self._notify(tr("rename_video_title", self._language), tr("rename_video_missing", self._language))
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))

    def rename_last_recording(self) -> None:
        if self._rename_dialog_open:
            return
        source = self._last_recording_output_path
        if source is None:
            self._notify(tr("rename_video_title", self._language), tr("rename_video_unavailable", self._language))
            return
        if not source.is_file():
            if self._rename_retry_remaining > 0:
                self._rename_retry_remaining -= 1
                self._notify(tr("rename_video_title", self._language), tr("rename_video_busy", self._language))
                QTimer.singleShot(500, self.rename_last_recording)
                return
            # First miss: allow a few retries for file flush.
            self._rename_retry_remaining = 6
            QTimer.singleShot(500, self.rename_last_recording)
            return

        self._rename_retry_remaining = 0
        self._rename_dialog_open = True
        try:
            new_name, accepted = prompt_text(
                self._bar,
                tr("rename_video_title", self._language),
                tr("rename_video_prompt", self._language),
                source.stem,
                self._language,
            )
        finally:
            self._rename_dialog_open = False
        new_name = new_name.strip()
        if not accepted:
            return
        if not new_name or any(character in new_name for character in '\\/:*?"<>|'):
            self._notify(tr("rename_video_title", self._language), tr("rename_video_invalid", self._language))
            return
        if source.suffix and new_name.lower().endswith(source.suffix.lower()):
            new_name = new_name[: -len(source.suffix)]
        target = source.with_name(f"{new_name}{source.suffix}")
        if target == source:
            return
        if target.exists():
            self._notify(tr("rename_video_title", self._language), tr("rename_video_exists", self._language))
            return
        self._attempt_rename(source, target, retries=8)

    def _attempt_rename(self, source: Path, target: Path, retries: int) -> None:
        try:
            source.rename(target)
        except OSError as error:
            if retries > 0:
                QTimer.singleShot(
                    400,
                    lambda: self._attempt_rename(source, target, retries - 1),
                )
                return
            self._notify(
                tr("rename_video_title", self._language),
                tr("rename_video_failed", self._language, error=error),
            )
            return
        self._last_recording_output_path = target
        self._bar.set_recording_output_path(str(target))
        recent = self._settings_store.remember_recording(str(target))
        self._bar.set_recent_recordings(recent)



    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.toggle_floating_bar()

    def _notify(self, title: str, message: str) -> None:
        self._tray.showMessage(title, message, QSystemTrayIcon.MessageIcon.Warning, 5_000)

    def quit(self) -> None:
        self._save_bar_position()
        self._bar.allow_application_exit()
        self._app.quit()

    def _cleanup(self) -> None:
        self._save_bar_position()
        self._status_poll.stop()
        self._hotkey.unregister()
        self._client.disconnect_from_server()
        self._tray.hide()
        logging.info("application exit")


def run() -> int:
    configure_logging()
    mutex = acquire_single_instance()
    if mutex is None:
        # Minimal feedback without a full QApplication when possible.
        app = QApplication.instance() or QApplication(sys.argv)
        show_alert(
            None,
            tr("already_running"),
            tr("already_running_detail"),
        )
        return 1

    app = QApplication(sys.argv)
    app.setApplicationName("OBS Floating Ball")
    app.setApplicationDisplayName("OBS Floating Ball")
    app.setApplicationVersion(__version__)
    app.setFont(QFont("Microsoft YaHei UI", 10))
    # Keep native dialogs from leaking mixed language labels where possible.
    app.setStyle("Fusion")
    app.setQuitOnLastWindowClosed(False)
    # Keep mutex handle alive for process lifetime.
    app._single_instance_mutex = mutex  # type: ignore[attr-defined]
    controller = ApplicationController(app)
    controller.start()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(run())
