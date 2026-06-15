"""First playable arena scene with JSON-tuned player, waves and pause menu."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pygame

from src.core.gameplay_config import GameplayConfig
from src.core.settings import AssetSettings
from src.entities.animation import PLAYER_ANIMATION_SPECS
from src.entities.enemy import Enemy, FastEnemy, HeavyEnemy, SlowEnemy
from src.entities.player import GROUND_Y, Player
from src.systems.control_settings import ControlSettings
from src.systems.sprite_loader import load_player_animation_frames
from src.systems.wave_manager import WaveManager
from src.ui.button import Button
from src.ui.control_settings_panel import ControlSettingsPanel


class GameScene:
    """Minimal combat sandbox with pause, settings overlay and generated waves."""

    BACKGROUND_COLOR = (9, 11, 18)
    FLOOR_COLOR = (42, 46, 62)
    TEXT_COLOR = (235, 238, 246)
    MUTED_TEXT_COLOR = (165, 170, 186)
    LAUNCH_READY_DOT_COLOR = (70, 180, 255)

    def __init__(
        self,
        screen_size: tuple[int, int],
        controls: ControlSettings,
        assets: AssetSettings,
        return_to_menu: Callable[[], None],
        gameplay_config: GameplayConfig | None = None,
        wave_manager: WaveManager | None = None,
    ) -> None:
        self.screen_width, self.screen_height = screen_size
        self.controls = controls
        self.assets = assets
        self.return_to_menu = return_to_menu
        self.gameplay_config = gameplay_config or GameplayConfig.from_files()
        self.wave_manager = wave_manager or WaveManager.from_file()
        self.ground_y = min(GROUND_Y, self.screen_height - 92)
        self.arena_rect = pygame.Rect(72, 96, self.screen_width - 144, self.ground_y - 96)
        self.player = Player(
            x=self.screen_width * 0.35,
            movement=self.gameplay_config.movement,
            attacks=self.gameplay_config.attacks,
            ground_y=self.ground_y,
        )
        self.enemies: list[Enemy] = []
        self._spawn_next_wave()
        font_path = pygame.font.match_font("dejavusans")
        self.button_font = pygame.font.Font(font_path, 28)
        self.small_font = pygame.font.Font(font_path, 17)
        self._key_names_down: set[str] = set()
        self.is_paused = False
        self.settings_panel = ControlSettingsPanel(screen_size=screen_size, controls=self.controls)
        self.pause_buttons = self._create_pause_buttons()
        self.background_image = self._load_scaled_image(self.assets.game_background, (self.screen_width, self.screen_height))
        self.player_frames = load_player_animation_frames(self.gameplay_config.sprites)

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle gameplay, pause and settings inputs."""
        if self.settings_panel.handle_event(event):
            return

        if event.type == pygame.KEYDOWN:
            key_name = pygame.key.name(event.key)
            self._key_names_down.add(key_name)
            if key_name == self.controls.get("pause"):
                self._toggle_pause()
                return
            if self.is_paused:
                return
            if key_name == self.controls.get("jump"):
                self.player.start_jump()
                return
            if key_name == self.controls.get("attack"):
                self.player.start_yamato_attack(
                    back_modifier=self._is_back_modifier_down(),
                    attack_key_held=self._is_attack_key_down(),
                )
                return
        elif event.type == pygame.KEYUP:
            self._key_names_down.discard(pygame.key.name(event.key))

        if self.is_paused:
            for button in self.pause_buttons:
                button.handle_event(event)

    def update(self, dt: float) -> None:
        """Update player, enemies and prototype combat collisions."""
        if self.is_paused or self.settings_panel.is_open:
            return

        keys = pygame.key.get_pressed()
        move_axis = 0
        if self._is_control_pressed(keys, "move_left"):
            move_axis -= 1
        if self._is_control_pressed(keys, "move_right"):
            move_axis += 1

        self.player.update(dt, move_axis=move_axis, arena_rect=self.arena_rect)
        for enemy in self.enemies:
            enemy.update(dt, self.player, self.arena_rect)
        self._resolve_player_attack_hits()
        if self.enemies and all(not enemy.is_alive for enemy in self.enemies):
            self._spawn_next_wave()

    def draw(self, surface: pygame.Surface) -> None:
        """Draw gameplay, pause menu and settings overlay."""
        surface.fill(self.BACKGROUND_COLOR)
        if self.background_image is not None:
            surface.blit(self.background_image, (0, 0))
        pygame.draw.rect(surface, (20, 24, 36, 190), self.arena_rect, border_radius=10)
        pygame.draw.line(
            surface,
            self.FLOOR_COLOR,
            (self.arena_rect.left, self.ground_y),
            (self.arena_rect.right, self.ground_y),
            4,
        )

        self._draw_player(surface)
        for enemy in self.enemies:
            if enemy.is_alive:
                self._draw_entity(surface, enemy.rect, enemy.color)
                self._draw_launch_ready_dot(surface, enemy)
                self._draw_health_bar(surface, enemy.rect, enemy.health, enemy.max_health)

        hitbox = self.player.attack_hitbox
        if hitbox is not None:
            pygame.draw.rect(surface, (120, 210, 255), hitbox, width=2, border_radius=3)

        self._draw_health_bar(surface, self.player.rect, self.player.health, self.player.max_health)
        self._draw_debug_text(surface)
        if self.is_paused:
            self._draw_pause_overlay(surface)
        self.settings_panel.draw(surface)

    def _spawn_next_wave(self) -> None:
        spawns = self.wave_manager.next_wave(self.screen_width)
        self.enemies = [self._create_enemy(spawn.enemy_id, spawn.x) for spawn in spawns]

    def _create_enemy(self, enemy_id: str, x: float) -> Enemy:
        profile = self.gameplay_config.enemies[enemy_id]
        enemy_classes = {"slow_enemy": SlowEnemy, "fast_enemy": FastEnemy, "heavy_enemy": HeavyEnemy}
        return enemy_classes[enemy_id](x=x, profile=profile, ground_y=self.ground_y)

    def _create_pause_buttons(self) -> list[Button]:
        button_width = 340
        button_height = 58
        gap = 20
        start_y = self.screen_height // 2 - button_height - gap
        left = self.screen_width // 2 - button_width // 2
        actions: tuple[tuple[str, Callable[[], None]], ...] = (
            ("Продолжить", self._resume),
            ("Настройки", self.settings_panel.open),
            ("В главное меню", self.return_to_menu),
        )
        return [
            Button(
                rect=pygame.Rect(left, start_y + index * (button_height + gap), button_width, button_height),
                text=label,
                on_click=action,
            )
            for index, (label, action) in enumerate(actions)
        ]

    def _rebuild_pause_buttons(self) -> None:
        button_width = 340
        button_height = 58
        gap = 20
        start_y = self.screen_height // 2 - button_height - gap
        left = self.screen_width // 2 - button_width // 2
        actions: tuple[tuple[str, Callable[[], None]], ...] = (
            ("Продолжить", self._resume),
            ("Настройки", self.settings_panel.open),
            ("В главное меню", self.return_to_menu),
        )
        self.pause_buttons = [
            Button(
                rect=pygame.Rect(left, start_y + index * (button_height + gap), button_width, button_height),
                text=label,
                on_click=action,
            )
            for index, (label, action) in enumerate(actions)
        ]

    def _toggle_pause(self) -> None:
        self.is_paused = not self.is_paused
        if self.is_paused:
            self._rebuild_pause_buttons()

    def _resume(self) -> None:
        self.is_paused = False
        self.settings_panel.close()

    def _is_back_modifier_down(self) -> bool:
        return "s" in self._key_names_down

    def _is_attack_key_down(self) -> bool:
        return self.controls.get("attack") in self._key_names_down

    def _is_control_pressed(self, keys: pygame.key.ScancodeWrapper, action: str) -> bool:
        try:
            return bool(keys[pygame.key.key_code(self.controls.get(action))])
        except ValueError:
            return False

    def _resolve_player_attack_hits(self) -> None:
        attack_state = self.player.attack_state
        hitbox = self.player.attack_hitbox
        if attack_state is None or hitbox is None:
            return

        hit_any_enemy = False
        for enemy in self.enemies:
            enemy_id = id(enemy)
            if enemy_id in attack_state.hit_enemy_ids or not enemy.is_alive or not hitbox.colliderect(enemy.rect):
                continue
            enemy.receive_attack(attack_state.profile, self.player.centerx)
            attack_state.hit_enemy_ids.add(enemy_id)
            hit_any_enemy = True

        if hit_any_enemy and attack_state.profile.player_vertical_boost and not attack_state.profile.launch_player:
            self.player.velocity_y = min(self.player.velocity_y, attack_state.profile.player_vertical_boost)
            self.player.is_on_ground = False

    def _draw_player(self, surface: pygame.Surface) -> None:
        frames = self.player_frames.get(self.player.current_animation)
        if frames:
            frame_index = int(pygame.time.get_ticks() / (self.gameplay_config.sprites.frame_duration * 1000)) % len(frames)
            frame = frames[frame_index]
            rect = frame.get_rect(midbottom=self.player.rect.midbottom)
            if self.player.facing < 0:
                frame = pygame.transform.flip(frame, True, False)
            surface.blit(frame, rect)
            return
        self._draw_entity(surface, self.player.rect, self.player.color, outline=(210, 240, 255))

    def _draw_entity(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        color: tuple[int, int, int],
        *,
        outline: tuple[int, int, int] | None = None,
    ) -> None:
        pygame.draw.rect(surface, color, rect, border_radius=6)
        pygame.draw.rect(surface, outline or (245, 245, 245), rect, width=2, border_radius=6)

    def _draw_launch_ready_dot(self, surface: pygame.Surface, enemy: Enemy) -> None:
        if enemy.needs_launch_charge and enemy.can_be_launched:
            pygame.draw.circle(surface, self.LAUNCH_READY_DOT_COLOR, (enemy.rect.centerx, enemy.rect.top - 18), 4)

    def _draw_health_bar(self, surface: pygame.Surface, rect: pygame.Rect, health: int, max_health: int) -> None:
        bar_rect = pygame.Rect(rect.left, rect.top - 10, rect.width, 5)
        pygame.draw.rect(surface, (45, 48, 58), bar_rect)
        fill_width = round(bar_rect.width * (health / max_health)) if max_health else 0
        pygame.draw.rect(surface, (90, 220, 120), pygame.Rect(bar_rect.left, bar_rect.top, fill_width, bar_rect.height))

    def _draw_pause_overlay(self, surface: pygame.Surface) -> None:
        mouse_position = pygame.mouse.get_pos()
        dim_layer = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        dim_layer.fill((0, 0, 0, 145))
        surface.blit(dim_layer, (0, 0))
        title = self.button_font.render("Пауза", True, self.TEXT_COLOR)
        surface.blit(title, title.get_rect(center=(self.screen_width // 2, self.screen_height // 2 - 120)))
        for button in self.pause_buttons:
            button.draw(surface, self.button_font, mouse_position=mouse_position)

    def _draw_debug_text(self, surface: pygame.Surface) -> None:
        attack = self.player.attack_state.profile.id if self.player.attack_state else "none"
        lines = [
            "GameScene prototype: A/D — движение, Alt — прыжок, J — атака, S+J — launcher/downslash, Esc — пауза",
            f"wave={self.wave_manager.current_wave}/{self.wave_manager.settings.max_waves} animation={self.player.current_animation} attack={attack}",
            "Волны, атаки, движение, гравитация, фон и спрайты настраиваются через JSON.",
            f"animation placeholders: {len(PLAYER_ANIMATION_SPECS)} specs ready for future sprite slicing",
        ]
        for index, line in enumerate(lines):
            color = self.TEXT_COLOR if index == 0 else self.MUTED_TEXT_COLOR
            label = self.small_font.render(line, True, color)
            surface.blit(label, (82, 24 + index * 23))

    def _load_scaled_image(self, image_path: str | None, size: tuple[int, int]) -> pygame.Surface | None:
        if not image_path:
            return None
        path = Path(image_path)
        if not path.exists():
            return None
        image = pygame.image.load(path).convert_alpha()
        return pygame.transform.smoothscale(image, size)
