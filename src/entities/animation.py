"""Animation metadata placeholders for Vergil's sprite sheet.

The current prototype renders colored rectangles, but the frame counts below
reserve every animation the final sprite renderer will need. To add real art
later, slice the sprite sheet into per-animation frame lists with matching
``source_frame_count`` values, then advance them using ``drawn_frame_count``.
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
        "taunt": AnimationSpec("taunt", 13, 26, "Taunt plays each source frame twice."),
        "run": AnimationSpec("run", 8, 8, "Horizontal movement left/right."),
        "jump_rise": AnimationSpec("jump_rise", 1, 1, "Jump ascent sprite."),
        "jump_hang": AnimationSpec("jump_hang", 1, 1, "Short hang-time sprite."),
        "fall": AnimationSpec("fall", 1, 1, "Falling sprite."),
        "hurt": AnimationSpec("hurt", 2, 2, "Hurt reaction."),
        "death": AnimationSpec("death", 2, 2, "Death pose remains on the final frame."),
        "yamato_air_lift": AnimationSpec("yamato_air_lift", 6, 6, "Air hit that lifts the enemy slightly."),
        "yamato_air_slam": AnimationSpec("yamato_air_slam", 6, 6, "Air hit that sends the enemy down."),
        "yamato_ground_slash": AnimationSpec("yamato_ground_slash", 11, 11, "Single grounded Yamato attack."),
        "yamato_ground_launcher_full": AnimationSpec(
            "yamato_ground_launcher_full",
            11,
            11,
            "Grounded S + attack launcher when attack is held.",
        ),
        "yamato_ground_launcher_rise": AnimationSpec(
            "yamato_ground_launcher_rise",
            11,
            8,
            "Grounded S + attack launcher branch that carries Vergil upward after frame 8.",
        ),
    }
)


def get_player_animation_spec(name: str) -> AnimationSpec:
    """Return animation metadata by name."""
    return PLAYER_ANIMATION_SPECS[name]
