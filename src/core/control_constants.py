"""Default control bindings for Vergil's Nightmare.

The values are stored as pygame-compatible key names, but this module does not
import pygame. Keeping the defaults import-free makes them cheap to reuse in
unit tests and in the JSON save/load layer.
"""

from __future__ import annotations

from types import MappingProxyType

CONTROL_STORAGE_PATH = "saves/controls.json"

DEFAULT_CONTROL_BINDINGS = MappingProxyType(
    {
        "move_up": "w",
        "move_left": "a",
        "move_down": "s",
        "move_right": "d",
        "jump": "left alt",
        "attack": "j",
        "switch_weapon": "q",
        "ability": "h",
        "teleport": "k",
        "taunt": "i",
        "pause": "escape",
    }
)

CONTROL_LABELS = MappingProxyType(
    {
        "move_up": "Модификатор атаки вверх",
        "move_left": "Движение влево",
        "move_down": "Модификатор атаки назад",
        "move_right": "Движение вправо",
        "jump": "Прыжок",
        "attack": "Атака",
        "switch_weapon": "Смена оружия",
        "ability": "Способность",
        "teleport": "Телепортация",
        "taunt": "Провокация",
        "pause": "Пауза",
    }
)

EDITABLE_CONTROLS = tuple(key for key in DEFAULT_CONTROL_BINDINGS if key != "pause")

LEFT_SETTINGS_COLUMN = (
    "move_up",
    "move_left",
    "move_down",
    "move_right",
    "jump",
)

RIGHT_SETTINGS_COLUMN = (
    "attack",
    "switch_weapon",
    "ability",
    "teleport",
    "taunt",
    "pause",
)
