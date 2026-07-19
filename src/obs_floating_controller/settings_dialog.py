"""Apple Settings–style connection dialog with grouped list rows."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from .i18n import CHINESE, ENGLISH, tr
from . import theme


class SettingsDialog(QDialog):
    settings_saved = Signal(str, str)

    def __init__(
        self,
        password: str,
        language: str,
        capture_status_for: Callable[[str], str],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._language = language
        self._capture_status_for = capture_status_for
        self.setObjectName("settingsDialog")
        self.setFixedWidth(theme.SETTINGS_WIDTH)
        self.setStyleSheet(theme.settings_stylesheet())

        root = QVBoxLayout(self)
        root.setContentsMargins(theme.SPACE_XXL, theme.SPACE_XL, theme.SPACE_XXL, theme.SPACE_XL)
        root.setSpacing(theme.SPACE_MD)

        self._title = QLabel(self)
        self._title.setObjectName("settingsTitle")
        root.addWidget(self._title)

        self._intro = QLabel(self)
        self._intro.setObjectName("settingsIntro")
        self._intro.setWordWrap(True)
        root.addWidget(self._intro)

        root.addSpacing(theme.SPACE_XS)

        # Group: Connection
        self._connection_header = QLabel(self)
        self._connection_header.setObjectName("groupHeader")
        root.addWidget(self._connection_header)

        connection_group = QFrame(self)
        connection_group.setObjectName("settingsGroup")
        connection_layout = QVBoxLayout(connection_group)
        connection_layout.setContentsMargins(0, 0, 0, 0)
        connection_layout.setSpacing(0)

        self._server = QLineEdit("127.0.0.1:4455", self)
        self._server.setObjectName("serverInput")
        self._server.setReadOnly(True)
        self._server.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._server_label = QLabel(self)
        self._server_label.setObjectName("rowLabel")
        connection_layout.addWidget(self._settings_row(self._server_label, self._server))

        connection_layout.addWidget(self._row_divider())

        self._password = QLineEdit(password, self)
        self._password.setObjectName("passwordInput")
        self._password.setEchoMode(QLineEdit.EchoMode.Password)
        self._password.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._password_label = QLabel(self)
        self._password_label.setObjectName("rowLabel")
        connection_layout.addWidget(self._settings_row(self._password_label, self._password))
        root.addWidget(connection_group)

        # Group: Preferences
        self._prefs_header = QLabel(self)
        self._prefs_header.setObjectName("groupHeader")
        root.addWidget(self._prefs_header)

        prefs_group = QFrame(self)
        prefs_group.setObjectName("settingsGroup")
        prefs_layout = QVBoxLayout(prefs_group)
        prefs_layout.setContentsMargins(0, 0, 0, 0)
        prefs_layout.setSpacing(0)

        self._language_select = QComboBox(self)
        self._language_select.setObjectName("languageSelect")
        self._language_select.addItem("中文", CHINESE)
        self._language_select.addItem("English", ENGLISH)
        self._language_select.setCurrentIndex(0 if language == CHINESE else 1)
        self._language_select.currentIndexChanged.connect(self._preview_language)
        self._language_label = QLabel(self)
        self._language_label.setObjectName("rowLabel")
        prefs_layout.addWidget(self._settings_row(self._language_label, self._language_select))
        root.addWidget(prefs_group)

        # Status card
        self._capture_status = QLabel(self)
        self._capture_status.setObjectName("captureStatus")
        self._capture_status.setWordWrap(True)
        root.addWidget(self._capture_status)

        root.addStretch(1)

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
        root.addLayout(buttons)

        self.set_language(language)

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
        self._server_label.setText(tr("server", language))
        self._password_label.setText(tr("password", language))
        self._language_label.setText(tr("language", language))
        self._password.setPlaceholderText(tr("password_placeholder", language))
        self._save.setText(tr("save_connect", language))
        self._cancel.setText(tr("cancel", language))
        self._capture_status.setText(self._capture_status_for(language))
        # Refresh palette in case OS color scheme changed while open.
        self.setStyleSheet(theme.settings_stylesheet())
        self._size_action_buttons()

    def _preview_language(self) -> None:
        self.set_language(self._language_select.currentData())

    def _save_settings(self) -> None:
        self.settings_saved.emit(self._password.text(), self._language_select.currentData())
        self.accept()
