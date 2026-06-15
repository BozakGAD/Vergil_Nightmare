from __future__ import annotations

import pytest

pygame = pytest.importorskip("pygame")

from src.core.gameplay_config import GameplayConfig  # noqa: E402
from src.entities.animation import PLAYER_ANIMATION_SPECS  # noqa: E402
from src.entities.enemy import HeavyEnemy, SlowEnemy  # noqa: E402
from src.entities.player import Player  # noqa: E402


def _config() -> GameplayConfig:
    return GameplayConfig.from_files()


def _player(config: GameplayConfig | None = None) -> Player:
    config = config or _config()
    return Player(x=100, movement=config.movement, attacks=config.attacks)


def test_player_animation_placeholders_match_declared_sprite_counts():
    assert PLAYER_ANIMATION_SPECS["idle"].source_frame_count == 4
    assert PLAYER_ANIMATION_SPECS["taunt"].source_frame_count == 13
    assert PLAYER_ANIMATION_SPECS["taunt"].drawn_frame_count == 26
    assert PLAYER_ANIMATION_SPECS["run"].source_frame_count == 8
    assert PLAYER_ANIMATION_SPECS["yamato_ground_slash"].source_frame_count == 11
    assert PLAYER_ANIMATION_SPECS["yamato_ground_launcher_rise"].drawn_frame_count == 8
    assert PLAYER_ANIMATION_SPECS["yamato_air_lift"].source_frame_count == 6
    assert PLAYER_ANIMATION_SPECS["yamato_air_slam"].source_frame_count == 6


def test_s_modifier_selects_launcher_rise_when_attack_is_held():
    player = _player()

    player.start_yamato_attack(back_modifier=True, attack_key_held=True)

    assert player.attack_state is not None
    assert player.attack_state.profile.id == "yamato_ground_launcher_rise"
    assert player.attack_state.profile.launch_player is True


def test_air_s_modifier_selects_yamato_slam():
    player = _player()
    player.is_on_ground = False

    player.start_yamato_attack(back_modifier=True, attack_key_held=True)

    assert player.attack_state is not None
    assert player.attack_state.profile.id == "yamato_air_slam"


def test_enemy_chases_grounded_player_but_backs_away_from_airborne_player():
    config = _config()
    arena = pygame.Rect(0, 0, 800, 600)
    player = _player(config)
    enemy = SlowEnemy(x=440, profile=config.enemies["slow_enemy"])

    player.is_on_ground = True
    enemy.update(0.1, player, arena)
    grounded_velocity = enemy.velocity_x

    player.is_on_ground = False
    enemy.update(0.1, player, arena)
    airborne_velocity = enemy.velocity_x

    assert grounded_velocity < 0
    assert airborne_velocity > 0


def test_heavy_enemy_launches_after_configured_hit_counter_then_resets():
    config = _config()
    enemy = HeavyEnemy(x=200, profile=config.enemies["heavy_enemy"])
    slash = config.attacks["yamato_ground_slash"]
    launcher = config.attacks["yamato_ground_launcher_full"]

    for _ in range(4):
        enemy.receive_attack(slash, attacker_center_x=0)

    assert enemy.can_be_launched is False

    enemy.receive_attack(launcher, attacker_center_x=0)

    assert enemy.is_on_ground is False
    assert enemy.launch_hit_counter == 0
    assert enemy.velocity_y == launcher.enemy_lift_velocity
    assert enemy.horizontal_knockback == launcher.enemy_knockback_x


def test_airborne_heavy_enemy_can_be_relaunched_without_counter():
    config = _config()
    enemy = HeavyEnemy(x=200, profile=config.enemies["heavy_enemy"])
    enemy.is_on_ground = False
    enemy.launch_hit_counter = 0
    lift = config.attacks["yamato_air_lift"]

    enemy.receive_attack(lift, attacker_center_x=0)

    assert enemy.velocity_y == lift.enemy_lift_velocity
    assert enemy.current_air_gravity_modifier == lift.enemy_air_gravity_modifier


def test_airborne_enemy_is_stunned_and_does_not_ai_walk():
    config = _config()
    arena = pygame.Rect(0, 0, 800, 600)
    player = _player(config)
    enemy = SlowEnemy(x=440, profile=config.enemies["slow_enemy"])
    enemy.is_on_ground = False
    enemy.velocity_x = 300

    enemy.update(0.1, player, arena)

    assert enemy.velocity_x == 0
