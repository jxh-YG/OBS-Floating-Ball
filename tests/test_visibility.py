from obs_floating_controller.visibility import VisibilityState


def test_hotkey_toggle_switches_visibility() -> None:
    state = VisibilityState(visible=True)
    assert state.toggle() is False
    assert state.toggle() is True


def test_set_visible_updates_state() -> None:
    state = VisibilityState(visible=True)
    assert state.set_visible(False) is False
    assert state.visible is False
    assert state.set_visible(True) is True
