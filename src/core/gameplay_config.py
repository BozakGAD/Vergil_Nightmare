"""JSON-backed tunable gameplay configuration."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from src.combat.attack import AttackProfile, load_attack_profiles


@dataclass(frozen=True, slots=True)
class ComboRankSettings:
    """Combo rank threshold and scoring multiplier."""

    rank: str
    min_hits: int
    score_multiplier: float


@dataclass(frozen=True, slots=True)
class StyleRankSettings:
    """Final style rank threshold by accumulated score."""

    rank: str
    min_score: float


@dataclass(frozen=True, slots=True)
class ComboSettings:
    """Session combo and style scoring settings."""

    timeout: float
    ranks: tuple[ComboRankSettings, ...]
    style_score_ranks: tuple[StyleRankSettings, ...]
    taunt_score_multiplier: float = 1.5


@dataclass(frozen=True, slots=True)
class PlayerCombatSettings:
    """Configurable player combat state timings and ability charge."""

    hurt_duration: float
    hurt_invulnerability_duration: float
    death_duration: float
    ability_charge_rate: float
    ability_damage_loss_percent: float


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


@dataclass(frozen=True, slots=True, eq=False)
class AnimationSettings:
    """Configurable animation folder and timing metadata."""

    folder: str
    frame_duration: float
    frame_count: int | None = None
    left_frames: int | None = None
    right_frames: int | None = None

    def __eq__(self, other: object) -> bool:
        """Support legacy comparisons that treated animation settings as folder strings."""
        if isinstance(other, str):
            return self.folder == other
        if not isinstance(other, AnimationSettings):
            return NotImplemented
        return (
            self.folder,
            self.frame_duration,
            self.frame_count,
            self.left_frames,
            self.right_frames,
        ) == (
            other.folder,
            other.frame_duration,
            other.frame_count,
            other.left_frames,
            other.right_frames,
        )


@dataclass(frozen=True, slots=True)
class SpriteSettings:
    """Sprite loading settings grouped by entity responsibility."""

    root: str | None
    animations: dict[str, AnimationSettings]
    scale: int
    default_frame_duration: float


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
    enemy_spacing_distance: float
    attack_damage: int
    attack_range: float
    attack_cooldown: float
    attack_duration: float
    attack_hit_start: float
    attack_hit_end: float
    attack_hitbox_width: int
    attack_hitbox_height: int
    idle_animation: str
    approach_animation: str
    hurt_animation: str
    death_animation: str
    hurt_duration: float
    attack_animation: str
    attack_hitbox_animation: str | None
    attack_hitbox_frame_count: int | None
    death_linger_duration: float


@dataclass(frozen=True, slots=True)
class GameplayConfig:
    """All gameplay prototype settings loaded from JSON files."""

    movement: MovementSettings
    sprites: SpriteSettings
    attacks: dict[str, AttackProfile]
    enemies: dict[str, EnemyProfile]
    enemy_sprites: SpriteSettings
    combo: ComboSettings
    player_combat: PlayerCombatSettings

    @classmethod
    def from_files(
        cls,
        *,
        player_path: str | Path = "data/player.json",
        attacks_path: str | Path = "data/attacks.json",
        enemies_path: str | Path = "data/enemies.json",
        combo_path: str | Path = "data/combo.json",
    ) -> "GameplayConfig":
        """Load player movement, attacks and enemies from JSON files."""
        return cls(
            movement=load_movement_settings(player_path),
            sprites=load_sprite_settings(player_path),
            attacks=load_attack_profiles(attacks_path, include_utility=True),
            enemies=load_enemy_profiles(enemies_path),
            enemy_sprites=load_sprite_settings(enemies_path),
            combo=load_combo_settings(combo_path),
            player_combat=load_player_combat_settings(player_path),
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


def load_player_combat_settings(path: str | Path = "data/player.json") -> PlayerCombatSettings:
    """Load player hurt/death timings and ability charge settings."""
    raw_data = json.loads(Path(path).read_text(encoding="utf-8"))
    combat = raw_data.get("combat", {})
    ability = raw_data.get("ability", {})
    return PlayerCombatSettings(
        hurt_duration=float(combat.get("hurt_duration", 0.45)),
        hurt_invulnerability_duration=float(combat.get("hurt_invulnerability_duration", 0.75)),
        death_duration=float(combat.get("death_duration", 1.0)),
        ability_charge_rate=float(ability.get("charge_rate_percent_per_second", 8.0)),
        ability_damage_loss_percent=float(ability.get("damage_loss_percent", 25.0)),
    )


def load_sprite_settings(path: str | Path = "data/player.json") -> SpriteSettings:
    """Load sprite animation folder settings from an entity JSON file."""
    raw_data = json.loads(Path(path).read_text(encoding="utf-8"))
    sprites = raw_data.get("sprites", {})
    if not isinstance(sprites, dict):
        return SpriteSettings(root=None, animations={}, scale=1, default_frame_duration=0.08)

    default_frame_duration = float(sprites.get("frame_duration", 0.08))
    return SpriteSettings(
        root=sprites.get("root"),
        animations=_load_animation_settings(sprites.get("animations", {}), default_frame_duration),
        scale=int(sprites.get("scale", 1)),
        default_frame_duration=default_frame_duration,
    )


def _load_animation_settings(raw_animations: object, default_frame_duration: float) -> dict[str, AnimationSettings]:
    if not isinstance(raw_animations, dict):
        return {}
    animations: dict[str, AnimationSettings] = {}
    for name, data in raw_animations.items():
        if isinstance(data, str):
            animations[str(name)] = AnimationSettings(folder=data, frame_duration=default_frame_duration)
        elif isinstance(data, dict):
            animations[str(name)] = AnimationSettings(
                folder=str(data["folder"]),
                frame_duration=float(data.get("frame_duration", default_frame_duration)),
                frame_count=int(data["frame_count"]) if data.get("frame_count") is not None else None,
                left_frames=int(data["left_frames"]) if data.get("left_frames") is not None else None,
                right_frames=int(data["right_frames"]) if data.get("right_frames") is not None else None,
            )
    return animations


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
        color = tuple(int(value) for value in enemy_data.get("color", (210, 80, 90)))
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
            enemy_spacing_distance=float(defaults.get("enemy_spacing_distance", 96)),
            attack_damage=int(enemy_data.get("attack_damage", defaults.get("attack_damage", 1))),
            attack_range=float(enemy_data.get("attack_range", defaults.get("attack_range", 70))),
            attack_cooldown=float(enemy_data.get("attack_cooldown", defaults.get("attack_cooldown", 1.2))),
            attack_duration=float(enemy_data.get("attack_duration", defaults.get("attack_duration", 0.45))),
            attack_hit_start=float(enemy_data.get("attack_hit_start", defaults.get("attack_hit_start", 0.12))),
            attack_hit_end=float(enemy_data.get("attack_hit_end", defaults.get("attack_hit_end", 0.24))),
            attack_hitbox_width=int(enemy_data.get("attack_hitbox_width", defaults.get("attack_hitbox_width", 56))),
            attack_hitbox_height=int(enemy_data.get("attack_hitbox_height", defaults.get("attack_hitbox_height", 56))),
            idle_animation=str(enemy_data.get("idle_animation", f"{enemy_id}_idle")),
            approach_animation=str(enemy_data.get("approach_animation", f"{enemy_id}_approach")),
            hurt_animation=str(enemy_data.get("hurt_animation", f"{enemy_id}_hurt")),
            death_animation=str(enemy_data.get("death_animation", f"{enemy_id}_death")),
            hurt_duration=float(enemy_data.get("hurt_duration", defaults.get("hurt_duration", 0.18))),
            attack_animation=str(enemy_data.get("attack_animation", f"{enemy_id}_attack")),
            attack_hitbox_animation=str(enemy_data["attack_hitbox_animation"]) if enemy_data.get("attack_hitbox_animation") else None,
            attack_hitbox_frame_count=(
                int(enemy_data.get("attack_hitbox_frame_count", defaults.get("attack_hitbox_frame_count")))
                if enemy_data.get("attack_hitbox_frame_count", defaults.get("attack_hitbox_frame_count")) is not None
                else None
            ),
            death_linger_duration=float(enemy_data.get("death_linger_duration", defaults.get("death_linger_duration", 1.2))),
        )
    return profiles


def load_combo_settings(path: str | Path = "data/combo.json") -> ComboSettings:
    """Load combo thresholds and final style scoring settings."""
    raw_data = json.loads(Path(path).read_text(encoding="utf-8"))
    ranks = tuple(
        ComboRankSettings(
            rank=str(rank_data["rank"]),
            min_hits=int(rank_data["min_hits"]),
            score_multiplier=float(rank_data.get("score_multiplier", 1.0)),
        )
        for rank_data in raw_data.get("ranks", [])
        if isinstance(rank_data, dict)
    )
    style_ranks = tuple(
        StyleRankSettings(rank=str(rank_data["rank"]), min_score=float(rank_data["min_score"]))
        for rank_data in raw_data.get("style_score_ranks", [])
        if isinstance(rank_data, dict)
    )
    return ComboSettings(
        timeout=float(raw_data.get("timeout", 5.0)),
        ranks=ranks,
        style_score_ranks=style_ranks,
        taunt_score_multiplier=float(raw_data.get("taunt_score_multiplier", 1.5)),
    )
