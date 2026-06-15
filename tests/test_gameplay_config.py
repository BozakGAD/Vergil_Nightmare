from __future__ import annotations

from src.combat.attack import load_attack_profiles
from src.core.gameplay_config import GameplayConfig, load_enemy_profiles, load_movement_settings


def test_gameplay_config_loads_player_movement_attacks_and_enemies():
    config = GameplayConfig.from_files()

    assert config.movement.horizontal_speed == 300
    assert config.movement.jump_velocity == -620
    assert config.movement.air_gravity == 1200
    assert config.attacks["yamato_ground_slash"].damage == 18
    assert config.attacks["yamato_air_lift"].player_gravity_modifier == 0.28
    assert config.attacks["yamato_ground_slash"].enemy_knockback_x == 190
    assert config.enemies["heavy_enemy"].launch_hits_required == 5
    assert config.sprites.root == "assets/sprites/player"


def test_attack_profiles_are_loaded_by_id():
    attacks = load_attack_profiles()

    assert set(attacks) == {
        "yamato_ground_slash",
        "yamato_ground_launcher_full",
        "yamato_ground_launcher_rise",
        "yamato_air_lift",
        "yamato_air_slam",
    }
    assert attacks["yamato_ground_launcher_rise"].launch_player is True
    assert attacks["yamato_air_slam"].enemy_slam_velocity == 620
    assert attacks["yamato_air_slam"].enemy_knockback_x == 120


def test_enemy_profiles_include_launch_hit_thresholds():
    enemies = load_enemy_profiles()

    assert enemies["slow_enemy"].launch_hits_required == 0
    assert enemies["fast_enemy"].speed == 145
    assert enemies["heavy_enemy"].max_health == 90
    assert enemies["heavy_enemy"].launch_hits_required == 5


def test_movement_settings_keep_wasd_vertical_movement_out_of_player_motion():
    movement = load_movement_settings()

    assert movement.horizontal_speed > 0
    assert movement.jump_velocity < 0
    assert movement.ground_gravity > movement.air_gravity
