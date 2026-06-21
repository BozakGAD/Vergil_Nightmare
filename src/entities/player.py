"""Player prototype with configurable movement, jump and Yamato attacks."""

from __future__ import annotations

from dataclasses import dataclass, field

import pygame

from src.combat.attack import AttackProfile
from src.core.gameplay_config import MovementSettings, PlayerCombatSettings
from src.entities.animation import get_player_animation_spec
from src.entities.entity import Entity

GROUND_Y = 560


@dataclass(slots=True)
class AttackState:
    """Runtime state for an active attack animation."""

    profile: AttackProfile
    elapsed: float = 0.0
    hit_enemy_ids: set[int] = field(default_factory=set)
    variant_choice_checked: bool = False
    animation_duration: float | None = None
    fixed_hitbox: pygame.Rect | None = None
    dash_resolved: bool = False

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
        combat: PlayerCombatSettings | None = None,
        ground_y: float = GROUND_Y,
    ) -> None:
        super().__init__(
            x=x,
            y=ground_y - movement.height,
            width=movement.width,
            height=movement.height,
            color=(120, 210, 255),
            max_health=5,
            health=5,
        )
        self.ground_y = ground_y
        self.movement = movement
        self.attacks = attacks
        self.combat = combat
        self.facing = 1
        self.attack_state: AttackState | None = None
        self.current_animation = "idle"
        self.is_on_ground = True
        self.hurt_timer = 0.0
        self.invulnerability_timer = 0.0
        self.death_timer = 0.0
        self.ability_charge_percent = 0.0
        self.is_ability_active = False

    @property
    def is_hurt(self) -> bool:
        return self.hurt_timer > 0

    @property
    def is_dead(self) -> bool:
        return self.health <= 0

    @property
    def can_be_attacked(self) -> bool:
        return not self.is_dead and self.invulnerability_timer <= 0

    def start_jump(self) -> None:
        """Start a jump using the configured separate jump key, not W/S."""
        if not self.is_dead and not self.is_hurt and self.is_on_ground and self.attack_state is None:
            self.velocity_y = self.movement.jump_velocity
            self.is_on_ground = False
            self.current_animation = "jump_rise"

    def start_yamato_attack(self, *, back_modifier: bool, attack_key_held: bool) -> None:
        """Choose the proper Yamato attack from ground/air and S + attack state."""
        if self.is_dead or self.is_hurt or self.attack_state is not None:
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
        animation_duration = profile.duration
        if attack_id in {"yamato_ground_launcher_rise", "yamato_ground_launcher_full"}:
            animation_duration = max(
                self.attacks["yamato_ground_launcher_rise"].duration,
                self.attacks["yamato_ground_launcher_full"].duration,
            )
        self.attack_state = AttackState(profile, animation_duration=animation_duration)
        self.current_animation = profile.animation
        get_player_animation_spec(profile.animation)

    @property
    def attack_hitbox(self) -> pygame.Rect | None:
        """Return the current Yamato hitbox during active attack frames."""
        if self.attack_state is None or not self.attack_state.is_active_hit_window:
            return None
        if self.attack_state.fixed_hitbox is not None:
            return self.attack_state.fixed_hitbox
        profile = self.attack_state.profile
        hitbox_top = self.rect.centery - profile.hitbox_height // 2
        if self.facing >= 0:
            return pygame.Rect(self.rect.right, hitbox_top, profile.range_px, profile.hitbox_height)
        return pygame.Rect(self.rect.left - profile.range_px, hitbox_top, profile.range_px, profile.hitbox_height)

    def update(self, dt: float, *, move_axis: int, arena_rect: pygame.Rect, attack_key_held: bool = False) -> None:
        """Advance movement, gravity and active attack animation."""
        if self.is_dead:
            self.current_animation = "death"
            self.death_timer += dt
            self.velocity_x = 0.0
            return
        self.invulnerability_timer = max(0.0, self.invulnerability_timer - dt)
        if self.hurt_timer > 0:
            self.hurt_timer = max(0.0, self.hurt_timer - dt)
            self.current_animation = "hurt"
            self.velocity_x = 0.0
        elif self.attack_state is None:
            self.velocity_x = move_axis * self.movement.horizontal_speed
            if move_axis != 0:
                self.facing = move_axis
        elif self.attack_state.profile.id == "ability":
            self.velocity_x = 0.0
            self._resolve_ability_dash(arena_rect)
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

        self._update_attack(dt, attack_key_held=attack_key_held)
        self._update_animation_from_motion(move_axis)
        if self.combat is not None:
            self.ability_charge_percent = min(100.0, self.ability_charge_percent + self.combat.ability_charge_rate * dt)

    def receive_damage(self, amount: int) -> None:
        """Apply damage, start hurt/death animation, and reduce ability charge."""
        if not self.can_be_attacked:
            return
        self.take_damage(amount)
        if self.combat is not None:
            self.ability_charge_percent = max(0.0, self.ability_charge_percent - self.combat.ability_damage_loss_percent)
            self.invulnerability_timer = self.combat.hurt_invulnerability_duration
            if self.is_dead:
                self.death_timer = 0.0
                self.current_animation = "death"
                self.attack_state = None
            else:
                self.hurt_timer = self.combat.hurt_duration
                self.current_animation = "hurt"
                self.attack_state = None

    def start_taunt(self) -> bool:
        """Start a taunt animation if the player can act."""
        if self.is_dead or self.is_hurt or self.attack_state is not None:
            return False
        profile = self.attacks.get("taunt")
        if profile is None:
            return False
        self.attack_state = AttackState(profile, animation_duration=profile.duration)
        self.current_animation = profile.animation
        return True

    def try_activate_ability(self) -> bool:
        """Consume a full charge and start the configured forward dash ability."""
        if self.ability_charge_percent < 100 or self.is_dead or self.is_hurt or self.attack_state is not None:
            return False
        profile = self.attacks.get("ability")
        if profile is None:
            return False
        self.ability_charge_percent = 0.0
        self.is_ability_active = True
        self.attack_state = AttackState(profile, animation_duration=profile.duration)
        self.current_animation = profile.animation
        return True

    def _resolve_ability_dash(self, arena_rect: pygame.Rect) -> None:
        if self.attack_state is None or self.attack_state.dash_resolved or self.attack_state.profile.id != "ability":
            return
        profile = self.attack_state.profile
        start_rect = self.rect.copy()
        target_x = self.x + self.facing * profile.range_px
        self.x = max(arena_rect.left, min(target_x, arena_rect.right - self.width))
        end_rect = self.rect.copy()
        left = min(start_rect.left, end_rect.left)
        right = max(start_rect.right, end_rect.right)
        top = self.rect.centery - profile.hitbox_height // 2
        self.attack_state.fixed_hitbox = pygame.Rect(left, top, max(1, right - left), profile.hitbox_height)
        self.attack_state.dash_resolved = True

    def _update_attack(self, dt: float, *, attack_key_held: bool) -> None:
        if self.attack_state is None:
            return
        self.attack_state.elapsed += dt
        self._resolve_launcher_variant(attack_key_held)
        profile = self.attack_state.profile
        if profile.launch_player and self.attack_state.elapsed >= profile.duration * 0.72 and self.is_on_ground:
            self.velocity_y = profile.player_vertical_boost
            self.is_on_ground = False
        if self.attack_state.elapsed >= profile.duration:
            if profile.id == "ability":
                self.is_ability_active = False
            self.attack_state = None

    def _resolve_launcher_variant(self, attack_key_held: bool) -> None:
        if self.attack_state is None or self.attack_state.variant_choice_checked:
            return
        profile = self.attack_state.profile
        if profile.id not in {"yamato_ground_launcher_rise", "yamato_ground_launcher_full"}:
            return
        check_time = profile.variant_check_time
        if check_time is None or self.attack_state.elapsed < check_time:
            return
        chosen_id = "yamato_ground_launcher_rise" if attack_key_held else "yamato_ground_launcher_full"
        if chosen_id != profile.id:
            self.attack_state.profile = self.attacks[chosen_id]
            if self.current_animation != self.attack_state.profile.animation:
                self.current_animation = self.attack_state.profile.animation
            get_player_animation_spec(self.attack_state.profile.animation)
        self.attack_state.variant_choice_checked = True

    def current_animation_frame_index(self, frame_count: int) -> int:
        """Return a frame index synchronized to the active attack duration when attacking."""
        if frame_count <= 0:
            return 0
        if self.is_dead:
            duration = self.combat.death_duration if self.combat is not None else 1.0
            return min(frame_count - 1, int(self.death_timer / max(0.001, duration / frame_count)))
        if self.attack_state is None:
            return 0
        animation_duration = self.attack_state.animation_duration or self.attack_state.profile.duration
        frame_duration = animation_duration / frame_count
        if frame_duration <= 0:
            return 0
        return min(frame_count - 1, int(self.attack_state.elapsed / frame_duration))

    def _update_animation_from_motion(self, move_axis: int) -> None:
        if self.is_dead or self.is_hurt or self.attack_state is not None:
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
