"""Shared Apple-style dialogs for consistent UI language and chrome."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .i18n import CHINESE, tr
from . import theme


class AppleDialog(QDialog):
    """Base framed dialog sharing the app visual language."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("appleDialog")
        self.setModal(True)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
        # Stay above the always-on-top floating ball so the first click hits controls.
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.setStyleSheet(theme.dialog_stylesheet())

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        self.raise_()
        self.activateWindow()


class TextInputDialog(AppleDialog):
    """Single-line text prompt (rename, etc.)."""

    def __init__(
        self,
        title: str,
        prompt: str,
        text: str = "",
        language: str = CHINESE,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._language = language
        self.setWindowTitle(title)
        self.setMinimumWidth(360)

        root = QVBoxLayout(self)
        root.setContentsMargins(theme.SPACE_XXL, theme.SPACE_XL, theme.SPACE_XXL, theme.SPACE_XL)
        root.setSpacing(theme.SPACE_MD)

        self._title = QLabel(title, self)
        self._title.setObjectName("dialogTitle")
        root.addWidget(self._title)

        self._prompt = QLabel(prompt, self)
        self._prompt.setObjectName("dialogPrompt")
        self._prompt.setWordWrap(True)
        root.addWidget(self._prompt)

        field_wrap = QWidget(self)
        field_wrap.setObjectName("dialogFieldWrap")
        field_layout = QVBoxLayout(field_wrap)
        field_layout.setContentsMargins(theme.SPACE_MD, theme.SPACE_SM, theme.SPACE_MD, theme.SPACE_SM)
        field_layout.setSpacing(0)
        self._field = QLineEdit(field_wrap)
        self._field.setObjectName("dialogField")
        self._field.setText(text)
        self._field.selectAll()
        field_layout.addWidget(self._field)
        root.addWidget(field_wrap)

        buttons = QHBoxLayout()
        buttons.setSpacing(theme.SPACE_SM)
        buttons.addStretch(1)
        self._cancel = QPushButton(tr("cancel", language), self)
        self._cancel.setObjectName("cancelButton")
        self._cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self._cancel.clicked.connect(self.reject)
        buttons.addWidget(self._cancel)
        self._ok = QPushButton(tr("ok", language), self)
        self._ok.setObjectName("saveButton")
        self._ok.setCursor(Qt.CursorShape.PointingHandCursor)
        self._ok.setDefault(True)
        self._ok.setAutoDefault(True)
        self._ok.clicked.connect(self.accept)
        buttons.addWidget(self._ok)
        root.addLayout(buttons)

        self._size_buttons()
        # Default button already accepts on Enter; avoid double-accept wiring.

    def _size_buttons(self) -> None:
        for button in (self._ok, self._cancel):
            button.setFixedHeight(theme.SETTINGS_BUTTON_H)
            button.setMinimumWidth(96)

    def value(self) -> str:
        return self._field.text()


class AlertDialog(AppleDialog):
    """Simple informational / confirmation alert."""

    def __init__(
        self,
        title: str,
        message: str,
        language: str = CHINESE,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(340)

        root = QVBoxLayout(self)
        root.setContentsMargins(theme.SPACE_XXL, theme.SPACE_XL, theme.SPACE_XXL, theme.SPACE_XL)
        root.setSpacing(theme.SPACE_MD)

        self._title = QLabel(title, self)
        self._title.setObjectName("dialogTitle")
        root.addWidget(self._title)

        self._message = QLabel(message, self)
        self._message.setObjectName("dialogPrompt")
        self._message.setWordWrap(True)
        root.addWidget(self._message)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        self._ok = QPushButton(tr("ok", language), self)
        self._ok.setObjectName("saveButton")
        self._ok.setCursor(Qt.CursorShape.PointingHandCursor)
        self._ok.setDefault(True)
        self._ok.setFixedHeight(theme.SETTINGS_BUTTON_H)
        self._ok.setMinimumWidth(96)
        self._ok.clicked.connect(self.accept)
        buttons.addWidget(self._ok)
        root.addLayout(buttons)


def prompt_text(
    parent: QWidget | None,
    title: str,
    prompt: str,
    text: str,
    language: str,
) -> tuple[str, bool]:
    dialog = TextInputDialog(title, prompt, text=text, language=language, parent=parent)
    accepted = dialog.exec() == QDialog.DialogCode.Accepted
    return (dialog.value() if accepted else text), accepted


def show_alert(
    parent: QWidget | None,
    title: str,
    message: str,
    language: str = CHINESE,
) -> None:
    dialog = AlertDialog(title, message, language=language, parent=parent)
    dialog.exec()
