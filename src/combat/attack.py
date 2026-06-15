"""Configurable attack profiles loaded from JSON."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class AttackProfile:
    """Data needed by the prototype combat loop for one attack."""

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
        )


def load_attack_profiles(path: str | Path = "data/attacks.json") -> dict[str, AttackProfile]:
    """Load all configured attacks by id."""
    raw_data = json.loads(Path(path).read_text(encoding="utf-8"))
    attacks = raw_data.get("attacks", [])
    if not isinstance(attacks, list):
        raise ValueError("attacks.json must contain an 'attacks' list")
    profiles = [AttackProfile.from_dict(attack) for attack in attacks if isinstance(attack, dict)]
    return {profile.id: profile for profile in profiles}
