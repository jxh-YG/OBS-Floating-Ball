import os

import pytest

from obs_floating_controller.config import DpapiProtector


@pytest.mark.skipif(os.name != "nt", reason="DPAPI is Windows-only")
def test_dpapi_round_trip_uses_the_current_windows_user() -> None:
    protector = DpapiProtector()
    assert protector.unprotect(protector.protect("test-password")) == "test-password"


def test_window_position_round_trip(tmp_path, monkeypatch) -> None:
    from PySide6.QtCore import QSettings
    from obs_floating_controller.config import SettingsStore

    QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope, str(tmp_path))
    store = SettingsStore()
    # Force INI under tmp by constructing with organization path already set.
    store._settings = QSettings(str(tmp_path / "pos.ini"), QSettings.Format.IniFormat)
    assert store.load_window_position() is None
    store.save_window_position(120, 340)
    assert store.load_window_position() == (120, 340)
