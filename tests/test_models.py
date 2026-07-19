from obs_floating_controller.models import RecordingState, RecordingStateMachine, format_elapsed


class Clock:
    def __init__(self) -> None:
        self.value = 100.0

    def __call__(self) -> float:
        return self.value


def test_recording_clock_advances_only_while_obs_reports_recording() -> None:
    clock = Clock()
    machine = RecordingStateMachine(clock)
    status = machine.apply_obs_status(output_active=True, output_paused=False, output_duration_ms=4_500)
    assert status.state is RecordingState.RECORDING
    assert status.elapsed_seconds == 4.5
    clock.value += 2.25
    assert machine.status().elapsed_seconds == 6.75

    machine.apply_obs_status(output_active=True, output_paused=True, output_duration_ms=6_750)
    clock.value += 9
    assert machine.status().state is RecordingState.PAUSED
    assert machine.status().elapsed_seconds == 6.75


def test_idle_and_disconnected_reset_the_elapsed_clock() -> None:
    machine = RecordingStateMachine(Clock())
    assert machine.apply_obs_status(output_active=False, output_paused=False).state is RecordingState.IDLE
    assert machine.status().elapsed_seconds == 0


def test_event_without_duration_preserves_the_calibrated_clock() -> None:
    clock = Clock()
    machine = RecordingStateMachine(clock)
    machine.apply_obs_status(output_active=True, output_paused=False, output_duration_ms=5_000)
    clock.value += 2
    paused = machine.apply_obs_status(output_active=True, output_paused=True)
    assert paused.elapsed_seconds == 7
    clock.value += 5
    assert machine.status().elapsed_seconds == 7
    assert machine.disconnected().state is RecordingState.DISCONNECTED
    assert machine.status().elapsed_seconds == 0


def test_elapsed_formatting() -> None:
    assert format_elapsed(65.9) == "01:05"
    assert format_elapsed(3_661) == "01:01:01"
