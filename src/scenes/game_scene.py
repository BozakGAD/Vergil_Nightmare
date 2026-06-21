"""First playable arena scene with JSON-tuned player, waves and pause menu."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pygame

from src.core.gameplay_config import GameplayConfig
from src.core.settings import AssetSettings
from src.entities.enemy import Enemy, create_enemy
from src.entities.player import GROUND_Y, Player
from src.systems.combo_system import ComboSystem
from src.systems.control_settings import ControlSettings
from src.systems.sprite_loader import load_animation_frames
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
        self.enemy_arena_rect = pygame.Rect(-self.screen_width, 96, self.screen_width * 3, self.ground_y - 96)
        self.player = Player(
            x=self.screen_width * 0.35,
            movement=self.gameplay_config.movement,
            attacks=self.gameplay_config.attacks,
            combat=self.gameplay_config.player_combat,
            ground_y=self.ground_y,
        )
        self.enemies: list[Enemy] = []
        self.wave_delay_timer = 0.0
        self.combo_system = ComboSystem(self.gameplay_config.combo)
        self.is_taunt_timeout_paused = False
        self.is_victory = False
        self.final_style_rank: str | None = None
        self.final_style_score: float = 0.0
        self._spawn_next_wave()
        font_path = pygame.font.match_font("dejavusans")
        self.button_font = pygame.font.Font(font_path, 28)
        self.small_font = pygame.font.Font(font_path, 17)
        self._key_names_down: set[str] = set()
        self.is_paused = False
        self.settings_panel = ControlSettingsPanel(screen_size=screen_size, controls=self.controls)
        self.pause_buttons = self._create_pause_buttons()
        self.background_image = self._load_scaled_image(self.assets.game_background, (self.screen_width, self.ground_y))
        self.hp_images = self._load_numbered_ui_images("assets/ui/hp", (190, 58))
        self.ability_images = self._load_numbered_ui_images("assets/ui/ability", (220, 34))
        self.player_frames = load_animation_frames(self.gameplay_config.sprites)
        self.enemy_frames = load_animation_frames(self.gameplay_config.enemy_sprites)
        self.victory_buttons = self._create_victory_buttons()

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle gameplay, pause and settings inputs."""
        if self.is_victory:
            for button in self.victory_buttons:
                button.handle_event(event)
            return

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
            if key_name == self.controls.get("taunt"):
                if self.player.start_taunt():
                    self.is_taunt_timeout_paused = self.combo_system.has_active_combo
                    self.combo_system.pause_timeout()
                return
            if key_name == self.controls.get("ability"):
                self.player.try_activate_ability()
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
        if self.is_victory or self.is_paused or self.settings_panel.is_open:
            return

        keys = pygame.key.get_pressed()
        move_axis = 0
        if self._is_control_pressed(keys, "move_left"):
            move_axis -= 1
        if self._is_control_pressed(keys, "move_right"):
            move_axis += 1

        was_taunting = self.player.attack_state is not None and self.player.attack_state.profile.id == "taunt"
        self.player.update(
            dt,
            move_axis=move_axis,
            arena_rect=self.arena_rect,
            attack_key_held=self._is_attack_key_down(),
        )
        if was_taunting and self.player.attack_state is None and not self.player.is_hurt and not self.player.is_dead:
            self.combo_system.resume_timeout()
            if self.is_taunt_timeout_paused:
                self.combo_system.activate_taunt_multiplier()
            self.is_taunt_timeout_paused = False
        for enemy in self.enemies:
            enemy.update(dt, self.player, self.enemy_arena_rect, neighbors=self.enemies)
        self._resolve_player_attack_hits()
        self._resolve_enemy_attack_hits()
        self.combo_system.update(dt)
        had_enemies_before_cleanup = bool(self.enemies)
        self.enemies = [enemy for enemy in self.enemies if not enemy.should_remove]
        if had_enemies_before_cleanup and not self.enemies and self.wave_delay_timer <= 0:
            self.wave_delay_timer = self.wave_manager.settings.inter_wave_delay
        if self.player.is_dead and self.player.death_timer >= self.gameplay_config.player_combat.death_duration:
            self._finish_victory()
            return
        if self.enemies and all(enemy.is_dying for enemy in self.enemies):
            return
        if self.enemies and all(not enemy.is_alive for enemy in self.enemies):
            self.enemies = []
            self.wave_delay_timer = self.wave_manager.settings.inter_wave_delay
            if self.wave_delay_timer <= 0:
                self._spawn_next_wave()
        if not self.enemies and self.wave_delay_timer > 0:
            self.wave_delay_timer = max(0.0, self.wave_delay_timer - dt)
            if self.wave_delay_timer == 0.0:
                self._spawn_next_wave()

    def draw(self, surface: pygame.Surface) -> None:
        """Draw gameplay, pause menu and settings overlay."""
        surface.fill(self.BACKGROUND_COLOR)
        if self.background_image is not None:
            surface.blit(self.background_image, (0, 0))
        else:
            pygame.draw.rect(surface, (20, 24, 36, 190), self.arena_rect)
        pygame.draw.line(
            surface,
            self.FLOOR_COLOR,
            (0, self.ground_y),
            (self.screen_width, self.ground_y),
            4,
        )

        self._draw_player(surface)
        for enemy in self.enemies:
            if enemy.is_alive or enemy.is_dying:
                self._draw_enemy(surface, enemy)
                if enemy.is_alive:
                    self._draw_launch_ready_dot(surface, enemy)
                    self._draw_health_bar(surface, enemy.rect, enemy.health, enemy.max_health)

        self._draw_attack_hitbox(surface)
        self._draw_enemy_attack_hitboxes(surface)

        self._draw_player_hud(surface)
        self._draw_combo_hud(surface)
        if self.is_paused:
            self._draw_pause_overlay(surface)
        if self.is_victory:
            self._draw_victory_overlay(surface)
        self.settings_panel.draw(surface)

    def _spawn_next_wave(self) -> None:
        spawns = self.wave_manager.next_wave(self.screen_width)
        if not spawns:
            self._finish_victory()
            return
        self.enemies = [self._create_enemy(spawn.enemy_id, spawn.x) for spawn in spawns]

    def _create_enemy(self, enemy_id: str, x: float) -> Enemy:
        profile = self.gameplay_config.enemies[enemy_id]
        return create_enemy(enemy_id, x=x, profile=profile, ground_y=self.ground_y)

    def _create_victory_buttons(self) -> list[Button]:
        button_width = 300
        button_height = 58
        gap = 22
        top = self.screen_height // 2 + 20
        left = self.screen_width // 2 - button_width // 2
        return [
            Button(pygame.Rect(left, top, button_width, button_height), "Начать заново", self._restart_after_victory),
            Button(pygame.Rect(left, top + button_height + gap, button_width, button_height), "В главное меню", self.return_to_menu),
        ]

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

    def _toggle_pause(self) -> None:
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.pause_buttons = self._create_pause_buttons()

    def _resume(self) -> None:
        self.is_paused = False
        self.settings_panel.close()

    def _restart_after_victory(self) -> None:
        self.player = Player(
            x=self.screen_width * 0.35,
            movement=self.gameplay_config.movement,
            attacks=self.gameplay_config.attacks,
            combat=self.gameplay_config.player_combat,
            ground_y=self.ground_y,
        )
        self.enemies = []
        self.wave_manager.reset()
        self.wave_delay_timer = 0.0
        self.combo_system = ComboSystem(self.gameplay_config.combo)
        self.is_taunt_timeout_paused = False
        self.is_victory = False
        self.final_style_rank = None
        self.final_style_score = 0.0
        self.is_paused = False
        self.settings_panel.close()
        self._key_names_down.clear()
        self._spawn_next_wave()

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
            if enemy_id in attack_state.hit_enemy_ids or not enemy.is_alive or enemy.is_dying or not hitbox.colliderect(enemy.rect):
                continue
            enemy.receive_attack(attack_state.profile, self.player.centerx)
            attack_state.hit_enemy_ids.add(enemy_id)
            self.combo_system.register_hit()
            hit_any_enemy = True

        if hit_any_enemy and attack_state.profile.player_vertical_boost and not attack_state.profile.launch_player:
            self.player.velocity_y = min(self.player.velocity_y, attack_state.profile.player_vertical_boost)
            self.player.is_on_ground = False

    def _resolve_enemy_attack_hits(self) -> None:
        for enemy in self.enemies:
            hitbox = enemy.attack_hitbox
            if hitbox is None or enemy.has_hit_player_this_attack or not enemy.is_alive or enemy.is_dying or not self.player.can_be_attacked:
                continue
            if hitbox.colliderect(self.player.rect):
                self.player.receive_damage(enemy.profile.attack_damage)
                enemy.has_hit_player_this_attack = True
                self.combo_system.register_player_damage()
                self.is_taunt_timeout_paused = False

    def _finish_victory(self) -> None:
        self.combo_system.reset_combo()
        self.final_style_rank = self.combo_system.final_style_rank()
        self.final_style_score = self.combo_system.total_score
        self._save_style_rank()
        self.is_victory = True

    def _save_style_rank(self) -> None:
        if self.final_style_rank is None:
            return
        path = Path("saves/style_rank.json")
        path.parent.mkdir(parents=True, exist_ok=True)
        import json

        path.write_text(
            json.dumps({"rank": self.final_style_rank, "score": round(self.final_style_score, 2)}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def _draw_player(self, surface: pygame.Surface) -> None:
        frames = self.player_frames.get(self.player.current_animation)
        if frames:
            frame_index = self._player_frame_index(frames)
            frame = frames[frame_index]
            rect = frame.get_rect(midbottom=self.player.rect.midbottom)
            if self.player.facing < 0:
                frame = pygame.transform.flip(frame, True, False)
            surface.blit(frame, rect)
            return
        self._draw_entity(surface, self.player.rect, self.player.color, outline=(210, 240, 255))

    def _player_frame_index(self, frames: list[pygame.Surface]) -> int:
        if self.player.attack_state is not None or self.player.is_dead:
            return self.player.current_animation_frame_index(len(frames))
        return int(pygame.time.get_ticks() / (self.gameplay_config.sprites.default_frame_duration * 1000)) % len(frames)

    def _draw_attack_hitbox(self, surface: pygame.Surface) -> None:
        attack_state = self.player.attack_state
        hitbox = self.player.attack_hitbox
        if attack_state is None or hitbox is None:
            return
        frames = self.player_frames.get(attack_state.profile.hitbox_animation or "")
        if frames:
            frame_count = attack_state.profile.hitbox_frame_count or len(frames)
            frame = frames[self.player.current_animation_frame_index(min(frame_count, len(frames)))]
            frame = pygame.transform.smoothscale(frame, hitbox.size)
            rect = frame.get_rect(center=hitbox.center)
            if self.player.facing < 0:
                frame = pygame.transform.flip(frame, True, False)
            surface.blit(frame, rect)
            return
        pygame.draw.rect(surface, (120, 210, 255), hitbox, width=2, border_radius=3)

    def _draw_enemy_attack_hitboxes(self, surface: pygame.Surface) -> None:
        for enemy in self.enemies:
            hitbox = enemy.attack_hitbox
            if hitbox is None:
                continue
            frames = self.enemy_frames.get(enemy.profile.attack_hitbox_animation or "")
            if frames:
                frame_count = enemy.profile.attack_hitbox_frame_count or len(frames)
                frame = pygame.transform.smoothscale(frames[enemy.current_animation_frame_index(min(frame_count, len(frames)))], hitbox.size)
                if self._should_flip_enemy_frame(enemy):
                    frame = pygame.transform.flip(frame, True, False)
                surface.blit(frame, frame.get_rect(center=hitbox.center))
            else:
                pygame.draw.rect(surface, (255, 110, 90), hitbox, width=2, border_radius=3)

    def _draw_player_hud(self, surface: pygame.Surface) -> None:
        health_rect = pygame.Rect(24, 24, 190, 58)
        pygame.draw.rect(surface, (0, 0, 0, 120), health_rect, border_radius=10)
        pygame.draw.rect(surface, self.TEXT_COLOR, health_rect, width=2, border_radius=10)
        hp_image = self.hp_images.get(self.player.health) or self.hp_images.get(max(self.hp_images) if self.hp_images else -1)
        if hp_image is not None:
            surface.blit(hp_image, health_rect)
        label = self.small_font.render(f"HP: {self.player.health}/5", True, self.TEXT_COLOR)
        surface.blit(label, label.get_rect(center=health_rect.center))
        ability_rect = pygame.Rect(24, 92, 220, 34)
        ability_image = self._ability_hud_image()
        if ability_image is not None:
            surface.blit(ability_image, ability_rect)
        else:
            pygame.draw.rect(surface, (35, 45, 80, 160), ability_rect, border_radius=8)
            pygame.draw.rect(surface, (110, 160, 255), ability_rect, width=2, border_radius=8)
        percent = round(self.player.ability_charge_percent)
        ability = self.small_font.render(f"Ability: {percent}%", True, self.TEXT_COLOR)
        surface.blit(ability, ability.get_rect(center=ability_rect.center))

    def _draw_combo_hud(self, surface: pygame.Surface) -> None:
        if self.combo_system.current_hits == 0:
            return
        rank = self.combo_system.current_combo_rank()
        if rank is not None:
            rank_rect = pygame.Rect(self.screen_width - 150, 24, 100, 70)
            pygame.draw.rect(surface, (0, 0, 0, 120), rank_rect, border_radius=10)
            pygame.draw.rect(surface, self.TEXT_COLOR, rank_rect, width=2, border_radius=10)
            rank_label = self.button_font.render(rank, True, self.TEXT_COLOR)
            surface.blit(rank_label, rank_label.get_rect(center=rank_rect.center))
        hits_label = self.small_font.render(f"Hits: {self.combo_system.current_hits}", True, self.TEXT_COLOR)
        surface.blit(hits_label, (self.screen_width - 155, 104))

    def _draw_victory_overlay(self, surface: pygame.Surface) -> None:
        mouse_position = pygame.mouse.get_pos()
        layer = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        layer.fill((0, 0, 0, 170))
        surface.blit(layer, (0, 0))
        rank_rect = pygame.Rect(0, 0, 260, 120)
        rank_rect.center = (self.screen_width // 2, 150)
        pygame.draw.rect(surface, (25, 28, 45), rank_rect, border_radius=12)
        pygame.draw.rect(surface, self.TEXT_COLOR, rank_rect, width=2, border_radius=12)
        rank_text = self.button_font.render(f"Style: {self.final_style_rank or '—'}", True, self.TEXT_COLOR)
        surface.blit(rank_text, rank_text.get_rect(center=(rank_rect.centerx, rank_rect.centery - 16)))
        score_text = self.small_font.render(f"Score: {self.final_style_score:.0f}", True, self.MUTED_TEXT_COLOR)
        surface.blit(score_text, score_text.get_rect(center=(rank_rect.centerx, rank_rect.centery + 26)))
        for button in self.victory_buttons:
            button.draw(surface, self.button_font, mouse_position=mouse_position)

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

    def _draw_enemy(self, surface: pygame.Surface, enemy: Enemy) -> None:
        frames = self.enemy_frames.get(enemy.current_animation)
        if frames:
            frame = pygame.transform.smoothscale(
                frames[enemy.current_animation_frame_index(len(frames))],
                enemy.rect.size,
            )
            rect = frame.get_rect(midbottom=enemy.rect.midbottom)
            if self._should_flip_enemy_frame(enemy):
                frame = pygame.transform.flip(frame, True, False)
            surface.blit(frame, rect)
            return
        self._draw_entity(surface, enemy.rect, enemy.color)

    def _should_flip_enemy_frame(self, enemy: Enemy) -> bool:
        """Return whether an enemy sprite needs horizontal flipping for its facing."""
        if enemy.profile.enemy_id == "fast_enemy":
            return enemy.facing > 0
        return enemy.facing < 0

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

    def _ability_hud_image(self) -> pygame.Surface | None:
        charge = self.player.ability_charge_percent
        if charge >= 100:
            index = 4
        elif charge < 25:
            index = 1
        elif charge < 50:
            index = 2
        elif charge < 75:
            index = 3
        else:
            index = 3
        return self.ability_images.get(index)

    def _load_numbered_ui_images(self, folder: str, size: tuple[int, int]) -> dict[int, pygame.Surface]:
        root = Path(folder)
        images: dict[int, pygame.Surface] = {}
        if not root.exists():
            return images
        for path in root.iterdir():
            if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
                continue
            try:
                index = int(path.stem)
            except ValueError:
                continue
            images[index] = self._load_scaled_image(str(path), size)
        return {key: value for key, value in images.items() if value is not None}

    def _load_scaled_image(self, image_path: str | None, size: tuple[int, int]) -> pygame.Surface | None:
        if not image_path:
            return None
        path = Path(image_path)
        if not path.exists():
            return None
        image = pygame.image.load(path).convert_alpha()
        return pygame.transform.smoothscale(image, size)
