from obs_floating_controller.visibility import VisibilityState


def test_hotkey_toggle_switches_visibility() -> None:
    visibility = VisibilityState()
    assert visibility.toggle() is False
    assert visibility.toggle() is True


def test_annotation_restores_the_visibility_that_existed_before_it_started() -> None:
    visible = VisibilityState(True)
    visible.enter_annotation()
    assert visible.visible is False
    assert visible.exit_annotation() is True

    hidden = VisibilityState(False)
    hidden.enter_annotation()
    assert hidden.exit_annotation() is False
