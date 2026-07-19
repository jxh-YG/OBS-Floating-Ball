"""Shared Apple Human Interface design tokens for the OBS floating controller."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication

# Typography
FONT_FAMILY = "Microsoft YaHei UI, Segoe UI, sans-serif"
FONT_FAMILY_PRIMARY = "Microsoft YaHei UI"

# System colors — light (primary)
LABEL_PRIMARY = "#1D1D1F"
LABEL_SECONDARY = "#6E6E73"
LABEL_TERTIARY = "#8E8E93"
LABEL_QUATERNARY = "#C7C7CC"

FILL_PRIMARY = "#FFFFFF"
FILL_SECONDARY = "#F2F2F7"
FILL_TERTIARY = "#E5E5EA"
FILL_QUATERNARY = "#EBEBF0"
FILL_ELEVATED = "#FFFFFF"

SEPARATOR = "#D1D1D6"
SEPARATOR_LIGHT = "#E5E5EA"
SEPARATOR_ULTRA_LIGHT = "#F2F2F7"

# Accent / semantic
BLUE = "#007AFF"
BLUE_HOVER = "#0A84FF"
BLUE_PRESSED = "#0066D6"
BLUE_SOFT = "#E8F1FF"
BLUE_SOFT_BORDER = "#C7E0FF"
BLUE_TEXT = "#0A66C2"
BLUE_RING = "#B8DBFF"
BLUE_RING_OUTER = "#D6E8FF"

GREEN = "#34C759"
ORANGE = "#FF9F0A"
ORANGE_SOFT = "#FFE8CC"
ORANGE_SOFT_HOVER = "#FFD9A8"
ORANGE_SOFT_PRESSED = "#FFCB8A"
RED = "#FF3B30"
RED_HOVER = "#FF453A"
RED_PRESSED = "#D70015"
RED_SOFT = "#FFD1CE"
GRAY = "#8E8E93"

# Dark mode counterparts (optional)
DARK_LABEL_PRIMARY = "#F5F5F7"
DARK_LABEL_SECONDARY = "#A1A1A6"
DARK_LABEL_TERTIARY = "#8E8E93"
DARK_FILL_PRIMARY = "#1C1C1E"
DARK_FILL_SECONDARY = "#000000"
DARK_FILL_TERTIARY = "#2C2C2E"
DARK_FILL_ELEVATED = "#2C2C2E"
DARK_SEPARATOR = "#38383A"
DARK_SEPARATOR_LIGHT = "#2C2C2E"
DARK_BLUE_SOFT = "#0A2848"
DARK_BLUE_SOFT_BORDER = "#1A3F66"
DARK_BLUE_TEXT = "#64B5FF"
DARK_ORANGE_SOFT = "#3D2A12"
DARK_ORANGE_SOFT_HOVER = "#4A3316"
DARK_ORANGE_SOFT_PRESSED = "#5A3F1A"
DARK_RED_SOFT = "#4A1C1A"

# Radii
RADIUS_CONTROL = 8
RADIUS_BUTTON = 10
RADIUS_CARD = 12
RADIUS_PILL = 22
RADIUS_BUBBLE = 27
RADIUS_MENU = 12
RADIUS_MENU_ITEM = 8

# Spacing
SPACE_XS = 4
SPACE_SM = 8
SPACE_MD = 12
SPACE_LG = 16
SPACE_XL = 20
SPACE_XXL = 24

# Component sizes from the supplied HTML reference, scaled to one third.
FLOAT_HEIGHT = 43
FLOAT_BUBBLE = 43
FLOAT_STRIP_HEIGHT = 30
FLOAT_STRIP_LEFT = 25
FLOAT_STRIP_WIDTH = 113
FLOAT_EXPANDED_WIDTH = 138
FLOAT_COLLAPSED_WIDTH = 43
BUTTON_HIT = 17
CONTROL_DIVIDER_WIDTH = 1
CONTROL_DIVIDER_HEIGHT = 10
STATUS_DOT_SIZE = 3
STATUS_DOT_MARGIN = 4
SETTINGS_BUTTON_W = 132
SETTINGS_BUTTON_H = 42
SETTINGS_WIDTH = 440
SETTINGS_ROW_HEIGHT = 44


@dataclass(frozen=True)
class Palette:
    """Resolved light/dark palette used by stylesheets and painters."""

    label_primary: str
    label_secondary: str
    label_tertiary: str
    fill_primary: str
    fill_secondary: str
    fill_tertiary: str
    fill_elevated: str
    separator: str
    separator_light: str
    blue: str
    blue_hover: str
    blue_pressed: str
    blue_soft: str
    blue_soft_border: str
    blue_text: str
    blue_ring: str
    blue_ring_outer: str
    orange_soft: str
    orange_soft_hover: str
    orange_soft_pressed: str
    red: str
    red_hover: str
    red_pressed: str
    red_soft: str
    gray: str
    is_dark: bool


def prefers_dark() -> bool:
    app = QGuiApplication.instance()
    if app is None:
        return False
    hints = app.styleHints()
    try:
        return hints.colorScheme() == Qt.ColorScheme.Dark
    except Exception:
        return False


def palette(dark: bool | None = None) -> Palette:
    use_dark = prefers_dark() if dark is None else dark
    if use_dark:
        return Palette(
            label_primary=DARK_LABEL_PRIMARY,
            label_secondary=DARK_LABEL_SECONDARY,
            label_tertiary=DARK_LABEL_TERTIARY,
            fill_primary=DARK_FILL_PRIMARY,
            fill_secondary=DARK_FILL_SECONDARY,
            fill_tertiary=DARK_FILL_TERTIARY,
            fill_elevated=DARK_FILL_ELEVATED,
            separator=DARK_SEPARATOR,
            separator_light=DARK_SEPARATOR_LIGHT,
            blue=BLUE_HOVER,
            blue_hover=BLUE,
            blue_pressed=BLUE_PRESSED,
            blue_soft=DARK_BLUE_SOFT,
            blue_soft_border=DARK_BLUE_SOFT_BORDER,
            blue_text=DARK_BLUE_TEXT,
            blue_ring="#3A6FA8",
            blue_ring_outer="#2A4F78",
            orange_soft=DARK_ORANGE_SOFT,
            orange_soft_hover=DARK_ORANGE_SOFT_HOVER,
            orange_soft_pressed=DARK_ORANGE_SOFT_PRESSED,
            red=RED_HOVER,
            red_hover=RED,
            red_pressed=RED_PRESSED,
            red_soft=DARK_RED_SOFT,
            gray=GRAY,
            is_dark=True,
        )
    return Palette(
        label_primary=LABEL_PRIMARY,
        label_secondary=LABEL_SECONDARY,
        label_tertiary=LABEL_TERTIARY,
        fill_primary=FILL_PRIMARY,
        fill_secondary=FILL_SECONDARY,
        fill_tertiary=FILL_TERTIARY,
        fill_elevated=FILL_ELEVATED,
        separator=SEPARATOR,
        separator_light=SEPARATOR_LIGHT,
        blue=BLUE,
        blue_hover=BLUE_HOVER,
        blue_pressed=BLUE_PRESSED,
        blue_soft=BLUE_SOFT,
        blue_soft_border=BLUE_SOFT_BORDER,
        blue_text=BLUE_TEXT,
        blue_ring=BLUE_RING,
        blue_ring_outer=BLUE_RING_OUTER,
        orange_soft=ORANGE_SOFT,
        orange_soft_hover=ORANGE_SOFT_HOVER,
        orange_soft_pressed=ORANGE_SOFT_PRESSED,
        red=RED,
        red_hover=RED_HOVER,
        red_pressed=RED_PRESSED,
        red_soft=RED_SOFT,
        gray=GRAY,
        is_dark=False,
    )


def settings_stylesheet(dark: bool | None = None) -> str:
    """Grouped-list settings dialog, Apple Settings–inspired."""
    p = palette(dark)
    return f"""
        QDialog#settingsDialog {{
            background: {p.fill_secondary};
            font-family: '{FONT_FAMILY_PRIMARY}';
            color: {p.label_primary};
        }}
        QLabel#settingsTitle {{
            color: {p.label_primary};
            font-size: 28px;
            font-weight: 700;
            letter-spacing: -0.4px;
        }}
        QLabel#settingsIntro {{
            color: {p.label_secondary};
            font-size: 13px;
        }}
        QFrame#settingsGroup {{
            background: {p.fill_primary};
            border: 1px solid {p.separator_light};
            border-radius: {RADIUS_CARD}px;
        }}
        QLabel#groupHeader {{
            color: {p.label_secondary};
            font-size: 12px;
            font-weight: 600;
            letter-spacing: 0.3px;
            padding-left: 4px;
            text-transform: uppercase;
        }}
        QLabel#rowLabel {{
            color: {p.label_primary};
            font-size: 15px;
            font-weight: 400;
        }}
        QLabel#rowCaption {{
            color: {p.label_tertiary};
            font-size: 12px;
        }}
        QFrame#rowDivider {{
            background: {p.separator_light};
            max-height: 1px;
            min-height: 1px;
            border: 0;
            margin-left: 16px;
        }}
        QFrame#settingsRow {{
            background: transparent;
            border: 0;
        }}
        QLineEdit, QComboBox {{
            min-height: 34px;
            max-height: 34px;
            padding: 0 10px;
            background: transparent;
            border: 0;
            border-radius: 0;
            color: {p.label_primary};
            font-size: 15px;
            selection-background-color: {p.blue_soft};
        }}
        QLineEdit:focus, QComboBox:focus {{
            background: transparent;
            border: 0;
        }}
        QLineEdit#serverInput {{
            color: {p.label_tertiary};
            background: transparent;
        }}
        QLineEdit#passwordInput {{
            color: {p.label_primary};
        }}
        QComboBox#languageSelect {{
            color: {p.label_secondary};
        }}
        QComboBox::drop-down {{
            border: 0;
            width: 22px;
        }}
        QComboBox::down-arrow {{
            width: 0;
            height: 0;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 5px solid {p.label_tertiary};
            margin-right: 6px;
        }}
        QComboBox QAbstractItemView {{
            background: {p.fill_primary};
            border: 1px solid {p.separator};
            border-radius: 8px;
            selection-background-color: {p.blue_soft};
            selection-color: {p.blue_text};
            outline: 0;
            padding: 4px;
        }}
        QLabel#captureStatus {{
            color: {p.blue_text};
            background: {p.blue_soft};
            border: 1px solid {p.blue_soft_border};
            border-radius: 10px;
            padding: 12px 14px;
            font-size: 12px;
        }}
        QPushButton#saveButton {{
            min-width: {SETTINGS_BUTTON_W}px;
            max-width: {SETTINGS_BUTTON_W}px;
            min-height: {SETTINGS_BUTTON_H}px;
            max-height: {SETTINGS_BUTTON_H}px;
            padding: 0 12px;
            background: {p.blue};
            color: #FFFFFF;
            border: 0;
            border-radius: {RADIUS_BUTTON}px;
            font-size: 15px;
            font-weight: 600;
        }}
        QPushButton#saveButton:hover {{
            background: {p.blue_hover};
        }}
        QPushButton#saveButton:pressed {{
            background: {p.blue_pressed};
        }}
        QPushButton#cancelButton {{
            min-width: {SETTINGS_BUTTON_W}px;
            max-width: {SETTINGS_BUTTON_W}px;
            min-height: {SETTINGS_BUTTON_H}px;
            max-height: {SETTINGS_BUTTON_H}px;
            padding: 0 12px;
            background: {p.fill_primary};
            color: {p.label_primary};
            border: 1px solid #D1D1D6;
            border-radius: {RADIUS_BUTTON}px;
            font-size: 15px;
            font-weight: 500;
        }}
        QPushButton#cancelButton:hover {{
            background: {p.fill_secondary};
            border-color: {p.separator};
        }}
        QPushButton#cancelButton:pressed {{
            background: {p.fill_tertiary};
            border-color: {p.separator};
        }}
    """.strip()


def floating_strip_stylesheet(dark: bool | None = None) -> str:
    """Control strip: soft elevated pill + clear media-state feedback."""
    p = palette(dark)
    return f"""
        #controlStrip {{
            background: {p.fill_primary};
            border: 1px solid {p.separator_light};
            border-radius: {RADIUS_PILL}px;
        }}
        QToolButton {{
            border: 0;
            border-radius: 8px;
            background: transparent;
            padding: 0;
        }}
        QToolButton:hover {{
            background: {p.fill_secondary};
        }}
        QToolButton:pressed {{
            background: {p.fill_tertiary};
        }}
        QToolButton:disabled {{
            background: transparent;
        }}
        QToolButton#primaryButton[recording="true"] {{
            background: {p.orange_soft};
        }}
        QToolButton#primaryButton[recording="true"]:hover {{
            background: {p.orange_soft_hover};
        }}
        QToolButton#primaryButton[recording="true"]:pressed {{
            background: {p.orange_soft_pressed};
        }}
        QToolButton#primaryButton[paused="true"] {{
            background: {p.blue_soft};
        }}
        QToolButton#primaryButton[paused="true"]:hover {{
            background: {p.blue_soft_border};
        }}
        QToolButton#primaryButton[paused="true"]:pressed {{
            background: {p.blue_soft};
        }}
        QToolButton#stopButton {{
            background: {p.red};
            border-radius: 8px;
        }}
        QToolButton#stopButton:hover {{
            background: {p.red_hover};
        }}
        QToolButton#stopButton:pressed {{
            background: {p.red_pressed};
        }}
        QToolButton#stopButton:disabled {{
            background: {p.red_soft};
        }}
        QToolButton#secondaryButton[active="true"] {{
            background: {p.blue_soft};
        }}
        QToolButton#secondaryButton[active="true"]:hover {{
            background: {p.blue_soft_border};
        }}
    """.strip()


def floating_menu_stylesheet(dark: bool | None = None) -> str:
    p = palette(dark)
    return f"""
        QMenu#floatingContextMenu {{
            background: {p.fill_primary};
            border: 1px solid {p.separator};
            border-radius: {RADIUS_MENU}px;
            padding: 6px;
        }}
        QMenu#floatingContextMenu::item {{
            padding: 8px 28px 8px 12px;
            border-radius: {RADIUS_MENU_ITEM}px;
            color: {p.label_primary};
            font-size: 13px;
        }}
        QMenu#floatingContextMenu::item:selected {{
            background: {p.blue_soft};
            color: {p.blue_text};
        }}
        QMenu#floatingContextMenu::separator {{
            height: 1px;
            background: {p.separator_light};
            margin: 4px 8px;
        }}
    """.strip()
