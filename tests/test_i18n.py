from obs_floating_controller.i18n import CHINESE, ENGLISH, normalize_language, tr


def test_chinese_and_english_catalogs_provide_distinct_interface_text() -> None:
    assert tr("start_recording", CHINESE) == "开始录制"
    assert tr("start_recording", ENGLISH) == "Start recording"
    assert tr("capture_unavailable", ENGLISH, reason="test") == "Annotation-tool exclusion unavailable: test"
    assert tr("floating_bar_capture_unavailable", ENGLISH, reason="test") == (
        "Floating control bar exclusion unavailable: test"
    )
    assert tr("request_failed", ENGLISH, request="StartRecord", comment="busy", code=500) == (
        "StartRecord failed: busy (code 500)"
    )


def test_unknown_language_defaults_to_chinese() -> None:
    assert normalize_language("fr_FR") == CHINESE
