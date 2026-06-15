"""JSON-backed tunable gameplay configuration."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from src.combat.attack import AttackProfile, load_attack_profiles


@dataclass(frozen=True, slots=True)
class MovementSettings:
    """Player movement and gravity parameters."""

    horizontal_speed: float
    attack_horizontal_speed_modifier: float
    jump_velocity: float
    ground_gravity: float
    air_gravity: float
    width: int
    height: int


@dataclass(frozen=True, slots=True)
class SpriteSettings:
    """Optional player sprite loading settings."""

    root: str | None
    animations: dict[str, str]
    frame_duration: float
    scale: int


@dataclass(frozen=True, slots=True)
class EnemyProfile:
    """Enemy parameters that can be tuned without editing code."""

    enemy_id: str
    width: int
    height: int
    speed: float
    max_health: int
    color: tuple[int, int, int]
    preferred_air_distance: float
    stop_distance: float
    gravity: float
    air_gravity_modifier: float
    launch_hits_required: int


@dataclass(frozen=True, slots=True)
class GameplayConfig:
    """All gameplay prototype settings loaded from JSON files."""

    movement: MovementSettings
    sprites: SpriteSettings
    attacks: dict[str, AttackProfile]
    enemies: dict[str, EnemyProfile]

    @classmethod
    def from_files(
        cls,
        *,
        player_path: str | Path = "data/player.json",
        attacks_path: str | Path = "data/attacks.json",
        enemies_path: str | Path = "data/enemies.json",
    ) -> "GameplayConfig":
        """Load player movement, attacks and enemies from JSON files."""
        return cls(
            movement=load_movement_settings(player_path),
            sprites=load_sprite_settings(player_path),
            attacks=load_attack_profiles(attacks_path),
            enemies=load_enemy_profiles(enemies_path),
        )


def load_movement_settings(path: str | Path = "data/player.json") -> MovementSettings:
    """Load player movement and gravity settings."""
    raw_data = json.loads(Path(path).read_text(encoding="utf-8"))
    movement = raw_data["movement"]
    size = raw_data["size"]
    return MovementSettings(
        horizontal_speed=float(movement["horizontal_speed"]),
        attack_horizontal_speed_modifier=float(movement["attack_horizontal_speed_modifier"]),
        jump_velocity=float(movement["jump_velocity"]),
        ground_gravity=float(movement["ground_gravity"]),
        air_gravity=float(movement["air_gravity"]),
        width=int(size["width"]),
        height=int(size["height"]),
    )


def load_sprite_settings(path: str | Path = "data/player.json") -> SpriteSettings:
    """Load optional sprite animation folder settings."""
    raw_data = json.loads(Path(path).read_text(encoding="utf-8"))
    sprites = raw_data.get("sprites", {})
    return SpriteSettings(
        root=sprites.get("root") if isinstance(sprites, dict) else None,
        animations=dict(sprites.get("animations", {})) if isinstance(sprites, dict) else {},
        frame_duration=float(sprites.get("frame_duration", 0.08)) if isinstance(sprites, dict) else 0.08,
        scale=int(sprites.get("scale", 1)) if isinstance(sprites, dict) else 1,
    )


def load_enemy_profiles(path: str | Path = "data/enemies.json") -> dict[str, EnemyProfile]:
    """Load all enemy profiles, merging common defaults into each enemy."""
    raw_data = json.loads(Path(path).read_text(encoding="utf-8"))
    defaults = raw_data.get("defaults", {})
    enemies = raw_data.get("enemies", {})
    if not isinstance(enemies, dict):
        raise ValueError("enemies.json must contain an 'enemies' object")

    profiles: dict[str, EnemyProfile] = {}
    for enemy_id, enemy_data in enemies.items():
        if not isinstance(enemy_data, dict):
            continue
        color_values = enemy_data.get("color", (210, 80, 90))
        color = tuple(int(value) for value in color_values)
        if len(color) != 3:
            raise ValueError(f"Enemy '{enemy_id}' color must contain exactly 3 components")
        profiles[str(enemy_id)] = EnemyProfile(
            enemy_id=str(enemy_id),
            width=int(enemy_data["width"]),
            height=int(enemy_data["height"]),
            speed=float(enemy_data["speed"]),
            max_health=int(enemy_data["max_health"]),
            color=color,
            preferred_air_distance=float(enemy_data.get("preferred_air_distance", defaults.get("preferred_air_distance", 150))),
            stop_distance=float(enemy_data.get("stop_distance", defaults.get("stop_distance", 58))),
            gravity=float(enemy_data.get("gravity", defaults.get("gravity", 1550))),
            air_gravity_modifier=float(enemy_data.get("air_gravity_modifier", defaults.get("air_gravity_modifier", 1.0))),
            launch_hits_required=int(enemy_data.get("launch_hits_required", defaults.get("launch_hits_required", 0))),
        )
    return profiles
