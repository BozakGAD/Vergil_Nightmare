"""Animation metadata contracts for Vergil's sprite sheet.

The frame counts below define every player animation the sprite renderer
expects. Sprite folders should contain matching source frame counts and advance
using ``drawn_frame_count``.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType


@dataclass(frozen=True, slots=True)
class AnimationSpec:
    """Metadata for an animation that will later be backed by real sprites."""

    name: str
    source_frame_count: int
    drawn_frame_count: int
    description: str


PLAYER_ANIMATION_SPECS = MappingProxyType(
    {
        "idle": AnimationSpec("idle", 4, 4, "Idle stance."),
        "taunt": AnimationSpec("taunt", 13, 26, "Ending this animation grants boost to combo"),
        "ability": AnimationSpec("ability", 11, 11, "Future special ability animation hook."),
        "run": AnimationSpec("run", 8, 8, "Horizontal movement left/right."),
        "jump_rise": AnimationSpec("jump_rise", 1, 1, "Jump ascent sprite."),
        "jump_hang": AnimationSpec("jump_hang", 1, 1, "Short hang-time sprite."),
        "fall": AnimationSpec("fall", 1, 1, "Falling sprite."),
        "hurt": AnimationSpec("hurt", 2, 2, "Short damage reaction; enemies cannot hit during configured invulnerability."),
        "death": AnimationSpec("death", 3, 3, "Death pose remains until the final menu opens."),
        "yamato_air_lift": AnimationSpec("yamato_air_lift", 6, 6, "Air hit that lifts the enemy slightly."),
        "yamato_air_slam": AnimationSpec("yamato_air_slam", 6, 6, "Air hit that sends the enemy down."),
        "yamato_ground_slash": AnimationSpec("yamato_ground_slash", 11, 11, "Single grounded Yamato attack."),
        "yamato_ground_launcher": AnimationSpec(
            "yamato_ground_launcher",
            9,
            11,
            "Shared grounded S + attack launcher animation for full and rise branches.",
        ),
    }
)


def get_player_animation_spec(name: str) -> AnimationSpec:
    """Return animation metadata by name."""
    return PLAYER_ANIMATION_SPECS[name]
