"""Player prototype with configurable movement, jump and Yamato attacks."""

from __future__ import annotations

from dataclasses import dataclass, field

import pygame

from src.combat.attack import AttackProfile
from src.core.gameplay_config import MovementSettings
from src.entities.animation import get_player_animation_spec
from src.entities.entity import Entity

GROUND_Y = 560


@dataclass(slots=True)
class AttackState:
    """Runtime state for an active attack animation."""

    profile: AttackProfile
    elapsed: float = 0.0
    hit_enemy_ids: set[int] = field(default_factory=set)

    @property
    def is_active_hit_window(self) -> bool:
        """Whether the attack can currently damage enemies."""
        return self.profile.hit_start <= self.elapsed <= self.profile.hit_end


class Player(Entity):
    """Controllable hero for the first playable arena slice."""

    def __init__(
        self,
        *,
        x: float,
        movement: MovementSettings,
        attacks: dict[str, AttackProfile],
        ground_y: float = GROUND_Y,
    ) -> None:
        super().__init__(
            x=x,
            y=ground_y - movement.height,
            width=movement.width,
            height=movement.height,
            color=(120, 210, 255),
            max_health=100,
            health=100,
        )
        self.ground_y = ground_y
        self.movement = movement
        self.attacks = attacks
        self.facing = 1
        self.attack_state: AttackState | None = None
        self.current_animation = "idle"
        self.is_on_ground = True

    def start_jump(self) -> None:
        """Start a jump using the configured separate jump key, not W/S."""
        if self.is_on_ground and self.attack_state is None:
            self.velocity_y = self.movement.jump_velocity
            self.is_on_ground = False
            self.current_animation = "jump_rise"

    def start_yamato_attack(self, *, back_modifier: bool, attack_key_held: bool) -> None:
        """Choose the proper Yamato attack from ground/air and S + attack state."""
        if self.attack_state is not None:
            return

        if self.is_on_ground:
            if back_modifier:
                attack_id = "yamato_ground_launcher_rise" if attack_key_held else "yamato_ground_launcher_full"
            else:
                attack_id = "yamato_ground_slash"
        elif back_modifier:
            attack_id = "yamato_air_slam"
        else:
            attack_id = "yamato_air_lift"

        profile = self.attacks[attack_id]
        self.attack_state = AttackState(profile)
        self.current_animation = profile.animation
        get_player_animation_spec(profile.animation)

    @property
    def attack_hitbox(self) -> pygame.Rect | None:
        """Return the current Yamato hitbox during active attack frames."""
        if self.attack_state is None or not self.attack_state.is_active_hit_window:
            return None
        profile = self.attack_state.profile
        hitbox_top = self.rect.centery - profile.hitbox_height // 2
        if self.facing >= 0:
            return pygame.Rect(self.rect.right, hitbox_top, profile.range_px, profile.hitbox_height)
        return pygame.Rect(self.rect.left - profile.range_px, hitbox_top, profile.range_px, profile.hitbox_height)

    def update(self, dt: float, *, move_axis: int, arena_rect: pygame.Rect) -> None:
        """Advance movement, gravity and active attack animation."""
        if self.attack_state is None:
            self.velocity_x = move_axis * self.movement.horizontal_speed
            if move_axis != 0:
                self.facing = move_axis
        else:
            self.velocity_x = move_axis * self.movement.horizontal_speed * self.movement.attack_horizontal_speed_modifier

        self.x += self.velocity_x * dt
        self.x = max(arena_rect.left, min(self.x, arena_rect.right - self.width))

        gravity = self.movement.ground_gravity if self.is_on_ground else self.movement.air_gravity
        if self.attack_state is not None:
            gravity *= self.attack_state.profile.player_gravity_modifier
        if not self.is_on_ground or self.velocity_y < 0:
            self.velocity_y += gravity * dt
            self.y += self.velocity_y * dt

        if self.bottom >= self.ground_y:
            self.y = self.ground_y - self.height
            self.velocity_y = 0.0
            self.is_on_ground = True
        else:
            self.is_on_ground = False

        self._update_attack(dt)
        self._update_animation_from_motion(move_axis)

    def _update_attack(self, dt: float) -> None:
        if self.attack_state is None:
            return
        self.attack_state.elapsed += dt
        profile = self.attack_state.profile
        if profile.launch_player and self.attack_state.elapsed >= profile.duration * 0.72 and self.is_on_ground:
            self.velocity_y = profile.player_vertical_boost
            self.is_on_ground = False
        if self.attack_state.elapsed >= profile.duration:
            self.attack_state = None

    def _update_animation_from_motion(self, move_axis: int) -> None:
        if self.attack_state is not None:
            return
        if not self.is_on_ground:
            if self.velocity_y < -80:
                self.current_animation = "jump_rise"
            elif abs(self.velocity_y) <= 80:
                self.current_animation = "jump_hang"
            else:
                self.current_animation = "fall"
        elif move_axis != 0:
            self.current_animation = "run"
        else:
            self.current_animation = "idle"
