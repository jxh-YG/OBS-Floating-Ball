import pytest

from PySide6.QtCore import QSize
from PySide6.QtWidgets import QApplication, QDialog

from obs_floating_controller.i18n import CHINESE
from obs_floating_controller.settings_dialog import SettingsDialog


@pytest.fixture(scope="module")
def qt_app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_cancel_button_matches_primary_button_size_and_rejects(qt_app: QApplication) -> None:
    dialog = SettingsDialog("", CHINESE, lambda _language: "")

    assert dialog._save.size() == QSize(132, 42)
    assert dialog._cancel.size() == dialog._save.size()
    assert "border: 1px solid #D1D1D6" in dialog.styleSheet()
    assert "QPushButton#cancelButton:pressed" in dialog.styleSheet()

    dialog._cancel.click()
    assert dialog.result() == QDialog.DialogCode.Rejected
