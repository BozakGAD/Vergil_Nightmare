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
        self.attack_elapsed = 0.0
        self.attack_cooldown_remaining = 0.0
        self.is_attacking = False
        self.has_hit_player_this_attack = False
        self.current_animation = "idle"
        self.facing = 1

    def current_animation_frame_index(self, frame_count: int) -> int:
        """Return a frame index synchronized to the active attack duration."""
        if frame_count <= 0:
            return 0
        if not self.is_attacking or self.profile.attack_duration <= 0:
            return 0
        frame_duration = self.profile.attack_duration / frame_count
        return min(frame_count - 1, int(self.attack_elapsed / frame_duration))

    @property
    def can_be_launched(self) -> bool:
        """Whether launch attacks can lift this enemy right now."""
        return self.launch_hit_counter >= self.profile.launch_hits_required

    @property
    def needs_launch_charge(self) -> bool:
        """Whether this enemy has an internal hit counter before launch."""
        return self.profile.launch_hits_required > 0

    def update(
        self,
        dt: float,
        player: Player,
        arena_rect: pygame.Rect,
        neighbors: list["Enemy"] | None = None,
    ) -> None:
        """Move according to the player's grounded/aerial state."""
        if not self.is_alive:
            return

        if self.attack_cooldown_remaining > 0:
            self.attack_cooldown_remaining = max(0.0, self.attack_cooldown_remaining - dt)
        if self.is_attacking:
            self._update_attack(dt)
        elif self.is_on_ground and self._can_start_attack(player):
            self._start_attack()

        if self.is_on_ground and not self.is_attacking:
            self.velocity_x = self._desired_ground_velocity(player)
            self.velocity_x = self._limit_velocity_for_spacing(self.velocity_x, neighbors or [])
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

    @property
    def is_attack_hit_active(self) -> bool:
        """Whether the current enemy attack can damage the player."""
        return self.is_attacking and self.profile.attack_hit_start <= self.attack_elapsed <= self.profile.attack_hit_end

    @property
    def attack_hitbox(self) -> pygame.Rect | None:
        """Return active attack hitbox for this enemy."""
        if not self.is_attack_hit_active:
            return None
        width = self.profile.attack_hitbox_width
        height = self.profile.attack_hitbox_height
        top = self.rect.centery - height // 2
        if self.facing < 0:
            return pygame.Rect(self.rect.left - width, top, width, height)
        return pygame.Rect(self.rect.right, top, width, height)

    def _can_start_attack(self, player: Player) -> bool:
        if self.attack_cooldown_remaining > 0:
            return False
        distance = player.centerx - self.centerx
        if abs(distance) <= self.profile.attack_range:
            self.facing = 1 if distance >= 0 else -1
            return True
        return False

    def _start_attack(self) -> None:
        self.is_attacking = True
        self.attack_elapsed = 0.0
        self.has_hit_player_this_attack = False
        self.velocity_x = 0.0
        self.current_animation = self.profile.attack_animation

    def _update_attack(self, dt: float) -> None:
        self.attack_elapsed += dt
        if self.attack_elapsed >= self.profile.attack_duration:
            self.is_attacking = False
            self.attack_elapsed = 0.0
            self.attack_cooldown_remaining = self.profile.attack_cooldown
            self.current_animation = "idle"

    def _limit_velocity_for_spacing(self, velocity_x: float, neighbors: list["Enemy"]) -> float:
        """Prevent movement that would push this enemy into another enemy's spacing bubble."""
        if velocity_x == 0 or not self.is_alive or not self.is_on_ground:
            return velocity_x
        spacing = self.profile.enemy_spacing_distance
        if spacing <= 0:
            return velocity_x
        for neighbor in neighbors:
            if neighbor is self or not neighbor.is_alive or not neighbor.is_on_ground:
                continue
            distance = neighbor.centerx - self.centerx
            if velocity_x > 0 and 0 < distance < spacing:
                return 0.0
            if velocity_x < 0 and -spacing < distance < 0:
                return 0.0
        return velocity_x

    def _desired_ground_velocity(self, player: Player) -> float:
        distance = player.centerx - self.centerx
        abs_distance = abs(distance)
        direction = 1 if distance > 0 else -1
        if not player.is_on_ground:
            preferred = self.profile.preferred_air_distance
            tolerance = self.profile.stop_distance
            if abs(abs_distance - preferred) <= tolerance:
                return 0.0
            velocity = direction * self.profile.speed if abs_distance > preferred else -direction * self.profile.speed
            self.facing = 1 if velocity > 0 else -1
            return velocity
        velocity = 0.0 if abs_distance <= self.profile.stop_distance else direction * self.profile.speed
        if velocity != 0:
            self.facing = 1 if velocity > 0 else -1
        return velocity

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


ENEMY_CLASSES: dict[str, type[Enemy]] = {
    "slow_enemy": SlowEnemy,
    "fast_enemy": FastEnemy,
    "heavy_enemy": HeavyEnemy,
}


def create_enemy(enemy_id: str, *, x: float, profile: EnemyProfile, ground_y: float = GROUND_Y) -> Enemy:
    """Create an enemy instance by id, keeping type mapping close to enemy classes."""
    return ENEMY_CLASSES[enemy_id](x=x, profile=profile, ground_y=ground_y)
