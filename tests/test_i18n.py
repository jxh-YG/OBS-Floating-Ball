from obs_floating_controller.i18n import CHINESE, ENGLISH, normalize_language, tr


def test_chinese_and_english_catalogs_provide_distinct_interface_text() -> None:
    assert tr("start_recording", CHINESE) == "开始录制"
    assert tr("start_recording", ENGLISH) == "Start recording"
    assert tr("recent_recordings", ENGLISH) == "Recent recordings"
    assert tr("request_failed", ENGLISH, request="StartRecord", comment="busy", code=500) == (
        "StartRecord failed: busy (code 500)"
    )


def test_unknown_language_defaults_to_chinese() -> None:
    assert normalize_language("fr_FR") == CHINESE


def test_missing_translation_key_returns_key() -> None:
    assert tr("does_not_exist_key") == "does_not_exist_key"


def test_capture_copy_mentions_display_capture_tradeoff() -> None:
    assert "display capture" in tr("capture_bar_excluded", ENGLISH).lower()
    assert "display capture" in tr("capture_bar_in_display", ENGLISH).lower()
    assert "显示器采集" in tr("capture_bar_excluded", CHINESE)
