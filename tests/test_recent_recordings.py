from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from obs_floating_controller.config import SettingsStore
from obs_floating_controller.floating_bar import FloatingControlBar


def test_load_recent_drops_missing_files_and_persists(tmp_path: Path, monkeypatch) -> None:
    settings = QSettings(str(tmp_path / "test.ini"), QSettings.Format.IniFormat)
    store = SettingsStore.__new__(SettingsStore)
    store._settings = settings
    monkeypatch.setattr(store, "_dpapi", lambda: None)

    alive = tmp_path / "alive.mkv"
    alive.write_bytes(b"x")
    dead = tmp_path / "dead.mkv"
    import json
    settings.setValue("recordings/recent", json.dumps([str(dead), str(alive)]))
    settings.sync()

    recent = store._load_recent()
    assert recent == (str(alive),)
    # persisted prune
    assert json.loads(str(settings.value("recordings/recent"))) == [str(alive)]


def test_set_recent_recordings_filters_missing(tmp_path: Path) -> None:
    app = QApplication.instance() or QApplication([])
    assert app is not None
    alive = tmp_path / "ok.mkv"
    alive.write_bytes(b"1")
    bar = FloatingControlBar()
    bar.set_recent_recordings([str(alive), str(tmp_path / "gone.mkv")])
    assert bar._recent_recordings == [str(alive)]
