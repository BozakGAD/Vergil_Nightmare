"""Configurable attack profiles loaded from JSON."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class AttackProfile:
    """Data needed by the prototype combat loop for one attack."""

    FRAMES_PER_SECOND = 60

    id: str
    animation: str
    duration: float
    hit_start: float
    hit_end: float
    damage: int
    range_px: int
    hitbox_height: int
    player_vertical_boost: float
    player_gravity_modifier: float
    enemy_lift_velocity: float
    enemy_slam_velocity: float
    enemy_air_gravity_modifier: float
    enemy_knockback_x: float
    launch_player: bool
    variant_check_frame: int | None
    hitbox_animation: str | None
    hitbox_frame_count: int | None

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "AttackProfile":
        """Build an attack profile from one JSON object."""
        return cls(
            id=str(data["id"]),
            animation=str(data["animation"]),
            duration=float(data["duration"]),
            hit_start=float(data["hit_start"]),
            hit_end=float(data["hit_end"]),
            damage=int(data["damage"]),
            range_px=int(data["range_px"]),
            hitbox_height=int(data["hitbox_height"]),
            player_vertical_boost=float(data.get("player_vertical_boost", 0.0)),
            player_gravity_modifier=float(data.get("player_gravity_modifier", 1.0)),
            enemy_lift_velocity=float(data.get("enemy_lift_velocity", 0.0)),
            enemy_slam_velocity=float(data.get("enemy_slam_velocity", 0.0)),
            enemy_air_gravity_modifier=float(data.get("enemy_air_gravity_modifier", 1.0)),
            enemy_knockback_x=float(data.get("enemy_knockback_x", 0.0)),
            launch_player=bool(data.get("launch_player", False)),
            variant_check_frame=int(data["variant_check_frame"]) if "variant_check_frame" in data else None,
            hitbox_animation=str(data["hitbox_animation"]) if data.get("hitbox_animation") else None,
            hitbox_frame_count=int(data["hitbox_frame_count"]) if data.get("hitbox_frame_count") is not None else None,
        )

    @property
    def variant_check_time(self) -> float | None:
        """Return the attack-button sampling time configured as an animation frame."""
        if self.variant_check_frame is None:
            return None
        return self.variant_check_frame / self.FRAMES_PER_SECOND


def load_attack_profiles(path: str | Path = "data/attacks.json", *, include_utility: bool = False) -> dict[str, AttackProfile]:
    """Load configured attacks by id, optionally including utility actions."""
    raw_data = json.loads(Path(path).read_text(encoding="utf-8"))
    attacks = raw_data.get("attacks", [])
    if not isinstance(attacks, list):
        raise ValueError("attacks.json must contain an 'attacks' list")
    utility_ids = {"taunt", "ability"}
    profiles = [
        AttackProfile.from_dict(attack)
        for attack in attacks
        if isinstance(attack, dict) and (include_utility or str(attack.get("id")) not in utility_ids)
    ]
    return {profile.id: profile for profile in profiles}
