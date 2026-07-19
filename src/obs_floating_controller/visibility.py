"""Pure visibility state used by the floating control and annotation mode."""

from __future__ import annotations


class VisibilityState:
    def __init__(self, visible: bool = True) -> None:
        self.visible = visible
        self._visible_before_annotation = visible

    def toggle(self) -> bool:
        self.visible = not self.visible
        return self.visible

    def set_visible(self, visible: bool) -> bool:
        self.visible = visible
        return self.visible

    def enter_annotation(self) -> None:
        self._visible_before_annotation = self.visible
        self.visible = False

    def exit_annotation(self) -> bool:
        self.visible = self._visible_before_annotation
        return self.visible
