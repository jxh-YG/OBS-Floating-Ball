"""Application composition and process entry point."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QAbstractNativeEventFilter, QObject, Qt, QTimer
from PySide6.QtGui import QAction, QCursor, QFont, QGuiApplication
from PySide6.QtWidgets import QApplication, QInputDialog, QMenu, QStyle, QSystemTrayIcon

from .annotation import AnnotationCanvas, AnnotationToolPanel
from .config import ConnectionSettings, SettingsStore
from .floating_bar import FloatingControlBar
from .i18n import normalize_language, tr
from .obs_websocket import ObsWebSocketClient
from .platform_windows import CaptureExclusionResult, GlobalHotkey, exclude_from_capture
from .settings_dialog import SettingsDialog
from .visibility import VisibilityState


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
        self._annotation_capture_result: CaptureExclusionResult | None = None
        self._visibility = VisibilityState()
        self._client = ObsWebSocketClient(self)
        self._bar = FloatingControlBar()
        self._bar.set_status_provider(lambda: self._client.current_status)
        self._last_recording_output_path: Path | None = None
        self._canvas = AnnotationCanvas()
        self._annotation_panel = AnnotationToolPanel(self._canvas)
        self._hotkey = GlobalHotkey()
        self._native_filter = NativeEventFilter(self._hotkey)
        self._app.installNativeEventFilter(self._native_filter)
        self._settings_dialog: SettingsDialog | None = None
        self._build_tray()
        self._wire_events()
        self._apply_language(self._language)

    def _build_tray(self) -> None:
        icon = self._app.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay)
        self._tray = QSystemTrayIcon(icon, self)
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
        self._client.connection_changed.connect(self._bar.set_connection)
        self._client.record_status_changed.connect(self._bar.set_record_status)
        self._client.recording_output_ready.connect(self._set_recording_output_path)
        self._client.request_failed.connect(lambda message: self._notify(tr("obs_action_failed", self._language), message))
        self._bar.start_requested.connect(self._client.start_record)
        self._bar.pause_requested.connect(self._client.pause_record)
        self._bar.resume_requested.connect(self._client.resume_record)
        self._bar.stop_requested.connect(self._client.stop_record)
        self._bar.annotation_requested.connect(self.enter_annotation)
        self._bar.rename_requested.connect(self.rename_last_recording)
        self._bar.close_requested.connect(self._hide_floating_bar)
        self._bar.hide_requested.connect(self._hide_floating_bar)
        self._annotation_panel.capture_exclusion_checked.connect(self._on_capture_exclusion_checked)
        self._annotation_panel.exit_requested.connect(self._canvas.exit)
        self._canvas.exited.connect(self.exit_annotation)
        self._hotkey.activated.connect(self.toggle_floating_bar)
        self._hotkey.registration_failed.connect(
            lambda message: self._notify(tr("shortcut_unavailable", self._language), message)
        )
        self._app.aboutToQuit.connect(self._cleanup)

    def _apply_language(self, language: str) -> None:
        self._language = normalize_language(language)
        self._app.setApplicationDisplayName(tr("app_name", self._language))
        self._client.set_language(self._language)
        self._bar.set_language(self._language)
        self._canvas.set_language(self._language)
        self._annotation_panel.set_language(self._language)
        self._toggle_action.setText(tr("show_hide", self._language))
        self._settings_action.setText(tr("connection_settings", self._language))
        self._quit_action.setText(tr("quit", self._language))
        self._tray.setToolTip(tr("app_name", self._language))
        if not self._client.is_connected:
            self._bar.set_connection(False, tr("not_connected", self._language))
        if self._settings_dialog:
            self._settings_dialog.set_language(self._language)

    def start(self) -> None:
        self._position_floating_bar()
        self._bar.show()
        # The top-level HWND is ready after the first turn of the event loop.
        # Applying affinity before then can make OBS show a black placeholder.
        QTimer.singleShot(0, self._verify_floating_bar_capture_exclusion)
        self._hotkey.register()
        if self._connection_settings.configured:
            self._client.connect_to_server(self._connection_settings.password)
        else:
            QTimer.singleShot(0, self.show_settings)

    def _verify_floating_bar_capture_exclusion(self) -> None:
        self._floating_bar_capture_result = exclude_from_capture(self._bar)
        if not self._floating_bar_capture_result.available:
            self._notify(
                tr("floating_bar_capture_unavailable_title", self._language),
                self._floating_bar_capture_result.message,
            )
        if self._settings_dialog:
            self._settings_dialog.set_language(self._language)

    def _position_floating_bar(self) -> None:
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            return
        geometry = screen.availableGeometry()
        self._bar.move(geometry.right() - self._bar.width() - 32, geometry.top() + 32)

    def _capture_status_text(self, language: str | None = None) -> str:
        active_language = language or self._language
        if self._floating_bar_capture_result is None:
            return tr("capture_checking", active_language)
        if not self._floating_bar_capture_result.available:
            return tr(
                "floating_bar_capture_unavailable",
                active_language,
                reason=self._floating_bar_capture_result.message,
            )
        if self._annotation_capture_result is None:
            return tr("capture_checking", active_language)
        if self._annotation_capture_result.available:
            return tr("capture_ready", active_language)
        return tr("capture_unavailable", active_language, reason=self._annotation_capture_result.message)

    def show_settings(self) -> None:
        if self._settings_dialog and self._settings_dialog.isVisible():
            self._settings_dialog.raise_()
            self._settings_dialog.activateWindow()
            return
        dialog = SettingsDialog(
            self._connection_settings.password,
            self._language,
            self._capture_status_text,
            self._bar,
        )
        dialog.settings_saved.connect(self._save_settings)
        dialog.finished.connect(lambda: setattr(self, "_settings_dialog", None))
        self._settings_dialog = dialog
        dialog.show()

    def _save_settings(self, password: str, language: str) -> None:
        try:
            self._connection_settings = self._settings_store.save_password(password, language)
        except OSError as error:
            self._notify(tr("password_save_failed", self._language), str(error))
            return
        self._apply_language(language)
        self._client.connect_to_server(password)

    def toggle_floating_bar(self) -> None:
        if self._canvas.isVisible():
            return
        if self._visibility.toggle():
            self._bar.show()
            self._bar.raise_()
        else:
            self._bar.hide()

    def _hide_floating_bar(self) -> None:
        self._visibility.set_visible(False)
        self._bar.hide()

    def _set_recording_output_path(self, output_path: str) -> None:
        self._last_recording_output_path = Path(output_path)
        self._bar.set_recording_output_path(output_path)

    def rename_last_recording(self) -> None:
        source = self._last_recording_output_path
        if source is None:
            self._notify(tr("rename_video_title", self._language), tr("rename_video_unavailable", self._language))
            return
        if not source.is_file():
            self._notify(tr("rename_video_title", self._language), tr("rename_video_missing", self._language))
            return

        new_name, accepted = QInputDialog.getText(
            self._bar,
            tr("rename_video_title", self._language),
            tr("rename_video_prompt", self._language),
            text=source.stem,
        )
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
        try:
            source.rename(target)
        except OSError as error:
            self._notify(tr("rename_video_title", self._language), tr("rename_video_failed", self._language, error=error))
            return
        self._last_recording_output_path = target
        self._bar.set_recording_output_path(str(target))

    def enter_annotation(self) -> None:
        screen = QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen()
        if screen is None:
            self._notify(tr("annotation_unavailable", self._language), tr("no_screen", self._language))
            return
        self._visibility.enter_annotation()
        self._bar.hide()
        self._canvas.enter(screen.geometry())
        self._annotation_panel.show_for_screen(screen.geometry())

    def exit_annotation(self) -> None:
        self._annotation_panel.hide()
        if self._visibility.exit_annotation():
            self._bar.show()
            self._bar.raise_()

    def _on_capture_exclusion_checked(self, result: CaptureExclusionResult) -> None:
        self._annotation_capture_result = result
        if not result.available:
            self._notify(tr("capture_unavailable_title", self._language), result.message)
        if self._settings_dialog:
            self._settings_dialog.set_language(self._language)

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.toggle_floating_bar()

    def _notify(self, title: str, message: str) -> None:
        self._tray.showMessage(title, message, QSystemTrayIcon.MessageIcon.Warning, 5_000)

    def quit(self) -> None:
        self._bar.allow_application_exit()
        self._app.quit()

    def _cleanup(self) -> None:
        self._hotkey.unregister()
        self._client.disconnect_from_server()
        self._annotation_panel.hide()
        self._canvas.hide()
        self._tray.hide()


def run() -> int:
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)
    app = QApplication(sys.argv)
    app.setApplicationName("OBS Floating Ball")
    app.setApplicationDisplayName("OBS Floating Ball")
    app.setFont(QFont("Microsoft YaHei UI", 10))
    app.setQuitOnLastWindowClosed(False)
    controller = ApplicationController(app)
    controller.start()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(run())
