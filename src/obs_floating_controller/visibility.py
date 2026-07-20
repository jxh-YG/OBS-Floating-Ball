"""Pure visibility state used by the floating control bar."""

from __future__ import annotations


class VisibilityState:
    def __init__(self, visible: bool = True) -> None:
        self.visible = visible

    def toggle(self) -> bool:
        self.visible = not self.visible
        return self.visible

    def set_visible(self, visible: bool) -> bool:
        self.visible = visible
        return self.visible
