"""Apple Settings–style connection dialog with grouped list rows."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QPainterPath, QRegion
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QKeySequenceEdit,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from .config import ConnectionSettings, HotkeyBundle, SettingsUpdate
from .i18n import CHINESE, ENGLISH, tr
from .platform_windows import (
    HotkeySpec,
    default_hotkey_bundle,
    hotkey_to_key_sequence,
    key_sequence_to_hotkey,
)
from . import theme


class ClippedGroupFrame(QFrame):
    """Grouped list container with true outer rounded corners."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("settingsGroup")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

    def resizeEvent(self, event: object) -> None:
        super().resizeEvent(event)
        radius = float(theme.RADIUS_CARD)
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), radius, radius)
        self.setMask(QRegion(path.toFillPolygon().toPolygon()))


class SettingsDialog(QDialog):
    settings_saved = Signal(object)

    def __init__(
        self,
        settings: ConnectionSettings,
        capture_status_for: Callable[[str], str],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._language = settings.language
        self._capture_status_for = capture_status_for
        self.setObjectName("settingsDialog")
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
        self.setFixedWidth(theme.SETTINGS_WIDTH)
        self.setMinimumHeight(560)
        self.setStyleSheet(theme.settings_stylesheet())

        outer = QVBoxLayout(self)
        outer.setContentsMargins(theme.SPACE_XL, theme.SPACE_LG, theme.SPACE_XL, theme.SPACE_LG)
        outer.setSpacing(theme.SPACE_MD)

        self._title = QLabel(self)
        self._title.setObjectName("settingsTitle")
        outer.addWidget(self._title)

        self._intro = QLabel(self)
        self._intro.setObjectName("settingsIntro")
        self._intro.setWordWrap(True)
        outer.addWidget(self._intro)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        body = QWidget(scroll)
        root = QVBoxLayout(body)
        root.setContentsMargins(0, 0, 4, 0)
        root.setSpacing(theme.SPACE_MD)

        self._connection_header = QLabel(body)
        self._connection_header.setObjectName("groupHeader")
        root.addWidget(self._connection_header)

        connection_group = ClippedGroupFrame(body)
        connection_layout = QVBoxLayout(connection_group)
        connection_layout.setContentsMargins(0, 0, 0, 0)
        connection_layout.setSpacing(0)

        self._host = QLineEdit(body)
        self._host.setText(settings.host)
        self._host_label = QLabel(body)
        self._host_label.setObjectName("rowLabel")
        connection_layout.addWidget(self._settings_row(self._host_label, self._host))
        connection_layout.addWidget(self._row_divider())

        self._port = QSpinBox(body)
        self._port.setRange(1, 65535)
        self._port.setValue(settings.port)
        self._port_label = QLabel(body)
        self._port_label.setObjectName("rowLabel")
        connection_layout.addWidget(self._settings_row(self._port_label, self._port))
        connection_layout.addWidget(self._row_divider())

        self._password = QLineEdit(body)
        self._password.setObjectName("passwordField")
        self._password.setEchoMode(QLineEdit.EchoMode.Password)
        self._password.setText(settings.password)
        self._password_label = QLabel(body)
        self._password_label.setObjectName("rowLabel")
        connection_layout.addWidget(self._settings_row(self._password_label, self._password))
        root.addWidget(connection_group)

        self._prefs_header = QLabel(body)
        self._prefs_header.setObjectName("groupHeader")
        root.addWidget(self._prefs_header)

        prefs_group = ClippedGroupFrame(body)
        prefs_layout = QVBoxLayout(prefs_group)
        prefs_layout.setContentsMargins(0, 0, 0, 0)
        prefs_layout.setSpacing(0)

        self._language_select = QComboBox(body)
        self._language_select.addItem("中文", CHINESE)
        self._language_select.addItem("English", ENGLISH)
        self._language_select.setCurrentIndex(0 if settings.language == CHINESE else 1)
        self._language_select.currentIndexChanged.connect(self._preview_language)
        self._language_label = QLabel(body)
        self._language_label.setObjectName("rowLabel")
        prefs_layout.addWidget(self._settings_row(self._language_label, self._language_select))
        prefs_layout.addWidget(self._row_divider())

        self._autostart = QCheckBox(body)
        self._autostart.setChecked(settings.autostart)
        self._autostart_label = QLabel(body)
        self._autostart_label.setObjectName("rowLabel")
        prefs_layout.addWidget(self._settings_row(self._autostart_label, self._autostart))
        prefs_layout.addWidget(self._row_divider())

        self._auto_rename = QCheckBox(body)
        self._auto_rename.setChecked(settings.auto_rename_on_stop)
        self._auto_rename_label = QLabel(body)
        self._auto_rename_label.setObjectName("rowLabel")
        prefs_layout.addWidget(self._settings_row(self._auto_rename_label, self._auto_rename))
        prefs_layout.addWidget(self._row_divider())

        self._auto_hide = QCheckBox(body)
        self._auto_hide.setChecked(settings.auto_hide_while_recording)
        self._auto_hide_label = QLabel(body)
        self._auto_hide_label.setObjectName("rowLabel")
        prefs_layout.addWidget(self._settings_row(self._auto_hide_label, self._auto_hide))
        root.addWidget(prefs_group)

        self._hotkeys_header = QLabel(body)
        self._hotkeys_header.setObjectName("groupHeader")
        root.addWidget(self._hotkeys_header)

        hotkeys_group = ClippedGroupFrame(body)
        hotkeys_layout = QVBoxLayout(hotkeys_group)
        hotkeys_layout.setContentsMargins(0, 0, 0, 0)
        hotkeys_layout.setSpacing(0)

        self._hotkey_toggle = self._hotkey_edit(settings.hotkeys.toggle)
        self._hotkey_start = self._hotkey_edit(settings.hotkeys.start)
        self._hotkey_pause = self._hotkey_edit(settings.hotkeys.pause)
        self._hotkey_stop = self._hotkey_edit(settings.hotkeys.stop)
        self._hotkey_toggle_label = QLabel(body)
        self._hotkey_start_label = QLabel(body)
        self._hotkey_pause_label = QLabel(body)
        self._hotkey_stop_label = QLabel(body)
        for label in (
            self._hotkey_toggle_label,
            self._hotkey_start_label,
            self._hotkey_pause_label,
            self._hotkey_stop_label,
        ):
            label.setObjectName("rowLabel")
        hotkeys_layout.addWidget(self._settings_row(self._hotkey_toggle_label, self._hotkey_toggle))
        hotkeys_layout.addWidget(self._row_divider())
        hotkeys_layout.addWidget(self._settings_row(self._hotkey_start_label, self._hotkey_start))
        hotkeys_layout.addWidget(self._row_divider())
        hotkeys_layout.addWidget(self._settings_row(self._hotkey_pause_label, self._hotkey_pause))
        hotkeys_layout.addWidget(self._row_divider())
        hotkeys_layout.addWidget(self._settings_row(self._hotkey_stop_label, self._hotkey_stop))
        hotkeys_layout.addWidget(self._row_divider())
        self._restore_hotkeys = QPushButton(body)
        self._restore_hotkeys.clicked.connect(self._restore_default_hotkeys)
        hotkeys_layout.addWidget(self._restore_hotkeys)
        root.addWidget(hotkeys_group)

        self._capture_status = QLabel(body)
        self._capture_status.setObjectName("captureStatus")
        self._capture_status.setWordWrap(True)
        root.addWidget(self._capture_status)
        root.addStretch(1)
        scroll.setWidget(body)
        outer.addWidget(scroll, 1)

        buttons = QHBoxLayout()
        buttons.setSpacing(theme.SPACE_SM)
        buttons.addStretch()
        self._save = QPushButton(self)
        self._save.setObjectName("saveButton")
        self._save.setFixedSize(theme.SETTINGS_BUTTON_W, theme.SETTINGS_BUTTON_H)
        self._save.setCursor(Qt.CursorShape.PointingHandCursor)
        buttons.addWidget(self._save)
        self._cancel = QPushButton(self)
        self._cancel.setObjectName("cancelButton")
        self._cancel.setFixedSize(theme.SETTINGS_BUTTON_W, theme.SETTINGS_BUTTON_H)
        self._cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        buttons.addWidget(self._cancel)
        self._cancel.clicked.connect(self.reject)
        self._save.clicked.connect(self._save_settings)
        outer.addLayout(buttons)

        self.set_language(settings.language)

    def _hotkey_edit(self, spec: HotkeySpec) -> QKeySequenceEdit:
        edit = QKeySequenceEdit(self)
        edit.setKeySequence(hotkey_to_key_sequence(spec))
        edit.setClearButtonEnabled(True)
        edit.setMaximumSequenceLength(1)
        return edit

    def _settings_row(self, label: QLabel, control: QWidget) -> QFrame:
        row = QFrame(self)
        row.setObjectName("settingsRow")
        row.setMinimumHeight(theme.SETTINGS_ROW_HEIGHT)
        layout = QHBoxLayout(row)
        layout.setContentsMargins(theme.SPACE_LG, theme.SPACE_SM, theme.SPACE_MD, theme.SPACE_SM)
        layout.setSpacing(theme.SPACE_MD)
        label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        layout.addWidget(label, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addStretch(1)
        control.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        control.setMinimumWidth(180)
        layout.addWidget(control, 0, Qt.AlignmentFlag.AlignVCenter)
        return row

    def _row_divider(self) -> QFrame:
        divider = QFrame(self)
        divider.setObjectName("rowDivider")
        divider.setFixedHeight(1)
        return divider

    def _size_action_buttons(self) -> None:
        for button in (self._save, self._cancel):
            button.setFixedSize(theme.SETTINGS_BUTTON_W, theme.SETTINGS_BUTTON_H)
            button.setMinimumSize(theme.SETTINGS_BUTTON_W, theme.SETTINGS_BUTTON_H)
            button.setMaximumSize(theme.SETTINGS_BUTTON_W, theme.SETTINGS_BUTTON_H)
            button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

    def set_language(self, language: str) -> None:
        self._language = language
        self.setWindowTitle(tr("settings_title", language))
        self._title.setText(tr("settings_heading", language))
        self._intro.setText(tr("settings_intro", language))
        self._connection_header.setText(tr("group_connection", language))
        self._prefs_header.setText(tr("group_preferences", language))
        self._hotkeys_header.setText(tr("group_hotkeys", language))
        self._host_label.setText(tr("host", language))
        self._port_label.setText(tr("port", language))
        self._password_label.setText(tr("password", language))
        self._language_label.setText(tr("language", language))
        self._hotkey_toggle_label.setText(tr("hotkey", language))
        self._hotkey_start_label.setText(tr("hotkey_start", language))
        self._hotkey_pause_label.setText(tr("hotkey_pause", language))
        self._hotkey_stop_label.setText(tr("hotkey_stop", language))
        self._autostart_label.setText(tr("autostart", language))
        self._autostart.setText(tr("autostart_enable", language))
        self._auto_rename_label.setText(tr("auto_rename", language))
        self._auto_rename.setText(tr("auto_rename_enable", language))
        self._auto_hide_label.setText(tr("auto_hide_recording", language))
        self._auto_hide.setText(tr("auto_hide_recording_enable", language))
        self._password.setPlaceholderText(tr("password_placeholder", language))
        self._restore_hotkeys.setText(tr("hotkey_restore", language))
        for edit in (self._hotkey_toggle, self._hotkey_start, self._hotkey_pause, self._hotkey_stop):
            edit.setToolTip(tr("hotkey_hint", language))
        self._save.setText(tr("save_connect", language))
        self._cancel.setText(tr("cancel", language))
        self._capture_status.setText(self._capture_status_for(language))
        self.setStyleSheet(theme.settings_stylesheet())
        self._size_action_buttons()

    def _preview_language(self) -> None:
        self.set_language(self._language_select.currentData())

    def _restore_default_hotkeys(self) -> None:
        defaults = default_hotkey_bundle()
        self._hotkey_toggle.setKeySequence(hotkey_to_key_sequence(defaults.toggle))
        self._hotkey_start.setKeySequence(hotkey_to_key_sequence(defaults.start))
        self._hotkey_pause.setKeySequence(hotkey_to_key_sequence(defaults.pause))
        self._hotkey_stop.setKeySequence(hotkey_to_key_sequence(defaults.stop))

    def _resolved_hotkey(self, edit: QKeySequenceEdit, fallback: HotkeySpec) -> HotkeySpec:
        parsed = key_sequence_to_hotkey(edit.keySequence())
        return parsed if parsed is not None else fallback

    def _save_settings(self) -> None:
        defaults = default_hotkey_bundle()
        hotkeys = HotkeyBundle(
            toggle=self._resolved_hotkey(self._hotkey_toggle, defaults.toggle),
            start=self._resolved_hotkey(self._hotkey_start, defaults.start),
            pause=self._resolved_hotkey(self._hotkey_pause, defaults.pause),
            stop=self._resolved_hotkey(self._hotkey_stop, defaults.stop),
        )
        self.settings_saved.emit(
            SettingsUpdate(
                host=self._host.text().strip() or "127.0.0.1",
                port=int(self._port.value()),
                password=self._password.text(),
                language=self._language_select.currentData(),
                hotkeys=hotkeys,
                autostart=self._autostart.isChecked(),
                auto_rename_on_stop=self._auto_rename.isChecked(),
                auto_hide_while_recording=self._auto_hide.isChecked(),
            )
        )
        self.accept()
