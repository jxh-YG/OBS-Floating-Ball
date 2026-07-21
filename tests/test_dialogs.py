from PySide6.QtWidgets import QApplication

from obs_floating_controller import theme
from obs_floating_controller.dialogs import TextInputDialog


def test_text_input_dialog_is_compact() -> None:
    app = QApplication.instance() or QApplication([])
    assert app is not None
    dialog = TextInputDialog("Rename", "New name", text="clip", language="en_US")
    assert dialog.width() == 300
    assert dialog._ok.height() == theme.COMPACT_BUTTON_H
    assert dialog._cancel.height() == theme.COMPACT_BUTTON_H
    assert dialog._prompt.text() == "New name"
    assert dialog.findChild(type(dialog._prompt), "dialogTitle") is None
