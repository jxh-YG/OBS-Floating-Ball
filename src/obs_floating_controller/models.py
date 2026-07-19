"""Recording state and elapsed-time calculation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from time import monotonic
from typing import Callable


class RecordingState(str, Enum):
    DISCONNECTED = "disconnected"
    IDLE = "idle"
    RECORDING = "recording"
    PAUSED = "paused"


@dataclass(frozen=True)
class RecordStatus:
    state: RecordingState
    elapsed_seconds: float

    @property
    def is_active(self) -> bool:
        return self.state in {RecordingState.RECORDING, RecordingState.PAUSED}

    @property
    def is_paused(self) -> bool:
        return self.state is RecordingState.PAUSED


class RecordingStateMachine:
    """Keeps a smooth local clock calibrated by OBS status payloads."""

    def __init__(self, clock: Callable[[], float] = monotonic) -> None:
        self._clock = clock
        self._state = RecordingState.DISCONNECTED
        self._base_elapsed = 0.0
        self._synced_at = clock()

    @property
    def state(self) -> RecordingState:
        return self._state

    def disconnected(self) -> RecordStatus:
        self._state = RecordingState.DISCONNECTED
        self._base_elapsed = 0.0
        self._synced_at = self._clock()
        return self.status()

    def apply_obs_status(
        self,
        *,
        output_active: bool,
        output_paused: bool,
        output_duration_ms: int | float | None = None,
    ) -> RecordStatus:
        if output_duration_ms is None:
            elapsed = self.status().elapsed_seconds
        else:
            elapsed = max(0.0, float(output_duration_ms) / 1000)
        if not output_active:
            self._state = RecordingState.IDLE
            self._base_elapsed = 0.0
        elif output_paused:
            self._state = RecordingState.PAUSED
            self._base_elapsed = elapsed
        else:
            self._state = RecordingState.RECORDING
            self._base_elapsed = elapsed
        self._synced_at = self._clock()
        return self.status()

    def status(self) -> RecordStatus:
        elapsed = self._base_elapsed
        if self._state is RecordingState.RECORDING:
            elapsed += self._clock() - self._synced_at
        return RecordStatus(self._state, max(0.0, elapsed))


def format_elapsed(seconds: float) -> str:
    total = max(0, int(seconds))
    hours, remainder = divmod(total, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"
