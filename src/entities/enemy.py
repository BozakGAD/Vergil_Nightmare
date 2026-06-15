"""Enemy prototypes configured from JSON."""

from __future__ import annotations

import pygame

from src.combat.attack import AttackProfile
from src.core.gameplay_config import EnemyProfile
from src.entities.entity import Entity
from src.entities.player import GROUND_Y, Player


class Enemy(Entity):
    """Base enemy that chases grounded player and keeps distance from aerial player."""

    def __init__(self, *, x: float, profile: EnemyProfile, ground_y: float = GROUND_Y) -> None:
        super().__init__(
            x=x,
            y=ground_y - profile.height,
            width=profile.width,
            height=profile.height,
            color=profile.color,
            max_health=profile.max_health,
            health=profile.max_health,
        )
        self.profile = profile
        self.ground_y = ground_y
        self.is_on_ground = True
        self.launch_hit_counter = 0
        self.current_air_gravity_modifier = profile.air_gravity_modifier
        self.horizontal_knockback = 0.0

    @property
    def can_be_launched(self) -> bool:
        """Whether launch attacks can lift this enemy right now."""
        return self.launch_hit_counter >= self.profile.launch_hits_required

    @property
    def needs_launch_charge(self) -> bool:
        """Whether this enemy has an internal hit counter before launch."""
        return self.profile.launch_hits_required > 0

    def update(self, dt: float, player: Player, arena_rect: pygame.Rect) -> None:
        """Move according to the player's grounded/aerial state."""
        if not self.is_alive:
            return

        if self.is_on_ground:
            distance = player.centerx - self.centerx
            abs_distance = abs(distance)
            direction = 1 if distance > 0 else -1
            self.velocity_x = 0.0 if abs_distance <= self.profile.stop_distance else direction * self.profile.speed
        else:
            self.velocity_x = 0.0

        movement_x = self.velocity_x + self.horizontal_knockback
        self.x += movement_x * dt
        self.x = max(arena_rect.left, min(self.x, arena_rect.right - self.width))
        self.horizontal_knockback = self._approach_zero(self.horizontal_knockback, 900 * dt)

        if not self.is_on_ground or self.velocity_y != 0:
            self.velocity_y += self.profile.gravity * self.current_air_gravity_modifier * dt
            self.y += self.velocity_y * dt
            if self.bottom >= self.ground_y:
                self.y = self.ground_y - self.height
                self.velocity_y = 0.0
                self.is_on_ground = True
                self.current_air_gravity_modifier = self.profile.air_gravity_modifier

    def receive_attack(self, profile: AttackProfile, attacker_center_x: float) -> bool:
        """Apply one attack and return whether the enemy was launched or slammed."""
        self.take_damage(profile.damage)
        if not self.is_alive:
            return False

        knockback_direction = 1 if self.centerx >= attacker_center_x else -1
        self.horizontal_knockback = knockback_direction * profile.enemy_knockback_x
        self.launch_hit_counter += 1
        moved_vertically = False
        if profile.enemy_lift_velocity and (not self.is_on_ground or self.can_be_launched):
            self.launch(profile.enemy_lift_velocity, profile.enemy_air_gravity_modifier)
            self.launch_hit_counter = 0 if self.needs_launch_charge else self.launch_hit_counter
            moved_vertically = True
        if profile.enemy_slam_velocity and not self.is_on_ground:
            self.slam(profile.enemy_slam_velocity, profile.enemy_air_gravity_modifier)
            moved_vertically = True
        return moved_vertically

    def launch(self, velocity_y: float, air_gravity_modifier: float) -> None:
        """Lift the enemy once its launch hit counter allows it."""
        self.velocity_y = velocity_y
        self.current_air_gravity_modifier = air_gravity_modifier
        self.is_on_ground = False

    def slam(self, velocity_y: float, air_gravity_modifier: float) -> None:
        """Send the enemy downward if it is airborne."""
        self.velocity_y = max(self.velocity_y, velocity_y)
        self.current_air_gravity_modifier = air_gravity_modifier

    def _approach_zero(self, value: float, amount: float) -> float:
        """Move a velocity value toward zero without changing its sign."""
        if value > 0:
            return max(0.0, value - amount)
        if value < 0:
            return min(0.0, value + amount)
        return 0.0


class SlowEnemy(Enemy):
    """Basic slow demon."""


class FastEnemy(Enemy):
    """Fast but fragile demon."""


class HeavyEnemy(Enemy):
    """Durable demon that must be hit several times before launch."""
