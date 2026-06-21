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


def test_player_animation_contracts_match_declared_sprite_counts():
    assert PLAYER_ANIMATION_SPECS["idle"].source_frame_count == 4
    assert PLAYER_ANIMATION_SPECS["taunt"].source_frame_count == 13
    assert PLAYER_ANIMATION_SPECS["taunt"].drawn_frame_count == 26
    assert PLAYER_ANIMATION_SPECS["run"].source_frame_count == 8
    assert PLAYER_ANIMATION_SPECS["yamato_ground_slash"].source_frame_count == 11
    assert PLAYER_ANIMATION_SPECS["yamato_ground_launcher"].drawn_frame_count == 11
    assert "yamato_ground_launcher_rise" not in PLAYER_ANIMATION_SPECS
    assert "yamato_ground_launcher_full" not in PLAYER_ANIMATION_SPECS
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

    player.x = 250
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

    for _ in range(3):
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


def test_launcher_variant_switches_to_full_when_attack_released_before_configured_frame():
    config = _config()
    player = _player(config)

    player.start_yamato_attack(back_modifier=True, attack_key_held=True)
    player.update(0.11, move_axis=0, arena_rect=pygame.Rect(0, 0, 800, 600), attack_key_held=False)

    assert player.attack_state is not None
    assert player.attack_state.profile.id == "yamato_ground_launcher_full"


def test_launcher_variant_stays_rise_when_attack_held_on_configured_frame():
    config = _config()
    player = _player(config)

    player.start_yamato_attack(back_modifier=True, attack_key_held=True)
    player.update(0.11, move_axis=0, arena_rect=pygame.Rect(0, 0, 800, 600), attack_key_held=True)

    assert player.attack_state is not None
    assert player.attack_state.profile.id == "yamato_ground_launcher_rise"


def test_enemy_spacing_stops_enemy_instead_of_pushing_neighbor():
    config = _config()
    arena = pygame.Rect(-800, 0, 2400, 600)
    player = _player(config)
    player.x = 600
    rear = SlowEnemy(x=200, profile=config.enemies["slow_enemy"])
    front = SlowEnemy(x=250, profile=config.enemies["slow_enemy"])

    rear.update(0.1, player, arena, neighbors=[rear, front])
    front.update(0.1, player, arena, neighbors=[rear, front])

    assert rear.velocity_x == 0
    assert rear.x == 200
    assert front.x > 250


def test_attack_animation_frame_index_is_scaled_to_attack_duration():
    config = _config()
    player = _player(config)

    player.start_yamato_attack(back_modifier=False, attack_key_held=True)
    player.update(0.21, move_axis=0, arena_rect=pygame.Rect(0, 0, 800, 600), attack_key_held=True)

    assert player.attack_state is not None
    assert player.current_animation_frame_index(11) == 5


def test_launcher_variant_keeps_shared_animation_when_branch_resolves():
    config = _config()
    player = _player(config)

    player.start_yamato_attack(back_modifier=True, attack_key_held=True)
    animation_before = player.current_animation
    player.update(0.09, move_axis=0, arena_rect=pygame.Rect(0, 0, 800, 600), attack_key_held=True)
    frame_before = player.current_animation_frame_index(11)
    player.update(0.02, move_axis=0, arena_rect=pygame.Rect(0, 0, 800, 600), attack_key_held=False)

    assert player.attack_state is not None
    assert player.attack_state.profile.id == "yamato_ground_launcher_full"
    assert player.current_animation == animation_before == "yamato_ground_launcher"
    assert player.current_animation_frame_index(11) >= frame_before


def test_enemy_attack_animation_frame_index_is_scaled_to_attack_duration():
    config = _config()
    player = _player(config)
    enemy = HeavyEnemy(x=120, profile=config.enemies["heavy_enemy"])

    enemy.update(0.01, player, pygame.Rect(0, 0, 800, 600), neighbors=[enemy])
    enemy.update(enemy.profile.attack_duration / 2, player, pygame.Rect(0, 0, 800, 600), neighbors=[enemy])

    assert enemy.current_animation_frame_index(enemy.profile.attack_hitbox_frame_count or 1) == 4


def test_enemy_attack_hitbox_damages_player_and_resets_combo():
    config = _config()
    player = _player(config)
    enemy = HeavyEnemy(x=120, profile=config.enemies["heavy_enemy"])

    enemy.update(0.01, player, pygame.Rect(0, 0, 800, 600), neighbors=[enemy])
    enemy.update(0.2, player, pygame.Rect(0, 0, 800, 600), neighbors=[enemy])

    assert enemy.attack_hitbox is not None
    assert enemy.profile.attack_damage == 2


def test_player_uses_five_health_points():
    player = _player()

    assert player.max_health == 5
    assert player.health == 5


def test_dead_enemy_keeps_knockback_without_chase_velocity():
    config = _config()
    enemy = HeavyEnemy(x=120, profile=config.enemies["heavy_enemy"])
    enemy.velocity_x = enemy.profile.speed
    enemy.health = 10

    enemy.receive_attack(config.attacks["yamato_air_slam"], attacker_center_x=0)

    assert enemy.is_dying is True
    assert enemy.velocity_x == 0
    assert enemy.horizontal_knockback > 0
    assert enemy.current_animation == enemy.profile.death_animation


def test_player_death_animation_stops_on_last_frame():
    config = _config()
    player = _player(config)
    player.receive_damage(player.health)
    player.update(config.player_combat.death_duration * 2, move_axis=0, arena_rect=pygame.Rect(0, 0, 800, 600))

    assert player.current_animation == "death"
    assert player.current_animation_frame_index(3) == 2


def test_enemy_death_animation_stops_on_last_frame():
    config = _config()
    enemy = HeavyEnemy(x=120, profile=config.enemies["heavy_enemy"])
    enemy.health = 1
    enemy.receive_attack(config.attacks["yamato_ground_slash"], attacker_center_x=0)
    enemy.update(enemy.profile.death_linger_duration * 2, _player(config), pygame.Rect(0, 0, 800, 600))

    assert enemy.current_animation == enemy.profile.death_animation
    assert enemy.current_animation_frame_index(3) == 2


def test_ability_dashes_forward_and_leaves_damaging_path_hitbox():
    config = _config()
    player = _player(config)
    player.ability_charge_percent = 100
    player.facing = 1
    arena = pygame.Rect(0, 0, 800, 600)

    assert player.try_activate_ability() is True
    player.update(0.13, move_axis=0, arena_rect=arena)

    ability = config.attacks["ability"]
    assert player.x == 100 + ability.range_px
    assert player.attack_hitbox is not None
    assert player.attack_hitbox.left <= 100
    assert player.attack_hitbox.right >= player.rect.right
    assert ability.damage > 0
