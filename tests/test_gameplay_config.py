from __future__ import annotations

from src.combat.attack import load_attack_profiles
from src.core.gameplay_config import GameplayConfig, load_enemy_profiles, load_movement_settings


def test_gameplay_config_loads_player_movement_attacks_and_enemies():
    config = GameplayConfig.from_files()

    assert config.movement.horizontal_speed == 300
    assert config.movement.jump_velocity == -620
    assert config.movement.air_gravity == 1200
    assert config.attacks["yamato_ground_slash"].damage == 25
    assert config.attacks["yamato_air_lift"].player_gravity_modifier == 0.6
    assert config.attacks["yamato_ground_slash"].enemy_knockback_x == 300
    assert config.enemies["heavy_enemy"].launch_hits_required == 4
    assert config.enemies["slow_enemy"].enemy_spacing_distance == 120
    assert config.sprites.root == "assets/sprites/player"
    assert config.sprites.animations["run"].folder == "run"
    assert config.sprites.animations["run"].right_frames == 8
    assert config.enemy_sprites.root == "assets/sprites/enemies"


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
    assert attacks["yamato_air_slam"].enemy_slam_velocity == 900
    assert attacks["yamato_air_slam"].enemy_knockback_x == 500
    assert attacks["yamato_ground_launcher_rise"].variant_check_frame == 6
    assert attacks["yamato_ground_launcher_rise"].animation == "yamato_ground_launcher"
    assert attacks["yamato_ground_launcher_full"].animation == "yamato_ground_launcher"
    assert attacks["yamato_ground_slash"].hitbox_animation == "yamato_ground_slash_hitbox"
    assert attacks["yamato_ground_launcher_rise"].hitbox_animation == "yamato_ground_launcher_hitbox"
    assert attacks["yamato_ground_launcher_full"].hitbox_animation == "yamato_ground_launcher_hitbox"


def test_enemy_profiles_include_launch_hit_thresholds():
    enemies = load_enemy_profiles()

    assert enemies["slow_enemy"].launch_hits_required == 0
    assert enemies["fast_enemy"].speed == 200
    assert enemies["heavy_enemy"].max_health == 150
    assert enemies["heavy_enemy"].launch_hits_required == 4
    assert enemies["fast_enemy"].enemy_spacing_distance == 120


def test_movement_settings_keep_wasd_vertical_movement_out_of_player_motion():
    movement = load_movement_settings()

    assert movement.horizontal_speed > 0
    assert movement.jump_velocity < 0
    assert movement.ground_gravity > movement.air_gravity


def test_combo_settings_and_enemy_attack_profiles_load_from_json():
    config = GameplayConfig.from_files()

    assert config.combo.timeout == 5.0
    assert config.combo.ranks[0].rank == "E"
    assert config.combo.ranks[-1].rank == "S"
    assert config.enemies["slow_enemy"].attack_damage == 1
    assert config.enemies["fast_enemy"].attack_damage == 1
    assert config.enemies["heavy_enemy"].attack_damage == 2
    assert config.enemies["heavy_enemy"].attack_hitbox_animation == "heavy_enemy_attack_hitbox"
    assert config.enemies["heavy_enemy"].attack_hitbox_frame_count == 8
    assert "yamato_ground_launcher_full" not in config.sprites.animations
    assert "yamato_ground_launcher_rise" not in config.sprites.animations
    assert config.sprites.animations["yamato_ground_launcher_hitbox"].folder == "../effects/yamato_ground_launcher_hitbox"
    assert config.sprites.animations["yamato_ground_launcher_hitbox"].frame_count == 11
    assert config.enemy_sprites.animations["heavy_enemy_attack"].folder == "heavy_enemy/attack"
